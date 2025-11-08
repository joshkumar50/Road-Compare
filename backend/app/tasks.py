import uuid
import os
import threading
from rq import Queue
from redis import Redis
from .config import settings


def get_queue() -> Queue:
    redis_conn = Redis.from_url(settings.redis_url)
    return Queue("rc-jobs", connection=redis_conn)


def enqueue_job(payload: dict) -> str:
    job_id = payload.get("job_id", str(uuid.uuid4()))
    
    # Choose pipeline based on configuration
    if settings.use_yolo:
        # Use advanced YOLOv8 pipeline
        from .worker_advanced import run_advanced_pipeline as run_pipeline
        print(f"🤖 Using YOLOv8 AI pipeline for job {job_id}")
    else:
        # Use basic pipeline
        from .worker import run_pipeline
        print(f"📊 Using basic pipeline for job {job_id}")
    
    # Check if background worker is enabled
    if os.getenv("ENABLE_WORKER", "false").lower() == "true":
        # Use RQ queue for background processing
        q = get_queue()
        q.enqueue(run_pipeline, job_id, payload, job_id=job_id)
        print(f"✅ Job {job_id} enqueued to RQ worker")
    else:
        # Process synchronously in a separate thread (non-blocking)
        print(f"🔄 Processing job {job_id} synchronously in background thread")
        thread = threading.Thread(target=run_pipeline, args=(job_id, payload), daemon=True)
        thread.start()
    
    return job_id






