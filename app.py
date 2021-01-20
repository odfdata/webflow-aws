import yaml
from aws_cdk import core

from src.create_cloudformation_template import WebflowAWSStack

with open('configuration.yaml') as f:
    configuration = yaml.load(f, Loader=yaml.SafeLoader)

if __name__ == '__main__':
    app = core.App()
    WebflowAWSStack(app, configuration['stack_name'], configuration)
    result = app.synth()
