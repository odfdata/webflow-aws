import glob
import json
import os
import shutil

import boto3
import click
import emoji as emoji

from webflow_aws.global_variables import AWS_REGION_NAME, SETUP_STACK_NAME, GITHUB_REPOSITORY_URL
from webflow_aws.utils.base_utils import configuration_yaml_exists, get_configuration, get_setup_bucket_name, \
    create_cloud_formation_setup_stack, check_cloud_formation_setup_stack_creation
from webflow_aws.utils.config_maker import ConfigMaker


@click.group()
def cli():
    # eventually we can set a --verbose @click.option at this level. See https://www.youtube.com/watch?v=kNke39OZ2k0
    # to get a demo
    pass


@cli.command(short_help='Create the webflow-aws-config.yaml file')
def create_config():
    """
    Creates the configuration file. If a file is already present, asks the user if he'd like to overwrite it or keep
    the current configuration.
    """
    # check if configuration is not already present. In case it's present, ask the user confirmation to edit.
    config_exists = configuration_yaml_exists()
    if config_exists:
        proceed = click.confirm('A configuration file already exists. Would you like to overwrite it?')
    else:
        proceed = True
    if not proceed:
        return

    # ask for elements
    config_maker = ConfigMaker()
    configuration_finished = config_maker.ask()
    if configuration_finished:
        config_maker.write_config()


@cli.command(short_help="Publish your website in production")
@click.pass_context
def publish(ctx):
    # check if the configuration.yaml file exists
    if not configuration_yaml_exists():
        ctx.forward(create_config)
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
    os.system(f'cdk deploy --profile {configuration["aws_profile_name"]} --require-approval never')
    os.remove('cdk.json')
    os.remove('app.py')
    s3_resource = session.resource(service_name='s3')
    s3_resource.meta.client.upload_file(
        Bucket=configuration['bucket_name'],
        Filename=zip_files[0],
        Key=f'artifacts/prod/package.zip')
    click.echo('')
    click.echo('------------------------------------------------------------------------------------------------')
    click.echo('')
    click.echo(
        f'You website has been published and you can visit it on https://{configuration["domain_name"]}. '
        f'Thanks for using webflow-aws!\n'
        f'If you find our project useful, please {emoji.emojize(":star:")} us on github {GITHUB_REPOSITORY_URL}')


@cli.command(short_help='Create all the needed resources to publish your website')
@click.pass_context
def setup(ctx):
    # check if the configuration.yaml file exists
    if not configuration_yaml_exists():
        ctx.forward(create_config)
    configuration = get_configuration()
    session = boto3.session.Session(profile_name=configuration['aws_profile_name'], region_name=AWS_REGION_NAME)
    cloudformation_client = session.client(service_name='cloudformation')
    click.echo('Going to create all the needed resources.')
    # check if the setup stack is already created
    response = cloudformation_client.describe_stacks()
    already_created_stack = [
        stack_info for stack_info in response.get('Stacks', [])
        if stack_info.get('StackName', '') == SETUP_STACK_NAME]
    setup_bucket_name = get_setup_bucket_name(
        aws_region_name=AWS_REGION_NAME, aws_profile_name=configuration['aws_profile_name'])
    if not already_created_stack:
        stack_id = create_cloud_formation_setup_stack(
            aws_profile_name=configuration['aws_profile_name'], aws_region_name=AWS_REGION_NAME,
            setup_stack_name=SETUP_STACK_NAME, setup_bucket_name=setup_bucket_name)
        if not check_cloud_formation_setup_stack_creation(
                aws_profile_name=configuration['aws_profile_name'], aws_region_name=AWS_REGION_NAME,
                stack_id=stack_id):
            return
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
