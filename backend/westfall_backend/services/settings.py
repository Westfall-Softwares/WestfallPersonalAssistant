"""
Application settings management.
"""

import os
from typing import Optional, List
from pathlib import Path


class LLMSettings:
    """LLM-specific settings."""
    def __init__(self):
        self.default_model_path: Optional[str] = None
        self.context_length: int = int(os.getenv('LLM_CONTEXT_LENGTH', '4096'))
        self.gpu_layers: int = int(os.getenv('LLM_GPU_LAYERS', '-1'))
        self.max_tokens: int = int(os.getenv('LLM_MAX_TOKENS', '2048'))
        self.temperature: float = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        self.top_p: float = float(os.getenv('LLM_TOP_P', '0.9'))
        self.top_k: int = int(os.getenv('LLM_TOP_K', '40'))
        self.repeat_penalty: float = float(os.getenv('LLM_REPEAT_PENALTY', '1.1'))


class ServerSettings:
    """Server configuration settings."""
    def __init__(self):
        self.host: str = os.getenv('SERVER_HOST', '127.0.0.1')
        self.port: int = int(os.getenv('SERVER_PORT', '8756'))
        self.workers: int = int(os.getenv('SERVER_WORKERS', '1'))
        self.reload: bool = os.getenv('SERVER_RELOAD', 'false').lower() == 'true'
        self.log_level: str = os.getenv('SERVER_LOG_LEVEL', 'info')


class SecuritySettings:
    """Security-related settings."""
    def __init__(self):
        self.allowed_hosts: List[str] = os.getenv('SECURITY_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
        self.cors_origins: List[str] = os.getenv('SECURITY_CORS_ORIGINS', 'http://127.0.0.1:*,http://localhost:*').split(',')
        self.max_requests_per_minute: int = int(os.getenv('SECURITY_MAX_REQUESTS_PER_MINUTE', '60'))
        self.max_tokens_per_hour: int = int(os.getenv('SECURITY_MAX_TOKENS_PER_HOUR', '100000'))


class DataSettings:
    """Data storage settings."""
    def __init__(self):
        self.data_dir: Optional[Path] = None
        self.models_dir: Optional[Path] = None
        self.logs_dir: Optional[Path] = None
        
        # Set default data directories based on OS
        data_dir_env = os.getenv('DATA_DIR')
        if data_dir_env:
            self.data_dir = Path(data_dir_env)
        else:
            if os.name == 'nt':  # Windows
                base_dir = Path(os.environ.get('LOCALAPPDATA', '~')) / "Westfall" / "Assistant"
            elif os.name == 'posix':
                if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':  # macOS
                    base_dir = Path.home() / "Library" / "Application Support" / "Westfall" / "Assistant"
                else:  # Linux
                    base_dir = Path.home() / ".local" / "share" / "westfall-assistant"
            else:
                base_dir = Path.home() / ".westfall-assistant"
            
            self.data_dir = base_dir.expanduser()
        
        # Set subdirectories
        self.models_dir = self.data_dir / "models"
        self.logs_dir = self.data_dir / "logs"
        
        # Create directories if they don't exist
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create data directories: {e}")


class Settings:
    """Main application settings."""
    
    def __init__(self):
        # Environment
        self.environment: str = os.getenv('ENVIRONMENT', 'production')
        self.debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Sub-settings
        self.llm: LLMSettings = LLMSettings()
        self.server: ServerSettings = ServerSettings()
        self.security: SecuritySettings = SecuritySettings()
        self.data: DataSettings = DataSettings()


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