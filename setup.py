from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='webflow-aws',
    version='1.1.1',
    description='Deploy your Webflow static website on AWS',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='CreateInCloud',
    author_email='it@createin.cloud',
    url='https://github.com/CreateInCloud/webflow-aws',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=requirements,
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
