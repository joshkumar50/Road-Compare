from pydantic import BaseModel, Field
from typing import Optional, List, Any


class JobCreate(BaseModel):
    sample_rate: int = 1
    metadata: Optional[dict] = None


class PresignRequest(BaseModel):
    base_filename: str
    present_filename: str


class PresignResponse(BaseModel):
    base_url: str
    present_url: str
    job_id: str


class IssueSchema(BaseModel):
    id: str
    element: str
    issue_type: str
    severity: str
    confidence: float
    first_frame: int
    last_frame: int
    base_crop_url: str
    present_crop_url: str
    reason: str
    gps: Optional[Any]
    status: str


class JobSummary(BaseModel):
    id: str
    status: str
    processed_frames: int
    runtime_seconds: float
    summary: dict = Field(default_factory=dict)


class JobResult(BaseModel):
    summary: JobSummary
    issues: List[IssueSchema]


class FeedbackIn(BaseModel):
    label: str
    note: Optional[str] = None






