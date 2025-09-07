import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Import all available windows
try:
    from placeholder_windows import EmailWindow
except ImportError:
    class EmailWindow(QMainWindow): pass

from password_manager import PasswordManagerWindow

try:
    from placeholder_windows import NotesWindow, CalculatorWindow, CalendarWindow, WeatherWindow
    from placeholder_windows import BrowserWindow, FileManagerWindow, TodoWindow, ContactsWindow
    from placeholder_windows import SettingsWindow, FinanceWindow, RecipeWindow
except ImportError:
    class NotesWindow(QMainWindow): pass
    class CalculatorWindow(QMainWindow): pass
    class CalendarWindow(QMainWindow): pass
    class WeatherWindow(QMainWindow): pass
    class BrowserWindow(QMainWindow): pass
    class FileManagerWindow(QMainWindow): pass
    class TodoWindow(QMainWindow): pass
    class ContactsWindow(QMainWindow): pass
    class SettingsWindow(QMainWindow): pass
    class FinanceWindow(QMainWindow): pass
    class RecipeWindow(QMainWindow): pass

from news import NewsWindow
from music_player import MusicPlayerWindow

# Import security
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows = {}
        self.ai_chat = None
        self.encryption_manager = None
        
        # Initialize security
        if not self.init_security():
            sys.exit()
        
        self.init_ui()
        self.init_ai()
        self.init_tray()
    
    def init_security(self):
        """Initialize security with master password"""
        master_file = 'data/.master'
        os.makedirs('data', exist_ok=True)
        
        first_time = not os.path.exists(master_file)
        
        dialog = MasterPasswordDialog(first_time=first_time)
        if dialog.exec_() != QDialog.Accepted:
            return False
        
        self.encryption_manager = EncryptionManager()
        
        if first_time:
            # Save master password hash
            hashed = self.encryption_manager.hash_password(dialog.password)
            with open(master_file, 'w') as f:
                f.write(hashed)
        else:
            # Verify password
            with open(master_file, 'r') as f:
                stored_hash = f.read()
            
            if self.encryption_manager.hash_password(dialog.password) != stored_hash:
                QMessageBox.critical(None, "Error", "Invalid master password!")
                return False
        
        return True
    
    def init_ui(self):
        self.setWindowTitle("Westfall Personal Assistant - Secure")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Westfall Personal Assistant")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding: 20px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        """)
        main_layout.addWidget(header)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search features or ask AI...")
        self.search_input.returnPressed.connect(self.handle_search)
        search_layout.addWidget(self.search_input)
        
        ai_btn = QPushButton("AI Assistant")
        ai_btn.clicked.connect(self.toggle_ai_chat)
        search_layout.addWidget(ai_btn)
        
        main_layout.addLayout(search_layout)
        
        # Feature grid
        grid = QGridLayout()
        
        features = [
            ("📧 Email", self.open_email),
            ("🔐 Passwords", self.open_password_manager),
            ("📝 Notes", self.open_notes),
            ("🧮 Calculator", self.open_calculator),
            ("📅 Calendar", self.open_calendar),
            ("🌤️ Weather", self.open_weather),
            ("📰 News", self.open_news),
            ("🌐 Browser", self.open_browser),
            ("📁 Files", self.open_file_manager),
            ("✅ Todo", self.open_todo),
            ("👥 Contacts", self.open_contacts),
            ("⚙️ Settings", self.open_settings),
            ("💰 Finance", self.open_finance),
            ("🍳 Recipes", self.open_recipe),
            ("🎵 Music", self.open_music),
        ]
        
        positions = [(i, j) for i in range(5) for j in range(3)]
        
        for position, (name, callback) in zip(positions, features):
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(80)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    background-color: white;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-color: #667eea;
                }
            """)
            grid.addWidget(btn, *position)
        
        main_layout.addLayout(grid)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Secure Mode Active")
        
        # Auto-lock timer
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.auto_lock)
        self.lock_timer.start(900000)  # 15 minutes
    
    def init_ai(self):
        """Initialize AI assistant"""
        self.ai_chat = AIChatWidget(self)
        self.ai_chat.hide()
    
    def init_tray(self):
        """Initialize system tray"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("Westfall Personal Assistant")
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = tray_menu.addAction("Show")
            show_action.triggered.connect(self.show)
            
            hide_action = tray_menu.addAction("Hide")
            hide_action.triggered.connect(self.hide)
            
            tray_menu.addSeparator()
            
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(QApplication.quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
    
    def handle_search(self):
        query = self.search_input.text()
        if query.startswith("ai:") or query.startswith("?"):
            # Send to AI
            if not self.ai_chat.isVisible():
                self.ai_chat.show()
            self.ai_chat.input_field.setText(query.lstrip("ai:").lstrip("?"))
            self.ai_chat.send_message()
        else:
            # Search features
            self.search_features(query)
    
    def search_features(self, query):
        # Simple feature search
        features_map = {
            "email": self.open_email,
            "password": self.open_password_manager,
            "note": self.open_notes,
            "calendar": self.open_calendar,
            "weather": self.open_weather,
            "news": self.open_news,
            "music": self.open_music,
        }
        
        query_lower = query.lower()
        for key, func in features_map.items():
            if key in query_lower:
                func()
                break
    
    def toggle_ai_chat(self):
        if self.ai_chat.isVisible():
            self.ai_chat.hide()
        else:
            self.ai_chat.show()
    
    def auto_lock(self):
        """Auto-lock after inactivity"""
        reply = QMessageBox.question(
            self, 'Session Timeout',
            'Your session will expire in 1 minute. Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.lock_timer.start(900000)  # Reset timer
        else:
            QApplication.quit()
    
    # Window opening methods
    def open_email(self):
        if 'email' not in self.windows:
            self.windows['email'] = EmailWindow()
        self.windows['email'].show()
        self.ai_chat.parent_window = self.windows['email']
    
    def open_password_manager(self):
        if 'password' not in self.windows:
            self.windows['password'] = PasswordManagerWindow()
        self.windows['password'].show()
        self.ai_chat.parent_window = self.windows['password']
    
    def open_notes(self):
        if 'notes' not in self.windows:
            self.windows['notes'] = NotesWindow()
        self.windows['notes'].show()
        self.ai_chat.parent_window = self.windows['notes']
    
    def open_calculator(self):
        if 'calculator' not in self.windows:
            self.windows['calculator'] = CalculatorWindow()
        self.windows['calculator'].show()
    
    def open_calendar(self):
        if 'calendar' not in self.windows:
            self.windows['calendar'] = CalendarWindow()
        self.windows['calendar'].show()
        self.ai_chat.parent_window = self.windows['calendar']
    
    def open_weather(self):
        if 'weather' not in self.windows:
            self.windows['weather'] = WeatherWindow()
        self.windows['weather'].show()
    
    def open_news(self):
        if 'news' not in self.windows:
            self.windows['news'] = NewsWindow()
        self.windows['news'].show()
    
    def open_browser(self):
        if 'browser' not in self.windows:
            self.windows['browser'] = BrowserWindow()
        self.windows['browser'].show()
    
    def open_file_manager(self):
        if 'files' not in self.windows:
            self.windows['files'] = FileManagerWindow()
        self.windows['files'].show()
    
    def open_todo(self):
        if 'todo' not in self.windows:
            self.windows['todo'] = TodoWindow()
        self.windows['todo'].show()
    
    def open_contacts(self):
        if 'contacts' not in self.windows:
            self.windows['contacts'] = ContactsWindow()
        self.windows['contacts'].show()
    
    def open_settings(self):
        if 'settings' not in self.windows:
            self.windows['settings'] = SettingsWindow()
        self.windows['settings'].show()
    
    def open_finance(self):
        if 'finance' not in self.windows:
            self.windows['finance'] = FinanceWindow()
        self.windows['finance'].show()
    
    def open_recipe(self):
        if 'recipe' not in self.windows:
            self.windows['recipe'] = RecipeWindow()
        self.windows['recipe'].show()
    
    def open_music(self):
        if 'music' not in self.windows:
            self.windows['music'] = MusicPlayerWindow()
        self.windows['music'].show()
        self.ai_chat.parent_window = self.windows['music']

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Westfall Personal Assistant")
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()