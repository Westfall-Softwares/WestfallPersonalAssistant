"""
Conversation Management for Westfall Personal Assistant

Handles conversation history, context management, and message processing.
Consolidates conversation functionality from various sources.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation"""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Conversation:
    """Represents a conversation with metadata"""
    id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a new message to the conversation"""
        message = Message(
            id=f"{self.id}_{len(self.messages)}",
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_context(self, max_messages: int = 10) -> List[Message]:
        """Get recent messages for context"""
        return self.messages[-max_messages:] if self.messages else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary"""
        messages = [Message.from_dict(msg_data) for msg_data in data['messages']]
        return cls(
            id=data['id'],
            title=data['title'],
            messages=messages,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {})
        )


class StorageBackend(ABC):
    """Abstract base class for conversation storage backends"""
    
    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation"""
        pass
    
    @abstractmethod
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation by ID"""
        pass
    
    @abstractmethod
    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List conversations (metadata only)"""
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        pass
    
    @abstractmethod
    def cleanup_old_conversations(self, retention_days: int) -> int:
        """Clean up old conversations, return count deleted"""
        pass


class FileStorageBackend(StorageBackend):
    """File-based storage backend for conversations"""
    
    def __init__(self, storage_dir: str = "data/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        """Load conversation index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load conversation index: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save conversation index"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save conversation index: {e}")
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation to file"""
        try:
            conversation_file = self.storage_dir / f"{conversation.id}.json"
            
            with open(conversation_file, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2, default=str)
            
            # Update index
            self.index[conversation.id] = {
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'message_count': len(conversation.messages)
            }
            self._save_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation.id}: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from file"""
        try:
            conversation_file = self.storage_dir / f"{conversation_id}.json"
            
            if not conversation_file.exists():
                return None
            
            with open(conversation_file, 'r') as f:
                data = json.load(f)
            
            return Conversation.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List conversations (metadata only)"""
        conversations = []
        
        for conv_id, metadata in self.index.items():
            conversations.append({
                'id': conv_id,
                **metadata
            })
        
        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return conversations[:limit]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            conversation_file = self.storage_dir / f"{conversation_id}.json"
            
            if conversation_file.exists():
                conversation_file.unlink()
            
            if conversation_id in self.index:
                del self.index[conversation_id]
                self._save_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def cleanup_old_conversations(self, retention_days: int) -> int:
        """Clean up old conversations"""
        if retention_days <= 0:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for conv_id, metadata in list(self.index.items()):
            try:
                updated_at = datetime.fromisoformat(metadata['updated_at'])
                if updated_at < cutoff_date:
                    if self.delete_conversation(conv_id):
                        deleted_count += 1
            except Exception as e:
                logger.error(f"Error checking conversation {conv_id} for cleanup: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old conversations")
        return deleted_count


class ConversationManager:
    """Manages conversations and message processing"""
    
    def __init__(self, storage_backend: StorageBackend = None, max_context_length: int = 10):
        self.storage_backend = storage_backend or FileStorageBackend()
        self.max_context_length = max_context_length
        self.current_conversation: Optional[Conversation] = None
        
    def start_new_conversation(self, title: str = None) -> Conversation:
        """Start a new conversation"""
        if title is None:
            title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.current_conversation = conversation
        self.save_current_conversation()
        
        logger.info(f"Started new conversation: {conversation_id}")
        return conversation
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Load an existing conversation"""
        conversation = self.storage_backend.load_conversation(conversation_id)
        
        if conversation:
            self.current_conversation = conversation
            logger.info(f"Loaded conversation: {conversation_id}")
            return True
        else:
            logger.error(f"Failed to load conversation: {conversation_id}")
            return False
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> Optional[Message]:
        """Add a message to the current conversation"""
        if not self.current_conversation:
            self.start_new_conversation()
        
        message = self.current_conversation.add_message(role, content, metadata)
        self.save_current_conversation()
        
        logger.debug(f"Added message: {role} - {content[:50]}...")
        return message
    
    def get_conversation_context(self) -> List[Message]:
        """Get context from current conversation"""
        if not self.current_conversation:
            return []
        
        return self.current_conversation.get_context(self.max_context_length)
    
    def format_context_for_model(self) -> str:
        """Format conversation context for model input"""
        context_messages = self.get_conversation_context()
        
        if not context_messages:
            return ""
        
        formatted_context = []
        for message in context_messages:
            role_prefix = {
                'user': 'User',
                'assistant': 'Assistant',
                'system': 'System'
            }.get(message.role, message.role.title())
            
            formatted_context.append(f"{role_prefix}: {message.content}")
        
        return "\n".join(formatted_context)
    
    def save_current_conversation(self) -> bool:
        """Save the current conversation"""
        if not self.current_conversation:
            return False
        
        return self.storage_backend.save_conversation(self.current_conversation)
    
    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List available conversations"""
        return self.storage_backend.list_conversations(limit)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        success = self.storage_backend.delete_conversation(conversation_id)
        
        # If we deleted the current conversation, clear it
        if success and self.current_conversation and self.current_conversation.id == conversation_id:
            self.current_conversation = None
        
        return success
    
    def update_conversation_title(self, title: str) -> bool:
        """Update the title of the current conversation"""
        if not self.current_conversation:
            return False
        
        self.current_conversation.title = title
        self.current_conversation.updated_at = datetime.now()
        return self.save_current_conversation()
    
    def get_current_conversation_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current conversation"""
        if not self.current_conversation:
            return None
        
        return {
            'id': self.current_conversation.id,
            'title': self.current_conversation.title,
            'message_count': len(self.current_conversation.messages),
            'created_at': self.current_conversation.created_at.isoformat(),
            'updated_at': self.current_conversation.updated_at.isoformat()
        }
    
    def cleanup_old_conversations(self, retention_days: int) -> int:
        """Clean up old conversations based on retention policy"""
        return self.storage_backend.cleanup_old_conversations(retention_days)
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by content (simple text search)"""
        conversations = self.list_conversations(limit=1000)  # Get more for searching
        matching_conversations = []
        
        query_lower = query.lower()
        
        for conv_meta in conversations:
            # Search in title
            if query_lower in conv_meta['title'].lower():
                matching_conversations.append(conv_meta)
                continue
            
            # Search in conversation content
            try:
                conversation = self.storage_backend.load_conversation(conv_meta['id'])
                if conversation:
                    for message in conversation.messages:
                        if query_lower in message.content.lower():
                            matching_conversations.append(conv_meta)
                            break
            except Exception as e:
                logger.error(f"Error searching conversation {conv_meta['id']}: {e}")
        
        return matching_conversations[:limit]


# Default manager instance
_conversation_manager_instance = None

def get_conversation_manager() -> ConversationManager:
    """Get singleton conversation manager instance"""
    global _conversation_manager_instance
    if _conversation_manager_instance is None:
        _conversation_manager_instance = ConversationManager()
    return _conversation_manager_instance