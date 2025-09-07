import sys
import os

# Add the project root to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPalette, QColor, QFont

# Import all windows
try:
    from email_window import EmailWindow
except ImportError:
    from placeholder_windows import EmailWindow

from password_manager import PasswordManagerWindow

try:
    from notes import NotesWindow
except ImportError:
    from placeholder_windows import NotesWindow

try:
    from calculator import CalculatorWindow
except ImportError:
    from placeholder_windows import CalculatorWindow

try:
    from calendar_window import CalendarWindow
except ImportError:
    from placeholder_windows import CalendarWindow

from weather import WeatherWindow
from news import NewsWindow

try:
    from browser import BrowserWindow
except ImportError:
    from placeholder_windows import BrowserWindow

try:
    from file_manager import FileManagerWindow
except ImportError:
    from placeholder_windows import FileManagerWindow

try:
    from todo import TodoWindow
except ImportError:
    from placeholder_windows import TodoWindow

try:
    from contacts import ContactsWindow
except ImportError:
    from placeholder_windows import ContactsWindow

try:
    from settings import SettingsWindow
except ImportError:
    from placeholder_windows import SettingsWindow

try:
    from finance import FinanceWindow
except ImportError:
    from placeholder_windows import FinanceWindow

try:
    from recipe import RecipeWindow
except ImportError:
    from placeholder_windows import RecipeWindow

try:
    from music_player import MusicPlayerWindow
except ImportError:
    from placeholder_windows import MusicPlayerWindow

# Import YOUR EXISTING business features
from business_intelligence.dashboard.business_dashboard import BusinessDashboard
from business_intelligence.dashboard.kpi_tracker import KPITracker
from business_intelligence.reports.report_generator import ReportGenerator
from crm_system.crm_manager import CRMManager

# Import security and AI
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

# For screen intelligence, check if multi_monitor_capture exists
try:
    from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
    # Create LiveScreenIntelligence from MultiMonitorCapture if it doesn't exist separately
    LiveScreenIntelligence = MultiMonitorCapture
