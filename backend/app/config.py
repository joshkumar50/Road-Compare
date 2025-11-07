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


settings = Settings()






