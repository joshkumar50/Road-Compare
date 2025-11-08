# MongoDB Atlas Setup Guide

## Current Status
✅ MongoDB Atlas account created  
⚠️ Connection string needs to be added to Render

---

## How to Connect MongoDB Atlas to Render

### Step 1: Get MongoDB Connection String

1. Go to https://cloud.mongodb.com
2. Click on your cluster (e.g., "Cluster0")
3. Click **"Connect"** button
4. Choose **"Connect your application"**
5. Copy the connection string, it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 2: Update Connection String

Replace `<username>` and `<password>` with your actual credentials:
```
mongodb+srv://roadcompare:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/roadcompare?retryWrites=true&w=majority
```

**Important:** Add the database name `/roadcompare` before the `?`

### Step 3: Add to Render Environment Variables

1. Go to https://dashboard.render.com
2. Select your `roadcompare-api` service
3. Go to **Environment** tab
4. Find `MONGO_URI` variable
5. Click **Edit** and paste your connection string
6. Click **Save Changes**
7. Service will automatically redeploy

### Step 4: Verify Connection

After deployment completes, check the logs for:
```
✅ MongoDB GridFS connected for large file storage
```

If you see this, MongoDB is working! If not, you'll see:
```
⚠️ MongoDB not available, using PostgreSQL only
```

---

## What MongoDB is Used For

In your Road Compare app, MongoDB Atlas provides:

### 1. **Large Video Storage (GridFS)**
- Videos > 2MB are stored in MongoDB
- Videos < 2MB are stored in PostgreSQL
- Helps avoid PostgreSQL size limits

### 2. **Analysis Results Storage**
- Detailed AI detection results
- Historical analysis data
- Better querying for large JSON documents

### 3. **Scalability**
- MongoDB free tier: 512MB storage
- Can upgrade as needed
- Better for large file storage than PostgreSQL

---

## Current Configuration

Your app is configured to use **hybrid storage**:

```python
# Small files (< 2MB)
→ PostgreSQL (Render database)

# Large files (> 2MB)  
→ MongoDB Atlas (GridFS)

# Metadata (always)
→ PostgreSQL (for fast queries)
```

---

## MongoDB Atlas Free Tier Limits

✅ **512 MB Storage**  
✅ **Shared RAM**  
✅ **No credit card required**  
⚠️ **Cluster pauses after 60 days inactivity**

**Current Usage:**
- PostgreSQL: 6.52% of 1GB (65.2 MB)
- MongoDB: Not yet connected

---

## Troubleshooting

### Issue: "MongoDB not available"

**Check these:**
1. Connection string is correct
2. Database user has read/write permissions
3. Network access allows all IPs (0.0.0.0/0)
4. Database name is included in connection string

### Issue: "Authentication failed"

**Solution:**
1. Go to MongoDB Atlas → Database Access
2. Verify username and password
3. Reset password if needed
4. Update MONGO_URI in Render

### Issue: "Connection timeout"

**Solution:**
1. Go to MongoDB Atlas → Network Access
2. Click "Add IP Address"
3. Choose "Allow Access from Anywhere" (0.0.0.0/0)
4. Save changes

---

## Optional: Test MongoDB Connection Locally

Create a test file `test_mongo.py`:

```python
from pymongo import MongoClient

# Replace with your connection string
MONGO_URI = "mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/roadcompare"

try:
    client = MongoClient(MONGO_URI)
    db = client.roadcompare
    
    # Test write
    db.test.insert_one({"test": "hello"})
    
    # Test read
    result = db.test.find_one({"test": "hello"})
    print(f"✅ MongoDB connected! Result: {result}")
    
    # Cleanup
    db.test.delete_one({"test": "hello"})
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
```

Run: `python test_mongo.py`

---

## Benefits of Using MongoDB

### For Your Hackathon:

1. **Scalability Story**
   - "We use hybrid storage for optimal performance"
   - "PostgreSQL for metadata, MongoDB for large files"

2. **Production Ready**
   - Shows understanding of database selection
   - Demonstrates microservices architecture

3. **Cost Effective**
   - Both free tiers combined = 1.5GB storage
   - No credit card needed

4. **Performance**
   - GridFS handles large files efficiently
   - PostgreSQL handles fast queries

---

## Next Steps

1. ✅ Get MongoDB connection string from Atlas
2. ✅ Add to Render as `MONGO_URI` environment variable
3. ✅ Redeploy and verify in logs
4. ✅ Test with large video upload (> 2MB)

**Note:** MongoDB is **optional** for your app. If not configured, everything will work using PostgreSQL only. MongoDB just provides better scalability for large files.
