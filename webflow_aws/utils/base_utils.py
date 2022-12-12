import os
from typing import Dict

import yaml


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
