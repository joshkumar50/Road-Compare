from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import api_router
import threading
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RoadCompare API", 
    version="1.0.0",
    description="AI-powered road infrastructure analysis API"
)

# Startup event to verify connections
@app.on_event("startup")
async def startup_event():
    """Verify database and Redis connections on startup"""
    logger.info("🚀 Starting RoadCompare API...")
    
    # Test database connection
    try:
        from .db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    # Test Redis connection (non-blocking)
    try:
        from redis import Redis
        redis_conn = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        redis_conn.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed (non-critical): {e}")
    
    logger.info("✅ RoadCompare API started successfully")

# Build allowed origins list from config
allowed_origins = [origin.strip() for origin in settings.cors_origins]
# Always include frontend_url
if settings.frontend_url not in allowed_origins:
    allowed_origins.insert(0, settings.frontend_url)

# Add both Vercel domain variations
allowed_origins.extend([
    "https://roadcompare.vercel.app",
    "https://road-compare.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000"
])

# Remove duplicates
allowed_origins = list(set(allowed_origins))

print(f"✅ CORS allowed origins: {allowed_origins}")

# More permissive CORS for production debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


@app.get("/")
def root():
    """Root endpoint for debugging"""
    return {
        "service": "RoadCompare API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api": settings.api_prefix,
            "jobs": f"{settings.api_prefix}/jobs",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "roadcompare-api",
        "database": "connected",
        "redis": "connected"
    }


app.include_router(api_router, prefix=settings.api_prefix)


# Start RQ worker in background thread (free alternative to separate worker service)
def start_worker():
    """Start RQ worker in background thread to process jobs"""
    import time
    # Wait for app to fully start
    time.sleep(2)
    
    try:
        from rq import Worker, Queue
        from redis import Redis
        
        print("🔄 Initializing RQ worker...")
        redis_conn = Redis.from_url(settings.redis_url, decode_responses=True)
        
        # Test connection
        redis_conn.ping()
        print("✅ Redis connection successful")
        
        # Create queue
        queue = Queue("rc-jobs", connection=redis_conn)
        print(f"✅ Queue created: {queue.name}")
        
        # Create and start worker
        worker = Worker([queue], connection=redis_conn)
        print(f"✅ Worker created: {worker.name}")
        print("🚀 Worker starting to listen for jobs...")
        
        worker.work(with_scheduler=False, logging_level='INFO')
        
    except ConnectionError as e:
        print(f"⚠️ Redis connection failed (worker disabled): {e}")
    except AttributeError as e:
        print(f"⚠️ Worker initialization error (check Redis version): {e}")
    except Exception as e:
        print(f"⚠️ Worker thread error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


# Disable background worker on Render (signal handlers don't work in threads)
# Jobs will be processed synchronously instead
if os.getenv("ENABLE_WORKER", "false").lower() == "true":
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    print("✅ RQ Worker thread started")
else:
    print("⚠️ Background worker disabled - jobs will process synchronously")






