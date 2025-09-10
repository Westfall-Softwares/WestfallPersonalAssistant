"""
API routes for the Westfall Personal Assistant web application.

This module contains all API endpoint definitions with comprehensive
input validation and security features.
"""

import logging
from functools import wraps
from flask import Blueprint, jsonify, request
from typing import Dict, Any, Optional

# Import security and validation modules
try:
    from backend.security.input_validation import input_validator, ValidationError
    INPUT_VALIDATION_AVAILABLE = True
except ImportError:
    INPUT_VALIDATION_AVAILABLE = False
    class ValidationError(Exception):
        pass

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

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


def validate_request_data(required_fields: Dict[str, type] = None, 
                         optional_fields: Dict[str, type] = None,
                         max_content_length: int = 10000):
    """
    Decorator for validating request data with comprehensive input validation.
    
    Args:
        required_fields: Dictionary of required field names and their expected types
        optional_fields: Dictionary of optional field names and their expected types
        max_content_length: Maximum allowed content length
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check content length
                if request.content_length and request.content_length > max_content_length:
                    return jsonify({
                        'status': 'error', 
                        'message': f'Request too large. Maximum size: {max_content_length} bytes'
                    }), 413
                
                # Validate JSON structure if POST/PUT request
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        data = request.get_json()
                        if data is None:
                            return jsonify({
                                'status': 'error', 
                                'message': 'Invalid JSON or missing Content-Type header'
                            }), 400
                    except Exception:
                        return jsonify({
                            'status': 'error', 
                            'message': 'Invalid JSON format'
                        }), 400
                    
                    # Validate required fields
                    if required_fields:
                        for field_name, field_type in required_fields.items():
                            if field_name not in data:
                                return jsonify({
                                    'status': 'error', 
                                    'message': f'Missing required field: {field_name}'
                                }), 400
                            
                            if not isinstance(data[field_name], field_type):
                                return jsonify({
                                    'status': 'error', 
                                    'message': f'Field {field_name} must be of type {field_type.__name__}'
                                }), 400
                            
                            # Additional validation using security module
                            if INPUT_VALIDATION_AVAILABLE:
                                try:
                                    if field_type == str:
                                        data[field_name] = input_validator.sanitize_string(
                                            data[field_name], max_length=1000
                                        )
                                except ValidationError as ve:
                                    return jsonify({
                                        'status': 'error', 
                                        'message': f'Validation error in {field_name}: {str(ve)}'
                                    }), 400
                    
                    # Validate optional fields
                    if optional_fields:
                        for field_name, field_type in optional_fields.items():
                            if field_name in data:
                                if not isinstance(data[field_name], field_type):
                                    return jsonify({
                                        'status': 'error', 
                                        'message': f'Field {field_name} must be of type {field_type.__name__}'
                                    }), 400
                                
                                # Additional validation using security module
                                if INPUT_VALIDATION_AVAILABLE and field_type == str:
                                    try:
                                        data[field_name] = input_validator.sanitize_string(
                                            data[field_name], max_length=1000
                                        )
                                    except ValidationError as ve:
                                        return jsonify({
                                            'status': 'error', 
                                            'message': f'Validation error in {field_name}: {str(ve)}'
                                        }), 400
                
                # Validate query parameters
                if INPUT_VALIDATION_AVAILABLE:
                    for param_name, param_value in request.args.items():
                        try:
                            input_validator.sanitize_string(param_value, max_length=100)
                        except ValidationError as ve:
                            return jsonify({
                                'status': 'error', 
                                'message': f'Invalid query parameter {param_name}: {str(ve)}'
                            }), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error in {f.__name__}: {str(e)}")
                return jsonify({
                    'status': 'error', 
                    'message': 'Internal validation error'
                }), 500
        
        return decorated_function
    return decorator


def handle_errors(f):
    """Decorator for consistent error handling across all endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as ve:
            logger.warning(f"Validation error in {f.__name__}: {str(ve)}")
            return jsonify({
                'status': 'error', 
                'message': f'Validation error: {str(ve)}'
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error', 
                'message': 'Internal server error'
            }), 500
    
    return decorated_function


@api_bp.route('/health')
@handle_errors
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'Westfall Personal Assistant API'})


@api_bp.route('/assistant/status')
@handle_errors
def assistant_status():
    """Get assistant status."""
    assistant = get_assistant_core()
    if assistant is None:
        return jsonify({'status': 'error', 'message': 'Assistant not available'}), 503
    
    status = assistant.get_status()
    return jsonify({'status': 'success', 'data': status})


