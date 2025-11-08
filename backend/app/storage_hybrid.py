"""
Hybrid storage implementation that uses temporary files for large videos
and database for metadata only. This prevents memory issues on free tier.
"""

import os
import json
import uuid
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Use temporary storage for actual video files
TEMP_DIR = Path("/tmp/roadcompare-videos")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Maximum size for in-memory operations (10MB)
MAX_MEMORY_SIZE = 10 * 1024 * 1024

def put_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream"):
    """
    Store video data efficiently:
    - Small files: Keep in memory
    - Large files: Stream to temporary storage
    """
    try:
        file_path = TEMP_DIR / object_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # For large files, write directly to disk
        if len(data) > MAX_MEMORY_SIZE:
            logger.info(f"📁 Writing large file ({len(data)} bytes) to disk: {object_name}")
            with open(file_path, 'wb') as f:
                f.write(data)
        else:
            # For smaller files, can keep in memory or write to disk
            logger.info(f"💾 Writing file ({len(data)} bytes) to disk: {object_name}")
            file_path.write_bytes(data)
        
        # Store metadata in database if available
        try:
            from .db import SessionLocal
            from .models import VideoMetadata
            
            db = SessionLocal()
            try:
                metadata = VideoMetadata(
                    key=object_name,
                    filename=Path(object_name).name,
                    content_type=content_type,
                    size=len(data),
                    storage_path=str(file_path),
                    created_at=datetime.utcnow()
                )
                db.add(metadata)
                db.commit()
                logger.info(f"✅ Metadata saved for {object_name}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not save metadata to database: {e}")
            # Continue anyway - file is saved
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to store {object_name}: {e}")
        raise

def get_bytes(object_name: str) -> bytes:
    """Retrieve video data from storage"""
    try:
        file_path = TEMP_DIR / object_name
        if file_path.exists():
            return file_path.read_bytes()
        
        # Fallback to database if file not found
        try:
            from .db import SessionLocal
            from .models import VideoMetadata
            
            db = SessionLocal()
            try:
                metadata = db.query(VideoMetadata).filter_by(key=object_name).first()
                if metadata and metadata.storage_path:
                    alt_path = Path(metadata.storage_path)
                    if alt_path.exists():
                        return alt_path.read_bytes()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not check database for {object_name}: {e}")
        
        logger.error(f"❌ File not found: {object_name}")
        return b""
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve {object_name}: {e}")
        return b""

def delete_prefix(prefix: str):
    """Delete all files with given prefix"""
    try:
        import shutil
        prefix_path = TEMP_DIR / prefix
        if prefix_path.exists():
            shutil.rmtree(prefix_path, ignore_errors=True)
            logger.info(f"🗑️ Deleted files with prefix: {prefix}")
        
        # Also clean up database entries
        try:
            from .db import SessionLocal
            from .models import VideoMetadata
            
            db = SessionLocal()
            try:
                db.query(VideoMetadata).filter(VideoMetadata.key.like(f"{prefix}%")).delete(synchronize_session=False)
                db.commit()
                logger.info(f"✅ Cleaned up database entries for prefix: {prefix}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not clean database entries: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to delete prefix {prefix}: {e}")

def presign_put(object_name: str) -> str:
    """Generate a presigned URL for upload (returns file path for now)"""
    return str(TEMP_DIR / object_name)

def presign_get(object_name: str) -> str:
    """Generate a presigned URL for download (returns file path for now)"""
    return str(TEMP_DIR / object_name)

def cleanup_old_files(days: int = 1):
    """Clean up old temporary files to save space"""
    try:
        import time
        from datetime import timedelta
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for file_path in TEMP_DIR.rglob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"🗑️ Deleted old file: {file_path}")
                    
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
