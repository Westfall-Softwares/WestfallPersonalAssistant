#!/usr/bin/env python3
"""
Network Error Handling Utilities for Westfall Personal Assistant

Provides robust network operations with retry logic, exponential backoff, and graceful degradation.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable, Union
from functools import wraps
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Custom exception for network-related errors."""
    pass


class NetworkManager:
    """Manages network operations with retry logic and error handling."""
    
    def __init__(self, 
                 default_timeout: int = 30,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.is_offline = False
        self.last_connection_check = None
        self.connection_check_interval = 300  # 5 minutes
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        if isinstance(error, requests.exceptions.Timeout):
            return True
        if isinstance(error, requests.exceptions.ConnectionError):
            return True
        if isinstance(error, requests.exceptions.RequestException):
            if hasattr(error, 'response') and error.response:
                # Retry on 5xx server errors and 429 (rate limit)
                status_code = error.response.status_code
                return status_code >= 500 or status_code == 429
            return True
        return False
    
    def _check_internet_connection(self) -> bool:
        """Check if internet connection is available."""
        try:
            # Quick connection test to a reliable host
            response = requests.get('https://httpbin.org/status/200', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_online(self) -> bool:
        """Check if we're currently online with caching."""
        current_time = datetime.now()
        
        # Use cached result if recent
        if (self.last_connection_check and 
            (current_time - self.last_connection_check).total_seconds() < self.connection_check_interval):
            return not self.is_offline
        
        # Perform actual check
        self.is_offline = not self._check_internet_connection()
        self.last_connection_check = current_time
        
        return not self.is_offline
    
    def get_with_retry(self, 
                      url: str, 
                      headers: Dict[str, str] = None,
                      params: Dict[str, Any] = None,
                      timeout: int = None,
                      max_retries: int = None) -> requests.Response:
        """
        Perform GET request with retry logic.
        
        Args:
            url: URL to request
            headers: Optional headers
            params: Optional parameters
            timeout: Request timeout (uses default if None)
            max_retries: Max retry attempts (uses default if None)
            
        Returns:
            Response object
            
        Raises:
            NetworkError: If all retries fail
        """
        timeout = timeout or self.default_timeout
        max_retries = max_retries or self.max_retries
        last_error = None
        
        # Check if we're offline
        if not self.is_online():
            raise NetworkError("No internet connection available")
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_error = e
                
                if attempt == max_retries:
                    # Last attempt failed
                    break
                
                if not self._is_retryable_error(e):
                    # Non-retryable error
                    break
                
                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), "
                             f"retrying in {delay:.1f}s: {str(e)}")
                time.sleep(delay)
        
        # All retries failed
        error_msg = f"Request failed after {max_retries + 1} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise NetworkError(error_msg)
    
    def post_with_retry(self,
                       url: str,
                       data: Dict[str, Any] = None,
                       json: Dict[str, Any] = None,
                       headers: Dict[str, str] = None,
                       timeout: int = None,
                       max_retries: int = None) -> requests.Response:
        """
        Perform POST request with retry logic.
        
        Args:
            url: URL to post to
            data: Form data
            json: JSON data
            headers: Optional headers
            timeout: Request timeout
            max_retries: Max retry attempts
            
        Returns:
            Response object
            
        Raises:
            NetworkError: If all retries fail
        """
        timeout = timeout or self.default_timeout
        max_retries = max_retries or self.max_retries
        last_error = None
        
        if not self.is_online():
            raise NetworkError("No internet connection available")
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_error = e
                
                if attempt == max_retries:
                    break
                
                if not self._is_retryable_error(e):
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"POST request failed (attempt {attempt + 1}/{max_retries + 1}), "
                             f"retrying in {delay:.1f}s: {str(e)}")
                time.sleep(delay)
        
        error_msg = f"POST request failed after {max_retries + 1} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise NetworkError(error_msg)
    
    def with_retry(self, 
                   max_retries: int = None,
                   timeout: int = None,
                   handle_offline: bool = True):
        """
        Decorator to add retry logic to network functions.
        
        Args:
            max_retries: Max retry attempts
            timeout: Operation timeout
            handle_offline: Whether to check for offline mode
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                _max_retries = max_retries or self.max_retries
                last_error = None
                
                if handle_offline and not self.is_online():
                    raise NetworkError("No internet connection available")
                
                for attempt in range(_max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                        
                    except Exception as e:
                        last_error = e
                        
                        if attempt == _max_retries:
                            break
                        
                        if not self._is_retryable_error(e):
                            break
                        
                        delay = self._calculate_delay(attempt)
                        logger.warning(f"Function {func.__name__} failed "
                                     f"(attempt {attempt + 1}/{_max_retries + 1}), "
                                     f"retrying in {delay:.1f}s: {str(e)}")
                        time.sleep(delay)
                
                error_msg = f"Function {func.__name__} failed after {_max_retries + 1} attempts: {str(last_error)}"
                logger.error(error_msg)
                raise NetworkError(error_msg)
            
            return wrapper
        return decorator
    
    def get_fallback_data(self, data_type: str) -> Dict[str, Any]:
        """
        Get fallback data when network operations fail.
        
        Args:
            data_type: Type of data requested ('weather', 'news', etc.)
            
        Returns:
            Fallback data structure
        """
        fallback_data = {
            'weather': {
                'status': 'offline',
                'message': 'Weather data unavailable - no internet connection',
                'location': 'Unknown',
                'temperature': None,
                'condition': 'Unknown',
                'last_updated': None
            },
            'news': {
                'status': 'offline',
                'message': 'News unavailable - no internet connection',
                'articles': [],
                'total_results': 0,
                'last_updated': None
            },
            'email': {
                'status': 'offline',
                'message': 'Email service unavailable - no internet connection',
                'can_send': False,
                'can_receive': False
            }
        }
        
        return fallback_data.get(data_type, {
            'status': 'offline',
            'message': f'{data_type} service unavailable - no internet connection'
        })
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status information."""
        is_online = self.is_online()
        
        return {
            'online': is_online,
            'last_check': self.last_connection_check.isoformat() if self.last_connection_check else None,
            'check_interval_seconds': self.connection_check_interval,
            'retry_config': {
                'max_retries': self.max_retries,
                'base_delay': self.base_delay,
                'max_delay': self.max_delay,
                'backoff_factor': self.backoff_factor,
                'default_timeout': self.default_timeout
            }
        }


