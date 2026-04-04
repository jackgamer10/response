@echo off
setlocal

echo [*] Launching Admin Activation Kit...
python generator.py
if %errorlevel% neq 0 (
    echo [-] Python is not installed or not in PATH.
    pause
    exit /b 1
)

pause
endlocal
