from typing import Optional, List

import click
import yaml

from webflow_aws.utils.base_utils import get_configuration


class ConfigMaker(object):

    def __init__(self, load_configuration: bool = False):
        self.CNAMEs: List = []
        self.domain_name: str = ""
        self.route_53_hosted_zone_id: Optional[str] = None
        self.route_53_hosted_zone_name: Optional[str] = None
        self.bucket_name: str = ""  # domain name  con account id in fondo
        self.stack_name: str = ""  # ex www-example-com   (è domain name)
        self.aws_profile_name: str = "default"  # chiederlo? eventualmente leggere quali disponibili e farli sceglere. Eventualmente usare boto3
        self.setup_bucket_name: str = ""   # webflow-aws-setup-bucket-{acc_id}  -  funzione in utils, usarla
        self.setup_stack_name: str = ""  # webflow-aws-setup-stack

        self._config_loaded: bool = load_configuration
        self._route53_zone_added: bool = False

        if load_configuration:
            self._load_config()

    def _load_config(self):
        """
        Loads the configuration and stores the values inside this class
        :return:
        """
        config = get_configuration()
        self.CNAMEs = config.get('CNAMEs', [])   # TODO put .get() on all elements
        self.bucket_name = config['bucket_name']
        self.domain_name = config['domain_name']
        self.domain_name = config['domain_name']
        self.route_53_hosted_zone_id = config['route_53_hosted_zone_id']
        self.route_53_hosted_zone_name = config['route_53_hosted_zone_name']
        self.stack_name = config['stack_name']
        self.aws_profile_name = config['aws_profile_name']
        self.setup_bucket_name = config['setup_bucket_name']
        self.setup_stack_name = config['setup_stack_name']

    def ask_cnames(self):
        """
        Asks for cnames to the final user
        :return:
        """
        # TODO ask first the main domain name, then cnames. Adjust variables
        incorrect = True
        while incorrect:
            user_input = click.prompt(f"Enter domain names that you plan to use with your website. "
                                      f"Separate them with commas (example.com,www.example.com)",
                                      default=','.join(self.CNAMEs) if len(','.join(self.CNAMEs)) > 0 else None,
                                      type=str)
            cnames = user_input.split(",")
            cnames = list(map(lambda c: c.strip(), cnames))
            cnames = list(filter(None, cnames))  # remove empty strings
            self.CNAMEs = cnames
            incorrect = len(self.CNAMEs) == 0

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
