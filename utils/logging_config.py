"""
Logging Configuration for Westfall Personal Assistant

This module provides centralized logging configuration and setup.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_string: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum log file size in bytes before rotation
        backup_count: Number of backup files to keep
        format_string: Custom log format string (optional)
        enable_console: Whether to enable console logging
        
    Returns:
        Configured logger instance
    """
    
    # Default format string
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Add console handler if enabled
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, log to console
            root_logger.error(f"Failed to setup file logging: {e}")
    
    # Create application logger
    app_logger = logging.getLogger("westfall_assistant")
    app_logger.info("Logging configuration initialized")
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> bool:
    """
    Set the logging level for all handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        True if level was set successfully, False otherwise
    """
    try:
        numeric_level = getattr(logging, level.upper(), None)
        if numeric_level is None:
            return False
            
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Update all handlers
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)
            
        return True
    except Exception:
        return False


def add_file_handler(
    log_file: str,
    level: str = "INFO",
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> bool:
    """
    Add a file handler to the root logger.
    
    Args:
        log_file: Path to log file
        level: Logging level for this handler
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        True if handler was added successfully, False otherwise
    """
    try:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # Set level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        file_handler.setLevel(numeric_level)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        return True
    except Exception:
        return False


def configure_third_party_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    
    # Common third-party loggers that can be noisy
    third_party_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'transformers',
        'torch',
        'httpx',
        'asyncio'
    ]
    
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)


def get_logging_config() -> Dict[str, Any]:
    """
    Get current logging configuration.
    
    Returns:
        Dictionary with current logging configuration
    """
    root_logger = logging.getLogger()
    
    config = {
        "level": logging.getLevelName(root_logger.level),
        "handlers": []
    }
    
    for handler in root_logger.handlers:
        handler_info = {
            "type": handler.__class__.__name__,
            "level": logging.getLevelName(handler.level),
            "formatter": str(handler.formatter._fmt) if handler.formatter else None
        }
        
        if hasattr(handler, 'baseFilename'):
            handler_info["file"] = handler.baseFilename
            
        config["handlers"].append(handler_info)
    
    return config


def setup_default_logging() -> logging.Logger:
    """
    Setup default logging configuration for the application.
    
    Returns:
        Configured logger instance
    """
    # Default configuration
    log_dir = Path.home() / ".westfall_assistant" / "logs"
    log_file = log_dir / "assistant.log"
    
    return setup_logging(
        level="INFO",
        log_file=str(log_file),
        enable_console=True
    )