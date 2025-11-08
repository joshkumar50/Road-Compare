from pydantic import BaseModel
import os


class Settings(BaseModel):
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    secret_key: str = os.getenv("SECRET_KEY", "devsecret")

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://road:compare@postgres:5432/roadcompare",
    )

    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://minio:9000")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_bucket: str = os.getenv("S3_BUCKET", "roadcompare")
    s3_secure: bool = os.getenv("S3_SECURE", "false").lower() == "true"

    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # CORS origins - support multiple origins for flexibility
    cors_origins: list = (
        os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if os.getenv("CORS_ORIGINS")
        else ["http://localhost:5173"]
    )

    frame_rate: int = int(os.getenv("FRAME_RATE", "1"))
    temporal_persist_n: int = int(os.getenv("TEMPORAL_PERSIST_N", "3"))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
    
    # Demo mode - use synthetic data instead of real video processing
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # MongoDB configuration for scalable storage
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    mongo_db: str = os.getenv("MONGO_DB", "roadcompare")
    
    # AI Model configuration
    model_path: str = os.getenv("MODEL_PATH", "models/road_defects_yolov8x.pt")
    use_yolo: bool = os.getenv("USE_YOLO", "true").lower() == "true"
    temporal_frames: int = int(os.getenv("TEMPORAL_FRAMES", "5"))
    blur_threshold: float = float(os.getenv("BLUR_THRESHOLD", "100.0"))


settings = Settings()






