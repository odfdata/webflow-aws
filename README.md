# webflow-aws
Python code to deploy your [Webflow](https://webflow.com/) static website in AWS using Cloud Formation.
In this version, everything needs to be hosted in AWS, also your domain.

## Prerequisites

In order to use this tool, you have to install:
- [NodeJS](https://nodejs.org/en/download/) 10.3.0 or later.
- Python 3.6 or later
- AWS CLI and configure it.

After you installed them, you have to install the AWS CDK tool.

```bash
npm install -g aws-cdk
```

Finally, you're ready to use our tool.

## Available commands

You are ready to use the following commands.

- ```bash
  webflow-aws setup
  ```
  
  This command will create the Cloud Formation stack containing the support resources.

  After that command, you can execute

  ```bash
  cdk deploy
  ```

  To create the other Cloud Formation stack to prepare all the needed resources to expose your static
  WWW website created with Webflow.
  
- ```bash
  webflow-aws publish
  ```
  
  This command will upload the **.zip** file inside the **websites/** folder to the correct S3 Bucket,
  unzip the content of it and make it public available under the specified **domains**
  
## Next releases

- ```bash
  webflow-aws create-config
  ```
  
  This command will guide you through the creation of the configuration file and all the customizable parameters.

- ```bash
  webflow-aws setup
  ```
  
  There will be an update to this command, and it will integrate the **cdk deploy** command inside it.