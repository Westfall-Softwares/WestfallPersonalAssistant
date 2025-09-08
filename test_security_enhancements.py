#!/usr/bin/env python3
"""
Test script for comprehensive security and architecture enhancements.
"""

import sys
import tempfile
import os
from pathlib import Path

def test_model_security():
    """Test model security functionality."""
    print("Testing Model Security...")
    try:
        sys.path.append('backend/security')
        from model_security import ModelSecurityManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            security_manager = ModelSecurityManager(temp_dir)
            
            # Test checksum
            test_file = Path(temp_dir) / 'test.txt'
            test_file.write_text('test content')
            checksum = security_manager.calculate_file_checksum(test_file)
            
            # Test validation
            result = security_manager.validate_model_before_load(
                test_file, 
                source_url="https://huggingface.co/test",
                expected_checksum=checksum
            )
            
            assert result['valid'] == True
            assert result['checksum_valid'] == True
            print("✅ Model security tests passed")
            
    except Exception as e:
        print(f"❌ Model security tests failed: {e}")
        raise

def test_input_validation():
    """Test input validation functionality."""
    print("Testing Input Validation...")
    try:
        sys.path.append('backend/security')
        from input_validation import InputValidator, ValidationError
        
        validator = InputValidator()
        
        # Test email validation
        email = validator.validate_email("test@example.com")
        assert email == "test@example.com"
        
        # Test string sanitization (safe string)
        safe_string = validator.sanitize_string("This is a safe string")
        assert safe_string == "This is a safe string"
        
        # Test dangerous string detection
        try:
            validator.sanitize_string("<script>alert('test')</script>")
            assert False, "Should have detected dangerous content"
        except ValidationError:
            pass  # This is expected
        
        # Test integer validation
        num = validator.validate_integer("42", min_val=0, max_val=100)
        assert num == 42
        
        print("✅ Input validation tests passed")
        
    except Exception as e:
        print(f"❌ Input validation tests failed: {e}")
        raise

def test_state_management():
    """Test state management functionality."""
    print("Testing State Management...")
    try:
        from backend.state_management import StateManager
        
        state = StateManager()
        
        # Test basic operations
        state.set("app.version", "1.0.0")
        version = state.get("app.version")
        assert version == "1.0.0"
        
        # Test nested operations
        state.set("user.preferences.theme", "dark")
        theme = state.get("user.preferences.theme")
        assert theme == "dark"
        
        # Test undo/redo
        state.set("test.value", 1)
        state.set("test.value", 2)
        assert state.get("test.value") == 2
        
        state.undo()
        assert state.get("test.value") == 1
        
        state.redo()
        assert state.get("test.value") == 2
        
        print("✅ State management tests passed")
        
    except Exception as e:
        print(f"❌ State management tests failed: {e}")
        raise

def test_logging_system():
    """Test enhanced logging system."""
    print("Testing Logging System...")
    try:
        from backend.logging_system import initialize_logging, LogCategory
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_manager = initialize_logging(temp_dir, "TestApp")
            
            # Test basic logging
            logger = log_manager.get_logger("test", LogCategory.SYSTEM)
            logger.info("Test log message")
            
            # Test security logging
            log_manager.log_security_event("Test security event", "WARNING")
            
            # Test performance logging
            log_manager.log_performance_metric("test_metric", 42.5, "ms")
            
            # Test log viewing
            log_viewer = log_manager.get_log_viewer()
            recent_logs = log_viewer.get_recent_logs(limit=10)
            
            print("✅ Logging system tests passed")
            
    except Exception as e:
        print(f"❌ Logging system tests failed: {e}")
        raise

def main():
    """Run all tests."""
    print("🧪 Running Comprehensive Security & Architecture Tests\n")
    
    tests = [
        test_input_validation,
        test_state_management,
        test_logging_system,
        test_model_security,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"Test failed: {e}")
            failed += 1
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Security and architecture enhancements are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementations.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)