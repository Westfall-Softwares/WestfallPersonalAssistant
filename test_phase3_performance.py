#!/usr/bin/env python3
"""
Test script for Phase 3 Performance Optimizations
Demonstrates caching, memory management, and database optimizations
"""

import sys
import os
import time
import tempfile
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from util.performance import (
    get_performance_manager, cached, lazy_property, optimize_startup
)
from util.database_performance import (
    get_db_performance_manager, ConnectionPool, QueryOptimizer
)


def test_caching_system():
    """Test the caching system"""
    print("=== Testing Caching System ===")
    
    performance_manager = get_performance_manager()
    cache_manager = performance_manager.cache_manager
    
    # Test different cache types
    print("\n1. Testing cache operations:")
    
    # Test API response cache
    cache_manager.set('api_responses', 'weather_data', {'temperature': 25, 'humidity': 60})
    cached_weather = cache_manager.get('api_responses', 'weather_data')
    print(f"   Cached weather data: {cached_weather}")
    
    # Test computed values cache
    cache_manager.set('computed_values', 'fibonacci_100', 354224848179261915075)
    cached_fib = cache_manager.get('computed_values', 'fibonacci_100')
    print(f"   Cached fibonacci: {cached_fib}")
    
    # Test cache with TTL
    cache_manager.set('ui_data', 'temp_setting', 'dark_mode', ttl=1)
    print(f"   Immediate read: {cache_manager.get('ui_data', 'temp_setting')}")
    
    time.sleep(1.1)  # Wait for TTL to expire
    expired_data = cache_manager.get('ui_data', 'temp_setting')
    print(f"   After TTL expiry: {expired_data}")
    
    # Test cache statistics
    print("\n2. Cache statistics:")
    stats = cache_manager.get_cache_stats()
    for cache_type, cache_stats in stats.items():
        if cache_type != 'total':
            print(f"   {cache_type}: {cache_stats['items']} items, {cache_stats['size_bytes']} bytes")
    
    print(f"   Total: {stats['total']['items']} items, {stats['total']['size_mb']:.2f} MB")
    
    print("✅ Caching system tests completed")


def test_memory_monitoring():
    """Test memory monitoring"""
    print("\n=== Testing Memory Monitoring ===")
    
    performance_manager = get_performance_manager()
    memory_monitor = performance_manager.memory_monitor
    
    # Get current memory usage
    memory_usage = memory_monitor.get_memory_usage()
    memory_mb = memory_usage / (1024 * 1024)
    
    print(f"\n1. Current memory usage: {memory_mb:.2f} MB")
    print(f"   Warning threshold: {memory_monitor.warning_threshold / (1024 * 1024):.2f} MB")
    print(f"   Critical threshold: {memory_monitor.critical_threshold / (1024 * 1024):.2f} MB")
    
    # Test gentle cleanup
    print("\n2. Testing cleanup mechanisms:")
    print("   Triggering gentle cleanup...")
    memory_monitor.trigger_gentle_cleanup()
    
    # Create some test data to use memory
    print("\n3. Creating test data to use memory...")
    test_data = []
    for i in range(1000):
        # Create some data structures
        test_data.append({
            'id': i,
            'data': f"Test data string {i}" * 100,
            'nested': {'value': i * 2, 'array': list(range(i % 50))}
        })
    
    # Cache the test data
    performance_manager.cache_manager.set('ui_data', 'test_bulk_data', test_data)
    
    new_memory = memory_monitor.get_memory_usage() / (1024 * 1024)
    print(f"   Memory after test data: {new_memory:.2f} MB (increase: {new_memory - memory_mb:.2f} MB)")
    
    # Test aggressive cleanup
    print("   Triggering aggressive cleanup...")
    memory_monitor.trigger_aggressive_cleanup()
    
    final_memory = memory_monitor.get_memory_usage() / (1024 * 1024)
    print(f"   Memory after cleanup: {final_memory:.2f} MB")
    
    print("✅ Memory monitoring tests completed")


