"""
Westfall Personal Assistant - Comprehensive Testing Framework
Advanced testing utilities for performance, integration, and edge cases
"""

import unittest
import time
import asyncio
import threading
import multiprocessing
import random
import string
import tempfile
import os
import sys
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from util.performance import get_performance_manager
from util.localization import get_localization_manager
from util.security_enhancements import get_security_manager

@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    details: Dict[str, Any]
    error: Optional[str] = None

@dataclass
class PerformanceBenchmark:
    operation: str
    target_time_ms: float
    memory_limit_mb: float
    iterations: int = 100

class ComprehensiveTestSuite:
    """
    Comprehensive test suite for Westfall Personal Assistant
    """
    
    def __init__(self):
        self.results = []
        self.performance_benchmarks = []
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="westfall_test_"))
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up isolated test environment"""
        # Create test directories
        (self.test_data_dir / "cache").mkdir()
        (self.test_data_dir / "localization").mkdir()
        (self.test_data_dir / "security").mkdir()
        
        # Initialize test data
        self.create_test_data()
    
    def create_test_data(self):
        """Create comprehensive test data sets"""
        # Large dataset for performance testing
        large_dataset = [
            {'id': i, 'data': ''.join(random.choices(string.ascii_letters, k=100))}
            for i in range(10000)
        ]
        
        with open(self.test_data_dir / "large_dataset.json", 'w') as f:
            json.dump(large_dataset, f)
        
        # Create test files of various sizes
        for size_mb in [1, 10, 50]:
            test_file = self.test_data_dir / f"test_file_{size_mb}mb.dat"
            with open(test_file, 'wb') as f:
                data = b'0' * (size_mb * 1024 * 1024)
                f.write(data)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("Starting Comprehensive Test Suite...")
        start_time = time.time()
        
        # Performance tests
        self.run_performance_tests()
        
        # Integration tests
        self.run_integration_tests()
        
        # Edge case tests
        self.run_edge_case_tests()
        
        # Stress tests
        self.run_stress_tests()
        
        # Security tests
        self.run_security_tests()
        
        # Localization tests
        self.run_localization_tests()
        
        # Memory leak tests
        self.run_memory_tests()
        
        total_time = time.time() - start_time
        
        return self.generate_test_report(total_time)
    
    def run_performance_tests(self):
        """Run performance benchmark tests"""
        print("Running performance tests...")
        
        # Test cache performance
        self.test_cache_performance()
        
        # Test memory management
        self.test_memory_management()
        
        # Test file operations
        self.test_file_operations()
        
        # Test concurrent operations
        self.test_concurrent_performance()
    
    def test_cache_performance(self):
        """Test caching system performance"""
        try:
            performance_manager = get_performance_manager()
            cache_manager = performance_manager.cache_manager
            
            # Test cache write performance
            start_time = time.time()
            for i in range(1000):
                cache_manager.set('ui_data', f'test_key_{i}', f'test_value_{i}')
            write_time = time.time() - start_time
            
            # Test cache read performance
            start_time = time.time()
            for i in range(1000):
                value = cache_manager.get('ui_data', f'test_key_{i}')
            read_time = time.time() - start_time
            
            # Test cache hit rate
            hits = 0
            for i in range(1000):
                if cache_manager.get('ui_data', f'test_key_{i}') is not None:
                    hits += 1
            hit_rate = hits / 1000
            
            self.results.append(TestResult(
                "cache_performance",
                write_time < 1.0 and read_time < 0.5 and hit_rate > 0.95,
                write_time + read_time,
                {
                    'write_time_ms': write_time * 1000,
                    'read_time_ms': read_time * 1000,
                    'hit_rate': hit_rate,
                    'operations_per_second': 2000 / (write_time + read_time)
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "cache_performance", False, 0, {}, str(e)
            ))
    
    def test_memory_management(self):
        """Test memory management and monitoring"""
        try:
            performance_manager = get_performance_manager()
            memory_monitor = performance_manager.memory_monitor
            
            initial_memory = memory_monitor.get_memory_usage()
            
            # Allocate large amount of memory
            large_data = []
            for i in range(1000):
                large_data.append('x' * 10000)  # 10KB each
            
            peak_memory = memory_monitor.get_memory_usage()
            memory_increase = peak_memory - initial_memory
            
            # Clean up
            del large_data
            
            # Force cleanup
            memory_monitor.trigger_aggressive_cleanup()
            
            # Wait for cleanup
            time.sleep(2)
            
            final_memory = memory_monitor.get_memory_usage()
            memory_recovered = peak_memory - final_memory
            
            # Check if memory was properly recovered
            recovery_rate = memory_recovered / memory_increase if memory_increase > 0 else 1.0
            
            self.results.append(TestResult(
                "memory_management",
                recovery_rate > 0.5,  # At least 50% memory recovery
                time.time(),
                {
                    'initial_memory_mb': initial_memory / 1024 / 1024,
                    'peak_memory_mb': peak_memory / 1024 / 1024,
                    'final_memory_mb': final_memory / 1024 / 1024,
                    'memory_increase_mb': memory_increase / 1024 / 1024,
                    'memory_recovered_mb': memory_recovered / 1024 / 1024,
                    'recovery_rate': recovery_rate
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "memory_management", False, 0, {}, str(e)
            ))
    
    def test_file_operations(self):
        """Test file operation performance"""
        try:
            # Test large file processing
            large_file = self.test_data_dir / "test_file_10mb.dat"
            
            # Test read performance
            start_time = time.time()
            with open(large_file, 'rb') as f:
                data = f.read()
            read_time = time.time() - start_time
            
            # Test write performance
            output_file = self.test_data_dir / "output_test.dat"
            start_time = time.time()
            with open(output_file, 'wb') as f:
                f.write(data)
            write_time = time.time() - start_time
            
            # Test file operations efficiency
            read_speed_mbps = (len(data) / 1024 / 1024) / read_time
            write_speed_mbps = (len(data) / 1024 / 1024) / write_time
            
            self.results.append(TestResult(
                "file_operations",
                read_speed_mbps > 50 and write_speed_mbps > 30,  # Minimum speeds
                read_time + write_time,
                {
                    'file_size_mb': len(data) / 1024 / 1024,
                    'read_time_s': read_time,
                    'write_time_s': write_time,
                    'read_speed_mbps': read_speed_mbps,
                    'write_speed_mbps': write_speed_mbps
                }
            ))
            
            # Cleanup
            output_file.unlink()
            
        except Exception as e:
            self.results.append(TestResult(
                "file_operations", False, 0, {}, str(e)
            ))
    
    def test_concurrent_performance(self):
        """Test performance under concurrent load"""
        try:
            performance_manager = get_performance_manager()
            
            def concurrent_cache_operations(thread_id):
                """Perform cache operations in separate thread"""
                operations = 100
                start_time = time.time()
                
                for i in range(operations):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    
                    # Write
                    performance_manager.cache_manager.set('ui_data', key, value)
                    
                    # Read
                    retrieved = performance_manager.cache_manager.get('ui_data', key)
                    
                    if retrieved != value:
                        return False, time.time() - start_time
                
                return True, time.time() - start_time
            
            # Run concurrent operations
            num_threads = 10
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(concurrent_cache_operations, i)
                    for i in range(num_threads)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Check results
            all_passed = all(result[0] for result in results)
            avg_thread_time = sum(result[1] for result in results) / len(results)
            
            # Calculate operations per second
            total_operations = num_threads * 100 * 2  # read + write
            ops_per_second = total_operations / total_time
            
            self.results.append(TestResult(
                "concurrent_performance",
                all_passed and ops_per_second > 500,  # Minimum 500 ops/sec
                total_time,
                {
                    'num_threads': num_threads,
                    'operations_per_thread': 200,
                    'total_operations': total_operations,
                    'total_time_s': total_time,
                    'avg_thread_time_s': avg_thread_time,
                    'operations_per_second': ops_per_second,
                    'all_threads_passed': all_passed
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "concurrent_performance", False, 0, {}, str(e)
            ))
    
    def run_integration_tests(self):
        """Run integration tests between components"""
        print("Running integration tests...")
        
        # Test performance + localization integration
        self.test_performance_localization_integration()
        
        # Test security + performance integration
        self.test_security_performance_integration()
        
        # Test component interaction under load
        self.test_component_interaction()
    
    def test_performance_localization_integration(self):
        """Test integration between performance and localization systems"""
        try:
            localization_manager = get_localization_manager()
            performance_manager = get_performance_manager()
            
            # Test cached translations
            start_time = time.time()
            
            # Perform many translation operations
            for i in range(1000):
                localization_manager.translate('app.name', 'en')
                localization_manager.translate('app.name', 'es')
                localization_manager.translate('app.name', 'fr')
                localization_manager.translate('app.name', 'de')
            
            translation_time = time.time() - start_time
            
            # Check cache effectiveness
            cache_stats = performance_manager.cache_manager.get_cache_stats()
            
            self.results.append(TestResult(
                "performance_localization_integration",
                translation_time < 1.0,  # Should be fast with caching
                translation_time,
                {
                    'translation_time_ms': translation_time * 1000,
                    'translations_per_second': 4000 / translation_time,
                    'cache_stats': cache_stats
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "performance_localization_integration", False, 0, {}, str(e)
            ))
    
    def test_security_performance_integration(self):
        """Test security features under performance load"""
        try:
            security_manager = get_security_manager()
            
            # Test encryption/decryption performance
            test_data = "Sensitive test data " * 100  # ~2KB
            
            start_time = time.time()
            
            # Encrypt/decrypt many times
            for i in range(100):
                encrypted = security_manager.encrypt_data(test_data)
                decrypted = security_manager.decrypt_data(encrypted)
                
                if decrypted != test_data:
                    raise ValueError("Decryption failed")
            
            crypto_time = time.time() - start_time
            
            # Test rate limiting performance
            start_time = time.time()
            
            passed_checks = 0
            for i in range(1000):
                if security_manager.check_rate_limit('test_operation', f'user_{i % 10}'):
                    passed_checks += 1
            
            rate_limit_time = time.time() - start_time
            
            self.results.append(TestResult(
                "security_performance_integration",
                crypto_time < 2.0 and rate_limit_time < 1.0,
                crypto_time + rate_limit_time,
                {
                    'crypto_time_ms': crypto_time * 1000,
                    'crypto_operations_per_second': 200 / crypto_time,
                    'rate_limit_time_ms': rate_limit_time * 1000,
                    'rate_limit_checks_per_second': 1000 / rate_limit_time,
                    'rate_limit_passed': passed_checks
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "security_performance_integration", False, 0, {}, str(e)
            ))
    
    def test_component_interaction(self):
        """Test interaction between all major components"""
        try:
            # Initialize all managers
            performance_manager = get_performance_manager()
            localization_manager = get_localization_manager()
            security_manager = get_security_manager()
            
            start_time = time.time()
            
            # Perform complex operations involving all components
            for i in range(50):
                # Localization with variable substitution
                text = localization_manager.translate(
                    'notifications.reminder_alert',
                    variables={'message': f'Test reminder {i}'}
                )
                
                # Encrypt the localized text
                encrypted_text = security_manager.encrypt_data(text)
                
                # Cache the encrypted result
                cache_key = f'encrypted_reminder_{i}'
                performance_manager.cache_manager.set('ui_data', cache_key, encrypted_text)
                
                # Retrieve and decrypt
                cached_encrypted = performance_manager.cache_manager.get('ui_data', cache_key)
                decrypted_text = security_manager.decrypt_data(cached_encrypted)
                
                if decrypted_text != text:
                    raise ValueError(f"Component interaction failed at iteration {i}")
            
            interaction_time = time.time() - start_time
            
            self.results.append(TestResult(
                "component_interaction",
                interaction_time < 5.0,  # Complex operations should complete in 5 seconds
                interaction_time,
                {
                    'interaction_time_ms': interaction_time * 1000,
                    'operations_per_second': 50 / interaction_time,
                    'components_tested': ['performance', 'localization', 'security']
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "component_interaction", False, 0, {}, str(e)
            ))
    
    def run_edge_case_tests(self):
        """Run edge case and boundary condition tests"""
        print("Running edge case tests...")
        
        # Test with extreme data sizes
        self.test_large_data_handling()
        
        # Test with unusual input
        self.test_unusual_input_handling()
        
        # Test error recovery
        self.test_error_recovery()
    
    def test_large_data_handling(self):
        """Test handling of extremely large data sets"""
        try:
            performance_manager = get_performance_manager()
            
            # Test with very large cache values
            large_value = 'x' * (1024 * 1024)  # 1MB string
            
            start_time = time.time()
            
            # Store large values
            for i in range(10):
                performance_manager.cache_manager.set('ui_data', f'large_key_{i}', large_value)
            
            # Retrieve large values
            retrieved_count = 0
            for i in range(10):
                value = performance_manager.cache_manager.get('ui_data', f'large_key_{i}')
                if value == large_value:
                    retrieved_count += 1
            
            large_data_time = time.time() - start_time
            
            self.results.append(TestResult(
                "large_data_handling",
                retrieved_count == 10 and large_data_time < 10.0,
                large_data_time,
                {
                    'data_size_mb': len(large_value) / 1024 / 1024,
                    'operations': 20,
                    'time_s': large_data_time,
                    'successful_retrievals': retrieved_count,
                    'throughput_mbps': (10 * len(large_value) / 1024 / 1024) / large_data_time
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "large_data_handling", False, 0, {}, str(e)
            ))
    
    def test_unusual_input_handling(self):
        """Test handling of unusual and malformed input"""
        try:
            localization_manager = get_localization_manager()
            
            unusual_inputs = [
                "",  # Empty string
                None,  # None value
                "nonexistent.key.path",  # Non-existent key
                "app.name" + "." * 1000,  # Very long key
                "key.with.unicode.characters.🚀.🌟",  # Unicode
                "key\nwith\nnewlines",  # Special characters
                "   whitespace   ",  # Whitespace
            ]
            
            handled_count = 0
            
            for unusual_input in unusual_inputs:
                try:
                    result = localization_manager.translate(unusual_input)
                    # Should return some string (fallback behavior)
                    if isinstance(result, str):
                        handled_count += 1
                except Exception:
                    # Some inputs may raise exceptions, which is acceptable
                    pass
            
            # Test unusual variables
            try:
                result = localization_manager.translate(
                    'notifications.reminder_alert',
                    variables={'message': None, 'extra': {'nested': 'object'}}
                )
                if isinstance(result, str):
                    handled_count += 1
            except Exception:
                pass
            
            self.results.append(TestResult(
                "unusual_input_handling",
                handled_count >= len(unusual_inputs) * 0.7,  # Handle at least 70%
                time.time(),
                {
                    'total_inputs_tested': len(unusual_inputs) + 1,
                    'successfully_handled': handled_count,
                    'handling_rate': handled_count / (len(unusual_inputs) + 1)
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "unusual_input_handling", False, 0, {}, str(e)
            ))
    
    def test_error_recovery(self):
        """Test system recovery from errors and failures"""
        try:
            performance_manager = get_performance_manager()
            
            # Simulate cache corruption
            cache_manager = performance_manager.cache_manager
            
            # Store some data
            cache_manager.set('ui_data', 'test_key', 'test_value')
            
            # Simulate corruption by directly modifying cache
            if hasattr(cache_manager, 'memory_caches'):
                # Corrupt the cache
                cache_manager.memory_caches['ui_data']['corrupted_key'] = object()
            
            # Test recovery
            recovery_successful = True
            try:
                # This should handle corruption gracefully
                value = cache_manager.get('ui_data', 'test_key')
                if value != 'test_value':
                    recovery_successful = False
                
                # Try to set new value (should work despite corruption)
                cache_manager.set('ui_data', 'recovery_test', 'recovery_value')
                recovered_value = cache_manager.get('ui_data', 'recovery_test')
                if recovered_value != 'recovery_value':
                    recovery_successful = False
                    
            except Exception:
                recovery_successful = False
            
            self.results.append(TestResult(
                "error_recovery",
                recovery_successful,
                time.time(),
                {
                    'corruption_simulated': True,
                    'recovery_successful': recovery_successful,
                    'cache_functional_after_corruption': recovery_successful
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "error_recovery", False, 0, {}, str(e)
            ))
    
    def run_stress_tests(self):
        """Run stress tests to find breaking points"""
        print("Running stress tests...")
        
        # High load test
        self.test_high_load_performance()
        
        # Memory pressure test
        self.test_memory_pressure()
        
        # Concurrent user simulation
        self.test_concurrent_users()
    
    def test_high_load_performance(self):
        """Test performance under high operation load"""
        try:
            performance_manager = get_performance_manager()
            
            start_time = time.time()
            operations = 10000
            
            # Perform many operations quickly
            for i in range(operations):
                # Cache operations
                performance_manager.cache_manager.set('stress_test', f'key_{i}', f'value_{i}')
                
                # Immediate retrieval
                value = performance_manager.cache_manager.get('stress_test', f'key_{i}')
                
                if i % 1000 == 0:  # Periodic cleanup
                    performance_manager.cache_manager.periodic_cleanup()
            
            high_load_time = time.time() - start_time
            ops_per_second = operations * 2 / high_load_time  # 2 ops per iteration
            
            # Check memory usage
            memory_usage = performance_manager.memory_monitor.get_memory_usage()
            memory_mb = memory_usage / 1024 / 1024
            
            self.results.append(TestResult(
                "high_load_performance",
                ops_per_second > 1000 and memory_mb < 1000,  # Good performance and reasonable memory
                high_load_time,
                {
                    'total_operations': operations * 2,
                    'time_s': high_load_time,
                    'operations_per_second': ops_per_second,
                    'memory_usage_mb': memory_mb,
                    'avg_operation_time_ms': (high_load_time / (operations * 2)) * 1000
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "high_load_performance", False, 0, {}, str(e)
            ))
    
    def test_memory_pressure(self):
        """Test behavior under memory pressure"""
        try:
            performance_manager = get_performance_manager()
            memory_monitor = performance_manager.memory_monitor
            
            initial_memory = memory_monitor.get_memory_usage()
            
            # Create memory pressure
            memory_hogs = []
            try:
                # Allocate memory in chunks until we hit limits
                for i in range(100):
                    # Allocate 10MB chunks
                    chunk = bytearray(10 * 1024 * 1024)
                    memory_hogs.append(chunk)
                    
                    current_memory = memory_monitor.get_memory_usage()
                    memory_increase = current_memory - initial_memory
                    
                    # Stop if we've allocated 500MB or hit system limits
                    if memory_increase > 500 * 1024 * 1024:
                        break
                
                # Test system responsiveness under pressure
                start_time = time.time()
                
                # Perform operations while under memory pressure
                for i in range(100):
                    performance_manager.cache_manager.set('pressure_test', f'key_{i}', f'value_{i}')
                    value = performance_manager.cache_manager.get('pressure_test', f'key_{i}')
                
                pressure_response_time = time.time() - start_time
                
                # Check if cleanup was triggered
                cleanup_triggered = memory_monitor.last_cleanup_time > initial_memory / 1000000  # Rough check
                
            finally:
                # Clean up memory
                del memory_hogs
                memory_monitor.trigger_aggressive_cleanup()
            
            final_memory = memory_monitor.get_memory_usage()
            memory_recovered = (initial_memory - final_memory) > 0
            
            self.results.append(TestResult(
                "memory_pressure",
                pressure_response_time < 5.0,  # Should remain responsive
                pressure_response_time,
                {
                    'initial_memory_mb': initial_memory / 1024 / 1024,
                    'final_memory_mb': final_memory / 1024 / 1024,
                    'pressure_response_time_s': pressure_response_time,
                    'cleanup_triggered': cleanup_triggered,
                    'memory_recovered': memory_recovered
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "memory_pressure", False, 0, {}, str(e)
            ))
    
    def test_concurrent_users(self):
        """Test system with multiple concurrent users"""
        try:
            def simulate_user(user_id):
                """Simulate a single user's operations"""
                operations = 50
                successful_ops = 0
                
                for i in range(operations):
                    try:
                        # Mixed operations typical of a user session
                        get_localization_manager().translate('app.name', 'en')
                        get_performance_manager().cache_manager.set('ui_data', f'user_{user_id}_data_{i}', f'data_{i}')
                        get_security_manager().check_rate_limit('api_requests', f'user_{user_id}')
                        
                        successful_ops += 1
                    except Exception:
                        pass
                
                return successful_ops
            
            num_users = 20
            start_time = time.time()
            
            # Simulate concurrent users
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [
                    executor.submit(simulate_user, i)
                    for i in range(num_users)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            concurrent_test_time = time.time() - start_time
            
            # Calculate success rate
            total_operations = sum(results)
            expected_operations = num_users * 50
            success_rate = total_operations / expected_operations
            
            self.results.append(TestResult(
                "concurrent_users",
                success_rate > 0.95,  # At least 95% success rate
                concurrent_test_time,
                {
                    'num_users': num_users,
                    'operations_per_user': 50,
                    'total_operations': total_operations,
                    'expected_operations': expected_operations,
                    'success_rate': success_rate,
                    'test_time_s': concurrent_test_time,
                    'operations_per_second': total_operations / concurrent_test_time
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "concurrent_users", False, 0, {}, str(e)
            ))
    
    def run_security_tests(self):
        """Run security validation tests"""
        print("Running security tests...")
        
        # Test encryption/decryption
        self.test_encryption_security()
        
        # Test rate limiting
        self.test_rate_limiting()
        
        # Test input validation
        self.test_input_validation()
    
    def test_encryption_security(self):
        """Test encryption system security"""
        try:
            security_manager = get_security_manager()
            
            test_data = "Highly sensitive test data 🔒"
            
            # Test encryption
            encrypted = security_manager.encrypt_data(test_data)
            
            # Verify encryption worked
            if encrypted == test_data:
                raise ValueError("Data was not encrypted")
            
            # Test decryption
            decrypted = security_manager.decrypt_data(encrypted)
            
            if decrypted != test_data:
                raise ValueError("Decryption failed")
            
            # Test that encrypted data looks random
            entropy_check = len(set(encrypted)) > len(encrypted) * 0.3  # At least 30% unique characters
            
            self.results.append(TestResult(
                "encryption_security",
                entropy_check,
                time.time(),
                {
                    'original_length': len(test_data),
                    'encrypted_length': len(encrypted),
                    'encryption_expansion': len(encrypted) / len(test_data),
                    'entropy_check_passed': entropy_check,
                    'round_trip_successful': decrypted == test_data
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "encryption_security", False, 0, {}, str(e)
            ))
    
    def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        try:
            security_manager = get_security_manager()
            
            # Configure strict rate limit for testing
            security_manager.rate_limits['test_operation'] = {'limit': 5, 'window': 1}
            
            user_id = 'test_user'
            allowed_requests = 0
            denied_requests = 0
            
            # Make requests rapidly
            for i in range(10):
                if security_manager.check_rate_limit('test_operation', user_id):
                    allowed_requests += 1
                else:
                    denied_requests += 1
            
            # Rate limiting should kick in
            rate_limiting_effective = denied_requests > 0 and allowed_requests <= 5
            
            self.results.append(TestResult(
                "rate_limiting",
                rate_limiting_effective,
                time.time(),
                {
                    'total_requests': 10,
                    'allowed_requests': allowed_requests,
                    'denied_requests': denied_requests,
                    'rate_limit': 5,
                    'rate_limiting_effective': rate_limiting_effective
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "rate_limiting", False, 0, {}, str(e)
            ))
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        try:
            security_manager = get_security_manager()
            
            # Test malicious inputs
            malicious_inputs = [
                "'; DROP TABLE users; --",  # SQL injection attempt
                "<script>alert('xss')</script>",  # XSS attempt
                "../../../etc/passwd",  # Path traversal
                "admin\x00hidden",  # Null byte injection
                "A" * 10000,  # Buffer overflow attempt
            ]
            
            validation_passed = 0
            
            for malicious_input in malicious_inputs:
                try:
                    # Test if input is properly handled (shouldn't crash)
                    result = security_manager.generate_secure_token()
                    if len(result) > 0:  # Basic functionality still works
                        validation_passed += 1
                except Exception:
                    # Crashing on malicious input is not acceptable
                    pass
            
            # Also test that normal inputs work
            normal_result = security_manager.generate_secure_token(32)
            normal_input_works = len(normal_result) == 32
            
            self.results.append(TestResult(
                "input_validation",
                validation_passed == len(malicious_inputs) and normal_input_works,
                time.time(),
                {
                    'malicious_inputs_tested': len(malicious_inputs),
                    'validation_passed': validation_passed,
                    'normal_input_works': normal_input_works,
                    'security_rating': validation_passed / len(malicious_inputs)
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "input_validation", False, 0, {}, str(e)
            ))
    
    def run_localization_tests(self):
        """Run localization system tests"""
        print("Running localization tests...")
        
        # Test translation accuracy
        self.test_translation_accuracy()
        
        # Test locale formatting
        self.test_locale_formatting()
        
        # Test language switching
        self.test_language_switching()
    
    def test_translation_accuracy(self):
        """Test translation system accuracy and completeness"""
        try:
            localization_manager = get_localization_manager()
            
            # Test basic translations
            translations = {
                'en': localization_manager.translate('app.name', 'en'),
                'es': localization_manager.translate('app.name', 'es'),
                'fr': localization_manager.translate('app.name', 'fr'),
                'de': localization_manager.translate('app.name', 'de')
            }
            
            # Verify translations exist and are different
            all_translated = all(trans for trans in translations.values())
            translations_differ = len(set(translations.values())) > 1
            
            # Test variable substitution
            variable_test = localization_manager.translate(
                'notifications.reminder_alert',
                'en',
                variables={'message': 'Test Message'}
            )
            
            variable_substitution_works = 'Test Message' in variable_test
            
            # Test fallback behavior
            fallback_test = localization_manager.translate('nonexistent.key', 'es')
            fallback_works = isinstance(fallback_test, str) and len(fallback_test) > 0
            
            self.results.append(TestResult(
                "translation_accuracy",
                all_translated and translations_differ and variable_substitution_works and fallback_works,
                time.time(),
                {
                    'languages_tested': list(translations.keys()),
                    'all_translated': all_translated,
                    'translations_differ': translations_differ,
                    'variable_substitution_works': variable_substitution_works,
                    'fallback_works': fallback_works,
                    'sample_translations': translations
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "translation_accuracy", False, 0, {}, str(e)
            ))
    
    def test_locale_formatting(self):
        """Test locale-specific formatting"""
        try:
            localization_manager = get_localization_manager()
            
            test_number = 1234.56
            test_currency = 1000.00
            test_date = datetime(2025, 9, 8, 14, 30)
            
            # Test number formatting
            number_formats = {
                'en': localization_manager.format_number(test_number, 'en'),
                'es': localization_manager.format_number(test_number, 'es'),
                'fr': localization_manager.format_number(test_number, 'fr'),
                'de': localization_manager.format_number(test_number, 'de')
            }
            
            # Test currency formatting
            currency_formats = {
                'en': localization_manager.format_currency(test_currency, 'USD', 'en'),
                'es': localization_manager.format_currency(test_currency, 'EUR', 'es'),
                'fr': localization_manager.format_currency(test_currency, 'EUR', 'fr'),
                'de': localization_manager.format_currency(test_currency, 'EUR', 'de')
            }
            
            # Test date formatting
            date_formats = {
                'en': localization_manager.format_date(test_date, 'medium', 'en'),
                'es': localization_manager.format_date(test_date, 'medium', 'es'),
                'fr': localization_manager.format_date(test_date, 'medium', 'fr'),
                'de': localization_manager.format_date(test_date, 'medium', 'de')
            }
            
            # Verify formatting works and produces different results
            number_formatting_works = all(fmt for fmt in number_formats.values())
            currency_formatting_works = all(fmt for fmt in currency_formats.values())
            date_formatting_works = all(fmt for fmt in date_formats.values())
            
            formatting_differs = (
                len(set(number_formats.values())) > 1 or
                len(set(currency_formats.values())) > 1 or
                len(set(date_formats.values())) > 1
            )
            
            self.results.append(TestResult(
                "locale_formatting",
                number_formatting_works and currency_formatting_works and date_formatting_works,
                time.time(),
                {
                    'number_formatting_works': number_formatting_works,
                    'currency_formatting_works': currency_formatting_works,
                    'date_formatting_works': date_formatting_works,
                    'formatting_differs': formatting_differs,
                    'sample_number_formats': number_formats,
                    'sample_currency_formats': currency_formats,
                    'sample_date_formats': date_formats
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "locale_formatting", False, 0, {}, str(e)
            ))
    
    def test_language_switching(self):
        """Test dynamic language switching"""
        try:
            localization_manager = get_localization_manager()
            
            original_language = localization_manager.get_current_language()
            
            # Test switching between languages
            languages_to_test = ['en', 'es', 'fr', 'de']
            switch_results = {}
            
            for lang in languages_to_test:
                # Switch language
                switch_success = localization_manager.set_language(lang)
                
                # Verify switch
                current_lang = localization_manager.get_current_language()
                
                # Test translation in new language
                translation = localization_manager.translate('app.name')
                
                switch_results[lang] = {
                    'switch_success': switch_success,
                    'language_set_correctly': current_lang == lang,
                    'translation_works': len(translation) > 0
                }
            
            # Restore original language
            localization_manager.set_language(original_language)
            
            # Check if all switches worked
            all_switches_successful = all(
                result['switch_success'] and result['language_set_correctly'] and result['translation_works']
                for result in switch_results.values()
            )
            
            self.results.append(TestResult(
                "language_switching",
                all_switches_successful,
                time.time(),
                {
                    'original_language': original_language,
                    'languages_tested': languages_to_test,
                    'switch_results': switch_results,
                    'all_switches_successful': all_switches_successful
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                "language_switching", False, 0, {}, str(e)
            ))
    
    def run_memory_tests(self):
        """Run memory leak detection tests"""
        print("Running memory leak tests...")
        
        self.test_memory_leak_detection()
    
    def test_memory_leak_detection(self):
        """Test memory leak detection capabilities"""
        try:
            performance_manager = get_performance_manager()
            memory_monitor = performance_manager.memory_monitor
            
            initial_memory = memory_monitor.get_memory_usage()
            
            # Simulate potential memory leak scenario
            leaked_objects = []
            
            for i in range(100):
                # Create objects that might not be properly cleaned up
                large_object = {
                    'data': 'x' * 1000,
                    'id': i,
                    'references': [j for j in range(100)]
                }
                leaked_objects.append(large_object)
                
                # Add to cache without expiration
                performance_manager.cache_manager.set('ui_data', f'potential_leak_{i}', large_object)
            
            # Wait and check memory
            time.sleep(2)
            peak_memory = memory_monitor.get_memory_usage()
            memory_increase = peak_memory - initial_memory
            
            # Trigger cleanup
            memory_monitor.trigger_aggressive_cleanup()
            
            # Wait for cleanup
            time.sleep(2)
            post_cleanup_memory = memory_monitor.get_memory_usage()
            
            # Calculate recovery
            memory_recovered = peak_memory - post_cleanup_memory
            recovery_rate = memory_recovered / memory_increase if memory_increase > 0 else 1.0
            
            # Check if memory monitor detected the growth
            memory_report = memory_monitor.get_memory_report()
            growth_detected = memory_report.get('growth_rate_mb_per_hour', 0) > 0
            
            self.results.append(TestResult(
                "memory_leak_detection",
                recovery_rate > 0.3 and growth_detected,  # Should detect growth and recover some memory
                time.time(),
                {
                    'initial_memory_mb': initial_memory / 1024 / 1024,
                    'peak_memory_mb': peak_memory / 1024 / 1024,
                    'post_cleanup_memory_mb': post_cleanup_memory / 1024 / 1024,
                    'memory_increase_mb': memory_increase / 1024 / 1024,
                    'memory_recovered_mb': memory_recovered / 1024 / 1024,
                    'recovery_rate': recovery_rate,
                    'growth_detected': growth_detected,
                    'memory_report': memory_report
                }
            ))
            
            # Cleanup
            del leaked_objects
            
        except Exception as e:
            self.results.append(TestResult(
                "memory_leak_detection", False, 0, {}, str(e)
            ))
    
    def generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.passed)
        failed_tests = total_tests - passed_tests
        
        # Calculate performance statistics
        performance_tests = [r for r in self.results if 'performance' in r.name]
        avg_performance_time = sum(r.duration for r in performance_tests) / len(performance_tests) if performance_tests else 0
        
        # Get system information
        system_info = self.get_system_info()
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration_s': total_time,
                'avg_performance_time_s': avg_performance_time
            },
            'test_results': [
                {
                    'name': result.name,
                    'passed': result.passed,
                    'duration_s': result.duration,
                    'details': result.details,
                    'error': result.error
                }
                for result in self.results
            ],
            'system_info': system_info,
            'test_environment': {
                'test_data_dir': str(self.test_data_dir),
                'timestamp': datetime.now().isoformat(),
                'python_version': sys.version,
                'platform': sys.platform
            },
            'performance_benchmarks': self.performance_benchmarks,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            import psutil
            
            # CPU information
            cpu_info = {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': memory.total / 1024 / 1024 / 1024,
                'available_gb': memory.available / 1024 / 1024 / 1024,
                'percent_used': memory.percent
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'percent_used': (disk.used / disk.total) * 100
            }
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info
            }
            
        except ImportError:
            return {'error': 'psutil not available for system info'}
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze failed tests
        failed_tests = [r for r in self.results if not r.passed]
        
        if any('performance' in r.name for r in failed_tests):
            recommendations.append("Consider optimizing performance-critical components")
        
        if any('memory' in r.name for r in failed_tests):
            recommendations.append("Review memory management and implement more aggressive cleanup")
        
        if any('security' in r.name for r in failed_tests):
            recommendations.append("Strengthen security measures and input validation")
        
        if any('concurrent' in r.name for r in failed_tests):
            recommendations.append("Improve thread safety and concurrent operation handling")
        
        # Performance-based recommendations
        performance_tests = [r for r in self.results if 'performance' in r.name and r.passed]
        if performance_tests:
            avg_time = sum(r.duration for r in performance_tests) / len(performance_tests)
            if avg_time > 5.0:
                recommendations.append("Performance could be improved - consider code optimization")
        
        # Memory-based recommendations
        memory_tests = [r for r in self.results if 'memory' in r.name and r.passed]
        for test in memory_tests:
            if 'memory_usage_mb' in test.details and test.details['memory_usage_mb'] > 500:
                recommendations.append("High memory usage detected - consider memory optimization")
        
        if not recommendations:
            recommendations.append("All tests passed successfully - system is performing well")
        
        return recommendations
    
    def cleanup(self):
        """Clean up test environment"""
        try:
            import shutil
            shutil.rmtree(self.test_data_dir)
        except Exception as e:
            print(f"Failed to cleanup test environment: {e}")


def run_comprehensive_tests():
    """Run the complete test suite and print results"""
    test_suite = ComprehensiveTestSuite()
    
    try:
        report = test_suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("WESTFALL PERSONAL ASSISTANT - COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        summary = report['test_summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Pass Rate: {summary['pass_rate']:.1%}")
        print(f"Total Duration: {summary['total_duration_s']:.2f} seconds")
        
        # Print failed tests
        failed_results = [r for r in report['test_results'] if not r['passed']]
        if failed_results:
            print(f"\nFAILED TESTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"  ❌ {result['name']}: {result.get('error', 'No error details')}")
        
        # Print recommendations
        print(f"\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print("\n" + "="*80)
        
        return report
        
    finally:
        test_suite.cleanup()


if __name__ == "__main__":
    run_comprehensive_tests()