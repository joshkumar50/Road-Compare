from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import api_router
import threading
import os


app = FastAPI(title="RoadCompare API", version="1.0.0")

# Build allowed origins list from config
allowed_origins = [origin.strip() for origin in settings.cors_origins]
# Always include frontend_url
if settings.frontend_url not in allowed_origins:
    allowed_origins.insert(0, settings.frontend_url)

print(f"✅ CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)


# Start RQ worker in background thread (free alternative to separate worker service)
def start_worker():
    """Start RQ worker in background thread to process jobs"""
    try:
        from rq import Worker, Queue
        from redis import Redis
        
        redis_conn = Redis.from_url(settings.redis_url)
        worker = Worker([Queue("rc-jobs", connection=redis_conn)])
        worker.work()
    except Exception as e:
        print(f"Worker thread error: {e}")


# Only start worker if not explicitly disabled (for local dev)
if os.getenv("ENABLE_WORKER", "true").lower() == "true":
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    print("✅ RQ Worker started in background thread")






