# PowerShell script to push RoadCompare to GitHub
# Repository: https://github.com/joshkumar50/Road-Compare

Write-Host "RoadCompare - GitHub Push Script" -ForegroundColor Cyan
Write-Host "Target: https://github.com/joshkumar50/Road-Compare" -ForegroundColor Yellow
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if already a git repo
if (Test-Path .git) {
    Write-Host "Git repository already initialized" -ForegroundColor Green
} else {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
}

# Add remote (will update if exists)
Write-Host "Setting up remote: origin -> https://github.com/joshkumar50/Road-Compare.git" -ForegroundColor Cyan
git remote remove origin 2>$null
git remote add origin https://github.com/joshkumar50/Road-Compare.git

# Check git status
Write-Host "`nChecking git status..." -ForegroundColor Cyan
git status

# Add all files
Write-Host "`nAdding all files..." -ForegroundColor Cyan
git add .

# Create commit
Write-Host "Creating commit..." -ForegroundColor Cyan
$commitMessage = "Initial commit: RoadCompare - Full-stack road infrastructure comparison application

- FastAPI backend with async job processing
- React frontend with Tailwind CSS
- YOLOv8 ML pipeline for road element detection
- Docker Compose setup for easy deployment
- PDF/CSV export functionality
- Evaluation scripts and metrics dashboard"

git commit -m $commitMessage

# Set main branch
Write-Host "Setting main branch..." -ForegroundColor Cyan
git branch -M main

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
Write-Host "You may be prompted for GitHub credentials." -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "Repository: https://github.com/joshkumar50/Road-Compare" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "1. Authentication required - use GitHub Personal Access Token" -ForegroundColor Yellow
    Write-Host "2. Repository might not exist - create it at https://github.com/new" -ForegroundColor Yellow
    Write-Host "3. Check your internet connection" -ForegroundColor Yellow
}


