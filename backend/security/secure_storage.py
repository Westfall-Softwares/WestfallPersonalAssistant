#!/usr/bin/env python3
"""
Secure Storage for Westfall Personal Assistant

Provides encrypted SQLite database wrapper for secure data storage.
"""

import os
import sqlite3
import json
from typing import Any, Dict, List, Optional, Union
import logging
from contextlib import contextmanager
from .encryption import EncryptionManager

logger = logging.getLogger(__name__)


class SecureStorage:
    """Encrypted SQLite database wrapper for secure data storage."""
    
    def __init__(self, db_path: str, encryption_manager: EncryptionManager):
        self.db_path = db_path
        self.encryption_manager = encryption_manager
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create secure_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secure_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create password_entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    url TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service, username)
                )
            ''')
            
            # Create api_keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT UNIQUE NOT NULL,
                    api_key TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create conversation_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    thinking_mode TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _encrypt_data(self, data: Any) -> str:
        """Encrypt data for storage."""
        if data is None:
            return None
        
        json_data = json.dumps(data) if not isinstance(data, str) else data
        return self.encryption_manager.encrypt(json_data)
    
    def _decrypt_data(self, encrypted_data: str, is_json: bool = False) -> Any:
        """Decrypt data from storage."""
        if encrypted_data is None:
            return None
        
        try:
            decrypted = self.encryption_manager.decrypt(encrypted_data)
            return json.loads(decrypted) if is_json else decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return None
    
    # Settings Management
    def set_setting(self, key: str, value: Any):
        """Store an encrypted setting."""
        encrypted_value = self._encrypt_data(value)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO secure_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, encrypted_value))
            conn.commit()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve and decrypt a setting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM secure_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                return self._decrypt_data(row['value'], is_json=True)
            return default
    
    def delete_setting(self, key: str):
        """Delete a setting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM secure_settings WHERE key = ?', (key,))
            conn.commit()
    
    def list_settings(self) -> List[str]:
        """List all setting keys."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key FROM secure_settings ORDER BY key')
            return [row['key'] for row in cursor.fetchall()]
    
    # Password Manager
    def store_password(self, service: str, username: str, password: str, 
                      url: str = None, notes: str = None):
        """Store an encrypted password entry."""
        encrypted_password = self._encrypt_data(password)
        encrypted_notes = self._encrypt_data(notes) if notes else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO password_entries 
                (service, username, password, url, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (service, username, encrypted_password, url, encrypted_notes))
            conn.commit()
    
    def get_password(self, service: str, username: str = None) -> Optional[Dict]:
        """Retrieve and decrypt a password entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if username:
                cursor.execute('''
                    SELECT * FROM password_entries 
                    WHERE service = ? AND username = ?
                ''', (service, username))
            else:
                cursor.execute('''
                    SELECT * FROM password_entries 
                    WHERE service = ? ORDER BY updated_at DESC LIMIT 1
                ''', (service,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'service': row['service'],
                    'username': row['username'],
                    'password': self._decrypt_data(row['password']),
                    'url': row['url'],
                    'notes': self._decrypt_data(row['notes']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
    
    def list_passwords(self) -> List[Dict]:
        """List all password entries (without actual passwords)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, service, username, url, created_at, updated_at 
                FROM password_entries ORDER BY service, username
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_password(self, service: str, username: str = None):
        """Delete a password entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if username:
                cursor.execute('''
                    DELETE FROM password_entries 
                    WHERE service = ? AND username = ?
                ''', (service, username))
            else:
                cursor.execute('''
                    DELETE FROM password_entries WHERE service = ?
                ''', (service,))
            
            conn.commit()
    
    # Conversation History
    def store_conversation(self, conversation_id: str, message_type: str, 
                          content: str, thinking_mode: str = None, metadata: Dict = None):
        """Store encrypted conversation history."""
        encrypted_content = self._encrypt_data(content)
        encrypted_metadata = self._encrypt_data(metadata) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_history 
                (conversation_id, message_type, content, thinking_mode, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (conversation_id, message_type, encrypted_content, thinking_mode, encrypted_metadata))
            conn.commit()
    
    def get_conversation_history(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """Retrieve and decrypt conversation history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM conversation_history 
                WHERE conversation_id = ? 
                ORDER BY timestamp DESC LIMIT ?
            ''', (conversation_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'conversation_id': row['conversation_id'],
                    'message_type': row['message_type'],
                    'content': self._decrypt_data(row['content']),
                    'thinking_mode': row['thinking_mode'],
                    'timestamp': row['timestamp'],
                    'metadata': self._decrypt_data(row['metadata'], is_json=True)
                })
            
            return list(reversed(history))  # Return in chronological order
    
    def delete_conversation_history(self, conversation_id: str = None):
        """Delete conversation history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if conversation_id:
                cursor.execute('''
                    DELETE FROM conversation_history WHERE conversation_id = ?
                ''', (conversation_id,))
            else:
                cursor.execute('DELETE FROM conversation_history')
            
            conn.commit()
    
    # Data Export/Import
    def export_data(self) -> Dict:
        """Export all data in encrypted format."""
        data = {
            'settings': {},
            'passwords': [],
            'conversations': []
        }
        
        # Export settings
        for key in self.list_settings():
            data['settings'][key] = self.get_setting(key)
        
        # Export passwords
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM password_entries')
            for row in cursor.fetchall():
                data['passwords'].append({
                    'service': row['service'],
                    'username': row['username'],
                    'password': self._decrypt_data(row['password']),
                    'url': row['url'],
                    'notes': self._decrypt_data(row['notes']),
                    'created_at': row['created_at']
                })
        
        return data
    
    def backup_database(self, backup_path: str):
        """Create encrypted backup of the database."""
        import shutil
        
        # Create backup of the database file
        backup_db_path = backup_path + ".db"
        shutil.copy2(self.db_path, backup_db_path)
        
        # Encrypt the backup
        encrypted_backup = self.encryption_manager.encrypt_file(backup_db_path, backup_path)
        
        # Remove unencrypted backup
        os.remove(backup_db_path)
        
        logger.info(f"Database backup created: {encrypted_backup}")
        return encrypted_backup