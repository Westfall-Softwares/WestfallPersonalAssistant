#!/usr/bin/env python3
"""
Keyboard Shortcuts Manager for Westfall Personal Assistant

Manages global and context-specific keyboard shortcuts with customization.
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import re

logger = logging.getLogger(__name__)


class ShortcutManager:
    """Keyboard shortcuts management with customization support."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/shortcuts.db"
        
        # Registered shortcuts
        self.shortcuts = {}
        self.context_shortcuts = {}
        
        # Action callbacks
        self.action_callbacks = {}
        
        # Default shortcuts configuration
        self.default_shortcuts = {
            # Global shortcuts
            "global": {
                "Ctrl+Home": {"action": "navigate_dashboard", "description": "Go to Dashboard"},
                "Ctrl+1": {"action": "navigate_news", "description": "Open News Reader"},
                "Ctrl+2": {"action": "navigate_music", "description": "Open Music Player"},
                "Ctrl+3": {"action": "navigate_browser", "description": "Open Browser"},
                "Ctrl+4": {"action": "navigate_calculator", "description": "Open Calculator"},
                "Ctrl+5": {"action": "navigate_ai_chat", "description": "Open AI Assistant"},
                "Ctrl+K": {"action": "open_command_palette", "description": "Open Command Palette"},
                "Ctrl+,": {"action": "open_settings", "description": "Open Settings"},
                "Ctrl+N": {"action": "context_new", "description": "New (context-aware)"},
                "Ctrl+S": {"action": "context_save", "description": "Save"},
                "Ctrl+F": {"action": "context_find", "description": "Find"},
                "Ctrl+Z": {"action": "context_undo", "description": "Undo"},
                "Ctrl+Y": {"action": "context_redo", "description": "Redo"},
                "Escape": {"action": "context_escape", "description": "Close dialog/return"},
                "F11": {"action": "toggle_fullscreen", "description": "Toggle Fullscreen"},
                "Alt+F4": {"action": "close_application", "description": "Close Application"}
            },
            
            # Music player shortcuts
            "music": {
                "Space": {"action": "music_play_pause", "description": "Play/Pause"},
                "Ctrl+Right": {"action": "music_next", "description": "Next Track"},
                "Ctrl+Left": {"action": "music_previous", "description": "Previous Track"},
                "Ctrl+Up": {"action": "music_volume_up", "description": "Volume Up"},
                "Ctrl+Down": {"action": "music_volume_down", "description": "Volume Down"},
                "Ctrl+M": {"action": "music_mute", "description": "Mute/Unmute"},
                "Ctrl+L": {"action": "music_open_library", "description": "Open Library"},
                "Ctrl+P": {"action": "music_create_playlist", "description": "Create Playlist"}
            },
            
            # Browser shortcuts
            "browser": {
                "Ctrl+T": {"action": "browser_new_tab", "description": "New Tab"},
                "Ctrl+W": {"action": "browser_close_tab", "description": "Close Tab"},
                "Ctrl+Shift+T": {"action": "browser_restore_tab", "description": "Restore Tab"},
                "Ctrl+L": {"action": "browser_address_bar", "description": "Focus Address Bar"},
                "Ctrl+R": {"action": "browser_refresh", "description": "Refresh Page"},
                "Ctrl+D": {"action": "browser_bookmark", "description": "Bookmark Page"},
                "Ctrl+H": {"action": "browser_history", "description": "Open History"},
                "Ctrl+J": {"action": "browser_downloads", "description": "Open Downloads"},
                "Ctrl+Tab": {"action": "browser_next_tab", "description": "Next Tab"},
                "Ctrl+Shift+Tab": {"action": "browser_previous_tab", "description": "Previous Tab"},
                "Alt+Left": {"action": "browser_back", "description": "Go Back"},
                "Alt+Right": {"action": "browser_forward", "description": "Go Forward"},
                "F5": {"action": "browser_refresh", "description": "Refresh Page"},
                "F12": {"action": "browser_dev_tools", "description": "Developer Tools"}
            },
            
            # Calculator shortcuts
            "calculator": {
                "Enter": {"action": "calculator_calculate", "description": "Calculate"},
                "Escape": {"action": "calculator_clear", "description": "Clear"},
                "Delete": {"action": "calculator_clear_entry", "description": "Clear Entry"},
                "Ctrl+M": {"action": "calculator_memory_store", "description": "Memory Store"},
                "Ctrl+R": {"action": "calculator_memory_recall", "description": "Memory Recall"},
                "Ctrl+P": {"action": "calculator_memory_plus", "description": "Memory Plus"},
                "Ctrl+-": {"action": "calculator_memory_minus", "description": "Memory Minus"},
                "Ctrl+L": {"action": "calculator_memory_clear", "description": "Memory Clear"},
                "F9": {"action": "calculator_toggle_mode", "description": "Toggle Mode"},
                "F2": {"action": "calculator_history", "description": "Show History"}
            },
            
            # News reader shortcuts
            "news": {
                "Ctrl+R": {"action": "news_refresh", "description": "Refresh Articles"},
                "Ctrl+A": {"action": "news_add_source", "description": "Add Source"},
                "Space": {"action": "news_mark_read", "description": "Mark as Read"},
                "J": {"action": "news_next_article", "description": "Next Article"},
                "K": {"action": "news_previous_article", "description": "Previous Article"},
                "O": {"action": "news_open_article", "description": "Open Article"},
                "S": {"action": "news_save_article", "description": "Save Article"},
                "A": {"action": "news_archive_article", "description": "Archive Article"}
            },
            
            # AI Chat shortcuts
            "ai_chat": {
                "Ctrl+Enter": {"action": "ai_send_message", "description": "Send Message"},
                "Ctrl+Shift+C": {"action": "ai_new_conversation", "description": "New Conversation"},
                "Ctrl+Shift+T": {"action": "ai_toggle_thinking", "description": "Toggle Thinking Mode"},
                "Ctrl+Shift+V": {"action": "ai_voice_input", "description": "Voice Input"},
                "Ctrl+E": {"action": "ai_export_conversation", "description": "Export Conversation"},
                "Up": {"action": "ai_previous_message", "description": "Previous Message (in input)"},
                "Down": {"action": "ai_next_message", "description": "Next Message (in input)"}
            }
        }
        
        # Initialize database
        self._init_database()
        
        # Load shortcuts will be called later
        self._shortcuts_loaded = False
    
    def _init_database(self):
        """Initialize SQLite database for shortcuts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create shortcuts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shortcuts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcut_key TEXT NOT NULL,
                        context TEXT NOT NULL,
                        action TEXT NOT NULL,
                        description TEXT,
                        is_custom BOOLEAN DEFAULT FALSE,
                        is_enabled BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(shortcut_key, context)
                    )
                ''')
                
                # Create shortcut usage statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shortcut_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcut_key TEXT NOT NULL,
                        context TEXT NOT NULL,
                        action TEXT NOT NULL,
                        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                ''')
                
                # Create shortcut conflicts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shortcut_conflicts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcut_key TEXT NOT NULL,
                        context1 TEXT NOT NULL,
                        context2 TEXT NOT NULL,
                        action1 TEXT NOT NULL,
                        action2 TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Shortcuts database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize shortcuts database: {e}")
            raise
    
    async def _load_shortcuts(self):
        """Load shortcuts from database or initialize with defaults."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM shortcuts')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # Initialize with default shortcuts
                    await self._initialize_default_shortcuts()
                else:
                    # Load existing shortcuts
                    await self._load_existing_shortcuts()
                    
        except Exception as e:
            logger.error(f"Failed to load shortcuts: {e}")
    
    async def _initialize_default_shortcuts(self):
        """Initialize database with default shortcuts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for context, context_shortcuts in self.default_shortcuts.items():
                    for shortcut_key, shortcut_info in context_shortcuts.items():
                        cursor.execute('''
                            INSERT INTO shortcuts (shortcut_key, context, action, description, is_custom)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            shortcut_key,
                            context,
                            shortcut_info["action"],
                            shortcut_info["description"],
                            False
                        ))
                        
                        # Register in memory
                        self._register_shortcut(shortcut_key, context, shortcut_info["action"])
                
                conn.commit()
                logger.info("Default shortcuts initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize default shortcuts: {e}")
    
    async def _load_existing_shortcuts(self):
        """Load existing shortcuts from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT shortcut_key, context, action FROM shortcuts
                    WHERE is_enabled = TRUE
                ''')
                
                for shortcut_key, context, action in cursor.fetchall():
                    self._register_shortcut(shortcut_key, context, action)
                    
        except Exception as e:
            logger.error(f"Failed to load existing shortcuts: {e}")
    
    def _register_shortcut(self, shortcut_key: str, context: str, action: str):
        """Register shortcut in memory."""
        normalized_key = self._normalize_shortcut_key(shortcut_key)
        
        if context == "global":
            self.shortcuts[normalized_key] = action
        else:
            if context not in self.context_shortcuts:
                self.context_shortcuts[context] = {}
            self.context_shortcuts[context][normalized_key] = action
    
    def _normalize_shortcut_key(self, shortcut_key: str) -> str:
        """Normalize shortcut key for consistent matching."""
        # Convert to lowercase and standardize modifier order
        parts = shortcut_key.lower().split('+')
        
        # Standard modifier order: Ctrl, Alt, Shift, then key
        modifiers = []
        key = ""
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control']:
                modifiers.append('ctrl')
            elif part in ['alt']:
                modifiers.append('alt')
            elif part in ['shift']:
                modifiers.append('shift')
            else:
                key = part
        
        # Remove duplicates and sort
        modifiers = sorted(list(set(modifiers)))
        
        if key:
            return '+'.join(modifiers + [key])
        else:
            return '+'.join(modifiers)
    
    async def register_action_callback(self, action: str, callback: Callable):
        """Register callback function for an action."""
        self.action_callbacks[action] = callback
        logger.info(f"Registered callback for action: {action}")
    
    async def handle_shortcut(self, shortcut_key: str, context: str = "global") -> Dict:
        """Handle shortcut key press."""
        try:
            normalized_key = self._normalize_shortcut_key(shortcut_key)
            
            # Check context-specific shortcuts first
            if context != "global" and context in self.context_shortcuts:
                if normalized_key in self.context_shortcuts[context]:
                    action = self.context_shortcuts[context][normalized_key]
                    result = await self._execute_action(action, context, shortcut_key)
                    return result
            
            # Check global shortcuts
            if normalized_key in self.shortcuts:
                action = self.shortcuts[normalized_key]
                result = await self._execute_action(action, "global", shortcut_key)
                return result
            
            return {"status": "not_found", "message": f"No action for shortcut: {shortcut_key}"}
            
        except Exception as e:
            logger.error(f"Failed to handle shortcut {shortcut_key}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_action(self, action: str, context: str, shortcut_key: str) -> Dict:
        """Execute action for shortcut."""
        try:
            # Record usage
            await self._record_usage(shortcut_key, context, action)
            
            # Execute callback if registered
            if action in self.action_callbacks:
                result = await self.action_callbacks[action]()
                return {"status": "success", "action": action, "result": result}
            
            # Return action info for external handling
            return {
                "status": "action_required",
                "action": action,
                "context": context,
                "shortcut": shortcut_key,
                "message": f"Action '{action}' needs to be handled externally"
            }
            
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            return {"status": "error", "action": action, "message": str(e)}
    
    async def _record_usage(self, shortcut_key: str, context: str, action: str):
        """Record shortcut usage for statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO shortcut_usage (shortcut_key, context, action)
                    VALUES (?, ?, ?)
                ''', (shortcut_key, context, action))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record shortcut usage: {e}")
    
    async def add_custom_shortcut(self, shortcut_key: str, context: str, action: str, description: str = "") -> bool:
        """Add custom shortcut."""
        try:
            # Check for conflicts
            conflicts = await self._check_conflicts(shortcut_key, context)
            if conflicts:
                logger.warning(f"Shortcut conflict detected: {shortcut_key} in {context}")
                return False
            
            # Add to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO shortcuts 
                    (shortcut_key, context, action, description, is_custom, is_enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (shortcut_key, context, action, description, True, True))
                conn.commit()
            
            # Register in memory
            self._register_shortcut(shortcut_key, context, action)
            
            logger.info(f"Added custom shortcut: {shortcut_key} -> {action} in {context}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom shortcut: {e}")
            return False
    
    async def remove_shortcut(self, shortcut_key: str, context: str) -> bool:
        """Remove shortcut."""
        try:
            normalized_key = self._normalize_shortcut_key(shortcut_key)
            
            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE shortcuts SET is_enabled = FALSE
                    WHERE shortcut_key = ? AND context = ?
                ''', (shortcut_key, context))
                conn.commit()
            
            # Remove from memory
            if context == "global" and normalized_key in self.shortcuts:
                del self.shortcuts[normalized_key]
            elif context in self.context_shortcuts and normalized_key in self.context_shortcuts[context]:
                del self.context_shortcuts[context][normalized_key]
            
            logger.info(f"Removed shortcut: {shortcut_key} from {context}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove shortcut: {e}")
            return False
    
    async def _check_conflicts(self, shortcut_key: str, context: str) -> List[Dict]:
        """Check for shortcut conflicts."""
        try:
            conflicts = []
            normalized_key = self._normalize_shortcut_key(shortcut_key)
            
            # Check global shortcuts
            if context != "global" and normalized_key in self.shortcuts:
                conflicts.append({
                    "existing_context": "global",
                    "existing_action": self.shortcuts[normalized_key],
                    "new_context": context
                })
            
            # Check context shortcuts
            for ctx, ctx_shortcuts in self.context_shortcuts.items():
                if ctx != context and normalized_key in ctx_shortcuts:
                    conflicts.append({
                        "existing_context": ctx,
                        "existing_action": ctx_shortcuts[normalized_key],
                        "new_context": context
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to check conflicts: {e}")
            return []
    
    async def get_shortcuts(self, context: str = None) -> Dict:
        """Get shortcuts, optionally filtered by context."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if context:
                    cursor.execute('''
                        SELECT shortcut_key, context, action, description, is_custom
                        FROM shortcuts 
                        WHERE context = ? AND is_enabled = TRUE
                        ORDER BY shortcut_key
                    ''', (context,))
                else:
                    cursor.execute('''
                        SELECT shortcut_key, context, action, description, is_custom
                        FROM shortcuts 
                        WHERE is_enabled = TRUE
                        ORDER BY context, shortcut_key
                    ''')
                
                shortcuts = {}
                for row in cursor.fetchall():
                    shortcut_key, ctx, action, description, is_custom = row
                    
                    if ctx not in shortcuts:
                        shortcuts[ctx] = []
                    
                    shortcuts[ctx].append({
                        "key": shortcut_key,
                        "action": action,
                        "description": description,
                        "is_custom": bool(is_custom)
                    })
                
                return shortcuts
                
        except Exception as e:
            logger.error(f"Failed to get shortcuts: {e}")
            return {}
    
    async def get_shortcut_conflicts(self) -> List[Dict]:
        """Get unresolved shortcut conflicts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM shortcut_conflicts
                    WHERE resolved = FALSE
                    ORDER BY created_at DESC
                ''')
                
                conflicts = []
                for row in cursor.fetchall():
                    conflict = {
                        "id": row[0],
                        "shortcut_key": row[1],
                        "context1": row[2],
                        "context2": row[3],
                        "action1": row[4],
                        "action2": row[5],
                        "created_at": row[7]
                    }
                    conflicts.append(conflict)
                
                return conflicts
                
        except Exception as e:
            logger.error(f"Failed to get shortcut conflicts: {e}")
            return []
    
    async def get_usage_statistics(self) -> Dict:
        """Get shortcut usage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Most used shortcuts
                cursor.execute('''
                    SELECT shortcut_key, context, action, COUNT(*) as usage_count
                    FROM shortcut_usage
                    GROUP BY shortcut_key, context, action
                    ORDER BY usage_count DESC
                    LIMIT 10
                ''')
                
                popular_shortcuts = []
                for row in cursor.fetchall():
                    popular_shortcuts.append({
                        "shortcut": row[0],
                        "context": row[1],
                        "action": row[2],
                        "usage_count": row[3]
                    })
                
                # Usage by context
                cursor.execute('''
                    SELECT context, COUNT(*) as usage_count
                    FROM shortcut_usage
                    GROUP BY context
                    ORDER BY usage_count DESC
                ''')
                
                context_usage = dict(cursor.fetchall())
                
                # Recent usage
                cursor.execute('''
                    SELECT COUNT(*) FROM shortcut_usage
                    WHERE used_at > datetime('now', '-1 day')
                ''')
                recent_usage = cursor.fetchone()[0]
                
                return {
                    "popular_shortcuts": popular_shortcuts,
                    "context_usage": context_usage,
                    "recent_usage": recent_usage,
                    "total_shortcuts": len(self.shortcuts) + sum(len(ctx) for ctx in self.context_shortcuts.values())
                }
                
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {}
    
    async def export_shortcuts(self) -> Dict:
        """Export shortcuts configuration."""
        try:
            shortcuts = await self.get_shortcuts()
            return {
                "shortcuts": shortcuts,
                "export_date": datetime.now().isoformat(),
                "version": "1.0"
            }
        except Exception as e:
            logger.error(f"Failed to export shortcuts: {e}")
            return {}
    
    async def import_shortcuts(self, shortcuts_data: Dict) -> Dict:
        """Import shortcuts configuration."""
        try:
            imported_count = 0
            failed_count = 0
            conflicts = []
            
            shortcuts = shortcuts_data.get("shortcuts", {})
            
            for context, context_shortcuts in shortcuts.items():
                for shortcut_info in context_shortcuts:
                    shortcut_key = shortcut_info["key"]
                    action = shortcut_info["action"]
                    description = shortcut_info.get("description", "")
                    
                    # Check for conflicts
                    shortcut_conflicts = await self._check_conflicts(shortcut_key, context)
                    if shortcut_conflicts:
                        conflicts.append({
                            "shortcut": shortcut_key,
                            "context": context,
                            "conflicts": shortcut_conflicts
                        })
                        failed_count += 1
                        continue
                    
                    # Add shortcut
                    success = await self.add_custom_shortcut(shortcut_key, context, action, description)
                    if success:
                        imported_count += 1
                    else:
                        failed_count += 1
            
            return {
                "imported_count": imported_count,
                "failed_count": failed_count,
                "conflicts": conflicts
            }
            
        except Exception as e:
            logger.error(f"Failed to import shortcuts: {e}")
            return {"error": str(e)}
    
    async def reset_to_defaults(self) -> bool:
        """Reset shortcuts to default configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear all shortcuts
                cursor.execute('DELETE FROM shortcuts')
                
                # Clear usage history
                cursor.execute('DELETE FROM shortcut_usage')
                
                conn.commit()
            
            # Clear memory
            self.shortcuts.clear()
            self.context_shortcuts.clear()
            
            # Reinitialize defaults
            await self._initialize_default_shortcuts()
            
            logger.info("Reset shortcuts to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset shortcuts: {e}")
            return False