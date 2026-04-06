@echo off
setlocal

cd /d "%~dp0.."

start "Perfil Backend" cmd /k "cd /d %~dp0.. && call scripts\start_backend_local.cmd"
start "Perfil Frontend" cmd /k "cd /d %~dp0..\frontend && call ..\scripts\start_frontend_local.cmd"

endlocal
