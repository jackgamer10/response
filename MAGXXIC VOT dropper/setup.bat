@echo off
title MAGXXIC VOT Dropper - Setup
cls
echo ==========================================
echo    MAGXXIC VOT DROPPER SETUP
echo ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.x and try again.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
python -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Setup complete!
    echo You can now run start.bat to begin.
) else (
    echo.
    echo [ERROR] Failed to install dependencies.
)

pause
