#!/usr/bin/env python3
"""
SQLAlchemy ORM Models for Westfall Personal Assistant

Defines database schema using SQLAlchemy ORM.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User profile and settings."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    preferences = Column(JSON)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    settings = relationship("Setting", back_populates="user")
    password_entries = relationship("PasswordEntry", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class Conversation(Base):
    """Conversation sessions."""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived = Column(Boolean, default=False)
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Individual messages within conversations."""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    thinking_mode = Column(String(20))  # 'normal', 'thinking', 'research'
    tokens_used = Column(Integer)
    processing_time = Column(Integer)  # milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Setting(Base):
    """User settings and preferences."""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category = Column(String(50), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default='string')  # 'string', 'integer', 'boolean', 'json'
    encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")


class PasswordEntry(Base):
    """Password manager entries."""
    __tablename__ = 'password_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(Text, nullable=False)  # Encrypted
    url = Column(String(500))
    notes = Column(Text)  # Encrypted
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="password_entries")


class APIKey(Base):
    """API key storage."""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service = Column(String(100), nullable=False)
    api_key = Column(Text, nullable=False)  # Encrypted
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class NewsSource(Base):
    """News sources configuration."""
    __tablename__ = 'news_sources'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(20), default='rss')  # 'rss', 'api', 'scrape'
    active = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=3600)  # seconds
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MusicPlaylist(Base):
    """Music playlists."""
    __tablename__ = 'music_playlists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))  # Path to M3U file
    tracks_count = Column(Integer, default=0)
    duration = Column(Integer, default=0)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemMetrics(Base):
    """System performance metrics."""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(50), nullable=False)  # 'cpu', 'memory', 'gpu', 'response_time'
    value = Column(String(100), nullable=False)
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    recorded_at = Column(DateTime, default=datetime.utcnow)


class NotificationQueue(Base):
    """Notification queue."""
    __tablename__ = 'notification_queue'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_data = Column(JSON)
    priority = Column(Integer, default=0)  # Higher numbers = higher priority
    scheduled_for = Column(DateTime)
    delivered_at = Column(DateTime)
    status = Column(String(20), default='pending')  # 'pending', 'delivered', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)