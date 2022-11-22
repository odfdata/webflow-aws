import boto3
import aws_cdk as cdk

from backend.component import Backend
from backend.utils.base_utils import configuration_yaml_exists, get_configuration

app = cdk.App()

if not configuration_yaml_exists:
    print('configuration.yaml file doesn\'t exist')
    exit()
# load the configuration
configuration = get_configuration()

Backend(
    app,
    "WebflowAwsApp",
    configuration=configuration,
    env={"region": "us-east-1"}
)

app.synth()
