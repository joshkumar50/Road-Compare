import json
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from .schemas import JobCreate, PresignRequest, PresignResponse, JobResult, JobSummary, IssueSchema, FeedbackIn
from .tasks import enqueue_job
from .db import get_db, Base, engine
from .models import Job, Issue, Feedback
from .config import settings
from .storage import presign_put, presign_get, put_bytes, STORAGE_DIR, USE_LOCAL_STORAGE
import uuid
import csv
import io
from pathlib import Path


Base.metadata.create_all(bind=engine)

api_router = APIRouter()


@api_router.post("/uploads/presign", response_model=PresignResponse)
def presign_upload(data: PresignRequest):
    job_id = str(uuid.uuid4())
    base_key = f"jobs/{job_id}/base/{data.base_filename}"
    present_key = f"jobs/{job_id}/present/{data.present_filename}"
    return PresignResponse(
        base_url=presign_put(base_key), present_url=presign_put(present_key), job_id=job_id
    )


@api_router.get("/storage/{file_path:path}")
async def serve_local_storage(file_path: str):
    """Serve files from local storage (only when using local storage mode)"""
    if not USE_LOCAL_STORAGE:
        raise HTTPException(404, "Local storage not enabled")
    
    full_path = STORAGE_DIR / file_path
    
    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")
    
    # Security check: ensure path is within STORAGE_DIR
    try:
        full_path.resolve().relative_to(STORAGE_DIR.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")
    
    return FileResponse(full_path)


@api_router.post("/jobs")
async def create_job(
    sample_rate: int = 1,
    base_video: UploadFile | None = File(default=None),
    present_video: UploadFile | None = File(default=None),
    metadata: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        job_id = str(uuid.uuid4())
        
        # Validate videos are provided
        if not base_video or not present_video:
            raise HTTPException(400, "Both base_video and present_video are required")
        
        # If direct upload provided, stream to object storage
        base_key = f"jobs/{job_id}/base/{base_video.filename}"
        present_key = f"jobs/{job_id}/present/{present_video.filename}"
        
        print(f"📤 Uploading videos for job {job_id}")
        put_bytes(base_key, await base_video.read(), base_video.content_type or "video/mp4")
        put_bytes(present_key, await present_video.read(), present_video.content_type or "video/mp4")
        print(f"✅ Videos uploaded for job {job_id}")

        meta_json = json.loads(metadata) if metadata else {}

        job = Job(id=job_id, status="queued", metadata_json=meta_json, sample_rate=sample_rate)
        db.add(job)
        db.commit()
        print(f"✅ Job {job_id} created in database")

        enqueue_job({
            "job_id": job_id,
            "base_key": base_key,
            "present_key": present_key,
            "sample_rate": sample_rate,
            "metadata": meta_json,
        })
        print(f"✅ Job {job_id} enqueued for processing")

        return {"job_id": job_id, "status": "queued"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating job: {type(e).__name__}: {e}")
        raise HTTPException(500, f"Failed to create job: {str(e)}")


@api_router.get("/jobs", response_model=List[JobSummary])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        JobSummary(
            id=j.id,
            status=j.status,
            processed_frames=j.processed_frames,
            runtime_seconds=j.runtime_seconds,
            summary=j.summary_json or {},
        )
        for j in jobs
    ]


@api_router.get("/jobs/{job_id}/results", response_model=JobResult)
def get_results(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    return JobResult(
        summary=JobSummary(
            id=job.id,
            status=job.status,
            processed_frames=job.processed_frames,
            runtime_seconds=job.runtime_seconds,
            summary=job.summary_json or {},
        ),
        issues=[
            IssueSchema(
                id=i.id,
                element=i.element,
                issue_type=i.issue_type,
                severity=i.severity,
                confidence=i.confidence,
                first_frame=i.first_frame,
                last_frame=i.last_frame,
                base_crop_url=i.base_crop_url,
                present_crop_url=i.present_crop_url,
                reason=i.reason,
                gps=i.gps,
                status=i.status,
            )
            for i in issues
        ],
    )


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
    from .pdf import generate_pdf

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    pdf_bytes = generate_pdf(job, issues)
    from fastapi.responses import Response

    return Response(content=pdf_bytes, media_type="application/pdf")


@api_router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and all associated data (issues, feedback, storage)"""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    
    # Delete all issues and feedback associated with this job
    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    for issue in issues:
        db.query(Feedback).filter(Feedback.issue_id == issue.id).delete()
        db.delete(issue)
    
    # Delete the job
    db.delete(job)
    db.commit()
    
    # Delete storage files (best effort)
    try:
        from .storage import delete_prefix
        delete_prefix(f"jobs/{job_id}/")
    except Exception as e:
        print(f"Warning: Could not delete storage for job {job_id}: {e}")
    
    return {"ok": True, "message": f"Job {job_id} and all associated data deleted"}


@api_router.delete("/jobs")
def delete_all_jobs(db: Session = Depends(get_db)):
    """Delete all jobs and associated data (use with caution)"""
    # Get all jobs
    jobs = db.query(Job).all()
    job_ids = [j.id for j in jobs]
    
    # Delete all feedback
    db.query(Feedback).delete()
    
    # Delete all issues
    db.query(Issue).delete()
    
    # Delete all jobs
    db.query(Job).delete()
    db.commit()
    
    # Delete storage files (best effort)
    try:
        from .storage import delete_prefix
        for job_id in job_ids:
            delete_prefix(f"jobs/{job_id}/")
    except Exception as e:
        print(f"Warning: Could not delete storage: {e}")
    
    return {"ok": True, "message": f"All {len(job_ids)} jobs deleted"}


