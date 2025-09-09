#!/usr/bin/env python3
"""
Westfall Personal Assistant Backend Server

This server handles local model inference and provides APIs for the Electron frontend.
Supports multiple model formats and GPU acceleration.

This is now a wrapper around the new westfall_backend package structure.
The original 2450-line implementation has been moved to archive/server_original.py
"""

import sys
from pathlib import Path

def main():
    """Main entry point that delegates to the new backend structure."""
    
    # Add the backend directory to path
    backend_path = Path(__file__).parent
    sys.path.insert(0, str(backend_path))
    
    print("Westfall Personal Assistant Backend Server")
    print("Starting with new modular backend structure...")
    
    # Delegate to the new backend implementation
    try:
        from simple_server import main as simple_main
        simple_main()
    except Exception as e:
        print(f"Failed to start backend: {e}")
        print("\nTroubleshooting:")
        print("1. Install FastAPI dependencies: pip install fastapi uvicorn psutil")
        print("2. Check Python version (requires 3.8+)")
        print("3. Verify working directory is correct")
        print(f"4. Backend path: {backend_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()