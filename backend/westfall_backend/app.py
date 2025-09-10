from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
from westfall_backend.services.settings import Settings
from westfall_backend.services.logging import setup_logging
from westfall_backend.routers import health, llm, metrics, web
import uvicorn

def get_static_dir():
    """Get static directory for both development and packaged modes."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys.executable).parent
        static_dir = base_path / "static"
        if not static_dir.exists():
            # Try relative to exe
            static_dir = base_path.parent / "static"
    else:
        # Running in development
        static_dir = Path(__file__).parent.parent.parent / "static"
    
    return static_dir

def create_app() -> FastAPI:
    settings = Settings()
    setup_logging(settings.data_dir)
    app = FastAPI(title="Westfall Backend")
    
    # Add CORS middleware for Electron integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:*", "http://127.0.0.1:*", "file://*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files if directory exists
    static_dir = get_static_dir()
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    app.include_router(health.router)
    app.include_router(llm.router)
    app.include_router(metrics.router)
    app.include_router(web.router)
    return app

if __name__ == "__main__":
    settings = Settings()
    app = create_app()
    uvicorn.run(app, host=settings.host, port=settings.port or 8756)