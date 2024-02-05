# This file will simulate the API.
import json
import boto3
import os
import urllib3
from boto3.dynamodb.conditions import Attr


def lambda_handler(event, context):

    # Store the PRNUM, job id, timestamp, and file content in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('webhook_data')

    # Get all the items from the table where status = pending
    response = table.scan(
        FilterExpression=Attr('status').eq('pending')
    )
    # loop through the response and call the api with job_id to get the status and data.
    for item in response['Items']:
        job_id = item['job_id']
        prnum = item['prnum']
        print("job_id", job_id)
        print("prnum", prnum)

        # Call the API to get the status and data
        url = os.environ['API_URL']
        http = urllib3.PoolManager()
        data = {
            "job_id": job_id
        }
        encoded_data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        response = http.request(
            'POST', url, body=encoded_data, headers=headers)
        print("API Response", response.data)

        # Update the status and data in DynamoDB
        api_response = json.loads(response.data)
        status = api_response['status']

        # if status is completed update the status.
        if status != "pending":
            markdown = api_response['markdown']
            response = table.update_item(
                Key={
                    'job_id': job_id
                },
                UpdateExpression="set status = :s",
                ExpressionAttributeValues={
                    ':s': status,
                },
                ReturnValues="UPDATED_NEW"
            )

            # Call GitHub webhook api.
            url = os.environ['WEBHOOK_API_URL']
            GitHub_Token = os.environ['GITHUB_TOKEN']
            http = urllib3.PoolManager()

            data = {
                "event_type": "webhook-event",
                "client_payload": {
                    "prnum": prnum,
                    "status": status,
                    "markdown": markdown,
                    'reason': api_response['reason']
                }
            }

            encoded_data = json.dumps(data)

            headers = {
                "Authorization": "token " + GitHub_Token,
                "Accept": "application/vnd.github.everest-preview+json",
                "Content-Type": "application/json"
            }

            response = http.request(
                "POST",
                url,
                body=encoded_data,
                headers=headers
            )
            print(response.status)
            print(response.data)
