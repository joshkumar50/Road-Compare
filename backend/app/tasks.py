import uuid
from rq import Queue
from redis import Redis
from .config import settings


def get_queue() -> Queue:
    redis_conn = Redis.from_url(settings.redis_url)
    return Queue("rc-jobs", connection=redis_conn)


def enqueue_job(payload: dict) -> str:
    job_id = str(uuid.uuid4())
    q = get_queue()
    # Defer import to avoid heavy deps on import time
    from .worker import run_pipeline

    q.enqueue(run_pipeline, job_id, payload, job_id=job_id)
    return job_id






