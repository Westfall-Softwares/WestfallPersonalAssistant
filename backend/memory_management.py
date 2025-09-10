#!/usr/bin/env python3
"""
Memory Management System for Westfall Personal Assistant

Provides memory monitoring, streaming for large data processing,
and resource management with warnings and limits.
"""

import threading
import time
import logging
import gc
import os
import sys
from typing import Dict, List, Optional, Callable, Any, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
import weakref
from pathlib import Path

# Optional dependency
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.info("psutil not available - using basic memory monitoring")

logger = logging.getLogger(__name__)


@dataclass
class MemoryUsage:
    """Memory usage statistics."""
    total_mb: float
    available_mb: float
    used_mb: float
    used_percent: float
    process_mb: float
    process_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total_mb': self.total_mb,
            'available_mb': self.available_mb,
            'used_mb': self.used_mb,
            'used_percent': self.used_percent,
            'process_mb': self.process_mb,
            'process_percent': self.process_percent,
            'timestamp': self.timestamp.isoformat()
        }


class MemoryMonitor:
    """Monitors memory usage and provides warnings."""
    
    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        self.warning_threshold = warning_threshold  # Percentage
        self.critical_threshold = critical_threshold  # Percentage
        self.monitoring = False
        self.monitor_thread = None
        self.check_interval = 5.0  # seconds
        self.observers = []
        self.usage_history = []
        self.max_history = 1000
        
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        else:
            self.process = None
            logger.warning("Advanced memory monitoring disabled - psutil not available")
        
    def add_observer(self, observer: Callable[[MemoryUsage], None]):
        """Add memory usage observer."""
        self.observers.append(weakref.ref(observer))
    
    def get_current_usage(self) -> MemoryUsage:
        """Get current memory usage statistics."""
        if PSUTIL_AVAILABLE:
            # System memory
            system_memory = psutil.virtual_memory()
            
            # Process memory
            process_memory = self.process.memory_info()
            
            usage = MemoryUsage(
                total_mb=system_memory.total / (1024 * 1024),
                available_mb=system_memory.available / (1024 * 1024),
                used_mb=system_memory.used / (1024 * 1024),
                used_percent=system_memory.percent,
                process_mb=process_memory.rss / (1024 * 1024),
                process_percent=(process_memory.rss / system_memory.total) * 100,
                timestamp=datetime.now()
            )
        else:
            # Fallback basic memory info (Linux only)
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.readlines()
                
                mem_data = {}
                for line in meminfo:
                    key, value = line.split(':')
                    mem_data[key.strip()] = int(value.split()[0]) * 1024  # Convert KB to bytes
                
                total_mb = mem_data['MemTotal'] / (1024 * 1024)
                available_mb = mem_data.get('MemAvailable', mem_data.get('MemFree', 0)) / (1024 * 1024)
                used_mb = total_mb - available_mb
                used_percent = (used_mb / total_mb) * 100
                
                usage = MemoryUsage(
                    total_mb=total_mb,
                    available_mb=available_mb,
                    used_mb=used_mb,
                    used_percent=used_percent,
                    process_mb=0.0,  # Cannot get process memory without psutil
                    process_percent=0.0,
                    timestamp=datetime.now()
                )
            except (FileNotFoundError, IOError, ValueError):
                # Ultimate fallback - estimate based on Python's memory usage
                import resource
                try:
                    # Get current memory usage of this process in KB, convert to MB
                    process_memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    # On Linux, this is in KB, on macOS it's in bytes
                    if sys.platform == 'darwin':
                        process_mb = process_memory_kb / (1024 * 1024)
                    else:
                        process_mb = process_memory_kb / 1024
                    
                    # Estimate system memory (this is very rough)
                    estimated_total = max(4096, process_mb * 10)  # Assume at least 4GB
                    
                    usage = MemoryUsage(
                        total_mb=estimated_total,
                        available_mb=estimated_total * 0.5,  # Rough estimate
                        used_mb=estimated_total * 0.5,
                        used_percent=50.0,  # Rough estimate
                        process_mb=process_mb,
                        process_percent=(process_mb / estimated_total) * 100,
                        timestamp=datetime.now()
                    )
                except Exception:
                    # Last resort fallback
                    usage = MemoryUsage(
                        total_mb=4096.0,  # Assume 4GB
                        available_mb=2048.0,
                        used_mb=2048.0,
                        used_percent=50.0,
                        process_mb=100.0,  # Rough estimate
                        process_percent=2.5,
                        timestamp=datetime.now()
                    )
        
        return usage
    
    def start_monitoring(self):
        """Start memory monitoring in background thread."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                usage = self.get_current_usage()
                
                # Store in history
                self.usage_history.append(usage)
                if len(self.usage_history) > self.max_history:
                    self.usage_history = self.usage_history[-self.max_history:]
                
                # Check thresholds
                self._check_thresholds(usage)
                
                # Notify observers
                self._notify_observers(usage)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def _check_thresholds(self, usage: MemoryUsage):
        """Check memory usage against thresholds."""
        if usage.used_percent >= self.critical_threshold:
            logger.critical(f"Critical memory usage: {usage.used_percent:.1f}% "
                          f"({usage.used_mb:.0f}MB used, {usage.available_mb:.0f}MB available)")
            self._trigger_memory_cleanup()
        elif usage.used_percent >= self.warning_threshold:
            logger.warning(f"High memory usage: {usage.used_percent:.1f}% "
                         f"({usage.used_mb:.0f}MB used, {usage.available_mb:.0f}MB available)")
    
    def _trigger_memory_cleanup(self):
        """Trigger aggressive memory cleanup."""
        logger.info("Triggering memory cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collector freed {collected} objects")
        
        # TODO: Notify application components to free memory
        # This could trigger model unloading, cache clearing, etc.
    
    def _notify_observers(self, usage: MemoryUsage):
        """Notify memory usage observers."""
        # Clean up dead references
        self.observers = [ref for ref in self.observers if ref() is not None]
        
        for observer_ref in self.observers:
            observer = observer_ref()
            if observer:
                try:
                    observer(usage)
                except Exception as e:
                    logger.error(f"Error notifying memory observer: {e}")
    
    def get_usage_history(self, limit: int = 100) -> List[Dict]:
        """Get recent memory usage history."""
        recent_history = self.usage_history[-limit:] if limit else self.usage_history
        return [usage.to_dict() for usage in recent_history]
    
    def get_usage_stats(self) -> Dict:
        """Get memory usage statistics."""
        if not self.usage_history:
            return {}
        
        recent_usage = [u.used_percent for u in self.usage_history[-60:]]  # Last 5 minutes
        
        return {
            'current': self.get_current_usage().to_dict(),
            'average_percent': sum(recent_usage) / len(recent_usage),
            'peak_percent': max(recent_usage),
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'monitoring': self.monitoring
        }


class StreamProcessor:
    """Processes large datasets in streaming fashion to minimize memory usage."""
    
    def __init__(self, chunk_size: int = 1024):
        self.chunk_size = chunk_size
    
    def process_large_file(self, file_path: Path, processor: Callable[[str], Any]) -> Iterator[Any]:
        """Process large file in chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    yield processor(chunk)
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def process_large_text(self, text: str, processor: Callable[[str], Any]) -> Iterator[Any]:
        """Process large text in chunks."""
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            yield processor(chunk)
    
    def stream_json_array(self, file_path: Path) -> Iterator[Dict]:
        """Stream JSON array elements one by one."""
        import json
        
        try:
            with open(file_path, 'r') as f:
                # Skip opening bracket
                f.read(1)
                
                decoder = json.JSONDecoder()
                buffer = ""
                
                for chunk in iter(lambda: f.read(self.chunk_size), ''):
                    buffer += chunk
                    
                    while buffer:
                        buffer = buffer.lstrip()
                        if not buffer:
                            break
                        
                        try:
                            obj, idx = decoder.raw_decode(buffer)
                            yield obj
                            buffer = buffer[idx:].lstrip()
                            
                            # Skip comma if present
                            if buffer.startswith(','):
                                buffer = buffer[1:]
                                
                        except json.JSONDecodeError:
                            # Need more data
                            break
                            
        except Exception as e:
            logger.error(f"Error streaming JSON from {file_path}: {e}")
            raise


class DataPaginator:
    """Provides pagination for large datasets."""
    
    def __init__(self, page_size: int = 100):
        self.page_size = page_size
    
    def paginate_list(self, data: List[Any], page: int = 1) -> Dict:
        """Paginate a list of data."""
        total_items = len(data)
        total_pages = (total_items + self.page_size - 1) // self.page_size
        
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        page_data = data[start_idx:end_idx]
        
        return {
            'items': page_data,
            'pagination': {
                'current_page': page,
                'page_size': self.page_size,
                'total_items': total_items,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        }
    
    def paginate_query_results(self, query_func: Callable, total_count: int, 
                              page: int = 1, **kwargs) -> Dict:
        """Paginate database query results."""
        total_pages = (total_count + self.page_size - 1) // self.page_size
        offset = (page - 1) * self.page_size
        
        # Execute query with limit and offset
        items = query_func(limit=self.page_size, offset=offset, **kwargs)
        
        return {
            'items': items,
            'pagination': {
                'current_page': page,
                'page_size': self.page_size,
                'total_items': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        }


class ResourceLimiter:
    """Enforces resource limits on background processes."""
    
    def __init__(self):
        self.active_processes = {}
        self.max_concurrent_processes = 10
        self.max_memory_per_process = 512  # MB
        self.max_cpu_percent = 80.0
        self.lock = threading.RLock()
    
    def register_process(self, process_id: str, memory_limit: int = None) -> bool:
        """Register a background process with resource limits."""
        with self.lock:
            if len(self.active_processes) >= self.max_concurrent_processes:
                logger.warning(f"Cannot register process {process_id}: max concurrent limit reached")
                return False
            
            self.active_processes[process_id] = {
                'start_time': datetime.now(),
                'memory_limit': memory_limit or self.max_memory_per_process,
                'pid': os.getpid(),
                'thread_id': threading.get_ident()
            }
            
            logger.info(f"Registered process {process_id} with {memory_limit or self.max_memory_per_process}MB limit")
            return True
    
    def unregister_process(self, process_id: str):
        """Unregister a background process."""
        with self.lock:
            if process_id in self.active_processes:
                process_info = self.active_processes.pop(process_id)
                duration = datetime.now() - process_info['start_time']
                logger.info(f"Unregistered process {process_id} (ran for {duration})")
    
    def check_resource_usage(self, process_id: str) -> Dict:
        """Check resource usage for a specific process."""
        with self.lock:
            if process_id not in self.active_processes:
                return {'error': 'Process not registered'}
            
            try:
                if PSUTIL_AVAILABLE:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    cpu_percent = process.cpu_percent()
                else:
                    # Fallback - basic memory estimation
                    import resource
                    try:
                        usage = resource.getrusage(resource.RUSAGE_SELF)
                        if sys.platform == 'darwin':
                            memory_mb = usage.ru_maxrss / (1024 * 1024)
                        else:
                            memory_mb = usage.ru_maxrss / 1024
                        cpu_percent = 0.0  # Cannot get CPU % without psutil
                    except Exception:
                        memory_mb = 100.0  # Estimate
                        cpu_percent = 0.0
                
                process_info = self.active_processes[process_id]
                memory_limit = process_info['memory_limit']
                
                status = {
                    'memory_mb': memory_mb,
                    'memory_limit_mb': memory_limit,
                    'memory_percent': (memory_mb / memory_limit) * 100,
                    'cpu_percent': cpu_percent,
                    'within_limits': memory_mb <= memory_limit and cpu_percent <= self.max_cpu_percent
                }
                
                if not status['within_limits']:
                    logger.warning(f"Process {process_id} exceeding limits: "
                                 f"Memory: {memory_mb:.1f}MB/{memory_limit}MB, "
                                 f"CPU: {cpu_percent:.1f}%")
                
                return status
                
            except Exception as e:
                return {'error': str(e)}
    
    def get_active_processes(self) -> Dict:
        """Get information about all active processes."""
        with self.lock:
            processes = {}
            for process_id, info in self.active_processes.items():
                processes[process_id] = {
                    **info,
                    'duration': str(datetime.now() - info['start_time']),
                    'resource_status': self.check_resource_usage(process_id)
                }
            return processes


class MemoryManager:
    """Central memory management system."""
    
    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        self.monitor = MemoryMonitor(warning_threshold, critical_threshold)
        self.stream_processor = StreamProcessor()
        self.paginator = DataPaginator()
        self.resource_limiter = ResourceLimiter()
        self.cleanup_callbacks = []
        
        # Register cleanup callback
        self.monitor.add_observer(self._on_memory_usage)
    
    def start_monitoring(self):
        """Start memory monitoring."""
        self.monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitor.stop_monitoring()
    
    def add_cleanup_callback(self, callback: Callable[[], None]):
        """Add a callback to be called during memory cleanup."""
        self.cleanup_callbacks.append(weakref.ref(callback))
    
    def _on_memory_usage(self, usage: MemoryUsage):
        """Handle memory usage updates."""
        if usage.used_percent >= self.monitor.critical_threshold:
            self._trigger_cleanup()
    
    def _trigger_cleanup(self):
        """Trigger memory cleanup across the application."""
        logger.info("Triggering application-wide memory cleanup")
        
        # Clean up dead callback references
        self.cleanup_callbacks = [ref for ref in self.cleanup_callbacks if ref() is not None]
        
        # Call all cleanup callbacks
        for callback_ref in self.cleanup_callbacks:
            callback = callback_ref()
            if callback:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Memory cleanup completed, freed {collected} objects")
    
    def get_status(self) -> Dict:
        """Get overall memory management status."""
        return {
            'memory_stats': self.monitor.get_usage_stats(),
            'active_processes': self.resource_limiter.get_active_processes(),
            'monitoring_active': self.monitor.monitoring
        }


# Global memory manager instance
memory_manager = MemoryManager()


def initialize_memory_management(warning_threshold: float = 80.0, 
                               critical_threshold: float = 90.0) -> MemoryManager:
    """Initialize global memory management."""
    global memory_manager
    memory_manager = MemoryManager(warning_threshold, critical_threshold)
    memory_manager.start_monitoring()
    return memory_manager