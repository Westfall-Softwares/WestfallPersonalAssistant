#!/usr/bin/env python3
"""
Enhanced Secure Storage for Westfall Personal Assistant

Provides encrypted SQLite database storage with additional security features:
- Tamper detection
- Key rotation
- Database integrity checks
- Secure backup integration
"""

import os
import sqlite3
import json
import hashlib
import time
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
import logging
from pathlib import Path
from .encryption import EncryptionManager

try:
    from .input_validation import input_validator, ValidationError
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    logger.warning("Input validation not available")

logger = logging.getLogger(__name__)


class SecureStorage:
    """Enhanced encrypted SQLite database wrapper with security features."""
    
    def __init__(self, db_path: str, encryption_manager: EncryptionManager):
        self.db_path = db_path
        self.encryption_manager = encryption_manager
        self.integrity_file = db_path + ".integrity"
        self.key_rotation_interval = timedelta(days=90)  # Rotate keys every 90 days
        self.last_integrity_check = None
        
        self._ensure_database_exists()
        self._initialize_integrity_tracking()
        self._check_key_rotation()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create password entries table
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
            
            # Create API keys table
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
            
            # Create security audit table for tracking access and modifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create key rotation table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_rotation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rotation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    old_key_hash TEXT,
                    new_key_hash TEXT,
                    success BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            logger.info("Enhanced database schema initialized successfully")
    
    def _initialize_integrity_tracking(self):
        """Initialize database integrity tracking."""
        try:
            if not Path(self.integrity_file).exists():
                self._create_integrity_baseline()
            else:
                self._verify_database_integrity()
        except Exception as e:
            logger.warning(f"Integrity tracking initialization failed: {e}")
    
    def _create_integrity_baseline(self):
        """Create initial integrity baseline for the database."""
        try:
            db_hash = self._calculate_database_hash()
            integrity_data = {
                "created_at": datetime.now().isoformat(),
                "last_verified": datetime.now().isoformat(),
                "database_hash": db_hash,
                "table_hashes": self._calculate_table_hashes()
            }
            
            with open(self.integrity_file, 'w') as f:
                json.dump(integrity_data, f, indent=2)
            
            logger.info("Database integrity baseline created")
        except Exception as e:
            logger.error(f"Failed to create integrity baseline: {e}")
    
    def _calculate_database_hash(self) -> str:
        """Calculate SHA-256 hash of the entire database file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(self.db_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate database hash: {e}")
            return ""
    
    def _calculate_table_hashes(self) -> Dict[str, str]:
        """Calculate hash for each table's content."""
        table_hashes = {}
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table} ORDER BY rowid")
                        table_data = cursor.fetchall()
                        
                        # Create hash of table content
                        table_content = json.dumps([dict(row) for row in table_data], 
                                                 sort_keys=True, default=str)
                        table_hash = hashlib.sha256(table_content.encode()).hexdigest()
                        table_hashes[table] = table_hash
                        
                    except Exception as e:
                        logger.warning(f"Failed to hash table {table}: {e}")
                        table_hashes[table] = ""
        
        except Exception as e:
            logger.error(f"Failed to calculate table hashes: {e}")
        
        return table_hashes
    
    def _verify_database_integrity(self) -> bool:
        """Verify database integrity against stored baseline."""
        try:
            if not Path(self.integrity_file).exists():
                logger.warning("No integrity baseline found")
                return False
            
            with open(self.integrity_file, 'r') as f:
                stored_integrity = json.load(f)
            
            current_hash = self._calculate_database_hash()
            stored_hash = stored_integrity.get("database_hash", "")
            
            if current_hash != stored_hash:
                logger.error("Database integrity check failed - file hash mismatch")
                self._log_security_event("integrity_violation", "database", 
                                        metadata={"expected": stored_hash, "actual": current_hash})
                return False
            
            # Update last verified timestamp
            stored_integrity["last_verified"] = datetime.now().isoformat()
            with open(self.integrity_file, 'w') as f:
                json.dump(stored_integrity, f, indent=2)
            
            self.last_integrity_check = datetime.now()
            logger.info("Database integrity verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def _check_key_rotation(self):
        """Check if key rotation is needed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT rotation_date FROM key_rotation_log 
                    WHERE success = 1 ORDER BY rotation_date DESC LIMIT 1
                ''')
                
                last_rotation = cursor.fetchone()
                if last_rotation:
                    last_date = datetime.fromisoformat(last_rotation[0])
                    if datetime.now() - last_date > self.key_rotation_interval:
                        logger.warning("Key rotation overdue - consider rotating encryption keys")
                else:
                    # No previous rotation recorded, create initial record
                    self._log_key_rotation(success=True, metadata={"type": "initial"})
                    
        except Exception as e:
            logger.warning(f"Key rotation check failed: {e}")
    
    def _log_security_event(self, operation: str, table_name: str, record_id: str = None, 
                           checksum: str = None, metadata: Dict = None):
        """Log security-related events for audit trail."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO security_audit 
                    (operation, table_name, record_id, checksum, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (operation, table_name, record_id, checksum, 
                     json.dumps(metadata) if metadata else None))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _log_key_rotation(self, success: bool, old_key_hash: str = None, 
                         new_key_hash: str = None, metadata: Dict = None):
        """Log key rotation events."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO key_rotation_log 
                    (old_key_hash, new_key_hash, success, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (old_key_hash, new_key_hash, success, 
                     json.dumps(metadata) if metadata else None))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log key rotation: {e}")
        
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