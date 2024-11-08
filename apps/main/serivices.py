# Python
import boto3

# Django
from django.conf import settings

acc_key = settings.AWS_ACCESS_KEY
region = settings.AWS_REGION_NAME
secret = settings.AWS_SECRET_ACCESS_KEY
input_bucket = settings.S3_BUCKET
output_transcribe_bucket = settings.S3_TRANSCRIBE_OUTPUT_BUCKET
output_translate_bucket = settings.S3_TRANSLATE_OUTPUT_BUCKET

s3_client = boto3.client(service_name='s3', aws_access_key_id=acc_key, aws_secret_access_key=secret, region_name=region)


def upload_progress_callback(bytes_transferred):
    print(f"Bytes transferred: {bytes_transferred}")


def s3_get_input_file_uri(obj_key):
    s3_uri = f"s3://{input_bucket}/{obj_key}"
    return s3_uri


def download_s3_file(obj_key):
    response = s3_client.get_object(Bucket=output_transcribe_bucket, Key=obj_key)
    return response
