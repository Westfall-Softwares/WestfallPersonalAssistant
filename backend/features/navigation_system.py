#!/usr/bin/env python3
"""
Navigation System for Westfall Personal Assistant

Provides navigation management, breadcrumb trails, command palette,
and global search functionality.
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)


class NavigationManager:
    """Navigation system with breadcrumbs, history, and search."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/navigation.db"
        
        # Navigation state
        self.current_location = {"module": "dashboard", "path": [], "context": {}}
        self.navigation_history = []
        self.max_history_size = 100
        
        # Search indexing
        self.search_index = {}
        
        # Available modules and their actions
        self.modules = {
            "dashboard": {
                "name": "Dashboard",
                "icon": "dashboard",
                "actions": ["view_stats", "quick_actions"],
                "shortcuts": ["Ctrl+Home"]
            },
            "news": {
                "name": "News Reader",
                "icon": "newspaper",
                "actions": ["fetch_articles", "search", "add_source", "manage_sources"],
                "shortcuts": ["Ctrl+1"]
            },
            "music": {
                "name": "Music Player",
                "icon": "music_note",
                "actions": ["play", "pause", "stop", "scan_library", "create_playlist"],
                "shortcuts": ["Ctrl+2", "Space"]
            },
            "browser": {
                "name": "Browser",
                "icon": "web",
                "actions": ["new_tab", "navigate", "bookmark", "history", "downloads"],
                "shortcuts": ["Ctrl+3", "Ctrl+T", "Ctrl+L"]
            },
            "calculator": {
                "name": "Calculator",
                "icon": "calculate",
                "actions": ["calculate", "convert_units", "memory_store", "view_history"],
                "shortcuts": ["Ctrl+4"]
            },
            "ai_chat": {
                "name": "AI Assistant",
                "icon": "smart_toy",
                "actions": ["new_chat", "thinking_mode", "voice_input"],
                "shortcuts": ["Ctrl+5", "Ctrl+K"]
            },
            "settings": {
                "name": "Settings",
                "icon": "settings",
                "actions": ["account", "preferences", "security", "backup"],
                "shortcuts": ["Ctrl+,"]
            }
        }
        
        # Initialize database
        self._init_database()
        
        # Build search index
        asyncio.create_task(self._build_search_index())
    
    def _init_database(self):
        """Initialize SQLite database for navigation data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create navigation history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS navigation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        module TEXT NOT NULL,
                        path TEXT,
                        context TEXT,
                        title TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                ''')
                
                # Create search index table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id TEXT NOT NULL,
                        item_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        keywords TEXT,
                        module TEXT NOT NULL,
                        action TEXT,
                        metadata TEXT,
                        search_weight INTEGER DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create quick actions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quick_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        module TEXT NOT NULL,
                        action TEXT NOT NULL,
                        icon TEXT,
                        shortcut TEXT,
                        frequency INTEGER DEFAULT 0,
                        last_used TIMESTAMP,
                        enabled BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Create breadcrumb templates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS breadcrumb_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        module TEXT NOT NULL,
                        path_pattern TEXT NOT NULL,
                        template TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Navigation database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize navigation database: {e}")
            raise
    
    async def navigate_to(self, module: str, path: List[str] = None, context: Dict = None) -> bool:
        """Navigate to a specific module and path."""
        try:
            if module not in self.modules:
                logger.error(f"Unknown module: {module}")
                return False
            
            # Store current location in history
            if self.current_location["module"] != "dashboard":  # Don't store dashboard visits
                await self._add_to_history(self.current_location)
            
            # Update current location
            self.current_location = {
                "module": module,
                "path": path or [],
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate title for history
            title = self._generate_title(module, path, context)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO navigation_history (module, path, context, title)
                    VALUES (?, ?, ?, ?)
                ''', (module, json.dumps(path or []), json.dumps(context or {}), title))
                conn.commit()
            
            logger.info(f"Navigated to: {module} -> {'/'.join(path or [])}")
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def go_back(self) -> Optional[Dict]:
        """Navigate back to previous location."""
        try:
            if len(self.navigation_history) > 0:
                previous_location = self.navigation_history.pop()
                self.current_location = previous_location
                return previous_location
            
            return None
            
        except Exception as e:
            logger.error(f"Go back failed: {e}")
            return None
    
    async def go_forward(self) -> bool:
        """Navigate forward (if available)."""
        # This would require a forward stack implementation
        # For now, return False as it's not implemented
        return False
    
    def get_current_location(self) -> Dict:
        """Get current navigation location."""
        return self.current_location.copy()
    
    def get_breadcrumbs(self) -> List[Dict]:
        """Generate breadcrumbs for current location."""
        breadcrumbs = []
        
        # Always start with dashboard
        breadcrumbs.append({
            "title": "Dashboard",
            "module": "dashboard",
            "path": [],
            "is_current": False
        })
        
        current_module = self.current_location["module"]
        current_path = self.current_location["path"]
        
        if current_module != "dashboard":
            # Add module breadcrumb
            breadcrumbs.append({
                "title": self.modules[current_module]["name"],
                "module": current_module,
                "path": [],
                "is_current": len(current_path) == 0
            })
            
            # Add path breadcrumbs
            for i, path_segment in enumerate(current_path):
                is_current = i == len(current_path) - 1
                breadcrumbs.append({
                    "title": self._format_path_segment(path_segment),
                    "module": current_module,
                    "path": current_path[:i+1],
                    "is_current": is_current
                })
        else:
            breadcrumbs[-1]["is_current"] = True
        
        return breadcrumbs
    
    def _format_path_segment(self, segment: str) -> str:
        """Format path segment for display."""
        # Convert snake_case to Title Case
        return segment.replace("_", " ").title()
    
    async def global_search(self, query: str, limit: int = 50) -> List[Dict]:
        """Perform global search across all modules and content."""
        try:
            if not query.strip():
                return []
            
            results = []
            
            # Search in indexed content
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fuzzy search in search index
                search_terms = query.lower().split()
                search_conditions = []
                search_params = []
                
                for term in search_terms:
                    search_conditions.append(
                        '(LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(keywords) LIKE ?)'
                    )
                    search_params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
                
                search_query = f'''
                    SELECT * FROM search_index 
                    WHERE {' AND '.join(search_conditions)}
                    ORDER BY search_weight DESC, title ASC
                    LIMIT ?
                '''
                search_params.append(limit)
                
                cursor.execute(search_query, search_params)
                db_results = cursor.fetchall()
                
                for row in db_results:
                    result = {
                        "id": row[1],
                        "type": row[2],
                        "title": row[3],
                        "description": row[4],
                        "keywords": row[5].split(',') if row[5] else [],
                        "module": row[6],
                        "action": row[7],
                        "metadata": json.loads(row[8]) if row[8] else {},
                        "weight": row[9]
                    }
                    results.append(result)
            
            # Search in modules and actions
            module_results = self._search_modules(query)
            results.extend(module_results)
            
            # Sort by relevance
            results.sort(key=lambda x: x.get("weight", 1), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Global search failed: {e}")
            return []
    
    def _search_modules(self, query: str) -> List[Dict]:
        """Search in modules and actions."""
        results = []
        query_lower = query.lower()
        
        for module_id, module_info in self.modules.items():
            # Search module name
            if query_lower in module_info["name"].lower():
                results.append({
                    "id": f"module_{module_id}",
                    "type": "module",
                    "title": module_info["name"],
                    "description": f"Navigate to {module_info['name']}",
                    "keywords": [module_id, module_info["name"]],
                    "module": module_id,
                    "action": "navigate",
                    "metadata": {"target_module": module_id},
                    "weight": 10
                })
            
            # Search actions
            for action in module_info["actions"]:
                if query_lower in action.lower():
                    results.append({
                        "id": f"action_{module_id}_{action}",
                        "type": "action",
                        "title": self._format_path_segment(action),
                        "description": f"{action.replace('_', ' ').title()} in {module_info['name']}",
                        "keywords": [action, module_info["name"]],
                        "module": module_id,
                        "action": action,
                        "metadata": {"target_module": module_id, "target_action": action},
                        "weight": 5
                    })
        
        return results
    
    async def get_command_palette_suggestions(self, query: str = "") -> List[Dict]:
        """Get suggestions for command palette."""
        try:
            if not query:
                # Return frequently used actions
                return await self._get_frequent_actions()
            
            # Return search results
            return await self.global_search(query, 20)
            
        except Exception as e:
            logger.error(f"Failed to get command palette suggestions: {e}")
            return []
    
    async def _get_frequent_actions(self) -> List[Dict]:
        """Get frequently used actions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM quick_actions 
                    WHERE enabled = TRUE
                    ORDER BY frequency DESC, last_used DESC
                    LIMIT 10
                ''')
                
                results = cursor.fetchall()
                actions = []
                
                for row in results:
                    action = {
                        "id": row[1],
                        "type": "quick_action",
                        "title": row[2],
                        "description": row[3],
                        "keywords": [],
                        "module": row[4],
                        "action": row[5],
                        "icon": row[6],
                        "shortcut": row[7],
                        "metadata": {"frequency": row[8]},
                        "weight": row[8]
                    }
                    actions.append(action)
                
                return actions
                
        except Exception as e:
            logger.error(f"Failed to get frequent actions: {e}")
            return []
    
    async def execute_action(self, action_data: Dict) -> Dict:
        """Execute an action from search/command palette."""
        try:
            action_type = action_data.get("type")
            module = action_data.get("module")
            action = action_data.get("action")
            metadata = action_data.get("metadata", {})
            
            if action_type == "module" or action == "navigate":
                # Navigate to module
                target_module = metadata.get("target_module", module)
                success = await self.navigate_to(target_module)
                
                if success:
                    return {"status": "success", "message": f"Navigated to {target_module}"}
                else:
                    return {"status": "error", "message": "Navigation failed"}
            
            elif action_type == "action":
                # Execute specific action
                # This would integrate with the appropriate module
                await self._record_action_usage(action_data["id"])
                
                return {
                    "status": "success", 
                    "message": f"Action '{action}' executed",
                    "action_data": action_data
                }
            
            else:
                return {"status": "error", "message": "Unknown action type"}
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _record_action_usage(self, action_id: str):
        """Record action usage for frequency tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE quick_actions 
                    SET frequency = frequency + 1, last_used = ?
                    WHERE action_id = ?
                ''', (datetime.now().isoformat(), action_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record action usage: {e}")
    
    async def _build_search_index(self):
        """Build search index for fast searching."""
        try:
            # This would be expanded to index content from all modules
            # For now, just index modules and actions
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing index
                cursor.execute('DELETE FROM search_index')
                
                # Index modules
                for module_id, module_info in self.modules.items():
                    cursor.execute('''
                        INSERT INTO search_index 
                        (item_id, item_type, title, description, keywords, module, action, search_weight)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        f"module_{module_id}",
                        "module",
                        module_info["name"],
                        f"Navigate to {module_info['name']}",
                        module_id,
                        module_id,
                        "navigate",
                        10
                    ))
                
                # Index quick actions
                quick_actions = [
                    ("new_tab", "New Tab", "Open a new browser tab", "browser", "new_tab", "web"),
                    ("new_chat", "New Chat", "Start a new AI conversation", "ai_chat", "new_chat", "smart_toy"),
                    ("play_music", "Play Music", "Play or resume music", "music", "play", "music_note"),
                    ("fetch_news", "Fetch News", "Fetch latest news articles", "news", "fetch_articles", "newspaper"),
                    ("calculate", "Calculator", "Open calculator", "calculator", "calculate", "calculate"),
                ]
                
                for action_id, title, description, module, action, icon in quick_actions:
                    cursor.execute('''
                        INSERT OR REPLACE INTO quick_actions
                        (action_id, title, description, module, action, icon, enabled)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (action_id, title, description, module, action, icon, True))
                    
                    cursor.execute('''
                        INSERT INTO search_index 
                        (item_id, item_type, title, description, keywords, module, action, search_weight)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        action_id,
                        "quick_action",
                        title,
                        description,
                        f"{action_id},{title.lower()}",
                        module,
                        action,
                        5
                    ))
                
                conn.commit()
                logger.info("Search index built successfully")
                
        except Exception as e:
            logger.error(f"Failed to build search index: {e}")
    
    async def _add_to_history(self, location: Dict):
        """Add location to navigation history."""
        self.navigation_history.append(location.copy())
        
        # Limit history size
        if len(self.navigation_history) > self.max_history_size:
            self.navigation_history.pop(0)
    
    def _generate_title(self, module: str, path: List[str], context: Dict) -> str:
        """Generate a human-readable title for navigation history."""
        title_parts = [self.modules.get(module, {}).get("name", module)]
        
        if path:
            title_parts.extend([self._format_path_segment(p) for p in path])
        
        return " → ".join(title_parts)
    
    async def get_navigation_stats(self) -> Dict:
        """Get navigation usage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Most visited modules
                cursor.execute('''
                    SELECT module, COUNT(*) as visits FROM navigation_history
                    GROUP BY module
                    ORDER BY visits DESC
                    LIMIT 5
                ''')
                popular_modules = dict(cursor.fetchall())
                
                # Recent navigation
                cursor.execute('''
                    SELECT COUNT(*) FROM navigation_history
                    WHERE timestamp > datetime('now', '-1 day')
                ''')
                recent_navigations = cursor.fetchone()[0]
                
                # Most used actions
                cursor.execute('''
                    SELECT action_id, title, frequency FROM quick_actions
                    WHERE frequency > 0
                    ORDER BY frequency DESC
                    LIMIT 5
                ''')
                popular_actions = [
                    {"action": row[0], "title": row[1], "frequency": row[2]}
                    for row in cursor.fetchall()
                ]
                
                return {
                    "current_location": self.current_location,
                    "popular_modules": popular_modules,
                    "recent_navigations": recent_navigations,
                    "popular_actions": popular_actions,
                    "available_modules": list(self.modules.keys())
                }
                
        except Exception as e:
            logger.error(f"Failed to get navigation stats: {e}")
            return {}