"""
Security module for WestfallPersonalAssistant
Handles encryption, authentication, and secure storage
"""

from .encryption_manager import EncryptionManager, MasterPasswordDialog
from .api_key_vault import APIKeyVault

__all__ = ['EncryptionManager', 'MasterPasswordDialog', 'APIKeyVault']
__version__ = '1.0.0'
