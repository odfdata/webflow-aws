# webflow-aws
Python code to deploy your [Webflow](https://webflow.com/) static website in AWS using Cloud Formation.

| :point_up:    | In this version, everything needs to be hosted in AWS, also your domain. |
|---------------|:-------------------------------------------------------------------------|

## Getting Started

### Prerequisites

In order to use this tool, you need to have:
- Access to an Active AWS account with all required permissions
- [NodeJS](https://nodejs.org/en/download/) 10.3.0 or later installed
  ([instructions](https://itsfoss.com/install-nodejs-ubuntu/)).
- Python 3.6 or later with pip3 installed ([instructions](https://docs.python-guide.org/starting/install3/linux/))
- AWS CLI installed and configured ([instructions](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)).

Finally, install the [AWS CDK command line tool](https://aws.amazon.com/cdk/?nc1=h_ls) with the following command

```bash
npm install -g aws-cdk
```

### Installation

You can download and install the latest version of this tool from the Python package index ([Pypi](https://pypi.org)) 
as follows:

```bash
pip3 install --upgrade webflow-aws
```

#### Advanced Installation

This section explains how build and install the Python package using the source code.

##### Clone repo & build your package

To use our tool, you have to clone this repository and install:

- Clone using HTTPs:
  ```bash
  git clone https://github.com/CreateInCloud/webflow-aws.git
  ```
- Clone using SSH:
  ```bash
  git clone git@github.com:CreateInCloud/webflow-aws.git 
  ```

After you cloned the repository, go inside the **webflow-aws** folder and generate the **.whl** package to be installed.

```bash
cd webflow-aws
python3 setup.py sdist bdist_wheel
```

##### Install the package

The build file (generate above) will be visible in the `dist/` folder. You will have a `wheel` and `tar.gz` file. 
If you previously installed another version of `webflow-aws`, it's recommended to uninstall it running the following
command:

```bash
pip3 uninstall dist/webflow_aws-{version}-py3-none-any.whl
```

Now you're ready to install the package inside the `dist/`folder. Without renaming them, you can install our tool on 
any computer with the following command

```bash
pip3 install dist/webflow_aws-{version}-py3-none-any.whl
```

You can find the `{version}` inside the `setup.py` file.

### Check if everything is working

At this point, on your target machine, you will be able to use the tool by typing `webflow-aws` from any folder. To see
the available commands, and check if it's correctly installed, run the following command

```bash
webflow-aws --help
```

## Deploy your website

Finally, you are ready to go to **Webflow** and download your `.zip` file 
([click here](https://university.webflow.com/lesson/code-export) to see the guide on how to download it).

Once you downloaded it, create a folder and put the `.zip` file inside. The folder's name doesn't matter.

### Create webflow-aws-config.yaml file

The `webflow-aws-config.yaml` file allows you to customize the website you want to publish online. This is an example
file you can customize:

```yaml
# REQUIRED parameters
bucket_name: "www.example.com"
domain_name: "www.example.com"
CNAMEs:
  - "example.com"
  - "www.example.com"
route_53_hosted_zone_id: "Z05234556KK8DIAQM"
route_53_hosted_zone_name: "example.com"
stack_name: "WwwExampleComStack"

# OPTIONAL parameters
aws_profile_name: "default"
support_bucket_name: "webflow-aws-support" 
support_stack_name: "WebflowAWSSupport"
```

- **bucket_name**: the AWS S3 bucket name you want to create. In most of the cases, it's equal to the domain name.
- **domain_name**: the domain name you want to use to expose your website.
- **CNAMEs**: the list of alternative domain names you want to redirect to the domain name.
- **route_53_hosted_zone_id**: the AWS Route53 hosted zone created. This is the 
  [guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingHostedZone.html) you can follow to create a
  new Route53 hosted zone and get his `id`.
- **route_53_hosted_zone_name**: the AWS Route53 hosted zone domain name.
- **stack_name**: the name of the stack which all the resources will be grouped in. In most of the cases, it's the
  domain name without dots `.`
  
#### Optional Parameters

- **aws_profile_name**: (optional) the AWS profile name configured in AWS CLI. If you didn't specify it,
  the profile name is `default`
- **support_bucket_name**: (optional) the AWS S3 bucket name created as support resource.
- **support_stack_name**: (optional) the AWS CloudFormation Stack name which all the resources will be grouped in.

Place this file inside the `websites/` folder previously created. The content of that folder should be
```bash
|—— www.example.com
|    |—— weblfow-files.zip
|    |—— configuration.yaml
```

### Publish your website

Now you are ready to publish your website online. 

Go inside the folder created before that contains:

+ `webflow-aws-config.yaml` file
+ `.zip` file

If it's the first time you are deploying it online, you have to call this command before:
```bash
webflow-aws setup
```
This command will create the Cloud Formation stack containing the support resources. 

After this command, you can execute:

```bash
webflow-aws publish
```

In 2 minutes, the content will be public available under the specified **domain names**.
  
## Next releases

We are planning to create the `webflow-aws create-config` command to guide the user through the creation of the 
configuration file setting all the customizable parameters without having him to create his own file.
