# WcBot | Chatbot CMS WooCommerce Server App 2.0

## Overview

This document is target to the technical user who want to host the Chatbot CMS server on their own platform rather than [Chatbot CMS](https://chatbotcms.com/wcbot.html) provides. Below are the requirements before working on WcBot server:
- A WordPress site (version 4.4 or above) with WooCommerce (version 3.0 or above) installed.
- [WcBot plugin](https://chatbotcms.com/wcbot.html) is installed in the WordPress
- An AWS account
- Basic knowledge of shell base (Linux/Mac) command line interface
- How to setup NPM (Node Package Manager)
- Basic knowledge of Gulp.js
- Knowledge of AWS User account, role, policy
- Basic knowledge of Serverless framework

If you want to modify the WcBot server, you'll need:
- Knowledge of Python programming language and virtual environment
- Knowledge of Flask web programming
- Basic knowledge of AWS Lambda, S3, DynamoDB
- Knowledge of Rivescript

## The Story

This is whole new version of ChatbotCMS - WcBot server. The different of new version has two milestones.

1. All server codes are re-written in Python (version 3): Why choose Python? The answer is faster prototyping from idea. As the WcBot codes result, it reduced 49% line of codes. All asynchronous codes are eliminated. It means the logic is easily to understand, modify and upgrade.

2. WcBot server goes serverless (AWS Lambda): One immense benefit of a serverless infrastructure is that it improves economy of scale of operations. Now we don't need to worry about servers down, setup cluster servers, server loading suddenly raise, install server patches, setup load-balance/firewalls..

We spent lot of efforts to achieve this. The purpose is obvious... We can focus on logic. We can make better chatbots in coming time.

## The Source Codes

There has two main codesets in WcBot server:
1. WcBot Web Server
2. Shopping Cart Mini-website

### Codeset 1: WcBot Web Server

WcBot server has consisted of python codes in project root (*.py). To setup the develop environment, do below steps:

#### 1. Install the required frameworks

Suppose you're using Linux or Mac OS, do below steps:

- Install [NodeJS](https://nodejs.org/en/) version 6 or above
- Install [AWS command line interface](https://aws.amazon.com/cn/cli/)
- Install [serverless framework](https://serverless.com/)
- Install Python 3 virtual environment: ([virtualenv](https://help.dreamhost.com/hc/en-us/articles/115000695551-Installing-and-using-Python-s-virtualenv-using-Python-3))

#### 2. Create a new AWS IAM user

In (AWS console)[https://console.aws.amazon.com/iam], Create a non-administrator (for security reason) with below policy attachment:

```javascript
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:Describe*",
                "cloudformation:List*",
                "cloudformation:Get*",
                "cloudformation:PreviewStackUpdate",
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack"
            ],
            "Resource": "arn:aws:cloudformation:*:*:*/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogGroups"
            ],
            "Resource": "arn:aws:logs:*:*:log-group::log-stream:*"
        },
        {
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DeleteLogGroup",
                "logs:DeleteLogStream",
                "logs:DescribeLogStreams",
                "logs:FilterLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/*:log-stream:*",
            "Effect": "Allow"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DeleteRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::*:role/*-lambdaRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:GET",
                "apigateway:POST",
                "apigateway:PUT",
                "apigateway:DELETE"
            ],
            "Resource": [
                "arn:aws:apigateway:*::/restapis"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:GET",
                "apigateway:POST",
                "apigateway:PUT",
                "apigateway:DELETE"
            ],
            "Resource": [
                "arn:aws:apigateway:*::/restapis/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:GetFunction",
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:UpdateFunctionConfiguration",
                "lambda:UpdateFunctionCode",
                "lambda:ListVersionsByFunction",
                "lambda:PublishVersion",
                "lambda:CreateAlias",
                "lambda:DeleteAlias",
                "lambda:UpdateAlias",
                "lambda:GetFunctionConfiguration",
                "lambda:AddPermission",
                "lambda:InvokeFunction",
                "lambda:RemovePermission"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:Put*",
                "events:Remove*",
                "events:Delete*",
                "events:Describe*"
            ],
            "Resource": "arn:aws:events::*:rule/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:*"
            ],
            "Resource": "arn:aws:dynamodb:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::*"
        }
    ]
}
```

#### 3. Obtain the AWS Access Key & Secret

When the new AWS IAM user created, you have a time to obtain the Access Key and Access Key Secret. Please copy & paste the keys into a new file `secrets.yml` in project root. The final contents of that file should be below: (change the value inside the brackets and exclude the characters []):

```yml
default: &default
  <<: *default
  FLASK_APP: server.py
  FLASK_DEBUG: 0
  DEBUG_MODE: 1
  AWS_ACCESS_KEY_ID: [YOUR_ACCESS_KEY]
  AWS_SECRET_ACCESS_KEY: [YOUR_ACCESS_KEY_SECRET]
  AWS_REGION: [YOUR_AWS_REGION]
  AWS_BUCKET: [YOUR_S3_BUCKET_NAME]

dev:
  <<: *default

stage:
  <<: *default

prod:
  <<: *default
```

#### 4. Run the WcBot server for local development

If you want to modify the WcBot server codes, you may thinking how to run the WcBot server on local server. Of course you can do that on local machine rather than deploy to AWS Lambda every time after the codes changed. To run the WcBot server in local machine, do below steps:

1. Start the web server

Before starting the server, make sure the necessary variables are assigned. The commands should like this:

```bash
FLASK_APP="server.py"
FLASK_DEBUG=0
DEBUG_MODE=1
AMZACCESSKEY=[YOUR_ACCESS_KEY]
AMZACCESSSECRET=[YOUR_ACCESS_KEY_SECRET]
AMZREGION=[YOUR_AWS_REGION]
AMZBUCKET=[YOUR_S3_BUCKET_NAME]
npm start
```

_*Notes:*_
- The ACCESS KEY valuess are same as the above section 3.
- If you want to adjust the server settings, you can modify the startup script "scripts"->"start" in `package.json`.

2. Setup a HTTPS tunnel using [Ngrok](https://ngrok.com)

```bash
ngrok http 5000
```

3. Setup Messenger webhook

Go to Facebook developer portal. Create or use your existing Facebook App. For more info to setup Messenger webhook, please refer to [WcBot document](https://chatbotcms.com/docs/wcbot/facebook-webhook/).

Thus the chatting messages are redirect to your local web WcBot web server. You can modify and debug the WcBot server. When finish, deploy the server to AWS Lambda.

4. Create Dynamodb tables

_*IMPORTANT:*_ It needs to create Dynamodb tables at the first time. Type:

```bash
npm run createdb
```

_*NOTE:*_ This is a one-off command. You actually don't need run it twice or more.

5. Test the server operation

You should test the server is operating correctly before Messenger conversion. Run below scripts to test the server operation areas:

Test the Flask is running (server general test):
```bash
curl https://[your ngrok reports URL]/
WcBot is running
```

Server ping test (simulate ping test from WcBot plugin):
```bash
curl https://[your ngrok reports URL]/ping?q=chatbotcms-wcbot
pong
```

Database connection test:
```bash
curl https://[your ngrok reports URL]/test_db?q=chatbotcms-wcbot
Database connection okay.
```

WooCommerce connection test:
```bash
curl https://[your ngrok reports URL]/test_wc?subscribe_vk=[your subscription verify token]
WooCommerce connection with 'https://wcbotdemo.com' okay.
```
*IMPORTANT*: To obtain the subscription verify token, you'll need to install WcBot plugin in your Wordpress. Please refer to [this doc](https://chatbotcms.com/docs/wcbot/install/) for the installation processes.

#### 5. Deploy the WcBot to AWS Lambda

Before the deployment, you'll need to specify the deployment destination S3 bucket. Input the deployment bucket into the `serverless.yml` file as below:

```yml
...
  deploymentBucket:
    name: [Your Bucket Name]
...
```

Thanks to the [serverless framework](https://serverless.com), it is easy to deploy WcBot. Just type in project root:

```bash
sls deploy
```

Then copy & paste the first endpoint to Messenger webhook. 

### Codeset 2: Shopping Cart website

WcBot has built-in shopping cart mini site. It allows customers to view cart, input checkout info and order payment. The codes are consisted of HTML, Javascript and some static files (such as images, ico).

- HTML files are located in `/templates` directory.
- JS files are located in `/shopping-cart-src` directory.
- Static files are located in `/static` directory.

#### Build & deploy the shopping cart  website

The shopping cart building processes is to minify the source codes and copy to the destination directory `/shopping-cart/`. It uses Gulp to build. There has two main tasks defined in `gulpfile.js`:

Task 1: Build the shopping cart

Command:
```bash
gulp build-shopcart
```

Task 2: Deploy the shopping cart to S3

It uploads all site built files (HTML, CSS, JS) to AWS S3. Make sure the environment variables are defined before. The vars are:
- AMZACCESSKEY: Your IAM access key for S3 upload
- AMZACCESSSECRET: Your IAM access secret for S3 upload
- AMZREGION: Your S3 bucket region
- AMZBUCKET: Your S3 bucket name

Command:
```bash
gulp upload-s3
```

## Support

If you're purchased customer of WcBot and need support. Please join this [Facebook Group](https://www.facebook.com/groups/chatbotcms.wcbot/?source_id=131279084162186) to post the question.

## License

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
