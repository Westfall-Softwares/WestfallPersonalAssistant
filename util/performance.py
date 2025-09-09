"""
WestfallPersonalAssistant Performance Manager
Handles caching, memory management, and performance optimizations
"""

import os
import sys
import time
import json
import pickle
import hashlib
import threading
import weakref
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps, lru_cache
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage

from utils.resource_manager import get_resource_manager


class CacheManager(QObject):
    """Manages application-wide caching with automatic cleanup"""
    
    # Signals
    cache_cleared = pyqtSignal(str, int)  # cache_type, items_cleared
    cache_limit_reached = pyqtSignal(str, int)  # cache_type, current_size
    
    def __init__(self, cache_dir: str = None, max_cache_size_mb: int = 100):
        super().__init__()
        
        # Cache configuration
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".westfall_assistant", "cache")
        self.max_cache_size_mb = max_cache_size_mb
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # In-memory caches with different policies
        self.memory_caches = {
            'images': {},           # Image cache with size limits
            'api_responses': {},    # API response cache with TTL
            'file_metadata': {},    # File metadata cache
            'computed_values': {},  # Expensive computation cache
            'ui_data': {}          # UI-related data cache
        }
        
        # Cache metadata
        self.cache_metadata = {
            cache_type: {
                'access_times': {},
                'creation_times': {},
                'sizes': {},
                'max_size': self._get_max_cache_size(cache_type),
                'ttl': self._get_cache_ttl(cache_type)
            } for cache_type in self.memory_caches.keys()
        }
        
        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.periodic_cleanup)
        self.cleanup_timer.start(300000)  # 5 minutes
        
        # Thread safety
        self._cache_lock = threading.RLock()
    
    def _get_max_cache_size(self, cache_type: str) -> int:
        """Get maximum cache size for cache type"""
        sizes = {
            'images': 50,           # 50 items max
            'api_responses': 1000,  # 1000 responses max
            'file_metadata': 500,   # 500 files max
            'computed_values': 200, # 200 computations max
            'ui_data': 100          # 100 UI data items max
        }
        return sizes.get(cache_type, 100)
    
    def _get_cache_ttl(self, cache_type: str) -> int:
        """Get TTL (time to live) in seconds for cache type"""
        ttls = {
            'images': 3600,         # 1 hour
            'api_responses': 1800,  # 30 minutes
            'file_metadata': 600,   # 10 minutes
            'computed_values': 7200, # 2 hours
            'ui_data': 1800         # 30 minutes
        }
        return ttls.get(cache_type, 1800)
    
    def get(self, cache_type: str, key: str, default: Any = None) -> Any:
        """Get item from cache"""
        with self._cache_lock:
            if cache_type not in self.memory_caches:
                return default
            
            cache = self.memory_caches[cache_type]
            metadata = self.cache_metadata[cache_type]
            
            if key not in cache:
                return default
            
            # Check TTL
            if self._is_expired(cache_type, key):
                self._remove_item(cache_type, key)
                return default
            
            # Update access time
            metadata['access_times'][key] = time.time()
            
            return cache[key]
    
    def set(self, cache_type: str, key: str, value: Any, 
            ttl: Optional[int] = None) -> bool:
        """Set item in cache"""
        with self._cache_lock:
            if cache_type not in self.memory_caches:
                return False
            
            cache = self.memory_caches[cache_type]
            metadata = self.cache_metadata[cache_type]
            
            # Calculate size
            item_size = self._calculate_size(value)
            
            # Check if we need to make space
            if len(cache) >= metadata['max_size']:
                self._evict_lru_items(cache_type, 1)
            
            # Store item
            cache[key] = value
            current_time = time.time()
            metadata['access_times'][key] = current_time
            metadata['creation_times'][key] = current_time
            metadata['sizes'][key] = item_size
            
            return True
    
    def remove(self, cache_type: str, key: str) -> bool:
        """Remove item from cache"""
        with self._cache_lock:
            return self._remove_item(cache_type, key)
    
    def _remove_item(self, cache_type: str, key: str) -> bool:
        """Internal method to remove item"""
        if cache_type not in self.memory_caches:
            return False
        
        cache = self.memory_caches[cache_type]
        metadata = self.cache_metadata[cache_type]
        
        if key in cache:
            del cache[key]
            metadata['access_times'].pop(key, None)
            metadata['creation_times'].pop(key, None)
            metadata['sizes'].pop(key, None)
            return True
        
        return False
    
    def clear_cache(self, cache_type: str = None) -> int:
        """Clear specific cache or all caches"""
        with self._cache_lock:
            cleared_count = 0
            
            if cache_type:
                if cache_type in self.memory_caches:
                    cleared_count = len(self.memory_caches[cache_type])
                    self.memory_caches[cache_type].clear()
                    self.cache_metadata[cache_type]['access_times'].clear()
                    self.cache_metadata[cache_type]['creation_times'].clear()
                    self.cache_metadata[cache_type]['sizes'].clear()
                    self.cache_cleared.emit(cache_type, cleared_count)
            else:
                for cache_name in self.memory_caches:
                    cleared_count += len(self.memory_caches[cache_name])
                    self.memory_caches[cache_name].clear()
                    self.cache_metadata[cache_name]['access_times'].clear()
                    self.cache_metadata[cache_name]['creation_times'].clear()
                    self.cache_metadata[cache_name]['sizes'].clear()
                self.cache_cleared.emit("all", cleared_count)
            
            return cleared_count
    
    def _is_expired(self, cache_type: str, key: str) -> bool:
        """Check if cache item is expired"""
        metadata = self.cache_metadata[cache_type]
        
        if key not in metadata['creation_times']:
            return True
        
        creation_time = metadata['creation_times'][key]
        ttl = metadata['ttl']
        
        return time.time() - creation_time > ttl
    
    def _evict_lru_items(self, cache_type: str, count: int):
        """Evict least recently used items"""
        cache = self.memory_caches[cache_type]
        metadata = self.cache_metadata[cache_type]
        access_times = metadata['access_times']
        
        # Sort by access time
        items_by_access = sorted(
            access_times.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest items
        for i in range(min(count, len(items_by_access))):
            key = items_by_access[i][0]
            self._remove_item(cache_type, key)
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            if isinstance(value, (QPixmap, QImage)):
                # Estimate image size
                if hasattr(value, 'width') and hasattr(value, 'height'):
                    return value.width() * value.height() * 4  # RGBA
                return 1024  # Default estimate
            elif isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._calculate_size(k) + self._calculate_size(v)
                    for k, v in value.items()
                )
            else:
                # Use pickle size as estimate
                return len(pickle.dumps(value))
        except Exception:
            return 1024  # Default estimate if calculation fails
    
    def periodic_cleanup(self):
        """Perform periodic cache cleanup"""
        with self._cache_lock:
            total_cleaned = 0
            
            for cache_type in self.memory_caches:
                # Remove expired items
                expired_keys = []
                for key in list(self.memory_caches[cache_type].keys()):
                    if self._is_expired(cache_type, key):
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self._remove_item(cache_type, key)
                    total_cleaned += 1
            
            if total_cleaned > 0:
                self.cache_cleared.emit("expired", total_cleaned)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._cache_lock:
            stats = {}
            total_items = 0
            total_size = 0
            
            for cache_type, cache in self.memory_caches.items():
                metadata = self.cache_metadata[cache_type]
                cache_size = sum(metadata['sizes'].values())
                
                stats[cache_type] = {
                    'items': len(cache),
                    'max_items': metadata['max_size'],
                    'size_bytes': cache_size,
                    'ttl_seconds': metadata['ttl']
                }
                
                total_items += len(cache)
                total_size += cache_size
            
            stats['total'] = {
                'items': total_items,
                'size_bytes': total_size,
                'size_mb': total_size / (1024 * 1024),
                'max_size_mb': self.max_cache_size_mb
            }
            
            return stats


