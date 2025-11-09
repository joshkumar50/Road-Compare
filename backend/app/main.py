from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
    except ImportError:
        logger.warning("⚠️ Redis module not available - background worker disabled")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed (non-critical): {e}")
    
    logger.info("✅ RoadCompare API started successfully")

# Build allowed origins list from config - USE WILDCARD FOR VERCEL PREVIEW DEPLOYMENTS
allowed_origins = ["*"]  # Allow all origins to fix CORS permanently

logger.info(f"✅ CORS configured: Allow all origins (*)")

# CORS configuration for production - CRITICAL: Must be added BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allow all
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Manual CORS middleware as ABSOLUTE failsafe
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ManualCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight
        if request.method == "OPTIONS":
            return Response(
                content="",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "3600",
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

app.add_middleware(ManualCORSMiddleware)


@app.get("/")
def root():
    """Root endpoint for debugging"""
    return {
        "service": "RoadCompare API",
        "version": "1.0.0",
        "status": "running",
        "cors": "enabled",
        "endpoints": {
            "health": "/health",
            "api": settings.api_prefix,
            "jobs": f"{settings.api_prefix}/jobs",
            "docs": "/docs"
        }
    }


@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    return {"status": "ok"}


@app.get("/health")
def health():
    """Health check endpoint with actual connection testing"""
    from datetime import datetime
    health_status = {
        "status": "ok",
        "service": "roadcompare-api",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Test database connection
    try:
        from .db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Test Redis connection
    try:
        from redis import Redis
        redis_conn = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        redis_conn.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"warning: {str(e)}"
        # Redis failure is non-critical for basic functionality
    
    return health_status


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
        
    except ImportError as e:
        print(f"⚠️ Required modules not available (worker disabled): {e}")
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






