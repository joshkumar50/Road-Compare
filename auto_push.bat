@echo off
REM Auto-push script for RoadCompare
cd /d "c:\Project Debug\RoadCompare"

echo.
echo ========================================
echo RoadCompare - Auto Push to GitHub
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Git found

REM Initialize git if needed
if not exist .git (
    echo Initializing git repository...
    git init
    git config user.email "roadcompare@hackathon.dev"
    git config user.name "RoadCompare Bot"
)

REM Set up remote
echo Setting up remote...
git remote remove origin 2>nul
git remote add origin https://github.com/joshkumar50/Road-Compare.git

REM Check for changes
echo.
echo Checking for changes...
git status --porcelain
if errorlevel 1 (
    echo No changes to commit
    exit /b 0
)

REM Stage and commit
echo.
echo Staging files...
git add .

echo Creating commit...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
git commit -m "feat: Full end-to-end functionality with enhanced UI and delete operations [%mydate% %mytime%]"

REM Set main branch
echo Setting main branch...
git branch -M main 2>nul

REM Pull and push
echo.
echo Pulling latest changes...
git pull origin main --allow-unrelated-histories 2>nul

echo Pushing to GitHub...
git push -u origin main

if errorlevel 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Pushed to GitHub!
    echo Repository: https://github.com/joshkumar50/Road-Compare
    echo ========================================
    echo.
) else (
    echo.
    echo [ERROR] Push failed!
    echo Check your GitHub credentials and internet connection.
    echo.
)

pause
