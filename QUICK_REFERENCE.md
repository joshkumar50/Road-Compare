# 🚀 RoadCompare - Quick Reference Guide

## 📍 Live Links

- **Frontend**: https://roadcompare.vercel.app
- **API Docs**: https://roadcompare-api.onrender.com/docs
- **GitHub**: https://github.com/joshkumar50/Road-Compare

---

## 🎯 Key Features at a Glance

| Feature | Status | Location |
|---------|--------|----------|
| Video Upload | ✅ | Home page |
| Real-time Analysis | ✅ | Background processing |
| Issue Detection | ✅ | Job results view |
| Delete Jobs | ✅ | History list (🗑️ button) |
| Delete All | ✅ | History list ("Clear All") |
| PDF Export | ✅ | Job details |
| CSV Download | ✅ | Job details |
| Metrics Dashboard | ✅ | Metrics page |
| Auto-Deploy | ✅ | GitHub → Render/Vercel |
| Auto-Push | ✅ | `auto_push.bat` or PowerShell |

---

## 🎨 Frontend Components

### Upload Section
```
📹 Upload Road Videos
├── Base Video (Before) - File input
├── Present Video (After) - File input
├── Metadata (optional) - JSON textarea
└── 🚀 Analyze Videos - Submit button
```

### History Section
```
📋 Analysis History
├── Status badges (COMPLETED/PROCESSING/FAILED/QUEUED)
├── Job ID (truncated)
├── Frame count & runtime
├── 🗑️ Delete button (individual)
└── 🗑️ Clear All button (bulk)
```

### Job Details
```
📊 Job Analysis Results
├── Summary Stats (4 cards)
│   ├── Status
│   ├── Frames Processed
│   ├── High Severity Issues
│   └── Medium Severity Issues
├── Issues List (clickable)
│   ├── Severity badge
│   ├── Element type
│   ├── Confidence %
│   ├── Frame range
│   └── Crop thumbnails
├── Issue Details Panel
│   ├── Element
│   ├── Issue Type
│   ├── Severity
│   ├── Confidence
│   ├── Reason
│   └── Full crop comparison
└── 📄 Download PDF button
```

### Metrics Dashboard
```
📊 System Metrics
├── Total Jobs (with breakdown)
├── Total Issues Detected
├── Frames Processed
├── Avg Processing Time
└── About RoadCompare section
```

---

## 🔌 API Quick Reference

### Create Job
```bash
POST /api/v1/jobs
Content-Type: multipart/form-data

base_video: <file>
present_video: <file>
metadata: {"start_gps": "...", "end_gps": "..."}
sample_rate: 1
```

### List Jobs
```bash
GET /api/v1/jobs
```

### Get Results
```bash
GET /api/v1/jobs/{job_id}/results
```

### Delete Job
```bash
DELETE /api/v1/jobs/{job_id}
```

### Delete All
```bash
DELETE /api/v1/jobs
```

### Download PDF
```bash
GET /api/v1/jobs/{job_id}/report.pdf
```

### Download CSV
```bash
GET /api/v1/jobs/{job_id}/results.csv
```

---

## 🛠️ Local Development

### Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 🔄 Auto-Push to GitHub

### Windows Batch
```bash
auto_push.bat
```

### PowerShell
```powershell
powershell -File push_to_github.ps1 -Message "Your message"
```

### Manual Git
```bash
git add .
git commit -m "Your message"
git push origin main
```

---

## 🎯 Judging Criteria

### Accuracy ✅
- YOLOv8 detection
- ORB+RANSAC alignment
- IoU matching (0.3 threshold)
- SSIM fading detection
- Temporal filtering (N=3)

### Usability ✅
- Modern UI design
- Real-time updates
- Clear visualizations
- One-click reports
- Easy data management

### Innovation ✅
- Novel frame alignment
- SSIM-based detection
- Temporal persistence
- Change classification
- Explainable AI

---

## 🗑️ Delete Operations

### Delete Single Job
1. Go to History section
2. Click 🗑️ button on job
3. Confirm deletion
4. Job removed with all data

### Delete All Jobs
1. Go to History section
2. Click 🗑️ Clear All button
3. Confirm deletion
4. All jobs removed

### API Delete
```bash
# Single job
curl -X DELETE http://localhost:8000/api/v1/jobs/{job_id}

# All jobs
curl -X DELETE http://localhost:8000/api/v1/jobs
```

---

## 📊 Issue Severity

| Severity | Color | Condition |
|----------|-------|-----------|
| HIGH | 🔴 Red | Missing or Faded elements |
| MEDIUM | 🟠 Orange | Moved elements |

---

## 🔍 Issue Types

| Type | Meaning |
|------|---------|
| missing | Element not found in present frame |
| moved | Element position changed (IoU < 0.3) |
| faded | Element faded (SSIM < 0.6) |
| changed | Element class changed |
| unchanged | No change detected |

---

## 📈 Performance Metrics

- **Frame Rate**: 1 FPS (configurable)
- **Detection Model**: YOLOv8n (nano)
- **Alignment**: ORB features + RANSAC
- **Temporal Filter**: 3 frames
- **Confidence Threshold**: 0.25
- **IoU Threshold**: 0.3
- **SSIM Threshold**: 0.6

---

## 🚨 Troubleshooting

### Videos Not Processing
1. Check file format (MP4, WebM, etc.)
2. Verify file size (< 100MB recommended)
3. Check backend logs
4. Ensure Redis is running

### Delete Not Working
1. Check database connection
2. Verify S3/MinIO access
3. Check error logs
4. Try single job delete first

### Frontend Not Loading
1. Check VITE_API env variable
2. Verify backend is running
3. Check browser console for errors
4. Clear browser cache

### Deployment Issues
1. Check Render logs
2. Check Vercel logs
3. Verify environment variables
4. Check GitHub Actions

---

## 📚 Documentation

- **README.md** - Project overview
- **DEPLOY_RENDER_VERCEL.md** - Deployment guide
- **IMPLEMENTATION_SUMMARY.md** - Complete implementation details
- **API Docs** - Interactive at `/docs` endpoint

---

## 🎓 Tech Stack

### Backend
- FastAPI, PostgreSQL, Redis, RQ
- YOLOv8, OpenCV, scikit-image
- WeasyPrint, SQLAlchemy

### Frontend
- React, Vite, Tailwind CSS
- Axios, Konva

### Deployment
- Render (backend), Vercel (frontend)
- AWS S3 or MinIO (storage)

---

## ✅ Checklist for Judges

- [ ] Access frontend at https://roadcompare.vercel.app
- [ ] Upload test videos
- [ ] Wait for processing
- [ ] View detected issues
- [ ] Download PDF report
- [ ] Test delete functionality
- [ ] Check metrics dashboard
- [ ] Review API documentation
- [ ] Verify GitHub repository
- [ ] Check deployment status

---

## 🏆 Ready for Submission

✅ All features implemented
✅ All judging criteria met
✅ Fully deployed and accessible
✅ Comprehensive documentation
✅ Auto-deployment configured
✅ Error handling in place
✅ Modern UI/UX
✅ Production-ready code

**Status**: 🚀 Ready for Hackathon Evaluation!

---

*For detailed information, see IMPLEMENTATION_SUMMARY.md*
