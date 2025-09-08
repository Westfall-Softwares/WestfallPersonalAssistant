"""
Westfall Personal Assistant Security Enhancements
Advanced security features for enterprise-grade protection
"""

import os
import ssl
import hashlib
import hmac
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import requests
from urllib.parse import urlparse

class SecurityManager:
    """
    Comprehensive security management for Westfall Personal Assistant
    """
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.westfall_assistant/security"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Security configuration
        self.master_key = None
        self.encryption_key = None
        self.certificate_store = {}
        self.pinned_certificates = {}
        
        # Security monitoring
        self.security_events = []
        self.failed_attempts = {}
        self.rate_limits = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize security components
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security components"""
        try:
            self._load_security_configuration()
            self._setup_certificate_pinning()
            self._initialize_encryption()
        except Exception as e:
            logging.error(f"Security initialization failed: {e}")
    
    def _load_security_configuration(self):
        """Load security configuration from secure storage"""
        config_file = self.config_dir / "security_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.pinned_certificates = config.get('pinned_certificates', {})
                self.rate_limits = config.get('rate_limits', {
                    'api_requests': {'limit': 1000, 'window': 3600},
                    'login_attempts': {'limit': 5, 'window': 900}
                })
            except Exception as e:
                logging.error(f"Failed to load security config: {e}")
    
    def _setup_certificate_pinning(self):
        """Set up certificate pinning for secure connections"""
        # Default pinned certificates for known APIs
        default_pins = {
            'api.openai.com': [
                '308201b23082017a02010030819f300d06092a864886f70d010101050003818d0030818902818100',  # Example
            ],
            'api.westfall.app': [
                '308201b23082017a02010030819f300d06092a864886f70d010101050003818d0030818902818100',  # Example
            ]
        }
        
        for domain, pins in default_pins.items():
            if domain not in self.pinned_certificates:
                self.pinned_certificates[domain] = pins
    
    def _initialize_encryption(self):
        """Initialize encryption system with key rotation"""
        key_file = self.config_dir / "master.key"
        
        if not key_file.exists():
            # Generate new master key
            self.master_key = Fernet.generate_key()
            
            # Save encrypted master key
            self._save_master_key(self.master_key)
        else:
            # Load existing master key
            self.master_key = self._load_master_key()
        
        # Initialize encryption cipher
        self.encryption_key = Fernet(self.master_key)
    
    def _save_master_key(self, key: bytes):
        """Save master key with additional protection"""
        key_file = self.config_dir / "master.key"
        
        # Additional password-based encryption for the master key
        password = os.environ.get('WESTFALL_MASTER_PASSWORD', 'default_password').encode()
        salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(password))
        cipher = Fernet(derived_key)
        
        encrypted_key = cipher.encrypt(key)
        
        # Save with salt
        with open(key_file, 'wb') as f:
            f.write(salt + encrypted_key)
        
        # Set secure file permissions
        os.chmod(key_file, 0o600)
    
    def _load_master_key(self) -> bytes:
        """Load and decrypt master key"""
        key_file = self.config_dir / "master.key"
        
        with open(key_file, 'rb') as f:
            data = f.read()
        
        salt = data[:16]
        encrypted_key = data[16:]
        
        # Derive decryption key
        password = os.environ.get('WESTFALL_MASTER_PASSWORD', 'default_password').encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(password))
        cipher = Fernet(derived_key)
        
        return cipher.decrypt(encrypted_key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.encryption_key:
            raise RuntimeError("Encryption not initialized")
        
        encrypted_bytes = self.encryption_key.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.encryption_key:
            raise RuntimeError("Encryption not initialized")
        
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = self.encryption_key.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    
    def verify_certificate_pin(self, hostname: str, certificate: bytes) -> bool:
        """Verify certificate against pinned certificates"""
        pins = self.pinned_certificates.get(hostname)
        if not pins:
            # No pins configured for this hostname - allow connection but log
            self._log_security_event('no_pin_configured', {'hostname': hostname})
            return True
        
        # Calculate certificate fingerprint
        cert_hash = hashlib.sha256(certificate).hexdigest()
        
        if cert_hash in pins:
            return True
        
        # Certificate pin mismatch - security violation
        self._log_security_event('certificate_pin_mismatch', {
            'hostname': hostname,
            'expected_pins': pins,
            'actual_hash': cert_hash
        })
        
        return False
    
    def create_secure_session(self, hostname: str) -> requests.Session:
        """Create a secure requests session with certificate pinning"""
        session = requests.Session()
        
        # Configure SSL context
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Add certificate verification callback
        original_verify = session.verify
        
        def verify_with_pinning(request, *args, **kwargs):
            # Perform standard verification
            response = original_verify(request, *args, **kwargs)
            
            # Additional certificate pinning check
            if hasattr(response, 'raw') and hasattr(response.raw, 'peer_cert'):
                cert_der = response.raw.peer_cert
                if not self.verify_certificate_pin(hostname, cert_der):
                    raise ssl.SSLError(f"Certificate pin mismatch for {hostname}")
            
            return response
        
        session.verify = verify_with_pinning
        return session
    
    def check_rate_limit(self, operation: str, identifier: str = 'default') -> bool:
        """Check if operation is within rate limits"""
        with self._lock:
            now = datetime.now()
            
            rate_config = self.rate_limits.get(operation, {'limit': 100, 'window': 3600})
            limit = rate_config['limit']
            window = rate_config['window']
            
            # Initialize tracking for this operation/identifier
            key = f"{operation}:{identifier}"
            if key not in self.failed_attempts:
                self.failed_attempts[key] = []
            
            # Clean old attempts outside the window
            cutoff_time = now - timedelta(seconds=window)
            self.failed_attempts[key] = [
                attempt for attempt in self.failed_attempts[key]
                if attempt > cutoff_time
            ]
            
            # Check if limit exceeded
            if len(self.failed_attempts[key]) >= limit:
                self._log_security_event('rate_limit_exceeded', {
                    'operation': operation,
                    'identifier': identifier,
                    'attempts': len(self.failed_attempts[key]),
                    'limit': limit
                })
                return False
            
            # Record this attempt
            self.failed_attempts[key].append(now)
            return True
    
    def detect_suspicious_activity(self, user_id: str, activity: Dict[str, Any]) -> bool:
        """Detect suspicious user activity patterns"""
        suspicious_indicators = []
        
        # Check for unusual login patterns
        if activity.get('type') == 'login':
            location = activity.get('location', {})
            if self._is_unusual_location(user_id, location):
                suspicious_indicators.append('unusual_location')
            
            if self._is_unusual_time(user_id, activity.get('timestamp')):
                suspicious_indicators.append('unusual_time')
        
        # Check for rapid API requests
        if activity.get('type') == 'api_request':
            if self._is_rapid_requests(user_id, activity.get('timestamp')):
                suspicious_indicators.append('rapid_requests')
        
        # Check for privilege escalation attempts
        if activity.get('type') == 'permission_request':
            if self._is_privilege_escalation(user_id, activity.get('requested_permissions')):
                suspicious_indicators.append('privilege_escalation')
        
        if suspicious_indicators:
            self._log_security_event('suspicious_activity', {
                'user_id': user_id,
                'activity': activity,
                'indicators': suspicious_indicators
            })
            return True
        
        return False
    
    def _is_unusual_location(self, user_id: str, location: Dict[str, Any]) -> bool:
        """Check if login location is unusual for user"""
        # Simplified implementation - in reality would use ML models
        # and historical location data
        return False
    
    def _is_unusual_time(self, user_id: str, timestamp: datetime) -> bool:
        """Check if login time is unusual for user"""
        # Simplified implementation - check if outside normal hours
        hour = timestamp.hour
        return hour < 6 or hour > 22  # Outside 6 AM - 10 PM
    
    def _is_rapid_requests(self, user_id: str, timestamp: datetime) -> bool:
        """Check for suspiciously rapid API requests"""
        # Simplified implementation
        return False
    
    def _is_privilege_escalation(self, user_id: str, requested_permissions: List[str]) -> bool:
        """Check for privilege escalation attempts"""
        # Simplified implementation
        high_privilege_permissions = ['admin', 'system', 'delete_all']
        return any(perm in high_privilege_permissions for perm in requested_permissions)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')[:length]
    
    def create_api_key_hash(self, api_key: str, salt: str = None) -> Tuple[str, str]:
        """Create secure hash of API key for storage"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for key stretching
        key_bytes = api_key.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', key_bytes, salt_bytes, 100000)
        key_hash = base64.urlsafe_b64encode(hash_obj).decode('utf-8')
        
        return key_hash, salt
    
    def verify_api_key_hash(self, api_key: str, stored_hash: str, salt: str) -> bool:
        """Verify API key against stored hash"""
        calculated_hash, _ = self.create_api_key_hash(api_key, salt)
        return hmac.compare_digest(calculated_hash, stored_hash)
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for monitoring and analysis"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }
        
        self.security_events.append(event)
        
        # Log to system logger
        logging.warning(f"Security event: {event_type} - {details}")
        
        # Keep only recent events in memory (last 1000)
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > last_24h
        ]
        
        event_counts = {}
        for event in recent_events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'report_timestamp': now.isoformat(),
            'total_events_24h': len(recent_events),
            'event_breakdown': event_counts,
            'pinned_certificates': len(self.pinned_certificates),
            'rate_limit_violations': event_counts.get('rate_limit_exceeded', 0),
            'suspicious_activities': event_counts.get('suspicious_activity', 0),
            'certificate_violations': event_counts.get('certificate_pin_mismatch', 0),
            'security_status': self._calculate_security_status()
        }
    
    def _calculate_security_status(self) -> str:
        """Calculate overall security status"""
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        critical_events = [
            event for event in recent_events
            if event['type'] in ['certificate_pin_mismatch', 'privilege_escalation', 'brute_force_detected']
        ]
        
        if critical_events:
            return 'CRITICAL'
        
        warning_events = [
            event for event in recent_events
            if event['type'] in ['suspicious_activity', 'rate_limit_exceeded']
        ]
        
        if len(warning_events) > 10:
            return 'WARNING'
        
        return 'NORMAL'
    
    def rotate_encryption_keys(self):
        """Rotate encryption keys for enhanced security"""
        with self._lock:
            try:
                # Generate new master key
                new_master_key = Fernet.generate_key()
                
                # Backup old key
                backup_file = self.config_dir / f"master_backup_{int(datetime.now().timestamp())}.key"
                old_key_file = self.config_dir / "master.key"
                
                if old_key_file.exists():
                    old_key_file.rename(backup_file)
                
                # Save new key
                self._save_master_key(new_master_key)
                
                # Update encryption key
                old_encryption_key = self.encryption_key
                self.master_key = new_master_key
                self.encryption_key = Fernet(new_master_key)
                
                self._log_security_event('key_rotation', {
                    'old_key_backed_up': str(backup_file),
                    'rotation_timestamp': datetime.now().isostring()
                })
                
                return True
                
            except Exception as e:
                self._log_security_event('key_rotation_failed', {'error': str(e)})
                return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Clean up old key backups"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        for backup_file in self.config_dir.glob("master_backup_*.key"):
            try:
                timestamp = int(backup_file.stem.split('_')[-1])
                backup_time = datetime.fromtimestamp(timestamp)
                
                if backup_time < cutoff_time:
                    backup_file.unlink()
                    self._log_security_event('backup_cleaned', {'file': str(backup_file)})
            except (ValueError, OSError) as e:
                logging.error(f"Failed to clean backup {backup_file}: {e}")


# Global security manager instance
_security_manager = None

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

# Decorator for secure API endpoints
def secure_endpoint(require_auth: bool = True, rate_limit: str = None):
    """Decorator for securing API endpoints"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            security_manager = get_security_manager()
            
            # Rate limiting
            if rate_limit:
                identifier = kwargs.get('user_id', 'anonymous')
                if not security_manager.check_rate_limit(rate_limit, identifier):
                    raise PermissionError("Rate limit exceeded")
            
            # Authentication check
            if require_auth:
                # Simplified auth check - implement proper authentication
                auth_token = kwargs.get('auth_token')
                if not auth_token:
                    raise PermissionError("Authentication required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator