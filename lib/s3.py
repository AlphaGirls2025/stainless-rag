import boto3

s3_client = boto3.client('s3', region_name='us-east-1')

def upload_file_to_s3(bucket_name, file_path, object_name):
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
    except Exception as e:
        print(f"Error uploading file: {e}")

# upload folder to s3
def upload_folder_to_s3(bucket_name, folder_path):
    import os
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            object_name = os.path.relpath(file_path, folder_path)
            upload_file_to_s3(bucket_name, file_path, object_name)

def list_buckets():
    response = s3_client.list_buckets()
    buckets = response['Buckets']
    # [print(f"Bucket Name: {bucket['Name']}") for bucket in buckets]
    return buckets

def get_objects(bucket_name, prefix=""):
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix  # 可選：只列出特定開頭的
    )
    # print(f"Objects in bucket '{bucket_name}':")
    objects = []
    if 'Contents' in response:
        for obj in response['Contents']:
            # print(f" - {obj['Key']}")
            objects.append(obj['Key'])
        return objects
    else:
        print("No objects found.")
        return []
        
# get s3 bucket-name arn
def get_s3_bucket_arn(bucket_name):
    return f"arn:aws:s3:::{bucket_name}"
# get s3 object arn
def get_s3_object_arn(bucket_name, object_name):
    return f"arn:aws:s3:::{bucket_name}/{object_name}"
# get s3 object url
def get_s3_object_url(bucket_name, object_name):
    return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

def get_s3_bucket_info(bucket_name):
    bucket_arn = get_s3_bucket_arn(bucket_name)
    objects = get_objects(bucket_name)
    object_arns = [get_s3_object_arn(bucket_name, obj) for obj in objects]
    object_urls = [get_s3_object_url(bucket_name, obj) for obj in objects]
    return {
        'bucket_name': bucket_name,
        'bucket_arn': bucket_arn,
        'objects': objects,
        'object_arns': object_arns,
        'object_urls': object_urls
    }