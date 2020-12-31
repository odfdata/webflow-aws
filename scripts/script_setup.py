from time import sleep

import boto3

if __name__ == '__main__':
    cloudformation_client = boto3.client('cloudformation')
    s3_resource = boto3.resource('s3')
    with open('../template_setup.yaml') as f:
        template_setup = f.read()

    response = cloudformation_client.create_stack(
        StackName='WebflowAWSSupport',
        TemplateBody=template_setup,
        TimeoutInMinutes=5,
        Capabilities=['CAPABILITY_IAM'],
        OnFailure='DO_NOTHING'
    )
    stack_id = response['StackId']
    
    while True:
        response = cloudformation_client.describe_stacks(StackName=stack_id)
        if response['Stacks'][0]['StackStatus'] in ['CREATE_IN_PROGRESS']:
            sleep(5)
        elif response['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE']:
            break
    print('Stack successfully created')
    s3_resource.meta.client.upload_file(
        Bucket='webflow-aws-support',
        Filename='../lambda_function/s3_trigger_artifacts_upload/s3_trigger_upload_artifacts.zip',
        Key='lambda_function/s3_trigger_artifacts_upload/package.zip'
    )
