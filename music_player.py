import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from pathlib import Path

class MusicPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.current_songs = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Now playing
        self.now_playing = QLabel("No song playing")
        self.now_playing.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.now_playing)
        
        # Progress bar
        self.progress = QSlider(Qt.Horizontal)
        self.progress.sliderMoved.connect(self.set_position)
        layout.addWidget(self.progress)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00")
        self.duration_label = QLabel("00:00")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        layout.addLayout(time_layout)
        
        # Controls
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.play_pause)
        controls.addWidget(self.play_btn)
        
        prev_btn = QPushButton("⏮")
        prev_btn.clicked.connect(self.playlist.previous)
        controls.addWidget(prev_btn)
        
        next_btn = QPushButton("⏭")
        next_btn.clicked.connect(self.playlist.next)
        controls.addWidget(next_btn)
        
        stop_btn = QPushButton("⏹")
        stop_btn.clicked.connect(self.player.stop)
        controls.addWidget(stop_btn)
        
        # Volume
        controls.addWidget(QLabel("Volume:"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setMaximum(100)
        self.volume.setValue(50)
        self.volume.valueChanged.connect(self.player.setVolume)
        controls.addWidget(self.volume)
        
        layout.addLayout(controls)
        
        # Playlist
        toolbar = QHBoxLayout()
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        toolbar.addWidget(add_file_btn)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        toolbar.addWidget(add_folder_btn)
        
        clear_btn = QPushButton("Clear Playlist")
        clear_btn.clicked.connect(self.clear_playlist)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Song list
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.song_list)
        
        # Connect player signals
        self.player.stateChanged.connect(self.state_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        
        # Timer for updating position
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
    
    def add_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Add Music File", "",
            "Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac);;All Files (*.*)"
        )
        if file:
            self.add_to_playlist(file)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add Music Folder")
        if folder:
            for file in Path(folder).glob("**/*"):
                if file.suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
                    self.add_to_playlist(str(file))
    
    def add_to_playlist(self, file_path):
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        file_name = os.path.basename(file_path)
        self.song_list.addItem(file_name)
        self.current_songs.append(file_path)
    
    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
    
    def play_selected(self, item):
        index = self.song_list.row(item)
        self.playlist.setCurrentIndex(index)
        self.player.play()
    
    def clear_playlist(self):
        reply = QMessageBox.question(
            self, 'Clear Playlist',
            'Are you sure you want to clear the playlist?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.playlist.clear()
            self.song_list.clear()
            self.current_songs.clear()
            self.now_playing.setText("No song playing")
    
    def state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def position_changed(self, position):
        self.progress.setValue(position)
        self.time_label.setText(self.format_time(position))
    
    def duration_changed(self, duration):
        self.progress.setMaximum(duration)
        self.duration_label.setText(self.format_time(duration))
    
    def set_position(self, position):
        self.player.setPosition(position)
    
    def playlist_position_changed(self, index):
        if index >= 0 and index < len(self.current_songs):
            file_name = os.path.basename(self.current_songs[index])
            self.now_playing.setText(f"Now Playing: {file_name}")
            
            # Highlight current song
            for i in range(self.song_list.count()):
                item = self.song_list.item(i)
                if i == index:
                    item.setBackground(Qt.lightGray)
                else:
                    item.setBackground(Qt.white)
    
    def update_position(self):
        # Update position slider
        if self.player.state() == QMediaPlayer.PlayingState:
            self.progress.setValue(self.player.position())
    
    def format_time(self, ms):
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"