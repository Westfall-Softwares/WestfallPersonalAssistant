"""
WestfallPersonalAssistant Resource Manager
Handles resource management and cleanup operations
"""

import os
import sys
import tempfile
import threading
import sqlite3
import logging
import shutil
import time
import weakref
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Callable
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ResourceManager(QObject):
    """Manages application resources and cleanup"""
    
    # Signals
    cleanup_completed = pyqtSignal(str, int)  # operation, count
    resource_warning = pyqtSignal(str)  # warning message
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ResourceManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize resource manager"""
        if self._initialized:
            return
            
        super().__init__()
        
        # Resource tracking
        self.temp_files = set()
        self.temp_dirs = set()
        self.database_connections = weakref.WeakSet()
        self.screen_capture_resources = weakref.WeakSet()
        self.open_files = weakref.WeakSet()
        
        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.periodic_cleanup)
        self.cleanup_timer.start(300000)  # 5 minutes
        
        # Configuration
        self.max_temp_age_hours = 24
        self.max_log_age_days = 7
        self.max_cache_size_mb = 100
        
        self._initialized = True
        logging.info("Resource manager initialized")
    
    def register_temp_file(self, file_path: str) -> str:
        """Register a temporary file for cleanup"""
        file_path = os.path.abspath(file_path)
        self.temp_files.add(file_path)
        logging.debug(f"Registered temp file: {file_path}")
        return file_path
    
    def register_temp_dir(self, dir_path: str) -> str:
        """Register a temporary directory for cleanup"""
        dir_path = os.path.abspath(dir_path)
        self.temp_dirs.add(dir_path)
        logging.debug(f"Registered temp directory: {dir_path}")
        return dir_path
    
    def register_database_connection(self, connection):
        """Register a database connection for proper cleanup"""
        if connection and hasattr(connection, 'close'):
            # Store connection info instead of weak reference for sqlite3 compatibility
            if not hasattr(self, '_db_connections'):
                self._db_connections = []
            self._db_connections.append(connection)
            logging.debug("Registered database connection")
    
    def register_screen_capture_resource(self, resource):
        """Register a screen capture resource for cleanup"""
        if resource:
            self.screen_capture_resources.add(resource)
            logging.debug("Registered screen capture resource")
    
    def register_open_file(self, file_handle):
        """Register an open file handle for cleanup"""
        if file_handle and hasattr(file_handle, 'close'):
            self.open_files.add(file_handle)
            logging.debug("Registered open file handle")

    @contextmanager
    def managed_file(self, file_path: str, mode: str = 'r'):
        """Context manager for automatic file cleanup"""
        file_handle = None
        try:
            file_handle = open(file_path, mode)
            self.register_open_file(file_handle)
            yield file_handle
        finally:
            if file_handle and not file_handle.closed:
                file_handle.close()
                try:
                    self.open_files.remove(file_handle)
                except KeyError:
                    pass  # Already removed
    
    @contextmanager 
    def managed_temp_file(self, suffix: str = '', prefix: str = 'wpa_'):
        """Context manager for temporary files with automatic cleanup"""
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=suffix, 
                prefix=prefix, 
                delete=False
            )
            self.register_temp_file(temp_file.name)
            yield temp_file
        finally:
            if temp_file:
                temp_file.close()
                try:
                    os.unlink(temp_file.name)
                    self.temp_files.discard(temp_file.name)
                except (OSError, PermissionError):
                    pass  # File may already be deleted
    
    @contextmanager
    def managed_database_connection(self, database_path: str):
        """Context manager for database connections with automatic cleanup"""
        connection = None
        try:
            connection = sqlite3.connect(database_path)
            self.register_database_connection(connection)
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                try:
                    connection.close()
                    if hasattr(self, '_db_connections'):
                        try:
                            self._db_connections.remove(connection)
                        except ValueError:
                            pass  # Already removed
                except Exception as e:
                    logging.error(f"Error closing database connection: {e}")
    
    def cleanup_temp_files(self) -> int:
        """Clean up temporary files"""
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = self.max_temp_age_hours * 3600
        
        # Clean registered temp files
        files_to_remove = set()
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
                        logging.debug(f"Cleaned temp file: {file_path}")
                files_to_remove.add(file_path)
            except Exception as e:
                logging.warning(f"Failed to clean temp file {file_path}: {e}")
                files_to_remove.add(file_path)  # Remove from tracking even if cleanup failed
        
        # Remove cleaned files from tracking
        self.temp_files -= files_to_remove
        
        # Clean system temp directory of our files
        cleaned_count += self._cleanup_system_temp_files()
        
        if cleaned_count > 0:
            self.cleanup_completed.emit("temp_files", cleaned_count)
            logging.info(f"Cleaned {cleaned_count} temporary files")
        
        return cleaned_count
    
    def cleanup_temp_dirs(self) -> int:
        """Clean up temporary directories"""
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = self.max_temp_age_hours * 3600
        
        dirs_to_remove = set()
        for dir_path in self.temp_dirs:
            try:
                if os.path.exists(dir_path):
                    dir_age = current_time - os.path.getmtime(dir_path)
                    if dir_age > max_age_seconds:
                        shutil.rmtree(dir_path)
                        cleaned_count += 1
                        logging.debug(f"Cleaned temp directory: {dir_path}")
                dirs_to_remove.add(dir_path)
            except Exception as e:
                logging.warning(f"Failed to clean temp directory {dir_path}: {e}")
                dirs_to_remove.add(dir_path)
        
        self.temp_dirs -= dirs_to_remove
        
        if cleaned_count > 0:
            self.cleanup_completed.emit("temp_dirs", cleaned_count)
            logging.info(f"Cleaned {cleaned_count} temporary directories")
        
        return cleaned_count
    
    def cleanup_database_connections(self) -> int:
        """Close any open database connections"""
        cleaned_count = 0
        
        if hasattr(self, '_db_connections'):
            connections_to_close = self._db_connections.copy()
            self._db_connections.clear()
            
            for connection in connections_to_close:
                try:
                    if connection and hasattr(connection, 'close'):
                        connection.close()
                        cleaned_count += 1
                        logging.debug("Closed database connection")
                except Exception as e:
                    logging.warning(f"Failed to close database connection: {e}")
        
        if cleaned_count > 0:
            self.cleanup_completed.emit("database_connections", cleaned_count)
            logging.info(f"Closed {cleaned_count} database connections")
        
        return cleaned_count
    
    def cleanup_screen_capture_resources(self) -> int:
        """Clean up screen capture resources"""
        cleaned_count = 0
        
        resources_to_cleanup = list(self.screen_capture_resources)
        
        for resource in resources_to_cleanup:
            try:
                if resource:
                    # Try different cleanup methods depending on resource type
                    if hasattr(resource, 'close'):
                        resource.close()
                    elif hasattr(resource, 'release'):
                        resource.release()
                    elif hasattr(resource, 'cleanup'):
                        resource.cleanup()
                    cleaned_count += 1
                    logging.debug("Cleaned screen capture resource")
            except Exception as e:
                logging.warning(f"Failed to clean screen capture resource: {e}")
        
        if cleaned_count > 0:
            self.cleanup_completed.emit("screen_capture", cleaned_count)
            logging.info(f"Cleaned {cleaned_count} screen capture resources")
        
        return cleaned_count
    
    def cleanup_open_files(self) -> int:
        """Close any open file handles"""
        cleaned_count = 0
        
        files_to_close = list(self.open_files)
        
        for file_handle in files_to_close:
            try:
                if file_handle and hasattr(file_handle, 'close') and not file_handle.closed:
                    file_handle.close()
                    cleaned_count += 1
                    logging.debug("Closed open file handle")
            except Exception as e:
                logging.warning(f"Failed to close file handle: {e}")
        
        if cleaned_count > 0:
            self.cleanup_completed.emit("open_files", cleaned_count)
            logging.info(f"Closed {cleaned_count} open file handles")
        
        return cleaned_count
    
    def _cleanup_system_temp_files(self) -> int:
        """Clean up application files in system temp directory"""
        cleaned_count = 0
        temp_dir = tempfile.gettempdir()
        app_prefix = "westfall_assistant_"
        
        try:
            for filename in os.listdir(temp_dir):
                if filename.startswith(app_prefix):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            file_age = time.time() - os.path.getmtime(file_path)
                            if file_age > self.max_temp_age_hours * 3600:
                                os.remove(file_path)
                                cleaned_count += 1
                        elif os.path.isdir(file_path):
                            dir_age = time.time() - os.path.getmtime(file_path)
                            if dir_age > self.max_temp_age_hours * 3600:
                                shutil.rmtree(file_path)
                                cleaned_count += 1
                    except Exception as e:
                        logging.warning(f"Failed to clean system temp file {file_path}: {e}")
        except Exception as e:
            logging.warning(f"Failed to scan system temp directory: {e}")
        
        return cleaned_count
    
    def periodic_cleanup(self):
        """Perform periodic cleanup of resources"""
        logging.debug("Starting periodic cleanup")
        
        total_cleaned = 0
        total_cleaned += self.cleanup_temp_files()
        total_cleaned += self.cleanup_temp_dirs()
        total_cleaned += self.cleanup_open_files()
        
        if total_cleaned > 0:
            logging.info(f"Periodic cleanup completed: {total_cleaned} items cleaned")
    
    def full_cleanup(self):
        """Perform a complete cleanup of all resources"""
        logging.info("Starting full resource cleanup")
        
        total_cleaned = 0
        total_cleaned += self.cleanup_temp_files()
        total_cleaned += self.cleanup_temp_dirs()
        total_cleaned += self.cleanup_database_connections()
        total_cleaned += self.cleanup_screen_capture_resources()
        total_cleaned += self.cleanup_open_files()
        
        logging.info(f"Full cleanup completed: {total_cleaned} items cleaned")
        return total_cleaned
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked resources"""
        db_connections = len(getattr(self, '_db_connections', []))
        return {
            'temp_files': len(self.temp_files),
            'temp_dirs': len(self.temp_dirs),
            'database_connections': db_connections,
            'screen_capture_resources': len(self.screen_capture_resources),
            'open_files': len(self.open_files),
            'cleanup_interval_minutes': self.cleanup_timer.interval() // 60000
        }


