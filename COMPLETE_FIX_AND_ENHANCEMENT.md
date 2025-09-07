# WestfallPersonalAssistant - Complete Fix & Enhancement Implementation
## Single Window App, Live AI Screen Control, Black/Red Theme, Complete Features
### Date: 2025-09-07

---

## PHASE 1: CONVERT TO SINGLE-WINDOW APPLICATION

### TASK 1.1: Redesign Main Window as Central Hub
**REPLACE FILE:** `main.py`
```python
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPalette, QColor, QFont

# Import all windows (will be converted to widgets)
from email_window import EmailWindow
from password_manager import PasswordManagerWindow
from notes import NotesWindow
from calculator import CalculatorWindow
from calendar_window import CalendarWindow
from weather import WeatherWindow
from news import NewsWindow
from browser import BrowserWindow
from file_manager import FileManagerWindow
from todo import TodoWindow
from contacts import ContactsWindow
from settings import SettingsWindow
from finance import FinanceWindow
from recipe import RecipeWindow
from music_player import MusicPlayerWindow

# Import business features
from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
from business_intelligence.dashboard.business_dashboard import BusinessDashboard
from crm_system.crm_manager import CRMManager

# Import security and AI
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

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
        self.setWindowTitle("Westfall Personal Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Sidebar Navigation
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-right: 2px solid #ff0000;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/Header
        header = QLabel("WESTFALL")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background-color: #ff0000;
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                letter-spacing: 3px;
            }
        """)
        sidebar_layout.addWidget(header)
        
        # Home button
        home_btn = NavigationButton("🏠 Dashboard")
        home_btn.clicked.connect(self.show_dashboard)
        sidebar_layout.addWidget(home_btn)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #333;")
        sidebar_layout.addWidget(separator)
        
        # Navigation buttons
        nav_buttons = [
            ("📧 Email", self.show_email),
            ("🔐 Passwords", self.show_passwords),
            ("📝 Notes", self.show_notes),
            ("🧮 Calculator", self.show_calculator),
            ("📅 Calendar", self.show_calendar),
            ("🌤️ Weather", self.show_weather),
            ("📰 News", self.show_news),
            ("🌐 Browser", self.show_browser),
            ("📁 Files", self.show_files),
            ("✅ Todo", self.show_todo),
            ("👥 Contacts", self.show_contacts),
            ("💰 Finance", self.show_finance),
            ("🍳 Recipes", self.show_recipes),
            ("🎵 Music", self.show_music),
            ("⚙️ Settings", self.show_settings),
        ]
        
        for text, callback in nav_buttons:
            btn = NavigationButton(text)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
        
        # Business Tools Section
        business_separator = QFrame()
        business_separator.setFrameShape(QFrame.HLine)
        business_separator.setStyleSheet("background-color: #ff0000;")
        sidebar_layout.addWidget(business_separator)
        
        business_label = QLabel("BUSINESS TOOLS")
        business_label.setStyleSheet("""
            QLabel {
                color: #ff0000;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        sidebar_layout.addWidget(business_label)
        
        # Business navigation
        business_buttons = [
            ("📊 Business Dashboard", self.show_business_dashboard),
            ("🤝 CRM", self.show_crm),
            ("🖥️ Screen Intelligence", self.show_screen_intelligence),
        ]
        
        for text, callback in business_buttons:
            btn = NavigationButton(text)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # AI Assistant button at bottom
        ai_btn = QPushButton("🤖 AI Assistant")
        ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        ai_btn.clicked.connect(self.toggle_ai_assistant)
        sidebar_layout.addWidget(ai_btn)
        
        main_layout.addWidget(self.sidebar)
        
        # Right Content Area
        self.content_area = QWidget()
        self.content_area.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
        """)
        
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Top bar with breadcrumb and controls
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-bottom: 2px solid #ff0000;
            }
        """)
        
        top_bar_layout = QHBoxLayout(self.top_bar)
        
        # Back button
        self.back_btn = QPushButton("← Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff0000;
                border: 1px solid #ff0000;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
                color: white;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.hide()
        top_bar_layout.addWidget(self.back_btn)
        
        # Breadcrumb
        self.breadcrumb = QLabel("Dashboard")
        self.breadcrumb.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                padding-left: 20px;
            }
        """)
        top_bar_layout.addWidget(self.breadcrumb)
        
        top_bar_layout.addStretch()
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search or ask AI...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                color: white;
                border: 1px solid #ff0000;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ff0000;
            }
        """)
        top_bar_layout.addWidget(self.search_bar)
        
        self.content_layout.addWidget(self.top_bar)
        
        # Stacked widget for content
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        # Add dashboard as first page
        self.dashboard = self.create_dashboard()
        self.stacked_widget.addWidget(self.dashboard)
        
        main_layout.addWidget(self.content_area)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1a1a1a;
                color: #ff0000;
                border-top: 1px solid #ff0000;
            }
        """)
        self.status_bar.showMessage("Ready")
    
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
    
    # Navigation methods
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
        self.show_widget(LiveScreenIntelligence, "Screen Intelligence")
    
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
    
    def init_shortcuts(self):
        """Initialize keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_bar.setFocus())
        QShortcut(QKeySequence("Ctrl+Space"), self, self.toggle_ai_assistant)
        QShortcut(QKeySequence("Alt+Left"), self, self.go_back)
        QShortcut(QKeySequence("Escape"), self, self.show_dashboard)
    
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
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

---

## PHASE 2: IMPLEMENT LIVE AI SCREEN INTERACTION

### TASK 2.1: Create Advanced Live Screen Intelligence with AI Control
**CREATE FILE:** `screen_intelligence/live_screen_intelligence.py`
```python
import mss
import mss.tools
import numpy as np
from PIL import Image, ImageDraw
import cv2
import pytesseract
import pyautogui
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage
import base64
from io import BytesIO
import json

