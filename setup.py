from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='webflow-aws',
    version='0.0.1',
    author='CreateInCloud',
    author_email='help@createin.cloud',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent'
    ],
    entry_points='''
        [console_scripts]
        webflow-aws=webflow_aws.webflow_aws_tool:cli
    '''
)
