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
    prnum = body_content_dict['prnum']
    file_content = body_content_dict['file_content']
    repo_owner = body_content_dict['repo_owner']
    repo_name = body_content_dict['repo_name']

    print("PRNUM", prnum)
    print("File Content", file_content)
    print("Repo Owner", repo_owner)
    print("Repo Name", repo_name)

    # Check if the prnum and file_content are not empty
    if not prnum or not file_content or not repo_owner or not repo_name:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid input')
        }

    # Generate a job id with a timestamp
    job_id = f"job-{int(time.time())}"

    # Store the PRNUM, job id, timestamp, and file content in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('data')

    response = table.put_item(
        Item={
            'job_id': job_id,
            'timestamp': str(datetime.now()),
            'prnum': prnum,
            'file_content': file_content,
            "status": "pending",
            "reason": "",
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }
    )
    data = {
        "job_id": job_id,
        "timestamp": str(datetime.now()),
        "prnum": prnum,
        "file_content": file_content,
        "status": "pending",
        "reason": ""
    }

    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }
