"""
Service modules for external integrations.

This package contains service modules that handle external API integrations
and third-party services like weather, news, email, etc.
"""

from .weather_service import WeatherWindow
from .news_service import NewsImageLoader, NewsCard

__all__ = ['WeatherWindow', 'NewsImageLoader', 'NewsCard']