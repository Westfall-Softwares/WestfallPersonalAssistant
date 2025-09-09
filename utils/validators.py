"""
Input Validation Utilities for Westfall Personal Assistant

Provides validation functions for user inputs, API parameters, and security.
"""

import re
import os
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_file_path(file_path: str, must_exist: bool = False, allowed_extensions: List[str] = None) -> bool:
    """Validate file path"""
    if not file_path or not isinstance(file_path, str):
        return False
    
    try:
        path = Path(file_path)
        
        # Check if file must exist
        if must_exist and not path.exists():
            return False
        
        # Check allowed extensions
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                return False
        
        # Basic security check - no path traversal
        resolved_path = path.resolve()
        if '..' in str(resolved_path):
            return False
        
        return True
        
    except Exception:
        return False


def validate_api_key(api_key: str, min_length: int = 10) -> bool:
    """Validate API key format"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic validation - length and no spaces
    if len(api_key) < min_length:
        return False
    
    if ' ' in api_key:
        return False
    
    return True


def validate_model_name(model_name: str) -> bool:
    """Validate AI model name"""
    if not model_name or not isinstance(model_name, str):
        return False
    
    # Allow alphanumeric, hyphens, underscores, colons, and periods
    pattern = r'^[a-zA-Z0-9\-_:.]+$'
    return bool(re.match(pattern, model_name))


def validate_conversation_id(conv_id: str) -> bool:
    """Validate conversation ID format"""
    if not conv_id or not isinstance(conv_id, str):
        return False
    
    # Should be alphanumeric with underscores and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, conv_id))


def sanitize_input(text: str, max_length: int = 10000, allow_html: bool = False) -> str:
    """Sanitize user input text"""
    if not text or not isinstance(text, str):
        return ""
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove HTML if not allowed
    if not allow_html:
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', text)
    
    # Remove null bytes and other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text


def validate_json_input(data: Any, required_fields: List[str] = None, max_depth: int = 10) -> bool:
    """Validate JSON input data"""
    try:
        # Check depth to prevent deeply nested attacks
        def check_depth(obj, depth=0):
            if depth > max_depth:
                return False
            if isinstance(obj, dict):
                return all(check_depth(v, depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return all(check_depth(item, depth + 1) for item in obj)
            return True
        
        if not check_depth(data):
            return False
        
        # Check required fields if specified
        if required_fields and isinstance(data, dict):
            for field in required_fields:
                if field not in data:
                    return False
        
        return True
        
    except Exception:
        return False


def validate_settings_data(settings_dict: Dict[str, Any]) -> List[str]:
    """Validate settings configuration data"""
    errors = []
    
    # Validate UI settings
    if 'ui' in settings_dict:
        ui_settings = settings_dict['ui']
        
        if 'window_width' in ui_settings:
            width = ui_settings['window_width']
            if not isinstance(width, int) or width < 200 or width > 10000:
                errors.append("Invalid window width")
        
        if 'window_height' in ui_settings:
            height = ui_settings['window_height']
            if not isinstance(height, int) or height < 200 or height > 10000:
                errors.append("Invalid window height")
    
    # Validate model settings
    if 'models' in settings_dict:
        model_settings = settings_dict['models']
        
        if 'temperature' in model_settings:
            temp = model_settings['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("Invalid temperature value")
        
        if 'max_tokens' in model_settings:
            tokens = model_settings['max_tokens']
            if not isinstance(tokens, int) or tokens < 1 or tokens > 100000:
                errors.append("Invalid max_tokens value")
    
    return errors


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no path traversal, etc.)"""
    if not filename or not isinstance(filename, str):
        return False
    
    # Check for dangerous patterns
    dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if filename.upper() in reserved_names:
        return False
    
    return True


def validate_port_number(port: Union[str, int]) -> bool:
    """Validate network port number"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_host_address(host: str) -> bool:
    """Validate host address (IP or hostname)"""
    if not host or not isinstance(host, str):
        return False
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, host):
        # Validate IP ranges
        parts = host.split('.')
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    # Hostname pattern
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(hostname_pattern, host))


class InputValidator:
    """Class-based input validator with configurable rules"""
    
    def __init__(self):
        self.rules = {}
    
    def add_rule(self, field_name: str, validator_func, error_message: str):
        """Add a validation rule"""
        self.rules[field_name] = (validator_func, error_message)
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against all rules"""
        errors = []
        
        for field_name, (validator_func, error_message) in self.rules.items():
            if field_name in data:
                value = data[field_name]
                try:
                    if not validator_func(value):
                        errors.append(f"{field_name}: {error_message}")
                except Exception as e:
                    errors.append(f"{field_name}: Validation error - {e}")
        
        return errors