# Quick Deploy Checklist

## Render (Backend)

1. ✅ Go to https://dashboard.render.com
2. ✅ **New +** → **Blueprint**
3. ✅ Connect: `joshkumar50/Road-Compare`
4. ✅ Render auto-creates from `render.yaml`
5. ✅ Add AWS S3 credentials:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
6. ✅ Update `FRONTEND_URL` after Vercel deploy
7. ✅ Copy API URL (e.g., `https://roadcompare-api.onrender.com`)

**Note:** The worker runs in a background thread within the API service (free alternative to a separate $7/month worker service). Jobs will be processed automatically.

## Vercel (Frontend)

1. ✅ Go to https://vercel.com
2. ✅ **Add New Project**
3. ✅ Import: `joshkumar50/Road-Compare`
4. ✅ Settings:
   - Root: `frontend`
   - Framework: Vite
5. ✅ Add env var:
   - `VITE_API=https://roadcompare-api.onrender.com/api/v1`
6. ✅ Deploy

## Test

- Frontend: `https://your-app.vercel.app`
- API: `https://roadcompare-api.onrender.com/docs`
- Health: `https://roadcompare-api.onrender.com/health`

## AWS S3 Setup (5 min)

1. Create bucket: `roadcompare-storage`
2. Create IAM user → S3 full access
3. Save Access Key + Secret
4. Add to Render env vars

Done! 🚀

