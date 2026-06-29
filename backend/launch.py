"""Launch uvicorn in a detached process (survives shell timeouts)."""
import subprocess
import sys
import os

venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    venv_python = sys.executable

proc = subprocess.Popen(
    [venv_python, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    cwd=os.path.dirname(__file__),
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    stdout=open(os.path.join(os.path.dirname(__file__), "server.log"), "w"),
    stderr=subprocess.STDOUT,
)
print(f"Backend started (PID: {proc.pid})")
print(f"Logs: {os.path.join(os.path.dirname(__file__), 'server.log')}")
