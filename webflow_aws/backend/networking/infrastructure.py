import builtins
import os
from pathlib import Path
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
    """
    The networking construct that contains all the AWS networking services and IAM roles used by them.
    """

    def __init__(self, scope: Construct, id_: builtins.str, configuration: dict):
        super().__init__(scope, id_)
        # load the existing route 53 hosted zone
        self.__load_route_53_hosted_zone(
            hosted_zone_id=configuration['route_53_hosted_zone_id'],
            hosted_zone_name=configuration['route_53_hosted_zone_name'])
        self.__create_cloud_front_origin_access_identity()
        self.__create_cloud_front_cache_policy()
        self.__create_ssl_certificate(
            route_53_hosted_zone=self.route_53_hosted_zone,
            domain_name=configuration['domain_name'], alternative_domain_names=configuration['CNAMEs'])
        self.__create_cloud_front_edit_path_for_origin_lambda_edge()
        self.__create_main_cloud_front_distribution(
            ssl_certificate=self.ssl_certificate, cache_policy=self.cloud_front_cache_policy,
            domain_name=configuration['domain_name'], alternative_domain_names=configuration['CNAMEs'],
            origin_access_identity=self.cloud_front_origin_access_identity,
            cloud_front_edit_path_for_origin_lambda_edge=self.cloud_front_edit_path_for_origin_lambda_edge,
            origin_bucket_name=configuration['bucket_name'])

    def __create_cloud_front_edit_path_for_origin_lambda_edge(self):
        """
        Create a new AWS Lambda @edge with all the correct permissions.
        """
        self.cloud_front_edit_path_for_origin_lambda_edge = aws_cloudfront.experimental.EdgeFunction(
            self,
            'CloudFrontEditPathForOriginLambdaEdge',
            description='Appends .html extension to universal paths, preserving files with other extensions (ex .css)',
            handler='editPathForOrigin.lambdaHandler',
            code=aws_lambda.Code.from_asset(
                Path(__file__).absolute().parent.parent.parent.__str__() +
                "/backend/networking/functions"
            ),
            log_retention=logs.RetentionDays.TWO_WEEKS,
            runtime=aws_lambda.Runtime.NODEJS_16_X,
            architecture=aws_lambda.Architecture.X86_64,
            timeout=Duration.seconds(5),
            memory_size=128
        )

    def __create_cloud_front_origin_access_identity(self):
        """
        Create a new CloudFront origin access identity
        """
        self.cloud_front_origin_access_identity = aws_cloudfront.OriginAccessIdentity(
            self,
            'CloudFrontOriginAccessIdentity',
            comment='cloudfront-only-acc-identity'
        )

    def __create_cloud_front_cache_policy(self):
        """
        Create a new CloudFront cache policy
        """
        self.cloud_front_cache_policy = aws_cloudfront.CachePolicy(
            self,
            'CloudFrontCachePolicy',
            comment='The CloudFront cache policy used by the DefaultCacheBehavior',
            default_ttl=Duration.seconds(1),
            max_ttl=Duration.seconds(1),
            min_ttl=Duration.seconds(1)
        )

    def __create_main_cloud_front_distribution(
            self, domain_name: str, alternative_domain_names: Optional[List[str]],
            origin_bucket_name: str, ssl_certificate: aws_certificatemanager.Certificate,
            cache_policy: aws_cloudfront.CachePolicy,
            origin_access_identity: aws_cloudfront.OriginAccessIdentity,
            cloud_front_edit_path_for_origin_lambda_edge: aws_cloudfront.experimental.EdgeFunction
    ):
        """
        Create the AWS CloudFront distribution for the domain name you want to configure

        :param domain_name: the main domain name you want to create a distribution for
        :param alternative_domain_names: the alternative domain names you want to include in your
        cloudfront distribution
        :param origin_bucket_name: the S3 bucket origin from which the content will be got from
        :param ssl_certificate: the SSL certificate previously configured
        :param cache_policy: the CDN cache policy previously configured
        :param origin_access_identity: the CDN origin access identity previously configured
        :param cloud_front_edit_path_for_origin_lambda_edge: the AWS lambda @edge previously configured
        """
        domain_names = alternative_domain_names if alternative_domain_names else []
        domain_names.append(domain_name)
        domain_names = set(domain_names)
        self.main_cloud_front_distribution = aws_cloudfront.Distribution(
            self,
            'CloudFrontMain',
            enabled=True,
            certificate=ssl_certificate,
            comment='CloudFront Distribution for your main static website',
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
            self, route_53_hosted_zone: aws_route53.IHostedZone, domain_name: str,
            alternative_domain_names: Optional[List[str]]):
        """
        Create the SSL certificate using the AWS Certificate Manager service

        :param route_53_hosted_zone: the route53 hosted zone that will be used to validate the SSL certificate
        :param domain_name: the domain name for which you want to create the SSL certificate for
        :param alternative_domain_names: the alternative domain names you want to create the SSL certificate for
        """
        self.ssl_certificate = aws_certificatemanager.Certificate(
            self,
            'SSLCertificate',
            domain_name=domain_name,
            validation=aws_certificatemanager.CertificateValidation.from_dns(hosted_zone=route_53_hosted_zone),
            subject_alternative_names=alternative_domain_names
        )

    def __load_route_53_hosted_zone(self, hosted_zone_id: str, hosted_zone_name: str):
        """
        Load the existent AWS Route53 hosted zone

        :param hosted_zone_id: the hosted zone id you want to load
        :param hosted_zone_name: the hosted zone name you want to load
        """
        self.route_53_hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
            self,
            'HostedZone',
            hosted_zone_id=hosted_zone_id,
            zone_name=hosted_zone_name
        )
