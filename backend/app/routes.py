import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from .schemas import JobCreate, PresignRequest, PresignResponse, JobResult, JobSummary, IssueSchema, FeedbackIn
from .tasks import enqueue_job
from .db import get_db, Base, engine
from .models import Job, Issue, Feedback
from .config import settings
import os

# Choose storage backend based on environment
storage_mode = os.getenv("STORAGE_MODE", "hybrid").lower()
if storage_mode == "database":
    from .storage_database import put_bytes, presign_put
elif storage_mode == "simple":
    from .storage_simple import put_bytes, presign_put
else:
    # Use hybrid storage by default for better memory management
    from .storage_hybrid import put_bytes, presign_put
import uuid
import csv
import io
from pathlib import Path


Base.metadata.create_all(bind=engine)

api_router = APIRouter()


@api_router.get("/debug/config")
def debug_config():
    """Debug endpoint to check API configuration"""
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔧 Debug config requested")
        
        # Test database connection
        db_status = "connected"
        try:
            from .db import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Test Redis connection
        redis_status = "not configured"
        if settings.redis_url:
            try:
                from redis import Redis
                redis_conn = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
                redis_conn.ping()
                redis_status = "connected"
            except Exception as e:
                redis_status = f"error: {str(e)}"
        
        return {
            "api_prefix": settings.api_prefix,
            "frontend_url": settings.frontend_url,
            "cors_origins": settings.cors_origins,
            "database_status": db_status,
            "redis_status": redis_status,
            "use_database_storage": os.getenv("USE_DATABASE_STORAGE", "true"),
            "demo_mode": settings.demo_mode,
            "use_yolo": settings.use_yolo,
            "model_path": settings.model_path,
            "confidence_threshold": settings.confidence_threshold,
            "frame_rate": settings.frame_rate,
        }
    except Exception as e:
        logger.error(f"❌ Error in debug config: {e}")
        return {"error": str(e)}


@api_router.post("/uploads/presign", response_model=PresignResponse)
def presign_upload(data: PresignRequest):
    job_id = str(uuid.uuid4())
    base_key = f"jobs/{job_id}/base/{data.base_filename}"
    present_key = f"jobs/{job_id}/present/{data.present_filename}"
    return PresignResponse(
        base_url=presign_put(base_key), present_url=presign_put(present_key), job_id=job_id
    )


