import os
from typing import Dict

import boto3
import yaml
from botocore.exceptions import ClientError


def configuration_yaml_exists() -> bool:
    """
    Check if the configuration.yaml file exists.
    :return: True if the file exists, False otherwise
    """
    return os.path.exists('./webflow-aws-config.yaml')


def get_configuration() -> Dict:
    with open('./webflow-aws-config.yaml') as f:
        configuration = yaml.load(f, Loader=yaml.SafeLoader)
    return configuration


def get_setup_bucket_name(aws_region_name: str, aws_profile_name: str) -> str:
    session = boto3.session.Session(profile_name=aws_profile_name, region_name=aws_region_name)
    sts = session.client(service_name='sts')
    return f'webflow-aws-setup-bucket-{sts.get_caller_identity()["Account"]}'


def setup_bucket_exists(aws_region_name: str, aws_profile_name: str) -> (bool, str):
    session = boto3.session.Session(profile_name=aws_profile_name, region_name=aws_region_name)
    s3 = session.resource(service_name='s3')
    setup_bucket_name = get_setup_bucket_name(
            aws_profile_name=aws_profile_name, aws_region_name=aws_region_name)
    try:
        s3.meta.client.head_bucket(Bucket=setup_bucket_name)
        return True, setup_bucket_name
    except ClientError:
        # The bucket does not exist or you have no access.
        return False, None
