import os
from typing import Dict

import boto3
import yaml


def configuration_yaml_exists() -> bool:
    """
    Check if the configuration.yaml file exists.
    :return: True if the file exists, False otherwise
    """
    return os.path.exists('./webflow-aws-config.yaml')


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
