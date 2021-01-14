import json

from cfn_flip import flip


def create_cloud_front_lambda_execution_role() -> dict:
    return {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": [
                                "lambda.amazonaws.com",
                                "edgelambda.amazonaws.com"
                            ]
                        },
                        "Action": [
                            "sts:AssumeRole"
                        ]
                    }
                ]
            },
            "Path": "/",
            "ManagedPolicyArns": [
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            ]
        }
    }


def create_s3_source_bucket() -> dict:
    return {
        "Type": "AWS::S3::Bucket",
        "DependsOn": [
            "S3TriggerLambdaInvokePermission"
        ],
        "Properties": {
            "BucketName": {
                "Ref": "BucketName"
            },
            "NotificationConfiguration": {
                "LambdaConfigurations": [
                    {
                        "Event": "s3:ObjectCreated:*",
                        "Filter": {
                            "S3Key": {
                                "Rules": [
                                    {
                                        "Name": "prefix",
                                        "Value": "artifacts/"
                                    },
                                    {
                                        "Name": "suffix",
                                        "Value": ".zip"
                                    }
                                ]
                            }
                        },
                        "Function": {
                            "Fn::GetAtt": [
                                "S3TriggerLambdaFunction",
                                "Arn"
                            ]
                        }
                    }
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        }
    }


def create_s3_trigger_lambda_execution_role() -> dict:
    return {
        'Type': 'AWS::IAM::Role',
        'Properties': {
            'AssumeRolePolicyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'Service': 'lambda.amazonaws.com'
                        },
                        'Action': ['sts:AssumeRole']
                    }
                ]
            },
            'Path': '/',
            'RoleName': 'S3TriggerLambdaExecutionRole',
            'Description': 'Execution role that allows the lambda function to get the uploaded zip from S3,'
                           ' upload the unpacked one and invalidate the CDN',
            'ManagedPolicyArns': ['arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'],
            'Policies': [
                {
                    'PolicyName': 's3_trigger_artifacts-upload-role',
                    'PolicyDocument': {
                        'Version': '2012-10-17',
                        'Statement': [
                            {
                                'Effect': 'Allow',
                                'Action': [
                                    's3:PutObject'
                                    's3:GetObject'
                                    's3:ListObject'
                                    's3:DeleteObject'
                                    's3:HeadBucket'
                                    'cloudfront:CreateInvalidation'
                                ],
                                "Resource": [
                                        {
                                            "Fn::Join": [
                                                "",
                                                [
                                                    "arn:aws:cloudfront::",
                                                    {
                                                        "Ref": "AWS::AccountId"
                                                    },
                                                    ":distribution/",
                                                    {
                                                        "Ref": "CloudFrontWWW"
                                                    }
                                                ]
                                            ]
                                        },
                                        {
                                            "Fn::Join": [
                                                "",
                                                [
                                                    "arn:aws:s3:::",
                                                    {
                                                        "Ref": "BucketName"
                                                    }
                                                ]
                                            ]
                                        },
                                        {
                                            "Fn::Join": [
                                                "",
                                                [
                                                    "arn:aws:s3:::",
                                                    {
                                                        "Ref": "BucketName"
                                                    },
                                                    "/*"
                                                ]
                                            ]
                                        }
                                    ]
                            }
                        ]
                    }
                }
            ]
        }
    }


def create_s3_trigger_lambda_invoke_permission() -> dict:
    return {
        "Type": "AWS::Lambda::Permission",
        "Properties": {
            "FunctionName": {
                "Fn::GetAtt": [
                    "S3TriggerLambdaFunction",
                    "Arn"
                ]
            },
            "Action": "lambda:InvokeFunction",
            "Principal": "s3.amazonaws.com",
            "SourceAccount": {
                "Ref": "AWS::AccountId"
            },
            "SourceArn": {
                "Fn::Sub": "arn:aws:s3:::${BucketName}"
            }
        }
    }


def create_s3_trigger_lambda_function() -> dict:
    return {
        "Type": "AWS::Lambda::Function",
        "Properties": {
            "FunctionName": "s3_trigger_artifacts-upload",
            "Description": "Function responsible of uzipping the zip file uploaded and move the files to the correct "
                           "folder",
            "Handler": "index.handler",
            "Runtime": "nodejs12.x",
            "Timeout": 300,
            "Role": {
                "Fn::GetAtt": [
                    "S3TriggerLambdaExecutionRole",
                    "Arn"
                ]
            },
            "Code": {
                "S3Bucket": {
                    "Ref": "SupportBucketName"
                },
                "S3Key": "lambda_function/s3_trigger_artifacts_upload/package1.zip"
            },
            "Environment": {
                "Variables": {
                    "CDN_DISTRIBUTION_ID": {
                        "Ref": "CloudFrontWWW"
                    }
                }
            }
        }
    }


def create_template(configuration: dict) -> dict:
    template = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': 'Cloud Formation template to deploy your Webflow static website in AWS.',
        'Parameters': {
            'BucketName': {'Type': 'String'},
            'SupportBucketName': {'Type': 'String'},
            'Route53HostedZoneName': {'Type': 'String'},
            'CNAMEs': {'Type': 'CommaDelimitedList', 'Description': 'The list of supported websites.'}
        },
        'Resources': {}
    }
    template['Resources']['S3TriggerLambdaExecutionRole'] = create_s3_trigger_lambda_execution_role()
    template['Resources']['S3TriggerLambdaFunction'] = create_s3_trigger_lambda_function()
    template['Resources']['S3SourceBucket'] = create_s3_source_bucket()
    return template


if __name__ == '__main__':
    output = flip(json.dumps(create_template(configuration={})))
    print(output)
    with open('../templates/template_webflow_aws.yaml') as f:
        some_yaml_or_json = flip(f.read())
    print(some_yaml_or_json)
    print(flip(some_yaml_or_json))
