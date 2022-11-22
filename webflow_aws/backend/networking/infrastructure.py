import builtins
from typing import Optional, List

from aws_cdk import (
    aws_certificatemanager,
    aws_cloudfront,
    aws_route53,
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
