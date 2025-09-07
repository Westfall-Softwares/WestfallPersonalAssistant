"""
WestfallPersonalAssistant Thread Safety Manager
Provides thread-safe operations and synchronization utilities
"""

import threading
import queue
import logging
import time
import weakref
from typing import Any, Callable, Dict, Optional, Set
from contextlib import contextmanager
from PyQt5.QtCore import QObject, QMutex, QWaitCondition, QThread, pyqtSignal, QTimer


class ThreadSafetyManager(QObject):
    """Manages thread safety across the application"""
    
    # Signals for thread-safe UI updates
    ui_update_requested = pyqtSignal(str, object)  # operation_id, data
    background_task_completed = pyqtSignal(str, bool, object)  # task_id, success, result
    
    _instance = None
    _init_lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super(ThreadSafetyManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize thread safety manager"""
        if self._initialized:
            return
            
        super().__init__()
        
        # Mutex locks for different resources
        self.locks = {
            'database': QMutex(),
            'file_operations': QMutex(),
            'network_requests': QMutex(),
            'screen_capture': QMutex(),
            'settings': QMutex(),
            'cache': QMutex(),
            'ui_updates': QMutex()
        }
        
        # Wait conditions for complex synchronization
        self.wait_conditions = {
            'database': QWaitCondition(),
            'network': QWaitCondition(),
            'file_ops': QWaitCondition()
        }
        
        # Thread tracking
        self.active_threads: Set[QThread] = weakref.WeakSet()
        self.background_tasks: Dict[str, QThread] = {}
        
        # Python threading locks for non-Qt operations
        self.py_locks = {
            'dependency_manager': threading.RLock(),
            'error_handler': threading.RLock(),
            'resource_manager': threading.RLock(),
            'logging': threading.RLock()
        }
        
        # Thread-safe data structures
        self.ui_update_queue = queue.Queue()
        self.task_results = {}
        
        # Setup UI update timer
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._process_ui_updates)
        self.ui_update_timer.start(50)  # Process UI updates every 50ms
        
        self._initialized = True
        logging.info("Thread safety manager initialized")
    
    @contextmanager
    def lock_resource(self, resource_name: str):
        """Context manager for acquiring resource locks"""
        if resource_name in self.locks:
            mutex = self.locks[resource_name]
            mutex.lock()
            try:
                yield
            finally:
                mutex.unlock()
        elif resource_name in self.py_locks:
            lock = self.py_locks[resource_name]
            with lock:
                yield
        else:
            logging.warning(f"Unknown resource lock requested: {resource_name}")
            yield
    
    @contextmanager
    def database_transaction(self, connection):
        """Context manager for thread-safe database transactions"""
        with self.lock_resource('database'):
            try:
                yield connection
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise e
    
    def safe_ui_update(self, operation_id: str, update_func: Callable, data: Any = None):
        """Queue a UI update for safe execution on the main thread"""
        self.ui_update_queue.put((operation_id, update_func, data))
    
    def _process_ui_updates(self):
        """Process queued UI updates on the main thread"""
        try:
            while not self.ui_update_queue.empty():
                operation_id, update_func, data = self.ui_update_queue.get_nowait()
                try:
                    if callable(update_func):
                        update_func(data)
                    self.ui_update_requested.emit(operation_id, data)
                except Exception as e:
                    logging.error(f"Error processing UI update {operation_id}: {e}")
        except queue.Empty:
            pass
    
    def register_thread(self, thread: QThread):
        """Register a thread for tracking"""
        self.active_threads.add(thread)
        thread.finished.connect(lambda: self._thread_finished(thread))
        logging.debug(f"Registered thread: {thread}")
    
    def _thread_finished(self, thread: QThread):
        """Handle thread cleanup when finished"""
        # Note: Using weak references, so thread might already be gone
        logging.debug(f"Thread finished: {thread}")
    
    def start_background_task(self, task_id: str, worker_func: Callable, 
                            callback: Optional[Callable] = None, 
                            error_callback: Optional[Callable] = None,
                            *args, **kwargs):
        """Start a background task with proper thread management"""
        
        class BackgroundWorker(QThread):
            finished_signal = pyqtSignal(str, bool, object)
            
            def __init__(self, task_id, func, args, kwargs):
                super().__init__()
                self.task_id = task_id
                self.func = func
                self.args = args
                self.kwargs = kwargs
                self.result = None
                self.success = False
            
            def run(self):
                try:
                    self.result = self.func(*self.args, **self.kwargs)
                    self.success = True
                except Exception as e:
                    self.result = e
                    self.success = False
                    logging.error(f"Background task {self.task_id} failed: {e}")
                finally:
                    self.finished_signal.emit(self.task_id, self.success, self.result)
        
        # Create and start worker
        worker = BackgroundWorker(task_id, worker_func, args, kwargs)
        
        # Connect signals
        worker.finished_signal.connect(
            lambda tid, success, result: self._handle_background_task_result(
                tid, success, result, callback, error_callback
            )
        )
        
        # Track the task
        self.background_tasks[task_id] = worker
        self.register_thread(worker)
        
        # Start the task
        worker.start()
        
        return worker
    
    def _handle_background_task_result(self, task_id: str, success: bool, result: Any,
                                     callback: Optional[Callable] = None,
                                     error_callback: Optional[Callable] = None):
        """Handle the result of a background task"""
        # Store result
        self.task_results[task_id] = (success, result)
        
        # Execute callbacks on main thread
        if success and callback:
            self.safe_ui_update(f"{task_id}_success", callback, result)
        elif not success and error_callback:
            self.safe_ui_update(f"{task_id}_error", error_callback, result)
        
        # Emit signal
        self.background_task_completed.emit(task_id, success, result)
        
        # Clean up
        if task_id in self.background_tasks:
            del self.background_tasks[task_id]
    
    def cancel_background_task(self, task_id: str) -> bool:
        """Cancel a running background task"""
        if task_id in self.background_tasks:
            worker = self.background_tasks[task_id]
            if worker.isRunning():
                worker.terminate()
                worker.wait(3000)  # Wait up to 3 seconds
                if worker.isRunning():
                    logging.warning(f"Failed to terminate background task {task_id}")
                    return False
            del self.background_tasks[task_id]
            return True
        return False
    
    def wait_for_task(self, task_id: str, timeout_ms: int = 5000) -> tuple:
        """Wait for a background task to complete"""
        if task_id in self.background_tasks:
            worker = self.background_tasks[task_id]
            if worker.wait(timeout_ms):
                return self.task_results.get(task_id, (False, None))
        return (False, "Task timeout or not found")
    
    def cancel_all_background_tasks(self):
        """Cancel all running background tasks"""
        task_ids = list(self.background_tasks.keys())
        cancelled_count = 0
        
        for task_id in task_ids:
            if self.cancel_background_task(task_id):
                cancelled_count += 1
        
        logging.info(f"Cancelled {cancelled_count} background tasks")
        return cancelled_count
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """Get statistics about thread usage"""
        return {
            'active_threads': len(self.active_threads),
            'background_tasks': len(self.background_tasks),
            'ui_update_queue_size': self.ui_update_queue.qsize(),
            'completed_tasks': len(self.task_results),
            'available_locks': list(self.locks.keys()) + list(self.py_locks.keys())
        }
    
    def cleanup_finished_tasks(self):
        """Clean up results from finished tasks"""
        # Keep only recent results (last 100)
        if len(self.task_results) > 100:
            items = list(self.task_results.items())
            items.sort(key=lambda x: x[0])  # Sort by task_id (which often includes timestamp)
            
            # Keep the 50 most recent
            keep_items = items[-50:]
            self.task_results = dict(keep_items)
            
            logging.debug(f"Cleaned up old task results, keeping {len(keep_items)}")


class ThreadSafeCounter:
    """Thread-safe counter with atomic operations"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1) -> int:
        """Atomically increment and return new value"""
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount: int = 1) -> int:
        """Atomically decrement and return new value"""
        with self._lock:
            self._value -= amount
            return self._value
    
    def get(self) -> int:
        """Get current value"""
        with self._lock:
            return self._value
    
    def set(self, value: int) -> int:
        """Set value and return previous value"""
        with self._lock:
            old_value = self._value
            self._value = value
            return old_value
    
    def reset(self) -> int:
        """Reset to zero and return previous value"""
        return self.set(0)


