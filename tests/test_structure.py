#!/usr/bin/env python3
"""
Simple test to verify the backend structure is working.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_backend_structure():
    """Test that the backend structure can be imported."""
    try:
        # Test basic file structure
        backend_path = project_root / "backend" / "westfall_backend"
        assert backend_path.exists(), "Backend directory should exist"
        assert (backend_path / "__init__.py").exists(), "Backend __init__.py should exist"
        assert (backend_path / "app.py").exists(), "Backend app.py should exist"
        assert (backend_path / "routers").exists(), "Backend routers directory should exist"
        assert (backend_path / "services").exists(), "Backend services directory should exist"
        
        print("✓ Backend structure exists")
        return True
    except Exception as e:
        print(f"✗ Backend structure test failed: {e}")
        return False

def test_settings():
    """Test settings file exists."""
    try:
        settings_path = project_root / "backend" / "westfall_backend" / "services" / "settings.py"
        assert settings_path.exists(), "Settings file should exist"
        
        print("✓ Settings file exists")
        return True
    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        return False

def test_utils_structure():
    """Test that utils can be imported."""
    try:
        import utils
        from utils import logging_config
        print("✓ Utils structure imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Utils import failed: {e}")
        return False

def test_tests_structure():
    """Test that tests can be imported."""
    try:
        import tests
        from tests.unit import test_utils
        print("✓ Tests structure imports successfully") 
        return True
    except ImportError as e:
        print(f"✗ Tests import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running structure tests...\n")
    
    tests = [
        test_backend_structure,
        test_settings,
        test_utils_structure,
        test_tests_structure,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All structure tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())