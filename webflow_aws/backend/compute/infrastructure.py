import builtins
import os

from aws_cdk import (
    aws_iam,
    aws_lambda,
    aws_lambda_nodejs as lambda_nodejs,
    aws_logs as logs,
    Duration
)
from constructs import Construct


class Compute(Construct):

    def __init__(self, scope: Construct, id_: builtins.str, configuration: dict):
        super().__init__(scope, id_)
        self.cloud_front_lambda_execution_role = self.__create_cloud_front_edit_path_for_origin_lambda_iam_role()
        self.cloud_front_edit_path_for_origin_lambda = self.__create_cloud_front_edit_path_for_origin_lambda(
            lambda_execution_role=self.cloud_front_lambda_execution_role)

    def __create_cloud_front_edit_path_for_origin_lambda_iam_role(self) -> aws_iam.Role:
        """
        Create the IAM role to be used by the Edit Path For Origin AWS lambda @ edge
        :return: The aws_iam.Role created
        """
        role = aws_iam.Role(
            self,
            'CloudFrontLambdaExecutionRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            path='/',
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')])
        role.assume_role_policy.add_statements(aws_iam.PolicyStatement(
            principals=[aws_iam.ServicePrincipal('edgelambda.amazonaws.com')],
            actions=['sts:AssumeRole']))
        return role

    def __create_cloud_front_edit_path_for_origin_lambda(
            self, lambda_execution_role: aws_iam.Role) -> lambda_nodejs.NodejsFunction:
        return lambda_nodejs.NodejsFunction(
            self,
            'CloudFrontEditPathForOrigin',
            description='Appends .html extension to universal paths, preserving files with other extensions (ex .css)',
            handler='lambdaHandler',
            entry=os.path.abspath("./backend/compute/src/index.editPathForOrigin.js"),
            deps_lock_file_path=os.path.abspath("./backend/compute/src/yarn.lock"),
            log_retention=logs.RetentionDays.TWO_WEEKS,
            runtime=aws_lambda.Runtime.NODEJS_16_X,
            architecture=aws_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(5),
            memory_size=128,
            role=lambda_execution_role,
        )
