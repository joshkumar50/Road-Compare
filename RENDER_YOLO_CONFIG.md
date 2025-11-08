# 🚀 Enable YOLOv8 on Render Deployment

## Step 1: Add Environment Variables on Render

Go to: https://dashboard.render.com → Your Service → Environment

Add these variables:

```
USE_YOLO=true
MODEL_PATH=models/road_defects_yolov8x.pt
TEMPORAL_FRAMES=5
BLUR_THRESHOLD=100.0
DEMO_MODE=false
ENABLE_WORKER=false
```

## Step 2: Update build.sh for Render

The build script needs to install YOLOv8 dependencies.
