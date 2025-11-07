import io
import os
from urllib.parse import urlparse
from pathlib import Path
from .config import settings

# Check if AWS credentials are available
HAS_AWS_CREDENTIALS = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))

# Support both MinIO (local) and AWS S3 (production)
USE_AWS_S3 = HAS_AWS_CREDENTIALS and ("amazonaws.com" in settings.s3_endpoint or settings.s3_endpoint.startswith("https://s3"))

# Fallback to local file storage if no credentials
USE_LOCAL_STORAGE = not HAS_AWS_CREDENTIALS and not os.getenv("MINIO_ROOT_USER")

if USE_LOCAL_STORAGE:
    print("⚠️ No S3/MinIO credentials found - using local file storage")
    STORAGE_DIR = Path("/tmp/roadcompare-storage")
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
elif USE_AWS_S3:
    import boto3
    from botocore.config import Config
    
    print("✅ Using AWS S3 for storage")
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
    if USE_LOCAL_STORAGE:
        # Return a placeholder URL for local storage
        return f"/local-storage/{object_name}"
    elif USE_AWS_S3:
        return s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': settings.s3_bucket, 'Key': object_name},
            ExpiresIn=3600
        )
    else:
        client = get_minio()
        return client.presigned_put_object(settings.s3_bucket, object_name, expires=3600)


def presign_get(object_name: str) -> str:
    if USE_LOCAL_STORAGE:
        # Return URL to the storage endpoint
        from .config import settings
        # Use the backend API URL to serve the file
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        return f"{base_url}{settings.api_prefix}/storage/{object_name}"
    elif USE_AWS_S3:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.s3_bucket, 'Key': object_name},
            ExpiresIn=3600
        )
    else:
        client = get_minio()
        return client.presigned_get_object(settings.s3_bucket, object_name, expires=3600)


def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    if USE_LOCAL_STORAGE:
        # Save to local file system
        file_path = STORAGE_DIR / object_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
    elif USE_AWS_S3:
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


def get_bytes(object_name: str) -> bytes:
    """Get object bytes from storage"""
    if USE_LOCAL_STORAGE:
        file_path = STORAGE_DIR / object_name
        if file_path.exists():
            return file_path.read_bytes()
        else:
            raise FileNotFoundError(f"Local file not found: {file_path}")
    elif USE_AWS_S3:
        response = s3_client.get_object(Bucket=settings.s3_bucket, Key=object_name)
        return response['Body'].read()
    else:
        client = get_minio()
        response = client.get_object(settings.s3_bucket, object_name)
        return response.read()


def delete_prefix(prefix: str):
    """Delete all objects with a given prefix"""
    if USE_LOCAL_STORAGE:
        # Delete local files
        import shutil
        prefix_path = STORAGE_DIR / prefix
        if prefix_path.exists():
            if prefix_path.is_dir():
                shutil.rmtree(prefix_path)
            else:
                prefix_path.unlink()
    elif USE_AWS_S3:
        # List all objects with prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix)
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_client.delete_object(Bucket=settings.s3_bucket, Key=obj['Key'])
    else:
        client = get_minio()
        # List and delete objects with prefix
        objects = client.list_objects(settings.s3_bucket, prefix=prefix, recursive=True)
        for obj in objects:
            client.remove_object(settings.s3_bucket, obj.object_name)