@api_bp.route('/assistant/message', methods=['POST'])
@validate_request_data(
    required_fields={'message': str}, 
    optional_fields={'context': str, 'session_id': str},
    max_content_length=5000
)
@handle_errors
def process_message():
    """Process a message through the assistant."""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    # Additional message validation
    if len(message) < 1:
        return jsonify({'status': 'error', 'message': 'Message cannot be empty'}), 400
    
    if len(message) > 2000:
        return jsonify({'status': 'error', 'message': 'Message too long (max 2000 characters)'}), 400
    
    # Validate message content using security module
    if INPUT_VALIDATION_AVAILABLE:
        try:
            message = input_validator.sanitize_string(message, max_length=2000)
            # Additional checks for suspicious content
            if input_validator.contains_suspicious_patterns(message):
                logger.warning(f"Suspicious message detected: {message[:50]}...")
                return jsonify({
                    'status': 'error', 
                    'message': 'Message contains potentially unsafe content'
                }), 400
        except ValidationError as ve:
            return jsonify({'status': 'error', 'message': str(ve)}), 400
    
    assistant = get_assistant_core()
    if assistant is None:
        return jsonify({'status': 'error', 'message': 'Assistant not available'}), 503
    
    # Process optional context
    context = data.get('context', '')
    if context and INPUT_VALIDATION_AVAILABLE:
        try:
            context = input_validator.sanitize_string(context, max_length=1000)
        except ValidationError:
            context = ''  # Ignore invalid context
    
    response = assistant.process_message(message, context=context)
    
    return jsonify({'status': 'success', 'response': response})


@api_bp.route('/weather')
@validate_request_data(
    optional_fields={'location': str, 'units': str},
    max_content_length=1000
)
@handle_errors
def get_weather():
    """Get weather information."""
    if not WEATHER_SERVICE_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'Weather service not available - requires desktop application components'
        }), 503
    
    # Validate location parameter
    location = request.args.get('location', '').strip()
    if location and INPUT_VALIDATION_AVAILABLE:
        try:
            location = input_validator.sanitize_string(location, max_length=100)
            # Additional validation for location format
            if not input_validator.is_safe_string(location):
                return jsonify({
                    'status': 'error', 
                    'message': 'Invalid location format'
                }), 400
        except ValidationError as ve:
            return jsonify({'status': 'error', 'message': str(ve)}), 400
    
    # Validate units parameter
    units = request.args.get('units', 'metric').lower()
    if units not in ['metric', 'imperial', 'kelvin']:
        return jsonify({
            'status': 'error', 
            'message': 'Invalid units. Use: metric, imperial, or kelvin'
        }), 400
    
    # This would integrate with the weather service
    # For now, return a placeholder response
    return jsonify({
        'status': 'success',
        'message': 'Weather service integration available via desktop application',
        'location': location if location else 'default',
        'units': units
    })


@api_bp.route('/news')
@validate_request_data(
    optional_fields={'category': str, 'limit': int, 'source': str},
    max_content_length=1000
)
@handle_errors
def get_news():
    """Get news information."""
    if not NEWS_SERVICE_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'News service not available - requires desktop application components'
        }), 503
    
    # Validate category parameter
    category = request.args.get('category', '').lower()
    valid_categories = ['business', 'technology', 'sports', 'entertainment', 'health', 'science', 'general']
    if category and category not in valid_categories:
        return jsonify({
            'status': 'error', 
            'message': f'Invalid category. Valid categories: {", ".join(valid_categories)}'
        }), 400
    
    # Validate limit parameter
    try:
        limit = int(request.args.get('limit', '10'))
        if limit < 1 or limit > 100:
            return jsonify({
                'status': 'error', 
                'message': 'Limit must be between 1 and 100'
            }), 400
    except ValueError:
        return jsonify({
            'status': 'error', 
            'message': 'Limit must be a valid integer'
        }), 400
    
    # Validate source parameter
    source = request.args.get('source', '').strip()
    if source and INPUT_VALIDATION_AVAILABLE:
        try:
            source = input_validator.sanitize_string(source, max_length=50)
        except ValidationError as ve:
            return jsonify({'status': 'error', 'message': str(ve)}), 400
    
    # This would integrate with the news service
    # For now, return a placeholder response
    return jsonify({
        'status': 'success',
        'message': 'News service integration available via desktop application',
        'category': category if category else 'general',
        'limit': limit,
        'source': source if source else 'all'
    })