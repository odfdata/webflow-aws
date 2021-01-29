import os
from pathlib import Path
from time import sleep
from typing import Dict

import boto3
import click
import yaml
from botocore.exceptions import ClientError
from tqdm import tqdm


def check_cloud_formation_setup_stack_creation(aws_region_name: str, aws_profile_name: str, stack_id: str) -> bool:
    # create the support stack and wait for the creation complete
    total_range = range(100)
    bar = tqdm(total=len(total_range), bar_format='{bar}')
    cloudformation_client = get_boto3_session(
        aws_profile_name=aws_profile_name, aws_region_name=aws_region_name).client(service_name='cloudformation')
    while True:
        response = cloudformation_client.describe_stacks(StackName=stack_id)
        if response['Stacks'][0]['StackStatus'] in ['CREATE_IN_PROGRESS']:
            for x in total_range:
                sleep(0.04)  # This is really hard work
                bar.update()
            bar.refresh()  # force print final state
        elif response['Stacks'][0]['StackStatus'] in ['CREATE_FAILED']:
            click.echo('Error creating the support stack', err=True)
            return False
        elif response['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE']:
            click.echo('')
            break
        bar.reset()  # reuse bar
    bar.close()  # close the bar permanently
    return True


def configuration_yaml_exists() -> bool:
    """
    Check if the configuration.yaml file exists.
    :return: True if the file exists, False otherwise
    """
    return os.path.exists('./webflow-aws-config.yaml')


def create_cloud_formation_setup_stack(
        aws_region_name: str, aws_profile_name: str, setup_bucket_name: str, setup_stack_name: str):
    # create the support stack and wait for the creation complete
    cloudformation_client = get_boto3_session(
        aws_profile_name=aws_profile_name, aws_region_name=aws_region_name).client(service_name='cloudformation')
    with open(Path(__file__).absolute().parent.parent.__str__() + '/templates/template_setup.yaml') as f:
        template_setup = f.read()
    response = cloudformation_client.create_stack(
        StackName=setup_stack_name,
        TemplateBody=template_setup,
        TimeoutInMinutes=5,
        Capabilities=['CAPABILITY_IAM'],
        OnFailure='DO_NOTHING',
        Parameters=[
            {
                'ParameterKey': 'BucketName',
                'ParameterValue': setup_bucket_name
            }
        ]
    )
    return response['StackId']


def get_boto3_session(aws_region_name: str, aws_profile_name: str):
    """

    :param aws_region_name:
    :param aws_profile_name:
    :return:
    """
    return boto3.session.Session(profile_name=aws_profile_name, region_name=aws_region_name)


def get_configuration() -> Dict:
    with open('./webflow-aws-config.yaml') as f:
        configuration = yaml.load(f, Loader=yaml.SafeLoader)
    return configuration


def get_setup_bucket_name(aws_region_name: str, aws_profile_name: str) -> str:
    """

    :param aws_region_name:
    :param aws_profile_name:
    :return:
    """
    sts = get_boto3_session(
        aws_region_name=aws_region_name, aws_profile_name=aws_profile_name).client(service_name='sts')
    return f'webflow-aws-setup-bucket-{sts.get_caller_identity()["Account"]}'


def setup_bucket_exists(aws_region_name: str, aws_profile_name: str) -> (bool, str):
    s3 = get_boto3_session(
        aws_region_name=aws_region_name, aws_profile_name=aws_profile_name).resource(service_name='s3')
    setup_bucket_name = get_setup_bucket_name(
            aws_profile_name=aws_profile_name, aws_region_name=aws_region_name)
    try:
        s3.meta.client.head_bucket(Bucket=setup_bucket_name)
        return True, setup_bucket_name
    except ClientError:
        # The bucket does not exist or you have no access.
        return False, None
