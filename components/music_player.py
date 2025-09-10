"""
Music Player Component for Westfall Personal Assistant

Provides music playback functionality with red/black theme integration.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QSlider, QListWidget, QSplitter, QProgressBar,
                           QComboBox, QLineEdit, QTabWidget, QGroupBox,
                           QFormLayout, QSpinBox, QCheckBox, QFileDialog,
                           QMessageBox, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap
from utils.app_theme import AppTheme
import logging
import os

logger = logging.getLogger(__name__)


class MusicThread(QThread):
    """Background thread for music operations"""
    song_loaded = pyqtSignal(dict)
    playlist_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, action, **kwargs):
        super().__init__()
        self.action = action
        self.kwargs = kwargs
        
    def run(self):
        """Run music operation in background"""
        try:
            if self.action == "load_library":
                # Simulate loading music library
                songs = [
                    {"title": "Coding Jazz", "artist": "Dev Beats", "album": "Programming Vibes", "duration": "3:45"},
                    {"title": "Debug Blues", "artist": "Stack Overflow", "album": "Error 404", "duration": "4:20"},
                    {"title": "Compile Success", "artist": "Binary Band", "album": "Clean Code", "duration": "2:30"},
                    {"title": "Async Dreams", "artist": "Promise All", "album": "Event Loop", "duration": "5:15"},
                ]
                self.playlist_loaded.emit(songs)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MusicPlayer(QWidget):
    """Music player interface with playback controls and library management"""
    
    def __init__(self):
        super().__init__()
        self.current_song = None
        self.is_playing = False
        self.is_shuffle = False
        self.is_repeat = False
        self.volume = 75
        self.position = 0
        self.duration = 100
        self.playlist = []
        self.current_index = 0
        
        # Timer for progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
        self.init_ui()
        self.apply_theme()
        self.load_music_library()
        
    def init_ui(self):
        """Initialize the music player interface"""
        layout = QVBoxLayout(self)
        
        # Header with title
        header_layout = QHBoxLayout()
        
        title = QLabel("🎵 Music Player")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Music controls
        self.import_btn = QPushButton("📁 Import")
        self.import_btn.clicked.connect(self.import_music)
        header_layout.addWidget(self.import_btn)
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Library and playlists
        left_panel = self.create_library_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Now playing and controls
        right_panel = self.create_player_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 600])
        
        # Bottom player controls
        self.create_player_controls()
        layout.addWidget(self.player_controls)
        
    def create_library_panel(self):
        """Create the music library panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Library tabs
        library_tabs = QTabWidget()
        
        # Songs tab
        songs_widget = QWidget()
        songs_layout = QVBoxLayout(songs_widget)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Search music...")
        self.search_field.textChanged.connect(self.filter_music)
        search_layout.addWidget(self.search_field)
        songs_layout.addLayout(search_layout)
        
        # Songs list
        self.songs_list = QListWidget()
        self.songs_list.itemDoubleClicked.connect(self.play_selected_song)
        songs_layout.addWidget(self.songs_list)
        
        library_tabs.addTab(songs_widget, "🎵 Songs")
        
        # Playlists tab
        playlists_widget = QWidget()
        playlists_layout = QVBoxLayout(playlists_widget)
        
        # Playlist controls
        playlist_controls = QHBoxLayout()
        self.new_playlist_btn = QPushButton("➕ New Playlist")
        self.new_playlist_btn.clicked.connect(self.create_playlist)
        playlist_controls.addWidget(self.new_playlist_btn)
        playlists_layout.addLayout(playlist_controls)
        
        # Playlists tree
        self.playlists_tree = QTreeWidget()
        self.playlists_tree.setHeaderLabels(["Playlists"])
        self.setup_playlists()
        playlists_layout.addWidget(self.playlists_tree)
        
        library_tabs.addTab(playlists_widget, "📋 Playlists")
        
        # Artists tab
        artists_widget = QWidget()
        artists_layout = QVBoxLayout(artists_widget)
        
        self.artists_list = QListWidget()
        artists_layout.addWidget(self.artists_list)
        
        library_tabs.addTab(artists_widget, "👤 Artists")
        
        layout.addWidget(library_tabs)
        
        return widget
        
    def create_player_panel(self):
        """Create the now playing panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Now playing header
        now_playing_label = QLabel("Now Playing")
        now_playing_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(now_playing_label)
        
        # Album art area
        self.album_art = QLabel()
        self.album_art.setMinimumSize(300, 300)
        self.album_art.setStyleSheet(f"""
            QLabel {{
                background-color: {AppTheme.SECONDARY_BG};
                border: 2px solid {AppTheme.BORDER_COLOR};
                border-radius: 10px;
            }}
        """)
        self.album_art.setAlignment(Qt.AlignCenter)
        self.album_art.setText("🎵\nNo Song Playing")
        layout.addWidget(self.album_art)
        
        # Song info
        info_layout = QVBoxLayout()
        
        self.song_title = QLabel("Select a song to play")
        self.song_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.song_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_title)
        
        self.song_artist = QLabel("")
        self.song_artist.setFont(QFont("Arial", 12))
        self.song_artist.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_artist)
        
        self.song_album = QLabel("")
        self.song_album.setFont(QFont("Arial", 10))
        self.song_album.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_album)
        
        layout.addLayout(info_layout)
        
        # Progress bar
        progress_layout = QVBoxLayout()
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self.progress_slider.sliderReleased.connect(self.on_progress_released)
        progress_layout.addWidget(self.progress_slider)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.current_time = QLabel("0:00")
        self.total_time = QLabel("0:00")
        time_layout.addWidget(self.current_time)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time)
        progress_layout.addLayout(time_layout)
        
        layout.addLayout(progress_layout)
        
        layout.addStretch()
        
        return widget
        
    def create_player_controls(self):
        """Create the main player control bar"""
        self.player_controls = QWidget()
        layout = QHBoxLayout(self.player_controls)
        
        # Shuffle button
        self.shuffle_btn = QPushButton("🔀")
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        layout.addWidget(self.shuffle_btn)
        
        # Previous button
        self.prev_btn = QPushButton("⏮️")
        self.prev_btn.clicked.connect(self.previous_song)
        layout.addWidget(self.prev_btn)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶️")
        self.play_btn.clicked.connect(self.toggle_playback)
        layout.addWidget(self.play_btn)
        
        # Next button
        self.next_btn = QPushButton("⏭️")
        self.next_btn.clicked.connect(self.next_song)
        layout.addWidget(self.next_btn)
        
        # Repeat button
        self.repeat_btn = QPushButton("🔁")
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.clicked.connect(self.toggle_repeat)
        layout.addWidget(self.repeat_btn)
        
        layout.addStretch()
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMaximumWidth(100)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout)
        
    def setup_playlists(self):
        """Setup default playlists"""
        favorites = QTreeWidgetItem(self.playlists_tree, ["❤️ Favorites"])
        recently_played = QTreeWidgetItem(self.playlists_tree, ["🕒 Recently Played"])
        coding_music = QTreeWidgetItem(self.playlists_tree, ["💻 Coding Music"])
        
        self.playlists_tree.expandAll()
        
    def apply_theme(self):
        """Apply red/black theme to music player"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QListWidget, QTreeWidget {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLineEdit {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_MEDIUM}px;
            }}
            QLineEdit:focus {{
                border-color: {AppTheme.HIGHLIGHT_COLOR};
            }}
            QPushButton {{
                {AppTheme.get_button_style()}
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:checked {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {AppTheme.BORDER_COLOR};
                height: 8px;
                background: {AppTheme.SECONDARY_BG};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {AppTheme.PRIMARY_COLOR};
                border: 1px solid {AppTheme.BORDER_COLOR};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {AppTheme.PRIMARY_COLOR};
                border-radius: 4px;
            }}
            QTabWidget::pane {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                background-color: {AppTheme.SECONDARY_BG};
            }}
            QTabBar::tab {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_SMALL}px {AppTheme.PADDING_MEDIUM}px;
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTabBar::tab:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
        """)
        
    def load_music_library(self):
        """Load music library"""
        self.music_thread = MusicThread("load_library")
        self.music_thread.playlist_loaded.connect(self.on_library_loaded)
        self.music_thread.error_occurred.connect(self.on_error)
        self.music_thread.start()
        
    def on_library_loaded(self, songs):
        """Handle music library loaded"""
        self.playlist = songs
        self.update_songs_list()
        self.update_artists_list()
        
    def on_error(self, error):
        """Handle music loading error"""
        QMessageBox.warning(self, "Music Player Error", f"Failed to load music: {error}")
        
    def update_songs_list(self):
        """Update the songs list"""
        self.songs_list.clear()
        for song in self.playlist:
            item_text = f"🎵 {song['title']} - {song['artist']} ({song['duration']})"
            self.songs_list.addItem(item_text)
            
    def update_artists_list(self):
        """Update the artists list"""
        self.artists_list.clear()
        artists = set(song['artist'] for song in self.playlist)
        for artist in sorted(artists):
            self.artists_list.addItem(f"👤 {artist}")
            
    def filter_music(self, text):
        """Filter music based on search text"""
        for i in range(self.songs_list.count()):
            item = self.songs_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def play_selected_song(self, item):
        """Play the selected song"""
        index = self.songs_list.row(item)
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.current_song = self.playlist[index]
            self.update_now_playing()
            self.start_playback()
            
    def update_now_playing(self):
        """Update the now playing display"""
        if self.current_song:
            self.song_title.setText(self.current_song['title'])
            self.song_artist.setText(self.current_song['artist'])
            self.song_album.setText(self.current_song['album'])
            self.album_art.setText("🎵\nNow Playing")
            self.total_time.setText(self.current_song['duration'])
            
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
            
    def start_playback(self):
        """Start music playback"""
        if self.current_song:
            self.is_playing = True
            self.play_btn.setText("⏸️")
            self.timer.start(1000)  # Update every second
            
    def pause_playback(self):
        """Pause music playback"""
        self.is_playing = False
        self.play_btn.setText("▶️")
        self.timer.stop()
        
    def update_progress(self):
        """Update playback progress"""
        if self.is_playing:
            self.position += 1
            if self.position >= self.duration:
                self.next_song()
            else:
                progress = int((self.position / self.duration) * 100)
                self.progress_slider.setValue(progress)
                
                # Update time display
                minutes = self.position // 60
                seconds = self.position % 60
                self.current_time.setText(f"{minutes}:{seconds:02d}")
                
    def on_progress_pressed(self):
        """Handle progress slider pressed"""
        self.timer.stop()
        
    def on_progress_released(self):
        """Handle progress slider released"""
        if self.is_playing:
            progress = self.progress_slider.value()
            self.position = int((progress / 100) * self.duration)
            self.timer.start(1000)
            
    def previous_song(self):
        """Play previous song"""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.current_song = self.playlist[self.current_index]
            self.update_now_playing()
            if self.is_playing:
                self.start_playback()
                
    def next_song(self):
        """Play next song"""
        if self.playlist:
            if self.is_shuffle:
                import random
                self.current_index = random.randint(0, len(self.playlist) - 1)
            else:
                self.current_index = (self.current_index + 1) % len(self.playlist)
                
            self.current_song = self.playlist[self.current_index]
            self.position = 0
            self.update_now_playing()
            if self.is_playing:
                self.start_playback()
                
    def toggle_shuffle(self):
        """Toggle shuffle mode"""
        self.is_shuffle = self.shuffle_btn.isChecked()
        
    def toggle_repeat(self):
        """Toggle repeat mode"""
        self.is_repeat = self.repeat_btn.isChecked()
        
    def change_volume(self, value):
        """Change playback volume"""
        self.volume = value
        # In a real implementation, this would adjust audio output volume
        
    def import_music(self):
        """Import music files"""
        file_dialog = QFileDialog()
        files, _ = file_dialog.getOpenFileNames(
            self, "Import Music Files", "", 
            "Audio Files (*.mp3 *.wav *.flac *.aac *.ogg)"
        )
        
        if files:
            QMessageBox.information(self, "Import Music", 
                                  f"Would import {len(files)} music files.\n\n"
                                  "In a real implementation, this would:\n"
                                  "- Parse audio metadata\n"
                                  "- Add to music database\n"
                                  "- Generate thumbnails\n"
                                  "- Update library display")
            
    def create_playlist(self):
        """Create a new playlist"""
        QMessageBox.information(self, "New Playlist", 
                              "Playlist creation dialog will be implemented here.")
        
    def show_settings(self):
        """Show music player settings"""
        QMessageBox.information(self, "Music Settings", 
                              "Music player settings panel will be implemented here.\n\n"
                              "Features to include:\n"
                              "- Audio output device selection\n"
                              "- Equalizer settings\n"
                              "- Library scan locations\n"
                              "- File format preferences\n"
                              "- Crossfade settings")