def test_cached_decorator():
    """Test the cached decorator"""
    print("\n=== Testing Cached Decorator ===")
    
    @cached(cache_type='computed_values', ttl=30)
    def expensive_computation(n):
        """Simulate expensive computation"""
        print(f"   Computing fibonacci({n})...")
        time.sleep(0.1)  # Simulate work
        
        if n <= 1:
            return n
        return expensive_computation(n-1) + expensive_computation(n-2)
    
    print("\n1. First call (should compute):")
    start_time = time.time()
    result1 = expensive_computation(10)
    time1 = time.time() - start_time
    print(f"   Result: {result1}, Time: {time1:.3f}s")
    
    print("\n2. Second call (should use cache):")
    start_time = time.time()
    result2 = expensive_computation(10)
    time2 = time.time() - start_time
    print(f"   Result: {result2}, Time: {time2:.3f}s")
    
    print(f"\n3. Performance improvement: {time1/time2:.1f}x faster with cache")
    
    print("✅ Cached decorator tests completed")


def test_database_performance():
    """Test database performance optimizations"""
    print("\n=== Testing Database Performance ===")
    
    # Create temporary database
    db_path = tempfile.mktemp(suffix='.db')
    
    try:
        # Initialize database with test schema
        print("\n1. Setting up test database...")
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE test_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE test_posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES test_users(id)
                )
            """)
        
        # Test connection pool
        print("\n2. Testing connection pool...")
        db_manager = get_db_performance_manager(db_path)
        
        # Insert test data
        print("   Inserting test data...")
        for i in range(100):
            db_manager.execute_query(
                "INSERT INTO test_users (username, email) VALUES (?, ?)",
                (f"user{i}", f"user{i}@example.com")
            )
        
        # Test batch operations
        print("   Testing batch insert...")
        post_data = [
            (i % 100 + 1, f"Post {i}", f"Content for post {i}")
            for i in range(500)
        ]
        
        start_time = time.time()
        affected = db_manager.execute_many(
            "INSERT INTO test_posts (user_id, title, content) VALUES (?, ?, ?)",
            post_data
        )
        batch_time = time.time() - start_time
        
        print(f"   Batch insert: {affected} rows in {batch_time:.3f}s")
        
        # Test query performance
        print("\n3. Testing query performance...")
        
        # Query without index (should be slow)
        start_time = time.time()
        results = db_manager.execute_query(
            "SELECT * FROM test_posts WHERE title LIKE ?",
            ('%Post 1%',)
        )
        query_time = time.time() - start_time
        print(f"   Query without index: {len(results)} results in {query_time:.3f}s")
        
        # Create index and test again
        print("   Creating index...")
        db_manager.execute_query("CREATE INDEX idx_posts_title ON test_posts(title)")
        
        start_time = time.time()
        results = db_manager.execute_query(
            "SELECT * FROM test_posts WHERE title LIKE ?",
            ('%Post 1%',)
        )
        indexed_time = time.time() - start_time
        print(f"   Query with index: {len(results)} results in {indexed_time:.3f}s")
        
        if query_time > 0 and indexed_time > 0:
            improvement = query_time / indexed_time
            print(f"   Index improvement: {improvement:.1f}x faster")
        
        # Test transaction performance
        print("\n4. Testing transaction performance...")
        start_time = time.time()
        with db_manager.transaction() as conn:
            for i in range(50):
                conn.execute(
                    "UPDATE test_users SET email = ? WHERE id = ?",
                    (f"updated{i}@example.com", i + 1)
                )
        transaction_time = time.time() - start_time
        print(f"   Transaction: 50 updates in {transaction_time:.3f}s")
        
        # Get performance statistics
        print("\n5. Performance statistics:")
        stats = db_manager.get_performance_stats()
        
        pool_stats = stats['connection_pool']
        print(f"   Connection pool: {pool_stats['created_connections']} created, "
              f"{pool_stats['available_connections']} available")
        
        query_stats = stats['query_performance']
        if query_stats['total_queries'] > 0:
            print(f"   Queries: {query_stats['total_queries']} total, "
                  f"avg {query_stats['average_time']:.3f}s, "
                  f"{query_stats['slow_queries']} slow")
        
        print(f"   Database size: {stats['database_file_size']} bytes")
        
        # Test optimization
        print("\n6. Testing database optimization...")
        db_manager.optimize_database()
        
        # Cleanup
        db_manager.cleanup()
        
    finally:
        # Clean up test database
        try:
            os.unlink(db_path)
        except:
            pass
    
    print("✅ Database performance tests completed")


def test_lazy_loading():
    """Test lazy loading functionality"""
    print("\n=== Testing Lazy Loading ===")
    
    performance_manager = get_performance_manager()
    lazy_loader = performance_manager.lazy_loader
    
    def expensive_data_loader():
        """Simulate expensive data loading"""
        print("   Loading expensive data...")
        time.sleep(0.2)  # Simulate work
        return {"data": "expensive computation result", "timestamp": time.time()}
    
    print("\n1. First lazy load (should load):")
    start_time = time.time()
    result1 = lazy_loader.lazy_load("test_data", expensive_data_loader)
    time1 = time.time() - start_time
    print(f"   Result: {result1}")
    print(f"   Time: {time1:.3f}s")
    
    print("\n2. Second lazy load (should use cache):")
    start_time = time.time()
    result2 = lazy_loader.lazy_load("test_data", expensive_data_loader)
    time2 = time.time() - start_time
    print(f"   Result: {result2}")
    print(f"   Time: {time2:.3f}s")
    
    print(f"\n3. Cache hit: {time1/time2:.1f}x faster")
    
    print("✅ Lazy loading tests completed")


@optimize_startup
def test_startup_optimization():
    """Test startup optimization"""
    print("\n=== Testing Startup Optimization ===")
    
    performance_manager = get_performance_manager()
    startup_optimizer = performance_manager.startup_optimizer
    
    # Simulate module imports with timing
    @startup_optimizer.measure_import_time("test_module_1")
    def import_module_1():
        time.sleep(0.05)  # Simulate import time
        return "Module 1 loaded"
    
    @startup_optimizer.measure_import_time("test_module_2")  
    def import_module_2():
        time.sleep(0.1)  # Simulate slower import
        return "Module 2 loaded"
    
    @startup_optimizer.measure_import_time("test_module_3")
    def import_module_3():
        time.sleep(0.02)  # Simulate fast import
        return "Module 3 loaded"
    
    print("\n1. Simulating module imports...")
    import_module_1()
    import_module_2()
    import_module_3()
    
    # Get startup report
    print("\n2. Startup performance report:")
    report = startup_optimizer.get_startup_report()
    
    print(f"   Total import time: {report['total_import_time']:.3f}s")
    print(f"   Import count: {report['import_count']}")
    
    print("   Slowest imports:")
    for module, import_time in report['slowest_imports'][:5]:
        print(f"     {module}: {import_time:.3f}s")
    
    print("✅ Startup optimization tests completed")


def main():
    """Run all Phase 3 performance tests"""
    print("WestfallPersonalAssistant - Phase 3 Performance Optimization Tests")
    print("=" * 70)
    
    try:
        # Test all performance components
        test_caching_system()
        test_memory_monitoring()
        test_cached_decorator()
        test_database_performance()
        test_lazy_loading()
        test_startup_optimization()
        
        print("\n" + "=" * 70)
        print("🎉 All Phase 3 performance optimization tests completed successfully!")
        print("\nImplemented improvements:")
        print("✅ Comprehensive caching system with TTL and LRU eviction")
        print("✅ Memory monitoring with automatic cleanup triggers")
        print("✅ Database connection pooling for improved performance")
        print("✅ Query optimization with performance tracking")
        print("✅ Lazy loading for expensive operations")
        print("✅ Startup performance monitoring and optimization")
        print("✅ Decorators for easy performance enhancement (@cached, @optimize_startup)")
        print("✅ Automatic resource cleanup and memory management")
        
        # Final performance summary
        performance_manager = get_performance_manager()
        stats = performance_manager.get_performance_stats()
        
        print(f"\nFinal Statistics:")
        print(f"  Cache: {stats['cache']['total']['items']} items, "
              f"{stats['cache']['total']['size_mb']:.2f} MB")
        print(f"  Memory: {stats['memory']['current_mb']:.2f} MB used")
        print(f"  Startup: {stats['startup']['import_count']} modules, "
              f"{stats['startup']['total_import_time']:.3f}s total")
        
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())