# RoadCompare Technical Note (1 page)

Architecture: Frontend (Vite React + Tailwind), Backend (FastAPI), Worker (RQ), Redis, Postgres, MinIO, Docker. API orchestrates uploads and job lifecycle; worker executes the ML pipeline.

Pipeline: Videos → frames (1 FPS) → alignment (ORB+RANSAC) → detection (YOLOv8n, classes: sign_board, lane_marking, guardrail, pavement_defect, road_stud, roadside_hazard) → cross-video matching (IoU, class) → change classification (missing/new/moved/faded/unchanged) → temporal filter (N=3) → aggregation → exports (crops, JSON, PDF).

Model: Uses `ultralytics` YOLOv8n pre-trained weights. Inference defaults to CPU; if GPU present, PyTorch uses CUDA automatically. Fine-tuning can be enabled by pointing to a local dataset and training a small number of epochs.

Storage: MinIO bucket `roadcompare` stores raw inputs, annotated crops, and generated artifacts. Access via presigned URLs.

DB schema: `jobs` (status, timing, summary) and `issues` (element, type, severity, confidence, frames, evidence URLs, GPS). `feedback` table stores human-in-the-loop decisions and updates issue status.

Explainability: Each issue includes base vs. present crops, confidence, and a reason string (e.g., "No matching detection found in present frames (IoU threshold = 0.3)"). Thresholds are configurable via env.

Performance: The demo shows runtime seconds and normalized processing time (sec per min of input). Batch size and frame rate are tunable.

Security: No auth by default for hackathon; ready for API key / OAuth. Pre-signed URLs, size/type validation hooks, and health endpoints included.

Limitations: Viewpoint and lighting changes reduce match quality; GPS optional; demo dataset is minimal. Future improvements: optical flow stabilization, segmentation for markings, dataset expansion, online learning from feedback.




