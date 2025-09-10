from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from westfall_backend.services.settings import Settings
from westfall_backend.services.logging import setup_logging
from westfall_backend.routers import health, llm, metrics, web
import uvicorn

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
    
    app.include_router(health.router)
    app.include_router(llm.router)
    app.include_router(metrics.router)
    app.include_router(web.router)
    return app

if __name__ == "__main__":
    settings = Settings()
    uvicorn.run("westfall_backend.app:create_app", host=settings.host, port=settings.port or 8756, factory=True)