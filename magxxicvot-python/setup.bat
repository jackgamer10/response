@echo off
setlocal
echo ===================================================
echo   MagxxicVOT XII Python Edition - Setup Utility
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Python is not installed or not in your system PATH.
    echo Please install Python from python.org and try again.
    pause
    exit /b
)

echo [+] Python detected.

:: Ensure pip is available and updated
echo [+] Verifying pip...
python -m ensurepip --default-pip >nul 2>&1
python -m pip install --upgrade pip setuptools wheel --user --prefer-binary --no-warn-script-location >nul 2>&1

:: Install dependencies
echo [+] Installing required dependencies...
echo.
python -m pip install -r requirements.txt --user --prefer-binary --no-warn-script-location

if errorlevel 1 (
    echo.
    echo [!] ERROR: Failed to install one or more dependencies.
    echo Please check your internet connection and try running this again.
) else (
    echo.
    echo [+] SUCCESS: All dependencies installed correctly.
    echo [+] You can now run the tool using start.bat.
)

echo.
pause
