#!/usr/bin/env python3
"""
Encryption Manager for Westfall Personal Assistant

Provides AES-256 encryption for sensitive data using cryptography library.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handles AES-256 encryption for sensitive data."""
    
    def __init__(self):
        self._key = None
        self._fernet = None
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def set_key(self, key: bytes):
        """Set the encryption key."""
        self._key = key
        self._fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not self._fernet:
            raise ValueError("Encryption key not set")
        
        encrypted_data = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not self._fernet:
            raise ValueError("Encryption key not set")
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_file(self, file_path: str, output_path: str = None):
        """Encrypt a file."""
        if not self._fernet:
            raise ValueError("Encryption key not set")
        
        if output_path is None:
            output_path = file_path + ".encrypted"
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = self._fernet.encrypt(file_data)
        
        with open(output_path, 'wb') as file:
            file.write(encrypted_data)
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str = None):
        """Decrypt a file."""
        if not self._fernet:
            raise ValueError("Encryption key not set")
        
        if output_path is None:
            output_path = encrypted_file_path.replace(".encrypted", "")
        
        with open(encrypted_file_path, 'rb') as file:
            encrypted_data = file.read()
        
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            return output_path
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise ValueError("Failed to decrypt file")
    
    @staticmethod
    def generate_random_key() -> bytes:
        """Generate a random encryption key."""
        return Fernet.generate_key()