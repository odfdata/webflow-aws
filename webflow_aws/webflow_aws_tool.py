import glob
import json
import os
import shutil
from time import sleep

import boto3
import click

from webflow_aws.utils import configuration_yaml_exists, get_configuration, get_setup_bucket_name, \
    create_cloud_formation_setup_stack
from webflow_aws.global_variables import AWS_REGION_NAME, SETUP_STACK_NAME


def check_if_configuration_yaml_exists():
    if not configuration_yaml_exists():
        click.echo(
            'The webflow-aws-config.yaml file doesn\'t exist. Read the README.md file to see how to create it',
            err=True)
        return False
    return True


@click.group()
def cli():
    # eventually we can set a --verbose @click.option at this level. See https://www.youtube.com/watch?v=kNke39OZ2k0
    # to get a demo
    pass


@cli.command(short_help='Create the configuration.yaml file')
def create_config():
    click.echo('Feature release')


@cli.command(short_help="Publish your website in production")
def publish():
    # check if the configuration.yaml file exists
    if not check_if_configuration_yaml_exists():
        return
    # check if there's a .zip file inside the websites folder
    zip_files = glob.glob('./*.zip')
    if not zip_files:
        click.echo('The folder doesn\'t contain a .zip file')
        return
    configuration = get_configuration()
    session = boto3.session.Session(
        profile_name=configuration.get('aws_profile_name', 'default'),
        region_name=AWS_REGION_NAME)
    # nano cdk.json
    with open('cdk.json', 'w') as outfile:
        json.dump({'app': 'python3 app.py'}, outfile)
    # cp app.py .
    dest = shutil.copyfile(os.path.dirname(os.path.abspath(__file__)) + '/app.py', 'app.py')
    # exec cdk deploy
    os.system(f'cdk deploy --profile {configuration.get("aws_profile_name", "default")} --require-approval never')
    os.remove('cdk.json')
    os.remove('app.py')
    s3_resource = session.resource(service_name='s3')
    s3_resource.meta.client.upload_file(
        Bucket=configuration['bucket_name'],
        Filename=zip_files[0],
        Key=f'artifacts/prod/package.zip')
    click.echo('Upload completed')


@cli.command(short_help='Create all the needed resources to publish your website')
def setup():
    # check if the configuration.yaml file exists
    if not check_if_configuration_yaml_exists():
        return
    configuration = get_configuration()
    session = boto3.session.Session(
        profile_name=configuration.get('aws_profile_name', 'default'),
        region_name=AWS_REGION_NAME)
    cloudformation_client = session.client(service_name='cloudformation')
    click.echo('Going to create all the needed resources.')
    # check if the setup stack is already created
    response = cloudformation_client.describe_stacks()
    already_created_stack = [
        stack_info for stack_info in response.get('Stacks', [])
        if stack_info.get('StackName', '') == SETUP_STACK_NAME]
    setup_bucket_name = get_setup_bucket_name(
        aws_region_name=AWS_REGION_NAME, aws_profile_name=configuration.get('aws_profile_name', 'default'))
    if not already_created_stack:
        stack_id = create_cloud_formation_setup_stack(
            aws_profile_name=configuration.get('aws_profile_name', 'default'), aws_region_name=AWS_REGION_NAME,
            setup_stack_name=SETUP_STACK_NAME, setup_bucket_name=setup_bucket_name)
        while True:
            response = cloudformation_client.describe_stacks(StackName=stack_id)
            if response['Stacks'][0]['StackStatus'] in ['CREATE_IN_PROGRESS']:
                sleep(5)
            elif response['Stacks'][0]['StackStatus'] in ['CREATE_FAILED']:
                click.echo('Error creating the support stack', err=True)
                return
            elif response['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE']:
                break
        click.echo('Stack successfully created')
    # going to upload all the needed lambda functions
    s3_resource = session.resource(service_name='s3')
    s3_resource.meta.client.upload_file(
        Bucket=setup_bucket_name,
        Filename=os.path.dirname(
            os.path.abspath(__file__)) + '/lambda_function/cloudfront_www_edit_path_for_origin/'
                                         'cloudfront_www_edit_path_for_origin.zip',
        Key='lambda_function/cloudfront_www_edit_path_for_origin/package.zip'
    )
    s3_resource.meta.client.upload_file(
        Bucket=setup_bucket_name,
        Filename=os.path.dirname(
            os.path.abspath(__file__)) + '/lambda_function/s3_trigger_artifacts_upload/s3_trigger_upload_artifacts.zip',
        Key='lambda_function/s3_trigger_artifacts_upload/package.zip'
    )
    click.echo('Everything has been created. Now you need to run this command: webflow-aws publish')
