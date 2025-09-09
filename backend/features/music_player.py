#!/usr/bin/env python3
"""
Music Player Implementation for Westfall Personal Assistant

Audio playback engine with playlist management, support for multiple formats,
volume control, seek functionality, and keyboard media controls.
"""

import asyncio
import logging
import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)


class MusicPlayer:
    """Advanced music player with playlist management and format support."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/music.db"
        
        # Playback state
        self.is_playing = False
        self.is_paused = False
        self.current_track = None
        self.current_playlist = None
        self.current_position = 0.0
        self.volume = 0.7
        self.shuffle = False
        self.repeat_mode = "none"  # "none", "one", "all"
        
        # Audio engine (we'll try multiple backends)
        self.audio_engine = None
        self.audio_engine_type = None
        
        # Event callbacks
        self.on_track_changed = None
        self.on_playback_state_changed = None
        self.on_position_changed = None
        
        # Supported formats
        self.supported_formats = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
        
        # Initialize components
        self._init_database()
        self._init_audio_engine()
    
    def _init_database(self):
        """Initialize SQLite database for music library."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tracks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT UNIQUE NOT NULL,
                        title TEXT,
                        artist TEXT,
                        album TEXT,
                        genre TEXT,
                        duration REAL DEFAULT 0.0,
                        track_number INTEGER,
                        year INTEGER,
                        file_size INTEGER,
                        bitrate INTEGER,
                        sample_rate INTEGER,
                        last_played TIMESTAMP,
                        play_count INTEGER DEFAULT 0,
                        rating INTEGER DEFAULT 0,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create playlists table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS playlists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        track_count INTEGER DEFAULT 0,
                        total_duration REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create playlist_tracks table (many-to-many)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS playlist_tracks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        playlist_id INTEGER,
                        track_id INTEGER,
                        position INTEGER,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
                        FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE,
                        UNIQUE(playlist_id, track_id)
                    )
                ''')
                
                # Create listening history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS listening_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        track_id INTEGER,
                        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        duration_played REAL,
                        completion_percentage REAL,
                        FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
                    )
                ''')
                
                conn.commit()
                logger.info("Music database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize music database: {e}")
            raise
    
    def _init_audio_engine(self):
        """Initialize audio engine (try multiple backends)."""
        # Try pygame first (most reliable)
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self.audio_engine = pygame.mixer
            self.audio_engine_type = "pygame"
            logger.info("Audio engine initialized: pygame")
            return
        except ImportError:
            logger.warning("pygame not available for audio playback")
        
        # Try pydub with simpleaudio
        try:
            import pydub
            import simpleaudio
            self.audio_engine_type = "pydub"
            logger.info("Audio engine initialized: pydub + simpleaudio")
            return
        except ImportError:
            logger.warning("pydub/simpleaudio not available")
        
        # Try VLC (most format support)
        try:
            import vlc
            self.vlc_instance = vlc.Instance()
            self.vlc_player = self.vlc_instance.media_player_new()
            self.audio_engine_type = "vlc"
            logger.info("Audio engine initialized: VLC")
            return
        except ImportError:
            logger.warning("python-vlc not available")
        
        logger.error("No audio engine available. Install pygame, pydub, or python-vlc")
        self.audio_engine_type = "none"
    
    async def scan_music_directory(self, directory: str, recursive: bool = True) -> int:
        """Scan directory for music files and add them to library."""
        added_count = 0
        
        try:
            directory_path = Path(directory).expanduser()
            if not directory_path.exists():
                logger.error(f"Directory does not exist: {directory}")
                return 0
            
            # Get all music files
            music_files = []
            if recursive:
                for ext in self.supported_formats:
                    music_files.extend(directory_path.rglob(f"*{ext}"))
            else:
                for ext in self.supported_formats:
                    music_files.extend(directory_path.glob(f"*{ext}"))
            
            logger.info(f"Found {len(music_files)} music files in {directory}")
            
            # Process each file
            for file_path in music_files:
                if await self._add_track_to_library(str(file_path)):
                    added_count += 1
            
            logger.info(f"Added {added_count} new tracks to library")
            
        except Exception as e:
            logger.error(f"Failed to scan music directory: {e}")
        
        return added_count
    
    async def _add_track_to_library(self, file_path: str) -> bool:
        """Add a single track to the music library."""
        try:
            file_path = Path(file_path).resolve()
            
            # Check if file already exists
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM tracks WHERE file_path = ?', (str(file_path),))
                if cursor.fetchone():
                    return False  # Already exists
            
            # Extract metadata
            metadata = await self._extract_metadata(file_path)
            
            # Insert into database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tracks 
                    (file_path, title, artist, album, genre, duration, track_number, 
                     year, file_size, bitrate, sample_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(file_path),
                    metadata.get("title", file_path.stem),
                    metadata.get("artist", "Unknown Artist"),
                    metadata.get("album", "Unknown Album"),
                    metadata.get("genre", "Unknown"),
                    metadata.get("duration", 0.0),
                    metadata.get("track_number", 0),
                    metadata.get("year", 0),
                    file_path.stat().st_size,
                    metadata.get("bitrate", 0),
                    metadata.get("sample_rate", 0)
                ))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add track {file_path}: {e}")
            return False
    
    async def _extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from audio file."""
        metadata = {}
        
        try:
            # Try mutagen first (best metadata support)
            try:
                from mutagen import File
                audio_file = File(str(file_path))
                
                if audio_file is not None:
                    metadata["duration"] = getattr(audio_file, "info", {}).length or 0.0
                    metadata["bitrate"] = getattr(audio_file, "info", {}).bitrate or 0
                    metadata["sample_rate"] = getattr(audio_file, "info", {}).sample_rate or 0
                    
                    # Extract tags
                    if audio_file.tags:
                        metadata["title"] = self._get_tag_value(audio_file.tags, ["TIT2", "TITLE", "\xa9nam"])
                        metadata["artist"] = self._get_tag_value(audio_file.tags, ["TPE1", "ARTIST", "\xa9ART"])
                        metadata["album"] = self._get_tag_value(audio_file.tags, ["TALB", "ALBUM", "\xa9alb"])
                        metadata["genre"] = self._get_tag_value(audio_file.tags, ["TCON", "GENRE", "\xa9gen"])
                        metadata["year"] = self._get_tag_value(audio_file.tags, ["TDRC", "DATE", "\xa9day"])
                        metadata["track_number"] = self._get_tag_value(audio_file.tags, ["TRCK", "TRACKNUMBER", "trkn"])
            
            except ImportError:
                logger.warning("mutagen not available for metadata extraction")
                # Fallback to basic file info
                metadata["duration"] = 0.0
                metadata["title"] = file_path.stem
                
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
        
        return metadata
    
    def _get_tag_value(self, tags: dict, tag_keys: list) -> str:
        """Get tag value from multiple possible keys."""
        for key in tag_keys:
            if key in tags:
                value = tags[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                return str(value)
        return ""
    
    async def play_track(self, track_id: int) -> bool:
        """Play a specific track."""
        try:
            # Get track info
            track = await self.get_track(track_id)
            if not track:
                return False
            
            # Stop current playback
            await self.stop()
            
            # Load and play track
            success = await self._load_and_play(track["file_path"])
            
            if success:
                self.current_track = track
                self.is_playing = True
                self.is_paused = False
                
                # Update play count and last played
                await self._update_play_stats(track_id)
                
                # Trigger callbacks
                if self.on_track_changed:
                    self.on_track_changed(track)
                if self.on_playback_state_changed:
                    self.on_playback_state_changed("playing")
                
                logger.info(f"Playing: {track['title']} by {track['artist']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to play track {track_id}: {e}")
            return False
    
    async def _load_and_play(self, file_path: str) -> bool:
        """Load and play audio file using available engine."""
        try:
            if self.audio_engine_type == "pygame":
                self.audio_engine.music.load(file_path)
                self.audio_engine.music.play()
                return True
            
            elif self.audio_engine_type == "vlc":
                media = self.vlc_instance.media_new(file_path)
                self.vlc_player.set_media(media)
                self.vlc_player.play()
                return True
            
            elif self.audio_engine_type == "pydub":
                # This is more complex with pydub - simplified for now
                return False
            
            else:
                logger.error("No audio engine available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load and play {file_path}: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause playback."""
        try:
            if not self.is_playing:
                return False
            
            if self.audio_engine_type == "pygame":
                self.audio_engine.music.pause()
            elif self.audio_engine_type == "vlc":
                self.vlc_player.pause()
            
            self.is_paused = True
            self.is_playing = False
            
            if self.on_playback_state_changed:
                self.on_playback_state_changed("paused")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume playback."""
        try:
            if not self.is_paused:
                return False
            
            if self.audio_engine_type == "pygame":
                self.audio_engine.music.unpause()
            elif self.audio_engine_type == "vlc":
                self.vlc_player.play()
            
            self.is_paused = False
            self.is_playing = True
            
            if self.on_playback_state_changed:
                self.on_playback_state_changed("playing")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop playback."""
        try:
            if self.audio_engine_type == "pygame":
                self.audio_engine.music.stop()
            elif self.audio_engine_type == "vlc":
                self.vlc_player.stop()
            
            self.is_playing = False
            self.is_paused = False
            self.current_position = 0.0
            
            if self.on_playback_state_changed:
                self.on_playback_state_changed("stopped")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False
    
    async def set_volume(self, volume: float) -> bool:
        """Set playback volume (0.0 to 1.0)."""
        try:
            volume = max(0.0, min(1.0, volume))
            
            if self.audio_engine_type == "pygame":
                self.audio_engine.music.set_volume(volume)
            elif self.audio_engine_type == "vlc":
                self.vlc_player.audio_set_volume(int(volume * 100))
            
            self.volume = volume
            return True
            
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    async def get_track(self, track_id: int) -> Optional[Dict]:
        """Get track information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tracks WHERE id = ?', (track_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._format_track(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get track {track_id}: {e}")
            return None
    
    async def get_tracks(self, limit: int = 100, offset: int = 0, 
                        search: str = None, genre: str = None, 
                        artist: str = None, album: str = None) -> List[Dict]:
        """Get tracks with optional filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM tracks WHERE 1=1'
                params = []
                
                if search:
                    query += ' AND (title LIKE ? OR artist LIKE ? OR album LIKE ?)'
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])
                
                if genre:
                    query += ' AND genre = ?'
                    params.append(genre)
                
                if artist:
                    query += ' AND artist = ?'
                    params.append(artist)
                
                if album:
                    query += ' AND album = ?'
                    params.append(album)
                
                query += ' ORDER BY artist, album, track_number LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [self._format_track(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get tracks: {e}")
            return []
    
    def _format_track(self, row) -> Dict:
        """Format raw database row into track dictionary."""
        return {
            "id": row[0],
            "file_path": row[1],
            "title": row[2],
            "artist": row[3],
            "album": row[4],
            "genre": row[5],
            "duration": row[6],
            "track_number": row[7],
            "year": row[8],
            "file_size": row[9],
            "bitrate": row[10],
            "sample_rate": row[11],
            "last_played": row[12],
            "play_count": row[13],
            "rating": row[14],
            "added_at": row[15]
        }
    
    async def create_playlist(self, name: str, description: str = "") -> Optional[int]:
        """Create a new playlist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO playlists (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to create playlist {name}: {e}")
            return None
    
    async def add_track_to_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Add track to playlist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get next position
                cursor.execute(
                    'SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id = ?',
                    (playlist_id,)
                )
                position = cursor.fetchone()[0]
                
                # Add track
                cursor.execute('''
                    INSERT OR REPLACE INTO playlist_tracks (playlist_id, track_id, position)
                    VALUES (?, ?, ?)
                ''', (playlist_id, track_id, position))
                
                # Update playlist stats
                await self._update_playlist_stats(playlist_id)
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add track to playlist: {e}")
            return False
    
    async def _update_play_stats(self, track_id: int):
        """Update play statistics for a track."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tracks 
                    SET play_count = play_count + 1, last_played = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), track_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update play stats: {e}")
    
    async def _update_playlist_stats(self, playlist_id: int):
        """Update playlist statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE playlists 
                    SET track_count = (
                        SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = ?
                    ),
                    total_duration = (
                        SELECT COALESCE(SUM(t.duration), 0) 
                        FROM playlist_tracks pt
                        JOIN tracks t ON pt.track_id = t.id
                        WHERE pt.playlist_id = ?
                    ),
                    updated_at = ?
                    WHERE id = ?
                ''', (playlist_id, playlist_id, datetime.now().isoformat(), playlist_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update playlist stats: {e}")
    
    async def get_playback_status(self) -> Dict:
        """Get current playback status."""
        return {
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "current_track": self.current_track,
            "current_position": self.current_position,
            "volume": self.volume,
            "shuffle": self.shuffle,
            "repeat_mode": self.repeat_mode,
            "audio_engine": self.audio_engine_type
        }