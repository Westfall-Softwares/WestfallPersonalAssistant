"""
Application Configuration Module for Westfall Personal Assistant

This module provides a convenient interface for accessing configuration values
from environment variables and settings files. It acts as a wrapper around
the main settings system and ensures secure credential loading.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in the project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded environment variables from {env_path}")
except ImportError:
    logging.warning("python-dotenv not available. Environment variables will only be loaded from system environment.")

# Import the main settings system
from .settings import get_settings

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Application configuration manager that provides secure access to credentials
    and configuration values from environment variables and settings files.
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._cached_values = {}
    
    # =============================================================================
    # API Key Management
    # =============================================================================
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or settings."""
        return os.getenv('OPENAI_API_KEY') or self._settings.models.openai_api_key or None
    
    def get_openweather_api_key(self) -> Optional[str]:
        """Get OpenWeatherMap API key from environment."""
        return os.getenv('OPENWEATHER_API_KEY')
    
    def get_newsapi_key(self) -> Optional[str]:
        """Get NewsAPI key from environment."""
        return os.getenv('NEWSAPI_KEY')
    
    def has_required_api_keys(self) -> Dict[str, bool]:
        """Check which required API keys are available."""
        return {
            'openai': bool(self.get_openai_api_key()),
            'openweather': bool(self.get_openweather_api_key()),
            'newsapi': bool(self.get_newsapi_key()),
        }
    
    # =============================================================================
    # Email Configuration
    # =============================================================================
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration from environment variables."""
        return {
            'smtp_host': os.getenv('EMAIL_SMTP_HOST'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'imap_host': os.getenv('EMAIL_IMAP_HOST'),
            'imap_port': int(os.getenv('EMAIL_IMAP_PORT', '993')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('EMAIL_USE_SSL', 'true').lower() == 'true',
        }
    
    def has_email_config(self) -> bool:
        """Check if email configuration is available."""
        config = self.get_email_config()
        return bool(config['smtp_host'] and config['username'] and config['password'])
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    
    def get_database_url(self) -> str:
        """Get database URL from environment or settings."""
        return os.getenv('DATABASE_URL') or self._settings.memory.database_url
    
    def get_database_encryption_key(self) -> Optional[str]:
        """Get database encryption key from environment."""
        return os.getenv('DATABASE_ENCRYPTION_KEY')
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    
    def get_session_timeout(self) -> int:
        """Get session timeout in minutes."""
        return int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limiting configuration."""
        return {
            'max_requests_per_minute': int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60')),
            'max_tokens_per_hour': int(os.getenv('MAX_TOKENS_PER_HOUR', '100000')),
        }
    
    def get_api_key_vault_encryption_key(self) -> Optional[str]:
        """Get API key vault encryption key from environment."""
        return os.getenv('API_KEY_VAULT_ENCRYPTION_KEY')
    
    # =============================================================================
    # Feature Flags
    # =============================================================================
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    def is_testing_mode(self) -> bool:
        """Check if testing mode is enabled."""
        return os.getenv('TESTING_MODE', 'false').lower() == 'true'
    
    def use_mock_services(self) -> bool:
        """Check if mock services should be used."""
        return os.getenv('USE_MOCK_SERVICES', 'false').lower() == 'true'
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return {
            'business_features': os.getenv('BUSINESS_FEATURES_ENABLED', 'false').lower() == 'true',
            'crm': os.getenv('CRM_ENABLED', 'false').lower() == 'true',
            'finance_tracking': os.getenv('FINANCE_TRACKING_ENABLED', 'false').lower() == 'true',
            'time_tracking': os.getenv('TIME_TRACKING_ENABLED', 'false').lower() == 'true',
            'screen_capture': os.getenv('SCREEN_CAPTURE_ENABLED', 'false').lower() == 'true',
            'automation': os.getenv('AUTOMATION_ENABLED', 'false').lower() == 'true',
            'web_search': os.getenv('WEB_SEARCH_ENABLED', 'true').lower() == 'true',
        }
    
    # =============================================================================
    # Application Paths
    # =============================================================================
    
    def get_data_directory(self) -> Path:
        """Get data directory path."""
        data_dir = os.getenv('DATA_DIRECTORY', 'data')
        path = Path(data_dir)
        path.mkdir(exist_ok=True)
        return path
    
    def get_models_directory(self) -> Path:
        """Get models directory path."""
        models_dir = os.getenv('MODELS_DIRECTORY', 'models')
        path = Path(models_dir)
        path.mkdir(exist_ok=True)
        return path
    
    def get_backup_directory(self) -> Path:
        """Get backup directory path."""
        backup_dir = os.getenv('BACKUP_DIRECTORY', 'backups')
        path = Path(backup_dir)
        path.mkdir(exist_ok=True)
        return path
    
    def get_extensions_directory(self) -> Path:
        """Get extensions directory path."""
        ext_dir = os.getenv('EXTENSIONS_DIRECTORY', 'extensions')
        path = Path(ext_dir)
        path.mkdir(exist_ok=True)
        return path
    
    # =============================================================================
    # Validation and Security
    # =============================================================================
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration and return a report.
        
        Returns:
            Dictionary with validation results
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'api_keys': self.has_required_api_keys(),
            'email_configured': self.has_email_config(),
            'security_keys_present': {
                'database_encryption': bool(self.get_database_encryption_key()),
                'vault_encryption': bool(self.get_api_key_vault_encryption_key()),
            }
        }
        
        # Check for critical missing configurations
        if not any(report['api_keys'].values()):
            report['warnings'].append("No API keys configured. Some features will be unavailable.")
        
        if not report['email_configured']:
            report['warnings'].append("Email configuration missing. Email features will be unavailable.")
        
        if not report['security_keys_present']['vault_encryption']:
            report['warnings'].append("API key vault encryption key not set. Consider setting API_KEY_VAULT_ENCRYPTION_KEY.")
        
        return report
    
    def get_safe_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of configuration without exposing sensitive values.
        
        Returns:
            Dictionary with safe configuration summary
        """
        return {
            'api_keys_configured': [key for key, available in self.has_required_api_keys().items() if available],
            'email_configured': self.has_email_config(),
            'debug_mode': self.is_debug_mode(),
            'testing_mode': self.is_testing_mode(),
            'feature_flags': self.get_feature_flags(),
            'directories': {
                'data': str(self.get_data_directory()),
                'models': str(self.get_models_directory()),
                'backups': str(self.get_backup_directory()),
                'extensions': str(self.get_extensions_directory()),
            },
            'rate_limits': self.get_rate_limits(),
            'session_timeout': self.get_session_timeout(),
        }


# Global configuration instance
_app_config_instance = None

def get_app_config() -> AppConfig:
    """Get singleton application configuration instance."""
    global _app_config_instance
    if _app_config_instance is None:
        _app_config_instance = AppConfig()
    return _app_config_instance

def reload_app_config():
    """Reload application configuration."""
    global _app_config_instance
    _app_config_instance = None
    return get_app_config()

# Convenience functions for backward compatibility
def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key."""
    return get_app_config().get_openai_api_key()

def get_openweather_api_key() -> Optional[str]:
    """Get OpenWeatherMap API key."""
    return get_app_config().get_openweather_api_key()

def get_newsapi_key() -> Optional[str]:
    """Get NewsAPI key."""
    return get_app_config().get_newsapi_key()

def get_email_config() -> Dict[str, Any]:
    """Get email configuration."""
    return get_app_config().get_email_config()