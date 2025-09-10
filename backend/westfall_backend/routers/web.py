from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Template directory - look for templates in the project root
template_dir = Path(__file__).parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web interface."""
    try:
        # Basic status info
        status = {
            "initialized": True,
            "backend_running": True
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
