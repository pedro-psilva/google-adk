@echo off
setlocal

cd /d "%~dp0.."

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
set "FALLBACK_PYTHON=C:\Users\iebt\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if exist "%VENV_PYTHON%" (
  "%VENV_PYTHON%" scripts\serve_backend_api.py >> backend.log 2>&1
  exit /b %errorlevel%
)

if exist "%FALLBACK_PYTHON%" (
  "%FALLBACK_PYTHON%" scripts\serve_backend_api.py >> backend.log 2>&1
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\serve_backend_api.py >> backend.log 2>&1
  exit /b %errorlevel%
)

echo Python nao encontrado. Recrie a .venv ou instale um interpretador compativel.
exit /b 1
