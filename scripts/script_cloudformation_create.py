import boto3


if __name__ == '__main__':

    with open('../template_webflow_aws.yaml') as f:
        template_body = f.read()
    client = boto3.client('cloudformation')

    response = client.create_stack(
        StackName='CreateInCloudTest',
        TemplateBody=template_body,
        TimeoutInMinutes=5,
        Capabilities=['CAPABILITY_IAM'],
        OnFailure='DO_NOTHING'
    )
    print(response)
