"""
Web routes for the Westfall Personal Assistant web application.

This module contains all web page route definitions.
"""

from flask import Blueprint, render_template

# Import core modules with graceful fallback
try:
    from core.assistant import get_assistant_core
except ImportError:
    def get_assistant_core():
        return None

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Home page."""
    try:
        assistant = get_assistant_core()
        if assistant:
            status = assistant.get_status()
            return render_template('index.html', assistant_status=status)
        else:
            return render_template('index.html', assistant_status={'initialized': False})
    except Exception as e:
        return render_template('index.html', error=str(e))

@web_bp.route('/dashboard')
def dashboard():
    """Dashboard page."""
    try:
        assistant = get_assistant_core()
        if assistant:
            status = assistant.get_status()
            return render_template('dashboard.html', assistant_status=status)
        else:
            return render_template('dashboard.html', assistant_status={'initialized': False})
    except Exception as e:
        return render_template('dashboard.html', error=str(e))

@web_bp.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')

@web_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')