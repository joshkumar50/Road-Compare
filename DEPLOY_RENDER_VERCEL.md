# Deploy RoadCompare to Render + Vercel

This guide walks you through deploying RoadCompare using:
- **Vercel** for frontend (React/Vite)
- **Render** for backend API, worker, Redis, and Postgres

## Prerequisites

1. GitHub repository: [https://github.com/joshkumar50/Road-Compare](https://github.com/joshkumar50/Road-Compare)
2. AWS S3 bucket (for video storage) - or use Render disk storage
3. Render account: https://render.com
4. Vercel account: https://vercel.com

## Step 1: Set up AWS S3 (or skip for Render disk storage)

1. Create an S3 bucket (e.g., `roadcompare-storage`)
2. Create IAM user with S3 read/write permissions
3. Save Access Key ID and Secret Access Key

**Alternative:** Use Render's disk storage (simpler but less scalable)

## Step 2: Deploy Backend to Render

### 2.1 Create Render Services

1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
3. Connect your GitHub repo: `joshkumar50/Road-Compare`
4. Render will detect `render.yaml` and create services automatically

OR manually create:

### 2.2 Web Service (API)

1. **New +** → **Web Service**
2. Connect repo: `joshkumar50/Road-Compare`
3. Settings:
   - **Name:** `roadcompare-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install --upgrade pip && pip install --only-binary=scipy --prefer-binary -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory:** (leave empty)
   
   **Note:** The worker runs in a background thread within this service (no separate worker needed for free tier)

4. **Environment Variables:**
   ```
   DATABASE_URL=<from Postgres service>
   REDIS_URL=<from Redis service>
   S3_ENDPOINT=https://s3.amazonaws.com
   S3_BUCKET=roadcompare-storage
   S3_REGION=us-east-1
   S3_SECURE=true
   AWS_ACCESS_KEY_ID=<your-aws-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   SECRET_KEY=<generate-random-string>
   API_PREFIX=/api/v1
   FRONTEND_URL=https://roadcompare.vercel.app
   FRAME_RATE=1
   TEMPORAL_PERSIST_N=3
   CONFIDENCE_THRESHOLD=0.25
   ```

### 2.3 Worker (Optional - Already Included)

**Note:** The worker runs automatically in a background thread within the API service (configured in `app/main.py`). This is a free alternative to a separate worker service. No separate worker service is needed.

If you want a dedicated worker service (for better isolation), you can create one:
1. **New +** → **Background Worker**
2. Connect same repo
3. Settings:
   - **Name:** `roadcompare-worker`
   - **Build Command:** `pip install --upgrade pip && pip install --only-binary=scipy --prefer-binary -r backend/requirements.txt`
   - **Start Command:** `cd backend && python -m app.worker`
   - Same environment variables as API (except `FRONTEND_URL`)

### 2.4 PostgreSQL Database

1. **New +** → **PostgreSQL**
2. Name: `roadcompare-db`
3. Plan: Free (or paid for production)
4. Copy connection string to API/Worker env vars

### 2.5 Redis

1. **New +** → **Redis**
2. Name: `roadcompare-redis`
3. Plan: Free
4. Copy connection string to API/Worker env vars

## Step 3: Deploy Frontend to Vercel

1. Go to https://vercel.com
2. **Add New Project**
3. Import GitHub repo: `joshkumar50/Road-Compare`
4. Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

5. **Environment Variables:**
   ```
   VITE_API=https://roadcompare-api.onrender.com/api/v1
   ```
   (Replace with your actual Render API URL)

6. Click **Deploy**

## Step 4: Update CORS and URLs

1. In Render API service, update:
   ```
   FRONTEND_URL=https://your-vercel-app.vercel.app
   ```

2. Redeploy API service

## Step 5: Initialize Database

The database tables will be created automatically on first API request (via `Base.metadata.create_all` in `routes.py`).

Or manually run migrations:
```bash
# Connect to Render Postgres and run:
# Tables are auto-created, but you can verify with:
# SELECT * FROM jobs LIMIT 1;
```

## Step 6: Test Deployment

1. **Frontend:** https://your-app.vercel.app
2. **API Docs:** https://roadcompare-api.onrender.com/docs
3. **Health Check:** https://roadcompare-api.onrender.com/health

## Troubleshooting

### Worker not processing jobs
- Check Redis connection in API service logs (worker runs in background thread)
- Verify `REDIS_URL` is set correctly
- Check `ENABLE_WORKER` env var is not set to "false"
- If using separate worker service, ensure it's running

### S3 uploads failing
- Verify AWS credentials
- Check bucket permissions
- Ensure bucket exists and is in correct region

### Frontend can't reach API
- Check `VITE_API` env var in Vercel
- Verify CORS settings in backend (`FRONTEND_URL`)
- Check Render API service is running

### Database connection errors
- Verify `DATABASE_URL` format: `postgresql+psycopg2://...`
- Check Postgres service is running
- Ensure database exists

## Cost Estimate (Free Tier)

- **Render:**
  - Web Service: Free (spins down after 15min inactivity)
  - Worker: Free (spins down after 15min inactivity)
  - Postgres: Free (90 days, then $7/mo)
  - Redis: Free (25MB, then $10/mo)

- **Vercel:**
  - Frontend: Free (unlimited)

- **AWS S3:**
  - ~$0.023/GB storage + $0.005/1000 requests

**Total:** ~$0-7/month for demo/hackathon

## Production Considerations

1. **Upgrade Render services** to paid plans for:
   - Always-on workers
   - Larger databases
   - Better performance

2. **Add domain** to Vercel and Render

3. **Enable HTTPS** (automatic on both platforms)

4. **Set up monitoring:**
   - Render logs dashboard
   - Vercel analytics

5. **Optimize ML model:**
   - Consider GPU instance for worker (Render doesn't support GPU, may need separate service)
   - Or use cloud ML API (AWS Rekognition, Google Vision)

## Quick Deploy Commands

After initial setup, updates are automatic via GitHub push:
- Push to `main` → Render auto-deploys
- Push to `main` → Vercel auto-deploys

Manual redeploy:
- Render: Dashboard → Service → Manual Deploy
- Vercel: Dashboard → Deployments → Redeploy

