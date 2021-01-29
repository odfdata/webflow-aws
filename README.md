# webflow-aws
An out-of-the box tool written in Python to deploy your [Webflow](https://webflow.com/) static website on AWS with a serverless architecture.

This tool uses the power of Cloud Formation to let you have your website up in minutes, with CDN and SSL Certificate enabled.

You can manage up to an infinite number of websites in the same AWS account, paying only for the real traffic. That's the beautiful part of serverless 😉

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

You are now ready to deploy your website. Start by going to **Webflow** and download your created website as a `.zip` file 
([click here](https://university.webflow.com/lesson/code-export) to see a detailed guide on how to do it).

Once you downloaded it, create a folder and put the `.zip` file inside. The folder's name doesn't matter, but make it meaningful for you. In our guide we will use the `example-website` folder

### Set up DNS record

Once your website is deployed, you will need a DNS Record to point to the file location. With `webflow-aws` you can do that in two ways:

* create a **hosted zone inside Route53** ([guide](https://medium.com/@dbclin/amazon-route-53-and-dns-whats-in-a-name-28fa4ac2826c)) on the AWS account you're using to deploy the website. In this scenario `webflow-aws` automatically manages the creation of all needed configuration, both for DNS Records and for SSL Certificate verification. 
* **[beta]** use a **custom DNS manager**, such as GoDaddy or your domain registrant. In this scenario, do not configure Route 53 properties and, once website is published, instructions with CNAMEs to set will be shown to you, so that you can manually configure them. Moreover, during first website deployment, you will need to publish a TXT record to verify your SSL Certificate.

With `webflow-aws` you can have one or more sub-domain point at your website, such as `example.com` and `www.example.com`.

In the `webflow-aws-config.yaml` file you will need to set the list of domains you would like to have your website pointing at. For example, you can have `example.com` and `www.example.com` enabled.

### Create webflow-aws-config.yaml file

The `webflow-aws-config.yaml` file allows you to customize the website you want to publish online. To create it, you
have to run this command:

```bash
webflow-aws create-config
```

It will guide you through the creation of the configuration. At the end of this procedure, you will see the
`webflow-aws-config.yaml` in your current directory.


#### Advanced creation

If you want to create the configuration file on your own, this is an example file you can customize:

```yaml
# REQUIRED parameters
bucket_name: "www.example.com"
domain_name: "example.com"
CNAMEs:
  - "www.example.com"
route_53_hosted_zone_id: "Z05234556KK8DIAQM"
route_53_hosted_zone_name: "example.com"
stack_name: "WwwExampleComStack"

# OPTIONAL parameters
aws_profile_name: "default"
```

- **bucket_name**: the AWS S3 bucket name you want to create. In most of the cases, it's equal to the domain name.
- **domain_name**: the domain name you want to use to expose your website.
- **CNAMEs**: the list of alternative domain names you want to redirect to the domain name.
- **route_53_hosted_zone_id**: the AWS Route53 hosted zone created. This  
  [guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingHostedZone.html) shows how to create a
  new hosted zone and get his `id`.
- **route_53_hosted_zone_name**: the AWS Route53 hosted zone domain name.
- **stack_name**: the name of the stack which all the resources will be grouped in. In most of the cases, it's the
  domain name without dots `.`
  
##### Optional Parameters

- **aws_profile_name**: (optional) the AWS profile name configured in AWS CLI. If you didn't specify it,
  the profile name is `default`

Place this file inside the `example-website/` folder previously created. The content of that folder should be

```bash
|—— example-website
|    |—— weblfow-files.zip
|    |—— webflow-aws-config.yaml
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