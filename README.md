# RoadCompare

RoadCompare — Fast, explainable AI audits for road safety.

**Repository:** [https://github.com/joshkumar50/Road-Compare](https://github.com/joshkumar50/Road-Compare)

## Quick start

Prereqs: Docker Desktop.

1. Copy env file:

```bash
cp env.example .env
```

2. Build and start:

```bash
make build
make up
```

3. Open the app: `http://localhost:5173` (frontend) and API: `http://localhost:8000/docs`.

4. Sample run (headless demo):

```bash
make sample-run
```

Artifacts saved to `artifacts_results.json` and `artifacts_report.pdf`.

## Services (docker-compose)
- Frontend (Vite React + Tailwind)
- Backend API (FastAPI)
- Worker (RQ + YOLOv8 pipeline)
- Redis, Postgres, MinIO

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
Run tests inside backend container:

```bash
docker compose exec backend pytest -q
```

## Make targets
- `make build` — build images
- `make up` — start stack
- `make down` — stop
- `make logs` — tail logs
- `make test` — backend tests
- `make sample-run` — end-to-end demo script

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

### Docker Compose (Local/Server)

```bash
cp env.example .env
make build && make up
```

Access at `http://localhost:5173` (frontend) and `http://localhost:8000/docs` (API).




