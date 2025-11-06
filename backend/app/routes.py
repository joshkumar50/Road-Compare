import json
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .schemas import JobCreate, PresignRequest, PresignResponse, JobResult, JobSummary, IssueSchema, FeedbackIn
from .tasks import enqueue_job
from .db import get_db, Base, engine
from .models import Job, Issue, Feedback
from .config import settings
from .storage import presign_put, presign_get, put_bytes
import uuid
import csv
import io


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


@api_router.post("/jobs")
async def create_job(
    sample_rate: int = 1,
    base_video: UploadFile | None = File(default=None),
    present_video: UploadFile | None = File(default=None),
    metadata: str | None = None,
    db: Session = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    # If direct upload provided, stream to object storage
    if base_video and present_video:
        base_key = f"jobs/{job_id}/base/{base_video.filename}"
        present_key = f"jobs/{job_id}/present/{present_video.filename}"
        put_bytes(base_key, await base_video.read(), base_video.content_type or "video/mp4")
        put_bytes(present_key, await present_video.read(), present_video.content_type or "video/mp4")
    else:
        base_key = None
        present_key = None

    meta_json = json.loads(metadata) if metadata else None

    job = Job(id=job_id, status="queued", metadata_json=meta_json, sample_rate=sample_rate)
    db.add(job)
    db.commit()

    enqueue_job({
        "job_id": job_id,
        "base_key": base_key,
        "present_key": present_key,
        "sample_rate": sample_rate,
        "metadata": meta_json or {},
    })

    return {"job_id": job_id, "status": "queued"}


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


