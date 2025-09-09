"""
Routes package for the Flask web application.

This package contains all route definitions for both web and API endpoints.
"""

from .api_routes import api_bp
from .web_routes import web_bp

__all__ = ["api_bp", "web_bp"]
