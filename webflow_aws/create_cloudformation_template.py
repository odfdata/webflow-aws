from typing import Optional, List

from aws_cdk import (
    core,
    aws_lambda,
    aws_s3,
    aws_s3_notifications,
    aws_iam,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_certificatemanager, aws_route53, aws_route53_targets
)
from aws_cdk.aws_certificatemanager import CertificateValidation
from aws_cdk.aws_cloudfront import BehaviorOptions, AllowedMethods, CachedMethods, ViewerProtocolPolicy, EdgeLambda, \
    LambdaEdgeEventType, HttpVersion, PriceClass, ErrorResponse
from aws_cdk.aws_iam import ServicePrincipal, ManagedPolicy, PolicyDocument, PolicyStatement, Effect
from aws_cdk.aws_lambda import Code
from aws_cdk.aws_route53 import HostedZone
from aws_cdk.aws_s3 import Bucket, EventType, NotificationKeyFilter, BlockPublicAccess
from aws_cdk.core import Fn, Duration


class WebflowAWSStack(core.Stack):

    def __init__(
            self, scope: core.Construct, id: str, webflow_aws_setup_bucket: str, configuration: dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        route_53_hosted_zone = HostedZone.from_hosted_zone_attributes(
            self, 'HostedZone', hosted_zone_id=configuration['route_53_hosted_zone_id'],
            zone_name=configuration['route_53_hosted_zone_name'])
        cloud_front_lambda_execution_role = self.__create_cloud_front_lambda_execution_role()
        cloud_front_www_edit_path_for_origin_lambda = self.__create_cloud_front_www_edit_path_for_origin_lambda(
            webflow_aws_setup_bucket=webflow_aws_setup_bucket, lambda_execution_role=cloud_front_lambda_execution_role)
        cloud_front_www_edit_path_for_origin_lambda_version = \
            self.__create_cloud_front_www_edit_path_for_origin_lambda_version(
                cloud_front_www_edit_path_for_origin_lambda=cloud_front_www_edit_path_for_origin_lambda)
        cloud_front_origin_access_identity = self.__create_cloud_front_origin_access_identity()
        cloud_front_cache_policy = self.__create_cloud_front_cache_policy()
        ssl_certificate = self.__create_ssl_certificate(
            route_53_hosted_zone=route_53_hosted_zone, domain_name=configuration['domain_name'],
            alternative_domain_names=configuration['CNAMEs'])
        cloud_front_www = self.__create_cloud_front_www(
            origin_bucket_name=configuration['bucket_name'], cache_policy=cloud_front_cache_policy,
            origin_access_identity=cloud_front_origin_access_identity, ssl_certificate=ssl_certificate,
            domain_names=configuration['CNAMEs'],
            edge_lambda_viewer_request=cloud_front_www_edit_path_for_origin_lambda_version)
        s3_trigger_lambda_execution_role = self.__create_s3_trigger_lambda_execution_role(
            bucket_name=configuration['bucket_name'], cloudfront_distribution=cloud_front_www)
        s3_trigger_lambda_function = self.__create_s3_trigger_lambda_function(
            webflow_aws_setup_bucket=webflow_aws_setup_bucket, execution_role=s3_trigger_lambda_execution_role,
            cloud_front_distribution=cloud_front_www)
        s3_source_bucket = self.__create_s3_source_bucket(
            bucket_name=configuration['bucket_name'], s3_trigger_lambda_function=s3_trigger_lambda_function)
        self.__create_s3_trigger_lambda_invoke_permission(
            bucket_name=configuration['bucket_name'], s3_trigger_lambda_function=s3_trigger_lambda_function)
        self.__create_s3_source_bucket_policy(
            s3_source_bucket=s3_source_bucket, cloud_front_origin_access_identity=cloud_front_origin_access_identity)
        self.__create_route_53_record_group(
            route_53_hosted_zone=route_53_hosted_zone,
            domain_names=configuration['CNAMEs'], cloud_front_distribution=cloud_front_www)
        self.__create_cloud_front_www_output(cloud_front_www=cloud_front_www)

    def __create_cloud_front_cache_policy(self) -> aws_cloudfront.CachePolicy:
        return aws_cloudfront.CachePolicy(
            self, 'CloudFrontCachePolicy',
            comment='The CloudFront cache policy used by the DefaultCacheBehavior',
            default_ttl=Duration.seconds(1),
            max_ttl=Duration.seconds(1),
            min_ttl=Duration.seconds(1),
            cache_policy_name='CloudFrontWWWCachePolicy')

    def __create_cloud_front_origin_access_identity(self) -> aws_cloudfront.OriginAccessIdentity:
        return aws_cloudfront.OriginAccessIdentity(
            self, 'CloudFrontOriginAccessIdentity', comment='cloudfront-only-acc-identity')

    def __create_cloud_front_lambda_execution_role(self) -> aws_iam.Role:
        role = aws_iam.Role(
            self, 'CloudFrontLambdaExecutionRole',
            assumed_by=ServicePrincipal('lambda.amazonaws.com'),
            path='/',
            managed_policies=[ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')])
        role.assume_role_policy.add_statements(PolicyStatement(
            principals=[ServicePrincipal('edgelambda.amazonaws.com')],
            actions=['sts:AssumeRole']))
        return role

    def __create_cloud_front_www(
            self, origin_bucket_name: str, domain_names: Optional[List[str]],
            ssl_certificate: aws_certificatemanager.Certificate,
            cache_policy: aws_cloudfront.CachePolicy, origin_access_identity: aws_cloudfront.OriginAccessIdentity,
            edge_lambda_viewer_request: aws_lambda.Version) -> aws_cloudfront.Distribution:
        return aws_cloudfront.Distribution(
            self, 'CloudFrontWWW',
            enabled=True,
            certificate=ssl_certificate,
            comment='CloudFront Distribution for your WWW static website',
            domain_names=domain_names,
            http_version=HttpVersion.HTTP2,
            price_class=PriceClass.PRICE_CLASS_100,
            default_behavior=BehaviorOptions(
                allowed_methods=AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=CachedMethods.CACHE_GET_HEAD,
                cache_policy=cache_policy,
                viewer_protocol_policy=ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin=aws_cloudfront_origins.S3Origin(
                    bucket=Bucket.from_bucket_name(self, "OriginProd", bucket_name=origin_bucket_name),
                    origin_access_identity=origin_access_identity,
                    origin_path='/src/prod'
                ),
                edge_lambdas=[
                    EdgeLambda(
                        event_type=LambdaEdgeEventType.VIEWER_REQUEST,
                        include_body=False,
                        function_version=edge_lambda_viewer_request)]
            ),
            error_responses=[
                ErrorResponse(
                    ttl=Duration.seconds(300),
                    response_page_path='/404.html',
                    http_status=403,
                    response_http_status=404)]
        )

    def __create_cloud_front_www_edit_path_for_origin_lambda(
            self, webflow_aws_setup_bucket: str, lambda_execution_role: aws_iam.Role) -> aws_lambda.Function:
        return aws_lambda.Function(
            self, 'CloudFrontWWWEditPathForOrigin',
            function_name='CloudFront_WWW_editPathForOriginTest',
            description='Appends .html extension to universal paths, preserving files with other extensions (ex .css)',
            handler='index.handler',
            runtime=aws_lambda.Runtime.NODEJS_12_X,
            timeout=Duration.seconds(5),
            memory_size=128,
            role=lambda_execution_role,
            code=Code.bucket(
                bucket=Bucket.from_bucket_name(
                    self, "SourceBucketWWWEditPathForOriginLambda", bucket_name=webflow_aws_setup_bucket),
                key='lambda_function/cloudfront_www_edit_path_for_origin/package.zip'))

    def __create_cloud_front_www_edit_path_for_origin_lambda_version(
            self, cloud_front_www_edit_path_for_origin_lambda: aws_lambda.Function) -> aws_lambda.Version:
        return aws_lambda.Version(
            self, 'CloudFrontWWWEditPathForOriginVersion',
            lambda_=cloud_front_www_edit_path_for_origin_lambda,
            description='Latest Version')

    def __create_cloud_front_www_output(self, cloud_front_www: aws_cloudfront.Distribution):
        return core.CfnOutput(
            self, 'ARecord',
            value=cloud_front_www.distribution_domain_name,
            description='If your domain name is not hosted in AWS Route53, you have to create an A Record in your DNS',
            export_name='ARecord')

    def __create_route_53_record_group(
            self, route_53_hosted_zone: aws_route53.HostedZone, domain_names: List[str],
            cloud_front_distribution: aws_cloudfront.Distribution) -> List[aws_route53.ARecord]:
        return [
            aws_route53.RecordSet(
                self, domain_name.replace('.', '').upper(),
                record_type=aws_route53.RecordType.A,
                zone=route_53_hosted_zone,
                record_name=domain_name,
                target=aws_route53.RecordTarget.from_alias(alias_target=aws_route53_targets.CloudFrontTarget(
                    distribution=cloud_front_distribution
                ))
            ) for index, domain_name in enumerate(domain_names)
        ]

    def __create_ssl_certificate(
            self, route_53_hosted_zone: aws_route53.HostedZone, domain_name: str,
            alternative_domain_names: Optional[List[str]]) -> aws_certificatemanager.Certificate:
        return aws_certificatemanager.Certificate(
            self, 'SSLCertificate',
            domain_name=domain_name,
            validation=CertificateValidation.from_dns(hosted_zone=route_53_hosted_zone),
            subject_alternative_names=alternative_domain_names)

    def __create_s3_source_bucket(
            self, bucket_name: str, s3_trigger_lambda_function: aws_lambda.Function) -> aws_s3.Bucket:
        s3_bucket = aws_s3.Bucket(
            self, 'S3SourceBucket',
            bucket_name=bucket_name,
            block_public_access=BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True))
        s3_bucket.add_event_notification(
            EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(s3_trigger_lambda_function),
            (NotificationKeyFilter(prefix='artifacts/', suffix='.zip')))
        return s3_bucket

    def __create_s3_source_bucket_policy(
            self, s3_source_bucket: aws_s3.Bucket,
            cloud_front_origin_access_identity: aws_cloudfront.OriginAccessIdentity):
        return aws_s3.CfnBucketPolicy(
            self, 'S3SourceBucketPolicy',
            bucket=s3_source_bucket.bucket_name,
            policy_document=PolicyDocument(
                statements=[
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=['s3:GetObject'],
                        sid='1',
                        resources=[f'arn:aws:s3:::{s3_source_bucket.bucket_name}/*'],
                        principals=[aws_iam.ArnPrincipal(
                            f'arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '
                            f'{cloud_front_origin_access_identity.origin_access_identity_name}')])]))

    def __create_s3_trigger_lambda_execution_role(
            self, bucket_name: str, cloudfront_distribution: aws_cloudfront.Distribution) -> aws_iam.Role:
        return aws_iam.Role(
            self, "S3TriggerLambdaExecutionRole",
            assumed_by=ServicePrincipal('lambda.amazonaws.com'),
            description='Execution role that allows the lambda function to get the uploaded zip from S3, upload the '
                        'unpacked one and invalidate the CDN',
            role_name='S3TriggerLambdaExecutionRole',
            path='/',
            managed_policies=[ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')],
            inline_policies={
                's3_trigger_artifacts-upload-role': PolicyDocument(
                    statements=[PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=[
                            's3:PutObject', 's3:GetObject', 's3:ListObject', 's3:DeleteObject', 's3:HeadBucket',
                            'cloudfront:CreateInvalidation'],
                        resources=[
                            f'arn:aws:cloudfront::{Fn.ref("AWS::AccountId")}:distribution/'
                            f'{cloudfront_distribution.distribution_id}',
                            f'arn:aws:s3:::{bucket_name}',
                            f'arn:aws:s3:::{bucket_name}/*'])])})

    def __create_s3_trigger_lambda_function(
            self, webflow_aws_setup_bucket: str, execution_role: aws_iam.Role,
            cloud_front_distribution: aws_cloudfront.Distribution) -> aws_lambda.Function:
        return aws_lambda.Function(
            self, 'S3TriggerLambdaFunction',
            function_name='s3_trigger_artifacts-upload',
            description='Function responsible of unzipping the zip file uploaded and move the files to the '
                        'correct folder',
            handler='index.handler',
            role=execution_role,
            runtime=aws_lambda.Runtime.NODEJS_12_X,
            timeout=Duration.seconds(300),
            environment={'CDN_DISTRIBUTION_ID': cloud_front_distribution.distribution_id},
            code=Code.bucket(
                bucket=Bucket.from_bucket_name(self, "WebflowAWSSupport", bucket_name=webflow_aws_setup_bucket),
                key='lambda_function/s3_trigger_artifacts_upload/package.zip'))

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