# Global network manager instance
_global_network_manager: Optional[NetworkManager] = None


def get_network_manager() -> NetworkManager:
    """Get or create the global network manager."""
    global _global_network_manager
    
    if _global_network_manager is None:
        _global_network_manager = NetworkManager()
    
    return _global_network_manager


def with_network_retry(max_retries: int = 3, timeout: int = 30, handle_offline: bool = True):
    """Convenience decorator for network retry logic."""
    manager = get_network_manager()
    return manager.with_retry(max_retries, timeout, handle_offline)


def safe_request_get(url: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
    """
    Convenience function for safe GET requests with fallback.
    
    Returns either the response or fallback data on failure.
    """
    manager = get_network_manager()
    
    try:
        return manager.get_with_retry(url, **kwargs)
    except NetworkError as e:
        logger.warning(f"Network request failed: {e}")
        return {"error": True, "message": str(e), "status": "network_error"}


def safe_request_post(url: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
    """
    Convenience function for safe POST requests with fallback.
    
    Returns either the response or fallback data on failure.
    """
    manager = get_network_manager()
    
    try:
        return manager.post_with_retry(url, **kwargs)
    except NetworkError as e:
        logger.warning(f"Network POST request failed: {e}")
        return {"error": True, "message": str(e), "status": "network_error"}