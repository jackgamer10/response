@echo off
setlocal
echo [MagxxicVOT] Setting up SMS API Scanner environment...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python to continue.
    pause
    exit /b 1
)

:: Ensure pip is up to date
python -m pip install --upgrade pip

:: Install requirements
echo [MagxxicVOT] Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies. Check your internet connection and permissions.
    pause
    exit /b 1
)

echo [MagxxicVOT] Setup completed successfully!
echo [MagxxicVOT] Run 'python scanner.py' to start the scanner.
pause
endlocal
