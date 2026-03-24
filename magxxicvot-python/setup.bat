@echo off
echo Setting up MagxxicVOT XII Python Edition...

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Ensure pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [!] pip is not installed. Attempting to install pip...
    python -m ensurepip --default-pip
)

echo [+] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] Failed to install dependencies.
) else (
    echo [+] Setup complete. Run start.bat to begin.
)

pause
