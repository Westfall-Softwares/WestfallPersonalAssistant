"""
API routes for the Westfall Personal Assistant web application.

This module contains all API endpoint definitions.
"""

from flask import Blueprint, jsonify, request
from core.assistant import get_assistant_core
from services.weather_service import WeatherWindow
from services.news_service import NewsImageLoader

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
        response = assistant.process_message(message)
        
        return jsonify({'status': 'success', 'response': response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/weather')
def get_weather():
    """Get weather information."""
    try:
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
        # This would integrate with the news service
        # For now, return a placeholder response
        return jsonify({
            'status': 'success',
            'message': 'News service integration available via desktop application'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500