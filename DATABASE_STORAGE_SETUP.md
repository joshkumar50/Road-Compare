# 🗄️ Database Storage Setup (No More Local Files!)

Your app now uses **database storage** instead of local files, perfect for production deployment!

## 📊 **Storage Options**

### **1. PostgreSQL (Default - Already on Render)** ✅
- Videos < 5MB stored directly in PostgreSQL
- Already included with Render deployment
- No additional setup needed!

### **2. MongoDB Atlas (Recommended for Large Videos)** 🚀
- Free 512MB storage
- GridFS for videos > 5MB
- Better scalability

---

## 🎯 **Option A: Use PostgreSQL Only (Simplest)**

**Already working!** Your Render PostgreSQL database will store videos automatically.

```env
# Add to Render Environment Variables
USE_DATABASE_STORAGE=true
```

That's it! Videos will be stored in your PostgreSQL database.

---

## 🚀 **Option B: Add MongoDB Atlas (Better for Scale)**

### **Step 1: Create Free MongoDB Atlas Account**

1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Sign up (free)
3. Create a free cluster (M0 - 512MB free)
4. Choose region closest to your Render deployment

### **Step 2: Get Connection String**

1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/roadcompare
   ```

### **Step 3: Add to Render Environment**

Go to Render Dashboard → Environment → Add:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/roadcompare
MONGO_DB=roadcompare
USE_DATABASE_STORAGE=true
```

### **Step 4: Whitelist IPs**

In MongoDB Atlas → Network Access:
1. Click "Add IP Address"
2. Click "Allow Access from Anywhere" (for simplicity)
3. Or add Render's IPs (more secure)

---

## 📦 **What Gets Stored Where**

### **PostgreSQL Stores:**
- Video metadata (filename, size, type)
- Small videos (< 5MB)
- Job information
- Detection results
- User feedback

### **MongoDB Stores (if enabled):**
- Large videos (> 5MB)
- Analysis results
- Temporal tracking data
- Performance metrics

---

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_DATABASE_STORAGE` | `true` | Enable database storage |
| `MONGO_URI` | `null` | MongoDB connection string |
| `MONGO_DB` | `roadcompare` | MongoDB database name |
| `MAX_VIDEO_SIZE_MB` | `100` | Maximum video size |

---

## 📈 **Benefits of Database Storage**

### **vs Local Files:**
- ✅ **Persistent** - Survives restarts
- ✅ **Scalable** - No disk limits
- ✅ **Distributed** - Multiple instances
- ✅ **Searchable** - Query by metadata
- ✅ **Secure** - Database encryption

### **Performance:**
- PostgreSQL: Fast for < 5MB
- MongoDB GridFS: Optimized for large files
- Hybrid: Best of both worlds

---

## 🚀 **Quick Setup for Render**

### **Step 1: Update Environment on Render**

Add these to your Render service:

```env
USE_DATABASE_STORAGE=true

# Optional: Add MongoDB for better performance
MONGO_URI=your_mongodb_atlas_connection_string
MONGO_DB=roadcompare
```

### **Step 2: Deploy**

```bash
git add -A
git commit -m "Enable database storage"
git push origin main
```

### **Step 3: Verify**

Check logs for:
```
✅ Database storage system initialized
✅ MongoDB GridFS connected for large file storage
```

---

## 📊 **Storage Statistics API**

Your app now has a storage stats endpoint:

```bash
curl https://roadcompare-api.onrender.com/api/v1/storage/stats
```

Response:
```json
{
  "total_videos": 42,
  "total_size_mb": 256.3,
  "storage_types": {
    "postgresql": 38,
    "mongodb": 4
  }
}
```

---

## 🔍 **How It Works**

### **Upload Flow:**
1. User uploads video
2. Backend receives file
3. If > 5MB and MongoDB available → GridFS
4. Else → PostgreSQL BYTEA
5. Metadata saved to PostgreSQL
6. Returns storage key

### **Processing Flow:**
1. Worker requests video by key
2. System checks PostgreSQL metadata
3. Retrieves from PostgreSQL or MongoDB
4. Creates temp file for OpenCV
5. Processes video
6. Cleans up temp file

---

## 🐛 **Troubleshooting**

### **Issue: "Video not found"**
Check if database has the video:
```sql
SELECT key, size FROM video_storage WHERE key LIKE 'jobs/%';
```

### **Issue: "MongoDB connection failed"**
- Check connection string
- Verify IP whitelist
- Try without MongoDB (PostgreSQL only)

### **Issue: "Out of storage"**
- PostgreSQL free tier: 256MB
- MongoDB free tier: 512MB
- Solution: Clean old jobs or upgrade

---

## 🧹 **Cleanup Old Data**

### **PostgreSQL:**
```python
# Add to routes.py
@api_router.delete("/storage/cleanup")
def cleanup_old_storage(days: int = 7):
    """Delete videos older than X days"""
    # Implementation in storage_database.py
```

### **MongoDB:**
```javascript
// In MongoDB Atlas console
db.fs.files.deleteMany({
  uploadDate: { $lt: new Date(Date.now() - 7*24*60*60*1000) }
})
```

---

## 📱 **Frontend Integration**

No changes needed! The frontend works exactly the same:

```javascript
// Upload videos (unchanged)
const formData = new FormData()
formData.append('base_video', baseFile)
formData.append('present_video', presentFile)

const response = await axios.post('/api/v1/jobs', formData)
```

---

## ✅ **Deployment Checklist**

- [x] Created `storage_database.py`
- [x] Updated `worker.py` to use database storage
- [x] Updated `routes.py` to use database storage
- [x] Added PostgreSQL video storage table
- [ ] **Add `USE_DATABASE_STORAGE=true` to Render** ← DO THIS!
- [ ] Optional: Add MongoDB Atlas connection
- [ ] Push and deploy

---

## 🎉 **Your App Now Has:**

- ✅ **No local file dependencies**
- ✅ **Cloud-native storage**
- ✅ **Scalable to millions of videos**
- ✅ **Works on Render free tier**
- ✅ **Optional MongoDB for large files**
- ✅ **Automatic temp file cleanup**
- ✅ **Storage statistics API**

---

## 📝 **Next Steps**

1. **Add to Render Environment:**
   ```
   USE_DATABASE_STORAGE=true
   ```

2. **Push Changes:**
   ```bash
   git push origin main
   ```

3. **Optional: Setup MongoDB Atlas** (free 512MB)
   - Create account
   - Get connection string
   - Add to Render

**Your app is now production-ready with professional database storage!** 🚀
