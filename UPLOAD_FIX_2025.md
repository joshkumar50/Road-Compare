# Upload Fix - January 2025

## Problem Summary

You were experiencing persistent **CORS errors** and **502 Gateway Timeout** errors during video uploads to your RoadCompare API deployed on Render free tier. The issues were:

1. ❌ **CORS Policy Blocks** - Missing 'Access-Control-Allow-Origin' header
2. ❌ **502 Bad Gateway** - Render edge proxy dropping connections during chunked uploads
3. ❌ **Network Errors** - ERR_FAILED on upload requests
4. ❌ **Upload Failures** - Even with retries, exponential backoff, and throttling

## Root Cause

The chunked upload approach was overwhelming Render's free tier edge gateway with high-frequency requests. Even with small 1MB chunks and throttling, the gateway would intermittently fail and strip CORS headers from error responses, causing both 502 and CORS errors.

## Solution Implemented

### 1. **Hybrid Upload Strategy** 

The frontend now intelligently chooses the upload method based on file size:

- **Files < 30MB total**: Use direct upload to `/api/v1/jobs` (fast, reliable, single request)
- **Files ≥ 30MB total**: Use chunked upload to `/api/v1/uploads/*` (slower but handles large files)

### 2. **Optimized Direct Upload** (`/api/v1/jobs`)

- Increased chunk read size to 5MB (fewer round trips)
- Extended timeout to 40 seconds per chunk
- Concurrent upload of both videos (faster for smaller files)
- Better error messages guiding users to smaller files

### 3. **Improved Chunked Upload** (`/api/v1/uploads/chunk`)

- Reduced retries from 5 to 3 (fail faster)
- Increased throttle between chunks to 200ms
- Added request timing logs for debugging
- Better error messages showing which chunk failed
- Sequential upload (not parallel) to reduce gateway load

### 4. **Enhanced Error Handling**

- Specific error messages for 502, network failures, and timeouts
- User guidance to try smaller files
- Retry logic with exponential backoff
- Chunk-level failure reporting

### 5. **User Guidance**

- Added tip in UI recommending files under 50MB
- File size validation before upload starts
- Clear error messages explaining issues

## Files Modified

### Frontend (`frontend/src/App.jsx`)
- ✅ Hybrid upload strategy (direct vs chunked)
- ✅ Better error handling and messages
- ✅ User guidance for file sizes
- ✅ Reduced chunked upload retries
- ✅ Increased throttling between chunks

### Backend (`backend/app/routes.py`)
- ✅ Optimized `/uploads/chunk` with timing logs
- ✅ Improved `/jobs` direct upload with larger chunks
- ✅ Better timeout handling (25s for chunk, 40s for direct)
- ✅ Added request performance logging

### Backend (`backend/app/main.py`)
- ✅ Added `/cors-check` endpoint for debugging
- ✅ Kept wildcard CORS (`*`) and manual CORS middleware
- ✅ OPTIONS handler for preflight requests

## Deployment Steps

### 1. **Commit and Push Changes**

```bash
git add .
git commit -m "Fix upload errors: hybrid upload strategy + optimized timeouts"
git push origin main
```

### 2. **Deploy to Render**

Render will automatically deploy from your GitHub push. Monitor the deployment:

- Go to https://dashboard.render.com
- Check your `roadcompare-api` service
- Wait for "Live" status
- Check logs for any errors

### 3. **Verify CORS is Working**

Open browser console on your Vercel frontend and test:

```javascript
fetch('https://roadcompare-api.onrender.com/cors-check')
  .then(r => r.json())
  .then(data => console.log('CORS test:', data))
  .catch(err => console.error('CORS test failed:', err))
```

Expected output: `{cors: "enabled", origin: "*", message: "If you can see this..."}`

If this fails with CORS error, Render deployment is broken.

### 4. **Test Small File Upload** (< 30MB total)

