import glob
import json
import os
import shutil

import boto3
import click
import emoji as emoji

from webflow_aws.global_variables import AWS_REGION_NAME, GITHUB_REPOSITORY_URL
from webflow_aws.utils.base_utils import configuration_yaml_exists, get_configuration
from webflow_aws.utils.config_maker import ConfigMaker


@click.version_option()
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
    """
    Publish the zip file contained in the current folder. It uploads the file in the correct S3 bucket and once the
    upload is finished, a trigger starts and the CDN invalidation starts
    """
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
    os.system(f'cdk deploy --profile {configuration["aws_profile_name"]} --require-approval never --strict')
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