@api_router.post("/jobs")
async def create_job(
    base_video: UploadFile = File(...),
    present_video: UploadFile = File(...),
    sample_rate: int = Form(1),
    metadata: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new video analysis job with comprehensive validation"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📥 Received job creation request")
    logger.info(f"   - Base video: {base_video.filename if base_video else 'None'}")
    logger.info(f"   - Present video: {present_video.filename if present_video else 'None'}")
    logger.info(f"   - Sample rate: {sample_rate}")
    logger.info(f"   - Metadata: {metadata}")
    
    try:
        job_id = str(uuid.uuid4())
        
        # Validate videos are provided
        if not base_video or not present_video:
            logger.error(f"❌ Validation failed: Missing videos")
            raise HTTPException(400, "Both base_video and present_video are required")
        
        # Validate file types
        allowed_types = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska']
        base_type = base_video.content_type or "video/mp4"
        present_type = present_video.content_type or "video/mp4"
        
        if base_type not in allowed_types and not base_video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            logger.error(f"❌ Invalid base video type: {base_type}")
            raise HTTPException(400, f"Invalid base video format. Allowed: MP4, AVI, MOV, MKV")
        
        if present_type not in allowed_types and not present_video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            logger.error(f"❌ Invalid present video type: {present_type}")
            raise HTTPException(400, f"Invalid present video format. Allowed: MP4, AVI, MOV, MKV")
        
        # Validate sample rate
        if sample_rate < 1 or sample_rate > 30:
            logger.error(f"❌ Invalid sample rate: {sample_rate}")
            raise HTTPException(400, "Sample rate must be between 1 and 30")
        
        # If direct upload provided, stream to object storage
        base_key = f"jobs/{job_id}/base/{base_video.filename}"
        present_key = f"jobs/{job_id}/present/{present_video.filename}"
        
        logger.info(f"📤 Uploading videos for job {job_id}")
        
        # Stream videos to storage with chunked reading for memory efficiency
        max_size = 100 * 1024 * 1024  # 100MB limit for free tier
        chunk_size = 1024 * 1024  # 1MB chunks
        
        # Process base video
        base_size = 0
        base_chunks = []
        while True:
            chunk = await base_video.read(chunk_size)
            if not chunk:
                break
            base_size += len(chunk)
            if base_size > max_size:
                logger.error(f"❌ Base video too large: {base_size} bytes")
                raise HTTPException(400, f"Base video exceeds maximum size of 100MB")
            base_chunks.append(chunk)
        
        base_content = b''.join(base_chunks)
        
        # Process present video
        present_size = 0
        present_chunks = []
        while True:
            chunk = await present_video.read(chunk_size)
            if not chunk:
                break
            present_size += len(chunk)
            if present_size > max_size:
                logger.error(f"❌ Present video too large: {present_size} bytes")
                raise HTTPException(400, f"Present video exceeds maximum size of 100MB")
            present_chunks.append(chunk)
        
        present_content = b''.join(present_chunks)
        
        # Store videos
        try:
            put_bytes(base_key, base_content, base_type)
            put_bytes(present_key, present_content, present_type)
        except Exception as e:
            logger.error(f"❌ Failed to store videos: {e}")
            raise HTTPException(500, f"Failed to store videos: {str(e)}")
        logger.info(f"✅ Videos uploaded for job {job_id}")

        # Parse and validate metadata
        meta_json = {}
        if metadata:
            try:
                meta_json = json.loads(metadata)
                if not isinstance(meta_json, dict):
                    raise ValueError("Metadata must be a JSON object")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid metadata JSON: {e}")
                raise HTTPException(400, f"Invalid metadata JSON: {str(e)}")

        job = Job(id=job_id, status="queued", metadata_json=meta_json, sample_rate=sample_rate)
        db.add(job)
        db.commit()
        logger.info(f"✅ Job {job_id} created in database")

        enqueue_job({
            "job_id": job_id,
            "base_key": base_key,
            "present_key": present_key,
            "sample_rate": sample_rate,
            "metadata": meta_json,
        })
        logger.info(f"✅ Job {job_id} enqueued for processing")

        return {"job_id": job_id, "status": "queued", "message": "Job created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating job: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to create job: {str(e)}")


