"""
Service modules for external integrations.

This package contains service modules that handle external API integrations
and third-party services like weather, news, email, etc.
"""

# Import email service (no PyQt5 dependency)
from .email_service import EmailService, get_email_service

# Import GUI services with graceful fallback
try:
    from .weather_service import WeatherWindow
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    WeatherWindow = None
    WEATHER_SERVICE_AVAILABLE = False

try:
    from .news_service import NewsImageLoader, NewsCard
    NEWS_SERVICE_AVAILABLE = True
except ImportError:
    NewsImageLoader = None
    NewsCard = None
    NEWS_SERVICE_AVAILABLE = False

__all__ = ['EmailService', 'get_email_service']

# Add GUI services to exports if available
if WEATHER_SERVICE_AVAILABLE:
    __all__.append('WeatherWindow')
if NEWS_SERVICE_AVAILABLE:
    __all__.extend(['NewsImageLoader', 'NewsCard'])