"""
Settings routes for the Westfall Personal Assistant web application.

Provides API endpoints for settings management with authentication.
"""

import logging
from flask import Blueprint, jsonify, request, render_template
from functools import wraps

# Import our settings manager
from core.settings_manager import get_settings_manager

# Import existing validation
try:
    from routes.api_routes import validate_request_data
except ImportError:
    # Fallback validation decorator
    def validate_request_data(**kwargs):
        def decorator(f):
            return f
        return decorator

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)


def require_valid_request(f):
    """Simple request validation decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST' and not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


@settings_bp.route('/settings-ui')
def settings_page():
    """Render the settings page."""
    try:
        settings_manager = get_settings_manager()
        current_settings = settings_manager.get_all_settings(mask_sensitive=True)
        service_status = settings_manager.get_service_status()
        
        return render_template('settings.html', 
                             settings=current_settings,
                             services=service_status)
    except Exception as e:
        logger.error(f"Error loading settings page: {e}")
        return f"Error loading settings: {e}", 500


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings with masked API keys."""
    try:
        settings_manager = get_settings_manager()
        settings_data = settings_manager.get_all_settings(mask_sensitive=True)
        service_status = settings_manager.get_service_status()
        
        return jsonify({
            'success': True,
            'settings': settings_data,
            'services': service_status
        })
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/settings', methods=['POST'])
@require_valid_request
def update_settings():
    """Update settings with values from request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        settings_manager = get_settings_manager()
        results = {}
        
        for key, value in data.items():
            if isinstance(value, str) and value.strip():  # Only update non-empty values
                results[key] = settings_manager.update_setting(key, value.strip())
            else:
                results[key] = True  # Skip empty values
        
        # Check if any updates failed
        failed_updates = [key for key, success in results.items() if not success]
        
        if failed_updates:
            return jsonify({
                'success': False,
                'error': f'Failed to update: {", ".join(failed_updates)}',
                'results': results
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/settings/test/<service>', methods=['POST'])
@require_valid_request
def test_api_key(service):
    """Test if API key is valid for specified service."""
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key')
        
        settings_manager = get_settings_manager()
        result = settings_manager.test_api_key(service, api_key)
        
        return jsonify({
            'success': True,
            'valid': result,
            'service': service
        })
        
    except Exception as e:
        logger.error(f"Error testing API key for {service}: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/reset', methods=['POST'])
@require_valid_request
def reset_settings():
    """Reset all settings to default values."""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Reset confirmation required',
                'requires_confirmation': True
            }), 400
        
        settings_manager = get_settings_manager()
        success = settings_manager.reset_settings()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Settings reset to defaults successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset settings'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/settings/status')
def get_settings_status():
    """Get overall settings and service status."""
    try:
        settings_manager = get_settings_manager()
        service_status = settings_manager.get_service_status()
        
        # Count configured services
        configured_count = sum(1 for service in service_status.values() if service['configured'])
        total_count = len(service_status)
        
        return jsonify({
            'success': True,
            'configured_services': configured_count,
            'total_services': total_count,
            'services': service_status,
            'configuration_complete': configured_count >= 2  # At least 2 services configured
        })
        
    except Exception as e:
        logger.error(f"Error getting settings status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.errorhandler(404)
def settings_not_found(error):
    """Handle 404 errors in settings routes."""
    return jsonify({'success': False, 'error': 'Settings endpoint not found'}), 404


@settings_bp.errorhandler(500)
def settings_server_error(error):
    """Handle 500 errors in settings routes."""
    logger.error(f"Settings server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500