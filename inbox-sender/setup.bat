@echo off
setlocal
title magxxicVox Inbox Sender Setup

echo ===================================================
echo   magxxicVox Inbox Sender Setup
echo ===================================================
echo.

:: Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Node.js is not installed. Please install it from https://nodejs.org/
    pause
    exit /b 1
)

echo [+] Node.js detected.
echo [+] Installing/Updating dependencies...
echo.

call npm install systeminformation bwip-js axios node-html-to-image nodemailer randomstring html-pdf-node html-minifier socks-proxy-agent socks @aws-sdk/client-ses nodemailer-mailgun-transport nodemailer-sendgrid-transport @smithy/node-http-handler

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
