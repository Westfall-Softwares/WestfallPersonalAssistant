"""
Application settings management using Pydantic.
"""

import os
from typing import Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Main application settings."""
    
    app_name: str = Field(default="Westfall Backend", env="WESTFALL_APP_NAME")
    host: str = Field(default="127.0.0.1", env="WESTFALL_HOST")
    port: int = Field(default=0, env="WESTFALL_PORT")  # 0 = pick free port
    data_dir: str = Field(default="", env="WESTFALL_DATA_DIR")
    model_path: str = Field(default="", env="WESTFALL_MODEL_PATH")
    n_threads: int = Field(default=4, env="WESTFALL_N_THREADS")
    n_ctx: int = Field(default=4096, env="WESTFALL_N_CTX")
    n_gpu_layers: int = Field(default=0, env="WESTFALL_N_GPU_LAYERS")
    log_level: str = Field(default="INFO", env="WESTFALL_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_prefix = "WESTFALL_"
        
    def get_data_dir(self) -> Path:
        """Get the data directory path, creating OS-appropriate default if needed."""
        if self.data_dir:
            return Path(self.data_dir)
            
        # Set default data directories based on OS
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('LOCALAPPDATA', '~')) / "Westfall" / "Assistant"
        elif os.name == 'posix':
            if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':  # macOS
                base_dir = Path.home() / "Library" / "Application Support" / "Westfall" / "Assistant"
            else:  # Linux
                base_dir = Path.home() / ".local" / "share" / "westfall-assistant"
        else:
            base_dir = Path.home() / ".westfall-assistant"
        
        return base_dir.expanduser()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment/config."""
    global _settings
    _settings = None
    return get_settings()