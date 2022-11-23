import builtins
import os
from typing import Optional, List

from aws_cdk import (
    aws_certificatemanager,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_lambda,
    aws_logs as logs,
    aws_route53,
    aws_s3,
    Duration
)
from constructs import Construct


class Networking(Construct):

    def __init__(self, scope: Construct, id_: builtins.str, configuration: dict):
        super().__init__(scope, id_)
        self.route_53_hosted_zone = self.__load_route_53_hosted_zone(
            hosted_zone_id=configuration['route_53_hosted_zone_id'],
            hosted_zone_name=configuration['route_53_hosted_zone_name'])
        self.cloud_front_origin_access_identity = self.__create_cloud_front_origin_access_identity()
        self.cloud_front_cache_policy = self.__create_cloud_front_cache_policy()
        self.ssl_certificate = self.__create_ssl_certificate(
            route_53_hosted_zone=self.route_53_hosted_zone,
            domain_name=configuration['domain_name'], alternative_domain_names=configuration['CNAMEs'])
        self.cloud_front_edit_path_for_origin_lambda_edge = aws_cloudfront.experimental.EdgeFunction(
            self,
            'CloudFrontEditPathForOriginLambdaEdge',
            description='Appends .html extension to universal paths, preserving files with other extensions (ex .css)',
            handler='lambdaHandler',
            code=aws_lambda.Code.from_asset(
                os.path.abspath("./webflow_aws/backend/networking/src/")),
            log_retention=logs.RetentionDays.TWO_WEEKS,
            runtime=aws_lambda.Runtime.NODEJS_16_X,
            architecture=aws_lambda.Architecture.X86_64,
            timeout=Duration.seconds(5),
            memory_size=128,
        )
        self.cloud_front_distribution_www = self.__create_cloud_front_www(
            ssl_certificate=self.ssl_certificate, cache_policy=self.cloud_front_cache_policy,
            domain_name=configuration['domain_name'], alternative_domain_names=configuration['CNAMEs'],
            origin_access_identity=self.cloud_front_origin_access_identity,
            cloud_front_edit_path_for_origin_lambda_edge=self.cloud_front_edit_path_for_origin_lambda_edge,
            origin_bucket_name=configuration['bucket_name'])

    def __create_cloud_front_origin_access_identity(self) -> aws_cloudfront.OriginAccessIdentity:
        return aws_cloudfront.OriginAccessIdentity(
            self,
            'CloudFrontOriginAccessIdentity',
            comment='cloudfront-only-acc-identity'
        )

    def __create_cloud_front_cache_policy(self) -> aws_cloudfront.CachePolicy:
        return aws_cloudfront.CachePolicy(
            self,
            'CloudFrontCachePolicy',
            comment='The CloudFront cache policy used by the DefaultCacheBehavior',
            default_ttl=Duration.seconds(1),
            max_ttl=Duration.seconds(1),
            min_ttl=Duration.seconds(1)
        )

    def __create_cloud_front_www(
            self, domain_name: str, alternative_domain_names: Optional[List[str]],
            origin_bucket_name: str, ssl_certificate: aws_certificatemanager.Certificate,
            cache_policy: aws_cloudfront.CachePolicy,
            origin_access_identity: aws_cloudfront.OriginAccessIdentity,
            cloud_front_edit_path_for_origin_lambda_edge: aws_cloudfront.experimental.EdgeFunction
    ) -> aws_cloudfront.Distribution:

        domain_names = alternative_domain_names if alternative_domain_names else []
        domain_names.append(domain_name)
        domain_names = set(domain_names)
        return aws_cloudfront.Distribution(
            self, 'CloudFrontWWW',
            enabled=True,
            certificate=ssl_certificate,
            comment='CloudFront Distribution for your WWW static website',
            domain_names=list(domain_names),
            http_version=aws_cloudfront.HttpVersion.HTTP2,
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_100,
            default_behavior=aws_cloudfront.BehaviorOptions(
                allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=aws_cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cache_policy,
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin=aws_cloudfront_origins.S3Origin(
                    bucket=aws_s3.Bucket.from_bucket_name(self, "OriginProd", bucket_name=origin_bucket_name),
                    origin_access_identity=origin_access_identity,
                    origin_path='/src/prod'
                ),
                edge_lambdas=[
                    aws_cloudfront.EdgeLambda(
                        event_type=aws_cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                        include_body=False,
                        function_version=cloud_front_edit_path_for_origin_lambda_edge)
                ]
            ),
            error_responses=[
               aws_cloudfront.ErrorResponse(
                    ttl=Duration.seconds(300),
                    response_page_path='/404.html',
                    http_status=403,
                    response_http_status=404)]
        )

    def __create_ssl_certificate(
            self, route_53_hosted_zone: aws_route53.HostedZone, domain_name: str,
            alternative_domain_names: Optional[List[str]]) -> aws_certificatemanager.Certificate:
        return aws_certificatemanager.Certificate(
            self,
            'SSLCertificate',
            domain_name=domain_name,
            validation=aws_certificatemanager.CertificateValidation.from_dns(hosted_zone=route_53_hosted_zone),
            subject_alternative_names=alternative_domain_names
        )

    def __load_route_53_hosted_zone(self, hosted_zone_id: str, hosted_zone_name: str) -> aws_route53.IHostedZone:
        return aws_route53.HostedZone.from_hosted_zone_attributes(
            self,
            'HostedZone',
            hosted_zone_id=hosted_zone_id,
            zone_name=hosted_zone_name
        )
