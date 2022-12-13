import builtins

from aws_cdk import (
    aws_s3,
    RemovalPolicy
)
from constructs import Construct


class Storage(Construct):
    """
    The storage construct that contains all the AWS storage services.
    """

    def __init__(self, scope: Construct, id_: builtins.str, configuration: dict):
        super().__init__(scope, id_)
        self.s3_bucket = aws_s3.Bucket(
            self,
            'S3SourceBucket',
            bucket_name=configuration['bucket_name'],
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
