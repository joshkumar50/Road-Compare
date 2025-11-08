"""
Database storage implementation using PostgreSQL and MongoDB
Replaces local file storage for production deployment
"""

import os
import base64
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import create_engine, Column, String, LargeBinary, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from gridfs import GridFS
import psycopg2
from .config import settings

logger = logging.getLogger(__name__)

# PostgreSQL setup for video metadata
Base = declarative_base()

class VideoStorage(Base):
    """PostgreSQL table for video storage"""
    __tablename__ = "video_storage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, index=True)  # s3-like key
    filename = Column(String)
    content_type = Column(String)
    size = Column(String)
    data = Column(LargeBinary)  # For small files
    data_url = Column(Text)  # For base64 encoded
    video_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class StorageManager:
    """Hybrid storage manager using PostgreSQL and MongoDB"""
    
    def __init__(self):
        # PostgreSQL for structured data
        self.engine = create_engine(settings.database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # MongoDB for large files (optional)
        self.mongo_client = None
        self.gridfs = None
        
        if settings.mongo_uri and settings.mongo_uri != "mongodb://localhost:27017/":
            try:
                self.mongo_client = MongoClient(settings.mongo_uri)
                self.mongo_db = self.mongo_client[settings.mongo_db]
                self.gridfs = GridFS(self.mongo_db)
                logger.info("✅ MongoDB GridFS connected for large file storage")
            except Exception as e:
                logger.warning(f"MongoDB not available, using PostgreSQL only: {e}")
    
    def put_video(self, key: str, data: bytes, content_type: str = "video/mp4") -> str:
        """Store video in database"""
        db: Session = self.SessionLocal()
        try:
            # For large videos, use MongoDB GridFS if available
            if self.gridfs and len(data) > 5 * 1024 * 1024:  # > 5MB
                # Store in MongoDB GridFS
                file_id = self.gridfs.put(
                    data,
                    filename=key,
                    content_type=content_type,
                    upload_date=datetime.utcnow()
                )
                
                # Store metadata in PostgreSQL
                video = VideoStorage(
                    key=key,
                    filename=key.split('/')[-1],
                    content_type=content_type,
                    size=str(len(data)),
                    data=None,  # Data is in MongoDB
                    video_metadata={"gridfs_id": str(file_id), "storage": "mongodb"}
                )
                db.add(video)
                db.commit()
                
                logger.info(f"✅ Video {key} stored in MongoDB GridFS ({len(data)} bytes)")
                return f"gridfs://{file_id}"
                
            else:
                # Store directly in PostgreSQL (for smaller files)
                # Convert to base64 for easier handling
                base64_data = base64.b64encode(data).decode('utf-8')
                data_url = f"data:{content_type};base64,{base64_data}"
                
                video = VideoStorage(
                    key=key,
                    filename=key.split('/')[-1],
                    content_type=content_type,
                    size=str(len(data)),
                    data=data,
                    data_url=data_url,
                    video_metadata={"storage": "postgresql"}
                )
                db.add(video)
                db.commit()
                
                logger.info(f"✅ Video {key} stored in PostgreSQL ({len(data)} bytes)")
                return f"postgresql://{video.id}"
                
        except Exception as e:
            logger.error(f"Error storing video {key}: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def get_video(self, key: str) -> Optional[bytes]:
        """Retrieve video from database"""
        db: Session = self.SessionLocal()
        try:
            video = db.query(VideoStorage).filter_by(key=key).first()
            
            if not video:
                logger.warning(f"Video {key} not found")
                return None
            
            # Check storage location
            metadata = video.video_metadata or {}
            
            if metadata.get("storage") == "mongodb" and self.gridfs:
                # Retrieve from MongoDB
                gridfs_id = metadata.get("gridfs_id")
                if gridfs_id:
                    file_data = self.gridfs.get(gridfs_id)
                    return file_data.read()
            
            # Retrieve from PostgreSQL
            if video.data:
                return video.data
            elif video.data_url:
                # Decode base64
                base64_str = video.data_url.split(',')[1]
                return base64.b64decode(base64_str)
            
            logger.error(f"No data found for video {key}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving video {key}: {e}")
            return None
        finally:
            db.close()
    
    def get_video_url(self, key: str) -> Optional[str]:
        """Get URL or data URL for video"""
        db: Session = self.SessionLocal()
        try:
            video = db.query(VideoStorage).filter_by(key=key).first()
            
            if not video:
                return None
            
            # If we have a data URL, return it directly
            if video.data_url:
                return video.data_url
            
            # Otherwise, create an API endpoint URL
            return f"/api/v1/storage/{video.id}"
            
        finally:
            db.close()
    
    def delete_video(self, key: str) -> bool:
        """Delete video from database"""
        db: Session = self.SessionLocal()
        try:
            video = db.query(VideoStorage).filter_by(key=key).first()
            
            if not video:
                return False
            
            # Delete from MongoDB if stored there
            metadata = video.video_metadata or {}
            if metadata.get("storage") == "mongodb" and self.gridfs:
                gridfs_id = metadata.get("gridfs_id")
                if gridfs_id:
                    self.gridfs.delete(gridfs_id)
            
            # Delete from PostgreSQL
            db.delete(video)
            db.commit()
            
            logger.info(f"✅ Video {key} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting video {key}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def list_videos(self, prefix: str = "") -> list:
        """List all videos with optional prefix filter"""
        db: Session = self.SessionLocal()
        try:
            query = db.query(VideoStorage)
            if prefix:
                query = query.filter(VideoStorage.key.like(f"{prefix}%"))
            
            videos = query.all()
            return [
                {
                    "key": v.key,
                    "filename": v.filename,
                    "size": v.size,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "storage": (v.video_metadata or {}).get("storage", "unknown")
                }
                for v in videos
            ]
        finally:
            db.close()

# Global storage instance
storage = StorageManager()

# Compatibility functions to match the existing interface
def presign_put(key: str) -> str:
    """Generate a put URL (compatibility)"""
    # For database storage, we handle uploads directly
    return f"/api/v1/storage/upload/{key}"

def presign_get(key: str) -> str:
    """Generate a get URL (compatibility)"""
    # Return URL or path for video retrieval
    url = storage.get_video_url(key)
    if url:
        return url
    # Fallback to temporary file for processing
    return save_to_temp_file(key)

def put_bytes(key: str, data: bytes, content_type: str = "video/mp4") -> bool:
    """Store bytes in database"""
    try:
        storage.put_video(key, data, content_type)
        return True
    except Exception as e:
        logger.error(f"Error storing {key}: {e}")
        return False

def get_bytes(key: str) -> Optional[bytes]:
    """Get bytes from database"""
    return storage.get_video(key)

def delete_prefix(prefix: str) -> int:
    """Delete all items with prefix"""
    videos = storage.list_videos(prefix)
    deleted = 0
    for video in videos:
        if storage.delete_video(video["key"]):
            deleted += 1
    return deleted

def save_to_temp_file(key: str) -> str:
    """Save video to temporary file for OpenCV processing"""
    import tempfile
    
    data = storage.get_video(key)
    if not data:
        raise FileNotFoundError(f"Video {key} not found")
    
    # Create temp file with proper extension
    extension = os.path.splitext(key)[1] or '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        tmp.write(data)
        return tmp.name

def cleanup_temp_file(path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Could not clean up temp file {path}: {e}")

# MongoDB-specific functions for analytics
def store_analysis_results(job_id: str, results: Dict[str, Any]):
    """Store analysis results in MongoDB for better querying"""
    if storage.mongo_db:
        try:
            collection = storage.mongo_db.analysis_results
            results["job_id"] = job_id
            results["timestamp"] = datetime.utcnow()
            collection.insert_one(results)
            logger.info(f"✅ Analysis results stored for job {job_id}")
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")

def get_analysis_results(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve analysis results from MongoDB"""
    if storage.mongo_db:
        try:
            collection = storage.mongo_db.analysis_results
            return collection.find_one({"job_id": job_id})
        except Exception as e:
            logger.error(f"Error retrieving analysis results: {e}")
    return None

def get_statistics() -> Dict[str, Any]:
    """Get storage statistics"""
    db: Session = storage.SessionLocal()
    try:
        total_videos = db.query(VideoStorage).count()
        total_size = db.query(VideoStorage.size).all()
        total_bytes = sum(int(s[0]) for s in total_size if s[0])
        
        stats = {
            "total_videos": total_videos,
            "total_size_mb": total_bytes / (1024 * 1024),
            "storage_types": {
                "postgresql": db.query(VideoStorage).filter(
                    VideoStorage.video_metadata['storage'].astext == 'postgresql'
                ).count(),
                "mongodb": db.query(VideoStorage).filter(
                    VideoStorage.video_metadata['storage'].astext == 'mongodb'
                ).count() if storage.gridfs else 0
            }
        }
        
        return stats
    finally:
        db.close()

logger.info("✅ Database storage system initialized")
