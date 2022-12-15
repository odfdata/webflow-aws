from setuptools import setup, find_namespace_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='webflow-aws',
    version='2.0.0',
    description='Deploy your Webflow static website on AWS',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='odfdata',
    author_email='fc@oracleofde.fi',
    url='https://github.com/odfdata/webflow-aws',
    packages=find_namespace_packages(),
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
