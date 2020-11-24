import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    package_name = event['package_name']
    dev_account = event['dev_account']
    tst_account = event['tst_account']
    
    sts = boto3.client('sts')
    dev_account = sts.assume_role(
        RoleArn='arn:aws:iam::652326971951:role/PorterLambda',
        RoleSessionName='dev_access'
    )
    
    tst_acct = sts.assume_role(
        RoleArn='arn:aws:iam::627041638206:role/PorterLambda',
        RoleSessionName='tst_access'
    )
    
    package_stack={'Resources':{}}
    
    package_config=get_package_config(dev_account)
    table_dict= read_tables(package_config,dev_account)
    raw_table_resource= get_table_resource(table_dict['raw_table'],tst_account)
    clean_table_resource= get_table_resource(table_dict['clean_table'], tst_account)
    
    package_stack['Resources']['RawTable']=raw_table_resource
    package_stack['Resources']['CleanTable']=clean_table_resource
    
    
    print(put_stack(package_name, package_stack, tst_acct))
    
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


def get_dev_stack(dev_account):
    dev_cloud_formation= boto3.client(
        'cloudformation',
        aws_access_key_id=dev_account['Credentials']['AccessKeyId'],
        aws_secret_access_key=dev_account['Credentials']['SecretAccessKey'],
        aws_session_token=dev_account['Credentials']['SessionToken']
    )
    
    stack_name='StackSet-PorterEnv-a793ffdf-974a-4803-b5a1-b6b74957607b'
    dev_stack=dev_cloud_formation.get_template(stack_name)
    
    
def get_package_config(dev_account):
    dev_cloud_formation= boto3.client(
        'codecommit',
        aws_access_key_id=dev_account['Credentials']['AccessKeyId'],
        aws_secret_access_key=dev_account['Credentials']['SecretAccessKey'],
        aws_session_token=dev_account['Credentials']['SessionToken']
    )
    
    raw_file=dev_cloud_formation.get_file(repositoryName='PorterETL', filePath='demo_opendata_taxitrips/assets.json')['fileContent']
    package_config=json.loads(raw_file)
    
    return package_config
    
    
def read_tables(package_config,account):
    glue= boto3.client(
        'glue',
        aws_access_key_id=account['Credentials']['AccessKeyId'],
        aws_secret_access_key=account['Credentials']['SecretAccessKey'],
        aws_session_token=account['Credentials']['SessionToken']
    )
    
    raw_table = glue.get_table(DatabaseName='porter_raw',Name=package_config['raw_table'])
    clean_table = glue.get_table(DatabaseName='porter_raw',Name=package_config['clean_table'])
    return {"raw_table": raw_table, "clean_table":clean_table}
    
def get_table_resource(table_config, account):
    resource={"Type" : "AWS::Glue::Table", "Properties" : { }}
    resource["Properties"]["CatalogId"] = account
    resource["Properties"]["DatabaseName"]= table_config["Table"]["DatabaseName"]
    resource["Properties"]["TableInput"]={}
    resource["Properties"]["TableInput"]["Name"] =  table_config["Table"]["Name"]
    resource["Properties"]["TableInput"]["Owner"] = table_config["Table"]["Owner"]
    resource["Properties"]["TableInput"]["Parameters"] = table_config["Table"]["Parameters"]
    resource["Properties"]["TableInput"]["PartitionKeys"] = table_config["Table"]["PartitionKeys"]
    resource["Properties"]["TableInput"]["Retention"] = table_config["Table"]["Retention"]
    resource["Properties"]["TableInput"]["StorageDescriptor"] = table_config["Table"]["StorageDescriptor"]
    resource["Properties"]["TableInput"]["TableType"] = table_config["Table"]["TableType"]
    return resource
    
def put_stack(stack_name,stack_body, account):
    cloud_formation= boto3.client(
        'cloudformation',
        aws_access_key_id=account['Credentials']['AccessKeyId'],
        aws_secret_access_key=account['Credentials']['SecretAccessKey'],
        aws_session_token=account['Credentials']['SessionToken']
    )

    new_stack=False
    #update or create?
    try:
        data = cloud_formation.describe_stacks(StackName = stack_name)
    except ClientError:
       new_stack=True
    
    if new_stack:
        print('new stack!')
        #response= cloud_formation.create_stack(StackName= stack_name, TemplateBody= json.dumps(stack_body), OnFailure='DELETE')
        response= cloud_formation.create_stack(StackName= stack_name, TemplateBody= json.dumps(stack_body))
    else:
        print('update')
        response= cloud_formation.update_stack(StackName= stack_name, TemplateBody= json.dumps(stack_body))
        
    return response