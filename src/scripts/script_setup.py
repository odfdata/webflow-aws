from time import sleep

import boto3
import yaml

if __name__ == '__main__':
    cloudformation_client = boto3.client('cloudformation')
    s3_resource = boto3.resource('s3')
    with open('../../configuration.yaml') as f:
        configuration = yaml.load(f, Loader=yaml.SafeLoader)
    with open('../../template_setup.yaml') as f:
        template_setup = f.read()
    response = cloudformation_client.create_stack(
        StackName=configuration['support_stack_name'],
        TemplateBody=template_setup,
        TimeoutInMinutes=5,
        Capabilities=['CAPABILITY_IAM'],
        OnFailure='DO_NOTHING',
        Parameters=[
            {
                'ParameterKey': 'BucketName',
                'ParameterValue': configuration['support_bucket_name']
            }
        ]
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
        Bucket=configuration['support_bucket_name'],
        Filename='../lambda_function/cloudfront_www_check_language/cloudfront_www_check_language.zip',
        Key='lambda_function/cloudfront_www_check_language/package.zip'
    )
    s3_resource.meta.client.upload_file(
        Bucket=configuration['support_bucket_name'],
        Filename='../lambda_function/cloudfront_www_edit_path_for_origin/cloudfront_www_edit_path_for_origin.zip',
        Key='lambda_function/cloudfront_www_edit_path_for_origin/package.zip'
    )
    s3_resource.meta.client.upload_file(
        Bucket=configuration['support_bucket_name'],
        Filename='../lambda_function/s3_trigger_artifacts_upload/s3_trigger_upload_artifacts.zip',
        Key='lambda_function/s3_trigger_artifacts_upload/package.zip'
    )
