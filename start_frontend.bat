@echo off
cd /d "%~dp0frontend"
echo Starting DCPR Frontend...
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)
npx vite --host --port 5173
pause