class ImageOptimizer:
    """Optimizes images for display and memory usage"""
    
    def __init__(self, max_dimension: int = 1920, quality: int = 85):
        self.max_dimension = max_dimension
        self.quality = quality
        self.cache_manager = None
    
    def set_cache_manager(self, cache_manager: CacheManager):
        """Set cache manager for optimized images"""
        self.cache_manager = cache_manager
    
    def optimize_image(self, image_path: str, target_size: tuple = None) -> Optional[QPixmap]:
        """Optimize image for display"""
        try:
            # Check cache first
            cache_key = f"{image_path}_{target_size}_{os.path.getmtime(image_path)}"
            
            if self.cache_manager:
                cached_image = self.cache_manager.get('images', cache_key)
                if cached_image:
                    return cached_image
            
            # Load and optimize image
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                return None
            
            # Resize if necessary
            if target_size:
                pixmap = pixmap.scaled(
                    target_size[0], target_size[1],
                    aspectRatioMode=1,  # KeepAspectRatio
                    transformMode=1     # SmoothTransformation
                )
            elif pixmap.width() > self.max_dimension or pixmap.height() > self.max_dimension:
                pixmap = pixmap.scaled(
                    self.max_dimension, self.max_dimension,
                    aspectRatioMode=1,
                    transformMode=1
                )
            
            # Cache optimized image
            if self.cache_manager:
                self.cache_manager.set('images', cache_key, pixmap)
            
            return pixmap
            
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")
            return None


