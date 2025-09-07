import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence

# Import all windows with fallbacks
try:
    from email_window import EmailWindow
except ImportError:
    class EmailWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Email (Placeholder)")

from password_manager import PasswordManagerWindow

try:
    from notes import NotesWindow
except ImportError:
    class NotesWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Notes (Placeholder)")

try:
    from calculator import CalculatorWindow
except ImportError:
    class CalculatorWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Calculator (Placeholder)")

try:
    from calendar_window import CalendarWindow
except ImportError:
    class CalendarWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Calendar (Placeholder)")

from weather import WeatherWindow

try:
    from news import NewsWindow
except ImportError:
    class NewsWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("News (Placeholder)")

try:
    from browser import BrowserWindow
except ImportError:
    class BrowserWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Browser (Placeholder)")

try:
    from file_manager import FileManagerWindow
except ImportError:
    class FileManagerWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("File Manager (Placeholder)")

try:
    from todo import TodoWindow
except ImportError:
    class TodoWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Todo (Placeholder)")

try:
    from contacts import ContactsWindow
except ImportError:
    class ContactsWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Contacts (Placeholder)")

try:
    from settings import SettingsWindow
except ImportError:
    class SettingsWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Settings (Placeholder)")

try:
    from finance import FinanceWindow
except ImportError:
    class FinanceWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Finance (Placeholder)")

try:
    from recipe import RecipeWindow
except ImportError:
    class RecipeWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Recipe (Placeholder)")

try:
    from music_player import MusicPlayerWindow
except ImportError:
    class MusicPlayerWindow(QMainWindow): 
        def __init__(self): 
            super().__init__()
            self.setWindowTitle("Music Player (Placeholder)")

