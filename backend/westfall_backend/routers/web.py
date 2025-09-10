from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
from westfall_backend.services.settings import Settings

router = APIRouter()

# Handle template directory for both development and packaged modes
def get_template_dir():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys.executable).parent
        template_dir = base_path / "templates"
        if not template_dir.exists():
            # Try relative to exe
            template_dir = base_path.parent / "templates"
    else:
        # Running in development
        template_dir = Path(__file__).parent.parent.parent.parent / "templates"
    
    return str(template_dir)

templates = Jinja2Templates(directory=get_template_dir())
app_settings = Settings()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web interface."""
    try:
        # Get model and backend status
        model_status = app_settings.get_model_status()
        status = {
            "initialized": True,
            "backend_running": True,
            "model_configured": model_status["configured"],
            "model_available": model_status["exists"],
            "model_path": model_status["path"]
        }
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "assistant_status": status
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/settings", response_class=HTMLResponse) 
async def settings(request: Request):
    """Serve the settings page."""
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page."""
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception:
        # Fallback if dashboard.html doesn't exist
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Dashboard not yet implemented"
        })

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Serve the about page."""
    try:
        return templates.TemplateResponse("about.html", {"request": request})
    except Exception:
        # Fallback if about.html doesn't exist
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "About page not yet implemented"
        })
