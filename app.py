#!/usr/bin/env python3
"""
Westfall Personal Assistant - Main Application Entry Point

This is the main entry point for the Flask application as specified in the reorganization.
This serves as the web interface entry point, separate from the main.py PyQt5 desktop application.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask
from config.settings import get_settings
from utils.logger import setup_logging

# Import routes
from routes.api_routes import api_bp
from routes.web_routes import web_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load settings
    settings = get_settings()
    app.config.update(settings.get('flask', {}))
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Westfall Personal Assistant Web Application")
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(web_bp, url_prefix='/')
    
    return app

def main():
    """Main entry point for the web application."""
    app = create_app()
    
    # Get configuration
    settings = get_settings()
    flask_config = settings.get('flask', {})
    
    host = flask_config.get('host', '127.0.0.1')
    port = flask_config.get('port', 5000)
    debug = flask_config.get('debug', False)
    
    print(f"Starting Flask web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()