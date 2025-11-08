from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)
    sample_rate = Column(Integer, default=1)
    processed_frames = Column(Integer, default=0)
    runtime_seconds = Column(Float, default=0.0)
    summary_json = Column(JSON, default={})

    issues = relationship("Issue", back_populates="job", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    element = Column(String)
    issue_type = Column(String)
    severity = Column(String)
    confidence = Column(Float)
    first_frame = Column(Integer)
    last_frame = Column(Integer)
    base_crop_url = Column(Text)
    present_crop_url = Column(Text)
    reason = Column(Text)
    gps = Column(JSON, nullable=True)
    status = Column(String, default="open")

    job = relationship("Job", back_populates="issues")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(String, ForeignKey("issues.id"))
    label = Column(String)  # false_positive / confirm
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoMetadata(Base):
    __tablename__ = "video_metadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, index=True)
    filename = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    storage_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)






