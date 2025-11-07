# Simplified storage stubs - we use base64 data URLs now, no external storage needed
USE_LOCAL_STORAGE = True
STORAGE_DIR = None

def presign_put(object_name: str) -> str:
    """Dummy function for compatibility"""
    return "data:image/png;base64,placeholder"

def presign_get(object_name: str) -> str:
    """Dummy function for compatibility"""
    return "data:image/png;base64,placeholder"

def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    """Dummy function for compatibility"""
    pass

def get_bytes(object_name: str) -> bytes:
    """Dummy function for compatibility"""
    return b""

def delete_prefix(prefix: str):
    """Dummy function for compatibility"""
    pass