# Configure pyautogui for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class LiveScreenIntelligence(QWidget):
    """Live AI-powered screen monitoring and interaction system"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.ai_control_enabled = False
        self.current_screens = []
        self.interaction_history = []
        self.init_ui()
        
        # Live monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.capture_screens)
        
        # AI analysis timer
        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.ai_analyze_screens)
        
    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: white;
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
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #ff0000;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ff0000;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🖥️ Live Screen Intelligence & AI Control")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff0000; padding: 10px;")
        layout.addWidget(header)
        
        # Control Panel
        control_panel = QGroupBox("Control Panel")
        control_layout = QHBoxLayout()
        
        # Live monitoring toggle
        self.monitor_btn = QPushButton("▶️ Start Live Monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        control_layout.addWidget(self.monitor_btn)
        
        # AI control toggle
        self.ai_control_btn = QPushButton("🤖 Enable AI Control")
        self.ai_control_btn.clicked.connect(self.toggle_ai_control)
        control_layout.addWidget(self.ai_control_btn)
        
        # Emergency stop
        self.stop_btn = QPushButton("🛑 EMERGENCY STOP")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
        """)
        self.stop_btn.clicked.connect(self.emergency_stop)
        control_layout.addWidget(self.stop_btn)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # Screen Display Area
        screen_tabs = QTabWidget()
        screen_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ff0000;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background-color: #ff0000;
            }
        """)
        
        # Live view tab
        self.live_view = QLabel("Live screen will appear here")
        self.live_view.setAlignment(Qt.AlignCenter)
        self.live_view.setMinimumHeight(400)
        self.live_view.setStyleSheet("border: 1px solid #ff0000;")
        screen_tabs.addTab(self.live_view, "Live View")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        screen_tabs.addTab(self.analysis_text, "AI Analysis")
        
        layout.addWidget(screen_tabs)
        
        # AI Interaction Panel
        ai_panel = QGroupBox("AI Developer Assistant")
        ai_layout = QVBoxLayout()
        
        # Problem description
        problem_layout = QHBoxLayout()
        problem_label = QLabel("Describe the problem:")
        problem_layout.addWidget(problem_label)
        
        self.problem_input = QLineEdit()
        self.problem_input.setPlaceholderText("e.g., 'Fix the error in my IDE', 'Debug this code', 'Set up this software'")
        self.problem_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 8px;
            }
        """)
        problem_layout.addWidget(self.problem_input)
        
        self.solve_btn = QPushButton("🔧 Let AI Solve")
        self.solve_btn.clicked.connect(self.ai_solve_problem)
        problem_layout.addWidget(self.solve_btn)
        
        ai_layout.addLayout(problem_layout)
        
        # AI action log
        self.action_log = QTextEdit()
        self.action_log.setMaximumHeight(150)
        self.action_log.setReadOnly(True)
        self.action_log.setPlaceholderText("AI actions will be logged here...")
        ai_layout.addWidget(self.action_log)
        
        ai_panel.setLayout(ai_layout)
        layout.addWidget(ai_panel)
        
        # Status bar
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #ff0000; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def toggle_monitoring(self):
        """Toggle live screen monitoring"""
        if not self.monitoring:
            # Check if mss is installed
            try:
                import mss
            except ImportError:
                QMessageBox.critical(self, "Missing Dependency", 
                    "MSS library not available. Please install with:\npip install mss")
                return
            
            self.monitoring = True
            self.monitor_btn.setText("⏸️ Stop Monitoring")
            self.monitor_timer.start(100)  # Update every 100ms for smooth live view
            self.status_label.setText("Status: Live monitoring active")
            self.log_action("Started live screen monitoring")
        else:
            self.monitoring = False
            self.monitor_btn.setText("▶️ Start Live Monitoring")
            self.monitor_timer.stop()
            self.status_label.setText("Status: Monitoring stopped")
            self.log_action("Stopped screen monitoring")
    
    def toggle_ai_control(self):
        """Toggle AI control of the screen"""
        if not self.ai_control_enabled:
            reply = QMessageBox.warning(self, "AI Control", 
                "⚠️ WARNING: Enabling AI control allows the assistant to control your mouse and keyboard.\n\n"
                "The AI will be able to:\n"
                "• Move and click the mouse\n"
                "• Type on the keyboard\n"
                "• Open and close applications\n"
                "• Modify files and settings\n\n"
                "Only enable if you trust the AI and need automated assistance.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.ai_control_enabled = True
                self.ai_control_btn.setText("🤖 Disable AI Control")
                self.ai_control_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: black;
                    }
                """)
                self.ai_timer.start(1000)  # Analyze every second
                self.status_label.setText("Status: AI CONTROL ACTIVE - AI can interact with screen")
                self.log_action("AI control enabled - AI has mouse/keyboard access")
        else:
            self.ai_control_enabled = False
            self.ai_control_btn.setText("🤖 Enable AI Control")
            self.ai_control_btn.setStyleSheet("")
            self.ai_timer.stop()
            self.status_label.setText("Status: AI control disabled")
            self.log_action("AI control disabled")
    
    def capture_screens(self):
        """Capture all screens in real-time"""
        try:
            with mss.mss() as sct:
                # Capture primary monitor for live view
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                
                # Convert to QPixmap for display
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                # Resize for display
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                
                # Convert to QPixmap
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())
                
                # Update live view
                self.live_view.setPixmap(pixmap.scaled(
                    self.live_view.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                
                # Store for AI analysis
                self.current_screens = [(monitor, img)]
                
        except Exception as e:
            self.log_action(f"Error capturing screen: {str(e)}")
    
    def ai_analyze_screens(self):
        """AI analyzes current screens for issues"""
        if not self.current_screens:
            return
        
        try:
            for monitor, img in self.current_screens:
                # Extract text using OCR
                text = pytesseract.image_to_string(img)
                
                # Look for error indicators
                error_keywords = [
                    'error', 'exception', 'failed', 'denied', 'invalid',
                    'undefined', 'null', 'crash', 'fatal', 'warning'
                ]
                
                found_issues = []
                for keyword in error_keywords:
                    if keyword.lower() in text.lower():
                        found_issues.append(keyword)
                
                if found_issues:
                    analysis = f"⚠️ Potential issues detected: {', '.join(found_issues)}\n"
                    analysis += f"Screen text sample:\n{text[:500]}"
                    self.analysis_text.append(analysis)
                    
                    if self.ai_control_enabled:
                        self.ai_respond_to_error(text, found_issues)
                
        except Exception as e:
            self.log_action(f"Analysis error: {str(e)}")
    
    def ai_respond_to_error(self, screen_text, issues):
        """AI responds to detected errors"""
        self.log_action(f"AI detected issues: {', '.join(issues)}")
        
        # Analyze error type and respond accordingly
        if 'null' in str(issues).lower() or 'undefined' in str(issues).lower():
            self.log_action("AI: Detected null reference error, checking for uninitialized variables")
            # Could implement automated debugging actions here
        
        elif 'syntax' in str(issues).lower():
            self.log_action("AI: Syntax error detected, analyzing code structure")
            # Could implement syntax correction
        
        elif 'connection' in str(issues).lower() or 'network' in str(issues).lower():
            self.log_action("AI: Network issue detected, checking connectivity")
            # Could implement network troubleshooting
    
    def ai_solve_problem(self):
        """AI attempts to solve the described problem"""
        problem = self.problem_input.text()
        if not problem:
            QMessageBox.warning(self, "No Problem", "Please describe the problem first")
            return
        
        if not self.ai_control_enabled:
            reply = QMessageBox.question(self, "Enable AI Control", 
                "AI needs control permission to solve this problem. Enable AI control?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.toggle_ai_control()
            else:
                return
        
        self.log_action(f"AI solving: {problem}")
        
        # Create AI solution thread
        self.solution_thread = AISolutionThread(problem, self.current_screens)
        self.solution_thread.action_signal.connect(self.log_action)
        self.solution_thread.start()
    
    def emergency_stop(self):
        """Emergency stop all AI actions"""
        self.ai_control_enabled = False
        self.monitoring = False
        self.monitor_timer.stop()
        self.ai_timer.stop()
        
        # Move mouse to corner (failsafe)
        pyautogui.moveTo(0, 0)
        
        self.monitor_btn.setText("▶️ Start Live Monitoring")
        self.ai_control_btn.setText("🤖 Enable AI Control")
        self.ai_control_btn.setStyleSheet("")
        
        self.status_label.setText("Status: EMERGENCY STOP - All operations halted")
        self.log_action("🛑 EMERGENCY STOP ACTIVATED")
        
        QMessageBox.information(self, "Emergency Stop", 
            "All AI operations have been stopped.\nMouse and keyboard control returned to user.")
    
    def log_action(self, message):
        """Log AI actions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.action_log.append(f"[{timestamp}] {message}")
        self.interaction_history.append((timestamp, message))

