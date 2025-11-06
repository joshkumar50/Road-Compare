# RoadCompare

RoadCompare — Fast, explainable AI audits for road safety.

**Repository:** [https://github.com/joshkumar50/Road-Compare](https://github.com/joshkumar50/Road-Compare)

## Quick start

### Local Development

1. Copy env file:

```bash
cp env.example .env
```

2. Set up backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. Set up frontend (in another terminal):
```bash
cd frontend
npm install
npm run dev
```

4. Open the app: `http://localhost:5173` (frontend) and API: `http://localhost:8000/docs`.

## Services
- Frontend (Vite React + Tailwind)
- Backend API (FastAPI)
- Worker (RQ + YOLOv8 pipeline)
- Redis, Postgres, S3/MinIO

## Environment variables
See `env.example` for all config knobs.

## API
- POST `${API_PREFIX}/jobs` — multipart form: `base_video`, `present_video`, `metadata` (JSON string), `sample_rate`. Returns `{ job_id, status: 'queued' }`.
- GET `${API_PREFIX}/jobs` — list jobs
- GET `${API_PREFIX}/jobs/{id}/results` — summary + issues
- POST `${API_PREFIX}/issues/{id}/feedback` — `{ label: 'false_positive'|'confirm', note? }`
- GET `${API_PREFIX}/jobs/{id}/report.pdf` — downloadable PDF
- POST `${API_PREFIX}/uploads/presign` — optional direct S3 upload flow

## Pipeline (worker)
- Store raw videos in S3 (MinIO).
- Extract frames (default 1 FPS).
- Frame alignment: ORB features + RANSAC homography.
- Detection: YOLOv8n pre-trained checkpoint.
- Matching & change types: missing/new/moved/faded/unchanged via IoU and SSIM for lane/pavement.
- Temporal filter: N=3.
- Outputs: crops to S3, issues and job summary to Postgres.
- PDF generation: WeasyPrint.

## Evaluation
- Minimal evaluation utilities are embedded; sample script produces counts and runtime stats. For mAP and richer metrics, fine-tune on your data by swapping the model checkpoint.

## Tests
Run tests:

```bash
cd backend
pytest -q
```

## Security & robustness
- Pre-signed URLs for storage access.
- File validation via content-type and size (extend `routes.py`).
- Health endpoint at `/health`.
- Configurable thresholds via env.

## Notes
- YOLOv8 model weights download on first run (`ultralytics` manages cache). CPU-only works; GPU improves speed if available.

## Deployment

### Render + Vercel (Recommended for Hackathon)

**Quick Deploy:**
1. **Render:** Connect GitHub repo → Auto-deploy from `render.yaml`
2. **Vercel:** Import repo → Set root to `frontend` → Add `VITE_API` env var

See [DEPLOY_RENDER_VERCEL.md](DEPLOY_RENDER_VERCEL.md) for detailed instructions.





