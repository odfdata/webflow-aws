from aws_cdk import core

from src.create_cloudformation_template import WebflowAWSStack

if __name__ == '__main__':
    app = core.App()
    WebflowAWSStack(app, "CreateInCloudTest")
    result = app.synth()
