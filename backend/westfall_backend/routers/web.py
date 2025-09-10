from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
from westfall_backend.services.settings import Settings

router = APIRouter()

# Handle template and static directories for both development and packaged modes
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

def get_static_dir():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys.executable).parent
        static_dir = base_path / "static"
        if not static_dir.exists():
            # Try relative to exe
            static_dir = base_path.parent / "static"
    else:
        # Running in development
        static_dir = Path(__file__).parent.parent.parent.parent / "static"
    
    return str(static_dir)

templates = Jinja2Templates(directory=get_template_dir())

# Add url_for function to Jinja2 environment
def url_for(endpoint: str, **values):
    """FastAPI equivalent of Flask's url_for for static files."""
    if endpoint == 'static':
        filename = values.get('filename', '')
        return f"/static/{filename}"
    return ""

templates.env.globals['url_for'] = url_for
app_settings = Settings()

# Mount static files
static_dir = get_static_dir()
if Path(static_dir).exists():
    from fastapi import FastAPI
    # We'll need to add this to the main app, not here
    pass

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web interface."""
    try:
        # Try to get the real assistant status
        try:
            from core.assistant import get_assistant_core
            assistant = get_assistant_core()
            if assistant:
                status = assistant.get_status()
            else:
                status = {"initialized": False}
        except ImportError:
            # Fallback status when core assistant isn't available
            model_status = app_settings.get_model_status()
            status = {
                "initialized": True,
                "backend_running": True,
                "conversation_count": 0,
                "session_duration": 0,
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
    try:
        # Try to get the real settings data
        try:
            from core.settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            current_settings = settings_manager.get_all_settings(mask_sensitive=True)
            service_status = settings_manager.get_service_status()
            
            return templates.TemplateResponse("settings.html", {
                "request": request,
                "settings": current_settings,
                "services": service_status
            })
        except ImportError:
            # Fallback if settings manager isn't available
            return templates.TemplateResponse("settings.html", {
                "request": request,
                "settings": {},
                "services": {}
            })
    except Exception as e:
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "error": str(e)
        })

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

@router.get("/api/settings/status")
async def get_settings_status():
    """Get overall settings and service status."""
    try:
        # Try to get the real settings data
        try:
            from core.settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            service_status = settings_manager.get_service_status()
            
            # Count configured services
            configured_count = sum(1 for service in service_status.values() if service.get('configured', False))
            total_count = len(service_status)
            
            return {
                'success': True,
                'configured_services': configured_count,
                'total_services': total_count,
                'services': service_status,
                'configuration_complete': configured_count >= 2  # At least 2 services configured
            }
        except ImportError:
            # Fallback if settings manager isn't available
            return {
                'success': True,
                'configured_services': 0,
                'total_services': 0,
                'services': {},
                'configuration_complete': False
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
