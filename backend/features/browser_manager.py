#!/usr/bin/env python3
"""
Browser Enhancement for Westfall Personal Assistant

Enhanced browser with tab management, bookmarks, history tracking,
download manager, password manager integration, and find functionality.
"""

import asyncio
import logging
import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)


class BrowserManager:
    """Enhanced browser with advanced features and integrations."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/browser.db"
        
        # Browser state
        self.current_tabs = {}
        self.active_tab_id = None
        self.next_tab_id = 1
        self.downloads = {}
        self.next_download_id = 1
        
        # Settings
        self.download_directory = os.path.expanduser("~/Downloads")
        self.max_history_days = 30
        self.auto_clear_downloads = True
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for browser data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tabs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tabs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tab_id TEXT UNIQUE NOT NULL,
                        title TEXT,
                        url TEXT,
                        favicon_url TEXT,
                        is_active BOOLEAN DEFAULT FALSE,
                        is_pinned BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create bookmarks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bookmarks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL,
                        description TEXT,
                        folder_path TEXT DEFAULT '',
                        tags TEXT,
                        favicon_url TEXT,
                        visit_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create bookmark folders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bookmark_folders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        parent_path TEXT DEFAULT '',
                        full_path TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS browse_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        title TEXT,
                        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        tab_id TEXT,
                        favicon_url TEXT,
                        session_id TEXT
                    )
                ''')
                
                # Create downloads table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        download_id TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_path TEXT,
                        file_size INTEGER DEFAULT 0,
                        downloaded_bytes INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        tab_id TEXT,
                        mime_type TEXT
                    )
                ''')
                
                # Create search history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        search_engine TEXT DEFAULT 'google',
                        result_url TEXT,
                        clicked BOOLEAN DEFAULT FALSE,
                        search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create saved passwords table (encrypted)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS saved_passwords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT NOT NULL,
                        url TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password_encrypted TEXT NOT NULL,
                        form_data TEXT,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_url ON browse_history(url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_time ON browse_history(visit_time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_folder ON bookmarks(folder_path)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)')
                
                conn.commit()
                logger.info("Browser database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize browser database: {e}")
            raise
    
    async def create_tab(self, url: str = "about:blank", title: str = "New Tab") -> str:
        """Create a new browser tab."""
        tab_id = f"tab_{self.next_tab_id}"
        self.next_tab_id += 1
        
        try:
            # Add to memory
            self.current_tabs[tab_id] = {
                "id": tab_id,
                "title": title,
                "url": url,
                "favicon_url": None,
                "is_active": False,
                "is_pinned": False,
                "history": [],
                "history_index": -1,
                "find_text": "",
                "zoom_level": 1.0
            }
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tabs (tab_id, title, url, is_active)
                    VALUES (?, ?, ?, ?)
                ''', (tab_id, title, url, False))
                conn.commit()
            
            logger.info(f"Created new tab: {tab_id}")
            return tab_id
            
        except Exception as e:
            logger.error(f"Failed to create tab: {e}")
            return None
    
    async def close_tab(self, tab_id: str) -> bool:
        """Close a browser tab."""
        try:
            if tab_id in self.current_tabs:
                # Remove from memory
                del self.current_tabs[tab_id]
                
                # If this was the active tab, switch to another
                if self.active_tab_id == tab_id:
                    if self.current_tabs:
                        self.active_tab_id = next(iter(self.current_tabs))
                    else:
                        self.active_tab_id = None
                
                # Remove from database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM tabs WHERE tab_id = ?', (tab_id,))
                    conn.commit()
                
                logger.info(f"Closed tab: {tab_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to close tab {tab_id}: {e}")
            return False
    
    async def switch_tab(self, tab_id: str) -> bool:
        """Switch to a specific tab."""
        try:
            if tab_id in self.current_tabs:
                # Update old active tab
                if self.active_tab_id:
                    self.current_tabs[self.active_tab_id]["is_active"] = False
                
                # Set new active tab
                self.active_tab_id = tab_id
                self.current_tabs[tab_id]["is_active"] = True
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tabs SET is_active = FALSE')
                    cursor.execute('UPDATE tabs SET is_active = TRUE WHERE tab_id = ?', (tab_id,))
                    conn.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to switch to tab {tab_id}: {e}")
            return False
    
    async def navigate_to(self, tab_id: str, url: str) -> bool:
        """Navigate tab to URL and record in history."""
        try:
            if tab_id not in self.current_tabs:
                return False
            
            # Parse and validate URL
            if not url.startswith(('http://', 'https://')):
                if not url.startswith('file://') and not url.startswith('about:'):
                    url = f"https://{url}"
            
            tab = self.current_tabs[tab_id]
            
            # Add to tab history
            if tab["history_index"] < len(tab["history"]) - 1:
                # Remove forward history if navigating to new page
                tab["history"] = tab["history"][:tab["history_index"] + 1]
            
            tab["history"].append({
                "url": url,
                "title": "",
                "timestamp": datetime.now().isoformat()
            })
            tab["history_index"] = len(tab["history"]) - 1
            tab["url"] = url
            
            # Record in global history
            await self._record_history(url, "", tab_id)
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tabs SET url = ?, updated_at = ? WHERE tab_id = ?
                ''', (url, datetime.now().isoformat(), tab_id))
                conn.commit()
            
            logger.info(f"Tab {tab_id} navigated to: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate tab {tab_id} to {url}: {e}")
            return False
    
    async def update_tab_title(self, tab_id: str, title: str) -> bool:
        """Update tab title."""
        try:
            if tab_id in self.current_tabs:
                self.current_tabs[tab_id]["title"] = title
                
                # Update current history entry
                history = self.current_tabs[tab_id]["history"]
                if history and self.current_tabs[tab_id]["history_index"] >= 0:
                    current_index = self.current_tabs[tab_id]["history_index"]
                    history[current_index]["title"] = title
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE tabs SET title = ?, updated_at = ? WHERE tab_id = ?
                    ''', (title, datetime.now().isoformat(), tab_id))
                    conn.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update tab title: {e}")
            return False
    
    async def go_back(self, tab_id: str) -> bool:
        """Navigate back in tab history."""
        try:
            if tab_id not in self.current_tabs:
                return False
            
            tab = self.current_tabs[tab_id]
            if tab["history_index"] > 0:
                tab["history_index"] -= 1
                new_url = tab["history"][tab["history_index"]]["url"]
                tab["url"] = new_url
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tabs SET url = ? WHERE tab_id = ?', (new_url, tab_id))
                    conn.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to go back in tab {tab_id}: {e}")
            return False
    
    async def go_forward(self, tab_id: str) -> bool:
        """Navigate forward in tab history."""
        try:
            if tab_id not in self.current_tabs:
                return False
            
            tab = self.current_tabs[tab_id]
            if tab["history_index"] < len(tab["history"]) - 1:
                tab["history_index"] += 1
                new_url = tab["history"][tab["history_index"]]["url"]
                tab["url"] = new_url
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tabs SET url = ? WHERE tab_id = ?', (new_url, tab_id))
                    conn.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to go forward in tab {tab_id}: {e}")
            return False
    
    async def _record_history(self, url: str, title: str, tab_id: str) -> bool:
        """Record page visit in browser history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if URL was visited recently (within last hour)
                cursor.execute('''
                    SELECT id, visit_count FROM browse_history 
                    WHERE url = ? AND visit_time > datetime('now', '-1 hour')
                    ORDER BY visit_time DESC LIMIT 1
                ''', (url,))
                
                recent_visit = cursor.fetchone()
                
                if recent_visit:
                    # Update existing recent entry
                    cursor.execute('''
                        UPDATE browse_history 
                        SET visit_count = ?, visit_time = ?, title = ?
                        WHERE id = ?
                    ''', (recent_visit[1] + 1, datetime.now().isoformat(), title, recent_visit[0]))
                else:
                    # Create new history entry
                    cursor.execute('''
                        INSERT INTO browse_history (url, title, tab_id)
                        VALUES (?, ?, ?)
                    ''', (url, title, tab_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record history for {url}: {e}")
            return False
    
    async def add_bookmark(self, title: str, url: str, folder_path: str = "", 
                          description: str = "", tags: List[str] = None) -> int:
        """Add a bookmark."""
        try:
            tags_str = json.dumps(tags) if tags else "[]"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO bookmarks (title, url, description, folder_path, tags)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, url, description, folder_path, tags_str))
                
                bookmark_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added bookmark: {title}")
                return bookmark_id
                
        except Exception as e:
            logger.error(f"Failed to add bookmark: {e}")
            return None
    
    async def remove_bookmark(self, bookmark_id: int) -> bool:
        """Remove a bookmark."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to remove bookmark {bookmark_id}: {e}")
            return False
    
    async def get_bookmarks(self, folder_path: str = None) -> List[Dict]:
        """Get bookmarks, optionally filtered by folder."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if folder_path is not None:
                    cursor.execute('''
                        SELECT * FROM bookmarks WHERE folder_path = ?
                        ORDER BY title
                    ''', (folder_path,))
                else:
                    cursor.execute('SELECT * FROM bookmarks ORDER BY folder_path, title')
                
                results = cursor.fetchall()
                return self._format_bookmarks(results)
                
        except Exception as e:
            logger.error(f"Failed to get bookmarks: {e}")
            return []
    
    def _format_bookmarks(self, raw_bookmarks: List) -> List[Dict]:
        """Format raw database bookmarks into dictionaries."""
        bookmarks = []
        
        for row in raw_bookmarks:
            bookmark = {
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "description": row[3],
                "folder_path": row[4],
                "tags": json.loads(row[5]) if row[5] else [],
                "favicon_url": row[6],
                "visit_count": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
            bookmarks.append(bookmark)
        
        return bookmarks
    
    async def search_history(self, query: str, limit: int = 50) -> List[Dict]:
        """Search browser history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM browse_history 
                    WHERE url LIKE ? OR title LIKE ?
                    ORDER BY visit_time DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', limit))
                
                results = cursor.fetchall()
                return self._format_history(results)
                
        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            return []
    
    def _format_history(self, raw_history: List) -> List[Dict]:
        """Format raw database history into dictionaries."""
        history = []
        
        for row in raw_history:
            entry = {
                "id": row[0],
                "url": row[1],
                "title": row[2],
                "visit_time": row[3],
                "visit_count": row[4],
                "tab_id": row[5],
                "favicon_url": row[6],
                "session_id": row[7]
            }
            history.append(entry)
        
        return history
    
    async def clear_history(self, days: int = None) -> int:
        """Clear browser history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if days:
                    cursor.execute('''
                        DELETE FROM browse_history 
                        WHERE visit_time < datetime('now', '-{} days')
                    '''.format(days))
                else:
                    cursor.execute('DELETE FROM browse_history')
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleared {deleted_count} history entries")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return 0
    
    async def start_download(self, url: str, filename: str = None, tab_id: str = None) -> str:
        """Start a file download."""
        try:
            download_id = f"download_{self.next_download_id}"
            self.next_download_id += 1
            
            # Generate filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or "download"
            
            # Ensure unique filename
            file_path = os.path.join(self.download_directory, filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                file_path = os.path.join(self.download_directory, f"{name}_{counter}{ext}")
                counter += 1
            
            # Detect MIME type
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            
            # Record download
            download_info = {
                "id": download_id,
                "url": url,
                "filename": filename,
                "file_path": file_path,
                "status": "pending",
                "start_time": datetime.now().isoformat(),
                "tab_id": tab_id,
                "mime_type": mime_type,
                "progress": 0
            }
            
            self.downloads[download_id] = download_info
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO downloads 
                    (download_id, url, filename, file_path, status, tab_id, mime_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (download_id, url, filename, file_path, "pending", tab_id, mime_type))
                conn.commit()
            
            logger.info(f"Started download: {download_id} - {filename}")
            return download_id
            
        except Exception as e:
            logger.error(f"Failed to start download: {e}")
            return None
    
    async def get_downloads(self, status: str = None) -> List[Dict]:
        """Get download list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT * FROM downloads WHERE status = ?
                        ORDER BY start_time DESC
                    ''', (status,))
                else:
                    cursor.execute('SELECT * FROM downloads ORDER BY start_time DESC')
                
                results = cursor.fetchall()
                return self._format_downloads(results)
                
        except Exception as e:
            logger.error(f"Failed to get downloads: {e}")
            return []
    
    def _format_downloads(self, raw_downloads: List) -> List[Dict]:
        """Format raw database downloads into dictionaries."""
        downloads = []
        
        for row in raw_downloads:
            download = {
                "id": row[0],
                "download_id": row[1],
                "url": row[2],
                "filename": row[3],
                "file_path": row[4],
                "file_size": row[5],
                "downloaded_bytes": row[6],
                "status": row[7],
                "start_time": row[8],
                "end_time": row[9],
                "tab_id": row[10],
                "mime_type": row[11],
                "progress": (row[6] / row[5] * 100) if row[5] > 0 else 0
            }
            downloads.append(download)
        
        return downloads
    
    async def get_tabs(self) -> List[Dict]:
        """Get all current tabs."""
        return list(self.current_tabs.values())
    
    async def get_browser_stats(self) -> Dict:
        """Get browser usage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total history entries
                cursor.execute('SELECT COUNT(*) FROM browse_history')
                total_history = cursor.fetchone()[0]
                
                # Total bookmarks
                cursor.execute('SELECT COUNT(*) FROM bookmarks')
                total_bookmarks = cursor.fetchone()[0]
                
                # Total downloads
                cursor.execute('SELECT COUNT(*) FROM downloads')
                total_downloads = cursor.fetchone()[0]
                
                # Recent history (last 7 days)
                cursor.execute('''
                    SELECT COUNT(*) FROM browse_history 
                    WHERE visit_time > datetime('now', '-7 days')
                ''')
                recent_history = cursor.fetchone()[0]
                
                # Top domains
                cursor.execute('''
                    SELECT url, COUNT(*) as count FROM browse_history
                    GROUP BY substr(url, 1, instr(url || '/', '/', 8) - 1)
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                top_domains = cursor.fetchall()
                
                return {
                    "total_tabs": len(self.current_tabs),
                    "total_history": total_history,
                    "total_bookmarks": total_bookmarks,
                    "total_downloads": total_downloads,
                    "recent_history": recent_history,
                    "top_domains": [{"domain": d[0], "visits": d[1]} for d in top_domains]
                }
                
        except Exception as e:
            logger.error(f"Failed to get browser stats: {e}")
            return {}