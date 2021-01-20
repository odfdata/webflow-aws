import glob
from time import sleep

import boto3
import click

from src.utils import configuration_yaml_exists, websites_folder_exists, get_configuration


@click.group()
def cli():
    # eventually we can set a --verbose @click.option at this level. See https://www.youtube.com/watch?v=kNke39OZ2k0
    # to get a demo
    pass


@cli.command(short_help='Create the configuration.yaml file')
def create_config():
    click.echo('Future release')


@cli.command(short_help="Publish your website in production")
def publish():
    # check if the configuration.yaml file exists
    if not configuration_yaml_exists():
        click.echo(
            'The configuration.yaml file doesn\'t exist. Read the README.md file to see how to create it', err=True)
        return
    # check if the websites folder exists
    if not websites_folder_exists():
        click.echo('The websites folder doesn\'t exist')
        return
    # check if there's a .zip file inside the websites folder
    zip_files = glob.glob('./websites/*.zip')
    if not zip_files:
        click.echo('The websites folder doesn\'t contain a .zip file')
        return
    configuration = get_configuration()
    s3_resource = boto3.resource(service_name='s3', profile_name=configuration.get('aws_profile_name', 'default'))
    s3_resource.meta.client.upload_file(
        Bucket=configuration['bucket_name'],
        Filename=zip_files[0],
        Key=f'artifacts/prod/package.zip')
    click.echo('Upload completed')


@cli.command(
    short_help='Create all the needed resources to publish your website. If the configuration.yaml file doesn\'t exist,'
               'it\'ll guide you through the creation process')
def setup():
    if not configuration_yaml_exists():
        click.echo(
            'The configuration.yaml file doesn\'t exist. Read the README.md file to see how to create it', err=True)
    configuration = get_configuration()
    cloudformation_client = boto3.client(
        service_name='cloudformation', profile_name=configuration.get('aws_profile_name', 'default'))
    click.echo('Going to create all the needed resources.')
    # check if the support stack is already created
    response = cloudformation_client.describe_stacks()
    already_created_stack = [
        stack_info for stack_info in response.get('Stacks', [])
        if stack_info.get('StackName', '') == configuration['support_stack_name']]
    if not already_created_stack:
        # create the support stack and wait for the creation complete
        with open('./templates/template_setup.yaml') as f:
            template_setup = f.read()
        response = cloudformation_client.create_stack(
            StackName=configuration['support_stack_name'],
            TemplateBody=template_setup,
            TimeoutInMinutes=5,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DO_NOTHING',
            Parameters=[
                {
                    'ParameterKey': 'BucketName',
                    'ParameterValue': configuration['support_bucket_name']
                }
            ]
        )
        stack_id = response['StackId']
        while True:
            response = cloudformation_client.describe_stacks(StackName=stack_id)
            if response['Stacks'][0]['StackStatus'] in ['CREATE_IN_PROGRESS']:
                sleep(5)
            elif response['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE']:
                break
        print('Stack successfully created')
    # going to upload all the needed lambda functions
    s3_resource = boto3.resource(service_name='s3', profile_name=configuration.get('aws_profile_name', 'default'))
    s3_resource.meta.client.upload_file(
        Bucket=configuration['support_bucket_name'],
        Filename='./src/lambda_function/cloudfront_www_edit_path_for_origin/cloudfront_www_edit_path_for_origin.zip',
        Key='lambda_function/cloudfront_www_edit_path_for_origin/package.zip'
    )
    s3_resource.meta.client.upload_file(
        Bucket=configuration['support_bucket_name'],
        Filename='./src/lambda_function/s3_trigger_artifacts_upload/s3_trigger_upload_artifacts.zip',
        Key='lambda_function/s3_trigger_artifacts_upload/package.zip'
    )
    click.echo('Everything has been created. Now you need to run this command: cdk deploy. If you configured a '
               'different aws_profile_name, you have to remember to specify the --profile {your_profile_name} '
               'parameter')
