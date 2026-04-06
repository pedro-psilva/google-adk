@echo off
cd /d "%~dp0..\frontend"
"C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1 --port 4173 >> "..\frontend.log" 2>&1