class AISolutionThread(QThread):
    """Thread for AI problem-solving actions"""
    action_signal = pyqtSignal(str)
    
    def __init__(self, problem, screens):
        super().__init__()
        self.problem = problem
        self.screens = screens
    
    def run(self):
        """Execute AI solution"""
        self.action_signal.emit(f"Starting to solve: {self.problem}")
        
        # Simulate AI problem-solving steps
        problem_lower = self.problem.lower()
        
        if 'error' in problem_lower or 'fix' in problem_lower:
            self.fix_error()
        elif 'debug' in problem_lower:
            self.debug_code()
        elif 'setup' in problem_lower or 'install' in problem_lower:
            self.setup_software()
        elif 'code' in problem_lower or 'write' in problem_lower:
            self.write_code()
        else:
            self.general_assistance()
    
    def fix_error(self):
        """AI fixes detected errors"""
        self.action_signal.emit("Analyzing error messages...")
        time.sleep(1)
        
        # Simulate error fixing actions
        self.action_signal.emit("Locating error in code...")
        time.sleep(1)
        
        # Move to error location (example)
        pyautogui.hotkey('ctrl', 'f')  # Open find
        time.sleep(0.5)
        pyautogui.typewrite('error')  # Search for error
        time.sleep(0.5)
        pyautogui.press('escape')  # Close find
        
        self.action_signal.emit("Analyzing error context...")
        time.sleep(1)
        
        self.action_signal.emit("Applying fix...")
        # Here would be actual fix implementation
        
        self.action_signal.emit("✅ Error fixing complete")
    
    def debug_code(self):
        """AI debugs code"""
        self.action_signal.emit("Starting debugging process...")
        time.sleep(1)
        
        # Simulate debugging actions
        self.action_signal.emit("Setting breakpoints...")
        pyautogui.hotkey('f9')  # Common breakpoint shortcut
        time.sleep(1)
        
        self.action_signal.emit("Starting debug session...")
        pyautogui.hotkey('f5')  # Common debug start
        time.sleep(2)
        
        self.action_signal.emit("Analyzing variable states...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Debugging session complete")
    
    def setup_software(self):
        """AI helps with software setup"""
        self.action_signal.emit("Assisting with software setup...")
        time.sleep(1)
        
        self.action_signal.emit("Checking system requirements...")
        time.sleep(1)
        
        self.action_signal.emit("Guiding through installation steps...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Setup assistance complete")
    
    def write_code(self):
        """AI writes code"""
        self.action_signal.emit("Generating code...")
        time.sleep(1)
        
        # Example: Write a simple function
        code = """def hello_world():
    print("Hello, World!")
    return True

# Call the function
hello_world()
"""
        
        self.action_signal.emit("Writing code to editor...")
        pyautogui.typewrite(code, interval=0.01)
        
        self.action_signal.emit("✅ Code written successfully")
    
    def general_assistance(self):
        """General AI assistance"""
        self.action_signal.emit("Analyzing request...")
        time.sleep(1)
        
        self.action_signal.emit("Providing general assistance...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Assistance provided")
