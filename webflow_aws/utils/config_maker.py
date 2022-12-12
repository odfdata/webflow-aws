from typing import Optional, List

import boto3
import click
import yaml
from botocore.exceptions import ClientError

from webflow_aws.utils.base_utils import get_configuration, configuration_yaml_exists


class ConfigMaker(object):
    """
    Used to create / edit .yaml configuration file for a specific website.

    Attributes:
        domain_name: str                The main domain connected to this project
        CNAMEs: list                    List of CNAMEs of this project
        route_53_hosted_zone_id: str    id of route53 hosted zone
        route_53_hosted_zone_name: str  name of the route53 hosted zone
        aws_profile_name: str           name of the internal aws profile to be used for deploy
        bucket_name: str                name of the bucket where to deploy static files
        stack_name: str                 name of the Cloudformation Stack that handles this project
        setup_bucket_name: str          name of the bucket where to store setup files
        setup_stack_name: str           name of the Cloudformation stack that handles the setup part
    """

    def __init__(self):
        # default values are set at the end of ask() process if they have not been asked to user or are not in
        # a pre-existing configuration file
        self.domain_name: str = ""
        self.CNAMEs: List = []
        self.route_53_hosted_zone_id: Optional[str] = None
        self.route_53_hosted_zone_name: Optional[str] = None
        self.aws_profile_name: str = "default"
        self.bucket_name: str = ""
        self.stack_name: str = ""

        self._config_loaded: bool = False
        self._load_config()

    @property
    def route53_zone_added(self) -> bool:
        return True if self.route_53_hosted_zone_id and self.route_53_hosted_zone_name else False

    def _load_config(self):
        """
        Loads the configuration (if present) and stores the values inside this class
        """
        if configuration_yaml_exists():
            config = get_configuration()
            self._config_loaded = True
        else:
            config = {}
        self.CNAMEs = config.get('CNAMEs', [])
        self.domain_name = config.get('domain_name', "")
        self.route_53_hosted_zone_id = config.get('route_53_hosted_zone_id', None)
        self.route_53_hosted_zone_name = config.get('route_53_hosted_zone_name', None)
        self.bucket_name = config.get('bucket_name', "")
        self.stack_name = config.get('stack_name', "")
        self.aws_profile_name = config.get('aws_profile_name', "default")

    def _ask_domain_and_cnames(self):
        """
        Asks for domain name and cnames to the user
        :return:
        """
        # get domain name
        user_input = click.prompt(f"Principal {click.style('domain name', bold=True, underline=True)}"
                                  f" to use with your website, like example.com",
                                  default=self.domain_name if len(self.domain_name) > 0 else None,
                                  type=str)
        self.domain_name = user_input.lower()

        # get domain names, if user would like to
        resp = click.confirm(f"Do you want to add other domain names, such as www.example.com "
                             f"or test.example.com?", default=len(self.CNAMEs) > 0)
        if resp:
            incorrect = True
            while incorrect:
                user_input = click.prompt(f"  Enter the domains comma separated, like www.example.com,test.example.com",
                                          default=','.join(self.CNAMEs) if len(','.join(self.CNAMEs)) > 0 else None,
                                          type=str)
                cnames = user_input.split(",")
                cnames = list(map(lambda c: c.strip().lower(), cnames))
                cnames = list(filter(None, cnames))  # remove empty strings
                self.CNAMEs = cnames
                incorrect = len(self.CNAMEs) == 0
        else:
            self.CNAMEs = []

    def _ask_route53(self):
        """
        Asks user if he'd like to configure route53 or use custom DNS manager
        """
        # ask if user would like to add route53 as manager
        # get domain names, if user would like to
        click.echo(
            f"You have to use {click.style('Route53', bold=True, underline=True)} to manage your DNS "
            f"(you need to have a hosted zone already configured).")
        # resp = click.confirm(
        #     f"You can either choose to use {click.style('Route53', bold=True, underline=True)} "
        #     f"to manage your DNS (you need to have a hosted zone already configured) or to use your "
        #     f"{click.style('custom DNS Manager', bold=True, underline=True)} (at the "
        #     f"end of setup you will need to add few CNAMEs)\n"
        #     f"Would you like to use {click.style('Route53', bold=True, underline=True)} as DNS Manager?",
        #     default=True)
        # default=self.route_53_hosted_zone_id)
        # self._route53_zone_added = resp
        # if resp:
        user_input = click.prompt(f"Enter your Route53 Hosted Zone ID",
                                  default=self.route_53_hosted_zone_id if self.route_53_hosted_zone_id and len(
                                      self.route_53_hosted_zone_id) > 0 else None,
                                  type=str)
        self.route_53_hosted_zone_id = user_input
        # user_input = click.prompt(f"Finally, your Route53 Hosted Zone Name",
        #                           default=self.route_53_hosted_zone_name if self.route_53_hosted_zone_name and len(
        #                               self.route_53_hosted_zone_name) > 0 else None,
        #                           type=str)
        # self.route_53_hosted_zone_name = user_input

    def _ask_profile_name(self):
        """
        Ask final user for the aws profile name choosing between those available
        :return:
        """
        not_confirmed = True
        while not_confirmed:
            aws_profiles = boto3.session.Session().available_profiles
            user_input = click.prompt(f"Which {click.style('aws profile', bold=True, underline=True)} "
                                      f"would you like to use for deploy?",
                                      default=self.aws_profile_name if len(
                                          self.aws_profile_name) > 0 and self.aws_profile_name in aws_profiles else None,
                                      type=click.Choice(aws_profiles))
            boto3_session = boto3.session.Session(profile_name=user_input)
            profile_data = boto3_session.client('sts').get_caller_identity()
            aws_account_id = profile_data.get('Account')
            aws_user_arn = profile_data.get('Arn')
            resp = click.confirm(f"  Confirm profile {click.style(user_input, bold=True)} "
                                 f"for account {click.style(aws_account_id, bold=True)} "
                                 f"(user ARN {click.style(aws_user_arn, bold=True)})?", default=True)
            not_confirmed = not resp
        self.aws_profile_name = user_input

    def ask(self):
        """
        Asks for all the basic information to the user in order to create the correct configuration .yaml file
        :return: True if all the variables have been set correctly
        """
        click.echo("")
        click.echo(click.style("CREATE A NEW CONFIGURATION FILE", fg="green", underline=True))
        self._ask_domain_and_cnames()
        click.echo("")
        self._ask_profile_name()
        click.echo("")
        self._ask_route53()

        # these values can be asked as advanced option in a future improvement of this command
        boto3_session = boto3.session.Session(profile_name=self.aws_profile_name)
        route53_client = boto3_session.client(service_name='route53')
        profile_data = boto3_session.client('sts').get_caller_identity()
        aws_account_id = profile_data.get('Account')
        try:
            self.route_53_hosted_zone_name = route53_client.get_hosted_zone(
                Id=self.route_53_hosted_zone_id)['HostedZone']['Name']
        except ClientError:
            click.echo(click.style('Invalid Route53 Hosted Zone ID', bold=True, underline=True, fg="red"), err=True)
            return False
        self.bucket_name = f"{self.domain_name}-{aws_account_id}"
        self.stack_name = self.domain_name.replace(".", "-")
        return True

    def write_config(self):
        """
        Dump the configuration to a file called webflow-aws-config.yaml
        """
        config_dict = {
            'CNAMEs': self.CNAMEs,
            'bucket_name': self.bucket_name,
            'domain_name': self.domain_name,
            **({
                   'route_53_hosted_zone_id': self.route_53_hosted_zone_id,
                   'route_53_hosted_zone_name': self.route_53_hosted_zone_name
               } if self.route53_zone_added else {}),
            'stack_name': self.stack_name,
            'aws_profile_name': self.aws_profile_name,
        }
        with open('webflow-aws-config.yaml', 'w') as outfile:
            yaml.dump(config_dict, outfile)
