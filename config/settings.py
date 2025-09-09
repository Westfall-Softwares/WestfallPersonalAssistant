"""
Centralized Settings for Westfall Personal Assistant

Consolidates configuration from various files throughout the application.
Provides a single source of truth for all settings with environment variable support.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class UISettings:
    """User Interface Settings"""
    theme_mode: ThemeMode = ThemeMode.AUTO
    window_width: int = 1200
    window_height: int = 800
    remember_window_size: bool = True
    auto_save: bool = True
    auto_save_interval: int = 300  # seconds
    font_size: int = 12
    font_family: str = "Segoe UI"
    enable_animations: bool = True
    confirm_exit: bool = True
    startup_minimized: bool = False
    system_tray_enabled: bool = True


@dataclass
class ModelSettings:
    """AI Model Settings"""
    default_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama2"
    openai_api_key: str = ""
    openai_default_model: str = "gpt-3.5-turbo"
    local_models_directory: str = "models"
    
    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # GPU settings (RTX 2060 optimized)
    gpu_layers: int = -1  # Auto-detect
    vram_limit_gb: float = 5.0
    batch_size: int = 512
    threads: int = 8
    context_length: int = 4096


@dataclass
class VoiceSettings:
    """Voice and TTS Settings"""
    tts_enabled: bool = False
    tts_voice: str = "default"
    tts_speed: float = 1.0
    tts_volume: float = 0.8
    
    # Speech recognition
    stt_enabled: bool = False
    stt_language: str = "en-US"
    stt_continuous: bool = False
    
    # Voice activation
    wake_word_enabled: bool = False
    wake_word: str = "assistant"


@dataclass
class MemorySettings:
    """Memory and Conversation Settings"""
    conversation_history_enabled: bool = True
    max_conversation_length: int = 100
    auto_summarize_enabled: bool = True
    summarize_threshold: int = 50
    
    # Storage
    storage_backend: str = "file"  # file, sqlite, memory
    history_file: str = "data/conversation_history.json"
    database_url: str = "sqlite:///data/assistant.db"
    
    # Privacy
    encrypt_history: bool = False
    retention_days: int = 30  # 0 = keep forever


@dataclass
class SecuritySettings:
    """Security and Privacy Settings"""
    enable_input_validation: bool = True
    enable_output_filtering: bool = True
    enable_api_key_encryption: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_hour: int = 100000
    
    # Content filtering
    content_filtering_enabled: bool = True
    blocked_keywords: List[str] = field(default_factory=list)


@dataclass
class LoggingSettings:
    """Logging Configuration"""
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_file: str = "logs/assistant.log"
    max_log_size_mb: int = 10
    backup_count: int = 5
    
    # What to log
    log_user_inputs: bool = False  # Privacy consideration
    log_ai_responses: bool = True
    log_api_calls: bool = True
    log_errors: bool = True


@dataclass
class FeatureSettings:
    """Optional Feature Settings"""
    # Business features
    business_dashboard_enabled: bool = False
    crm_enabled: bool = False
    finance_tracking_enabled: bool = False
    time_tracking_enabled: bool = False
    
    # Extensions
    extensions_enabled: bool = True
    extension_directory: str = "extensions"
    auto_load_extensions: bool = True
    
    # Advanced features
    screen_capture_enabled: bool = False
    automation_enabled: bool = False
    web_search_enabled: bool = True


class Settings:
    """Main settings manager"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_file()
        
        # Initialize default settings
        self.ui = UISettings()
        self.models = ModelSettings()
        self.voice = VoiceSettings()
        self.memory = MemorySettings()
        self.security = SecuritySettings()
        self.logging = LoggingSettings()
        self.features = FeatureSettings()
        
        # Load settings from file and environment
        self.load()
    
    def _get_default_config_file(self) -> str:
        """Get default config file path"""
        # Use data directory in project root
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "settings.json")
    
    def load(self):
        """Load settings from file and environment variables"""
        # Load from file first
        self._load_from_file()
        
        # Override with environment variables
        self._load_from_environment()
        
        logger.info(f"Settings loaded from {self.config_file}")
    
    def save(self):
        """Save current settings to file"""
        try:
            config_data = {
                "ui": asdict(self.ui),
                "models": asdict(self.models),
                "voice": asdict(self.voice),
                "memory": asdict(self.memory),
                "security": asdict(self.security),
                "logging": asdict(self.logging),
                "features": asdict(self.features)
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Settings saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _load_from_file(self):
        """Load settings from JSON file"""
        if not os.path.exists(self.config_file):
            logger.info("No config file found, using defaults")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Update settings from file data
            if 'ui' in data:
                self._update_dataclass(self.ui, data['ui'])
            if 'models' in data:
                self._update_dataclass(self.models, data['models'])
            if 'voice' in data:
                self._update_dataclass(self.voice, data['voice'])
            if 'memory' in data:
                self._update_dataclass(self.memory, data['memory'])
            if 'security' in data:
                self._update_dataclass(self.security, data['security'])
            if 'logging' in data:
                self._update_dataclass(self.logging, data['logging'])
            if 'features' in data:
                self._update_dataclass(self.features, data['features'])
                
        except Exception as e:
            logger.error(f"Failed to load settings from file: {e}")
    
    def _load_from_environment(self):
        """Load settings from environment variables"""
        # Model settings
        if os.getenv('OPENAI_API_KEY'):
            self.models.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if os.getenv('OLLAMA_BASE_URL'):
            self.models.ollama_base_url = os.getenv('OLLAMA_BASE_URL')
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            try:
                self.logging.log_level = LogLevel(os.getenv('LOG_LEVEL').upper())
            except ValueError:
                pass
        
        # Feature flags
        if os.getenv('BUSINESS_FEATURES_ENABLED'):
            self.features.business_dashboard_enabled = os.getenv('BUSINESS_FEATURES_ENABLED').lower() == 'true'
    
    def _update_dataclass(self, instance, data: Dict[str, Any]):
        """Update dataclass instance with data dictionary"""
        for key, value in data.items():
            if hasattr(instance, key):
                # Handle enum types
                field_type = type(getattr(instance, key))
                if hasattr(field_type, '__bases__') and Enum in field_type.__bases__:
                    try:
                        setattr(instance, key, field_type(value))
                    except ValueError:
                        pass  # Keep default value
                else:
                    setattr(instance, key, value)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for model manager"""
        return {
            "gpu_layers": self.models.gpu_layers,
            "context_length": self.models.context_length,
            "temperature": self.models.temperature,
            "top_p": self.models.top_p,
            "top_k": self.models.top_k,
            "repeat_penalty": self.models.repeat_penalty,
            "max_tokens": self.models.max_tokens,
            "vram_limit_gb": self.models.vram_limit_gb,
            "batch_size": self.models.batch_size,
            "threads": self.models.threads
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.logging.log_level.value,
            "filename": self.logging.log_file if self.logging.log_to_file else None,
            "maxBytes": self.logging.max_log_size_mb * 1024 * 1024,
            "backupCount": self.logging.backup_count,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.ui = UISettings()
        self.models = ModelSettings()
        self.voice = VoiceSettings()
        self.memory = MemorySettings()
        self.security = SecuritySettings()
        self.logging = LoggingSettings()
        self.features = FeatureSettings()
        
        logger.info("Settings reset to defaults")


# Global settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get singleton settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

def reload_settings():
    """Reload settings from file"""
    global _settings_instance
    if _settings_instance:
        _settings_instance.load()
        
def save_settings():
    """Save current settings"""
    global _settings_instance
    if _settings_instance:
        _settings_instance.save()