@echo off
cd /d "%~dp0backend"
echo Starting DCPR Backend...
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\pip install -r requirements.txt
)
call venv\Scripts\uvicorn app.main:app --reload --port 8000
pause
