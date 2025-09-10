#!/usr/bin/env python3
"""
News Reader Implementation for Westfall Personal Assistant

Provides RSS feed support, multiple news source management, article categorization,
offline reading mode, and search functionality.
"""

import asyncio
import logging
import aiohttp
import feedparser
import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class NewsReader:
    """Advanced news reader with RSS feeds, multiple sources, and offline capabilities."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/news.db"
        self.sources = []
        self.cached_articles = []
        self.categories = ["general", "technology", "science", "business", "sports", "health"]
        
        # Initialize database
        self._init_database()
        
        # Load default sources
        self._load_default_sources()
    
    def _init_database(self):
        """Initialize SQLite database for offline storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create articles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id INTEGER,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        summary TEXT,
                        content TEXT,
                        author TEXT,
                        published_date TEXT,
                        category TEXT,
                        tags TEXT,
                        read_status BOOLEAN DEFAULT FALSE,
                        archived BOOLEAN DEFAULT FALSE,
                        rating INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create sources table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS news_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        source_type TEXT DEFAULT 'rss',
                        category TEXT DEFAULT 'general',
                        active BOOLEAN DEFAULT TRUE,
                        refresh_interval INTEGER DEFAULT 3600,
                        last_fetched TIMESTAMP,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create full-text search index
                cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                        title, summary, content, author, tags,
                        content='articles',
                        content_rowid='id'
                    )
                ''')
                
                conn.commit()
                logger.info("News database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize news database: {e}")
            raise
    
    def _load_default_sources(self):
        """Load default news sources."""
        default_sources = [
            {
                "name": "BBC Technology",
                "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
                "category": "technology",
                "active": True
            },
            {
                "name": "Reuters Science",
                "url": "https://feeds.reuters.com/reuters/scienceNews",
                "category": "science",
                "active": True
            },
            {
                "name": "Hacker News",
                "url": "https://feeds.feedburner.com/oreilly/radar",
                "category": "technology",
                "active": True
            }
        ]
        
        for source in default_sources:
            asyncio.run(self.add_source(**source))
    
    async def add_source(self, name: str, url: str, category: str = "general", 
                        source_type: str = "rss", active: bool = True, 
                        refresh_interval: int = 3600) -> bool:
        """Add a new news source."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO news_sources 
                    (name, url, source_type, category, active, refresh_interval, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, url, source_type, category, active, refresh_interval, "{}"))
                
                conn.commit()
                logger.info(f"Added news source: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add news source {name}: {e}")
            return False
    
    async def fetch_articles(self, source_id: int = None, force_refresh: bool = False) -> List[Dict]:
        """Fetch articles from RSS feeds."""
        articles = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get active sources
                if source_id:
                    cursor.execute('SELECT * FROM news_sources WHERE id = ? AND active = TRUE', (source_id,))
                else:
                    cursor.execute('SELECT * FROM news_sources WHERE active = TRUE')
                
                sources = cursor.fetchall()
                
                for source in sources:
                    source_id, name, url, source_type, category, active, refresh_interval, last_fetched, metadata, created_at = source
                    
                    # Check if refresh is needed
                    if not force_refresh and last_fetched:
                        last_fetch_time = datetime.fromisoformat(last_fetched)
                        if datetime.now() - last_fetch_time < timedelta(seconds=refresh_interval):
                            logger.info(f"Skipping {name} - refresh interval not reached")
                            continue
                    
                    logger.info(f"Fetching articles from: {name}")
                    
                    try:
                        if source_type == "rss":
                            source_articles = await self._fetch_rss_articles(source_id, name, url, category)
                            articles.extend(source_articles)
                        
                        # Update last fetched time
                        cursor.execute(
                            'UPDATE news_sources SET last_fetched = ? WHERE id = ?',
                            (datetime.now().isoformat(), source_id)
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to fetch from {name}: {e}")
                        continue
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to fetch articles: {e}")
        
        return articles
    
    async def _fetch_rss_articles(self, source_id: int, source_name: str, url: str, category: str) -> List[Dict]:
        """Fetch articles from RSS feed."""
        articles = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries:
                            article = {
                                "source_id": source_id,
                                "source_name": source_name,
                                "title": entry.get("title", "No Title"),
                                "url": entry.get("link", ""),
                                "summary": self._clean_html(entry.get("summary", "")),
                                "author": entry.get("author", ""),
                                "published_date": self._parse_date(entry.get("published", "")),
                                "category": category,
                                "tags": self._extract_tags(entry)
                            }
                            
                            # Store in database
                            await self._store_article(article)
                            articles.append(article)
                    
        except Exception as e:
            logger.error(f"Failed to fetch RSS from {url}: {e}")
        
        return articles
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean_text = re.sub('<.*?>', '', text)
        return clean_text.strip()
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats."""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # Try common RSS date formats
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def _extract_tags(self, entry: Dict) -> str:
        """Extract tags from RSS entry."""
        tags = []
        
        # Get tags from entry
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    tags.append(tag.term)
        
        # Get categories
        if hasattr(entry, 'category'):
            tags.append(entry.category)
        
        return json.dumps(tags) if tags else "[]"
    
    async def _store_article(self, article: Dict) -> bool:
        """Store article in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (source_id, title, url, summary, author, published_date, category, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article["source_id"],
                    article["title"],
                    article["url"],
                    article["summary"],
                    article["author"],
                    article["published_date"],
                    article["category"],
                    article["tags"]
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to store article: {e}")
            return False
    
    async def get_articles(self, category: str = None, read_status: bool = None, 
                          limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get articles with optional filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM articles WHERE 1=1'
                params = []
                
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                
                if read_status is not None:
                    query += ' AND read_status = ?'
                    params.append(read_status)
                
                query += ' ORDER BY published_date DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                return self._format_articles(results)
                
        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            return []
    
    def _format_articles(self, raw_articles: List) -> List[Dict]:
        """Format raw database results into article dictionaries."""
        articles = []
        
        for row in raw_articles:
            article = {
                "id": row[0],
                "source_id": row[1],
                "title": row[2],
                "url": row[3],
                "summary": row[4],
                "content": row[5],
                "author": row[6],
                "published_date": row[7],
                "category": row[8],
                "tags": json.loads(row[9]) if row[9] else [],
                "read_status": bool(row[10]),
                "archived": bool(row[11]),
                "rating": row[12],
                "created_at": row[13]
            }
            articles.append(article)
        
        return articles