import boto3

if __name__ == '__main__':
    with open('../template_webflow_aws.yaml') as f:
        template_body = f.read()
    client = boto3.client('cloudformation')

    response = client.update_stack(
        StackName='CreateInCloudTest',
        TemplateBody=template_body,
        UsePreviousTemplate=False,
        Capabilities=['CAPABILITY_IAM'],
        Parameters=[
            {
                'ParameterKey': 'BucketName',
                'ParameterValue': 'test.createin.cloud'
            }
        ]

    )
    print(response)
