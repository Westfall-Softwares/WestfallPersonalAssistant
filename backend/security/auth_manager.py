#!/usr/bin/env python3
"""
Authentication Manager for Westfall Personal Assistant

Handles master password authentication and session management.
"""

import bcrypt
import time
import os
from typing import Optional, Dict, Any
import logging
from .encryption import EncryptionManager

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication, master password, and session security."""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.path.expanduser("~/.westfall_assistant")
        self.auth_file = os.path.join(self.config_dir, "auth.dat")
        self.session_timeout = 30 * 60  # 30 minutes default
        self.last_activity = None
        self.is_authenticated = False
        self.master_password_hash = None
        self.encryption_manager = EncryptionManager()
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load existing auth data
        self._load_auth_data()
    
    def _load_auth_data(self):
        """Load authentication data from file."""
        if os.path.exists(self.auth_file):
            try:
                with open(self.auth_file, 'rb') as f:
                    self.master_password_hash = f.read()
                logger.info("Master password hash loaded")
            except Exception as e:
                logger.error(f"Failed to load auth data: {e}")
    
    def _save_auth_data(self):
        """Save authentication data to file."""
        try:
            with open(self.auth_file, 'wb') as f:
                f.write(self.master_password_hash)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.auth_file, 0o600)
            logger.info("Master password hash saved")
        except Exception as e:
            logger.error(f"Failed to save auth data: {e}")
            raise
    
    def has_master_password(self) -> bool:
        """Check if a master password is set."""
        return self.master_password_hash is not None
    
    def set_master_password(self, password: str) -> bool:
        """Set the master password."""
        try:
            # Generate salt and hash the password
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            self.master_password_hash = password_hash
            self._save_auth_data()
            
            logger.info("Master password set successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set master password: {e}")
            return False
    
    def verify_master_password(self, password: str) -> bool:
        """Verify the master password."""
        if not self.has_master_password():
            return False
        
        try:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), self.master_password_hash)
            if is_valid:
                self.is_authenticated = True
                self.last_activity = time.time()
                
                # Set up encryption key from password
                key, salt = self.encryption_manager.generate_key_from_password(password)
                self.encryption_manager.set_key(key)
                
                logger.info("Authentication successful")
            else:
                logger.warning("Authentication failed - invalid password")
            
            return is_valid
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Change the master password."""
        if not self.verify_master_password(old_password):
            return False
        
        return self.set_master_password(new_password)
    
    def is_session_valid(self) -> bool:
        """Check if the current session is still valid."""
        if not self.is_authenticated:
            return False
        
        if self.last_activity is None:
            return False
        
        if time.time() - self.last_activity > self.session_timeout:
            self.logout()
            return False
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp."""
        if self.is_authenticated:
            self.last_activity = time.time()
    
    def logout(self):
        """Logout and clear session data."""
        self.is_authenticated = False
        self.last_activity = None
        self.encryption_manager._key = None
        self.encryption_manager._fernet = None
        logger.info("User logged out")
    
    def auto_lock(self):
        """Automatically lock the application."""
        self.logout()
        logger.info("Application auto-locked due to inactivity")
    
    def set_session_timeout(self, timeout_minutes: int):
        """Set session timeout in minutes."""
        self.session_timeout = timeout_minutes * 60
        logger.info(f"Session timeout set to {timeout_minutes} minutes")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        return {
            "authenticated": self.is_authenticated,
            "has_master_password": self.has_master_password(),
            "session_valid": self.is_session_valid(),
            "last_activity": self.last_activity,
            "timeout_seconds": self.session_timeout
        }
    
    def require_authentication(self, func):
        """Decorator to require authentication for sensitive operations."""
        def wrapper(*args, **kwargs):
            if not self.is_session_valid():
                raise PermissionError("Authentication required")
            self.update_activity()
            return func(*args, **kwargs)
        return wrapper