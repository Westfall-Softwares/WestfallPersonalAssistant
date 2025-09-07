#!/usr/bin/env python3
"""
Notification Manager for Westfall Personal Assistant

System for managing notifications, alerts, and in-app messaging with
priority levels, history, and do-not-disturb functionality.
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    REMINDER = "reminder"
    SYSTEM = "system"


class NotificationManager:
    """Comprehensive notification system with priority and persistence."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/notifications.db"
        
        # Notification state
        self.active_notifications = {}
        self.do_not_disturb = False
        self.dnd_until = None
        
        # Notification callbacks
        self.notification_callbacks = {}
        
        # Settings
        self.max_active_notifications = 10
        self.default_duration = 5000  # milliseconds
        self.sound_enabled = True
        self.system_tray_enabled = True
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for notifications."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create notifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        module TEXT,
                        action_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        scheduled_for TIMESTAMP,
                        delivered_at TIMESTAMP,
                        dismissed_at TIMESTAMP,
                        read_at TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        persistent BOOLEAN DEFAULT FALSE,
                        sound_enabled BOOLEAN DEFAULT TRUE,
                        duration INTEGER DEFAULT 5000
                    )
                ''')
                
                # Create notification settings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        module TEXT,
                        notification_type TEXT,
                        enabled BOOLEAN DEFAULT TRUE,
                        sound_enabled BOOLEAN DEFAULT TRUE,
                        priority_threshold INTEGER DEFAULT 1,
                        do_not_disturb_enabled BOOLEAN DEFAULT FALSE,
                        quiet_hours_start TEXT,
                        quiet_hours_end TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create notification history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        action_data TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (notification_id) REFERENCES notifications (notification_id)
                    )
                ''')
                
                # Create notification templates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        template_id TEXT UNIQUE NOT NULL,
                        title_template TEXT NOT NULL,
                        message_template TEXT NOT NULL,
                        type TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        module TEXT,
                        variables TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Notification database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize notification database: {e}")
            raise
    
    async def send_notification(self, title: str, message: str, 
                               notification_type: NotificationType = NotificationType.INFO,
                               priority: NotificationPriority = NotificationPriority.NORMAL,
                               module: str = None, action_data: Dict = None,
                               duration: int = None, persistent: bool = False,
                               sound_enabled: bool = None, scheduled_for: datetime = None) -> str:
        """Send a notification."""
        try:
            # Generate unique ID
            notification_id = str(uuid.uuid4())
            
            # Apply settings
            if duration is None:
                duration = self.default_duration
            if sound_enabled is None:
                sound_enabled = self.sound_enabled
            
            # Check if notifications are enabled for this type/module
            if not await self._is_notification_enabled(notification_type, module, priority):
                logger.info(f"Notification blocked by settings: {title}")
                return None
            
            # Check do not disturb
            if self._is_do_not_disturb_active() and priority.value < NotificationPriority.URGENT.value:
                # Schedule for later or store as pending
                status = "do_not_disturb"
                delivered_at = None
            else:
                status = "delivered"
                delivered_at = datetime.now()
            
            # Create notification record
            notification = {
                "id": notification_id,
                "title": title,
                "message": message,
                "type": notification_type.value,
                "priority": priority.value,
                "module": module,
                "action_data": action_data,
                "created_at": datetime.now(),
                "scheduled_for": scheduled_for,
                "delivered_at": delivered_at,
                "status": status,
                "persistent": persistent,
                "sound_enabled": sound_enabled,
                "duration": duration
            }
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notifications 
                    (notification_id, title, message, type, priority, module, action_data,
                     scheduled_for, delivered_at, status, persistent, sound_enabled, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_id, title, message, notification_type.value, priority.value,
                    module, json.dumps(action_data or {}), 
                    scheduled_for.isoformat() if scheduled_for else None,
                    delivered_at.isoformat() if delivered_at else None,
                    status, persistent, sound_enabled, duration
                ))
                conn.commit()
            
            # If delivered, add to active notifications and trigger callbacks
            if status == "delivered":
                self.active_notifications[notification_id] = notification
                await self._trigger_notification_callbacks(notification)
                
                # Auto-dismiss after duration (if not persistent)
                if not persistent:
                    asyncio.create_task(self._auto_dismiss(notification_id, duration))
            
            # Record history
            await self._record_history(notification_id, "created", {"status": status})
            
            logger.info(f"Notification created: {notification_id} - {title}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return None
    
    async def send_template_notification(self, template_id: str, variables: Dict = None) -> str:
        """Send notification using a template."""
        try:
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Replace variables in template
            title = self._replace_variables(template["title_template"], variables or {})
            message = self._replace_variables(template["message_template"], variables or {})
            
            # Send notification
            return await self.send_notification(
                title=title,
                message=message,
                notification_type=NotificationType(template["type"]),
                priority=NotificationPriority(template["priority"]),
                module=template["module"]
            )
            
        except Exception as e:
            logger.error(f"Failed to send template notification: {e}")
            return None
    
    def _replace_variables(self, template: str, variables: Dict) -> str:
        """Replace variables in template string."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    async def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss a notification."""
        try:
            if notification_id in self.active_notifications:
                # Remove from active
                del self.active_notifications[notification_id]
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE notifications 
                        SET dismissed_at = ?, status = 'dismissed'
                        WHERE notification_id = ?
                    ''', (datetime.now().isoformat(), notification_id))
                    conn.commit()
                
                # Record history
                await self._record_history(notification_id, "dismissed")
                
                logger.info(f"Notification dismissed: {notification_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to dismiss notification: {e}")
            return False
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE notifications 
                    SET read_at = ?
                    WHERE notification_id = ?
                ''', (datetime.now().isoformat(), notification_id))
                conn.commit()
            
            # Record history
            await self._record_history(notification_id, "read")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    async def _auto_dismiss(self, notification_id: str, duration: int):
        """Auto-dismiss notification after duration."""
        try:
            await asyncio.sleep(duration / 1000)  # Convert to seconds
            await self.dismiss_notification(notification_id)
        except Exception as e:
            logger.error(f"Auto-dismiss failed for {notification_id}: {e}")
    
    async def set_do_not_disturb(self, enabled: bool, until: datetime = None):
        """Set do not disturb mode."""
        self.do_not_disturb = enabled
        self.dnd_until = until
        
        if enabled:
            logger.info(f"Do not disturb enabled until: {until}")
        else:
            logger.info("Do not disturb disabled")
    
    def _is_do_not_disturb_active(self) -> bool:
        """Check if do not disturb is currently active."""
        if not self.do_not_disturb:
            return False
        
        if self.dnd_until and datetime.now() > self.dnd_until:
            self.do_not_disturb = False
            self.dnd_until = None
            return False
        
        return True
    
    async def _is_notification_enabled(self, notification_type: NotificationType, 
                                     module: str, priority: NotificationPriority) -> bool:
        """Check if notification is enabled based on settings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check module-specific settings
                if module:
                    cursor.execute('''
                        SELECT enabled, priority_threshold FROM notification_settings
                        WHERE module = ? AND notification_type = ?
                    ''', (module, notification_type.value))
                    
                    result = cursor.fetchone()
                    if result:
                        enabled, threshold = result
                        return enabled and priority.value >= threshold
                
                # Check general settings
                cursor.execute('''
                    SELECT enabled, priority_threshold FROM notification_settings
                    WHERE module IS NULL AND notification_type = ?
                ''', (notification_type.value,))
                
                result = cursor.fetchone()
                if result:
                    enabled, threshold = result
                    return enabled and priority.value >= threshold
                
                # Default: enabled
                return True
                
        except Exception as e:
            logger.error(f"Failed to check notification settings: {e}")
            return True
    
    async def _trigger_notification_callbacks(self, notification: Dict):
        """Trigger registered notification callbacks."""
        try:
            for callback_name, callback in self.notification_callbacks.items():
                try:
                    await callback(notification)
                except Exception as e:
                    logger.error(f"Notification callback {callback_name} failed: {e}")
        except Exception as e:
            logger.error(f"Failed to trigger notification callbacks: {e}")
    
    async def register_callback(self, name: str, callback: Callable):
        """Register notification callback."""
        self.notification_callbacks[name] = callback
        logger.info(f"Registered notification callback: {name}")
    
    async def get_active_notifications(self) -> List[Dict]:
        """Get currently active notifications."""
        return list(self.active_notifications.values())
    
    async def get_notification_history(self, limit: int = 100, 
                                     notification_type: str = None,
                                     module: str = None) -> List[Dict]:
        """Get notification history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM notifications WHERE 1=1'
                params = []
                
                if notification_type:
                    query += ' AND type = ?'
                    params.append(notification_type)
                
                if module:
                    query += ' AND module = ?'
                    params.append(module)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return self._format_notifications(results)
                
        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return []
    
    def _format_notifications(self, raw_notifications: List) -> List[Dict]:
        """Format raw database notifications into dictionaries."""
        notifications = []
        
        for row in raw_notifications:
            notification = {
                "id": row[0],
                "notification_id": row[1],
                "title": row[2],
                "message": row[3],
                "type": row[4],
                "priority": row[5],
                "module": row[6],
                "action_data": json.loads(row[7]) if row[7] else {},
                "created_at": row[8],
                "scheduled_for": row[9],
                "delivered_at": row[10],
                "dismissed_at": row[11],
                "read_at": row[12],
                "status": row[13],
                "persistent": bool(row[14]),
                "sound_enabled": bool(row[15]),
                "duration": row[16]
            }
            notifications.append(notification)
        
        return notifications
    
    async def clear_notifications(self, notification_type: str = None, 
                                module: str = None, older_than_days: int = None) -> int:
        """Clear notifications based on criteria."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'DELETE FROM notifications WHERE 1=1'
                params = []
                
                if notification_type:
                    query += ' AND type = ?'
                    params.append(notification_type)
                
                if module:
                    query += ' AND module = ?'
                    params.append(module)
                
                if older_than_days:
                    query += ' AND created_at < datetime("now", "-{} days")'.format(older_than_days)
                
                cursor.execute(query, params)
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleared {deleted_count} notifications")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to clear notifications: {e}")
            return 0
    
    async def create_template(self, template_id: str, title_template: str, 
                            message_template: str, notification_type: NotificationType,
                            priority: NotificationPriority, module: str = None,
                            variables: List[str] = None) -> bool:
        """Create notification template."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notification_templates
                    (template_id, title_template, message_template, type, priority, module, variables)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_id, title_template, message_template,
                    notification_type.value, priority.value, module,
                    json.dumps(variables or [])
                ))
                conn.commit()
            
            logger.info(f"Created notification template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
    
    async def _get_template(self, template_id: str) -> Optional[Dict]:
        """Get notification template."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM notification_templates WHERE template_id = ?
                ''', (template_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "template_id": row[1],
                        "title_template": row[2],
                        "message_template": row[3],
                        "type": row[4],
                        "priority": row[5],
                        "module": row[6],
                        "variables": json.loads(row[7]) if row[7] else [],
                        "created_at": row[8]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None
    
    async def _record_history(self, notification_id: str, action: str, action_data: Dict = None):
        """Record notification action in history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notification_history (notification_id, action, action_data)
                    VALUES (?, ?, ?)
                ''', (notification_id, action, json.dumps(action_data or {})))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record notification history: {e}")
    
    async def get_statistics(self) -> Dict:
        """Get notification statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total notifications
                cursor.execute('SELECT COUNT(*) FROM notifications')
                total_notifications = cursor.fetchone()[0]
                
                # Notifications by type
                cursor.execute('''
                    SELECT type, COUNT(*) FROM notifications
                    GROUP BY type
                ''')
                type_counts = dict(cursor.fetchall())
                
                # Notifications by module
                cursor.execute('''
                    SELECT module, COUNT(*) FROM notifications
                    WHERE module IS NOT NULL
                    GROUP BY module
                ''')
                module_counts = dict(cursor.fetchall())
                
                # Recent notifications (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) FROM notifications
                    WHERE created_at > datetime('now', '-1 day')
                ''')
                recent_notifications = cursor.fetchone()[0]
                
                # Unread notifications
                cursor.execute('''
                    SELECT COUNT(*) FROM notifications
                    WHERE read_at IS NULL AND status = 'delivered'
                ''')
                unread_notifications = cursor.fetchone()[0]
                
                return {
                    "total_notifications": total_notifications,
                    "notifications_by_type": type_counts,
                    "notifications_by_module": module_counts,
                    "recent_notifications": recent_notifications,
                    "unread_notifications": unread_notifications,
                    "active_notifications": len(self.active_notifications),
                    "do_not_disturb": self._is_do_not_disturb_active()
                }
                
        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return {}