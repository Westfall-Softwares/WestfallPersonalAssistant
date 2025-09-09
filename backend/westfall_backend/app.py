from fastapi import FastAPI
from .services.settings import Settings
from .services.logging import setup_logging
from .routers import health, llm, metrics
import uvicorn

def create_app() -> FastAPI:
    settings = Settings()
    setup_logging(settings.data_dir)
    app = FastAPI(title="Westfall Backend")
    app.include_router(health.router)
    app.include_router(llm.router)
    app.include_router(metrics.router)
    return app

if __name__ == "__main__":
    settings = Settings()
    uvicorn.run("westfall_backend.app:create_app", host=settings.host, port=settings.port or 8756, factory=True)