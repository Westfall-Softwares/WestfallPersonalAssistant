from pydantic_settings import BaseSettings
from pathlib import Path
import os, platform
from typing import Dict, Any

def default_data_dir() -> str:
    sys = platform.system()
    if sys == "Windows":
        base = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        return str(Path(base) / "Westfall" / "Assistant")
    elif sys == "Darwin":
        return str(Path.home() / "Library" / "Application Support" / "Westfall" / "Assistant")
    else:
        return str(Path.home() / ".local" / "share" / "westfall-assistant")

class Settings(BaseSettings):
    app_name: str = "Westfall Backend"
    host: str = "127.0.0.1"
    port: int = 0
    data_dir: str = default_data_dir()
    model_path: str = ""
    n_threads: int = 4
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "WESTFALL_"
        protected_namespaces = ('settings_',)
    
    def validate_model_path(self) -> bool:
        """Check if the model path exists and is valid."""
        if not self.model_path:
            return False
        return Path(self.model_path).exists()
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get model configuration status."""
        return {
            "configured": bool(self.model_path),
            "exists": self.validate_model_path(),
            "path": self.model_path
        }