class ThreadSafeDict:
    """Thread-safe dictionary wrapper"""
    
    def __init__(self, initial_data: Dict = None):
        self._data = initial_data or {}
        self._lock = threading.RLock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get value with thread safety"""
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: Any, value: Any):
        """Set value with thread safety"""
        with self._lock:
            self._data[key] = value
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """Pop value with thread safety"""
        with self._lock:
            return self._data.pop(key, default)
    
    def update(self, other: Dict):
        """Update with another dict"""
        with self._lock:
            self._data.update(other)
    
    def keys(self):
        """Get keys (returns a copy)"""
        with self._lock:
            return list(self._data.keys())
    
    def values(self):
        """Get values (returns a copy)"""
        with self._lock:
            return list(self._data.values())
    
    def items(self):
        """Get items (returns a copy)"""
        with self._lock:
            return list(self._data.items())
    
    def __len__(self):
        with self._lock:
            return len(self._data)
    
    def __contains__(self, key):
        with self._lock:
            return key in self._data


# Decorator for thread-safe functions
def thread_safe(lock_name: str = None):
    """Decorator to make functions thread-safe"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_thread_safety_manager()
            lock_to_use = lock_name or 'ui_updates'
            
            with manager.lock_resource(lock_to_use):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Global instance
_thread_safety_manager = None

def get_thread_safety_manager() -> ThreadSafetyManager:
    """Get the global thread safety manager instance"""
    global _thread_safety_manager
    if _thread_safety_manager is None:
        _thread_safety_manager = ThreadSafetyManager()
    return _thread_safety_manager


def safe_call_later(func: Callable, delay_ms: int = 0, *args, **kwargs):
    """Safely call a function on the main thread after a delay"""
    manager = get_thread_safety_manager()
    task_id = f"delayed_call_{time.time()}"
    
    def delayed_func():
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        return func(*args, **kwargs)
    
    return manager.start_background_task(task_id, delayed_func)