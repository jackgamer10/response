@echo off
setlocal
echo ===================================================
echo   MagxxicVOT XII Node.js Edition - Setup Utility
echo ===================================================
echo.

:: Check for Node.js
node -v >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Node.js is not installed or not in your system PATH.
    echo Please install Node.js from nodejs.org and try again.
    pause
    exit /b
)

echo [+] Node.js detected.

:: Install dependencies
echo [+] Installing required dependencies...
echo.
npm install

if errorlevel 1 (
    echo.
    echo [!] ERROR: npm install failed.
    echo Please check your internet connection and try running this again.
) else (
    echo.
    echo [+] SUCCESS: All dependencies installed correctly.
    echo [+] You can now run the tool using start.bat.
)

echo.
pause
