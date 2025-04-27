import re
import boto3

aoss = boto3.client('opensearchserverless', region_name='us-east-1')

def get_collection_arn_and_id(collection_name):
    list_response = aoss.list_collections()
    collection_id = None
    collection_arn = None
    for col in list_response['collectionSummaries']:
        if col['name'] == collection_name:
            collection_id = col['id']
            collection_arn = col['arn']
            break
    return collection_arn, collection_id

