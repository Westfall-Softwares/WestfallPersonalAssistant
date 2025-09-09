"""
Utils module for Westfall Personal Assistant
Shared utilities and helper functions
"""

__version__ = "1.0.0"
__author__ = "Westfall Software"

# Import utilities for easy access
from .logger import setup_logging, get_logger
from .file_handler import (
    ensure_directory, safe_read_file, safe_write_file, 
    safe_read_json, safe_write_json, get_file_size, get_file_hash
)
from .validators import validate_email, validate_url, validate_api_key
from .date_utils import (
    get_current_timestamp, parse_date_string, format_relative_time,
    get_week_range, get_month_range, is_business_day, add_business_days,
    format_duration
)
from .text_utils import (
    clean_text, truncate_text, extract_keywords, highlight_text,
    camel_to_snake, snake_to_camel, extract_urls, extract_emails,
    format_file_size, pluralize, mask_sensitive_data
)

__all__ = [
    'setup_logging',
    'get_logger', 
    # File handler functions
    'ensure_directory',
    'safe_read_file',
    'safe_write_file',
    'safe_read_json',
    'safe_write_json',
    'get_file_size',
    'get_file_hash',
    # Validators
    'validate_email',
    'validate_url',
    'validate_api_key',
    # Date utilities
    'get_current_timestamp',
    'parse_date_string',
    'format_relative_time',
    'get_week_range',
    'get_month_range',
    'is_business_day',
    'add_business_days',
    'format_duration',
    # Text utilities
    'clean_text',
    'truncate_text',
    'extract_keywords',
    'highlight_text',
    'camel_to_snake',
    'snake_to_camel',
    'extract_urls',
    'extract_emails',
    'format_file_size',
    'pluralize',
    'mask_sensitive_data'
]