@contextmanager
def managed_temp_file(suffix='', prefix='westfall_assistant_', dir=None):
    """Context manager for temporary files with automatic cleanup"""
    resource_manager = get_resource_manager()
    
    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)  # Close the file descriptor, we just need the path
    
    # Register for cleanup
    resource_manager.register_temp_file(temp_path)
    
    try:
        yield temp_path
    finally:
        # Immediate cleanup
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            resource_manager.temp_files.discard(temp_path)
        except Exception as e:
            logging.warning(f"Failed to cleanup temp file {temp_path}: {e}")


@contextmanager
def managed_temp_dir(suffix='', prefix='westfall_assistant_', dir=None):
    """Context manager for temporary directories with automatic cleanup"""
    resource_manager = get_resource_manager()
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
    
    # Register for cleanup
    resource_manager.register_temp_dir(temp_dir)
    
    try:
        yield temp_dir
    finally:
        # Immediate cleanup
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            resource_manager.temp_dirs.discard(temp_dir)
        except Exception as e:
            logging.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


@contextmanager
def managed_database_connection(database_path: str, **kwargs):
    """Context manager for database connections with automatic cleanup"""
    resource_manager = get_resource_manager()
    connection = None
    
    try:
        connection = sqlite3.connect(database_path, **kwargs)
        resource_manager.register_database_connection(connection)
        yield connection
    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except:
                pass
        raise e
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logging.warning(f"Failed to close database connection: {e}")


