"""
Database module for Westfall Personal Assistant

Enhanced database architecture with SQLAlchemy ORM and migration support.
"""

from .models import Base, User, Conversation, Message, Setting, PasswordEntry, APIKey
from .backup_manager import BackupManager
from .sync_manager import SyncManager

__all__ = ['Base', 'User', 'Conversation', 'Message', 'Setting', 'PasswordEntry', 'APIKey', 'BackupManager', 'SyncManager']