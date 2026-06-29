@echo off
title DCPR Knowledge Platform
cd /d "%~dp0"

echo ========================================
echo  DCPR Knowledge Platform - Production
echo ========================================
echo.

:: Check environment
echo [1/4] Checking Python...
python --version >nul 2>&1 || ( echo ERROR: Python not found & pause & exit /b 1 )
echo       OK

echo [2/4] Checking Node.js...
node --version >nul 2>&1 || ( echo ERROR: Node.js not found & pause & exit /b 1 )
echo       OK

:: Backend setup
echo [3/4] Setting up backend...
if not exist "backend\venv\Scripts\python.exe" (
    echo       Creating virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\pip install -r requirements.txt >nul
    cd ..
)
echo       OK

:: Frontend setup
echo [4/4] Setting up frontend...
if not exist "frontend\node_modules" (
    echo       Installing dependencies...
    cd frontend
    call npm install >nul
    cd ..
)
echo       OK

echo.
echo ========================================
echo  Starting servers...
echo ========================================
echo.

:: Start backend (in background)
start "DCPR Backend" /B /MIN cmd /c "cd /d %~dp0backend && call venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info" > backend\server.log 2>&1

:: Wait for backend to be ready
echo Waiting for backend...
:wait_backend
timeout /t 2 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" 2>nul && (
    echo       Backend running at http://localhost:8000
) || (
    goto wait_backend
)

:: Start frontend
start "DCPR Frontend" /B /MIN cmd /c "cd /d %~dp0frontend && npx vite --host --port 5173" > frontend\vite.log 2>&1

timeout /t 3 /nobreak >nul
echo       Frontend running at http://localhost:5173

echo.
echo ========================================
echo  Open http://localhost:5173 in your browser
echo  Backend API: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to stop all servers...
pause >nul

:: Cleanup
echo Stopping servers...
taskkill /f /fi "WINDOWTITLE eq DCPR Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq DCPR Frontend" >nul 2>&1
echo Done.