class LazyLoader:
    """Lazy loading utility for expensive operations"""
    
    def __init__(self, cache_manager: CacheManager = None):
        self.cache_manager = cache_manager
        self._loading_states = {}
        self._lock = threading.RLock()
    
    def lazy_load(self, key: str, loader_func: Callable, 
                  cache_type: str = 'computed_values',
                  force_reload: bool = False) -> Any:
        """Lazy load data with caching"""
        with self._lock:
            # Check if already loading
            if key in self._loading_states and self._loading_states[key]:
                return None  # Currently loading
            
            # Check cache first
            if not force_reload and self.cache_manager:
                cached_value = self.cache_manager.get(cache_type, key)
                if cached_value is not None:
                    return cached_value
            
            # Mark as loading
            self._loading_states[key] = True
            
            try:
                # Load data
                result = loader_func()
                
                # Cache result
                if self.cache_manager and result is not None:
                    self.cache_manager.set(cache_type, key, result)
                
                return result
                
            except Exception as e:
                print(f"Error in lazy loader for {key}: {e}")
                return None
            finally:
                # Mark as not loading
                self._loading_states[key] = False


class StartupOptimizer:
    """Optimizes application startup performance"""
    
    def __init__(self):
        self.import_cache = {}
        self.initialization_times = {}
        self.critical_imports = set()
        self.deferred_imports = set()
    
    def measure_import_time(self, module_name: str):
        """Decorator to measure import time"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    import_time = time.time() - start_time
                    self.initialization_times[module_name] = import_time
                    return result
                except Exception as e:
                    import_time = time.time() - start_time
                    self.initialization_times[f"{module_name}_failed"] = import_time
                    raise e
            return wrapper
        return decorator
    
    def defer_import(self, module_name: str):
        """Mark module for deferred import"""
        self.deferred_imports.add(module_name)
    
    def mark_critical(self, module_name: str):
        """Mark module as critical for startup"""
        self.critical_imports.add(module_name)
    
    def get_startup_report(self) -> Dict[str, Any]:
        """Get startup performance report"""
        total_time = sum(self.initialization_times.values())
        
        # Sort by time taken
        sorted_times = sorted(
            self.initialization_times.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'total_import_time': total_time,
            'slowest_imports': sorted_times[:10],
            'critical_imports': list(self.critical_imports),
            'deferred_imports': list(self.deferred_imports),
            'import_count': len(self.initialization_times)
        }


class MemoryMonitor(QObject):
    """Monitors memory usage and triggers cleanup when needed"""
    
    # Signals
    memory_warning = pyqtSignal(float)  # memory_usage_mb
    memory_critical = pyqtSignal(float)  # memory_usage_mb
    cleanup_triggered = pyqtSignal(str)  # cleanup_type
    memory_leak_detected = pyqtSignal(str, float)  # component, growth_rate
    
    def __init__(self, warning_threshold_mb: float = 200, 
                 critical_threshold_mb: float = 500):
        super().__init__()
        
        self.warning_threshold = warning_threshold_mb * 1024 * 1024  # Convert to bytes
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        
        # Memory tracking
        self.memory_history = []
        self.component_memory = {}
        self.last_cleanup_time = time.time()
        
        # Monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_memory_usage)
        self.monitor_timer.start(30000)  # Check every 30 seconds
        
        # Leak detection timer
        self.leak_timer = QTimer()
        self.leak_timer.timeout.connect(self.detect_memory_leaks)
        self.leak_timer.start(300000)  # Check every 5 minutes
        
        # Components to manage
        self.managed_components = []
        self.memory_alerts_sent = set()
    
    def register_component(self, component, name: str = None):
        """Register component for memory management"""
        component_name = name or component.__class__.__name__
        self.managed_components.append({
            'ref': weakref.ref(component),
            'name': component_name,
            'initial_memory': self.get_memory_usage()
        })
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in bytes"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss
        except ImportError:
            # Fallback method using resource module
            try:
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            except ImportError:
                return 0  # Can't measure memory
    
    def get_detailed_memory_info(self) -> Dict[str, float]:
        """Get detailed memory information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'shared': getattr(memory_info, 'shared', 0),
                'text': getattr(memory_info, 'text', 0),
                'data': getattr(memory_info, 'data', 0),
                'lib': getattr(memory_info, 'lib', 0),
                'dirty': getattr(memory_info, 'dirty', 0)
            }
        except ImportError:
            return {'rss': self.get_memory_usage()}
    
    def check_memory_usage(self):
        """Check current memory usage and trigger cleanup if needed"""
        memory_usage = self.get_memory_usage()
        memory_mb = memory_usage / (1024 * 1024)
        
        # Track memory history
        self.memory_history.append({
            'timestamp': time.time(),
            'memory_mb': memory_mb,
            'detailed': self.get_detailed_memory_info()
        })
        
        # Keep only last 100 readings
        if len(self.memory_history) > 100:
            self.memory_history = self.memory_history[-100:]
        
        # Check thresholds
        if memory_usage > self.critical_threshold:
            alert_key = f"critical_{int(memory_mb)}"
            if alert_key not in self.memory_alerts_sent:
                self.memory_critical.emit(memory_mb)
                self.memory_alerts_sent.add(alert_key)
                self.trigger_aggressive_cleanup()
        elif memory_usage > self.warning_threshold:
            alert_key = f"warning_{int(memory_mb)}"
            if alert_key not in self.memory_alerts_sent:
                self.memory_warning.emit(memory_mb)
                self.memory_alerts_sent.add(alert_key)
                self.trigger_gentle_cleanup()
        
        # Clear old alerts
        current_level = int(memory_mb)
        self.memory_alerts_sent = {
            alert for alert in self.memory_alerts_sent
            if abs(int(alert.split('_')[1]) - current_level) < 50
        }
    
    def detect_memory_leaks(self):
        """Detect potential memory leaks by analyzing memory growth patterns"""
        if len(self.memory_history) < 10:
            return  # Not enough data
        
        # Calculate memory growth rate over last 10 readings
        recent_readings = self.memory_history[-10:]
        initial_memory = recent_readings[0]['memory_mb']
        final_memory = recent_readings[-1]['memory_mb']
        time_span = recent_readings[-1]['timestamp'] - recent_readings[0]['timestamp']
        
        if time_span > 0:
            growth_rate_mb_per_hour = (final_memory - initial_memory) / (time_span / 3600)
            
            # Consider it a leak if memory grows consistently > 10MB/hour
            if growth_rate_mb_per_hour > 10:
                # Check if growth is consistent (not just a spike)
                growths = []
                for i in range(1, len(recent_readings)):
                    growth = recent_readings[i]['memory_mb'] - recent_readings[i-1]['memory_mb']
                    growths.append(growth)
                
                positive_growths = [g for g in growths if g > 0]
                if len(positive_growths) > len(growths) * 0.8:  # 80% of readings show growth
                    self.memory_leak_detected.emit("System", growth_rate_mb_per_hour)
                    
                    # Log detailed information for debugging
                    print(f"Potential memory leak detected: {growth_rate_mb_per_hour:.2f} MB/hour growth")
                    self._log_memory_leak_details()
    
    def _log_memory_leak_details(self):
        """Log detailed memory information for leak analysis"""
        try:
            import psutil
            process = psutil.Process()
            
            # Get memory maps if available
            if hasattr(process, 'memory_maps'):
                memory_maps = process.memory_maps()
                large_mappings = [
                    mapping for mapping in memory_maps
                    if mapping.rss > 10 * 1024 * 1024  # > 10MB
                ]
                
                print("Large memory mappings:")
                for mapping in large_mappings[:10]:  # Top 10
                    print(f"  {mapping.path}: {mapping.rss / 1024 / 1024:.1f} MB")
            
            # Get open file descriptors
            if hasattr(process, 'open_files'):
                open_files = process.open_files()
                print(f"Open file descriptors: {len(open_files)}")
                
            # Get thread count
            print(f"Thread count: {process.num_threads()}")
            
        except Exception as e:
            print(f"Failed to log memory leak details: {e}")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory usage report"""
        if not self.memory_history:
            return {}
        
        current_memory = self.memory_history[-1]
        memory_mb = current_memory['memory_mb']
        
        # Calculate statistics
        memory_values = [reading['memory_mb'] for reading in self.memory_history]
        min_memory = min(memory_values)
        max_memory = max(memory_values)
        avg_memory = sum(memory_values) / len(memory_values)
        
        # Calculate growth rate
        growth_rate = 0
        if len(self.memory_history) >= 2:
            first_reading = self.memory_history[0]
            last_reading = self.memory_history[-1]
            time_diff = last_reading['timestamp'] - first_reading['timestamp']
            if time_diff > 0:
                memory_diff = last_reading['memory_mb'] - first_reading['memory_mb']
                growth_rate = memory_diff / (time_diff / 3600)  # MB per hour
        
        return {
            'current_memory_mb': memory_mb,
            'min_memory_mb': min_memory,
            'max_memory_mb': max_memory,
            'avg_memory_mb': avg_memory,
            'growth_rate_mb_per_hour': growth_rate,
            'warning_threshold_mb': self.warning_threshold / (1024 * 1024),
            'critical_threshold_mb': self.critical_threshold / (1024 * 1024),
            'readings_count': len(self.memory_history),
            'last_cleanup': self.last_cleanup_time,
            'detailed_info': current_memory.get('detailed', {}),
            'managed_components': len([c for c in self.managed_components if c['ref']() is not None])
        }
    
    def trigger_gentle_cleanup(self):
        """Trigger gentle cleanup"""
        # Clear expired cache items
        try:
            cache_manager = get_performance_manager().cache_manager
            cache_manager.periodic_cleanup()
        except:
            pass
        
        # Clean up resources
        try:
            resource_manager = get_resource_manager()
            resource_manager.cleanup_temp_files()
        except:
            pass
        
        self.last_cleanup_time = time.time()
        self.cleanup_triggered.emit("gentle")
    
    def trigger_aggressive_cleanup(self):
        """Trigger aggressive cleanup"""
        # Clear all caches
        try:
            cache_manager = get_performance_manager().cache_manager
            cache_manager.clear_cache()
        except:
            pass
        
        # Clean up all resources
        try:
            resource_manager = get_resource_manager()
            resource_manager.full_cleanup()
        except:
            pass
        
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Clear component references if they're no longer valid
        self.managed_components = [
            comp for comp in self.managed_components
            if comp['ref']() is not None
        ]
        
        self.last_cleanup_time = time.time()
        self.cleanup_triggered.emit("aggressive")
    
    def force_garbage_collection(self):
        """Force comprehensive garbage collection"""
        import gc
        
        # Enable garbage collection debug
        old_flags = gc.get_debug()
        gc.set_debug(gc.DEBUG_STATS)
        
        # Multiple collection passes
        for i in range(3):
            collected = gc.collect()
            print(f"Garbage collection pass {i+1}: {collected} objects collected")
        
        # Restore original debug flags
        gc.set_debug(old_flags)
        
        return gc.get_stats()


class PerformanceManager(QObject):
    """Main performance management class"""
    
    def __init__(self, cache_dir: str = None, max_cache_size_mb: int = 100):
        super().__init__()
        
        # Components
        self.cache_manager = CacheManager(cache_dir, max_cache_size_mb)
        self.image_optimizer = ImageOptimizer()
        self.lazy_loader = LazyLoader(self.cache_manager)
        self.startup_optimizer = StartupOptimizer()
        self.memory_monitor = MemoryMonitor()
        
        # Connect components
        self.image_optimizer.set_cache_manager(self.cache_manager)
        
        # Connect signals
        self.memory_monitor.memory_warning.connect(self.on_memory_warning)
        self.memory_monitor.memory_critical.connect(self.on_memory_critical)
    
    def on_memory_warning(self, memory_mb: float):
        """Handle memory warning"""
        print(f"Memory warning: {memory_mb:.1f}MB used")
    
    def on_memory_critical(self, memory_mb: float):
        """Handle critical memory usage"""
        print(f"Critical memory usage: {memory_mb:.1f}MB used - triggering cleanup")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'cache': self.cache_manager.get_cache_stats(),
            'memory': {
                'current_mb': self.memory_monitor.get_memory_usage() / (1024 * 1024),
                'warning_threshold_mb': self.memory_monitor.warning_threshold / (1024 * 1024),
                'critical_threshold_mb': self.memory_monitor.critical_threshold / (1024 * 1024)
            },
            'startup': self.startup_optimizer.get_startup_report()
        }


# Decorators for performance optimization
def cached(cache_type: str = 'computed_values', ttl: Optional[int] = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = f"{func.__name__}_{args}_{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            performance_manager = get_performance_manager()
            cached_result = performance_manager.cache_manager.get(cache_type, cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            performance_manager.cache_manager.set(cache_type, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def lazy_property(func):
    """Decorator for lazy property evaluation"""
    attr_name = f'_lazy_{func.__name__}'
    
    @property
    @wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return wrapper


# Global instance
_performance_manager = None

def get_performance_manager() -> PerformanceManager:
    """Get the global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager


def optimize_startup(func):
    """Decorator to measure and optimize startup functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            print(f"Startup function {func.__name__}: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"Startup function {func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper