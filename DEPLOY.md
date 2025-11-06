# Deployment & GitHub Setup

## Push to GitHub

### 1. Install Git (if not installed)
Download from: https://git-scm.com/download/win

### 2. Initialize repository and push

```powershell
# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: RoadCompare full-stack application"

# Add your GitHub remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Create GitHub repository first
1. Go to https://github.com/new
2. Create a new repository (e.g., `RoadCompare`)
3. Don't initialize with README (we already have one)
4. Copy the repository URL and use it in step 2 above

## Alternative: Use GitHub Desktop
1. Install GitHub Desktop: https://desktop.github.com/
2. File → Add Local Repository → Select this folder
3. Commit all files
4. Publish to GitHub

## After pushing, update CI workflow
The `.github/workflows/ci.yml` will automatically run on push if you have GitHub Actions enabled.


