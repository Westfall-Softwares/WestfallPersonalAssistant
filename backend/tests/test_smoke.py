"""
Basic smoke tests for the Westfall Personal Assistant backend.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import pytest
    import httpx
    from unittest.mock import Mock
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# Test that we can import the backend
def test_backend_import():
    """Test that the backend can be imported without errors."""
    from backend.westfall_backend.app import create_app
    app = create_app()
    assert app is not None

def test_settings_creation():
    """Test that settings can be created."""
    from backend.westfall_backend.services.settings import get_settings
    settings = get_settings()
    assert settings is not None
    assert settings.host == "127.0.0.1"
    assert settings.n_ctx == 4096

def test_health_endpoint():
    """Test the health endpoint with a test client."""
    from backend.westfall_backend.app import create_app
    try:
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "uptime" in data
        assert "pid" in data
    except ImportError:
        print("FastAPI TestClient not available for testing")

def test_root_endpoint():
    """Test the root endpoint."""
    from backend.westfall_backend.app import create_app
    try:
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Westfall Personal Assistant Backend"
        assert data["status"] == "running"
    except ImportError:
        print("FastAPI TestClient not available for testing")

def test_llama_supervisor_creation():
    """Test that LLM supervisor can be created."""
    from backend.westfall_backend.services.settings import get_settings
    from backend.westfall_backend.services.llama_supervisor import LlamaSupervisor
    
    settings = get_settings()
    supervisor = LlamaSupervisor(settings)
    assert supervisor is not None
    assert supervisor.llama_cpp_available is True  # Since we installed it

if __name__ == "__main__":
    # Simple test runner if pytest not available
    print("Running basic smoke tests...")
    
    try:
        test_backend_import()
        print("✓ Backend import test passed")
    except Exception as e:
        print(f"✗ Backend import test failed: {e}")
    
    try:
        test_settings_creation()
        print("✓ Settings creation test passed")
    except Exception as e:
        print(f"✗ Settings creation test failed: {e}")
    
    try:
        test_llama_supervisor_creation()
        print("✓ LLM supervisor creation test passed")
    except Exception as e:
        print(f"✗ LLM supervisor creation test failed: {e}")
    
    print("Basic smoke tests completed")