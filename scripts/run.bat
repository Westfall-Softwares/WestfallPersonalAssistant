@echo off
REM Westfall Personal Assistant - Windows Launcher
REM This script automatically sets up and runs the application

echo.
echo 🚀 Westfall Personal Assistant - Zero-Dependency Launcher
echo ==================================================================
echo.

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is required but not installed.
    echo Please install Node.js 16+ from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8+ from: https://python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('node --version') do echo ✅ Node.js %%i detected
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo ✅ Python %%i detected
echo.

REM Use the Node.js launcher with updated path
node electron\launcher.js

pause