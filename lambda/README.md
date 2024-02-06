# AWS Lambda Deployment and Configuration Guide

This guide outlines the steps to deploy an AWS Lambda function from a zip file, change the handler for different Python scripts, install dependencies, create a shared permission for DynamoDB access, and enable a function URL with public access.

### Function purposes.
#### Actual
- **webhook.py**: A webhook endpoint that check the status of a job and send webhook to GitHub.
- **webhook_api.py**: A API endpoint to store job_id and status in DynamoDB.

#### Mock API / Simulated
- **api.py**: A MOCK API endpoint that returns a JSON response with a status code.
- **api_status_check.py**: A MOCK API to check the status of a job.
- **cron.py**: Simulate the status of a job and update the status in DynamoDB.


## Deploying a Lambda Function as a Zip File

1. **Prepare Your Lambda Function Package**
   - Ensure your Lambda function code is written and saved in files such as `api.py`, `webhook.py`, etc.
   - Install the required dependencies.

     ```bash
     pip install boto3 -t .
     ```

   - Zip your code and dependencies:

     ```bash
     zip -r function.zip .
     ```

2. **Upload Your Zip File to Lambda**
   - Navigate to the AWS Lambda console.
   - Choose or create a Lambda function.
   - On creating a new function, It will ask you to create new pemission, choose "Create a new role with basic Lambda permissions". But for rest of the functions, choose the existing role of first function.
   - Under the "Function code" section, select "Upload from" > ".zip file" and upload your `function.zip` file.
   - Click "Save" to deploy your code.

3. **Add Environment variables For webhook function**
    - In the Lambda console, select your function.
    - In the "Configuration" tab, find the "Environment variables" section and click "Edit".
    - Add the following environment variables:
        - `GITHUB_TOKEN`: Your GitHub token.
            - You can create a new token from https://github.com/settings/tokens
        - `WEBHOOK_API_URL`: GitHub webhook endpoint.
            - It will be like: `https://api.github.com/repos/{uername}/{repo}/dispatches`
            - Replace `{username}` with your GitHub username and `{repo}` with your repository name.
        - `API_URL`: The will be your API url which return the status of the job.

    - Click "Save" to apply your changes.
4. **Update execution time for lambda functions**
    - In the Lambda console, select your function.
    - In the "Configuration" tab, find the "General configuration" section and click "Edit".
    - Update the "Timeout" to 2 minutes and 30 seconds.
    - Click "Save" to apply your changes.


## Changing the Handler for Different Python Files

- When you have multiple entry points such as `api.py`, `webhook.py`, etc., specify the handler in the format `filename.method_name`.
    - **Note:** All functions have same method name `lambda_handler`.
- For example, if `api.py` contains a method named `lambda_handler`, set the handler to `api.lambda_handler`.
- Update the handler in the Lambda console under the "Runtime settings" section.

## Enabling Function URL with Public Access
- In the Lambda console, select your function.
- In the "Configuration" tab, find the "Function URL" section and click "Create function URL".
- Set the "Auth type" to "NONE" for public access without IAM authentication.
- Click "Save" to apply your changes.

**Note:** You do not need the URL for `webhook` and `cron` function.

- Once you get the url, i.e for `webhook_api` function, Update that to GitHub secret store.

## Create and configure DynamoDB table.
- Open the DynamoDB console at https://console.aws.amazon.com/dynamodb/
- Choose "Create table".
- The table name used in the functions are as follow:
    - `data` for `api`
    - `webhook_data` for `webhook_api` and others.
- Choose the primary key as `job_id` and click "Create".

## Create a shared permission for DynamoDB access
- Open the IAM console at https://console.aws.amazon.com/iam/
- Choose "Roles" and select the role used by the Lambda function.
    - It will be like `{functionname}-role-{id}`
- Click "Add Permissions" and Choose "Create Inline Policy" and then click json.
- Paste following content.
```json
        {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": "dynamodb:*",
			"Resource": "*"
		}
	]
}
```

- Click Next and enter the name of the policy and click "Create Policy".

## How to Schedule a Lambda Function.
- Open Amazon EventBridge console at https://us-east-1.console.aws.amazon.com/scheduler/home?region=us-east-1
- From the left pane, find "Schedules" and click it.
- Then click "Create schedule".
- Enter some friendly name.
- Choose "Occurance" as recurring from "Schedule pattern" section.
- Enter the valid cronjob expression.
    - https://crontab.guru/
- Set "Flexible time window" Off
- click Next.
- From "Target AP" Click "All APIs"
- Search "Lambda" and click it.
- Then search "invoke" and click the one which says "invoke"
- Choose your function
- Click "Next" and Finish it.

**Note:** You only need to schedule `cron` and `webhook` function.