except ImportError:
    # Only if it truly doesn't exist
    print("Warning: Screen intelligence module not found")
    class LiveScreenIntelligence(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()
        
        def init_ui(self):
            layout = QVBoxLayout()
            
            # At least make it look good
            header = QLabel("🖥️ Live Screen Intelligence")
            header.setStyleSheet("""
                QLabel {
                    color: #ff0000;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 20px;
                }
            """)
            header.setAlignment(Qt.AlignCenter)
            layout.addWidget(header)
            
            install_btn = QPushButton("Install Dependencies")
            install_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff0000;
                    color: white;
                    border: none;
                    padding: 15px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            install_btn.clicked.connect(lambda: QMessageBox.information(
                self, "Install", "Run: pip install mss pyautogui opencv-python pytesseract"
            ))
            layout.addWidget(install_btn)
            
            layout.addStretch()
            self.setLayout(layout)

class NavigationButton(QPushButton):
    """Custom button with hover effects for navigation"""
    def __init__(self, text, icon="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        
    def enterEvent(self, event):
        self.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_widget = None
        self.widget_stack = []
        self.widgets_cache = {}
        self.encryption_manager = None
        
        # Initialize security
        if not self.init_security():
            sys.exit()
        
        self.init_ui()
        self.init_shortcuts()
        self.init_ai()
        self.apply_black_red_theme()
    
    def init_security(self):
        """Initialize security with master password"""
        master_file = 'data/.master'
        os.makedirs('data', exist_ok=True)
        
        first_time = not os.path.exists(master_file)
        
        dialog = MasterPasswordDialog(first_time=first_time)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #000000;
                color: white;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 2px solid #ff0000;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QLabel {
                color: white;
            }
        """)
        
        if dialog.exec_() != QDialog.Accepted:
            return False
        
        self.encryption_manager = EncryptionManager()
        
        if first_time:
            hashed = self.encryption_manager.hash_password(dialog.password)
            with open(master_file, 'w') as f:
                f.write(hashed)
        else:
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
            # New Business Intelligence Features
            ("🖥️ Screen Intelligence", self.open_screen_intelligence, "Multi-monitor capture & analysis", "Ctrl+I"),
            ("📊 Business Dashboard", self.open_business_dashboard, "Business metrics & KPIs", "Ctrl+Shift+B"),
            ("📈 KPI Tracker", self.open_kpi_tracker, "Track key performance indicators", "Ctrl+Shift+K"),
            ("📄 Report Generator", self.open_report_generator, "Generate business reports", "Ctrl+Shift+R"),
            ("🤝 CRM Manager", self.open_crm_manager, "Customer relationship management", "Ctrl+Shift+M"),
        ]
        
        positions = [(i, j) for i in range(7) for j in range(3)]
        
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
    
    def create_dashboard(self):
        """Create main dashboard"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome message
        welcome = QLabel("Welcome to Westfall Personal Assistant")
        welcome.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)
        
        # Quick stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        
        # Create stat cards
        stats = [
            ("📧 Unread Emails", "12"),
            ("✅ Tasks Today", "8"),
            ("📅 Events", "3"),
            ("📰 News Updates", "24"),
            ("💰 Revenue Today", "$2,450"),
            ("👥 Active Clients", "15"),
        ]
        
        for i, (label, value) in enumerate(stats):
            card = self.create_stat_card(label, value)
            stats_grid.addWidget(card, i // 3, i % 3)
        
        layout.addLayout(stats_grid)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 2px solid #ff0000;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff0000;
            }
        """)
        
        activity_layout = QVBoxLayout()
        activity_list = QListWidget()
        activity_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #ff0000;
            }
        """)
        
        activities = [
            "09:30 - New email from John Doe",
            "10:15 - Task 'Review proposal' completed",
            "11:00 - Meeting with Client ABC in 1 hour",
            "14:30 - Invoice #1045 paid - $3,500",
            "15:45 - New lead from website contact form",
        ]
        
        for activity in activities:
            activity_list.addItem(activity)
        
        activity_layout.addWidget(activity_list)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        layout.addStretch()
        
        return dashboard
    
    def create_stat_card(self, label, value):
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 10px;
                padding: 20px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
            }
        """)
        
        layout = QVBoxLayout()
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("color: #ff0000; font-size: 28px; font-weight: bold;")
        layout.addWidget(value_widget)
        
        card.setLayout(layout)
        return card
    
    def show_widget(self, widget_class, title):
        """Show a widget in the content area"""
        # Cache widgets for faster switching
        widget_name = widget_class.__name__
        
        if widget_name not in self.widgets_cache:
            widget = widget_class()
            # Convert window to widget if necessary
            if isinstance(widget, QMainWindow):
                widget = widget.centralWidget()
            self.widgets_cache[widget_name] = widget
            self.stacked_widget.addWidget(widget)
        
        widget = self.widgets_cache[widget_name]
        self.stacked_widget.setCurrentWidget(widget)
        
        # Update breadcrumb
        self.breadcrumb.setText(title)
        
        # Show back button if not on dashboard
        if title != "Dashboard":
            self.back_btn.show()
            self.widget_stack.append(("Dashboard", self.dashboard))
        
        self.status_bar.showMessage(f"Viewing {title}")
    
    def go_back(self):
        """Go back to previous widget"""
        if self.widget_stack:
            title, widget = self.widget_stack.pop()
            self.stacked_widget.setCurrentWidget(widget)
            self.breadcrumb.setText(title)
            
            if not self.widget_stack:
                self.back_btn.hide()
    
    def show_dashboard(self):
        """Show main dashboard"""
        self.stacked_widget.setCurrentWidget(self.dashboard)
        self.breadcrumb.setText("Dashboard")
        self.back_btn.hide()
        self.widget_stack.clear()
    
    # Navigation methods for new architecture
    def show_email(self):
        self.show_widget(EmailWidget, "Email")
    
    def show_passwords(self):
        self.show_widget(PasswordManagerWindow, "Password Manager")
    
    def show_notes(self):
        self.show_widget(NotesWidget, "Notes")
    
    def show_calculator(self):
        self.show_widget(CalculatorWidget, "Calculator")
    
    def show_calendar(self):
        self.show_widget(CalendarWidget, "Calendar")
    
    def show_weather(self):
        self.show_widget(WeatherWindow, "Weather")
    
    def show_news(self):
        self.show_widget(NewsWidget, "News")
    
    def show_browser(self):
        self.show_widget(BrowserWidget, "Browser")
    
    def show_files(self):
        self.show_widget(FileManagerWidget, "File Manager")
    
    def show_todo(self):
        self.show_widget(TodoWidget, "Todo List")
    
    def show_contacts(self):
        self.show_widget(ContactsWidget, "Contacts")
    
    def show_finance(self):
        self.show_widget(FinanceWidget, "Finance")
    
    def show_recipes(self):
        self.show_widget(RecipeWidget, "Recipes")
    
    def show_music(self):
        self.show_widget(MusicPlayerWindow, "Music Player")
    
    def show_settings(self):
        self.show_widget(SettingsWidget, "Settings")
    
    def show_business_dashboard(self):
        self.show_widget(BusinessDashboard, "Business Dashboard")
    
    def show_crm(self):
        self.show_widget(CRMManager, "CRM")
    
    def show_screen_intelligence(self):
        # Use MultiMonitorCapture which we know exists
        try:
            from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
            self.show_widget(MultiMonitorCapture, "Screen Intelligence")
        except ImportError:
            QMessageBox.critical(self, "Module Not Found", 
                "Screen Intelligence module not found.\n"
                "Please ensure all files were created properly.")
    
    def toggle_ai_assistant(self):
        """Toggle AI Assistant"""
        if not hasattr(self, 'ai_assistant'):
            self.init_ai()
        
        if self.ai_assistant.isVisible():
            self.ai_assistant.hide()
        else:
            self.ai_assistant.show()
            self.ai_assistant.raise_()
            self.ai_assistant.activateWindow()
    
    def apply_black_red_theme(self):
        """Apply black and red theme to entire application"""
        app = QApplication.instance()
        app.setStyle('Fusion')
        
        # Create dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(26, 26, 26))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(26, 26, 26))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(255, 0, 0))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
    
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
        
        # New Business Intelligence shortcuts
        QShortcut(QKeySequence("Ctrl+I"), self, self.open_screen_intelligence)
        QShortcut(QKeySequence("Ctrl+Shift+B"), self, self.open_business_dashboard)
        QShortcut(QKeySequence("Ctrl+Shift+K"), self, self.open_kpi_tracker)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.open_report_generator)
        QShortcut(QKeySequence("Ctrl+Shift+M"), self, self.open_crm_manager)
        
        # System shortcuts
        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+Space"), self, self.toggle_ai_chat)
        QShortcut(QKeySequence("Ctrl+/"), self, self.show_shortcuts)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_dark_mode)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Escape"), self, self.handle_escape)
        QShortcut(QKeySequence("F1"), self, self.show_help)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
    
    def init_ai(self):
        """Initialize AI Assistant"""
        self.ai_assistant = AIChatWidget(self)
        self.ai_assistant.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.ai_assistant.setGeometry(self.x() + self.width() - 420, self.y() + 100, 400, 600)
        
        # Apply black/red theme to AI
        self.ai_assistant.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: white;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 10px;
            }
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QLabel {
                color: white;
            }
        """)
    
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
        
        <h2>Business Intelligence Shortcuts</h2>
        <table>
        <tr><td><b>Ctrl+I</b></td><td>Open Screen Intelligence</td></tr>
        <tr><td><b>Ctrl+Shift+B</b></td><td>Open Business Dashboard</td></tr>
        <tr><td><b>Ctrl+Shift+K</b></td><td>Open KPI Tracker</td></tr>
        <tr><td><b>Ctrl+Shift+R</b></td><td>Open Report Generator</td></tr>
        <tr><td><b>Ctrl+Shift+M</b></td><td>Open CRM Manager</td></tr>
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
    
    # New Business Intelligence window opening methods
    def open_screen_intelligence(self):
        if 'screen_intelligence' not in self.windows:
            self.windows['screen_intelligence'] = MultiMonitorCapture()
        self.windows['screen_intelligence'].show()
        self.windows['screen_intelligence'].raise_()
        self.windows['screen_intelligence'].activateWindow()
        self.ai_chat.parent_window = self.windows['screen_intelligence']
        self.status_bar.showMessage("Screen Intelligence opened - Multi-monitor capture & analysis")
    
    def open_business_dashboard(self):
        if 'business_dashboard' not in self.windows:
            self.windows['business_dashboard'] = BusinessDashboard()
        self.windows['business_dashboard'].show()
        self.windows['business_dashboard'].raise_()
        self.windows['business_dashboard'].activateWindow()
        self.ai_chat.parent_window = self.windows['business_dashboard']
        self.status_bar.showMessage("Business Dashboard opened - Track your business metrics")
    
    def open_kpi_tracker(self):
        if 'kpi_tracker' not in self.windows:
            self.windows['kpi_tracker'] = KPITracker()
        self.windows['kpi_tracker'].show()
        self.windows['kpi_tracker'].raise_()
        self.windows['kpi_tracker'].activateWindow()
        self.ai_chat.parent_window = self.windows['kpi_tracker']
        self.status_bar.showMessage("KPI Tracker opened - Monitor key performance indicators")
    
    def open_report_generator(self):
        if 'report_generator' not in self.windows:
            self.windows['report_generator'] = ReportGenerator()
        self.windows['report_generator'].show()
        self.windows['report_generator'].raise_()
        self.windows['report_generator'].activateWindow()
        self.ai_chat.parent_window = self.windows['report_generator']
        self.status_bar.showMessage("Report Generator opened - Create automated business reports")
    
    def open_crm_manager(self):
        if 'crm_manager' not in self.windows:
            self.windows['crm_manager'] = CRMManager()
        self.windows['crm_manager'].show()
        self.windows['crm_manager'].raise_()
        self.windows['crm_manager'].activateWindow()
        self.ai_chat.parent_window = self.windows['crm_manager']
        self.status_bar.showMessage("CRM Manager opened - Manage customer relationships & sales pipeline")
    
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

