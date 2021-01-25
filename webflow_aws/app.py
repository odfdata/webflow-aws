import boto3
from aws_cdk import core

from webflow_aws.create_cloudformation_template import WebflowAWSStack
from webflow_aws.utils import get_configuration, configuration_yaml_exists, setup_bucket_exists

aws_region_name = 'us-east-1'


if __name__ == '__main__':
    if not configuration_yaml_exists:
        print('configuration.yaml file doesn\'t exist')
        exit()
    # check if the setup bucket exists
    configuration = get_configuration()
    session = boto3.session.Session(
        profile_name=configuration.get('aws_profile_name', 'default'), region_name=aws_region_name)
    bucket_exists, webflow_aws_setup_bucket = setup_bucket_exists(
            aws_profile_name=configuration.get('aws_profile_name', 'default'), aws_region_name=aws_region_name)
    if not bucket_exists:
        print(f'The bucket setup bucket doesn\'t exist. Run webflow-aws setup to create it')
    else:
        app = core.App()
        WebflowAWSStack(app, configuration['stack_name'], webflow_aws_setup_bucket, configuration)
        result = app.synth()