# Global instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def cleanup_all_resources():
    """Cleanup all tracked resources"""
    return get_resource_manager().full_cleanup()


class LRUCache:
    """LRU (Least Recently Used) cache with size limits and automatic eviction"""
    
    def __init__(self, max_size_mb: int = 50, max_items: int = 1000):
        """Initialize LRU cache with size and item limits"""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_items = max_items
        self.cache = {}
        self.access_order = []  # Most recent at end
        self.current_size_bytes = 0
        self._lock = threading.Lock()
    
    def _estimate_size(self, value) -> int:
        """Estimate memory size of a value"""
        if isinstance(value, str):
            return len(value.encode('utf-8'))
        elif isinstance(value, bytes):
            return len(value)
        elif isinstance(value, (int, float)):
            return 8  # Approximate
        elif isinstance(value, (list, tuple)):
            return sum(self._estimate_size(item) for item in value)
        elif isinstance(value, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) 
                      for k, v in value.items())
        else:
            # Fallback estimation
            return sys.getsizeof(value)
    
    def _evict_lru(self):
        """Evict least recently used items to stay within limits"""
        while (len(self.cache) > self.max_items or 
               self.current_size_bytes > self.max_size_bytes):
            if not self.access_order:
                break
                
            # Remove least recently used item
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                value_size = self._estimate_size(self.cache[lru_key])
                del self.cache[lru_key]
                self.current_size_bytes -= value_size
                logging.debug(f"LRU cache evicted key: {lru_key}")
    
    def get(self, key, default=None):
        """Get value from cache, updating access order"""
        with self._lock:
            if key in self.cache:
                # Move to end (most recent)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return default
    
    def set(self, key, value):
        """Set value in cache with LRU eviction"""
        with self._lock:
            value_size = self._estimate_size(value)
            
            # Remove existing key if present
            if key in self.cache:
                old_size = self._estimate_size(self.cache[key])
                self.current_size_bytes -= old_size
                self.access_order.remove(key)
            
            # Add new value
            self.cache[key] = value
            self.access_order.append(key)
            self.current_size_bytes += value_size
            
            # Evict if necessary
            self._evict_lru()
    
    def remove(self, key):
        """Remove key from cache"""
        with self._lock:
            if key in self.cache:
                value_size = self._estimate_size(self.cache[key])
                del self.cache[key]
                self.access_order.remove(key)
                self.current_size_bytes -= value_size
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_size_bytes = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'size_mb': self.current_size_bytes / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'items': len(self.cache),
                'max_items': self.max_items,
                'usage_percent': (self.current_size_bytes / self.max_size_bytes) * 100
            }


# Global cache instances
_data_cache = None
_image_cache = None

def get_data_cache() -> LRUCache:
    """Get global data cache instance"""
    global _data_cache
    if _data_cache is None:
        _data_cache = LRUCache(max_size_mb=50, max_items=500)
    return _data_cache

def get_image_cache() -> LRUCache:
    """Get global image cache instance"""
    global _image_cache
    if _image_cache is None:
        _image_cache = LRUCache(max_size_mb=25, max_items=100)
    return _image_cache