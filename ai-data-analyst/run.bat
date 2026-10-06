@echo off
title AI Data Analyst Launcher
chcp 65001 >nul
cls

echo ========================================================
echo         AI Data Analyst - Multi-Agent Platform
echo ========================================================
echo.

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.11+ and try again.
    pause
    exit /b 1
)

:: 2. Check Node / npm installation
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not in PATH!
    echo Please install Node.js and try again.
    pause
    exit /b 1
)

echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000...
start "AI Data Analyst - Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/3] Starting Vite Frontend on http://127.0.0.1:5173...
start "AI Data Analyst - Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Wait 3 seconds for frontend server to be ready
timeout /t 3 /nobreak >nul

echo [3/3] Opening application in your default browser...
start http://127.0.0.1:5173/

echo.
echo ========================================================
echo   Services are running!
echo   - Web App UI:      http://127.0.0.1:5173/
echo   - Backend API:     http://127.0.0.1:8000/
echo   - API Swagger UI:  http://127.0.0.1:8000/docs
echo ========================================================
echo.
echo You can close this launcher window at any time.
echo To stop the servers, close the Backend and Frontend windows.
echo.
pause
