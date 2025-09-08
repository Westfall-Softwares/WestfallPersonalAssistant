"""
API Gateway for Westfall Personal Assistant
Provides centralized API management, rate limiting, and security
"""

import time
import threading
import hashlib
import hmac
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid


@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_secret: str
    service: str
    name: str
    created_date: datetime
    last_used: Optional[datetime]
    usage_count: int
    rate_limit: int
    is_active: bool
    permissions: List[str]


@dataclass
class APIRequest:
    """API request information"""
    request_id: str
    service: str
    endpoint: str
    method: str
    timestamp: datetime
    response_time: float
    status_code: int
    error_message: Optional[str]
    api_key_id: Optional[str]


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.request_counts = defaultdict(lambda: deque())
        self.lock = threading.RLock()
        
    def is_allowed(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """Check if request is allowed based on rate limit"""
        with self.lock:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Clean old requests
            while (self.request_counts[key] and 
                   self.request_counts[key][0] < window_start):
                self.request_counts[key].popleft()
                
            # Check if limit exceeded
            if len(self.request_counts[key]) >= limit:
                return False
                
            # Add current request
            self.request_counts[key].append(current_time)
            return True
            
    def get_remaining_requests(self, key: str, limit: int, window_seconds: int = 3600) -> int:
        """Get remaining requests in current window"""
        with self.lock:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Clean old requests
            while (self.request_counts[key] and 
                   self.request_counts[key][0] < window_start):
                self.request_counts[key].popleft()
                
            return max(0, limit - len(self.request_counts[key]))


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.RLock()
        
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == "OPEN":
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time > self.timeout_seconds):
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
                    
            try:
                result = func(*args, **kwargs)
                
                # Success - reset circuit breaker
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    
                raise e


