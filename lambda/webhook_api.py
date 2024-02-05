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
    print("job_id", job_id)
    print("pr_num", prnum)

    # Check if the job_id is not empty
    if not job_id:
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
            "prnum": prnum
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Webhook data stored successfully!')
    }
