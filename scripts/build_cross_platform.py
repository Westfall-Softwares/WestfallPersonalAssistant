#!/usr/bin/env python3
"""
Cross-Platform Deployment Script for Westfall Entrepreneur Assistant
Builds and packages the application for Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path

def get_platform_info():
    """Get current platform information"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if arch in ['x86_64', 'amd64']:
        arch = 'x64'
    elif arch in ['aarch64', 'arm64']:
        arch = 'arm64'
    
    return system, arch

def run_command(cmd, cwd=None):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return False

def build_cross_platform():
    """Build the application for cross-platform deployment"""
    
    print("🏗️  Westfall Entrepreneur Assistant - Cross-Platform Build")
    print("=" * 60)
    
    system, arch = get_platform_info()
    print(f"Building on: {system} {arch}")
    print()
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    for dir_name in ['dist', 'build']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    
    # Check Node.js
    if not run_command(['node', '--version']):
        print("❌ Node.js not found. Please install Node.js 16+")
        return False
    
    # Check Python
    if not run_command(['python3', '--version']):
        print("❌ Python 3 not found. Please install Python 3.8+")
        return False
    
    # Install Node.js dependencies
    print("📦 Installing Node.js dependencies...")
    if not run_command(['npm', 'install']):
        print("❌ Failed to install Node.js dependencies")
        return False
    
    # Install Python dependencies
    print("🐍 Installing Python dependencies...")
    if not run_command(['pip3', 'install', '-r', 'requirements.txt']):
        print("❌ Failed to install Python dependencies")
        return False
    
    # Build React frontend
    print("⚛️  Building React frontend...")
    if not run_command(['npm', 'run', 'build-react']):
        print("❌ Failed to build React frontend")
        return False
    
    # Create platform-specific builds
    print("🎯 Creating platform-specific builds...")
    
    # Create base distribution directory
    dist_dir = Path('dist')
    dist_dir.mkdir(exist_ok=True)
    
    # Build for current platform
    build_for_platform(system, arch, dist_dir)
    
    # If possible, create universal builds
    if system == 'linux':
        print("🐧 Creating Linux builds...")
        create_linux_packages(dist_dir)
    elif system == 'darwin':
        print("🍎 Creating macOS builds...")
        create_macos_packages(dist_dir)
    elif system == 'windows':
        print("🪟 Creating Windows builds...")
        create_windows_packages(dist_dir)
    
    print()
    print("✅ Cross-platform build complete!")
    print(f"📁 Built packages are in: {dist_dir.absolute()}")
    
    return True

def build_for_platform(system, arch, dist_dir):
    """Build for a specific platform"""
    platform_dir = dist_dir / f"westfall-entrepreneur-assistant-{system}-{arch}"
    platform_dir.mkdir(exist_ok=True)
    
    # Copy core files
    core_files = [
        'build', 'backend', 'main.js', 'preload.js', 'package.json',
        'westfall.png', 'launcher.js', 'requirements.txt'
    ]
    
    for file_path in core_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.copytree(file_path, platform_dir / file_path, dirs_exist_ok=True)
            else:
                shutil.copy2(file_path, platform_dir / file_path)
    
    # Copy platform-specific files
    if system == 'windows':
        if os.path.exists('run.bat'):
            shutil.copy2('run.bat', platform_dir / 'run.bat')
        create_windows_installer_script(platform_dir)
    else:
        if os.path.exists('run.sh'):
            shutil.copy2('run.sh', platform_dir / 'run.sh')
            os.chmod(platform_dir / 'run.sh', 0o755)
        create_unix_installer_script(platform_dir, system)
    
    # Create platform-specific package.json
    create_platform_package_json(platform_dir, system, arch)
    
    # Create README
    create_platform_readme(platform_dir, system)

def create_linux_packages(dist_dir):
    """Create Linux-specific packages"""
    
    # Create AppImage if available
    try:
        print("📦 Creating AppImage...")
        # This would require appimagetool
        pass
    except Exception:
        print("⚠️  AppImage creation skipped (appimagetool not available)")
    
    # Create .deb package structure
    try:
        print("📦 Creating .deb package structure...")
        deb_dir = dist_dir / "debian-package"
        deb_dir.mkdir(exist_ok=True)
        
        # Create DEBIAN control directory
        debian_control_dir = deb_dir / "DEBIAN"
        debian_control_dir.mkdir(exist_ok=True)
        
        # Create control file
        control_content = """Package: westfall-entrepreneur-assistant
Version: 2.0.0
Section: office
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8), nodejs (>= 16)
Maintainer: Westfall Softwares <contact@westfallsoftwares.com>
Description: AI-powered entrepreneur assistant with Tailor Pack extensions
 A comprehensive business assistant with cross-platform support,
 extensible Tailor Pack system, and integrated AI capabilities.
"""
        with open(debian_control_dir / "control", "w") as f:
            f.write(control_content)
        
        print("✅ Debian package structure created")
    except Exception as e:
        print(f"⚠️  Debian package creation failed: {e}")

