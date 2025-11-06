import io
import os
from urllib.parse import urlparse
from .config import settings

# Support both MinIO (local) and AWS S3 (production)
USE_AWS_S3 = "amazonaws.com" in settings.s3_endpoint or settings.s3_endpoint.startswith("https://s3")

if USE_AWS_S3:
    import boto3
    from botocore.config import Config
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=settings.s3_region,
        config=Config(signature_version='s3v4')
    )
else:
    from minio import Minio
    
    def get_minio():
        parsed = urlparse(settings.s3_endpoint)
        secure = parsed.scheme == "https" if parsed.scheme else settings.s3_secure
        access_key = os.getenv("MINIO_ROOT_USER") or os.getenv("S3_ACCESS_KEY")
        secret_key = os.getenv("MINIO_ROOT_PASSWORD") or os.getenv("S3_SECRET_KEY")
        return Minio(
            parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )


def presign_put(object_name: str) -> str:
    if USE_AWS_S3:
        return s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': settings.s3_bucket, 'Key': object_name},
            ExpiresIn=3600
        )
    else:
        client = get_minio()
        return client.presigned_put_object(settings.s3_bucket, object_name, expires=3600)


def presign_get(object_name: str) -> str:
    if USE_AWS_S3:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.s3_bucket, 'Key': object_name},
            ExpiresIn=3600
        )
    else:
        client = get_minio()
        return client.presigned_get_object(settings.s3_bucket, object_name, expires=3600)


def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    if USE_AWS_S3:
        s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=object_name,
            Body=data,
            ContentType=content_type
        )
    else:
        client = get_minio()
        data_io = io.BytesIO(data)
        client.put_object(settings.s3_bucket, object_name, data_io, length=len(data), content_type=content_type)






