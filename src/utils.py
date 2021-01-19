import os
from typing import Dict

import yaml


def configuration_yaml_exists() -> bool:
    """
    Check if the configuration.yaml file exists.
    :return: True if the file exists, False otherwise
    """
    return os.path.exists('./configuration.yaml')


def get_configuration() -> Dict:
    with open('./configuration.yaml') as f:
        configuration = yaml.load(f, Loader=yaml.SafeLoader)
    return configuration


def websites_folder_exists() -> bool:
    """
    Check if the websites/ folder exists.
    :return: True if the folder exists, False otherwise
    """
    return os.path.exists('./websites')
