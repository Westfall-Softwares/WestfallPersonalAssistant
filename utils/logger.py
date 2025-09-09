"""
Logging Utilities for Westfall Personal Assistant

Consolidated logging functionality with proper configuration management.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from config.settings import get_settings


def setup_logging(log_level: str = None, log_file: str = None) -> logging.Logger:
    """Setup application logging with proper configuration"""
    settings = get_settings()
    
    # Use settings if parameters not provided
    if log_level is None:
        log_level = settings.logging.log_level.value
    if log_file is None and settings.logging.log_to_file:
        log_file = settings.logging.log_file
    
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if log_file:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_log_size_mb * 1024 * 1024,
                backupCount=settings.logging.backup_count
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")
    
    # Get application logger
    app_logger = logging.getLogger('westfall_assistant')
    app_logger.info("Logging system initialized")
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(f'westfall_assistant.{name}')


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs"""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'key', 'secret', 'api_key',
        'auth', 'credential', 'private'
    ]
    
    def filter(self, record):
        # Don't log if user input logging is disabled and it's a user message
        settings = get_settings()
        if not settings.logging.log_user_inputs and hasattr(record, 'user_input'):
            return False
        
        # Filter sensitive data from message
        message = str(record.getMessage()).lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = "[FILTERED - SENSITIVE DATA]"
                record.args = ()
                break
        
        return True


def add_sensitive_filter():
    """Add sensitive data filter to all loggers"""
    filter_instance = SensitiveDataFilter()
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(filter_instance)