"""
API routes for the Westfall Personal Assistant web application.

This module contains all API endpoint definitions.
"""

from flask import Blueprint, jsonify, request

# Import core modules
try:
    from core.assistant import get_assistant_core
except ImportError:
    def get_assistant_core():
        return None

# Import services with graceful fallback
try:
    from services.weather_service import WeatherWindow
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    WeatherWindow = None
    WEATHER_SERVICE_AVAILABLE = False

try:
    from services.news_service import NewsImageLoader
    NEWS_SERVICE_AVAILABLE = True
except ImportError:
    NewsImageLoader = None
    NEWS_SERVICE_AVAILABLE = False

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'Westfall Personal Assistant API'})

@api_bp.route('/assistant/status')
def assistant_status():
    """Get assistant status."""
    try:
        assistant = get_assistant_core()
        if assistant is None:
            return jsonify({'status': 'error', 'message': 'Assistant not available'}), 503
        
        status = assistant.get_status()
        return jsonify({'status': 'success', 'data': status})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/assistant/message', methods=['POST'])
def process_message():
    """Process a message through the assistant."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'status': 'error', 'message': 'Message is required'}), 400
        
        assistant = get_assistant_core()
        if assistant is None:
            return jsonify({'status': 'error', 'message': 'Assistant not available'}), 503
        
        response = assistant.process_message(message)
        
        return jsonify({'status': 'success', 'response': response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/weather')
def get_weather():
    """Get weather information."""
    try:
        if not WEATHER_SERVICE_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'Weather service not available - requires desktop application components'
            }), 503
        
        # This would integrate with the weather service
        # For now, return a placeholder response
        return jsonify({
            'status': 'success',
            'message': 'Weather service integration available via desktop application'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/news')
def get_news():
    """Get news information."""
    try:
        if not NEWS_SERVICE_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'News service not available - requires desktop application components'
            }), 503
        
        # This would integrate with the news service
        # For now, return a placeholder response
        return jsonify({
            'status': 'success',
            'message': 'News service integration available via desktop application'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500