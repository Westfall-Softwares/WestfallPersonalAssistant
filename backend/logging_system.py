#!/usr/bin/env python3
"""
Enhanced Logging System for Westfall Personal Assistant

Provides structured logging with levels, rotation, centralized viewing,
and crash reporting with privacy controls.
"""

import logging
import logging.handlers
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import threading
import queue
import weakref
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Enhanced log levels."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    TRACE = 5


class LogCategory(Enum):
    """Log categories for better organization."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"
    SYSTEM = "system"
    AI_MODEL = "ai_model"
    DATABASE = "database"
    NETWORK = "network"
    ERROR = "error"
    AUDIT = "audit"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    category: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'category': self.category,
            'message': self.message,
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'thread_id': self.thread_id,
            'process_id': self.process_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'context': self.context,
            'stack_trace': self.stack_trace
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class PrivacyFilter:
    """Filters sensitive information from log messages."""
    
    def __init__(self):
        self.sensitive_patterns = [
            # Common patterns for sensitive data
            r'password["\s]*[:=]["\s]*[^\s"]+',
            r'api[_-]?key["\s]*[:=]["\s]*[^\s"]+',
            r'token["\s]*[:=]["\s]*[^\s"]+',
            r'secret["\s]*[:=]["\s]*[^\s"]+',
            r'auth["\s]*[:=]["\s]*[^\s"]+',
            # Email patterns
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Credit card patterns
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            # Social security numbers
            r'\b\d{3}-\d{2}-\d{4}\b',
        ]
        
        self.compiled_patterns = [
            __import__('re').compile(pattern, __import__('re').IGNORECASE)
            for pattern in self.sensitive_patterns
        ]
    
    def filter_message(self, message: str) -> str:
        """Filter sensitive information from message."""
        import re
        
        filtered_message = message
        
        for pattern in self.compiled_patterns:
            filtered_message = pattern.sub('[REDACTED]', filtered_message)
        
        return filtered_message
    
    def filter_context(self, context: Dict) -> Dict:
        """Filter sensitive information from context dictionary."""
        if not context:
            return context
        
        filtered_context = {}
        sensitive_keys = {
            'password', 'api_key', 'token', 'secret', 'auth', 'key',
            'credential', 'private_key', 'cert', 'certificate'
        }
        
        for key, value in context.items():
            if any(sensitive_word in key.lower() for sensitive_word in sensitive_keys):
                filtered_context[key] = '[REDACTED]'
            elif isinstance(value, str):
                filtered_context[key] = self.filter_message(value)
            elif isinstance(value, dict):
                filtered_context[key] = self.filter_context(value)
            else:
                filtered_context[key] = value
        
        return filtered_context


class CrashReporter:
    """Handles crash reporting with privacy controls."""
    
    def __init__(self, crash_dir: str, privacy_enabled: bool = True):
        self.crash_dir = Path(crash_dir)
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        self.privacy_enabled = privacy_enabled
        self.privacy_filter = PrivacyFilter()
    
    def report_crash(self, exc_type, exc_value, exc_traceback, context: Dict = None):
        """Report a crash with optional privacy filtering."""
        try:
            crash_id = f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
            crash_file = self.crash_dir / f"{crash_id}.json"
            
            # Get stack trace
            stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Apply privacy filtering if enabled
            if self.privacy_enabled:
                stack_trace = self.privacy_filter.filter_message(stack_trace)
                if context:
                    context = self.privacy_filter.filter_context(context)
            
            crash_data = {
                'crash_id': crash_id,
                'timestamp': datetime.now().isoformat(),
                'exception_type': str(exc_type.__name__),
                'exception_message': str(exc_value),
                'stack_trace': stack_trace,
                'context': context or {},
                'system_info': {
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'process_id': os.getpid(),
                    'thread_id': threading.get_ident()
                }
            }
            
            with open(crash_file, 'w') as f:
                json.dump(crash_data, f, indent=2, default=str)
            
            return crash_id
            
        except Exception as e:
            # Fallback logging to prevent crash reporting from crashing
            print(f"Failed to report crash: {e}", file=sys.stderr)
            return None


class LogViewer:
    """Centralized log viewer for browsing and searching logs."""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
    
    def get_recent_logs(self, limit: int = 100, level_filter: str = None,
                       category_filter: str = None) -> List[Dict]:
        """Get recent log entries with optional filtering."""
        logs = []
        
        try:
            if not self.log_file.exists():
                return logs
            
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Process lines in reverse order (most recent first)
            for line in reversed(lines[-limit * 2:]):  # Read more than limit to account for filtering
                try:
                    log_entry = json.loads(line.strip())
                    
                    # Apply filters
                    if level_filter and log_entry.get('level') != level_filter:
                        continue
                    
                    if category_filter and log_entry.get('category') != category_filter:
                        continue
                    
                    logs.append(log_entry)
                    
                    if len(logs) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
            
            return logs
            
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []
    
    def search_logs(self, query: str, limit: int = 100, 
                   start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Search logs by message content and time range."""
        matching_logs = []
        
        try:
            if not self.log_file.exists():
                return matching_logs
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Check time range
                        log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                        
                        # Check message content
                        message = log_entry.get('message', '').lower()
                        if query.lower() in message:
                            matching_logs.append(log_entry)
                            
                            if len(matching_logs) >= limit:
                                break
                                
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            return matching_logs
            
        except Exception as e:
            print(f"Error searching logs: {e}")
            return []
    
    def get_log_stats(self) -> Dict:
        """Get statistics about the log file."""
        stats = {
            'total_lines': 0,
            'levels': {},
            'categories': {},
            'file_size': 0,
            'date_range': None
        }
        
        try:
            if not self.log_file.exists():
                return stats
            
            stats['file_size'] = self.log_file.stat().st_size
            earliest_time = None
            latest_time = None
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    stats['total_lines'] += 1
                    
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Count levels
                        level = log_entry.get('level', 'UNKNOWN')
                        stats['levels'][level] = stats['levels'].get(level, 0) + 1
                        
                        # Count categories
                        category = log_entry.get('category', 'UNKNOWN')
                        stats['categories'][category] = stats['categories'].get(category, 0) + 1
                        
                        # Track time range
                        timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        if earliest_time is None or timestamp < earliest_time:
                            earliest_time = timestamp
                        if latest_time is None or timestamp > latest_time:
                            latest_time = timestamp
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            if earliest_time and latest_time:
                stats['date_range'] = {
                    'earliest': earliest_time.isoformat(),
                    'latest': latest_time.isoformat()
                }
            
            return stats
            
        except Exception as e:
            print(f"Error getting log stats: {e}")
            return stats