1. Go to your Vercel frontend: https://road-compare.vercel.app
2. Upload TWO small videos (e.g., 10MB each)
3. This should use the direct upload path
4. Check browser console - should see: `Using direct upload for small files`
5. Upload should complete without errors

### 5. **Test Large File Upload** (≥ 30MB total)

1. Upload TWO larger videos (e.g., 20MB each = 40MB total)
2. This should use the chunked upload path
3. Check browser console - should see: `Using chunked upload for large files`
4. Should see chunk progress: `Base video: 10/20 chunks uploaded`
5. Upload should complete without 502 or CORS errors

## Expected Behavior

✅ **Small files (< 30MB)**: Fast, single-request upload via `/jobs`  
✅ **Large files (≥ 30MB)**: Chunked upload with progress logging  
✅ **No CORS errors**: All responses include `Access-Control-Allow-Origin: *`  
✅ **No 502 errors**: Properly handled timeouts and retries  
✅ **Clear error messages**: Users know what to do if upload fails  

## Troubleshooting

### Still Getting CORS Errors?

1. **Check Render deployment status**: Make sure service is "Live"
2. **Test CORS endpoint**: Use the JavaScript test above
3. **Check Render logs**: Look for errors during startup
4. **Verify environment variables**: Check `CORS_ORIGINS` is set in Render dashboard

### Still Getting 502 Errors?

1. **Check file sizes**: Are you trying to upload > 100MB files?
2. **Check Render service health**: Service might be sleeping or overloaded
3. **Try direct upload**: If files are < 30MB, it should use direct upload automatically
4. **Check browser console**: Look for which chunk is failing
5. **Reduce file size**: Compress videos to < 50MB each

### Uploads Timing Out?

1. **Use smaller files**: Compress videos or trim length
2. **Check network connection**: Upload speed affects timeouts
3. **Try direct upload**: < 30MB files use faster method
4. **Wait and retry**: Render free tier can be slow during peak times

## Recommended File Sizes

| File Size (each) | Total Size | Method | Expected Time | Reliability |
|-----------------|------------|--------|---------------|-------------|
| < 10MB | < 20MB | Direct | ~10-20s | ⭐⭐⭐⭐⭐ Excellent |
| 10-25MB | 20-50MB | Direct | ~30-60s | ⭐⭐⭐⭐ Very Good |
| 25-50MB | 50-100MB | Chunked | ~2-5min | ⭐⭐⭐ Good |
| > 50MB | > 100MB | ❌ Not Supported | N/A | ❌ Will Fail |

## Long-Term Solutions

If you continue to have issues with Render's free tier gateway:

### Option 1: Upgrade Render Plan
- Paid plans have better gateway stability
- Higher timeout limits
- More consistent performance

### Option 2: Use Cloud Storage for Uploads
- Implement presigned URL uploads to S3/R2/GCS
- Users upload directly to cloud storage (bypasses Render)
- Backend only processes metadata and job creation
- Much more reliable for large files

### Option 3: Alternative Hosting
- Consider Railway, Fly.io, or self-hosting
- Some platforms handle uploads better than others
- Free tiers vary in capabilities

## Testing Checklist

Before declaring victory, test these scenarios:

- [ ] Upload 2 small videos (5MB each) - should use direct upload
- [ ] Upload 2 medium videos (20MB each) - should use direct upload
- [ ] Upload 2 large videos (40MB each) - should use chunked upload
- [ ] Check browser console for errors during each upload
- [ ] Verify CORS check endpoint works
- [ ] Verify `/health` endpoint returns OK
- [ ] Check Render logs for any errors
- [ ] Verify uploaded videos process correctly

## Summary

The fix implements a smart hybrid approach:
- **Small files**: Fast direct upload (bypasses chunking overhead)
- **Large files**: Reliable chunked upload (with better error handling)
- **Clear guidance**: Users know file size limits upfront
- **Better errors**: Actionable messages when things fail

This should eliminate the CORS and 502 errors you were seeing!

---

**Need help?** Check Render logs or browser console errors for specific failure details.
