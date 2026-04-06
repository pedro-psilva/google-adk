@echo off
cd /d "%~dp0.."
"C:\Users\iebt\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts\serve_backend_api.py >> backend.log 2>&1
