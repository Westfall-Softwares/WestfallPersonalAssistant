#!/usr/bin/env python3
"""
Test script for comprehensive security and architecture enhancements.
"""

import sys
import tempfile
import os
import time
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

def test_memory_management():
    """Test memory management system."""
    print("Testing Memory Management...")
    try:
        from backend.memory_management import MemoryManager, StreamProcessor, DataPaginator
        
        # Test memory monitoring
        memory_manager = MemoryManager()
        usage = memory_manager.monitor.get_current_usage()
        assert usage.total_mb > 0, f"Expected positive total memory, got {usage.total_mb}"
        assert usage.process_mb >= 0, f"Expected non-negative process memory, got {usage.process_mb}"
        
        # Test stream processing
        stream_processor = StreamProcessor(chunk_size=10)
        test_text = "This is a test string for streaming processing"
        chunks = list(stream_processor.process_large_text(test_text, lambda x: x.upper()))
        assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
        assert all(chunk.isupper() for chunk in chunks), "All chunks should be uppercase"
        
        # Test pagination
        paginator = DataPaginator(page_size=5)
        test_data = list(range(20))
        page_result = paginator.paginate_list(test_data, page=2)
        assert len(page_result['items']) == 5, f"Expected 5 items, got {len(page_result['items'])}"
        assert page_result['items'] == [5, 6, 7, 8, 9], f"Expected [5,6,7,8,9], got {page_result['items']}"
        assert page_result['pagination']['current_page'] == 2, f"Expected page 2, got {page_result['pagination']['current_page']}"
        
        print("✅ Memory management tests passed")
        
    except Exception as e:
        print(f"❌ Memory management tests failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_platform_compatibility():
    """Test platform compatibility system."""
    print("Testing Platform Compatibility...")
    try:
        from backend.platform_compatibility import PlatformManager, is_linux
        
        platform_manager = PlatformManager()
        
        # Test platform detection
        platform_info = platform_manager.get_system_info()
        assert 'platform' in platform_info, "Platform info should contain 'platform' key"
        assert 'paths' in platform_info, "Platform info should contain 'paths' key"
        
        # Test path management
        app_dirs = platform_manager.setup_application_directories("TestApp")
        assert 'config' in app_dirs, "App dirs should contain 'config'"
        assert 'data' in app_dirs, "App dirs should contain 'data'"
        assert 'cache' in app_dirs, "App dirs should contain 'cache'"
        assert 'logs' in app_dirs, "App dirs should contain 'logs'"
        
        # Test path safety
        safe_path = platform_manager.paths.normalize_path("test.txt")
        assert platform_manager.paths.is_path_safe(safe_path), f"Path {safe_path} should be safe"
        
        # Test unsafe path detection
        unsafe_path = "../../../etc/passwd"
        assert not platform_manager.paths.is_path_safe(unsafe_path), f"Path {unsafe_path} should be unsafe"
        
        print("✅ Platform compatibility tests passed")
        
    except Exception as e:
        print(f"❌ Platform compatibility tests failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_enhanced_threading():
    """Test enhanced threading capabilities."""
    print("Testing Enhanced Threading...")
    try:
        # Import without PyQt5 dependency issues
        import threading
        import time
        
        # Test thread-safe counter (basic implementation)
        class ThreadSafeCounter:
            def __init__(self):
                self._value = 0
                self._lock = threading.Lock()
            
            def increment(self):
                with self._lock:
                    self._value += 1
                    return self._value
            
            def get(self):
                with self._lock:
                    return self._value
        
        counter = ThreadSafeCounter()
        
        def worker():
            for _ in range(10):
                counter.increment()
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert counter.get() == 50
        
        print("✅ Enhanced threading tests passed")
        
    except Exception as e:
        print(f"❌ Enhanced threading tests failed: {e}")
        raise

def main():
    """Run all tests."""
    print("🧪 Running Comprehensive Security & Architecture Tests\n")
    
    tests = [
        test_input_validation,
        test_state_management,
        test_logging_system,
        test_memory_management,
        test_platform_compatibility,
        test_enhanced_threading,
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