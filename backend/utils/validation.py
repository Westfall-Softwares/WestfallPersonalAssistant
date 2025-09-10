#!/usr/bin/env python3
"""
Input Validation Utilities for Westfall Personal Assistant

Provides validation functions for user input across the application.
"""

import re
import os
from datetime import datetime
from typing import Tuple, Optional
from urllib.parse import urlparse


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        return False, "Invalid email format"
    
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address too long"
    
    return True, None


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """Validate password strength requirements."""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, None


def validate_date(date_str: str, format_str: str = "%Y-%m-%d") -> Tuple[bool, Optional[str]]:
    """Validate date string format."""
    if not date_str or not isinstance(date_str, str):
        return False, "Date is required"
    
    try:
        datetime.strptime(date_str.strip(), format_str)
        return True, None
    except ValueError:
        return False, f"Invalid date format. Expected format: {format_str}"


def validate_file_path(file_path: str, must_exist: bool = False, must_be_readable: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate file path."""
    if not file_path or not isinstance(file_path, str):
        return False, "File path is required"
    
    file_path = file_path.strip()
    
    # Check for potentially dangerous paths
    if ".." in file_path or file_path.startswith("/proc") or file_path.startswith("/sys"):
        return False, "Invalid file path"
    
    if must_exist and not os.path.exists(file_path):
        return False, "File does not exist"
    
    if must_be_readable and not os.access(file_path, os.R_OK):
        return False, "File is not readable"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False, "URL is required"
    
    try:
        result = urlparse(url.strip())
        if not result.scheme or not result.netloc:
            return False, "Invalid URL format"
        
        if result.scheme not in ['http', 'https', 'ftp']:
            return False, "URL must use http, https, or ftp protocol"
        
        return True, None
    except Exception:
        return False, "Invalid URL format"


def validate_port(port: str) -> Tuple[bool, Optional[str]]:
    """Validate port number."""
    if not port or not isinstance(port, str):
        return False, "Port is required"
    
    try:
        port_num = int(port.strip())
        if port_num < 1 or port_num > 65535:
            return False, "Port must be between 1 and 65535"
        return True, None
    except ValueError:
        return False, "Port must be a valid number"


def validate_api_key(api_key: str, service: str = "generic") -> Tuple[bool, Optional[str]]:
    """Validate API key format based on service."""
    if not api_key or not isinstance(api_key, str):
        return False, "API key is required"
    
    api_key = api_key.strip()
    
    if len(api_key) < 10:
        return False, "API key appears too short"
    
    if len(api_key) > 512:
        return False, "API key appears too long"
    
    # Service-specific validation
    service_patterns = {
        "openai": r'^sk-[A-Za-z0-9]{48}$',
        "openweathermap": r'^[a-fA-F0-9]{32}$',
        "newsapi": r'^[a-fA-F0-9]{32}$'
    }
    
    if service.lower() in service_patterns:
        pattern = service_patterns[service.lower()]
        if not re.match(pattern, api_key):
            return False, f"Invalid {service} API key format"
    
    return True, None


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required"
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone.strip())
    
    # Check if only digits remain
    if not cleaned.isdigit():
        return False, "Phone number can only contain digits and formatting characters"
    
    # Check length (7-15 digits for international numbers)
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False, "Phone number must be between 7 and 15 digits"
    
    return True, None


def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """Validate IP address format."""
    if not ip or not isinstance(ip, str):
        return False, "IP address is required"
    
    ip = ip.strip()
    
    # IPv4 validation
    ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    ipv4_match = re.match(ipv4_pattern, ip)
    
    if ipv4_match:
        octets = [int(x) for x in ipv4_match.groups()]
        if all(0 <= octet <= 255 for octet in octets):
            return True, None
        else:
            return False, "Invalid IPv4 address - octets must be 0-255"
    
    # Basic IPv6 validation (simplified)
    if ':' in ip:
        parts = ip.split(':')
        if len(parts) <= 8:
            try:
                for part in parts:
                    if part and not (0 <= int(part, 16) <= 0xFFFF):
                        return False, "Invalid IPv6 address format"
                return True, None
            except ValueError:
                return False, "Invalid IPv6 address format"
    
    return False, "Invalid IP address format"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters."""
    if not filename:
        return "untitled"
    
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "untitled"
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_len = 255 - len(ext)
        sanitized = name[:max_name_len] + ext
    
    return sanitized


def validate_json_string(json_str: str) -> Tuple[bool, Optional[str]]:
    """Validate JSON string format."""
    if not json_str or not isinstance(json_str, str):
        return False, "JSON string is required"
    
    try:
        import json
        json.loads(json_str.strip())
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"


def validate_hex_color(color: str) -> Tuple[bool, Optional[str]]:
    """Validate hex color format."""
    if not color or not isinstance(color, str):
        return False, "Color is required"
    
    color = color.strip()
    
    # Add # if missing
    if not color.startswith('#'):
        color = '#' + color
    
    # Check format
    hex_pattern = r'^#[0-9A-Fa-f]{6}$'
    if not re.match(hex_pattern, color):
        return False, "Invalid hex color format (expected #RRGGBB)"
    
    return True, None