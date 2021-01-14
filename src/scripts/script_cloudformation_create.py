import boto3
import yaml

if __name__ == '__main__':
    with open('../../configuration.yaml') as f:
        configuration = yaml.load(f, Loader=yaml.SafeLoader)
    with open('../../templates/template_webflow_aws.yaml') as f:
        template_body = f.read()
    client = boto3.client('cloudformation')

    response = client.create_stack(
        StackName=configuration['stack_name'],
        TemplateBody=template_body,
        TimeoutInMinutes=5,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
        Parameters=[
            {
                'ParameterKey': 'BucketName',
                'ParameterValue': configuration['bucket_name']
            },
            {
                'ParameterKey': 'SupportBucketName',
                'ParameterValue': configuration['support_bucket_name']
            },
            {
                'ParameterKey': 'CNAMEs',
                'ParameterValue': ','.join(configuration['CNAMEs'])
            },
            {
                'ParameterKey': 'Route53HostedZoneName',
                'ParameterValue': configuration['route_53_hosted_zone_name']
            }
        ]
    )
    print(response)
