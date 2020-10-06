import json
import boto3

def lambda_handler(event, context):
    #interpret incoming s3 key
    #fake plastic comment
    file_key=event['Records'][0]['s3']['object']['key']
    project=file_key.split('/')[0]
    provider=file_key.split('/')[1]
    dataset=file_key.split('/')[2]
    
    last_slash_location=file_key.rfind('/')
    job_name=file_key[0:last_slash_location]

    glue_client= boto3.client('glue')
    
    response = glue_client.start_job_run(JobName=job_name)
    
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
