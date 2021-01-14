# webflow-aws
Python code to deploy your [Webflow](https://webflow.com/) static website in AWS using Cloud Formation.
In this version, everything needs to be hosted in AWS, also your domain.

You can find two different templates:

- **template_setup.yaml**: creates all the required support resources used by template_webflow_aws.yaml (like the S3 bucket in which you can find the AWS Lambda function codes).
- **template_webflow_aws.yaml**: creates all the required resources to publish your website on Internet. 

## Template setup
The template will create the following resources:

- **AWS S3 Source Bucket**: the bucket which the AWS Lambda functions codes will be uploaded in. 

## Template Webflow AWS
The template will create the following resources:

* **AWS S3 Source Bucket**: the bucket which you'll upload your Webflow zip file in.
* **AWS Lambda Functions**:
    * S3 Trigger: function called each time new Webflow zip files are uploaded to the AWS S3 Source bucket. It unzips the file uploaded and move the files to the correct folder.
    * Edit path for origin: appends .html extension to universal paths, preserving files with other extensions (ex .css)
    * Check language: function that checks if the language has been set in the path request
* **AWS Certificate**: certificate SSL/TLS for your custom domain
* **AWS CloudFront Distribution**: distribution that points to the AWS S3 source bucket configured
* **AWS Route 53 record**: record of type A to point your domain to the Cloud Front Distribution

Obviously, it will create all the required IAM roles and policies to allow the resources to be triggered.