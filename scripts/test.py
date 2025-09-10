#!/usr/bin/env python3
"""
Test script for Westfall Personal Assistant
Tests the backend functionality
"""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_backend_health():
    """Test if the backend health endpoint works."""
    try:
        response = requests.get("http://127.0.0.1:8756/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend health check passed")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_web_interface():
    """Test if the web interface loads."""
    try:
        response = requests.get("http://127.0.0.1:8756/", timeout=5)
        if response.status_code == 200 and "Westfall Personal Assistant" in response.text:
            print("✓ Web interface loads correctly")
            return True
        else:
            print(f"✗ Web interface failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Web interface test failed: {e}")
        return False

def test_settings_page():
    """Test if the settings page loads."""
    try:
        response = requests.get("http://127.0.0.1:8756/settings", timeout=5)
        if response.status_code == 200:
            print("✓ Settings page loads correctly")
            return True
        else:
            print(f"✗ Settings page failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Settings page test failed: {e}")
        return False

def start_backend():
    """Start the backend for testing."""
    backend_path = Path("dist-backend/westfall-backend.exe")
    if not backend_path.exists():
        print(f"✗ Backend binary not found at {backend_path}")
        return None
    
    print("Starting backend for testing...")
    try:
        proc = subprocess.Popen([str(backend_path)], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        # Give it time to start
        time.sleep(3)
        return proc
    except Exception as e:
        print(f"✗ Failed to start backend: {e}")
        return None

def main():
    """Run all tests."""
    print("=== Westfall Personal Assistant Test Suite ===")
    
    # Start backend
    backend_proc = start_backend()
    if not backend_proc:
        sys.exit(1)
    
    try:
        # Run tests
        tests = [
            test_backend_health,
            test_web_interface,
            test_settings_page,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Small delay between tests
        
        print(f"\n=== Test Results ===")
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed")
            return 1
    
    finally:
        # Clean up
        if backend_proc:
            backend_proc.terminate()
            backend_proc.wait()
            print("Backend stopped")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
