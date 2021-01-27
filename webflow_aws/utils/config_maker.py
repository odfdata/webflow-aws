import click
import yaml

from webflow_aws.utils.base_utils import get_configuration


class ConfigMaker(object):

    def __init__(self, load_configuration: bool = False):
        self.CNAMEs = []
        self.bucket_name = ""
        self.domain_name = ""
        self.route_53_hosted_zone_id = ""
        self.route_53_hosted_zone_name = ""
        self.stack_name = ""
        self.aws_profile_name = ""
        self.support_bucket_name = ""
        self.support_stack_name = ""
        self._config_loaded = load_configuration
        if load_configuration:
            self._load_config()

    def _load_config(self):
        """
        Loads the configuration and stores the values inside this class
        :return:
        """
        config = get_configuration()
        self.CNAMEs = config['CNAMEs']
        self.bucket_name = config['bucket_name']
        self.domain_name = config['domain_name']
        self.domain_name = config['domain_name']
        self.route_53_hosted_zone_id = config['route_53_hosted_zone_id']
        self.route_53_hosted_zone_name = config['route_53_hosted_zone_name']
        self.stack_name = config['stack_name']
        self.aws_profile_name = config['aws_profile_name']
        self.support_bucket_name = config['support_bucket_name']
        self.support_stack_name = config['support_stack_name']

    def ask_cnames(self):
        """
        Asks for cnames to the final user
        :return:
        """
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
            'route_53_hosted_zone_id': self.route_53_hosted_zone_id,
            'route_53_hosted_zone_name': self.route_53_hosted_zone_name,
            'stack_name': self.stack_name,
            'aws_profile_name': self.aws_profile_name,
            'support_bucket_name': self.support_bucket_name,
            'support_stack_name': self.support_stack_name
        }
        with open('webflow-aws-config.yaml', 'w') as outfile:
            yaml.dump(config_dict, outfile)
