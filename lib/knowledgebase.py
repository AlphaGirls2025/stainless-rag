import boto3

KNOWLEDGE_BASE_NAME = 'stainlness'
BEDROCK_USER_ARN = 'arn:aws:iam::904375567622:user/stainlness-rag'
BEDROCK_ROLE_ARN = 'arn:aws:iam::904375567622:role/bedrock_role'
EMBEDDING_MODEL_ARN = 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
OPENSEARCH_COLLECTION_ARN = ''
OPENSEARCH_COLLECTION_ID = ''
OPENSEARCH_VECTOR_INDEX_NAME = 'vector-index-1024'
OPENSEARCH_VECTOR_FIELD_NAME = 'vector-index-1024'

bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

def create_knowledge_base(knowledge_base_name):
    create_kb_response = bedrock_agent.create_knowledge_base(
        name=knowledge_base_name,
        description="Knowledge Base created with S3 as data source and OpenSearch as vector store.",
        roleArn=BEDROCK_ROLE_ARN,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": EMBEDDING_MODEL_ARN,
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "embeddingDataType": "FLOAT32",
                        "dimensions": 1024
                    }
                }
            }
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": OPENSEARCH_COLLECTION_ARN,
                "vectorIndexName": OPENSEARCH_VECTOR_INDEX_NAME,
                "fieldMapping": {
                    "vectorField": OPENSEARCH_VECTOR_FIELD_NAME,
                    "textField": "text",
                    "metadataField": "metadata"
                }
            }
        }
    )

    knowledge_base_id = create_kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"Knowledge Base Created Successfully! ID: {knowledge_base_id}")
    return knowledge_base_id

def create_data_source(knowledge_base_id, data_source_name, s3_bucket_arn, s3_prefix):
    create_ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=knowledge_base_id,
        name=data_source_name,  # 你自己取名字
        description="Data source from S3 bucket",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": s3_bucket_arn,         # S3 bucket ARN
                "inclusionPrefixes": [s3_prefix] if s3_prefix else []  # Optional prefix
            }
        }
    )

    data_source_id = create_ds_response['dataSource']['dataSourceId']
    print(f"Data Source Created Successfully! ID: {data_source_id}")
    return data_source_id

def ingestion_job(knowledge_base_id, data_source_id):
    start_ingestion_response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=data_source_id
    )

    ingestion_job_id = start_ingestion_response['ingestionJob']['ingestionJobId']
    print(f"Ingestion Job Started! ID: {ingestion_job_id}")

    import time

    while True:
        response = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            ingestionJobId=ingestion_job_id
        )
        status = response['ingestionJob']['status']
        print(f"Ingestion job status: {status}")
        if status in ['COMPLETE', 'FAIL']:
            break
        time.sleep(5)  # 每 5 秒查一次
    print(f"Ingestion job completed with status: {status}")
    return ingestion_job_id, status