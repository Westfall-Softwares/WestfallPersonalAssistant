"""
Conversation History Storage for Westfall Personal Assistant

Provides concrete implementations of storage backends for conversation history.
Supports file-based and SQLite storage with encryption options.
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from core.conversation import StorageBackend, Conversation
from config.settings import get_settings

logger = logging.getLogger(__name__)


class SQLiteStorageBackend(StorageBackend):
    """SQLite-based storage backend for conversations"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or get_settings().memory.database_url
        self.db_path = self.database_url.replace('sqlite:///', '')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Conversations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        metadata TEXT
                    )
                ''')
                
                # Messages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversation_updated 
                    ON conversations (updated_at DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_message_conversation 
                    ON messages (conversation_id, timestamp)
                ''')
                
                conn.commit()
                logger.debug("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Save conversation metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO conversations 
                    (id, title, created_at, updated_at, metadata) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    conversation.id,
                    conversation.title,
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                    json.dumps(conversation.metadata)
                ))
                
                # Delete existing messages for this conversation
                cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation.id,))
                
                # Save all messages
                for message in conversation.messages:
                    cursor.execute('''
                        INSERT INTO messages 
                        (id, conversation_id, role, content, timestamp, metadata) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        message.id,
                        conversation.id,
                        message.role,
                        message.content,
                        message.timestamp.isoformat(),
                        json.dumps(message.metadata)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation.id}: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Load conversation metadata
                cursor.execute('''
                    SELECT title, created_at, updated_at, metadata 
                    FROM conversations WHERE id = ?
                ''', (conversation_id,))
                
                conv_row = cursor.fetchone()
                if not conv_row:
                    return None
                
                title, created_at, updated_at, metadata_json = conv_row
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                # Load messages
                cursor.execute('''
                    SELECT id, role, content, timestamp, metadata 
                    FROM messages WHERE conversation_id = ? 
                    ORDER BY timestamp
                ''', (conversation_id,))
                
                messages = []
                for msg_row in cursor.fetchall():
                    msg_id, role, content, timestamp, msg_metadata_json = msg_row
                    msg_metadata = json.loads(msg_metadata_json) if msg_metadata_json else {}
                    
                    from core.conversation import Message
                    message = Message(
                        id=msg_id,
                        role=role,
                        content=content,
                        timestamp=datetime.fromisoformat(timestamp),
                        metadata=msg_metadata
                    )
                    messages.append(message)
                
                conversation = Conversation(
                    id=conversation_id,
                    title=title,
                    messages=messages,
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    metadata=metadata
                )
                
                return conversation
                
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List conversations from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT c.id, c.title, c.created_at, c.updated_at, 
                           COUNT(m.id) as message_count
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    GROUP BY c.id, c.title, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                ''', (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    conv_id, title, created_at, updated_at, message_count = row
                    conversations.append({
                        'id': conv_id,
                        'title': title,
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'message_count': message_count
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete messages first (foreign key constraint)
                cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
                
                # Delete conversation
                cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def cleanup_old_conversations(self, retention_days: int) -> int:
        """Clean up old conversations from SQLite"""
        if retention_days <= 0:
            return 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get conversations to delete
                cursor.execute('''
                    SELECT id FROM conversations 
                    WHERE updated_at < ?
                ''', (cutoff_date.isoformat(),))
                
                conversation_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete messages for old conversations
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE conversation_id IN (
                        SELECT id FROM conversations WHERE updated_at < ?
                    )
                ''', (cutoff_date.isoformat(),))
                
                # Delete old conversations
                cursor.execute('''
                    DELETE FROM conversations WHERE updated_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = len(conversation_ids)
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old conversations from SQLite")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
            return 0


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for conversations (non-persistent)"""
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save conversation to memory"""
        try:
            # Create a deep copy to avoid reference issues
            import copy
            self.conversations[conversation.id] = copy.deepcopy(conversation)
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation to memory: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from memory"""
        return self.conversations.get(conversation_id)
    
    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List conversations from memory"""
        conversations = []
        
        for conversation in self.conversations.values():
            conversations.append({
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'message_count': len(conversation.messages)
            })
        
        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return conversations[:limit]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from memory"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def cleanup_old_conversations(self, retention_days: int) -> int:
        """Clean up old conversations from memory"""
        if retention_days <= 0:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        to_delete = []
        
        for conversation in self.conversations.values():
            if conversation.updated_at < cutoff_date:
                to_delete.append(conversation.id)
        
        for conv_id in to_delete:
            del self.conversations[conv_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old conversations from memory")
        return len(to_delete)


def create_storage_backend(backend_type: str = None) -> StorageBackend:
    """Factory function to create storage backends"""
    if backend_type is None:
        backend_type = get_settings().memory.storage_backend
    
    if backend_type == "sqlite":
        return SQLiteStorageBackend()
    elif backend_type == "memory":
        return MemoryStorageBackend()
    elif backend_type == "file":
        from core.conversation import FileStorageBackend
        return FileStorageBackend()
    else:
        logger.warning(f"Unknown storage backend: {backend_type}, using file backend")
        from core.conversation import FileStorageBackend
        return FileStorageBackend()