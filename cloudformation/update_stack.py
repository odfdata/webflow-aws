import boto3


if __name__ == '__main__':

    with open('../template.yaml') as f:
        template_body = f.read()
    client = boto3.client('cloudformation')

    print(client.validate_template(TemplateBody=template_body))

    response = client.update_stack(
        StackName='CreateInCloudTest',
        TemplateBody=template_body,
        UsePreviousTemplate=False,
        Capabilities=['CAPABILITY_IAM'],
        Parameters=[
            {
                'ParameterKey': 'BucketName',
                'ParameterValue': 'your_bucket_name'
            }
        ]

    )
    """
    
    """
    print(response)
