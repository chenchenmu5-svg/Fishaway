@echo off
title Fish away Launcher
cd /d "%~dp0"

rem ---- Check Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and check "Add Python to PATH".
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem ---- Check dependencies, install if missing ----
python -c "import PySide6, winpty, pyte" >nul 2>nul
if errorlevel 1 (
    echo [Fish away] First launch: installing dependencies, please wait...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed. Check your network and retry.
        pause
        exit /b 1
    )
)

rem ---- Launch with pythonw (no console window) when available ----
where pythonw >nul 2>nul
if errorlevel 1 (
    start "" python fishaway.pyw
) else (
    start "" pythonw fishaway.pyw
)
exit /b 0
