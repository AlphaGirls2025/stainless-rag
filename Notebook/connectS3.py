import boto3

# S3 客戶端
s3_client = boto3.client('s3', region_name='us-east-1')

bucket_name = "aiwave-hackathon-team-4"

def list_objects(bucket):
    response = s3_client.list_objects_v2(Bucket=bucket)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(obj['Key'])
    else:
        print("❗ Bucket裡面目前沒有檔案")

list_objects(bucket_name)