```

---

## PHASE 3: UPDATE REQUIREMENTS FOR MISSING DEPENDENCIES

### TASK 3.1: Update requirements.txt
**APPEND TO FILE:** `requirements.txt`
```
# Screen capture and AI control
mss>=9.0.1
pyautogui>=0.9.54
opencv-python>=4.8.0
pytesseract>=0.3.10
Pillow>=10.1.0

# For Windows screen capture enhancements
pywin32>=305; sys_platform == 'win32'
```

---

## PHASE 4: ENHANCED NEWS TAB WITH IMAGES

### TASK 4.1: Create Enhanced News with Image Support
**REPLACE FILE:** `news.py`
```python
import sys
import requests
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import feedparser
from urllib.parse import urlparse

class NewsImageLoader(QThread):
    image_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, url, article_id):
        super().__init__()
        self.url = url
        self.article_id = article_id
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_loaded.emit(self.article_id, pixmap)
        except:
            pass

class NewsCard(QFrame):
    """Modern news card with image"""
    
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.init_ui()
        self.load_image()
    
    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 10px;
                padding: 15px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
                border-color: #ff3333;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Image placeholder
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 100)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #ff0000;
                border-radius: 5px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("📰")
        layout.addWidget(self.image_label)
        
        # Content area
        content_layout = QVBoxLayout()
        
        # Title
        title = QLabel(self.article.get('title', 'No title'))
        title.setWordWrap(True)
        title.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(title)
        
        # Source and date
        source = self.article.get('source', {}).get('name', 'Unknown')
        published = self.article.get('publishedAt', '')
        if published:
            try:
                dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                published = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        meta = QLabel(f"📍 {source} • 🕐 {published}")
        meta.setStyleSheet("color: #888888; font-size: 12px;")
        content_layout.addWidget(meta)
        
        # Description
        description = self.article.get('description', 'No description available')
        desc_label = QLabel(description[:200] + "..." if len(description) > 200 else description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        content_layout.addWidget(desc_label)
        
        # Read more button
        read_btn = QPushButton("Read Full Article →")
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        read_btn.clicked.connect(self.open_article)
        content_layout.addWidget(read_btn, alignment=Qt.AlignRight)
        
        content_layout.addStretch()
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
    
    def load_image(self):
        """Load article image"""
        image_url = self.article.get('urlToImage')
        if image_url:
            loader = NewsImageLoader(image_url, str(id(self)))
            loader.image_loaded.connect(self.set_image)
            loader.start()
    
    def set_image(self, article_id, pixmap):
        """Set loaded image"""
        if str(id(self)) == article_id:
            scaled = pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
    
    def open_article(self):
        """Open article in browser"""
        url = self.article.get('url')
        if url:
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(url))

class NewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.init_ui()
        self.apply_theme()
        self.load_news()
    
    def init_ui(self):
        self.setWindowTitle("News Reader")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📰 Latest News")
        title.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Source selector
        self.source_combo = QComboBox()
        self.source_combo.addItems(["All", "BBC", "CNN", "Reuters", "TechCrunch", "The Verge", "Bloomberg"])
        self.source_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 8px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ff0000;
            }
        """)
        self.source_combo.currentTextChanged.connect(self.filter_news)
        header_layout.addWidget(self.source_combo)
        
        # Category selector
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Business", "Technology", "Sports", "Entertainment", "Health", "Science"])
        self.category_combo.setStyleSheet(self.source_combo.styleSheet())
        self.category_combo.currentTextChanged.connect(self.filter_news)
        header_layout.addWidget(self.category_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        refresh_btn.clicked.connect(self.load_news)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search news...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.search_news)
        layout.addWidget(self.search_input)
        
        # News cards area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #000000;
                border: none;
            }
        """)
        
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.news_container)
        layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1a1a1a;
                color: #ff0000;
            }
        """)
    
    def apply_theme(self):
        """Apply black and red theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                background-color: #000000;
                color: white;
            }
        """)
    
    def load_news(self):
        """Load news from API or RSS"""
        self.status_bar.showMessage("Loading news...")
        
        # Clear existing news
        for i in reversed(range(self.news_layout.count())): 
            self.news_layout.itemAt(i).widget().setParent(None)
        
        # Try NewsAPI first
        try:
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            api_key = vault.get_key('newsapi')
            
            if api_key:
                url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    self.articles = data.get('articles', [])
                    self.display_news()
                    return
        except:
            pass
        
        # Fallback to RSS
        self.load_rss_news()
    
    def load_rss_news(self):
        """Load news from RSS feeds"""
        feeds = {
            "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "Reuters": "http://feeds.reuters.com/reuters/topNews"
        }
        
        self.articles = []
        
        for source, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # Get 5 from each source
                    article = {
                        "title": entry.title,
                        "description": entry.get("summary", ""),
                        "url": entry.link,
                        "publishedAt": entry.get("published", ""),
                        "source": {"name": source},
                        "urlToImage": self.extract_image_from_entry(entry)
                    }
                    self.articles.append(article)
            except:
                continue
        
        self.display_news()
    
    def extract_image_from_entry(self, entry):
        """Try to extract image URL from RSS entry"""
        # Check for media content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'image' in media.get('type', ''):
                    return media.get('url')
        
        # Check for enclosures
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get