@api_router.get("/jobs", response_model=List[JobSummary])
def list_jobs(db: Session = Depends(get_db)):
    """List all jobs with their status and summary"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("📋 Fetching all jobs...")
        
        # More efficient query with limited columns
        jobs = db.query(
            Job.id,
            Job.status,
            Job.processed_frames,
            Job.runtime_seconds,
            Job.summary_json
        ).order_by(Job.created_at.desc()).limit(100).all()  # Reduced limit for free tier
        
        logger.info(f"✅ Found {len(jobs)} jobs")
        
        # Handle empty result set
        if not jobs:
            return []
        
        return [
            JobSummary(
                id=j.id,
                status=j.status,
                processed_frames=j.processed_frames or 0,
                runtime_seconds=j.runtime_seconds or 0,
                summary=j.summary_json or {},
            )
            for j in jobs
        ]
    except Exception as e:
        logger.error(f"❌ Error fetching jobs: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty list instead of 500 error for better UX
        return []


@api_router.get("/jobs/{job_id}/results", response_model=JobResult)
def get_results(job_id: str, db: Session = Depends(get_db)):
    """Get job results with comprehensive error handling"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔍 Fetching results for job {job_id}")
        
        # Validate job_id format
        try:
            uuid.UUID(job_id)
        except ValueError:
            logger.error(f"❌ Invalid job ID format: {job_id}")
            raise HTTPException(400, "Invalid job ID format")
        
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"❌ Job not found: {job_id}")
            raise HTTPException(404, f"Job {job_id} not found")
        
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        logger.info(f"✅ Found {len(issues)} issues for job {job_id}")
        
        return JobResult(
            summary=JobSummary(
                id=job.id,
                status=job.status,
                processed_frames=job.processed_frames or 0,
                runtime_seconds=job.runtime_seconds or 0,
                summary=job.summary_json or {},
            ),
            issues=[
                IssueSchema(
                    id=i.id,
                    element=i.element or "unknown",
                    issue_type=i.issue_type or "unknown",
                    severity=i.severity or "MEDIUM",
                    confidence=i.confidence or 0.0,
                    first_frame=i.first_frame or 0,
                    last_frame=i.last_frame or 0,
                    base_crop_url=i.base_crop_url or "",
                    present_crop_url=i.present_crop_url or "",
                    reason=i.reason or "No reason provided",
                    gps=i.gps or "{}",
                    status=i.status or "pending",
                )
                for i in issues
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching results for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to fetch results: {str(e)}")


@api_router.get("/jobs/{job_id}/results.csv")
def get_results_csv(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id",
        "element",
        "issue_type",
        "severity",
        "confidence",
        "first_frame",
        "last_frame",
        "base_crop_url",
        "present_crop_url",
        "reason",
    ])
    for i in issues:
        writer.writerow([
            i.id,
            i.element,
            i.issue_type,
            i.severity,
            f"{i.confidence:.2f}",
            i.first_frame,
            i.last_frame,
            i.base_crop_url,
            i.present_crop_url,
            i.reason,
        ])
    from fastapi.responses import Response
    return Response(content=buf.getvalue(), media_type="text/csv")


@api_router.post("/issues/{issue_id}/feedback")
def feedback(issue_id: str, data: FeedbackIn, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(404, "issue not found")
    fb = Feedback(issue_id=issue_id, label=data.label, note=data.note)
    db.add(fb)
    if data.label == "false_positive":
        issue.status = "dismissed"
    elif data.label == "confirm":
        issue.status = "confirmed"
    db.commit()
    return {"ok": True}


@api_router.get("/jobs/{job_id}/report.pdf")
def report_pdf(job_id: str, db: Session = Depends(get_db)):
    """Generate PDF or HTML report for job"""
    from .pdf import generate_pdf
    from fastapi.responses import Response
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📄 Generating report for job {job_id}")
        
        # Validate job_id format
        try:
            uuid.UUID(job_id)
        except ValueError:
            logger.error(f"❌ Invalid job ID format: {job_id}")
            raise HTTPException(400, "Invalid job ID format")
        
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"❌ Job not found: {job_id}")
            raise HTTPException(404, f"Job {job_id} not found")
        
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        
        if not issues:
            # Return simple message if no issues
            html = f"""
            <html>
            <body style="font-family: Arial; padding: 40px;">
                <h1>RoadCompare Report</h1>
                <p>Job ID: {job_id}</p>
                <p>Status: {job.status}</p>
                <p>No issues detected in this analysis.</p>
            </body>
            </html>
            """
            return Response(content=html.encode('utf-8'), media_type="text/html")
        
        # Generate report (PDF or HTML)
        report_bytes = generate_pdf(job, issues)
        
        # Check if it's PDF or HTML based on first bytes
        if report_bytes.startswith(b'%PDF'):
            # It's a PDF
            return Response(
                content=report_bytes, 
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=report_{job_id}.pdf"}
            )
        else:
            # It's HTML (fallback)
            return Response(
                content=report_bytes, 
                media_type="text/html; charset=utf-8",
                headers={"Content-Disposition": f"inline; filename=report_{job_id}.html"}
            )
            
    except Exception as e:
        print(f"Error generating report: {e}")
        # Return error page
        error_html = f"""
        <html>
        <body style="font-family: Arial; padding: 40px;">
            <h1>Report Generation Error</h1>
            <p>Unable to generate report for job {job_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/api/v1/jobs">Back to Jobs</a></p>
        </body>
        </html>
        """
        return Response(content=error_html.encode('utf-8'), media_type="text/html", status_code=500)


@api_router.get("/storage/stats")
def get_storage_stats(db: Session = Depends(get_db)):
    """Get storage statistics"""
    if os.getenv("USE_DATABASE_STORAGE", "true").lower() == "true":
        from .storage_database import get_statistics
        return get_statistics()
    else:
        return {"error": "Database storage not enabled"}


@api_router.delete("/storage/cleanup")
def cleanup_old_storage(days: int = 7, db: Session = Depends(get_db)):
    """Delete videos and jobs older than specified days"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old jobs and their issues
    old_jobs = db.query(Job).filter(Job.created_at < cutoff_date).all()
    deleted_jobs = len(old_jobs)
    
    for job in old_jobs:
        # Delete issues
        db.query(Issue).filter(Issue.job_id == job.id).delete()
        # Delete job
        db.delete(job)
    
    db.commit()
    
    # Delete old videos if using database storage
    deleted_videos = 0
    if os.getenv("USE_DATABASE_STORAGE", "true").lower() == "true":
        from .storage_database import storage
        videos = storage.list_videos()
        for video in videos:
            if video.get("created_at"):
                video_date = datetime.fromisoformat(video["created_at"])
                if video_date < cutoff_date:
                    if storage.delete_video(video["key"]):
                        deleted_videos += 1
    
    return {
        "deleted_jobs": deleted_jobs,
        "deleted_videos": deleted_videos,
        "cutoff_date": cutoff_date.isoformat()
    }


@api_router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and all associated data (issues, feedback, storage)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🗑️ Deleting job {job_id}")
        
        # Validate job_id format
        try:
            uuid.UUID(job_id)
        except ValueError:
            logger.error(f"❌ Invalid job ID format: {job_id}")
            raise HTTPException(400, "Invalid job ID format")
        
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"❌ Job not found: {job_id}")
            raise HTTPException(404, f"Job {job_id} not found")
        
        # Delete all issues and feedback associated with this job
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        issue_count = len(issues)
        
        for issue in issues:
            feedback_count = db.query(Feedback).filter(Feedback.issue_id == issue.id).delete()
            db.delete(issue)
        
        # Delete the job
        db.delete(job)
        db.commit()
        
        logger.info(f"✅ Deleted job {job_id} with {issue_count} issues")
        
        return {
            "ok": True, 
            "message": f"Job {job_id} and all associated data deleted",
            "deleted_issues": issue_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting job {job_id}: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to delete job: {str(e)}")


@api_router.delete("/jobs")
def delete_all_jobs(db: Session = Depends(get_db)):
    """Delete all jobs and associated data (use with caution)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.warning("⚠️ Deleting ALL jobs - this is a destructive operation")
        
        # Get all jobs
        jobs = db.query(Job).all()
        job_count = len(jobs)
        
        # Delete all feedback
        feedback_count = db.query(Feedback).delete()
        
        # Delete all issues
        issue_count = db.query(Issue).delete()
        
        # Delete all jobs
        db.query(Job).delete()
        db.commit()
        
        logger.info(f"✅ Deleted {job_count} jobs, {issue_count} issues, {feedback_count} feedback")
        
        return {
            "ok": True, 
            "message": f"All {job_count} jobs deleted",
            "deleted_jobs": job_count,
            "deleted_issues": issue_count,
            "deleted_feedback": feedback_count
        }
    except Exception as e:
        logger.error(f"❌ Error deleting all jobs: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to delete all jobs: {str(e)}")