def create_macos_packages(dist_dir):
    """Create macOS-specific packages"""
    try:
        print("📦 Creating macOS app bundle...")
        
        app_bundle = dist_dir / "Westfall Entrepreneur Assistant.app"
        contents = app_bundle / "Contents"
        macos_dir = contents / "MacOS"
        resources = contents / "Resources"
        
        for dir_path in [macos_dir, resources]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create Info.plist
        info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>westfall-assistant</string>
    <key>CFBundleIdentifier</key>
    <string>com.westfall.entrepreneur-assistant</string>
    <key>CFBundleName</key>
    <string>Westfall Entrepreneur Assistant</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleIconFile</key>
    <string>westfall.icns</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>"""
        
        with open(contents / "Info.plist", "w") as f:
            f.write(info_plist)
        
        print("✅ macOS app bundle created")
    except Exception as e:
        print(f"⚠️  macOS package creation failed: {e}")

def create_windows_packages(dist_dir):
    """Create Windows-specific packages"""
    try:
        print("📦 Creating Windows installer structure...")
        
        # Create NSIS installer script if possible
        nsis_script = dist_dir / "installer.nsi"
        nsis_content = '''
!define APPNAME "Westfall Entrepreneur Assistant"
!define COMPANYNAME "Westfall Softwares"
!define DESCRIPTION "AI-powered entrepreneur assistant"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0

Name "${APPNAME}"
OutFile "westfall-entrepreneur-assistant-setup.exe"
InstallDir "$PROGRAMFILES\\${COMPANYNAME}\\${APPNAME}"

Section "install"
    SetOutPath $INSTDIR
    File /r "westfall-entrepreneur-assistant-windows-x64\\*"
    
    CreateDirectory "$SMPROGRAMS\\${COMPANYNAME}"
    CreateShortCut "$SMPROGRAMS\\${COMPANYNAME}\\${APPNAME}.lnk" "$INSTDIR\\run.bat"
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\run.bat"
SectionEnd
'''
        with open(nsis_script, "w") as f:
            f.write(nsis_content)
        
        print("✅ Windows installer structure created")
    except Exception as e:
        print(f"⚠️  Windows package creation failed: {e}")

def create_windows_installer_script(platform_dir):
    """Create Windows installation script"""
    script_content = '''@echo off
echo Westfall Entrepreneur Assistant - Setup
echo =====================================
echo.

echo Checking dependencies...
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js 16+ first.
    pause
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo Installing dependencies...
call npm install
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Setup complete! You can now run the application.
echo Double-click run.bat to start.
pause
'''
    with open(platform_dir / "setup.bat", "w") as f:
        f.write(script_content)

def create_unix_installer_script(platform_dir, system):
    """Create Unix installation script"""
    script_content = f'''#!/bin/bash

echo "Westfall Entrepreneur Assistant - Setup"
echo "======================================"
echo ""

echo "Checking dependencies..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

echo "Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Node.js dependencies"
    exit 1
fi

pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "Setup complete! You can now run the application."
echo "Run ./run.sh to start."
'''
    script_path = platform_dir / "setup.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)

def create_platform_package_json(platform_dir, system, arch):
    """Create platform-specific package.json"""
    package_data = {
        "name": f"westfall-entrepreneur-assistant-{system}",
        "version": "2.0.0",
        "description": f"Westfall Entrepreneur Assistant for {system.title()}",
        "main": "main.js",
        "scripts": {
            "start": "electron .",
            "launch": "node launcher.js"
        },
        "author": "Westfall Softwares",
        "license": "MIT",
        "platform": {
            "os": system,
            "arch": arch
        }
    }
    
    with open(platform_dir / "package.json", "w") as f:
        json.dump(package_data, f, indent=2)

def create_platform_readme(platform_dir, system):
    """Create platform-specific README"""
    readme_content = f"""# Westfall Entrepreneur Assistant

Welcome to your cross-platform entrepreneur assistant with AI capabilities and Tailor Pack support!

## System Requirements

- **{system.title()}** operating system
- **Node.js** 16 or higher
- **Python** 3.8 or higher

## Quick Start

1. **First-time setup:**
   - Run `setup.{"bat" if system == "windows" else "sh"}` to install dependencies

2. **Start the application:**
   - Run `run.{"bat" if system == "windows" else "sh"}` to launch

## Features

- 🤖 **AI-Powered Assistant** - Get intelligent help with business tasks
- 📦 **Tailor Pack System** - Extend functionality with business-specific modules
- 🌐 **Cross-Platform** - Works on Windows, macOS, and Linux
- 📊 **Business Dashboard** - Track KPIs and business metrics
- 🔐 **Secure** - Your data stays local and private

## Getting Help

- Press `F1` in the application for built-in help
- Visit our documentation for Tailor Pack development
- Check the status bar for quick tips and shortcuts

## Tailor Packs

This assistant supports Tailor Packs - specialized business modules that add functionality:

- **Marketing Packs** - Campaign tracking, social media, lead generation
- **Sales Packs** - Pipeline management, proposals, customer onboarding
- **Finance Packs** - Advanced accounting, tax prep, financial planning
- **Operations Packs** - Project management, team collaboration, automation

Import Tailor Packs through the **📦 Tailor Packs** menu in the application.

---

*Westfall Entrepreneur Assistant v2.0.0*
*Built for entrepreneurs who demand efficiency and intelligence in their business tools.*
"""
    
    with open(platform_dir / "README.md", "w") as f:
        f.write(readme_content)

if __name__ == "__main__":
    if build_cross_platform():
        print("\n🎉 Build successful!")
        sys.exit(0)
    else:
        print("\n❌ Build failed!")
        sys.exit(1)