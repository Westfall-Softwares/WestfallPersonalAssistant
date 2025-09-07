#!/usr/bin/env python3
"""
Global Error Handler for Westfall Personal Assistant

Provides centralized exception handling, logging, and crash recovery.
"""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
import json


class ErrorHandler:
    """Centralized error handling and logging system."""
    
    def __init__(self, config_dir: str = None, debug_mode: bool = False):
        self.config_dir = config_dir or os.path.expanduser("~/.westfall_assistant")
        self.debug_mode = debug_mode
        self.log_dir = os.path.join(self.config_dir, "logs")
        self.crash_dir = os.path.join(self.config_dir, "crashes")
        
        # Ensure directories exist
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.crash_dir, exist_ok=True)
        
        # Set up logging
        self._setup_logging()
        
        # Error statistics
        self.error_count = 0
        self.last_errors = []
        self.max_stored_errors = 100
        
    def _setup_logging(self):
        """Set up logging configuration."""
        log_file = os.path.join(self.log_dir, f"westfall_assistant_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Error handler initialized - Debug mode: {self.debug_mode}")
    
    def get_user_friendly_message(self, exc_type, exc_value) -> str:
        """Get user-friendly error message."""
        error_messages = {
            "ConnectionError": "Unable to connect to the service. Please check your internet connection.",
            "FileNotFoundError": "A required file was not found. Please check your installation.",
            "PermissionError": "Permission denied. Please check file permissions or run as administrator.",
            "ValueError": "Invalid input provided. Please check your data and try again.",
            "KeyError": "Configuration error. Please check your settings.",
            "ImportError": "A required component is missing. Please reinstall the application.",
            "TimeoutError": "Operation timed out. Please try again.",
            "MemoryError": "Out of memory. Please close other applications and try again.",
        }
        
        exc_name = exc_type.__name__
        user_message = error_messages.get(exc_name, f"An unexpected error occurred: {exc_name}")
        
        if self.debug_mode:
            user_message += f"\n\nDebug info: {str(exc_value)}"
        
        return user_message
    
    def log_error(self, message: str, exc_info: bool = True, context: str = "Application"):
        """Log an error with optional exception info."""
        self.logger.error(f"[{context}] {message}", exc_info=exc_info)
        self.error_count += 1
    
    def log_warning(self, message: str, context: str = "Application"):
        """Log a warning message."""
        self.logger.warning(f"[{context}] {message}")
    
    def log_info(self, message: str, context: str = "Application"):
        """Log an info message."""
        self.logger.info(f"[{context}] {message}")
    
    def log_debug(self, message: str, context: str = "Application"):
        """Log a debug message."""
        self.logger.debug(f"[{context}] {message}")
    
    def handle_api_error(self, error: Exception, endpoint: str = "unknown") -> Dict[str, Any]:
        """Handle API-specific errors and return standardized response."""
        error_response = {
            "success": False,
            "error_type": type(error).__name__,
            "message": self.get_user_friendly_message(type(error), error),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.debug_mode:
            error_response["debug_info"] = {
                "exception_message": str(error),
                "traceback": traceback.format_exc()
            }
        
        self.log_error(f"API error in {endpoint}: {error}", exc_info=True, context=f"API:{endpoint}")
        
        return error_response
    
    def with_error_handling(self, context: str = "Unknown"):
        """Decorator to add error handling to functions."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(f"Error in {func.__name__}: {e}", exc_info=True, context=context)
                    if hasattr(e, 'status_code'):
                        # Re-raise HTTP exceptions
                        raise
                    return self.handle_api_error(e, func.__name__)
            return wrapper
        return decorator


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def setup_global_error_handling(config_dir: str = None, debug_mode: bool = False) -> ErrorHandler:
    """Set up global error handling."""
    global _global_error_handler
    
    _global_error_handler = ErrorHandler(config_dir, debug_mode)
    
    # Log startup
    _global_error_handler.log_info("Global error handling initialized", "ErrorHandler")
    
    return _global_error_handler


def get_global_error_handler() -> Optional[ErrorHandler]:
    """Get the global error handler instance."""
    return _global_error_handler