# Widget wrapper classes
class EmailWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.email_window = EmailWindow()
        if hasattr(self.email_window, 'centralWidget'):
            layout.addWidget(self.email_window.centralWidget())
        else:
            layout.addWidget(self.email_window)
        self.setLayout(layout)

class NotesWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.notes_window = NotesWindow()
        if hasattr(self.notes_window, 'centralWidget'):
            layout.addWidget(self.notes_window.centralWidget())
        else:
            layout.addWidget(self.notes_window)
        self.setLayout(layout)

class CalculatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.calc_window = CalculatorWindow()
        if hasattr(self.calc_window, 'centralWidget'):
            layout.addWidget(self.calc_window.centralWidget())
        else:
            layout.addWidget(self.calc_window)
        self.setLayout(layout)

class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.calendar_window = CalendarWindow()
        if hasattr(self.calendar_window, 'centralWidget'):
            layout.addWidget(self.calendar_window.centralWidget())
        else:
            layout.addWidget(self.calendar_window)
        self.setLayout(layout)

class NewsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.news_window = NewsWindow()
        if hasattr(self.news_window, 'centralWidget'):
            layout.addWidget(self.news_window.centralWidget())
        else:
            layout.addWidget(self.news_window)
        self.setLayout(layout)

class BrowserWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.browser_window = BrowserWindow()
        if hasattr(self.browser_window, 'centralWidget'):
            layout.addWidget(self.browser_window.centralWidget())
        else:
            layout.addWidget(self.browser_window)
        self.setLayout(layout)

class FileManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.file_window = FileManagerWindow()
        if hasattr(self.file_window, 'centralWidget'):
            layout.addWidget(self.file_window.centralWidget())
        else:
            layout.addWidget(self.file_window)
        self.setLayout(layout)

class TodoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.todo_window = TodoWindow()
        if hasattr(self.todo_window, 'centralWidget'):
            layout.addWidget(self.todo_window.centralWidget())
        else:
            layout.addWidget(self.todo_window)
        self.setLayout(layout)

class ContactsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.contacts_window = ContactsWindow()
        if hasattr(self.contacts_window, 'centralWidget'):
            layout.addWidget(self.contacts_window.centralWidget())
        else:
            layout.addWidget(self.contacts_window)
        self.setLayout(layout)

class FinanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.finance_window = FinanceWindow()
        if hasattr(self.finance_window, 'centralWidget'):
            layout.addWidget(self.finance_window.centralWidget())
        else:
            layout.addWidget(self.finance_window)
        self.setLayout(layout)

class RecipeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.recipe_window = RecipeWindow()
        if hasattr(self.recipe_window, 'centralWidget'):
            layout.addWidget(self.recipe_window.centralWidget())
        else:
            layout.addWidget(self.recipe_window)
        self.setLayout(layout)

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.settings_window = SettingsWindow()
        if hasattr(self.settings_window, 'centralWidget'):
            layout.addWidget(self.settings_window.centralWidget())
        else:
            layout.addWidget(self.settings_window)
        self.setLayout(layout)

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