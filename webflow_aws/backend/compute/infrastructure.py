import builtins
import os
from pathlib import Path

from aws_cdk import (
    aws_cloudfront,
    aws_iam,
    aws_lambda,
    aws_lambda_nodejs as lambda_nodejs,
    aws_logs as logs,
    Duration,
    Fn
)
from constructs import Construct


class Compute(Construct):
    """
    The computing construct that contains all the AWS computing services and IAM roles used by them.
    """

    def __init__(
            self, scope: Construct, id_: builtins.str, cloud_front_distribution: aws_cloudfront.Distribution,
            configuration: dict):
        super().__init__(scope, id_)
        self.__create_s3_trigger_lambda_execution_role(
            bucket_name=configuration['bucket_name'], cloudfront_distribution=cloud_front_distribution)
        self.__create_s3_trigger_lambda_function(cloud_front_distribution=cloud_front_distribution)

    def __create_s3_trigger_lambda_execution_role(
            self, bucket_name: str, cloudfront_distribution: aws_cloudfront.Distribution):
        """
        Create the IAM role to be used by the AWS lambda function that manages the publication of the updates
        in the correct S3 bucket folder and invalidates the CDN.

        :param bucket_name: the bucket name the AWS lambda function will be allowed to access
        :param cloudfront_distribution: the CDN distribution the AWS lambda function will be allowed to invalidate
        """
        self.s3_trigger_lambda_execution_role = aws_iam.Role(
            self,
            "S3TriggerLambdaExecutionRole",
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            description='Execution role that allows the lambda function to get the uploaded zip from S3, upload the '
                        'unpacked one and invalidate the CDN',
            path='/',
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')],
            inline_policies={
                's3_trigger_artifacts-upload-role': aws_iam.PolicyDocument(
                    statements=[aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            's3:PutObject', 's3:GetObject', 's3:ListObject', 's3:DeleteObject', 's3:HeadBucket',
                            'cloudfront:CreateInvalidation'],
                        resources=[
                            f'arn:aws:cloudfront::{Fn.ref("AWS::AccountId")}:distribution/'
                            f'{cloudfront_distribution.distribution_id}',
                            f'arn:aws:s3:::{bucket_name}',
                            f'arn:aws:s3:::{bucket_name}/*'])])})

    def __create_s3_trigger_lambda_function(
            self, cloud_front_distribution: aws_cloudfront.Distribution
    ):
        """
        Create an AWS Lambda function that is responsible for unzipping the uploaded files, move the files to
        the correct folder and invalidate the CDN distribution.

        :param cloud_front_distribution: the cloudfront distribution the AWS lambda function will be allowed
        to invalidate. It will be set as environment variables named CDN_DISTRIBUTION_ID
        """
        print(Path(__file__).absolute().parent.parent.parent.__str__())
        self.s3_trigger_lambda = lambda_nodejs.NodejsFunction(
            self,
            'S3TriggerLambdaFunction',
            description='Function responsible of unzipping the zip file uploaded and move the files to the '
                        'correct folder',
            handler='lambdaHandler',
            entry=Path(__file__).absolute().parent.parent.parent.__str__() +
            "/backend/compute/functions/index.s3TriggerArtifactsUpload.js",
            deps_lock_file_path=Path(__file__).absolute().parent.parent.parent.__str__() +
            "/backend/compute/functions/yarn.lock",
            role=self.s3_trigger_lambda_execution_role,
            runtime=aws_lambda.Runtime.NODEJS_16_X,
            architecture=aws_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(300),
            memory_size=1024,
            bundling={
                "node_modules": ["adm-zip"],
                "minify": True
            },
            environment={'CDN_DISTRIBUTION_ID': cloud_front_distribution.distribution_id},
            log_retention=logs.RetentionDays.TWO_WEEKS
        )
