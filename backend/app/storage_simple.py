import os
from pathlib import Path

# Local file storage for videos and images
USE_LOCAL_STORAGE = True
STORAGE_DIR = Path("/tmp/roadcompare-storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def presign_put(object_name: str) -> str:
    """Return local file path for upload"""
    return str(STORAGE_DIR / object_name)

def presign_get(object_name: str) -> str:
    """Return local file path for download"""
    return str(STORAGE_DIR / object_name)

def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    """Save bytes to local file"""
    file_path = STORAGE_DIR / object_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)
    print(f"💾 Saved {len(data)} bytes to {file_path}")

def get_bytes(object_name: str) -> bytes:
    """Read bytes from local file"""
    file_path = STORAGE_DIR / object_name
    if file_path.exists():
        return file_path.read_bytes()
    return b""

def delete_prefix(prefix: str):
    """Delete all files with given prefix"""
    import shutil
    prefix_path = STORAGE_DIR / prefix
    if prefix_path.exists():
        shutil.rmtree(prefix_path, ignore_errors=True)
