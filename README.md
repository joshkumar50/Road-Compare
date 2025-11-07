# 🛣️ RoadCompare

**Fast, explainable AI audits for road safety** — Hackathon Edition

RoadCompare is a comprehensive AI-powered system for detecting road infrastructure deterioration by analyzing video footage. It uses YOLOv8 for object detection, frame alignment with ORB+RANSAC, and temporal filtering to identify safety issues.

**Repository:** [https://github.com/joshkumar50/Road-Compare](https://github.com/joshkumar50/Road-Compare)

## 🎯 Features

### ✅ Core Functionality
- **Video Analysis**: Compare base and present road videos to detect changes
- **AI Detection**: YOLOv8 for detecting road infrastructure elements (signs, lane markings, guardrails, pavement defects, road studs, hazards)
- **Frame Alignment**: ORB features + RANSAC homography for accurate frame matching
- **Change Detection**: Identifies missing, moved, faded, and changed elements
- **Temporal Filtering**: Reduces false positives with N=3 frame persistence
- **Severity Classification**: HIGH/MEDIUM severity levels based on issue type

### 🎨 Frontend Features
- **Modern UI**: Beautiful gradient design with Tailwind CSS
- **Real-time Updates**: Live job status monitoring
- **Issue Visualization**: Side-by-side comparison of detected issues
- **Detailed Reports**: Click on issues to view full details and crop comparisons
- **Metrics Dashboard**: System-wide statistics and performance metrics
- **Data Management**: Delete individual jobs or clear all history
- **PDF Export**: Generate comprehensive PDF reports
- **CSV Download**: Export results for further analysis
- **Responsive Design**: Works on desktop and tablet

### 🔧 Backend Features
- **FastAPI**: High-performance async API
- **Job Queue**: RQ-based background job processing
- **Error Handling**: Comprehensive error logging and recovery
- **Database**: PostgreSQL for persistent storage
- **Storage**: S3/MinIO for video and crop storage
- **Pre-signed URLs**: Secure temporary access to stored files
- **CORS Support**: Configured for multiple origins

## 🚀 Quick Start

### Local Development

1. **Clone and setup environment:**
```bash
git clone https://github.com/joshkumar50/Road-Compare.git
cd Road-Compare
cp env.example .env
```

2. **Start backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Start frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

4. **Access the app:**
   - Frontend: `http://localhost:5173`
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

## 📋 API Endpoints

### Jobs
- **POST** `/api/v1/jobs` — Create analysis job
  - Form data: `base_video`, `present_video`, `metadata` (JSON), `sample_rate`
  - Returns: `{ job_id, status: 'queued' }`

- **GET** `/api/v1/jobs` — List all jobs
  - Returns: Array of job summaries with status and frame counts

- **GET** `/api/v1/jobs/{job_id}/results` — Get job results
  - Returns: Summary + detected issues with crops and confidence scores

- **DELETE** `/api/v1/jobs/{job_id}` — Delete specific job
  - Removes job, issues, feedback, and storage files

- **DELETE** `/api/v1/jobs` — Delete all jobs
  - Clears entire history (use with caution)

### Reports & Exports
- **GET** `/api/v1/jobs/{job_id}/report.pdf` — Download PDF report
- **GET** `/api/v1/jobs/{job_id}/results.csv` — Download CSV results

### Feedback
- **POST** `/api/v1/issues/{issue_id}/feedback` — Mark issue as confirmed/false positive
  - Body: `{ label: 'false_positive'|'confirm', note?: string }`

### Utilities
- **GET** `/health` — Health check endpoint

## 🔬 Processing Pipeline

1. **Video Upload**: Store videos in S3/MinIO
2. **Frame Extraction**: Extract frames at configurable rate (default 1 FPS)
3. **Frame Alignment**: Use ORB features + RANSAC to align present frame to base
4. **Detection**: Run YOLOv8n on both frames
5. **Matching**: Match detections by class and IoU (threshold 0.3)
6. **Change Classification**: Determine if missing/moved/faded/unchanged
7. **Temporal Filtering**: Keep issues that persist for N frames
8. **Persistence**: Save crops and issue metadata to database
9. **Report Generation**: Create PDF with findings

## 🛠️ Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+psycopg2://user:pass@localhost/roadcompare

# Redis (job queue)
REDIS_URL=redis://localhost:6379/0

# Storage (S3/MinIO)
S3_ENDPOINT=https://s3.amazonaws.com  # or http://minio:9000
S3_BUCKET=roadcompare-storage
S3_REGION=us-east-1
S3_SECURE=true
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# API
API_PREFIX=/api/v1
FRONTEND_URL=http://localhost:5173
SECRET_KEY=your-secret-key

# Processing
FRAME_RATE=1
TEMPORAL_PERSIST_N=3
CONFIDENCE_THRESHOLD=0.25
```

## 📊 Judging Criteria Alignment

### ✅ Accuracy
- YOLOv8 pre-trained model for robust detection
- Frame alignment with RANSAC for precise matching
- IoU-based matching with configurable thresholds
- SSIM-based fading detection for lane markings and pavement
- Temporal filtering to reduce false positives

### ✅ Usability
- Intuitive web interface with modern design
- Real-time job status updates
- Detailed issue visualization with crop comparisons
- One-click PDF report generation
- CSV export for further analysis
- Clear severity indicators (HIGH/MEDIUM)
- Metrics dashboard for system overview

### ✅ Innovation
- Novel frame alignment approach using ORB+RANSAC
- SSIM-based deterioration detection
- Temporal persistence filtering
- Comprehensive change classification (missing/moved/faded)
- Real-time processing with background workers
- Explainable AI with detailed reasoning for each detection

## 🗑️ Data Management

### Delete Individual Job
```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/{job_id}
```

### Delete All Jobs
```bash
curl -X DELETE http://localhost:8000/api/v1/jobs
```

### Frontend Delete
- Click the 🗑️ button next to any job in the history
- Use "🗑️ Clear All" button to delete all jobs at once
- Confirmation dialog prevents accidental deletion

## 📦 Deployment

### Render + Vercel (Recommended)

**Backend (Render):**
1. Connect GitHub repo
2. Auto-deploy from `render.yaml`
3. Set environment variables
4. PostgreSQL and Redis services auto-created

**Frontend (Vercel):**
1. Import GitHub repo
2. Set root directory to `frontend`
3. Add `VITE_API` environment variable
4. Auto-deploy on push

See [DEPLOY_RENDER_VERCEL.md](DEPLOY_RENDER_VERCEL.md) for detailed instructions.

### Auto-Push to GitHub
```bash
# Windows
auto_push.bat

# Or use PowerShell script
powershell -File push_to_github.ps1 -Message "Your commit message"
```

## 📚 Architecture

```
RoadCompare/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + worker thread
│   │   ├── routes.py        # API endpoints + delete operations
│   │   ├── worker.py        # YOLOv8 pipeline + frame alignment
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── storage.py       # S3/MinIO operations
│   │   ├── pdf.py           # PDF generation
│   │   └── config.py        # Settings
│   ├── requirements.txt     # Python dependencies
│   └── tests/               # Unit tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # Entry point
│   │   └── styles.css       # Global styles
│   ├── package.json         # NPM dependencies
│   └── vite.config.js       # Vite configuration
├── render.yaml              # Render deployment config
├── vercel.json              # Vercel deployment config
└── push_to_github.ps1       # Auto-push script
```

## 🧪 Testing

```bash
cd backend
pytest -q
```

## 📝 License

MIT - See LICENSE file

## 👥 Contributors

Built for Hackathon - Road Safety Audit Challenge

## 🔗 Links

- **GitHub**: https://github.com/joshkumar50/Road-Compare
- **Live Demo**: https://roadcompare.vercel.app
- **API Docs**: https://roadcompare-api.onrender.com/docs

## 📞 Support

For issues or questions:
1. Check [DEPLOY_RENDER_VERCEL.md](DEPLOY_RENDER_VERCEL.md) for deployment help
2. Review API documentation at `/docs` endpoint
3. Check logs in Render dashboard for backend issues





