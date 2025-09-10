"""
Settings Manager for Westfall Personal Assistant

Bridges the existing settings and security infrastructure to provide
a unified interface for the settings UI.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import requests

# Import existing infrastructure
from config.settings import get_settings, save_settings
try:
    from backend.security.api_key_vault import APIKeyVault
    from backend.security.auth_manager import AuthManager
    API_VAULT_AVAILABLE = True
except ImportError:
    API_VAULT_AVAILABLE = False

logger = logging.getLogger(__name__)


class SettingsManager:
    """Unified settings manager that bridges existing infrastructure."""
    
    def __init__(self):
        self.settings = get_settings()
        self.env_path = Path('.env')
        
        # Initialize API key vault if available
        self.api_vault = None
        if API_VAULT_AVAILABLE:
            try:
                # This would typically be initialized with proper encryption manager
                # For now, we'll work with the existing config system
                pass
            except Exception as e:
                logger.warning(f"API key vault not available: {e}")
    
    def get_all_settings(self, mask_sensitive: bool = True) -> Dict[str, Any]:
        """
        Get all settings with API keys masked if requested.
        
        Returns a flat dictionary of settings suitable for the UI.
        """
        settings_dict = {}
        
        # Weather settings from environment/config
        openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        settings_dict['OPENWEATHER_API_KEY'] = self._mask_if_needed(openweather_key, mask_sensitive)
        
        # News API settings
        newsapi_key = os.getenv('NEWSAPI_KEY', '')
        settings_dict['NEWSAPI_KEY'] = self._mask_if_needed(newsapi_key, mask_sensitive)
        
        # OpenAI settings from config
        settings_dict['OPENAI_API_KEY'] = self._mask_if_needed(self.settings.models.openai_api_key, mask_sensitive)
        settings_dict['OPENAI_DEFAULT_MODEL'] = self.settings.models.openai_default_model
        
        # Email settings from environment
        settings_dict['EMAIL_SMTP_HOST'] = os.getenv('EMAIL_SMTP_HOST', '')
        settings_dict['EMAIL_SMTP_PORT'] = os.getenv('EMAIL_SMTP_PORT', '587')
        settings_dict['EMAIL_USERNAME'] = os.getenv('EMAIL_USERNAME', '')
        settings_dict['EMAIL_PASSWORD'] = self._mask_if_needed(os.getenv('EMAIL_PASSWORD', ''), mask_sensitive)
        settings_dict['EMAIL_USE_TLS'] = os.getenv('EMAIL_USE_TLS', 'true')
        
        # Ollama settings
        settings_dict['OLLAMA_BASE_URL'] = self.settings.models.ollama_base_url
        settings_dict['OLLAMA_DEFAULT_MODEL'] = self.settings.models.ollama_default_model
        
        # Feature toggles
        settings_dict['ENABLE_VOICE'] = str(self.settings.voice.tts_enabled).lower()
        settings_dict['BUSINESS_FEATURES_ENABLED'] = str(self.settings.features.business_dashboard_enabled).lower()
        settings_dict['SCREEN_CAPTURE_ENABLED'] = str(self.settings.features.screen_capture_enabled).lower()
        settings_dict['WEB_SEARCH_ENABLED'] = str(self.settings.features.web_search_enabled).lower()
        
        # UI settings
        settings_dict['THEME_MODE'] = self.settings.ui.theme_mode.value
        settings_dict['ENABLE_ANIMATIONS'] = str(self.settings.ui.enable_animations).lower()
        
        # Security settings
        settings_dict['MAX_REQUESTS_PER_MINUTE'] = str(self.settings.security.max_requests_per_minute)
        settings_dict['CONTENT_FILTERING_ENABLED'] = str(self.settings.security.content_filtering_enabled).lower()
        
        return settings_dict
    
    def _mask_if_needed(self, value: str, mask: bool) -> str:
        """Mask sensitive data if requested."""
        if not value or not mask:
            return value
        if len(value) <= 4:
            return "••••"
        return value[:4] + "•" * max(0, len(value) - 4)
    
    def update_setting(self, key: str, value: str) -> bool:
        """
        Update a setting in the appropriate storage location.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle different types of settings
            if key in ['OPENAI_API_KEY', 'OPENAI_DEFAULT_MODEL']:
                # Update model settings
                if key == 'OPENAI_API_KEY':
                    self.settings.models.openai_api_key = value
                elif key == 'OPENAI_DEFAULT_MODEL':
                    self.settings.models.openai_default_model = value
                    
            elif key in ['OLLAMA_BASE_URL', 'OLLAMA_DEFAULT_MODEL']:
                # Update Ollama settings
                if key == 'OLLAMA_BASE_URL':
                    self.settings.models.ollama_base_url = value
                elif key == 'OLLAMA_DEFAULT_MODEL':
                    self.settings.models.ollama_default_model = value
                    
            elif key.startswith('EMAIL_'):
                # Update environment file for email settings
                self._update_env_file(key, value)
                
            elif key in ['OPENWEATHER_API_KEY', 'NEWSAPI_KEY']:
                # Update environment file for external API keys
                self._update_env_file(key, value)
                
            elif key == 'ENABLE_VOICE':
                self.settings.voice.tts_enabled = value.lower() == 'true'
                
            elif key == 'BUSINESS_FEATURES_ENABLED':
                self.settings.features.business_dashboard_enabled = value.lower() == 'true'
                
            elif key == 'SCREEN_CAPTURE_ENABLED':
                self.settings.features.screen_capture_enabled = value.lower() == 'true'
                
            elif key == 'WEB_SEARCH_ENABLED':
                self.settings.features.web_search_enabled = value.lower() == 'true'
                
            elif key == 'THEME_MODE':
                from config.settings import ThemeMode
                try:
                    self.settings.ui.theme_mode = ThemeMode(value.lower())
                except ValueError:
                    return False
                    
            elif key == 'ENABLE_ANIMATIONS':
                self.settings.ui.enable_animations = value.lower() == 'true'
                
            elif key == 'MAX_REQUESTS_PER_MINUTE':
                try:
                    self.settings.security.max_requests_per_minute = int(value)
                except ValueError:
                    return False
                    
            elif key == 'CONTENT_FILTERING_ENABLED':
                self.settings.security.content_filtering_enabled = value.lower() == 'true'
                
            else:
                logger.warning(f"Unknown setting key: {key}")
                return False
            
            # Save settings to file
            save_settings()
            logger.info(f"Setting '{key}' updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update setting '{key}': {e}")
            return False
    
    def _update_env_file(self, key: str, value: str):
        """Update or add a setting in the .env file."""
        try:
            env_content = []
            key_found = False
            
            # Read existing .env file if it exists
            if self.env_path.exists():
                with open(self.env_path, 'r') as f:
                    env_content = f.readlines()
            
            # Update existing key or prepare to add new one
            for i, line in enumerate(env_content):
                if line.strip().startswith(f"{key}="):
                    env_content[i] = f"{key}={value}\n"
                    key_found = True
                    break
            
            # Add new key if not found
            if not key_found:
                env_content.append(f"{key}={value}\n")
            
            # Write back to file
            with open(self.env_path, 'w') as f:
                f.writelines(env_content)
                
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            raise
    
    def test_api_key(self, service: str, api_key: Optional[str] = None) -> bool:
        """
        Test if an API key is valid for the specified service.
        
        Args:
            service: Service name (openweather, newsapi, openai)
            api_key: API key to test (uses stored key if None)
            
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            if service == 'openweather':
                key = api_key or os.getenv('OPENWEATHER_API_KEY')
                return self._test_openweather_key(key)
            elif service == 'newsapi':
                key = api_key or os.getenv('NEWSAPI_KEY')
                return self._test_newsapi_key(key)
            elif service == 'openai':
                key = api_key or self.settings.models.openai_api_key
                return self._test_openai_key(key)
            else:
                logger.warning(f"Unknown service for API key testing: {service}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing API key for {service}: {e}")
            return False
    
    def _test_openweather_key(self, api_key: str) -> bool:
        """Test OpenWeather API key."""
        if not api_key:
            return False
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": "London", "appid": api_key},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _test_newsapi_key(self, api_key: str) -> bool:
        """Test NewsAPI key."""
        if not api_key:
            return False
        try:
            response = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "us", "pageSize": 1},
                headers={"X-API-Key": api_key},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _test_openai_key(self, api_key: str) -> bool:
        """Test OpenAI API key."""
        if not api_key:
            return False
        try:
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured services."""
        services = {}
        
        # Check OpenWeather
        openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        services['openweather'] = {
            'configured': bool(openweather_key),
            'name': 'OpenWeather',
            'description': 'Weather information service'
        }
        
        # Check NewsAPI
        newsapi_key = os.getenv('NEWSAPI_KEY', '')
        services['newsapi'] = {
            'configured': bool(newsapi_key),
            'name': 'NewsAPI',
            'description': 'News and headlines service'
        }
        
        # Check OpenAI
        openai_key = self.settings.models.openai_api_key
        services['openai'] = {
            'configured': bool(openai_key),
            'name': 'OpenAI',
            'description': 'AI language model service'
        }
        
        # Check email configuration
        email_configured = all([
            os.getenv('EMAIL_SMTP_HOST'),
            os.getenv('EMAIL_USERNAME'),
            os.getenv('EMAIL_PASSWORD')
        ])
        services['email'] = {
            'configured': email_configured,
            'name': 'Email',
            'description': 'Email sending capability'
        }
        
        return services
    
    def reset_settings(self) -> bool:
        """Reset settings to defaults."""
        try:
            self.settings.reset_to_defaults()
            save_settings()
            logger.info("Settings reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False


# Global instance
_settings_manager_instance = None

def get_settings_manager() -> SettingsManager:
    """Get singleton settings manager instance."""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager()
    return _settings_manager_instance