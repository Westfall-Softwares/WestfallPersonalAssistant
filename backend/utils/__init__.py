"""
Utility modules for Westfall Assistant - Entrepreneur Edition

This package provides common utilities for error handling, validation, and other shared functionality.
"""

from .error_handler import ErrorHandler, setup_global_error_handling, get_global_error_handler
from .validation import (
    validate_email, validate_password_strength, validate_date, validate_file_path,
    validate_url, validate_port, validate_api_key, validate_phone_number,
    validate_ip_address, sanitize_filename, validate_json_string, validate_hex_color
)
from .safe_delete import SafeDeleteManager, get_safe_delete_manager, safe_delete, recover_item
from .network import (
    NetworkManager, NetworkError, get_network_manager, 
    with_network_retry, safe_request_get, safe_request_post
)

__all__ = [
    'ErrorHandler', 
    'setup_global_error_handling',
    'get_global_error_handler',
    'validate_email',
    'validate_password_strength', 
    'validate_date',
    'validate_file_path',
    'validate_url',
    'validate_port',
    'validate_api_key',
    'validate_phone_number',
    'validate_ip_address',
    'sanitize_filename',
    'validate_json_string',
    'validate_hex_color',
    'SafeDeleteManager',
    'get_safe_delete_manager',
    'safe_delete',
    'recover_item',
    'NetworkManager',
    'NetworkError',
    'get_network_manager',
    'with_network_retry',
    'safe_request_get',
    'safe_request_post'
]