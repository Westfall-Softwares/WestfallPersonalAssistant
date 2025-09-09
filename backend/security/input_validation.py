#!/usr/bin/env python3
"""
Input Validation and Sanitization Module for Westfall Personal Assistant

Provides comprehensive input validation, sanitization, and boundary checking
for all user inputs, API responses, and data imports.
"""

import re
import json
import html
import logging
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime, date
import ipaddress
import email.utils

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    def __init__(self):
        # Common regex patterns
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'),
            'filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
            'path': re.compile(r'^[a-zA-Z0-9/\\._-]+$'),
            'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
            'safe_string': re.compile(r'^[a-zA-Z0-9\s._-]+$'),
            'model_name': re.compile(r'^[a-zA-Z0-9._-]+\.(gguf|ggml|bin|safetensors)$'),
            'hex_hash': re.compile(r'^[a-fA-F0-9]{64}$'),  # SHA-256
            'api_key': re.compile(r'^[a-zA-Z0-9._-]+$')
        }
        
        # Dangerous patterns to reject
        self.dangerous_patterns = [
            re.compile(r'<script.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'exec\s*\(', re.IGNORECASE),
            re.compile(r'__import__', re.IGNORECASE),
            re.compile(r'\.\./', re.IGNORECASE),  # Path traversal
            re.compile(r'\\\\', re.IGNORECASE),   # Windows path traversal
        ]
        
        # File extension whitelist
        self.safe_extensions = {
            'models': ['.gguf', '.ggml', '.bin', '.safetensors'],
            'documents': ['.txt', '.md', '.pdf', '.doc', '.docx'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'data': ['.json', '.csv', '.xml', '.yaml', '.yml'],
            'archives': ['.zip', '.tar', '.gz', '.7z']
        }
    
    def sanitize_string(self, value: str, max_length: int = None, 
                       allow_html: bool = False) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(value):
                raise ValidationError("Input contains potentially dangerous content")
        
        # HTML escape if not allowing HTML
        if not allow_html:
            value = html.escape(value)
        
        # URL decode (basic protection against encoded attacks)
        value = urllib.parse.unquote(value)
        
        # Strip whitespace
        value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(f"String exceeds maximum length of {max_length}")
        
        return value
    
    def validate_email(self, email_str: str) -> str:
        """Validate and sanitize email address."""
        email_str = self.sanitize_string(email_str, max_length=254)
        
        if not self.patterns['email'].match(email_str):
            raise ValidationError("Invalid email format")
        
        # Additional validation using email.utils
        try:
            parsed = email.utils.parseaddr(email_str)
            if not parsed[1]:
                raise ValidationError("Invalid email format")
        except Exception:
            raise ValidationError("Invalid email format")
        
        return email_str.lower()
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> str:
        """Validate and sanitize URL."""
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        url = self.sanitize_string(url, max_length=2048)
        
        if not self.patterns['url'].match(url):
            raise ValidationError("Invalid URL format")
        
        # Parse URL for additional validation
        try:
            parsed = urllib.parse.urlparse(url)
            
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {allowed_schemes}")
            
            # Check for suspicious domains
            if parsed.netloc.lower() in ['localhost', '127.0.0.1', '0.0.0.0']:
                raise ValidationError("Local URLs not allowed")
            
            # Validate IP addresses
            try:
                ip = ipaddress.ip_address(parsed.netloc)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    raise ValidationError("Private/local IP addresses not allowed")
            except ValueError:
                pass  # Not an IP address, which is fine
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"URL validation failed: {e}")
        
        return url
    
    def validate_file_path(self, path: str, allow_absolute: bool = False,
                          allowed_extensions: List[str] = None) -> Path:
        """Validate and sanitize file path."""
        path = self.sanitize_string(path, max_length=1024)
        path_obj = Path(path)
        
        # Check for path traversal
        if '..' in path_obj.parts:
            raise ValidationError("Path traversal not allowed")
        
        # Check if absolute path is allowed
        if path_obj.is_absolute() and not allow_absolute:
            raise ValidationError("Absolute paths not allowed")
        
        # Validate extension if specified
        if allowed_extensions:
            if path_obj.suffix.lower() not in allowed_extensions:
                raise ValidationError(f"File extension must be one of: {allowed_extensions}")
        
        return path_obj
    
    def validate_filename(self, filename: str, category: str = None) -> str:
        """Validate filename."""
        filename = self.sanitize_string(filename, max_length=255)
        
        if not self.patterns['filename'].match(filename):
            raise ValidationError("Invalid filename format")
        
        # Check extension if category is specified
        if category and category in self.safe_extensions:
            path_obj = Path(filename)
            if path_obj.suffix.lower() not in self.safe_extensions[category]:
                raise ValidationError(f"Invalid file extension for category {category}")
        
        return filename
    
    def validate_integer(self, value: Any, min_val: int = None, 
                        max_val: int = None) -> int:
        """Validate integer input."""
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                raise ValidationError(f"Expected integer, got {type(value)}")
        except ValueError:
            raise ValidationError("Invalid integer format")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        
        return value
    
    def validate_float(self, value: Any, min_val: float = None, 
                      max_val: float = None) -> float:
        """Validate float input."""
        try:
            if isinstance(value, str):
                value = float(value)
            elif not isinstance(value, (int, float)):
                raise ValidationError(f"Expected number, got {type(value)}")
            value = float(value)
        except ValueError:
            raise ValidationError("Invalid number format")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        
        return value
    
    def validate_json(self, json_str: str, max_size: int = None) -> Dict:
        """Validate and parse JSON."""
        json_str = self.sanitize_string(json_str, allow_html=False)
        
        if max_size and len(json_str) > max_size:
            raise ValidationError(f"JSON exceeds maximum size of {max_size}")
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {e}")
        
        return data
    
    def validate_api_key(self, api_key: str) -> str:
        """Validate API key format."""
        api_key = self.sanitize_string(api_key, max_length=512)
        
        if not self.patterns['api_key'].match(api_key):
            raise ValidationError("Invalid API key format")
        
        if len(api_key) < 16:
            raise ValidationError("API key too short")
        
        return api_key
    
    def validate_checksum(self, checksum: str) -> str:
        """Validate SHA-256 checksum."""
        checksum = self.sanitize_string(checksum, max_length=64)
        
        if not self.patterns['hex_hash'].match(checksum):
            raise ValidationError("Invalid SHA-256 checksum format")
        
        return checksum.lower()
    
    def validate_model_name(self, model_name: str) -> str:
        """Validate AI model filename."""
        model_name = self.sanitize_string(model_name, max_length=255)
        
        if not self.patterns['model_name'].match(model_name):
            raise ValidationError("Invalid model filename format")
        
        return model_name
    
    def validate_date(self, date_str: str, date_format: str = "%Y-%m-%d") -> date:
        """Validate date string."""
        date_str = self.sanitize_string(date_str, max_length=50)
        
        try:
            parsed_date = datetime.strptime(date_str, date_format).date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")
        
        return parsed_date
    
    def contains_suspicious_patterns(self, value: str) -> bool:
        """Check if input contains suspicious patterns."""
        if not isinstance(value, str):
            return False
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(value):
                return True
        
        # Additional suspicious patterns for AI input
        suspicious_ai_patterns = [
            re.compile(r'ignore\s+previous\s+instructions', re.IGNORECASE),
            re.compile(r'ignore\s+all\s+previous', re.IGNORECASE),
            re.compile(r'pretend\s+you\s+are', re.IGNORECASE),
            re.compile(r'system\s+prompt', re.IGNORECASE),
            re.compile(r'role\s*:\s*system', re.IGNORECASE),
            re.compile(r'</system>', re.IGNORECASE),
            re.compile(r'\\n\\n###', re.IGNORECASE),
        ]
        
        for pattern in suspicious_ai_patterns:
            if pattern.search(value):
                return True
        
        return False
    
    def is_safe_string(self, value: str) -> bool:
        """Check if string contains only safe characters."""
        if not isinstance(value, str):
            return False
        
        return bool(self.patterns['safe_string'].match(value))
    
    def validate_config_data(self, config: Dict) -> Dict:
        """Validate configuration data structure."""
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")
        
        validated_config = {}
        
        for key, value in config.items():
            # Validate key
            if not isinstance(key, str):
                raise ValidationError("Configuration keys must be strings")
            
            key = self.sanitize_string(key, max_length=100)
            
            if not self.patterns['safe_string'].match(key):
                raise ValidationError(f"Invalid configuration key: {key}")
            
            # Validate value based on type
            if isinstance(value, str):
                value = self.sanitize_string(value, max_length=1000)
            elif isinstance(value, (int, float)):
                # Numbers are generally safe
                pass
            elif isinstance(value, bool):
                # Booleans are safe
                pass
            elif isinstance(value, list):
                # Validate list items
                value = [self.sanitize_string(str(item), max_length=500) 
                        for item in value if item is not None]
            elif isinstance(value, dict):
                # Recursively validate nested dictionaries
                value = self.validate_config_data(value)
            elif value is None:
                # None values are allowed
                pass
            else:
                raise ValidationError(f"Unsupported configuration value type: {type(value)}")
            
            validated_config[key] = value
        
        return validated_config
    
    def validate_import_data(self, data: Dict, expected_schema: Dict) -> Dict:
        """Validate imported data against expected schema."""
        if not isinstance(data, dict):
            raise ValidationError("Import data must be a dictionary")
        
        validated_data = {}
        
        for field, constraints in expected_schema.items():
            value = data.get(field)
            
            # Check required fields
            if constraints.get('required', False) and value is None:
                raise ValidationError(f"Required field missing: {field}")
            
            if value is None:
                validated_data[field] = None
                continue
            
            # Validate based on type constraint
            field_type = constraints.get('type', str)
            validator = constraints.get('validator')
            
            try:
                if field_type == str:
                    value = self.sanitize_string(
                        str(value), 
                        max_length=constraints.get('max_length', 1000)
                    )
                elif field_type == int:
                    value = self.validate_integer(
                        value,
                        min_val=constraints.get('min_val'),
                        max_val=constraints.get('max_val')
                    )
                elif field_type == float:
                    value = self.validate_float(
                        value,
                        min_val=constraints.get('min_val'),
                        max_val=constraints.get('max_val')
                    )
                elif field_type == bool:
                    value = bool(value)
                elif field_type == date:
                    if isinstance(value, str):
                        value = self.validate_date(value)
                
                # Apply custom validator if provided
                if validator and callable(validator):
                    value = validator(value)
                
                validated_data[field] = value
                
            except Exception as e:
                raise ValidationError(f"Validation failed for field {field}: {e}")
        
        return validated_data


class BoundaryValidator:
    """Validates numerical boundaries and limits."""
    
    @staticmethod
    def validate_memory_limit(memory_mb: int) -> int:
        """Validate memory limit in MB."""
        if not isinstance(memory_mb, int):
            raise ValidationError("Memory limit must be an integer")
        
        if memory_mb < 128:
            raise ValidationError("Memory limit too low (minimum 128MB)")
        
        if memory_mb > 32768:  # 32GB
            raise ValidationError("Memory limit too high (maximum 32GB)")
        
        return memory_mb
    
    @staticmethod
    def validate_file_size(size_bytes: int, max_size_mb: int = 1024) -> int:
        """Validate file size."""
        if not isinstance(size_bytes, int):
            raise ValidationError("File size must be an integer")
        
        if size_bytes < 0:
            raise ValidationError("File size cannot be negative")
        
        max_bytes = max_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValidationError(f"File too large (maximum {max_size_mb}MB)")
        
        return size_bytes
    
    @staticmethod
    def validate_timeout(seconds: Union[int, float]) -> Union[int, float]:
        """Validate timeout value."""
        if not isinstance(seconds, (int, float)):
            raise ValidationError("Timeout must be a number")
        
        if seconds <= 0:
            raise ValidationError("Timeout must be positive")
        
        if seconds > 3600:  # 1 hour
            raise ValidationError("Timeout too long (maximum 1 hour)")
        
        return seconds
    
    @staticmethod
    def validate_port(port: int) -> int:
        """Validate network port number."""
        if not isinstance(port, int):
            raise ValidationError("Port must be an integer")
        
        if port < 1 or port > 65535:
            raise ValidationError("Port must be between 1 and 65535")
        
        # Check for reserved ports
        if port < 1024:
            logger.warning(f"Using reserved port {port}")
        
        return port


# Global validator instance
input_validator = InputValidator()
boundary_validator = BoundaryValidator()


def validate_and_sanitize(validator_func: Callable, *args, **kwargs):
    """Decorator for automatic validation and sanitization."""
    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            try:
                # Apply validation
                validated_args = []
                for i, arg in enumerate(func_args):
                    if i < len(args):
                        validated_args.append(validator_func(arg, *args[i:], **kwargs))
                    else:
                        validated_args.append(arg)
                
                return func(*validated_args, **func_kwargs)
            except ValidationError as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator