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
        repo_owner = item['repo_owner']
        repo_name = item['repo_name']

        print("job_id", job_id)
        print("prnum", prnum)
        print("repo_owner", repo_owner)
        print("repo_name", repo_name)

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

        if response.status != 200:
            print("Error calling API")
            continue
        print("API Response", response.data)

        # Update the status and data in DynamoDB
        api_response = json.loads(response.data)
        status = api_response['status']

        # if status is completed update the status.
        if status != "pending":
            # check if key exists.
            if 'markdown' in api_response:
                markdown = api_response['markdown']
            else:
                markdown = ""

            if "github_token" in api_response:
                github_token = api_response['github_token']
            else:
                github_token = None

            response = table.update_item(
                Key={
                    'job_id': job_id
                },
                UpdateExpression="set #st = :s",
                ExpressionAttributeNames={
                    '#st': 'status',
                },
                ExpressionAttributeValues={
                    ':s': status,
                },
                ReturnValues="UPDATED_NEW"
            )

            # Call GitHub webhook api.
            if github_token is None:
                url = os.environ['WEBHOOK_API_URL']
                GitHub_Token = os.environ['GITHUB_TOKEN']
            else:
                # if github_token is present in the response use that.
                # Build the url with repo_owner and repo_name
                url = "https://api.github.com/repos/" + repo_owner + "/" + repo_name + "/dispatches"
                GitHub_Token = github_token

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
