from setuptools import setup, find_packages

# with open('requirements.txt') as f:
#     requirements = f.read().splitlines()

setup(
    name='webflow-aws',
    version='1.1.2',
    description='Deploy your Webflow static website on AWS',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='CreateInCloud',
    author_email='it@createin.cloud',
    url='https://github.com/CreateInCloud/webflow-aws',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'boto3~=1.16.46',
        'botocore~=1.19.46',
        'pyyaml~=5.3.1',
        'aws-cdk.core~=1.86.0',
        'aws-cdk.aws-certificatemanager~=1.86.0',
        'aws-cdk.aws-cloudfront~=1.86.0',
        'aws-cdk.aws-s3~=1.86.0',
        'aws-cdk.aws-s3-notifications~=1.86.0',
        'aws-cdk.aws-lambda~=1.86.0',
        'aws-cdk.aws-iam~=1.86.0',
        'aws-cdk.aws-cloudfront-origins~=1.86.0',
        'aws-cdk.aws-route53~=1.86.0',
        'aws-cdk.aws-route53-targets~=1.86.0',
        'Click~=7.1.2',
        'tqdm~=4.56.0',
        'emoji~=1.2.0'
    ],
    include_package_data=True,
    license="Apache License 2.0",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent'
    ],
    entry_points='''
        [console_scripts]
        webflow-aws=webflow_aws.webflow_aws_tool:cli
    '''
)
