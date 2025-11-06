import io
from minio import Minio
from urllib.parse import urlparse
from .config import settings


def get_minio():
    parsed = urlparse(settings.s3_endpoint)
    secure = parsed.scheme == "https" if parsed.scheme else settings.s3_secure
    return Minio(
        parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
        access_key=None,  # anonymous if behind docker network with root user set via mc
        secret_key=None,
        secure=secure,
    )


def presign_put(object_name: str) -> str:
    client = get_minio()
    return client.presigned_put_object(settings.s3_bucket, object_name)


def presign_get(object_name: str) -> str:
    client = get_minio()
    return client.presigned_get_object(settings.s3_bucket, object_name)


def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    client = get_minio()
    data_io = io.BytesIO(data)
    client.put_object(settings.s3_bucket, object_name, data_io, length=len(data), content_type=content_type)






