#!/usr/bin/env python3
"""
Build script for Westfall Personal Assistant
Builds the backend binary and Electron app
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"  in: {cwd}")
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def build_backend():
    """Build the backend binary with PyInstaller."""
    print("=== Building Backend ===")
    
    # Build using the spec file
    cmd = "pyinstaller --noconfirm --clean backend/westfall-backend.spec"
    run_command(cmd)
    
    # Copy to dist-backend
    src = Path("dist/westfall-backend.exe")
    dst = Path("dist-backend/westfall-backend.exe")
    dst.parent.mkdir(exist_ok=True)
    
    if src.exists():
        import shutil
        shutil.copy2(src, dst)
        print(f"Backend binary copied to {dst}")
    else:
        print("ERROR: Backend binary not found!")
        sys.exit(1)

def build_electron():
    """Build the Electron app."""
    print("=== Building Electron App ===")
    
    # Set environment variables to disable code signing
    env = os.environ.copy()
    env["CSC_IDENTITY_AUTO_DISCOVERY"] = "false"
    env["WIN_CSC_LINK"] = ""
    
    cmd = "npx electron-builder --win --publish never"
    result = run_command(cmd, cwd="electron", check=False)
    
    if result.returncode != 0:
        print("Electron build had issues but may have produced artifacts")
        print("Checking for dist directory...")
        
        dist_dir = Path("electron/dist")
        if dist_dir.exists():
            print("Electron build artifacts found:")
            for item in dist_dir.iterdir():
                print(f"  {item}")
        else:
            print("No Electron build artifacts found")

def main():
    """Main build process."""
    print("=== Westfall Personal Assistant Build Script ===")
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("electron").exists():
        print("ERROR: Must run from project root directory")
        sys.exit(1)
    
    build_backend()
    build_electron()
    
    print("=== Build Complete ===")
    print("Check the following directories for outputs:")
    print("  - Backend: dist-backend/westfall-backend.exe")
    print("  - Electron: electron/dist/")

if __name__ == "__main__":
    main()
