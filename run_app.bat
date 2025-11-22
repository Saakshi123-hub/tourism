@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Multi-Agent Tourism System - Windows launcher
REM This script will create a venv (if missing), install deps, and start the server.

set VENV_DIR=.venv
set PYTHON=python
set PORT=8000

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [Setup] Creating virtual environment...
    %PYTHON% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [Error] Failed to create virtual environment. Ensure Python is installed and on PATH.
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [Error] Failed to activate virtual environment.
    exit /b 1
)

echo [Setup] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [Error] Failed to install dependencies.
    exit /b 1
)

echo [Firewall] Attempting to open TCP port %PORT% in Windows Defender Firewall (may require Administrator)...
netsh advfirewall firewall add rule name="Multi-Agent Tourism %PORT%" dir=in action=allow protocol=TCP localport=%PORT% profile=any >nul 2>&1
if errorlevel 1 (
    echo [Firewall] Could not add firewall rule automatically. If you need external access, run this as Administrator:
    echo     netsh advfirewall firewall add rule name="Multi-Agent Tourism %PORT%" dir=in action=allow protocol=TCP localport=%PORT% profile=any
)

echo [Run] Starting server on http://127.0.0.1:%PORT%/ (listening on 0.0.0.0 for LAN access)
start "Multi-Agent Tourism UI" http://127.0.0.1:%PORT%/
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port %PORT%

endlocal