class EnhancedLogHandler(logging.Handler):
    """Custom log handler with structured logging and privacy filtering."""
    
    def __init__(self, log_file: str, privacy_enabled: bool = True):
        super().__init__()
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.privacy_enabled = privacy_enabled
        self.privacy_filter = PrivacyFilter()
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.log_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.log_thread.start()
        
        # Observers for real-time log viewing
        self.observers = []
    
    def emit(self, record):
        """Emit a log record."""
        try:
            # Create structured log entry
            log_entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                category=getattr(record, 'category', LogCategory.SYSTEM.value),
                message=record.getMessage(),
                module=record.module,
                function=record.funcName,
                line_number=record.lineno,
                thread_id=str(threading.get_ident()),
                process_id=os.getpid(),
                user_id=getattr(record, 'user_id', None),
                session_id=getattr(record, 'session_id', None),
                context=getattr(record, 'context', None),
                stack_trace=self.format(record) if record.exc_info else None
            )
            
            # Apply privacy filtering
            if self.privacy_enabled:
                log_entry.message = self.privacy_filter.filter_message(log_entry.message)
                if log_entry.context:
                    log_entry.context = self.privacy_filter.filter_context(log_entry.context)
                if log_entry.stack_trace:
                    log_entry.stack_trace = self.privacy_filter.filter_message(log_entry.stack_trace)
            
            # Queue for background writing
            self.log_queue.put(log_entry)
            
            # Notify observers
            self._notify_observers(log_entry)
            
        except Exception:
            self.handleError(record)
    
    def _log_worker(self):
        """Background worker for writing logs to file."""
        while not self.stop_event.is_set():
            try:
                log_entry = self.log_queue.get(timeout=1.0)
                
                with open(self.log_file, 'a') as f:
                    f.write(log_entry.to_json() + '\n')
                
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing log: {e}", file=sys.stderr)
    
    def add_observer(self, observer):
        """Add a log observer for real-time viewing."""
        self.observers.append(weakref.ref(observer))
    
    def _notify_observers(self, log_entry: LogEntry):
        """Notify observers of new log entries."""
        # Clean up dead references
        self.observers = [ref for ref in self.observers if ref() is not None]
        
        for observer_ref in self.observers:
            observer = observer_ref()
            if observer and hasattr(observer, 'on_log_entry'):
                try:
                    observer.on_log_entry(log_entry)
                except Exception:
                    pass  # Don't let observer errors break logging
    
    def close(self):
        """Close the handler and stop background thread."""
        self.stop_event.set()
        if self.log_thread.is_alive():
            self.log_thread.join(timeout=5.0)
        super().close()


