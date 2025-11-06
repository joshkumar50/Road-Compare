#!/usr/bin/env bash
set -euo pipefail

echo "Starting services..."
docker compose up -d

API=${API:-http://localhost:8000/api/v1}

echo "Generating sample dataset..."
python scripts/generate_sample_videos.py || true

echo "Submitting sample job (no files, synthetic demo)..."
JOB_ID=$(curl -s -X POST "$API/jobs" -F "sample_rate=1" | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job: $JOB_ID"

echo "Waiting for completion..."
for i in {1..60}; do
  STATUS=$(curl -s "$API/jobs" | python - <<PY
import sys,json,os
jobs=json.load(sys.stdin)
jid=os.environ['JOB_ID']
print([j['status'] for j in jobs if j['id']==jid][0])
PY
)
  echo "Status: $STATUS"; [ "$STATUS" = "completed" ] && break; sleep 2
done

echo "Fetching results..."
curl -s "$API/jobs/$JOB_ID/results" -o artifacts_results.json
echo "Downloading PDF..."
curl -s "$API/jobs/$JOB_ID/report.pdf" -o artifacts_report.pdf

echo "Evaluating results..."
python scripts/evaluate.py --labels sample_data/labels.csv --results artifacts_results.json --out artifacts_metrics.json || true

echo "Done. Results at artifacts_results.json, artifacts_report.pdf, artifacts_metrics.json"