class APIGateway:
    """Central API gateway for managing external service integrations"""
    
    def __init__(self):
        self.api_keys = {}
        self.request_history = []
        self.rate_limiter = RateLimiter()
        self.circuit_breakers = {}
        self.service_health = {}
        self.request_transformers = {}
        self.response_transformers = {}
        
        # Default service configurations
        self.service_configs = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "rate_limit": 3000,  # requests per hour
                "timeout": 30,
                "retry_attempts": 3,
                "circuit_breaker": {"failure_threshold": 5, "timeout": 300}
            },
            "weather": {
                "base_url": "https://api.openweathermap.org/data/2.5",
                "rate_limit": 1000,
                "timeout": 10,
                "retry_attempts": 2,
                "circuit_breaker": {"failure_threshold": 3, "timeout": 120}
            },
            "news": {
                "base_url": "https://newsapi.org/v2",
                "rate_limit": 500,
                "timeout": 15,
                "retry_attempts": 2,
                "circuit_breaker": {"failure_threshold": 3, "timeout": 120}
            },
            "email": {
                "base_url": "smtp.gmail.com",
                "rate_limit": 100,
                "timeout": 30,
                "retry_attempts": 1,
                "circuit_breaker": {"failure_threshold": 2, "timeout": 180}
            }
        }
        
        # Initialize circuit breakers
        for service, config in self.service_configs.items():
            cb_config = config.get("circuit_breaker", {})
            self.circuit_breakers[service] = CircuitBreaker(
                failure_threshold=cb_config.get("failure_threshold", 5),
                timeout_seconds=cb_config.get("timeout", 60)
            )
            
        self._init_default_api_keys()
        
    def _init_default_api_keys(self):
        """Initialize default API keys (would load from secure storage)"""
        # These would normally be loaded from encrypted storage
        default_keys = [
            {
                "service": "openai",
                "name": "Default OpenAI Key",
                "permissions": ["chat", "completions", "embeddings"]
            },
            {
                "service": "weather",
                "name": "OpenWeatherMap Key",
                "permissions": ["current", "forecast", "history"]
            },
            {
                "service": "news",
                "name": "NewsAPI Key", 
                "permissions": ["everything", "top-headlines", "sources"]
            }
        ]
        
        for key_info in default_keys:
            self.create_api_key(**key_info)
            
    def create_api_key(self, service: str, name: str, 
                      permissions: List[str] = None, 
                      rate_limit: int = None) -> APIKey:
        """Create a new API key"""
        key_id = str(uuid.uuid4())
        key_secret = self._generate_key_secret()
        
        service_config = self.service_configs.get(service, {})
        default_rate_limit = service_config.get("rate_limit", 1000)
        
        api_key = APIKey(
            key_id=key_id,
            key_secret=key_secret,
            service=service,
            name=name,
            created_date=datetime.now(),
            last_used=None,
            usage_count=0,
            rate_limit=rate_limit or default_rate_limit,
            is_active=True,
            permissions=permissions or []
        )
        
        self.api_keys[key_id] = api_key
        return api_key
        
    def _generate_key_secret(self) -> str:
        """Generate a secure API key secret"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
        
    def rotate_api_key(self, key_id: str) -> Optional[str]:
        """Rotate an API key (generate new secret)"""
        if key_id not in self.api_keys:
            return None
            
        api_key = self.api_keys[key_id]
        old_secret = api_key.key_secret
        api_key.key_secret = self._generate_key_secret()
        
        return api_key.key_secret
        
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id not in self.api_keys:
            return False
            
        self.api_keys[key_id].is_active = False
        return True
        
    def make_request(self, service: str, endpoint: str, method: str = "GET",
                    data: Any = None, headers: Dict[str, str] = None,
                    api_key_id: str = None, **kwargs) -> Dict[str, Any]:
        """Make an API request through the gateway"""
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate service
            if service not in self.service_configs:
                raise ValueError(f"Unknown service: {service}")
                
            # Get API key
            api_key = None
            if api_key_id:
                api_key = self.api_keys.get(api_key_id)
                if not api_key or not api_key.is_active:
                    raise ValueError("Invalid or inactive API key")
                    
            # Check rate limits
            rate_limit_key = f"{service}:{api_key_id}" if api_key_id else service
            service_config = self.service_configs[service]
            rate_limit = api_key.rate_limit if api_key else service_config["rate_limit"]
            
            if not self.rate_limiter.is_allowed(rate_limit_key, rate_limit):
                raise Exception("Rate limit exceeded")
                
            # Transform request if transformer exists
            if service in self.request_transformers:
                data = self.request_transformers[service](data, **kwargs)
                
            # Make request through circuit breaker
            def _make_actual_request():
                return self._execute_request(service, endpoint, method, data, headers, **kwargs)
                
            response = self.circuit_breakers[service].call(_make_actual_request)
            
            # Transform response if transformer exists
            if service in self.response_transformers:
                response = self.response_transformers[service](response)
                
            # Update API key usage
            if api_key:
                api_key.last_used = datetime.now()
                api_key.usage_count += 1
                
            # Log successful request
            self._log_request(
                request_id, service, endpoint, method,
                time.time() - start_time, 200, None, api_key_id
            )
            
            return {
                "success": True,
                "data": response,
                "request_id": request_id,
                "service": service
            }
            
        except Exception as e:
            # Log failed request
            self._log_request(
                request_id, service, endpoint, method,
                time.time() - start_time, 500, str(e), api_key_id
            )
            
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id,
                "service": service
            }
            
    def _execute_request(self, service: str, endpoint: str, method: str,
                        data: Any, headers: Dict[str, str], **kwargs) -> Any:
        """Execute the actual API request"""
        # This would normally use requests library
        # For now, return mock responses
        
        mock_responses = {
            "openai": {
                "chat/completions": {
                    "choices": [{"message": {"content": "Mock AI response"}}]
                },
                "completions": {
                    "choices": [{"text": "Mock completion"}]
                }
            },
            "weather": {
                "weather": {
                    "weather": [{"main": "Clear", "description": "clear sky"}],
                    "main": {"temp": 72, "humidity": 45},
                    "name": "Mock City"
                },
                "forecast": {
                    "list": [
                        {"dt_txt": "2024-01-01 12:00:00", "main": {"temp": 70}},
                        {"dt_txt": "2024-01-01 15:00:00", "main": {"temp": 75}}
                    ]
                }
            },
            "news": {
                "everything": {
                    "articles": [
                        {
                            "title": "Mock News Article",
                            "description": "This is a mock news article",
                            "url": "https://example.com/news/1"
                        }
                    ]
                },
                "top-headlines": {
                    "articles": [
                        {
                            "title": "Breaking: Mock Headlines",
                            "description": "Important mock news",
                            "url": "https://example.com/breaking/1"
                        }
                    ]
                }
            }
        }
        
        # Simulate network delay
        import random
        time.sleep(random.uniform(0.1, 0.5))
        
        service_responses = mock_responses.get(service, {})
        return service_responses.get(endpoint, {"message": "Mock response"})
        
    def _log_request(self, request_id: str, service: str, endpoint: str, 
                    method: str, response_time: float, status_code: int,
                    error_message: Optional[str], api_key_id: Optional[str]):
        """Log API request for analytics"""
        request_log = APIRequest(
            request_id=request_id,
            service=service,
            endpoint=endpoint,
            method=method,
            timestamp=datetime.now(),
            response_time=response_time,
            status_code=status_code,
            error_message=error_message,
            api_key_id=api_key_id
        )
        
        self.request_history.append(request_log)
        
        # Keep only last 1000 requests to prevent memory issues
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
            
    def add_request_transformer(self, service: str, transformer: Callable):
        """Add request transformer for a service"""
        self.request_transformers[service] = transformer
        
    def add_response_transformer(self, service: str, transformer: Callable):
        """Add response transformer for a service"""
        self.response_transformers[service] = transformer
        
    def get_service_health(self, service: str) -> Dict[str, Any]:
        """Get health status of a service"""
        if service not in self.service_configs:
            return {"status": "unknown", "message": "Service not configured"}
            
        circuit_breaker = self.circuit_breakers[service]
        recent_requests = [r for r in self.request_history 
                          if r.service == service and 
                          r.timestamp > datetime.now() - timedelta(hours=1)]
        
        success_count = len([r for r in recent_requests if r.status_code == 200])
        error_count = len([r for r in recent_requests if r.status_code != 200])
        total_requests = len(recent_requests)
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = (sum(r.response_time for r in recent_requests) / total_requests 
                           if total_requests > 0 else 0)
        
        status = "healthy"
        if circuit_breaker.state == "OPEN":
            status = "circuit_breaker_open"
        elif success_rate < 90:
            status = "degraded"
        elif avg_response_time > 5.0:
            status = "slow"
            
        return {
            "service": service,
            "status": status,
            "circuit_breaker_state": circuit_breaker.state,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "total_requests_last_hour": total_requests,
            "error_count_last_hour": error_count
        }
        
    def get_usage_analytics(self, service: str = None, 
                           hours: int = 24) -> Dict[str, Any]:
        """Get API usage analytics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_requests = [r for r in self.request_history 
                           if r.timestamp > cutoff_time]
        
        if service:
            filtered_requests = [r for r in filtered_requests if r.service == service]
            
        total_requests = len(filtered_requests)
        successful_requests = len([r for r in filtered_requests if r.status_code == 200])
        failed_requests = total_requests - successful_requests
        
        # Group by service
        by_service = defaultdict(int)
        for request in filtered_requests:
            by_service[request.service] += 1
            
        # Group by hour
        by_hour = defaultdict(int)
        for request in filtered_requests:
            hour_key = request.timestamp.strftime("%Y-%m-%d %H:00")
            by_hour[hour_key] += 1
            
        avg_response_time = (sum(r.response_time for r in filtered_requests) / total_requests 
                           if total_requests > 0 else 0)
        
        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "average_response_time": avg_response_time,
            "requests_by_service": dict(by_service),
            "requests_by_hour": dict(by_hour)
        }
        
    def get_api_key_usage(self, key_id: str) -> Dict[str, Any]:
        """Get usage statistics for a specific API key"""
        if key_id not in self.api_keys:
            return {"error": "API key not found"}
            
        api_key = self.api_keys[key_id]
        key_requests = [r for r in self.request_history if r.api_key_id == key_id]
        
        recent_requests = [r for r in key_requests 
                          if r.timestamp > datetime.now() - timedelta(hours=24)]
        
        remaining_requests = self.rate_limiter.get_remaining_requests(
            f"{api_key.service}:{key_id}", api_key.rate_limit
        )
        
        return {
            "key_id": key_id,
            "service": api_key.service,
            "name": api_key.name,
            "total_usage": api_key.usage_count,
            "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
            "requests_last_24h": len(recent_requests),
            "rate_limit": api_key.rate_limit,
            "remaining_requests": remaining_requests,
            "is_active": api_key.is_active
        }
        
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get overall gateway status"""
        services_status = {}
        for service in self.service_configs:
            services_status[service] = self.get_service_health(service)
            
        total_keys = len(self.api_keys)
        active_keys = len([k for k in self.api_keys.values() if k.is_active])
        
        return {
            "gateway_version": "1.0.0",
            "uptime": "Mock uptime",  # Would calculate actual uptime
            "total_api_keys": total_keys,
            "active_api_keys": active_keys,
            "total_requests": len(self.request_history),
            "services": services_status,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
api_gateway = APIGateway()


def get_api_gateway() -> APIGateway:
    """Get the global API gateway instance"""
    return api_gateway