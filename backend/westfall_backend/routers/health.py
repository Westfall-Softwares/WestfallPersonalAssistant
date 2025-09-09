"""
Health and status endpoints for the backend service.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from fastapi import APIRouter, Request
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create stub classes
    class APIRouter:
        def __init__(self): pass
        def get(self, path): 
            def decorator(func): return func
            return decorator
    
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

router = APIRouter()

# Store startup time
startup_time = time.time()

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    timestamp: str
    pid: int
    memory_usage: Dict[str, Any]
    system_info: Dict[str, Any]
    model_status: Dict[str, Any]

@router.get("/health")
async def health_check(request=None):
    """
    Health check endpoint that returns system status and metrics.
    """
    current_time = time.time()
    uptime = current_time - startup_time
    
    # Get memory usage (with fallback if psutil not available)
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage = {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "percent": process.memory_percent()
            }
            
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            }
        except Exception:
            memory_usage = {"error": "Could not get memory info"}
            system_info = {"error": "Could not get system info"}
    else:
        memory_usage = {"status": "psutil not available"}
        system_info = {"status": "psutil not available"}
    
    # Check model status (if available)
    model_status = {"loaded": False, "model_name": None}
    if request and hasattr(request, 'app') and hasattr(request.app, 'state') and hasattr(request.app.state, 'llama_supervisor'):
        supervisor = request.app.state.llama_supervisor
        if supervisor and hasattr(supervisor, 'is_model_loaded') and supervisor.is_model_loaded():
            model_status = {
                "loaded": True,
                "model_name": supervisor.get_model_name(),
                "model_size": supervisor.get_model_size()
            }
    
    if FASTAPI_AVAILABLE:
        return HealthResponse(
            status="ok",
            version="1.0.0",
            uptime=uptime,
            timestamp=datetime.utcnow().isoformat(),
            pid=os.getpid(),
            memory_usage=memory_usage,
            system_info=system_info,
            model_status=model_status
        )
    else:
        return {
            "status": "ok",
            "version": "1.0.0",
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "pid": os.getpid(),
            "memory_usage": memory_usage,
            "system_info": system_info,
            "model_status": model_status
        }

@router.get("/metrics")
async def metrics():
    """
    Prometheus-style metrics endpoint.
    """
    current_time = time.time()
    uptime = current_time - startup_time
    
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = psutil.cpu_percent()
            rss = memory_info.rss
        except Exception:
            rss = 0
            cpu_percent = 0
    else:
        rss = 0
        cpu_percent = 0
    
    metrics = [
        f"# HELP westfall_uptime_seconds Total uptime in seconds",
        f"# TYPE westfall_uptime_seconds counter",
        f"westfall_uptime_seconds {uptime}",
        f"",
        f"# HELP westfall_memory_rss_bytes Resident set size memory",
        f"# TYPE westfall_memory_rss_bytes gauge", 
        f"westfall_memory_rss_bytes {rss}",
        f"",
        f"# HELP westfall_cpu_percent CPU usage percentage",
        f"# TYPE westfall_cpu_percent gauge",
        f"westfall_cpu_percent {cpu_percent}",
    ]
    
    return "\n".join(metrics)

@router.get("/ready")
async def readiness_check(request=None):
    """
    Readiness check endpoint for container orchestration.
    """
    # Check if critical services are ready
    ready = True
    services = {}
    
    # Check LLM supervisor
    if request and hasattr(request, 'app') and hasattr(request.app, 'state') and hasattr(request.app.state, 'llama_supervisor'):
        supervisor = request.app.state.llama_supervisor
        services["llama_supervisor"] = supervisor is not None
    else:
        services["llama_supervisor"] = False
        ready = False
    
    return {
        "ready": ready,
        "services": services,
        "timestamp": datetime.utcnow().isoformat()
    }