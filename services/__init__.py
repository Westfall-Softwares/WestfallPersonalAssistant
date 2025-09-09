"""
Service modules for external integrations.

This package contains service modules that handle external API integrations
and third-party services like weather, news, email, etc.
"""

from .weather_service import WeatherWindow
from .news_service import NewsImageLoader, NewsCard
from .email_service import EmailService, get_email_service

__all__ = ['WeatherWindow', 'NewsImageLoader', 'NewsCard', 'EmailService', 'get_email_service']