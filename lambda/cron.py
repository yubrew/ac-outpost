# Process the API Simulate data.
import json
import boto3
import random
from boto3.dynamodb.conditions import Attr


def lambda_handler(event, context):
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('data')

    # Get items from the table where status is 'pending'
    response = table.scan(
        FilterExpression=Attr('status').eq('pending')
    )

    # Define possible statuses and reasons
    statuses = ['success', 'timeout', 'failed']
    reasons = ['Reason 1', 'Reason 2', 'Reason 3']

    # Update each item's status and add a reason
    for item in response['Items']:
        new_status = random.choice(statuses)
        reason = random.choice(reasons)

        table.update_item(
            Key={'job_id': item['job_id']},
            UpdateExpression='SET #status = :status, reason = :reason',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':reason': reason
            }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Status updated successfully!')
    }
