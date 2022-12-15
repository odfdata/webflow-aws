from typing import List

from aws_cdk import (
    aws_cloudfront,
    aws_lambda,
    aws_route53,
    aws_route53_targets,
    aws_s3,
    aws_s3_notifications,
    Fn,
    Stack
)
from constructs import Construct

from webflow_aws.backend.compute.infrastructure import Compute
from webflow_aws.backend.networking.infrastructure import Networking
from webflow_aws.backend.storage.infrastructure import Storage


class Backend(Stack):
    """
    The backend AWS CDK app. It contains these sub-constructs:
        + networking: contains all networking services used for WebflowAWS
        + compute: contains all compute services used for WebflowAWS
        + storage: contains all storage services used for WebflowAWS
    """

    def __init__(self, scope: Construct, construct_id: str, configuration: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.networking = Networking(self, "WebflowAwsNetworking", configuration=configuration)
        self.compute = Compute(
            self, "WebflowAwsCompute", cloud_front_distribution=self.networking.main_cloud_front_distribution,
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
            cloud_front_distribution=self.networking.main_cloud_front_distribution)

    @staticmethod
    def __add_s3_bucket_event_notification(
            s3_bucket: aws_s3.Bucket, s3_trigger_lambda_function: aws_lambda.Function
    ):
        """
        Add the S3 bucket event notification to trigger the AWS Lambda function every time a new object is created
        in the AWS S3 bucket inside the artifacts/ folder.

        :param s3_bucket: The S3 bucket for which you want to create the event notification for
        :param s3_trigger_lambda_function: The AWS Lambda function you want to trigger
        """
        s3_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(s3_trigger_lambda_function),
            (aws_s3.NotificationKeyFilter(prefix='artifacts/', suffix='.zip')))

    def __create_route_53_record_group(
            self, route_53_hosted_zone: aws_route53.HostedZone, domain_name: str, alternative_domain_names: List[str],
            cloud_front_distribution: aws_cloudfront.Distribution
    ):
        """
        Create a new route 53 record group based on domain name and alternative domain names.

        :param route_53_hosted_zone: the route 53 hosted zone you want to update
        :param domain_name: the domain name
        :param alternative_domain_names: the list of domain names you want to support
        :param cloud_front_distribution: the cloudfront distribution you want to point all the domains
        and subdomains to
        """
        domain_names = alternative_domain_names
        domain_names.append(domain_name)
        [
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

    @staticmethod
    def __create_s3_source_bucket_policy(
            s3_source_bucket: aws_s3.Bucket,
            cloud_front_origin_access_identity: aws_cloudfront.OriginAccessIdentity
    ):
        """
        Create the S3 source bucket policy that allows the CDN to get files from the S3 bucket
        :param s3_source_bucket: the S3 source bucket you want to allow CDN to get files from
        :param cloud_front_origin_access_identity: the cloudfront origin access identity you want to allow
        bucket access for
        """
        s3_source_bucket.grant_read(cloud_front_origin_access_identity)

    def __create_s3_trigger_lambda_invoke_permission(
            self, bucket_name: str, s3_trigger_lambda_function: aws_lambda.Function
    ):
        """
        Create the permission to invoke the AWS lambda function from the S3 bucket
        :param bucket_name: the s3 bucket name from which the AWS Lambda function will be invoked
        :param s3_trigger_lambda_function: the AWS lambda function the bucket needs to have the permission to invoke
        """
        aws_lambda.CfnPermission(
            self,
            'S3TriggerLambdaInvokePermission',
            function_name=s3_trigger_lambda_function.function_name,
            action='lambda:InvokeFunction',
            principal='s3.amazonaws.com',
            source_account=Fn.ref('AWS::AccountId'),
            source_arn=f'arn:aws:s3:::{bucket_name}'
        )
