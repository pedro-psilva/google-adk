@echo off
cd /d "%~dp0.."
python scripts\serve_backend_api.py >> backend.log 2>&1
