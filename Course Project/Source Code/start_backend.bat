@echo off
cd /d "%~dp0"
echo Starting AURA Backend on http://localhost:8000
echo API Docs: http://localhost:8000/docs
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
pause
