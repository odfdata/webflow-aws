from typing import Optional, List

import boto3
import click
import yaml

from webflow_aws.utils.base_utils import get_configuration, configuration_yaml_exists, get_setup_bucket_name


class ConfigMaker(object):

    def __init__(self):
        # default values are set at the end of ask() process if they have not been asked to user or are not in
        # a pre-existing configuration file
        self.CNAMEs: List = []
        self.domain_name: str = ""
        self.route_53_hosted_zone_id: Optional[str] = None
        self.route_53_hosted_zone_name: Optional[str] = None
        self.aws_profile_name: str = "default"
        self.bucket_name: str = ""
        self.stack_name: str = ""
        self.setup_bucket_name: str = ""
        self.setup_stack_name: str = ""

        self._config_loaded: bool = False
        self._route53_zone_added: bool = False

        self._load_config()

    def _load_config(self):
        """
        Loads the configuration and stores the values inside this class
        :return:
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
        self.setup_bucket_name = config.get('setup_bucket_name', "")
        self.setup_stack_name = config.get('setup_stack_name', "webflow-aws-setup-stack")

    def _ask_domain_and_cnames(self):
        """
        Asks for domain name and cnames to the final user
        :return:
        """
        # get domain name
        user_input = click.prompt(f"Principal domain name to use with your website, "
                                  f"like example.com",
                                  default=self.domain_name if len(self.domain_name) > 0 else None,
                                  type=str)
        self.domain_name = user_input.lower()

        # get domain names, if user would like to
        resp = click.confirm(f"Do you want to add other domain names, such as www.example.com "
                             f"or test.example.com?")
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
        Asks if the user would like to configure route53 or use custom DNS manager
        :return:
        """
        # ask if user would like to add route53 as manager
        # get domain names, if user would like to
        resp = click.confirm(f"You can either choose to use Route53 to manage your DNS (you need to have "
                             f"a hosted zone already configured) or to use your custom DNS Manager (at the "
                             f"end of setup you will need to add few CNAMEs)\n"
                             f"Would you like to use Route53 as DNS Manager?")
        if resp:
            user_input = click.prompt(f"Enter your Route53 Hosted Zone ID",
                                      default=self.route_53_hosted_zone_id if self.route_53_hosted_zone_id and len(
                                          self.route_53_hosted_zone_id) > 0 else None,
                                      type=str)
            self.route_53_hosted_zone_id = user_input
            user_input = click.prompt(f"Finally, your Route53 Hosted Zone Name",
                                      default=self.route_53_hosted_zone_name if self.route_53_hosted_zone_name and len(
                                          self.route_53_hosted_zone_name) > 0 else None,
                                      type=str)
            self.route_53_hosted_zone_name = user_input

    def _ask_profile_name(self):
        not_confirmed = True
        while not_confirmed:
            aws_profiles = boto3.session.Session().available_profiles
            user_input = click.prompt(f"Which aws profile would you like to use for deploy?",
                                      default=self.aws_profile_name if len(
                                          self.aws_profile_name) > 0 and self.aws_profile_name in aws_profiles else None,
                                      type=click.Choice(aws_profiles))
            boto3_session = boto3.session.Session(profile_name=user_input)
            profle_data = boto3_session.client('sts').get_caller_identity()
            aws_account_id = profle_data.get('Account')
            aws_user_arn = profle_data.get('Arn')
            resp = click.confirm(f"  Confirm profile {user_input} for account {aws_account_id} "
                                 f"(user ARN {aws_user_arn})?", default=True)
            not_confirmed = not resp
        self.aws_profile_name = user_input

    def ask(self):
        """
        Does all the asks in the correct order to get all the information and fill the correct configuration
        :return:
        """
        self._ask_domain_and_cnames()
        click.echo("")
        self._ask_route53()
        click.echo("")
        self._ask_profile_name()

        # these values can be asked as advanced option in a future improvement of this command
        boto3_session = boto3.session.Session(profile_name=self.aws_profile_name)
        profle_data = boto3_session.client('sts').get_caller_identity()
        aws_account_id = profle_data.get('Account')
        self.bucket_name = f"{self.domain_name}-{aws_account_id}"
        self.stack_name = self.domain_name.replace(".", "-")
        self.setup_bucket_name = get_setup_bucket_name("us-east-1", self.aws_profile_name)
        self.setup_stack_name = 'webflow-aws-setup-stack'

    def write_config(self):
        """
        Dump the configuration to a file called webflow-aws-config.yaml
        :return:
        """
        config_dict = {
            'CNAMEs': self.CNAMEs,
            'bucket_name': self.bucket_name,
            'domain_name': self.domain_name,
            **({
                   'route_53_hosted_zone_id': self.route_53_hosted_zone_id,
                   'route_53_hosted_zone_name': self.route_53_hosted_zone_name
               } if self._route53_zone_added else {}),
            'stack_name': self.stack_name,
            'aws_profile_name': self.aws_profile_name,
            'setup_bucket_name': self.setup_bucket_name,
            'setup_stack_name': self.setup_stack_name
        }
        with open('webflow-aws-config.yaml', 'w') as outfile:
            yaml.dump(config_dict, outfile)
