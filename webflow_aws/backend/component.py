from typing import List

from constructs import Construct
from aws_cdk import (
    aws_cloudfront,
    aws_iam,
    aws_lambda,
    aws_route53,
    aws_route53_targets,
    aws_s3,
    aws_s3_notifications,
    Fn,
    Stack,
)

from backend.compute.infrastructure import Compute
from backend.networking.infrastructure import Networking
from backend.storage.infrastructure import Storage


class Backend(Stack):

    def __init__(self, scope: Construct, construct_id: str, configuration: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.networking = Networking(self, "WebflowAwsNetworking", configuration=configuration)
        self.compute = Compute(
            self, "WebflowAwsCompute", cloud_front_distribution=self.networking.cloud_front_distribution_www,
            configuration=configuration)
        self.storage = Storage(self, "WebflowAwsStorage", configuration=configuration)
        self.__add_s3_bucket_event_notification(
            s3_bucket=self.storage.s3_bucket, s3_trigger_lambda_function=self.compute.s3_trigger_lambda)
        self.__create_s3_trigger_lambda_invoke_permission(
            bucket_name=configuration['bucket_name'], s3_trigger_lambda_function=self.compute.s3_trigger_lambda)
        self.__create_s3_source_bucket_policy(
            s3_source_bucket=self.storage.s3_bucket,
            cloud_front_origin_access_identity=self.networking.cloud_front_origin_access_identity)
        self.__create_route_53_record_group(
            route_53_hosted_zone=self.networking.route_53_hosted_zone,
            domain_name=configuration['domain_name'],
            alternative_domain_names=configuration['CNAMEs'],
            cloud_front_distribution=self.networking.cloud_front_distribution_www)

    @staticmethod
    def __add_s3_bucket_event_notification(
            s3_bucket: aws_s3.Bucket, s3_trigger_lambda_function: aws_lambda.Function):
        s3_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(s3_trigger_lambda_function),
            (aws_s3.NotificationKeyFilter(prefix='artifacts/', suffix='.zip')))

    def __create_route_53_record_group(
            self, route_53_hosted_zone: aws_route53.HostedZone, domain_name: str, alternative_domain_names: List[str],
            cloud_front_distribution: aws_cloudfront.Distribution) -> List[aws_route53.ARecord]:
        domain_names = alternative_domain_names
        domain_names.append(domain_name)
        return [
            aws_route53.RecordSet(
                self,
                domain_name.replace('.', '').upper(),
                record_type=aws_route53.RecordType.A,
                zone=route_53_hosted_zone,
                record_name=domain_name,
                target=aws_route53.RecordTarget.from_alias(alias_target=aws_route53_targets.CloudFrontTarget(
                    distribution=cloud_front_distribution
                ))
            ) for domain_name in set(domain_names)
        ]

    def __create_s3_source_bucket_policy(
            self, s3_source_bucket: aws_s3.Bucket,
            cloud_front_origin_access_identity: aws_cloudfront.OriginAccessIdentity):
        return aws_s3.CfnBucketPolicy(
            self, 'S3SourceBucketPolicy',
            bucket=s3_source_bucket.bucket_name,
            policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=['s3:GetObject'],
                        sid='1',
                        resources=[f'arn:aws:s3:::{s3_source_bucket.bucket_name}/*'],
                        principals=[aws_iam.ArnPrincipal(
                            f'arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '
                            f'{cloud_front_origin_access_identity.origin_access_identity_name}')])]))

    def __create_s3_trigger_lambda_invoke_permission(
            self, bucket_name: str, s3_trigger_lambda_function: aws_lambda.Function) -> aws_lambda.Permission:
        return aws_lambda.CfnPermission(
            self, 'S3TriggerLambdaInvokePermission',
            function_name=s3_trigger_lambda_function.function_name,
            action='lambda:InvokeFunction',
            principal='s3.amazonaws.com',
            source_account=Fn.ref('AWS::AccountId'),
            source_arn=f'arn:aws:s3:::{bucket_name}'
        )
