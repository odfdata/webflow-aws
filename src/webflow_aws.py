import boto3
import click
import os
import glob

import yaml

from src.utils import configuration_yaml_exists, websites_folder_exists, get_configuration

s3_resource = boto3.resource('s3')


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
    click.echo('Going to create all the needed resources.')
    # check if the support stack is already created

    click.echo('Everything has been created. Now you need to run this command: cdk deploy')
