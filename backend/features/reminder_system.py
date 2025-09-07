#!/usr/bin/env python3
"""
Reminder System for Westfall Personal Assistant

Advanced reminder system with time-based and location-based reminders,
recurring patterns, snooze functionality, and calendar integration.
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid
import re

logger = logging.getLogger(__name__)


class ReminderType(Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    LOCATION = "location"
    CONDITIONAL = "conditional"


class RecurrencePattern(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    CUSTOM = "custom"


class ReminderPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ReminderSystem:
    """Comprehensive reminder system with various trigger types."""
    
    def __init__(self, config_dir: str = None, db_path: str = None, notification_manager=None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/reminders.db"
        self.notification_manager = notification_manager
        
        # Reminder state
        self.active_reminders = {}
        self.scheduled_tasks = {}
        
        # System running
        self.running = False
        self.check_interval = 60  # seconds
        
        # Callbacks
        self.reminder_callbacks = {}
        
        # Initialize database
        self._init_database()
        
        # Start reminder checking task will be started later
        self._reminder_loop_started = False
    
    def _init_database(self):
        """Initialize SQLite database for reminders."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create reminders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reminder_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        reminder_type TEXT NOT NULL,
                        priority INTEGER DEFAULT 2,
                        trigger_time TIMESTAMP,
                        location_lat REAL,
                        location_lng REAL,
                        location_name TEXT,
                        location_radius REAL DEFAULT 100,
                        recurrence_pattern TEXT,
                        recurrence_data TEXT,
                        is_recurring BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        snooze_count INTEGER DEFAULT 0,
                        max_snoozes INTEGER DEFAULT 3,
                        snooze_duration INTEGER DEFAULT 300,
                        tags TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        next_trigger TIMESTAMP
                    )
                ''')
                
                # Create reminder executions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminder_executions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reminder_id TEXT NOT NULL,
                        execution_id TEXT UNIQUE NOT NULL,
                        triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        action_taken TEXT,
                        snoozed_until TIMESTAMP,
                        completed BOOLEAN DEFAULT FALSE,
                        notes TEXT,
                        FOREIGN KEY (reminder_id) REFERENCES reminders (reminder_id)
                    )
                ''')
                
                # Create location history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS location_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        lat REAL NOT NULL,
                        lng REAL NOT NULL,
                        accuracy REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source TEXT DEFAULT 'manual'
                    )
                ''')
                
                # Create reminder templates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminder_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        template_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        reminder_type TEXT NOT NULL,
                        default_priority INTEGER DEFAULT 2,
                        default_recurrence TEXT,
                        variables TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_trigger_time ON reminders(trigger_time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_location ON reminders(location_lat, location_lng)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active)')
                
                conn.commit()
                logger.info("Reminder database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize reminder database: {e}")
            raise
    
    async def create_reminder(self, title: str, description: str = "",
                            reminder_type: ReminderType = ReminderType.ONE_TIME,
                            trigger_time: datetime = None,
                            location: Dict = None,
                            recurrence: Dict = None,
                            priority: ReminderPriority = ReminderPriority.NORMAL,
                            tags: List[str] = None,
                            metadata: Dict = None) -> str:
        """Create a new reminder."""
        try:
            reminder_id = str(uuid.uuid4())
            
            # Validate and process inputs
            if reminder_type == ReminderType.ONE_TIME and not trigger_time:
                raise ValueError("One-time reminders require a trigger time")
            
            if reminder_type == ReminderType.LOCATION and not location:
                raise ValueError("Location reminders require location data")
            
            # Process location data
            location_lat = location_lng = location_name = location_radius = None
            if location:
                location_lat = location.get("lat")
                location_lng = location.get("lng")
                location_name = location.get("name", "")
                location_radius = location.get("radius", 100)
            
            # Process recurrence data
            is_recurring = reminder_type == ReminderType.RECURRING
            recurrence_pattern = None
            recurrence_data = None
            next_trigger = trigger_time
            
            if is_recurring and recurrence:
                recurrence_pattern = recurrence.get("pattern")
                recurrence_data = json.dumps(recurrence)
                next_trigger = self._calculate_next_trigger(trigger_time, recurrence)
            
            # Create reminder record
            reminder = {
                "reminder_id": reminder_id,
                "title": title,
                "description": description,
                "reminder_type": reminder_type.value,
                "priority": priority.value,
                "trigger_time": trigger_time,
                "location_lat": location_lat,
                "location_lng": location_lng,
                "location_name": location_name,
                "location_radius": location_radius,
                "recurrence_pattern": recurrence_pattern,
                "recurrence_data": recurrence_data,
                "is_recurring": is_recurring,
                "is_active": True,
                "snooze_count": 0,
                "max_snoozes": 3,
                "snooze_duration": 300,  # 5 minutes
                "tags": json.dumps(tags or []),
                "metadata": json.dumps(metadata or {}),
                "next_trigger": next_trigger
            }
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reminders 
                    (reminder_id, title, description, reminder_type, priority,
                     trigger_time, location_lat, location_lng, location_name, location_radius,
                     recurrence_pattern, recurrence_data, is_recurring, is_active,
                     snooze_count, max_snoozes, snooze_duration, tags, metadata, next_trigger)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reminder_id, title, description, reminder_type.value, priority.value,
                    trigger_time.isoformat() if trigger_time else None,
                    location_lat, location_lng, location_name, location_radius,
                    recurrence_pattern, recurrence_data, is_recurring, True,
                    0, 3, 300, json.dumps(tags or []), json.dumps(metadata or {}),
                    next_trigger.isoformat() if next_trigger else None
                ))
                conn.commit()
            
            # Add to active reminders
            self.active_reminders[reminder_id] = reminder
            
            logger.info(f"Created reminder: {reminder_id} - {title}")
            return reminder_id
            
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            return None
    
    def _calculate_next_trigger(self, base_time: datetime, recurrence: Dict) -> datetime:
        """Calculate next trigger time for recurring reminders."""
        pattern = recurrence.get("pattern")
        interval = recurrence.get("interval", 1)
        
        if pattern == "daily":
            return base_time + timedelta(days=interval)
        elif pattern == "weekly":
            return base_time + timedelta(weeks=interval)
        elif pattern == "monthly":
            # Add months (approximate)
            new_month = base_time.month + interval
            new_year = base_time.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            return base_time.replace(year=new_year, month=new_month)
        elif pattern == "yearly":
            return base_time.replace(year=base_time.year + interval)
        elif pattern == "weekdays":
            # Next weekday
            days_ahead = 1
            while (base_time + timedelta(days=days_ahead)).weekday() > 4:  # 0-4 = Mon-Fri
                days_ahead += 1
            return base_time + timedelta(days=days_ahead)
        elif pattern == "weekends":
            # Next weekend day
            days_ahead = 1
            while (base_time + timedelta(days=days_ahead)).weekday() < 5:  # 5-6 = Sat-Sun
                days_ahead += 1
            return base_time + timedelta(days=days_ahead)
        elif pattern == "custom":
            # Custom pattern with specific days/times
            custom_data = recurrence.get("custom_data", {})
            days_of_week = custom_data.get("days_of_week", [])
            
            if days_of_week:
                # Find next occurrence of specified weekday
                current_weekday = base_time.weekday()
                days_ahead = None
                
                for day in sorted(days_of_week):
                    if day > current_weekday:
                        days_ahead = day - current_weekday
                        break
                
                if days_ahead is None:
                    # Next week's first day
                    days_ahead = (7 - current_weekday) + min(days_of_week)
                
                return base_time + timedelta(days=days_ahead)
        
        # Default: daily
        return base_time + timedelta(days=1)
    
    async def _start_reminder_loop(self):
        """Start the main reminder checking loop."""
        self.running = True
        logger.info("Reminder system started")
        
        while self.running:
            try:
                await self._check_reminders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def _check_reminders(self):
        """Check for reminders that need to be triggered."""
        try:
            current_time = datetime.now()
            
            # Check time-based reminders
            await self._check_time_reminders(current_time)
            
            # Check location-based reminders (if location is available)
            # This would integrate with location services
            
            # Process any pending recurring reminders
            await self._process_recurring_reminders(current_time)
            
        except Exception as e:
            logger.error(f"Failed to check reminders: {e}")
    
    async def _check_time_reminders(self, current_time: datetime):
        """Check time-based reminders."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM reminders 
                    WHERE is_active = TRUE 
                    AND (trigger_time <= ? OR next_trigger <= ?)
                    AND reminder_type IN ('one_time', 'recurring')
                ''', (current_time.isoformat(), current_time.isoformat()))
                
                results = cursor.fetchall()
                
                for row in results:
                    reminder = self._format_reminder(row)
                    await self._trigger_reminder(reminder)
                    
        except Exception as e:
            logger.error(f"Failed to check time reminders: {e}")
    
    async def _process_recurring_reminders(self, current_time: datetime):
        """Process recurring reminders and schedule next occurrence."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM reminders 
                    WHERE is_active = TRUE 
                    AND is_recurring = TRUE 
                    AND next_trigger <= ?
                ''', (current_time.isoformat(),))
                
                results = cursor.fetchall()
                
                for row in results:
                    reminder = self._format_reminder(row)
                    
                    # Calculate next trigger
                    recurrence_data = json.loads(reminder.get("recurrence_data", "{}"))
                    next_trigger = self._calculate_next_trigger(current_time, recurrence_data)
                    
                    # Update next trigger in database
                    cursor.execute('''
                        UPDATE reminders 
                        SET next_trigger = ?, updated_at = ?
                        WHERE reminder_id = ?
                    ''', (next_trigger.isoformat(), current_time.isoformat(), reminder["reminder_id"]))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to process recurring reminders: {e}")
    
    async def _trigger_reminder(self, reminder: Dict):
        """Trigger a reminder and send notification."""
        try:
            reminder_id = reminder["reminder_id"]
            execution_id = str(uuid.uuid4())
            
            # Create execution record
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reminder_executions 
                    (reminder_id, execution_id, triggered_at)
                    VALUES (?, ?, ?)
                ''', (reminder_id, execution_id, datetime.now().isoformat()))
                conn.commit()
            
            # Send notification if notification manager is available
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    title=f"Reminder: {reminder['title']}",
                    message=reminder.get("description", ""),
                    notification_type="reminder",
                    priority=reminder.get("priority", 2),
                    module="reminders",
                    action_data={
                        "reminder_id": reminder_id,
                        "execution_id": execution_id,
                        "actions": ["complete", "snooze", "dismiss"]
                    },
                    persistent=True
                )
            
            # Trigger callbacks
            await self._trigger_reminder_callbacks(reminder, execution_id)
            
            # If one-time reminder, mark as completed
            if reminder["reminder_type"] == "one_time":
                await self.complete_reminder(reminder_id)
            
            logger.info(f"Triggered reminder: {reminder_id} - {reminder['title']}")
            
        except Exception as e:
            logger.error(f"Failed to trigger reminder: {e}")
    
    async def _trigger_reminder_callbacks(self, reminder: Dict, execution_id: str):
        """Trigger registered reminder callbacks."""
        try:
            for callback_name, callback in self.reminder_callbacks.items():
                try:
                    await callback(reminder, execution_id)
                except Exception as e:
                    logger.error(f"Reminder callback {callback_name} failed: {e}")
        except Exception as e:
            logger.error(f"Failed to trigger reminder callbacks: {e}")
    
    async def snooze_reminder(self, reminder_id: str, duration_minutes: int = None) -> bool:
        """Snooze a reminder for specified duration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get reminder info
                cursor.execute('''
                    SELECT snooze_count, max_snoozes, snooze_duration FROM reminders
                    WHERE reminder_id = ?
                ''', (reminder_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                snooze_count, max_snoozes, default_duration = result
                
                # Check if snooze limit reached
                if snooze_count >= max_snoozes:
                    logger.warning(f"Snooze limit reached for reminder: {reminder_id}")
                    return False
                
                # Calculate snooze duration
                if duration_minutes is None:
                    duration_minutes = default_duration // 60
                
                snooze_until = datetime.now() + timedelta(minutes=duration_minutes)
                
                # Update reminder
                cursor.execute('''
                    UPDATE reminders 
                    SET snooze_count = snooze_count + 1,
                        next_trigger = ?,
                        updated_at = ?
                    WHERE reminder_id = ?
                ''', (snooze_until.isoformat(), datetime.now().isoformat(), reminder_id))
                
                # Update latest execution
                cursor.execute('''
                    UPDATE reminder_executions 
                    SET snoozed_until = ?, action_taken = 'snoozed'
                    WHERE reminder_id = ? 
                    ORDER BY triggered_at DESC 
                    LIMIT 1
                ''', (snooze_until.isoformat(), reminder_id))
                
                conn.commit()
                
                logger.info(f"Snoozed reminder {reminder_id} until {snooze_until}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to snooze reminder: {e}")
            return False
    
    async def complete_reminder(self, reminder_id: str) -> bool:
        """Mark reminder as completed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                completion_time = datetime.now().isoformat()
                
                # Update reminder
                cursor.execute('''
                    UPDATE reminders 
                    SET completed_at = ?, is_active = FALSE, updated_at = ?
                    WHERE reminder_id = ?
                ''', (completion_time, completion_time, reminder_id))
                
                # Update latest execution
                cursor.execute('''
                    UPDATE reminder_executions 
                    SET completed = TRUE, action_taken = 'completed'
                    WHERE reminder_id = ? 
                    ORDER BY triggered_at DESC 
                    LIMIT 1
                ''', (reminder_id,))
                
                conn.commit()
                
                # Remove from active reminders
                if reminder_id in self.active_reminders:
                    del self.active_reminders[reminder_id]
                
                logger.info(f"Completed reminder: {reminder_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to complete reminder: {e}")
            return False
    
    async def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete executions first
                cursor.execute('DELETE FROM reminder_executions WHERE reminder_id = ?', (reminder_id,))
                
                # Delete reminder
                cursor.execute('DELETE FROM reminders WHERE reminder_id = ?', (reminder_id,))
                
                conn.commit()
                
                # Remove from active reminders
                if reminder_id in self.active_reminders:
                    del self.active_reminders[reminder_id]
                
                logger.info(f"Deleted reminder: {reminder_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            return False
    
    async def get_reminders(self, active_only: bool = True, 
                          reminder_type: str = None,
                          limit: int = 100) -> List[Dict]:
        """Get reminders list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM reminders WHERE 1=1'
                params = []
                
                if active_only:
                    query += ' AND is_active = TRUE'
                
                if reminder_type:
                    query += ' AND reminder_type = ?'
                    params.append(reminder_type)
                
                query += ' ORDER BY trigger_time ASC, created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [self._format_reminder(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get reminders: {e}")
            return []
    
    def _format_reminder(self, row) -> Dict:
        """Format raw database reminder into dictionary."""
        return {
            "id": row[0],
            "reminder_id": row[1],
            "title": row[2],
            "description": row[3],
            "reminder_type": row[4],
            "priority": row[5],
            "trigger_time": row[6],
            "location_lat": row[7],
            "location_lng": row[8],
            "location_name": row[9],
            "location_radius": row[10],
            "recurrence_pattern": row[11],
            "recurrence_data": row[12],
            "is_recurring": bool(row[13]),
            "is_active": bool(row[14]),
            "snooze_count": row[15],
            "max_snoozes": row[16],
            "snooze_duration": row[17],
            "tags": json.loads(row[18]) if row[18] else [],
            "metadata": json.loads(row[19]) if row[19] else {},
            "created_at": row[20],
            "updated_at": row[21],
            "completed_at": row[22],
            "next_trigger": row[23]
        }
    
    async def register_callback(self, name: str, callback: Callable):
        """Register reminder callback."""
        self.reminder_callbacks[name] = callback
        logger.info(f"Registered reminder callback: {name}")
    
    async def update_location(self, lat: float, lng: float, accuracy: float = None):
        """Update current location for location-based reminders."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO location_history (lat, lng, accuracy)
                    VALUES (?, ?, ?)
                ''', (lat, lng, accuracy))
                conn.commit()
            
            # Check location-based reminders
            await self._check_location_reminders(lat, lng)
            
        except Exception as e:
            logger.error(f"Failed to update location: {e}")
    
    async def _check_location_reminders(self, current_lat: float, current_lng: float):
        """Check location-based reminders."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM reminders 
                    WHERE is_active = TRUE 
                    AND reminder_type = 'location'
                    AND location_lat IS NOT NULL 
                    AND location_lng IS NOT NULL
                ''')
                
                results = cursor.fetchall()
                
                for row in results:
                    reminder = self._format_reminder(row)
                    
                    # Calculate distance
                    distance = self._calculate_distance(
                        current_lat, current_lng,
                        reminder["location_lat"], reminder["location_lng"]
                    )
                    
                    # Check if within radius
                    if distance <= reminder["location_radius"]:
                        await self._trigger_reminder(reminder)
                        
        except Exception as e:
            logger.error(f"Failed to check location reminders: {e}")
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters (Haversine formula)."""
        import math
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    async def get_statistics(self) -> Dict:
        """Get reminder system statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total reminders
                cursor.execute('SELECT COUNT(*) FROM reminders')
                total_reminders = cursor.fetchone()[0]
                
                # Active reminders
                cursor.execute('SELECT COUNT(*) FROM reminders WHERE is_active = TRUE')
                active_reminders = cursor.fetchone()[0]
                
                # Completed reminders
                cursor.execute('SELECT COUNT(*) FROM reminders WHERE completed_at IS NOT NULL')
                completed_reminders = cursor.fetchone()[0]
                
                # Reminders by type
                cursor.execute('''
                    SELECT reminder_type, COUNT(*) FROM reminders
                    GROUP BY reminder_type
                ''')
                type_counts = dict(cursor.fetchall())
                
                # Upcoming reminders (next 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) FROM reminders 
                    WHERE is_active = TRUE 
                    AND (trigger_time BETWEEN datetime('now') AND datetime('now', '+1 day')
                         OR next_trigger BETWEEN datetime('now') AND datetime('now', '+1 day'))
                ''')
                upcoming_reminders = cursor.fetchone()[0]
                
                return {
                    "total_reminders": total_reminders,
                    "active_reminders": active_reminders,
                    "completed_reminders": completed_reminders,
                    "reminders_by_type": type_counts,
                    "upcoming_reminders": upcoming_reminders,
                    "system_running": self.running
                }
                
        except Exception as e:
            logger.error(f"Failed to get reminder statistics: {e}")
            return {}
    
    async def stop(self):
        """Stop the reminder system."""
        self.running = False
        logger.info("Reminder system stopped")