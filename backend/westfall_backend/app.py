#!/usr/bin/env python3
"""
Westfall Personal Assistant Backend Application

Main FastAPI application factory and configuration.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

# Add project root to path first
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import dependencies that might not be available yet
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    import uvicorn
except ImportError as e:
    print(f"FastAPI dependencies not available: {e}")
    print("Please install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("psutil not available. Please install with: pip install psutil")
    psutil = None

# Import local modules with error handling
try:
    from .routers import health, llm, tools
    from .services.settings import get_settings
    from .services.logging import setup_logging
    from .services.llama_runtime import LlamaSupervisor
except ImportError as e:
    print(f"Relative import error: {e}")
    try:
        # Fallback to absolute imports
        from backend.westfall_backend.routers import health, llm, tools
        from backend.westfall_backend.services.settings import get_settings
        from backend.westfall_backend.services.logging import setup_logging
        from backend.westfall_backend.services.llama_runtime import LlamaSupervisor
    except ImportError as e2:
        print(f"Absolute import error: {e2}")
        # Create minimal stubs for missing modules
        class StubRouter:
            def __init__(self):
                from fastapi import APIRouter
                self.router = APIRouter()
                
                @self.router.get("/")
                async def stub():
                    return {"status": "stub", "message": "Module not fully loaded"}
        
        health = llm = tools = StubRouter()
        
        def get_settings():
            class StubSettings:
                def __init__(self):
                    self.llm = type('obj', (object,), {})()
                    self.server = type('obj', (object,), {})()
                    self.security = type('obj', (object,), {})()
                    self.data = type('obj', (object,), {})()
            return StubSettings()
        
        def setup_logging():
            logging.basicConfig(level=logging.INFO)
        
        class LlamaSupervisor:
            def __init__(self, settings):
                self.settings = settings
            async def shutdown(self):
                pass

# Global state
llama_supervisor = None
settings = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global llama_supervisor, settings
    
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting Westfall Personal Assistant Backend...")
    
    try:
        # Initialize settings
        settings = get_settings()
        
        # Initialize LLM supervisor
        llama_supervisor = LlamaSupervisor(settings)
        app.state.llama_supervisor = llama_supervisor
        
        # Initialize other services as needed
        logger.info("Backend startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend...")
    if llama_supervisor:
        await llama_supervisor.shutdown()
    logger.info("Backend shutdown completed")

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Westfall Personal Assistant Backend",
        description="Backend API for Westfall Personal Assistant",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost"]
    )
    
    # CORS middleware (restricted to localhost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:*", "http://localhost:*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Request ID middleware for correlation
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add to logs
        logger = logging.getLogger(__name__)
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Westfall Personal Assistant Backend",
            "version": "1.0.0",
            "status": "running"
        }
    
    # Shutdown endpoint for graceful shutdown
    @app.post("/shutdown")
    async def shutdown():
        logger.info("Shutdown request received")
        # This will be handled by the process manager
        return {"message": "Shutdown initiated"}
    
    return app

def main():
    """Main entry point for the backend server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Westfall Personal Assistant Backend")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8756, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Create the app
    app = create_app()
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()