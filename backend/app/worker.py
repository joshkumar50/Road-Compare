import time
import uuid
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Job, Issue
from .config import settings


def create_demo_image_base64(text, color):
    """Create a simple demo image and return as base64"""
    img = Image.new('RGB', (200, 150), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 190, 140], fill=color, outline='black', width=2)
    
    # Simple text positioning
    draw.text((100, 75), text, fill='white', anchor='mm')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def run_pipeline(job_id: str, payload: dict):
    """Simple demo pipeline that always works"""
    db: Session = SessionLocal()
    job = None
    try:
        print(f"[Job {job_id}] Starting simple demo pipeline...")
        
        # Get or create job
        job = db.get(Job, job_id)
        if not job:
            job = Job(id=job_id, status="queued")
            db.add(job)
            db.commit()
        
        job.status = "processing"
        db.commit()
        
        start = time.time()
        
        # Create demo issues with inline base64 images
        demo_issues = [
            {
                "element": "lane_marking", 
                "issue_type": "faded",
                "severity": "HIGH",
                "confidence": 0.92,
                "base_color": (255, 200, 0),  # Yellow
                "present_color": (255, 255, 200),  # Faded yellow
                "reason": "Lane marking shows 45% reduction in visibility"
            },
            {
                "element": "sign_board",
                "issue_type": "missing", 
                "severity": "HIGH",
                "confidence": 0.87,
                "base_color": (0, 100, 255),  # Blue
                "present_color": (240, 240, 240),  # Gray (missing)
                "reason": "Stop sign detected in base but not in present video"
            },
            {
                "element": "guardrail",
                "issue_type": "damaged",
                "severity": "MEDIUM", 
                "confidence": 0.75,
                "base_color": (100, 100, 100),  # Gray
                "present_color": (255, 100, 100),  # Red (damaged)
                "reason": "Guardrail shows structural damage, 30cm displacement detected"
            }
        ]
        
        # Create issues with embedded images
        for idx, issue_data in enumerate(demo_issues):
            issue_id = str(uuid.uuid4())
            
            # Create base64 encoded images
            base_img = create_demo_image_base64("BEFORE", issue_data["base_color"])
            present_img = create_demo_image_base64(
                "MISSING" if issue_data["issue_type"] == "missing" else "AFTER",
                issue_data["present_color"]
            )
            
            # Store as data URLs (no external storage needed!)
            base_url = f"data:image/png;base64,{base_img}"
            present_url = f"data:image/png;base64,{present_img}"
            
            issue = Issue(
                id=issue_id,
                job_id=job_id,
                element=issue_data["element"],
                issue_type=issue_data["issue_type"],
                severity=issue_data["severity"],
                confidence=issue_data["confidence"],
                first_frame=idx * 10,
                last_frame=(idx + 1) * 10,
                base_crop_url=base_url,
                present_crop_url=present_url,
                reason=issue_data["reason"],
                gps=json.dumps({
                    "lat": 10.3170 + (idx * 0.001),
                    "lon": 77.9444 + (idx * 0.001)
                }),
            )
            db.add(issue)
        
        # Update job as completed
        job.processed_frames = 30
        job.runtime_seconds = float(time.time() - start) 
        job.summary_json = {
            "processed_frames": 30,
            "total_issues": 3,
            "high_severity": 2,
            "medium_severity": 1,
            "accuracy": "87%",
            "demo_mode": True
        }
        job.status = "completed"
        db.commit()
        
        print(f"[Job {job_id}] ✅ Demo completed in {job.runtime_seconds:.2f}s")
        return True
        
    except Exception as e:
        print(f"[Job {job_id}] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if job:
            job.status = "failed"
            job.summary_json = {"error": str(e)}
            db.commit()
        return False
    finally:
        db.close()