# Import security and AI
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows = {}
        self.ai_chat = None
        self.encryption_manager = None
        self.recent_features = []
        
        # Initialize security
        if not self.init_security():
            sys.exit()
        
        self.init_ui()
        self.init_shortcuts()
        self.init_ai()
        self.init_tray()
        self.load_preferences()
    
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
            
            # Show welcome message
            QMessageBox.information(None, "Welcome!", 
                "Your master password has been set.\n\n"
                "Tips:\n"
                "• Press Ctrl+K to open command palette\n"
                "• Press Ctrl+/ for keyboard shortcuts\n"
                "• Click AI Assistant or press Ctrl+Space for AI help")
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
        self.setGeometry(100, 100, 900, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # Header with gradient
        header = QLabel("Westfall Personal Assistant")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }
        """)
        header.setToolTip("Your secure personal assistant with AI capabilities")
        main_layout.addWidget(header)
        
        # Quick Access Bar (for recent/favorite features)
        quick_access_widget = QWidget()
        quick_access_layout = QHBoxLayout(quick_access_widget)
        quick_access_label = QLabel("Quick Access:")
        quick_access_label.setStyleSheet("font-weight: bold;")
        quick_access_layout.addWidget(quick_access_label)
        
        self.quick_access_buttons = QHBoxLayout()
        quick_access_layout.addLayout(self.quick_access_buttons)
        quick_access_layout.addStretch()
        
        # Dark mode toggle
        self.dark_mode_btn = QPushButton("🌙")
        self.dark_mode_btn.setToolTip("Toggle Dark Mode (Ctrl+D)")
        self.dark_mode_btn.setMaximumWidth(40)
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        quick_access_layout.addWidget(self.dark_mode_btn)
        
        main_layout.addWidget(quick_access_widget)
        
        # Search/Command bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search features, type commands, or ask AI (prefix with 'ai:' or '?')... Press Ctrl+K")
        self.search_input.setToolTip("Quick search: Type to find features | AI mode: Start with 'ai:' or '?' | Command palette: Ctrl+K")
        self.search_input.returnPressed.connect(self.handle_search)
        search_layout.addWidget(self.search_input)
        
        ai_btn = QPushButton("🤖 AI Assistant")
        ai_btn.setToolTip("Open AI Assistant (Ctrl+Space)")
        ai_btn.clicked.connect(self.toggle_ai_chat)
        search_layout.addWidget(ai_btn)
        
        shortcuts_btn = QPushButton("⌨")
        shortcuts_btn.setToolTip("View keyboard shortcuts (Ctrl+/)")
        shortcuts_btn.clicked.connect(self.show_shortcuts)
        shortcuts_btn.setMaximumWidth(40)
        search_layout.addWidget(shortcuts_btn)
        
        main_layout.addLayout(search_layout)
        
        # Feature grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.features = [
            ("📧 Email", self.open_email, "Manage your emails", "Ctrl+E"),
            ("🔐 Passwords", self.open_password_manager, "Secure password storage", "Ctrl+P"),
            ("📝 Notes", self.open_notes, "Create and organize notes", "Ctrl+N"),
            ("🧮 Calculator", self.open_calculator, "Perform calculations", "Ctrl+Shift+C"),
            ("📅 Calendar", self.open_calendar, "Manage events and appointments", "Ctrl+Shift+D"),
            ("🌤️ Weather", self.open_weather, "Check weather conditions", "Ctrl+W"),
            ("📰 News", self.open_news, "Read latest news", "Ctrl+Shift+N"),
            ("🌐 Browser", self.open_browser, "Browse the web", "Ctrl+B"),
            ("📁 Files", self.open_file_manager, "Manage your files", "Ctrl+F"),
            ("✅ Todo", self.open_todo, "Track your tasks", "Ctrl+T"),
            ("👥 Contacts", self.open_contacts, "Manage contacts", "Ctrl+Shift+O"),
            ("⚙️ Settings", self.open_settings, "Configure application", "Ctrl+,"),
            ("💰 Finance", self.open_finance, "Track finances", "Ctrl+Shift+F"),
            ("🍳 Recipes", self.open_recipe, "Manage recipes", "Ctrl+R"),
            ("🎵 Music", self.open_music, "Play music", "Ctrl+M"),
        ]
        
        positions = [(i, j) for i in range(5) for j in range(3)]
        
        for position, (name, callback, tooltip, shortcut) in zip(positions, self.features):
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            btn.clicked.connect(lambda checked, n=name: self.add_to_recent(n))
            btn.setMinimumHeight(80)
            btn.setToolTip(f"{tooltip}\nShortcut: {shortcut}")
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    background-color: white;
                    transition: all 0.3s;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-color: #667eea;
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
            """)
            grid.addWidget(btn, *position)
        
        main_layout.addLayout(grid)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Secure Mode Active | Press Ctrl+/ for shortcuts")
        
        # Auto-lock timer
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.auto_lock)
        self.lock_timer.start(900000)  # 15 minutes
        
        # Update quick access with recent items
        self.update_quick_access()
    
    def init_shortcuts(self):
        """Initialize global keyboard shortcuts"""
        # Feature shortcuts
        QShortcut(QKeySequence("Ctrl+E"), self, self.open_email)
        QShortcut(QKeySequence("Ctrl+P"), self, self.open_password_manager)
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_notes)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, self.open_calculator)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.open_calendar)
        QShortcut(QKeySequence("Ctrl+W"), self, self.open_weather)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.open_news)
        QShortcut(QKeySequence("Ctrl+B"), self, self.open_browser)
        QShortcut(QKeySequence("Ctrl+F"), self, self.open_file_manager)
        QShortcut(QKeySequence("Ctrl+T"), self, self.open_todo)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.open_contacts)
        QShortcut(QKeySequence("Ctrl+,"), self, self.open_settings)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.open_finance)
        QShortcut(QKeySequence("Ctrl+R"), self, self.open_recipe)
        QShortcut(QKeySequence("Ctrl+M"), self, self.open_music)
        
        # System shortcuts
        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+Space"), self, self.toggle_ai_chat)
        QShortcut(QKeySequence("Ctrl+/"), self, self.show_shortcuts)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_dark_mode)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Escape"), self, self.handle_escape)
        QShortcut(QKeySequence("F1"), self, self.show_help)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        """Initialize AI assistant"""
        self.ai_chat = AIChatWidget(self)
        self.ai_chat.hide()
    
    def init_tray(self):
        """Initialize system tray"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Westfall Personal Assistant - Click to show/hide")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show Main Window")
        show_action.triggered.connect(self.show)
        
        hide_action = tray_menu.addAction("Minimize to Tray")
        hide_action.triggered.connect(self.hide)
        
        tray_menu.addSeparator()
        
        # Quick access from tray
        email_action = tray_menu.addAction("📧 Open Email")
        email_action.triggered.connect(self.open_email)
        
        notes_action = tray_menu.addAction("📝 Open Notes")
        notes_action.triggered.connect(self.open_notes)
        
        todo_action = tray_menu.addAction("✅ Open Todo")
        todo_action.triggered.connect(self.open_todo)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def show_shortcuts(self):
        """Display keyboard shortcuts dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 600)
        
        layout = QVBoxLayout()
        
        # Create shortcuts text
        shortcuts_text = """
        <h2>Feature Shortcuts</h2>
        <table>
        <tr><td><b>Ctrl+E</b></td><td>Open Email</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>Open Password Manager</td></tr>
        <tr><td><b>Ctrl+N</b></td><td>Open Notes</td></tr>
        <tr><td><b>Ctrl+T</b></td><td>Open Todo</td></tr>
        <tr><td><b>Ctrl+W</b></td><td>Open Weather</td></tr>
        <tr><td><b>Ctrl+B</b></td><td>Open Browser</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Open File Manager</td></tr>
        <tr><td><b>Ctrl+M</b></td><td>Open Music Player</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Open Recipes</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>Open Settings</td></tr>
        </table>
        
        <h2>System Shortcuts</h2>
        <table>
        <tr><td><b>Ctrl+K</b></td><td>Focus Search/Command Bar</td></tr>
        <tr><td><b>Ctrl+Space</b></td><td>Toggle AI Assistant</td></tr>
        <tr><td><b>Ctrl+/</b></td><td>Show This Help</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Toggle Dark Mode</td></tr>
        <tr><td><b>F1</b></td><td>Show Help</td></tr>
        <tr><td><b>F11</b></td><td>Toggle Fullscreen</td></tr>
        <tr><td><b>Escape</b></td><td>Close Current Window</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit Application</td></tr>
        </table>
        
        <h2>AI Commands</h2>
        <p>In the search bar, prefix with 'ai:' or '?' to ask the AI assistant</p>
        <p>Examples:</p>
        <ul>
        <li>ai: help me write an email</li>
        <li>? what's on my calendar today</li>
        <li>ai: generate a secure password</li>
        </ul>
        """
        
        text_browser = QTextBrowser()
        text_browser.setHtml(shortcuts_text)
        layout.addWidget(text_browser)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_help(self):
        """Show help documentation"""
        QMessageBox.information(self, "Help", 
            "Westfall Personal Assistant Help\n\n"
            "• Use Ctrl+K to quickly search for features\n"
            "• Press Ctrl+Space to open AI Assistant\n"
            "• Press Ctrl+/ to see all keyboard shortcuts\n"
            "• Click on any feature to open it\n"
            "• Your data is encrypted and secure\n\n"
            "For more help, ask the AI Assistant!")
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        if self.dark_mode_btn.text() == "🌙":
            # Switch to dark mode
            self.dark_mode_btn.setText("☀️")
            self.dark_mode_btn.setToolTip("Switch to Light Mode (Ctrl+D)")
            app = QApplication.instance()
            app.setStyleSheet("""
                QMainWindow, QDialog, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555;
                }
                QPushButton:hover {
                    background-color: #484848;
                }
                QLineEdit, QTextEdit, QListWidget {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555;
                }
            """)
            self.status_bar.showMessage("Dark mode enabled")
        else:
            # Switch to light mode
            self.dark_mode_btn.setText("🌙")
            self.dark_mode_btn.setToolTip("Switch to Dark Mode (Ctrl+D)")
            app = QApplication.instance()
            app.setStyleSheet("")
            self.status_bar.showMessage("Light mode enabled")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.status_bar.showMessage("Exited fullscreen mode")
        else:
            self.showFullScreen()
            self.status_bar.showMessage("Entered fullscreen mode - Press F11 to exit")
    
    def handle_escape(self):
        """Handle escape key press"""
        # Close topmost window or exit fullscreen
        if self.isFullScreen():
            self.showNormal()
        elif self.ai_chat and self.ai_chat.isVisible():
            self.ai_chat.hide()
        else:
            # Close the most recently opened window
            for window in self.windows.values():
                if window.isVisible():
                    window.close()
                    break
    
    def add_to_recent(self, feature_name):
        """Add feature to recent/quick access"""
        # Remove emoji for storage
        clean_name = feature_name.split(' ', 1)[1] if ' ' in feature_name else feature_name
        
        if clean_name in self.recent_features:
            self.recent_features.remove(clean_name)
        
        self.recent_features.insert(0, clean_name)
        self.recent_features = self.recent_features[:4]  # Keep only 4 recent
        
        self.update_quick_access()
        self.save_preferences()
    
    def update_quick_access(self):
        """Update quick access buttons"""
        # Clear existing buttons
        while self.quick_access_buttons.count():
            child = self.quick_access_buttons.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add recent feature buttons
        for feature_name in self.recent_features:
            # Find the feature
            for name, callback, tooltip, shortcut in self.features:
                if feature_name in name:
                    btn = QPushButton(name.split()[0])  # Just emoji
                    btn.setToolTip(f"Quick access: {feature_name}")
                    btn.clicked.connect(callback)
                    btn.setMaximumWidth(40)
                    self.quick_access_buttons.addWidget(btn)
                    break
    
    def save_preferences(self):
        """Save user preferences"""
        prefs_file = 'data/.preferences'
        prefs = {
            'recent_features': self.recent_features,
            'dark_mode': self.dark_mode_btn.text() == "☀️"
        }
        
        try:
            import json
            with open(prefs_file, 'w') as f:
                json.dump(prefs, f)
        except:
            pass
    
    def load_preferences(self):
        """Load user preferences"""
        prefs_file = 'data/.preferences'
        
        try:
            import json
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                    self.recent_features = prefs.get('recent_features', [])
                    if prefs.get('dark_mode', False):
                        self.toggle_dark_mode()
                    self.update_quick_access()
        except:
            pass
    
    def handle_search(self):
        query = self.search_input.text()
        if query.startswith("ai:") or query.startswith("?"):
            # Send to AI
            if not self.ai_chat.isVisible():
                self.ai_chat.show()
            self.ai_chat.input_field.setText(query.lstrip("ai:").lstrip("?").strip())
            self.ai_chat.send_message()
            self.search_input.clear()
        else:
            # Search features
            self.search_features(query)
    
    def search_features(self, query):
        """Search and open features"""
        query_lower = query.lower()
        
        for name, callback, _, _ in self.features:
            clean_name = name.split(' ', 1)[1].lower() if ' ' in name else name.lower()
            if query_lower in clean_name:
                callback()
                self.search_input.clear()
                self.status_bar.showMessage(f"Opened {name}")
                break
        else:
            self.status_bar.showMessage(f"No feature found for '{query}'")
    
    def toggle_ai_chat(self):
        if self.ai_chat.isVisible():
            self.ai_chat.hide()
            self.status_bar.showMessage("AI Assistant hidden")
        else:
            self.ai_chat.show()
            self.ai_chat.raise_()
            self.ai_chat.activateWindow()
            self.ai_chat.input_field.setFocus()
            self.status_bar.showMessage("AI Assistant ready - Ask me anything!")
    
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
            self.save_preferences()
            QApplication.quit()
    
    # Window opening methods with tracking
    def open_email(self):
        if 'email' not in self.windows:
            self.windows['email'] = EmailWindow()
        self.windows['email'].show()
        self.windows['email'].raise_()
        self.windows['email'].activateWindow()
        self.ai_chat.parent_window = self.windows['email']
        self.status_bar.showMessage("Email opened")
    
    def open_password_manager(self):
        if 'password' not in self.windows:
            self.windows['password'] = PasswordManagerWindow()
        self.windows['password'].show()
        self.windows['password'].raise_()
        self.windows['password'].activateWindow()
        self.ai_chat.parent_window = self.windows['password']
        self.status_bar.showMessage("Password Manager opened - Your passwords are encrypted")
    
    def open_notes(self):
        if 'notes' not in self.windows:
            self.windows['notes'] = NotesWindow()
        self.windows['notes'].show()
        self.windows['notes'].raise_()
        self.windows['notes'].activateWindow()
        self.ai_chat.parent_window = self.windows['notes']
        self.status_bar.showMessage("Notes opened")
    
    def open_calculator(self):
        if 'calculator' not in self.windows:
            self.windows['calculator'] = CalculatorWindow()
        self.windows['calculator'].show()
        self.windows['calculator'].raise_()
        self.windows['calculator'].activateWindow()
        self.status_bar.showMessage("Calculator opened")
    
    def open_calendar(self):
        if 'calendar' not in self.windows:
            self.windows['calendar'] = CalendarWindow()
        self.windows['calendar'].show()
        self.windows['calendar'].raise_()
        self.windows['calendar'].activateWindow()
        self.ai_chat.parent_window = self.windows['calendar']
        self.status_bar.showMessage("Calendar opened")
    
    def open_weather(self):
        if 'weather' not in self.windows:
            self.windows['weather'] = WeatherWindow()
        self.windows['weather'].show()
        self.windows['weather'].raise_()
        self.windows['weather'].activateWindow()
        self.status_bar.showMessage("Weather opened")
    
    def open_news(self):
        if 'news' not in self.windows:
            self.windows['news'] = NewsWindow()
        self.windows['news'].show()
        self.windows['news'].raise_()
        self.windows['news'].activateWindow()
        self.status_bar.showMessage("News Reader opened")
    
    def open_browser(self):
        if 'browser' not in self.windows:
            self.windows['browser'] = BrowserWindow()
        self.windows['browser'].show()
        self.windows['browser'].raise_()
        self.windows['browser'].activateWindow()
        self.status_bar.showMessage("Browser opened")
    
    def open_file_manager(self):
        if 'files' not in self.windows:
            self.windows['files'] = FileManagerWindow()
        self.windows['files'].show()
        self.windows['files'].raise_()
        self.windows['files'].activateWindow()
        self.status_bar.showMessage("File Manager opened")
    
    def open_todo(self):
        if 'todo' not in self.windows:
            self.windows['todo'] = TodoWindow()
        self.windows['todo'].show()
        self.windows['todo'].raise_()
        self.windows['todo'].activateWindow()
        self.status_bar.showMessage("Todo List opened")
    
    def open_contacts(self):
        if 'contacts' not in self.windows:
            self.windows['contacts'] = ContactsWindow()
        self.windows['contacts'].show()
        self.windows['contacts'].raise_()
        self.windows['contacts'].activateWindow()
        self.status_bar.showMessage("Contacts opened")
    
    def open_settings(self):
        if 'settings' not in self.windows:
            self.windows['settings'] = SettingsWindow()
        self.windows['settings'].show()
        self.windows['settings'].raise_()
        self.windows['settings'].activateWindow()
        self.status_bar.showMessage("Settings opened")
    
    def open_finance(self):
        if 'finance' not in self.windows:
            self.windows['finance'] = FinanceWindow()
        self.windows['finance'].show()
        self.windows['finance'].raise_()
        self.windows['finance'].activateWindow()
        self.status_bar.showMessage("Finance Tracker opened")
    
    def open_recipe(self):
        if 'recipe' not in self.windows:
            self.windows['recipe'] = RecipeWindow()
        self.windows['recipe'].show()
        self.windows['recipe'].raise_()
        self.windows['recipe'].activateWindow()
        self.status_bar.showMessage("Recipe Manager opened")
    
    def open_music(self):
        if 'music' not in self.windows:
            self.windows['music'] = MusicPlayerWindow()
        self.windows['music'].show()
        self.windows['music'].raise_()
        self.windows['music'].activateWindow()
        self.ai_chat.parent_window = self.windows['music']
        self.status_bar.showMessage("Music Player opened")
    
    def closeEvent(self, event):
        """Handle application close"""
        self.save_preferences()
        
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close all windows
            for window in self.windows.values():
                window.close()
            
            if self.ai_chat:
                self.ai_chat.close()
            
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Westfall Personal Assistant")
    app.setOrganizationName("Westfall Softwares")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application icon if available
    if os.path.exists('assets/icon.png'):
        app.setWindowIcon(QIcon('assets/icon.png'))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    main()