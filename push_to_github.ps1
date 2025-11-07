# PowerShell script to push RoadCompare to GitHub
# Repository: https://github.com/joshkumar50/Road-Compare
# This script automatically commits and pushes changes

param(
    [string]$Message = "Update: RoadCompare improvements and bug fixes",
    [switch]$Force = $false
)

Write-Host "🚀 RoadCompare - GitHub Auto-Push Script" -ForegroundColor Cyan
Write-Host "Target: https://github.com/joshkumar50/Road-Compare" -ForegroundColor Yellow
Write-Host "Commit Message: $Message" -ForegroundColor Green
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if already a git repo
if (Test-Path .git) {
    Write-Host "✓ Git repository already initialized" -ForegroundColor Green
} else {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
    git config user.email "roadcompare@hackathon.dev"
    git config user.name "RoadCompare Bot"
}

# Set up remote
Write-Host "`nSetting up remote..." -ForegroundColor Cyan
$remoteUrl = "https://github.com/joshkumar50/Road-Compare.git"
$existingRemote = git config --get remote.origin.url 2>$null
if ($existingRemote -ne $remoteUrl) {
    git remote remove origin 2>$null
    git remote add origin $remoteUrl
    Write-Host "✓ Remote configured: $remoteUrl" -ForegroundColor Green
} else {
    Write-Host "✓ Remote already configured" -ForegroundColor Green
}

# Check git status
Write-Host "`nChecking git status..." -ForegroundColor Cyan
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✓ No changes to commit" -ForegroundColor Yellow
    exit 0
}

Write-Host "Changes detected:" -ForegroundColor Yellow
Write-Host $status

# Add all files
Write-Host "`nStaging files..." -ForegroundColor Cyan
git add .
Write-Host "✓ Files staged" -ForegroundColor Green

# Create commit
Write-Host "Creating commit..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$fullMessage = "$Message`n`nTimestamp: $timestamp"
git commit -m $fullMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Commit failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Commit created" -ForegroundColor Green

# Ensure main branch
Write-Host "Setting main branch..." -ForegroundColor Cyan
git branch -M main 2>$null
Write-Host "✓ Main branch set" -ForegroundColor Green

# Pull before push
Write-Host "`nPulling latest changes..." -ForegroundColor Cyan
git pull origin main --allow-unrelated-histories 2>$null
Write-Host "✓ Pull complete" -ForegroundColor Green

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
if ($Force) {
    git push -u origin main --force
} else {
    git push -u origin main
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "Repository: https://github.com/joshkumar50/Road-Compare" -ForegroundColor Cyan
    Write-Host "Commit: $(git rev-parse --short HEAD)" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ Push failed. Troubleshooting:" -ForegroundColor Red
    Write-Host "1. Check authentication: Use GitHub Personal Access Token" -ForegroundColor Yellow
    Write-Host "2. Ensure repository exists: https://github.com/new" -ForegroundColor Yellow
    Write-Host "3. Check internet connection" -ForegroundColor Yellow
    Write-Host "4. Try: git push -u origin main --force" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✓ Script completed successfully!" -ForegroundColor Green


