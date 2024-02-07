# This file will simulate the API.
import json
import boto3
import time
from datetime import datetime


def lambda_handler(event, context):
    # Parse the incoming request
    body = event
    print("Body", body)
    # Assuming `body` is your dictionary
    body_content = body['body']

    # Try to parse the body_content into a dictionary
    try:
        body_content_dict = json.loads(body_content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid JSON input')
        }

    # Now you can access the values in the body_content_dict
    job_id = body_content_dict['job_id']
    prnum = body_content_dict['prnum']
    repo_owner = body_content_dict['repo_owner']
    repo_name = body_content_dict['repo_name']

    print("job_id", job_id)
    print("pr_num", prnum)
    print("Repo Owner", repo_owner)
    print("Repo Name", repo_name)

    # Check if the job_id and prnum is empty
    if not job_id or not prnum:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid input')
        }

    # Store the job id and timestamp in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('webhook_data')

    response = table.put_item(
        Item={
            'job_id': job_id,
            'timestamp': str(datetime.now()),
            "status": "pending",
            "prnum": prnum,
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Webhook data stored successfully!')
    }
