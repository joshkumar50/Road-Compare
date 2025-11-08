"""
Download YOLOv8 model for deployment
This runs on Render during build to ensure model is available
"""

import os
import sys
from pathlib import Path

def download_model():
    """Download YOLOv8 model if not present"""
    model_dir = Path("app/models")
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / "road_defects_yolov8x.pt"
    
    # Check if model already exists
    if model_path.exists():
        print(f"✅ Model already exists at {model_path}")
        return True
    
    print("📥 Downloading YOLOv8x model...")
    
    try:
        from ultralytics import YOLO
        
        # This will download the model if not present
        model = YOLO('yolov8x.pt')
        
        # The model is downloaded to ~/.cache/ultralytics
        # We'll use it from there or copy if needed
        print("✅ YOLOv8x model downloaded successfully")
        
        # Note: On Render, the model will be cached between builds
        print(f"ℹ️ Model will be loaded from cache on first run")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("⚠️ App will run in basic mode without YOLOv8")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
