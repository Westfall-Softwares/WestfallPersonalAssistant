import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.encryption_manager import EncryptionManager

def test_encryption():
    manager = EncryptionManager()
    
    # Test string encryption
    original = "test_password_123"
    encrypted = manager.encrypt(original)
    decrypted = manager.decrypt(encrypted)
    
    assert decrypted == original
    assert encrypted != original

def test_password_hashing():
    manager = EncryptionManager()
    
    password = "MySecurePassword123!"
    hash1 = manager.hash_password(password)
    hash2 = manager.hash_password(password)
    
    assert hash1 == hash2
    assert hash1 != password