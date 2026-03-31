@echo off
setlocal
title magxxicVox Inbox Sender Setup (Python)

echo ===================================================
echo   magxxicVox Inbox Sender Setup (Python)
echo ===================================================
echo.

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed. Please install it from https://www.python.org/
    pause
    exit /b 1
)

echo [+] Python detected.
echo [+] Installing dependencies...
echo.

python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [!] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [+] Setup complete!
echo [+] You can now run the sender using: start.bat
echo.
pause
exit /b 0