class LoggerManager:
    """Manages the enhanced logging system."""
    
    def __init__(self, log_dir: str, app_name: str = "WestfallAssistant"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.app_name = app_name
        self.privacy_enabled = True
        
        # Log files
        self.main_log_file = self.log_dir / f"{app_name.lower()}.jsonl"
        self.error_log_file = self.log_dir / f"{app_name.lower()}_errors.jsonl"
        self.audit_log_file = self.log_dir / f"{app_name.lower()}_audit.jsonl"
        self.crash_dir = self.log_dir / "crashes"
        
        # Initialize components
        self.crash_reporter = CrashReporter(self.crash_dir, self.privacy_enabled)
        self.log_viewer = LogViewer(self.main_log_file)
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up the enhanced logging system."""
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add enhanced handler
        self.enhanced_handler = EnhancedLogHandler(self.main_log_file, self.privacy_enabled)
        self.enhanced_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(self.enhanced_handler)
        
        # Add rotating file handler for errors
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # Set up crash reporting
        sys.excepthook = self._handle_exception
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for crash reporting."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Report crash
        crash_id = self.crash_reporter.report_crash(
            exc_type, exc_value, exc_traceback,
            context={'app_name': self.app_name}
        )
        
        # Log the crash
        logger = logging.getLogger(__name__)
        logger.critical(
            f"Unhandled exception occurred - Crash ID: {crash_id}",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={'category': LogCategory.ERROR.value}
        )
        
        # Call original exception hook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def get_logger(self, name: str, category: LogCategory = LogCategory.SYSTEM) -> logging.Logger:
        """Get a logger with category metadata."""
        logger = logging.getLogger(name)
        
        # Add category filter
        class CategoryFilter(logging.Filter):
            def filter(self, record):
                if not hasattr(record, 'category'):
                    record.category = category.value
                return True
        
        logger.addFilter(CategoryFilter())
        return logger
    
    def log_user_action(self, action: str, user_id: str = None, context: Dict = None):
        """Log a user action for audit trail."""
        logger = self.get_logger('user_actions', LogCategory.USER_ACTION)
        logger.info(
            f"User action: {action}",
            extra={
                'user_id': user_id,
                'context': context,
                'category': LogCategory.USER_ACTION.value
            }
        )
    
    def log_security_event(self, event: str, severity: str = "INFO", context: Dict = None):
        """Log a security-related event."""
        logger = self.get_logger('security', LogCategory.SECURITY)
        level = getattr(logging, severity.upper(), logging.INFO)
        logger.log(
            level,
            f"Security event: {event}",
            extra={
                'context': context,
                'category': LogCategory.SECURITY.value
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = None, 
                              context: Dict = None):
        """Log a performance metric."""
        logger = self.get_logger('performance', LogCategory.PERFORMANCE)
        logger.info(
            f"Performance metric - {metric_name}: {value} {unit or ''}",
            extra={
                'context': {
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    **(context or {})
                },
                'category': LogCategory.PERFORMANCE.value
            }
        )
    
    def enable_privacy_mode(self, enabled: bool = True):
        """Enable or disable privacy filtering."""
        self.privacy_enabled = enabled
        if hasattr(self, 'enhanced_handler'):
            self.enhanced_handler.privacy_enabled = enabled
        self.crash_reporter.privacy_enabled = enabled
    
    def get_log_viewer(self) -> LogViewer:
        """Get the log viewer instance."""
        return self.log_viewer
    
    def get_log_stats(self) -> Dict:
        """Get logging statistics."""
        stats = {
            'main_log': self.log_viewer.get_log_stats(),
            'log_files': {
                'main': str(self.main_log_file),
                'errors': str(self.error_log_file),
                'audit': str(self.audit_log_file)
            },
            'privacy_enabled': self.privacy_enabled,
            'crash_reports': len(list(self.crash_dir.glob("*.json"))) if self.crash_dir.exists() else 0
        }
        return stats


# Global logger manager
logger_manager = None


def initialize_logging(log_dir: str, app_name: str = "WestfallAssistant") -> LoggerManager:
    """Initialize the enhanced logging system."""
    global logger_manager
    logger_manager = LoggerManager(log_dir, app_name)
    return logger_manager


def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> logging.Logger:
    """Get a logger with enhanced features."""
    if logger_manager:
        return logger_manager.get_logger(name, category)
    else:
        return logging.getLogger(name)