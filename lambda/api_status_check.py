# This file will simulate the API.
import json
import boto3
import time
from datetime import datetime


markdown = '''
    
# AI AUDIT DETAILS

There is a significant accounting / balance discrepancy vulnerability in the withdrawal function, specifically in the "withdraw" function in the "contract.rs" file. This function does not dedupe lockup ids when withdrawing, leading to a vulnerability of calling multiple duplicate ids to drain the contract balance.

Here is the relevant code:

```rs
pub fn withdraw(deps: DepsMut, env: Env, info: MessageInfo, ids: Vec<u64>,) -> Result<Response, ContractError> {
    // ...
    for lockup in lockups {
        if lockup.owner != info.sender || env.block.time < lockup.release_timestamp {
            return Err(ContractError::Unauthorized { });
        }
        total_amount += lockup.amount;
        LOCKUPS.remove(deps.storage, lockup.id);
    }
    // ...
}
```

The for loop  `for lockup in lockups`  is intended to iterate different lockup ids. However, it does not dedupe in the case of duplicate lockup ids. So if the same lockup id is passed multiple times, the contract can be drained.

### Recommendation

To fix this issue, you can either only withdraw 1 id per message, or dedupe the ids vec. Here's an example of deduping the ids vec:

```rs
pub fn withdraw(deps: DepsMut, env: Env, info: MessageInfo, ids: Vec<u64>,) -> Result<Response, ContractError> {
    // ...
    let mut ids = ids;
    ids.sort();
    ids.dedup();

    for lockup_id in ids.clone().into_iter() {
    // ...
}
```

With this fix, the contract will only withdraw 1 time per lockup id.
    '''

def lambda_handler(event, context):
    # Parse the incoming request
    body = event
    print("Body", body)
    try:
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
        print("job_id", job_id)

        # Check if the prnum and file_content are not empty
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid input')
            }

        # Store the PRNUM, job id, timestamp, and file content in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('data')

        # get from dynamodb where job_id = job_id
        response = table.get_item(
            Key={
                'job_id': job_id
            }
        )
        data = response['Item']
        # delete key file_content from data
        del data['file_content']

        # check if status is pending.
        if response['Item']['status'] == "success":
            data['markdown'] = markdown
            return {
                'statusCode': 200,
                'body': json.dumps(data)
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps(data)
            }
    except Exception as e:
        print(f"Error: {e}")
        data = {
            "error": str(e),
            "status": "failed"
        }
        return {
            'statusCode': 400,
            'body': json.dumps(data)
        }