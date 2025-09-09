import sys
import os

# FIX: Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPalette, QColor, QFont

# Import all windows
try:
    from placeholder_windows import EmailWindow
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

from services.weather_service import WeatherWindow
from services.news_service import NewsWindow

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
    from utils.entrepreneur_config import SettingsWindow
except ImportError:
    from placeholder_windows import SettingsWindow

try:
    from finance import FinanceWindow
except ImportError:
    from placeholder_windows import FinanceWindow

try:
    from crm_system import CRMWindow
except ImportError:
    from placeholder_windows import CRMWindow

# Import business features
try:
    from business_intelligence.dashboard.business_dashboard import BusinessDashboard
    from crm_system.crm_manager import CRMManager
    BUSINESS_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Business features import error: {e}")
    BUSINESS_FEATURES_AVAILABLE = False
    class BusinessDashboard(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("Business Dashboard - Import Error")
            layout.addWidget(label)
            self.setLayout(layout)
    
    class CRMManager(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("CRM - Import Error")
            layout.addWidget(label)
            self.setLayout(layout)

# Import time tracking module
try:
    from time_tracking import TimeTrackingWidget
    TIME_TRACKING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Time tracking import error: {e}")
    TIME_TRACKING_AVAILABLE = False
    class TimeTrackingWidget(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("Time Tracking - Import Error")
            layout.addWidget(label)
            self.setLayout(layout)

# Import security and AI
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

# Import dependency manager if available
try:
    from utils.dependency_manager import DependencyManager, DependencyManagerDialog
    DEPENDENCY_MANAGER_AVAILABLE = True
except ImportError:
    DEPENDENCY_MANAGER_AVAILABLE = False

# Import advanced features
try:
    from utils.voice_control import get_voice_manager
    from utils.marketplace_manager import get_marketplace_manager
    from utils.template_exchange import get_template_manager
    from utils.api_gateway import get_api_gateway
    from util.tailor_pack_manager import get_tailor_pack_manager
    from utils.tailor_pack_widget import TailorPackManagerWidget
    from utils.welcome_experience import show_welcome_if_needed
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Advanced features import error: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

# Handle screen intelligence imports
try:
    from screen_intelligence.enhanced_screen_intelligence import ScreenIntelligenceWidget, EnhancedScreenIntelligence
    # Use Enhanced version as primary
    LiveScreenIntelligence = EnhancedScreenIntelligence
    SCREEN_INTELLIGENCE_AVAILABLE = True
    ENHANCED_SCREEN_INTELLIGENCE = True
except ImportError:
    try:
        from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
        # Use MultiMonitorCapture as LiveScreenIntelligence
        LiveScreenIntelligence = MultiMonitorCapture
        SCREEN_INTELLIGENCE_AVAILABLE = True
        ENHANCED_SCREEN_INTELLIGENCE = False
    except ImportError as e:
        print(f"Warning: Screen intelligence import error: {e}")
        SCREEN_INTELLIGENCE_AVAILABLE = False
        ENHANCED_SCREEN_INTELLIGENCE = False
    class LiveScreenIntelligence(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("Screen Intelligence - Import Error")
            layout.addWidget(label)
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
        
        # Show welcome experience for new users
        QTimer.singleShot(1000, self.show_welcome_if_needed)  # Delay to ensure UI is ready
    
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
        self.setWindowTitle("Westfall Assistant - Entrepreneur Edition")
        self.setGeometry(100, 100, 900, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # Header with gradient
        header = QLabel("Westfall Assistant - Entrepreneur Edition")
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
        header.setToolTip("Your AI-powered business assistant with Tailor Pack extensions - Built for entrepreneurs who demand efficiency and intelligence")
        main_layout.addWidget(header)
        
        # Quick Access Bar (for recent/favorite features)
        quick_access_widget = QWidget()
        quick_access_layout = QHBoxLayout(quick_access_widget)
        quick_access_label = QLabel("🚀 Entrepreneur Quick Access:")
        quick_access_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        quick_access_layout.addWidget(quick_access_label)
        
        self.quick_access_buttons = QHBoxLayout()
        quick_access_layout.addLayout(self.quick_access_buttons)
        quick_access_layout.addStretch()
        
        # Dependencies check button
        if DEPENDENCY_MANAGER_AVAILABLE:
            self.check_deps_btn = QPushButton("📦 Check Dependencies")
            self.check_deps_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a1a;
                    color: #ff0000;
                    border: 1px solid #ff0000;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff0000;
                    color: white;
                }
            """)
            self.check_deps_btn.clicked.connect(self.check_dependencies)
            quick_access_layout.addWidget(self.check_deps_btn)
        
        # Import Tailor Pack button (prominent placement)
        self.import_pack_btn = QPushButton("📦 Import Pack")
        self.import_pack_btn.setToolTip("Import a new Tailor Pack to extend functionality")
        self.import_pack_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.import_pack_btn.clicked.connect(self.quick_import_pack)
        quick_access_layout.addWidget(self.import_pack_btn)
        
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
        self.search_input.setPlaceholderText("🔍 Smart Business Search: 'revenue', 'customers', 'time', 'dashboard', 'growth' or ask AI with 'ai:' ...")
        self.search_input.setToolTip("Entrepreneur Quick Search: Try 'revenue', 'customers', 'pipeline', 'cash flow', 'kpi', 'growth' | AI mode: 'ai: your question' | 70+ business shortcuts available!")
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
            # Core Business Features
            ("📊 Business Dashboard", self.open_business_dashboard, "Business metrics & KPIs", "Ctrl+Shift+B"),
            ("🤝 CRM Manager", self.open_crm_manager, "Customer relationship management", "Ctrl+Shift+M"),
            ("💰 Finance Tracker", self.open_finance, "Track business finances", "Ctrl+Shift+F"),
            ("⏱️ Time Tracking", self.open_time_tracking, "Track billable hours", "Ctrl+Shift+T"),
            ("📈 KPI Tracker", self.open_kpi_tracker, "Track key performance indicators", "Ctrl+Shift+K"),
            ("📄 Report Generator", self.open_report_generator, "Generate business reports", "Ctrl+Shift+R"),
            
            # Essential Productivity Tools
            ("📧 Email", self.open_email, "Manage business communications", "Ctrl+E"),
            ("📝 Notes", self.open_notes, "Business notes and ideas", "Ctrl+N"),
            ("📅 Calendar", self.open_calendar, "Schedule meetings and appointments", "Ctrl+Shift+D"),
            ("✅ Todo", self.open_todo, "Track business tasks", "Ctrl+T"),
            ("👥 Contacts", self.open_contacts, "Manage business contacts", "Ctrl+Shift+O"),
            ("📁 Files", self.open_file_manager, "Organize business documents", "Ctrl+F"),
            
            # Core Tools
            ("🔐 Passwords", self.open_password_manager, "Secure business credentials", "Ctrl+P"),
            ("🧮 Calculator", self.open_calculator, "Business calculations", "Ctrl+Shift+C"),
            ("🌐 Browser", self.open_browser, "Research and web browsing", "Ctrl+B"),
            ("🖥️ Screen Intelligence", self.open_screen_intelligence, "Screen capture & analysis", "Ctrl+I"),
            
            # Tailor Pack System
            ("📦 Tailor Packs", self.open_tailor_pack_manager, "Manage business feature packs", "Ctrl+Alt+T"),
            ("📋 Templates", self.open_templates, "Business document templates", "Ctrl+J"),
            
            # Information & Tools
            ("🌤️ Weather", self.open_weather, "Weather for business travel", "Ctrl+W"),
            ("📰 News", self.open_news, "Business and industry news", "Ctrl+Shift+N"),
            
            # Advanced Features
            ("🎤 Voice Control", self.open_voice_control, "Voice commands for productivity", "Ctrl+V"),
            ("🛍️ Get More Packs", self.open_pack_marketplace, "Browse and download Tailor Packs", "Ctrl+X"),
            ("🌐 API Gateway", self.open_api_gateway, "Monitor business integrations", "Ctrl+G"),
            
            # Settings & Configuration
            ("⚙️ Settings", self.open_settings, "Configure business assistant", "Ctrl+,"),
        ]
        
        positions = [(i, j) for i in range(9) for j in range(3)]
        
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
        self.status_bar.showMessage("🚀 Your Entrepreneur Assistant is Ready | ⌨️ Ctrl+K: Quick Search | 🤖 Ctrl+Space: AI Assistant | 📦 Import Tailor Packs to extend functionality")
        
        # Add business status widgets to status bar
        self.init_business_status_bar()
        
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
        welcome = QLabel("Welcome to Westfall Assistant")
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
    
    def show_time_tracking(self):
        self.show_widget(TimeTrackingWidget, "Time Tracking")
    
    def show_recipes(self):
        self.show_widget(RecipeWidget, "Recipes")
    
    def show_settings(self):
        self.show_widget(SettingsWidget, "Settings")
    
    def show_business_dashboard(self):
        self.show_widget(BusinessDashboard, "Business Dashboard")
    
    def show_crm(self):
        self.show_widget(CRMManager, "CRM")
    
    def show_screen_intelligence(self):
        if ENHANCED_SCREEN_INTELLIGENCE:
            try:
                self.show_widget(ScreenIntelligenceWidget, "Enhanced Screen Intelligence")
            except ImportError:
                # Fallback to basic version
                from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
                self.show_widget(MultiMonitorCapture, "Screen Intelligence")
        else:
            try:
                from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
                self.show_widget(MultiMonitorCapture, "Screen Intelligence")
            except ImportError:
                QMessageBox.critical(self, "Module Not Found", 
                    "Screen Intelligence module not found.\n"
                    "Please ensure all dependencies are installed.")
    
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
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.open_time_tracking)
        
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
    
    def show_welcome_if_needed(self):
        """Show welcome experience for new users"""
        if ADVANCED_FEATURES_AVAILABLE:
            try:
                show_welcome_if_needed(self)
            except Exception as e:
                print(f"Error showing welcome experience: {e}")
    
    def init_tray(self):
        """Initialize system tray"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Westfall Assistant - Click to show/hide")
        
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
        """Show entrepreneur-focused help and tips"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("📚 Entrepreneur Assistant Help")
        help_dialog.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(help_dialog)
        
        # Create tab widget for different help sections
        tabs = QTabWidget()
        
        # Quick Start tab
        quick_start_tab = self.create_quick_start_help()
        tabs.addTab(quick_start_tab, "🚀 Quick Start")
        
        # Business Features tab
        business_tab = self.create_business_features_help()
        tabs.addTab(business_tab, "💼 Business Features")
        
        # Tailor Packs tab
        packs_tab = self.create_tailor_packs_help()
        tabs.addTab(packs_tab, "📦 Tailor Packs")
        
        # Keyboard Shortcuts tab
        shortcuts_tab = self.create_shortcuts_help()
        tabs.addTab(shortcuts_tab, "⌨️ Shortcuts")
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.exec_()
    
    def create_quick_start_help(self):
        """Create quick start help content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>🚀 Getting Started with Entrepreneur Assistant</h2>
        
        <h3>1. Set Up Your Business Profile</h3>
        <p>Go to <b>Settings → Business Profile</b> to configure your business information. This personalizes your experience and enables better AI insights.</p>
        
        <h3>2. Explore Core Business Features</h3>
        <ul>
            <li><b>📊 Business Dashboard</b> - Your central hub for KPIs and metrics</li>
            <li><b>🤝 CRM Manager</b> - Track customers and sales pipeline</li>
            <li><b>💰 Finance Tracker</b> - Monitor revenue, expenses, and profitability</li>
            <li><b>⏱️ Time Tracking</b> - Track billable hours and productivity</li>
        </ul>
        
        <h3>3. Install Tailor Packs</h3>
        <p>Use <b>📦 Tailor Packs</b> to extend functionality with industry-specific tools. Start with the Marketing Essentials pack.</p>
        
        <h3>4. Use Smart Search</h3>
        <p>Type keywords like 'revenue', 'customers', or 'time' in the search bar, or ask the AI with 'ai: [your question]'.</p>
        
        <h3>5. Get AI Help</h3>
        <p>Press <b>Ctrl+Space</b> or click the AI button to get intelligent assistance with business tasks and data analysis.</p>
        """)
        
        layout.addWidget(content)
        return widget
    
    def create_business_features_help(self):
        """Create business features help content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>💼 Business Features Guide</h2>
        
        <h3>📊 Business Dashboard</h3>
        <p>Your central command center for business metrics. Track revenue, growth, customer acquisition, and key performance indicators at a glance.</p>
        
        <h3>🤝 CRM Manager</h3>
        <p>Manage customer relationships, track sales pipeline, log interactions, and never miss a follow-up. Integrates with email for automatic contact tracking.</p>
        
        <h3>💰 Finance Tracker</h3>
        <p>Monitor cash flow, track expenses by category, manage invoices, and get profitability insights. Perfect for solo entrepreneurs and small businesses.</p>
        
        <h3>⏱️ Time Tracking</h3>
        <p>Track billable hours by project, client, or task. Generate timesheets, analyze productivity patterns, and optimize your schedule.</p>
        
        <h3>📈 KPI Tracker</h3>
        <p>Define and monitor key performance indicators specific to your business. Set targets and track progress toward your goals.</p>
        
        <h3>📄 Report Generator</h3>
        <p>Create professional business reports with charts and insights. Perfect for investor updates, performance reviews, and business planning.</p>
        
        <h3>🔐 Security Features</h3>
        <p>All your business data is encrypted and stored locally. Set up automatic backups and control access to sensitive information.</p>
        """)
        
        layout.addWidget(content)
        return widget
    
    def create_tailor_packs_help(self):
        """Create Tailor Packs help content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>📦 Tailor Packs System</h2>
        
        <h3>What are Tailor Packs?</h3>
        <p>Tailor Packs are specialized business functionality modules that extend your assistant with industry-specific tools and workflows.</p>
        
        <h3>Available Pack Categories</h3>
        <ul>
            <li><b>Marketing Packs</b> - Campaign tracking, social media management, lead generation</li>
            <li><b>Sales Packs</b> - Sales pipeline, proposal generation, customer onboarding</li>
            <li><b>Finance Packs</b> - Advanced accounting, tax preparation, financial planning</li>
            <li><b>Operations Packs</b> - Project management, team collaboration, workflow automation</li>
            <li><b>Industry Packs</b> - Specialized tools for specific industries (legal, medical, real estate, etc.)</li>
        </ul>
        
        <h3>Installing Packs</h3>
        <ol>
            <li>Click <b>📦 Tailor Packs</b> in the main menu</li>
            <li>Click <b>Import Pack</b> to install from a ZIP file</li>
            <li>Or browse the marketplace for available packs</li>
            <li>Enable/disable packs as needed</li>
        </ol>
        
        <h3>Trial Licenses</h3>
        <p>Most premium packs offer 30-day free trials. You can start a trial directly from the pack manager.</p>
        
        <h3>Creating Custom Packs</h3>
        <p>Developers can create custom Tailor Packs using our SDK. Contact support for development resources.</p>
        """)
        
        layout.addWidget(content)
        return widget
    
    def create_shortcuts_help(self):
        """Create keyboard shortcuts help content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>⌨️ Keyboard Shortcuts</h2>
        
        <h3>🚀 Quick Access</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><b>Ctrl+Space</b></td><td>Open AI Assistant</td></tr>
        <tr><td><b>Ctrl+K</b></td><td>Focus search bar</td></tr>
        <tr><td><b>Ctrl+Alt+T</b></td><td>Open Tailor Pack Manager</td></tr>
        <tr><td><b>F1</b></td><td>Show this help</td></tr>
        </table>
        
        <h3>💼 Business Features</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><b>Ctrl+Shift+B</b></td><td>Business Dashboard</td></tr>
        <tr><td><b>Ctrl+Shift+M</b></td><td>CRM Manager</td></tr>
        <tr><td><b>Ctrl+Shift+F</b></td><td>Finance Tracker</td></tr>
        <tr><td><b>Ctrl+Shift+T</b></td><td>Time Tracking</td></tr>
        <tr><td><b>Ctrl+Shift+K</b></td><td>KPI Tracker</td></tr>
        <tr><td><b>Ctrl+Shift+R</b></td><td>Report Generator</td></tr>
        </table>
        
        <h3>📝 Productivity</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><b>Ctrl+E</b></td><td>Email</td></tr>
        <tr><td><b>Ctrl+N</b></td><td>Notes</td></tr>
        <tr><td><b>Ctrl+T</b></td><td>Todo List</td></tr>
        <tr><td><b>Ctrl+Shift+D</b></td><td>Calendar</td></tr>
        <tr><td><b>Ctrl+Shift+O</b></td><td>Contacts</td></tr>
        </table>
        
        <h3>🔧 System</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Toggle dark mode</td></tr>
        <tr><td><b>F11</b></td><td>Toggle fullscreen</td></tr>
        </table>
        """)
        
        layout.addWidget(content)
        return widget
    
    def init_business_status_bar(self):
        """Initialize business-focused status bar widgets"""
        # Add permanent widgets to status bar
        
        # Tailor Packs status
        self.packs_status = QLabel("📦 Packs: Loading...")
        self.packs_status.setStyleSheet("color: #666; margin: 0 10px;")
        self.status_bar.addPermanentWidget(self.packs_status)
        
        # Business profile status
        self.profile_status = QLabel("👤 Profile: Not Set")
        self.profile_status.setStyleSheet("color: #666; margin: 0 10px;")
        self.status_bar.addPermanentWidget(self.profile_status)
        
        # Update status
        QTimer.singleShot(2000, self.update_business_status)
    
    def update_business_status(self):
        """Update business status indicators"""
        try:
            # Update Tailor Packs status
            if ADVANCED_FEATURES_AVAILABLE:
                pack_manager = get_tailor_pack_manager()
                active_packs = pack_manager.get_active_packs()
                self.packs_status.setText(f"📦 Packs: {len(active_packs)} active")
                
                if len(active_packs) == 0:
                    self.packs_status.setStyleSheet("color: #ff6600; margin: 0 10px;")
                    self.packs_status.setToolTip("No Tailor Packs active. Click to browse available packs.")
                    self.packs_status.mousePressEvent = lambda e: self.open_tailor_pack_manager()
                else:
                    self.packs_status.setStyleSheet("color: #4CAF50; margin: 0 10px;")
                    pack_names = [p.name for p in active_packs[:3]]
                    tooltip = "Active packs: " + ", ".join(pack_names)
                    if len(active_packs) > 3:
                        tooltip += f" (+{len(active_packs) - 3} more)"
                    self.packs_status.setToolTip(tooltip)
            
            # Update business profile status
            try:
                from utils.entrepreneur_config import get_entrepreneur_config
                config = get_entrepreneur_config()
                if config.business_profile.business_name:
                    business_name = config.business_profile.business_name
                    if len(business_name) > 15:
                        business_name = business_name[:12] + "..."
                    self.profile_status.setText(f"👤 {business_name}")
                    self.profile_status.setStyleSheet("color: #4CAF50; margin: 0 10px;")
                    self.profile_status.setToolTip(f"Business: {config.business_profile.business_name}\nType: {config.business_profile.business_type}")
                else:
                    self.profile_status.setText("👤 Profile: Not Set")
                    self.profile_status.setStyleSheet("color: #ff6600; margin: 0 10px;")
                    self.profile_status.setToolTip("Click to set up your business profile")
                    self.profile_status.mousePressEvent = lambda e: self.open_settings()
            except:
                pass
                
        except Exception as e:
            print(f"Error updating business status: {e}")
    
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
            # Send to AI with business context
            if not self.ai_chat.isVisible():
                self.ai_chat.show()
            
            # Add business context to AI queries
            business_query = self.enhance_ai_query(query.lstrip("ai:").lstrip("?").strip())
            self.ai_chat.input_field.setText(business_query)
            self.ai_chat.send_message()
            self.search_input.clear()
        else:
            # Enhanced business-focused search
            self.search_features(query)
    
    def enhance_ai_query(self, query):
        """Enhance AI queries with business context"""
        # Add business context for common entrepreneur queries
        business_enhancements = {
            "revenue": "Show me business revenue analysis and trends",
            "customers": "Help me analyze customer data and relationships",
            "marketing": "Provide marketing strategy and campaign insights",
            "productivity": "Suggest productivity improvements for my business",
            "growth": "Analyze business growth opportunities and metrics",
            "expenses": "Help me understand business expenses and cost optimization"
        }
        
        query_lower = query.lower()
        for keyword, enhancement in business_enhancements.items():
            if keyword in query_lower:
                return f"{enhancement}: {query}"
        
        # Add general business context
        return f"As an entrepreneur assistant, help with: {query}"
    
    def search_features(self, query):
        """Enhanced search with business shortcuts and suggestions"""
        query_lower = query.lower()
        
        # Business quick actions - comprehensive entrepreneur terminology
        business_shortcuts = {
            # Financial Terms
            "revenue": self.open_finance,
            "income": self.open_finance,
            "expenses": self.open_finance,
            "profit": self.open_finance,
            "finance": self.open_finance,
            "money": self.open_finance,
            "budget": self.open_finance,
            "cash flow": self.open_finance,
            "cashflow": self.open_finance,
            "accounting": self.open_finance,
            "taxes": self.open_finance,
            "invoices": self.open_finance,
            "billing": self.open_finance,
            
            # Customer & Sales Terms
            "customers": self.open_crm_manager,
            "crm": self.open_crm_manager,
            "leads": self.open_crm_manager,
            "sales": self.open_crm_manager,
            "clients": self.open_crm_manager,
            "prospects": self.open_crm_manager,
            "deals": self.open_crm_manager,
            "pipeline": self.open_crm_manager,
            "contacts": self.open_contacts,
            
            # Time & Productivity
            "time": self.open_time_tracking,
            "hours": self.open_time_tracking,
            "billable": self.open_time_tracking,
            "tracking": self.open_time_tracking,
            "schedule": self.open_calendar,
            "calendar": self.open_calendar,
            "appointments": self.open_calendar,
            "meetings": self.open_calendar,
            "tasks": self.open_todo,
            "todo": self.open_todo,
            "productivity": self.open_todo,
            
            # Analytics & Reporting
            "kpi": self.open_kpi_tracker,
            "metrics": self.open_business_dashboard,
            "dashboard": self.open_business_dashboard,
            "analytics": self.open_business_dashboard,
            "insights": self.open_business_dashboard,
            "reports": self.open_report_generator,
            "reporting": self.open_report_generator,
            "performance": self.open_kpi_tracker,
            
            # Business Growth & Strategy
            "growth": self.open_business_dashboard,
            "strategy": self.open_business_dashboard,
            "planning": self.open_business_dashboard,
            "goals": self.open_kpi_tracker,
            "targets": self.open_kpi_tracker,
            "roi": self.open_business_dashboard,
            "conversion": self.open_business_dashboard,
            
            # Extensions & Tools
            "packs": self.open_tailor_pack_manager,
            "extensions": self.open_tailor_pack_manager,
            "tools": self.open_tailor_pack_manager,
            "marketplace": self.open_pack_marketplace,
            "import": self.quick_import_pack,
            
            # Specialized Business Areas
            "marketing": lambda: self.show_marketing_suggestions(),
            "automation": lambda: self.show_automation_suggestions(),
            "email": self.open_email,
            "communication": self.open_email,
            "notes": self.open_notes,
            "documents": self.open_file_manager,
            "files": self.open_file_manager,
            "passwords": self.open_password_manager,
            "security": self.open_password_manager,
            "calculator": self.open_calculator,
            "calc": self.open_calculator,
            "math": self.open_calculator,
            "weather": self.open_weather,
            "news": self.open_news,
            "browser": self.open_browser,
            "web": self.open_browser
        }
        
        # Check business shortcuts first
        for keyword, action in business_shortcuts.items():
            if keyword in query_lower:
                action()
                self.search_input.clear()
                self.status_bar.showMessage(f"Opened {keyword} tools")
                return
        
        # Standard feature search
        for name, callback, _, _ in self.features:
            clean_name = name.split(' ', 1)[1].lower() if ' ' in name else name.lower()
            if query_lower in clean_name:
                callback()
                self.search_input.clear()
                self.status_bar.showMessage(f"Opened {name}")
                return
        
        # No match found - show suggestions
        self.show_search_suggestions(query)
    
    def show_marketing_suggestions(self):
        """Show marketing-related suggestions"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Marketing Tools")
        msg.setText("Marketing functionality is available through Tailor Packs!")
        msg.setInformativeText("Install the Marketing Essentials pack for campaign tracking, social media management, and lead generation tools.")
        
        install_btn = msg.addButton("Install Marketing Pack", QMessageBox.ActionRole)
        browse_btn = msg.addButton("Browse Packs", QMessageBox.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
        
        result = msg.exec_()
        
        if msg.clickedButton() == install_btn:
            self.open_tailor_pack_manager()
        elif msg.clickedButton() == browse_btn:
            self.open_marketplace()
    
    def show_automation_suggestions(self):
        """Show automation-related suggestions"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Automation Tools")
        msg.setText("Automation features are available through specialized Tailor Packs!")
        msg.setInformativeText("Install workflow packs for email automation, social media scheduling, and business process automation.")
        
        browse_btn = msg.addButton("Browse Automation Packs", QMessageBox.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
        
        result = msg.exec_()
        
        if msg.clickedButton() == browse_btn:
            self.open_tailor_pack_manager()
    
    def show_search_suggestions(self, query):
        """Show search suggestions when no direct match is found"""
        suggestions = [
            "💰 Financial: 'revenue', 'expenses', 'profit', 'cash flow', 'budget', 'invoices'",
            "👥 Customers: 'customers', 'crm', 'leads', 'sales', 'pipeline', 'deals'", 
            "⏱️ Time: 'time', 'hours', 'billable', 'schedule', 'calendar', 'meetings'",
            "📊 Analytics: 'dashboard', 'metrics', 'kpi', 'reports', 'performance', 'growth'",
            "🚀 Growth: 'strategy', 'planning', 'goals', 'targets', 'roi', 'conversion'",
            "📦 Tools: 'packs', 'import', 'marketing', 'automation', 'tools'",
            "🤖 AI Help: 'ai: [your business question]' for intelligent assistance"
        ]
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Entrepreneur Search Guide")
        msg.setText(f"No direct match found for '{query}'")
        msg.setInformativeText("Try these business-focused search terms:\n\n" + "\n".join(suggestions) + 
                              "\n\nOr browse the main grid for all available tools.")
        msg.exec_()
    
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
    
    def open_time_tracking(self):
        self.show_time_tracking()
    
    # New Business Intelligence window opening methods
    def open_screen_intelligence(self):
        if 'screen_intelligence' not in self.windows:
            if ENHANCED_SCREEN_INTELLIGENCE:
                self.windows['screen_intelligence'] = ScreenIntelligenceWidget()
            else:
                self.windows['screen_intelligence'] = MultiMonitorCapture()
        self.windows['screen_intelligence'].show()
        self.windows['screen_intelligence'].raise_()
        self.windows['screen_intelligence'].activateWindow()
        self.ai_chat.parent_window = self.windows['screen_intelligence']
        self.status_bar.showMessage("Screen Intelligence opened - AI-powered screen analysis")
    
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
    
    # Advanced Features Methods
    def open_voice_control(self):
        """Open voice control interface"""
        if ADVANCED_FEATURES_AVAILABLE:
            if 'voice_control' not in self.windows:
                self.windows['voice_control'] = VoiceControlWidget()
            self.windows['voice_control'].show()
            self.windows['voice_control'].raise_()
            self.windows['voice_control'].activateWindow()
        else:
            QMessageBox.information(self, "Advanced Features", 
                                  "Voice control requires additional dependencies.\n"
                                  "Please install: speech_recognition, pyttsx3")
    
    def open_pack_marketplace(self):
        """Open Tailor Pack Marketplace"""
        if ADVANCED_FEATURES_AVAILABLE:
            # For now, show a marketplace preview dialog with available pack categories
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTextEdit
            
            marketplace_dialog = QDialog(self)
            marketplace_dialog.setWindowTitle("Tailor Pack Marketplace")
            marketplace_dialog.setGeometry(300, 300, 600, 500)
            
            layout = QVBoxLayout(marketplace_dialog)
            
            # Header
            header = QLabel("🛍️ Tailor Pack Marketplace")
            header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; padding: 10px;")
            layout.addWidget(header)
            
            # Description
            desc = QLabel("Extend your entrepreneur assistant with specialized business functionality packs.")
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #666; padding: 5px 10px;")
            layout.addWidget(desc)
            
            # Pack categories
            categories_layout = QHBoxLayout()
            
            # Categories list
            categories_widget = QVBoxLayout()
            categories_label = QLabel("Pack Categories:")
            categories_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            categories_widget.addWidget(categories_label)
            
            categories_list = QListWidget()
            categories_list.setMaximumWidth(200)
            
            pack_categories = [
                "📊 Marketing Essentials",
                "💼 Sales & CRM",
                "💰 Advanced Finance",
                "📈 Analytics & BI", 
                "🤝 Team Collaboration",
                "🔧 Operations & PM",
                "⚖️ Legal & Compliance",
                "🏥 Healthcare/Medical",
                "🏠 Real Estate",
                "🛒 E-commerce",
                "🎓 Education/Training",
                "🔧 Developer Tools"
            ]
            
            for category in pack_categories:
                item = QListWidgetItem(category)
                categories_list.addItem(item)
            
            categories_widget.addWidget(categories_list)
            categories_layout.addLayout(categories_widget)
            
            # Pack details
            details_widget = QVBoxLayout()
            details_label = QLabel("Featured Packs:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            details_widget.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setHtml("""
            <h3>🚀 Coming Soon!</h3>
            <p>The Tailor Pack Marketplace is under development. Featured packs will include:</p>
            <ul>
                <li><b>Marketing Automation Pack</b> - Advanced campaign management, A/B testing, conversion tracking</li>
                <li><b>Sales Pipeline Pro</b> - Advanced CRM, proposal generation, contract management</li>
                <li><b>Financial Analytics Plus</b> - Advanced reporting, forecasting, budget optimization</li>
                <li><b>E-commerce Toolkit</b> - Inventory management, order processing, customer analytics</li>
                <li><b>Legal Assistant Pack</b> - Contract templates, compliance tracking, document automation</li>
            </ul>
            
            <h4>For Now:</h4>
            <p>• Use the <b>"Import Pack"</b> button to install pack files (.zip)</p>
            <p>• Check our website for available pack downloads</p>
            <p>• Contact support for custom pack development</p>
            
            <p><i>The marketplace will support one-click installation, automatic updates, and pack ratings when launched.</i></p>
            """)
            details_widget.addWidget(details_text)
            categories_layout.addLayout(details_widget)
            
            layout.addLayout(categories_layout)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            visit_website_btn = QPushButton("🌐 Visit Website")
            visit_website_btn.clicked.connect(lambda: self.open_url("https://westfallsoftwares.com/tailor-packs"))
            button_layout.addWidget(visit_website_btn)
            
            import_pack_btn = QPushButton("📦 Import Pack File")
            import_pack_btn.clicked.connect(lambda: (marketplace_dialog.close(), self.quick_import_pack()))
            button_layout.addWidget(import_pack_btn)
            
            button_layout.addStretch()
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(marketplace_dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            marketplace_dialog.exec_()
        else:
            QMessageBox.information(self, "Marketplace", 
                                  "Tailor Pack marketplace is not available.")
    
    def open_url(self, url):
        """Open URL in default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.information(self, "Browser", f"Could not open URL: {url}\n\nError: {str(e)}")
    
    def open_marketplace(self):
        """Legacy method - redirect to pack marketplace"""
        self.open_pack_marketplace()
    
    def open_tailor_pack_manager(self):
        """Open Tailor Pack Manager"""
        if ADVANCED_FEATURES_AVAILABLE:
            if 'tailor_packs' not in self.windows:
                self.windows['tailor_packs'] = TailorPackManagerWidget()
            self.windows['tailor_packs'].show()
            self.windows['tailor_packs'].raise_()
            self.windows['tailor_packs'].activateWindow()
        else:
            QMessageBox.information(self, "Tailor Packs", 
                                  "Tailor Pack management is not available.")
    
    def quick_import_pack(self):
        """Quick import of a Tailor Pack from the main interface"""
        if ADVANCED_FEATURES_AVAILABLE:
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Tailor Pack",
                "",
                "Tailor Pack Files (*.zip);;All Files (*.*)"
            )
            
            if file_path:
                # Show import progress
                self.status_bar.showMessage("Importing Tailor Pack...")
                
                from util.tailor_pack_manager import get_tailor_pack_manager
                manager = get_tailor_pack_manager()
                
                try:
                    result = manager.import_tailor_pack(file_path)
                    if result["success"]:
                        QMessageBox.information(
                            self, 
                            "Import Successful", 
                            f"Successfully imported Tailor Pack!\n\n{result['message']}\n\nThe pack is now available in the Tailor Pack Manager."
                        )
                        self.status_bar.showMessage("Tailor Pack imported successfully")
                        self.update_business_status_bar()  # Refresh pack status
                    else:
                        QMessageBox.warning(
                            self,
                            "Import Failed",
                            f"Failed to import Tailor Pack:\n\n{result['error']}"
                        )
                        self.status_bar.showMessage("Tailor Pack import failed")
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Import Error",
                        f"An error occurred while importing the Tailor Pack:\n\n{str(e)}"
                    )
                    self.status_bar.showMessage("Tailor Pack import error")
        else:
            QMessageBox.information(self, "Tailor Packs", 
                                  "Tailor Pack import is not available.\n\nPlease ensure all dependencies are installed.")
    
    def open_templates(self):
        """Open template exchange"""
        if ADVANCED_FEATURES_AVAILABLE:
            if 'templates' not in self.windows:
                self.windows['templates'] = TemplateWidget()
            self.windows['templates'].show()
            self.windows['templates'].raise_()
            self.windows['templates'].activateWindow()
        else:
            QMessageBox.information(self, "Advanced Features", 
                                  "Template exchange is not available.")
    
    def open_api_gateway(self):
        """Open API gateway monitor"""
        if ADVANCED_FEATURES_AVAILABLE:
            if 'api_gateway' not in self.windows:
                self.windows['api_gateway'] = APIGatewayWidget()
            self.windows['api_gateway'].show()
            self.windows['api_gateway'].raise_()
            self.windows['api_gateway'].activateWindow()
        else:
            QMessageBox.information(self, "Advanced Features", 
                                  "API gateway monitoring is not available.")
        self.ai_chat.parent_window = self.windows['crm_manager']
        self.status_bar.showMessage("CRM Manager opened - Manage customer relationships & sales pipeline")
    
    def check_dependencies(self):
        """Check for missing dependencies"""
        if DEPENDENCY_MANAGER_AVAILABLE:
            # Quick check for missing dependencies
            manager = DependencyManager()
            result = manager.check_dependencies()
            missing = result["missing"]
            outdated = result["outdated"]
            
            if missing or outdated:
                message = "Some dependencies need attention:\n\n"
                
                if missing:
                    message += f"- {len(missing)} missing packages\n"
                if outdated:
                    message += f"- {len(outdated)} outdated packages\n"
                
                message += "\nWould you like to open the Dependency Manager?"
                
                reply = QMessageBox.question(self, "Dependencies", message, 
                                            QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    dialog = DependencyManagerDialog(self)
                    dialog.exec_()
            else:
                QMessageBox.information(self, "Dependencies", 
                                      "All dependencies are installed and up to date!")
        else:
            QMessageBox.warning(self, "Not Available", 
                              "Dependency manager is not available.\n"
                              "Please check your installation.")
    
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


# Advanced Features Widget Classes
class VoiceControlWidget(QWidget):
    """Widget for voice control interface"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Control System")
        self.setFixedSize(800, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎤 Voice Control System")
        title.setStyleSheet("font-size: 24px; color: #ff0000; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not ADVANCED_FEATURES_AVAILABLE:
            error_label = QLabel("Advanced features not available. Please install required dependencies.")
            error_label.setStyleSheet("color: #ff6666; font-size: 16px; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            self.setLayout(layout)
            return
            
        # Get voice manager
        try:
            from utils.voice_control import get_voice_manager
            self.voice_manager = get_voice_manager()
            
            # Status display
            status_group = QGroupBox("Voice Control Status")
            status_layout = QVBoxLayout()
            
            self.status_label = QLabel("Initializing...")
            status_layout.addWidget(self.status_label)
            
            # Control buttons
            button_layout = QHBoxLayout()
            
            self.enable_btn = QPushButton("Enable Voice Control")
            self.enable_btn.clicked.connect(self.toggle_voice_control)
            button_layout.addWidget(self.enable_btn)
            
            self.listening_btn = QPushButton("Start Listening")
            self.listening_btn.clicked.connect(self.toggle_listening)
            button_layout.addWidget(self.listening_btn)
            
            status_layout.addLayout(button_layout)
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            # Available commands
            commands_group = QGroupBox("Available Voice Commands")
            commands_layout = QVBoxLayout()
            
            commands_list = QListWidget()
            for command in self.voice_manager.get_available_commands():
                commands_list.addItem(command)
            commands_layout.addWidget(commands_list)
            
            commands_group.setLayout(commands_layout)
            layout.addWidget(commands_group)
            
            # Update status
            self.update_status()
            
            # Timer for status updates
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_status)
            self.timer.start(1000)  # Update every second
            
        except Exception as e:
            error_label = QLabel(f"Error initializing voice control: {str(e)}")
            error_label.setStyleSheet("color: #ff6666; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
        
        self.setLayout(layout)
        
    def toggle_voice_control(self):
        """Toggle voice control on/off"""
        if self.voice_manager.enabled:
            self.voice_manager.disable_voice_control()
            self.enable_btn.setText("Enable Voice Control")
        else:
            if self.voice_manager.enable_voice_control():
                self.enable_btn.setText("Disable Voice Control")
            else:
                QMessageBox.warning(self, "Voice Control", 
                                  "Failed to enable voice control. Check if microphone is available.")
        
    def toggle_listening(self):
        """Toggle listening on/off"""
        if self.voice_manager.listening:
            self.voice_manager.stop_listening()
            self.listening_btn.setText("Start Listening")
        else:
            if self.voice_manager.start_listening():
                self.listening_btn.setText("Stop Listening")
            else:
                QMessageBox.warning(self, "Voice Control", 
                                  "Failed to start listening. Voice control must be enabled first.")
        
    def update_status(self):
        """Update status display"""
        status = self.voice_manager.get_status()
        status_text = f"""
Enabled: {'Yes' if status['enabled'] else 'No'}
Listening: {'Yes' if status['listening'] else 'No'}
Speech Recognition: {'Available' if status['sr_available'] else 'Not Available'}
Text-to-Speech: {'Available' if status['tts_available'] else 'Not Available'}
Command Queue: {status['queue_size']} commands
"""
        self.status_label.setText(status_text)


class MarketplaceWidget(QWidget):
    """Widget for extension marketplace"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extension Marketplace")
        self.setFixedSize(1000, 700)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🛍️ Extension Marketplace")
        title.setStyleSheet("font-size: 24px; color: #ff0000; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not ADVANCED_FEATURES_AVAILABLE:
            error_label = QLabel("Advanced features not available.")
            error_label.setStyleSheet("color: #ff6666; font-size: 16px; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            self.setLayout(layout)
            return
            
        try:
            from utils.marketplace_manager import get_marketplace_manager
            self.marketplace = get_marketplace_manager()
            
            # Search bar
            search_layout = QHBoxLayout()
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search extensions...")
            search_btn = QPushButton("Search")
            search_btn.clicked.connect(self.search_extensions)
            
            search_layout.addWidget(self.search_input)
            search_layout.addWidget(search_btn)
            layout.addLayout(search_layout)
            
            # Extensions list
            self.extensions_list = QListWidget()
            layout.addWidget(self.extensions_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            install_btn = QPushButton("Install Selected")
            install_btn.clicked.connect(self.install_extension)
            button_layout.addWidget(install_btn)
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_marketplace)
            button_layout.addWidget(refresh_btn)
            
            layout.addLayout(button_layout)
            
            # Load initial data
            self.refresh_marketplace()
            
        except Exception as e:
            error_label = QLabel(f"Error initializing marketplace: {str(e)}")
            error_label.setStyleSheet("color: #ff6666; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
        
        self.setLayout(layout)
        
    def search_extensions(self):
        """Search for extensions"""
        query = self.search_input.text()
        extensions = self.marketplace.search_marketplace(query=query)
        self.update_extensions_list(extensions)
        
    def refresh_marketplace(self):
        """Refresh marketplace data"""
        extensions = self.marketplace.search_marketplace()
        self.update_extensions_list(extensions)
        
    def update_extensions_list(self, extensions):
        """Update the extensions list widget"""
        self.extensions_list.clear()
        for ext in extensions:
            item_text = f"{ext.name} v{ext.version} - {ext.description} (⭐ {ext.rating:.1f})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ext.id)
            self.extensions_list.addItem(item)
            
    def install_extension(self):
        """Install selected extension"""
        current_item = self.extensions_list.currentItem()
        if current_item:
            extension_id = current_item.data(Qt.UserRole)
            
            # Create progress dialog
            progress = QProgressDialog("Installing extension...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            
            def update_progress(message, percent):
                progress.setLabelText(message)
                progress.setValue(int(percent * 100))
                QApplication.processEvents()
                
            success = self.marketplace.install_extension(extension_id, update_progress)
            progress.close()
            
            if success:
                QMessageBox.information(self, "Installation", "Extension installed successfully!")
            else:
                QMessageBox.warning(self, "Installation", "Failed to install extension.")


class TemplateWidget(QWidget):
    """Widget for template exchange"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Template Exchange")
        self.setFixedSize(1000, 700)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📋 Template Exchange")
        title.setStyleSheet("font-size: 24px; color: #ff0000; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not ADVANCED_FEATURES_AVAILABLE:
            error_label = QLabel("Advanced features not available.")
            error_label.setStyleSheet("color: #ff6666; font-size: 16px; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            self.setLayout(layout)
            return
            
        try:
            from utils.template_exchange import get_template_manager
            self.template_manager = get_template_manager()
            
            # Toolbar
            toolbar_layout = QHBoxLayout()
            
            new_btn = QPushButton("New Template")
            new_btn.clicked.connect(self.create_template)
            toolbar_layout.addWidget(new_btn)
            
            import_btn = QPushButton("Import")
            import_btn.clicked.connect(self.import_template)
            toolbar_layout.addWidget(import_btn)
            
            export_btn = QPushButton("Export")
            export_btn.clicked.connect(self.export_template)
            toolbar_layout.addWidget(export_btn)
            
            toolbar_layout.addStretch()
            layout.addLayout(toolbar_layout)
            
            # Templates list
            self.templates_list = QListWidget()
            layout.addWidget(self.templates_list)
            
            # Template details
            details_group = QGroupBox("Template Details")
            details_layout = QVBoxLayout()
            
            self.details_label = QLabel("Select a template to view details")
            details_layout.addWidget(self.details_label)
            
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)
            
            # Load templates
            self.refresh_templates()
            
            # Connect selection
            self.templates_list.itemSelectionChanged.connect(self.on_template_selected)
            
        except Exception as e:
            error_label = QLabel(f"Error initializing templates: {str(e)}")
            error_label.setStyleSheet("color: #ff6666; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
        
        self.setLayout(layout)
        
    def refresh_templates(self):
        """Refresh templates list"""
        self.templates_list.clear()
        for template_id, template_info in self.template_manager.local_templates.items():
            item_text = f"{template_info.name} ({template_info.category})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, template_id)
            self.templates_list.addItem(item)
            
    def on_template_selected(self):
        """Handle template selection"""
        current_item = self.templates_list.currentItem()
        if current_item:
            template_id = current_item.data(Qt.UserRole)
            template_info = self.template_manager.get_template(template_id)
            if template_info:
                details = f"""
Name: {template_info.name}
Category: {template_info.category}
Author: {template_info.author}
Version: {template_info.version}
Created: {template_info.created_date.strftime('%Y-%m-%d %H:%M')}
Variables: {len(template_info.variables)}
Tags: {', '.join(template_info.tags)}

Description:
{template_info.description}
"""
                self.details_label.setText(details)
                
    def create_template(self):
        """Create new template dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Template")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Template info
        name_input = QLineEdit()
        name_input.setPlaceholderText("Template name")
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        
        category_combo = QComboBox()
        category_combo.addItems(["business", "operations", "legal", "marketing", "technical"])
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(category_combo)
        
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Template description")
        desc_input.setMaximumHeight(80)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(desc_input)
        
        content_input = QTextEdit()
        content_input.setPlaceholderText("Template content with {{variables}}")
        layout.addWidget(QLabel("Content:"))
        layout.addWidget(content_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        
        def create_template():
            name = name_input.text().strip()
            if name:
                template_id = self.template_manager.create_template(
                    name=name,
                    category=category_combo.currentText(),
                    content=content_input.toPlainText(),
                    description=desc_input.toPlainText()
                )
                dialog.accept()
                self.refresh_templates()
                QMessageBox.information(self, "Success", f"Template '{name}' created successfully!")
            else:
                QMessageBox.warning(dialog, "Error", "Please enter a template name.")
                
        create_btn.clicked.connect(create_template)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def import_template(self):
        """Import template from file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Template", "", "ZIP Files (*.zip)")
        if file_path:
            template_id = self.template_manager.import_template(file_path)
            if template_id:
                self.refresh_templates()
                QMessageBox.information(self, "Success", "Template imported successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to import template.")
                
    def export_template(self):
        """Export selected template"""
        current_item = self.templates_list.currentItem()
        if current_item:
            template_id = current_item.data(Qt.UserRole)
            file_path, _ = QFileDialog.getSaveFileName(self, "Export Template", f"{template_id}.zip", "ZIP Files (*.zip)")
            if file_path:
                exported_path = self.template_manager.export_template(template_id, file_path)
                if exported_path:
                    QMessageBox.information(self, "Success", f"Template exported to {exported_path}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export template.")
        else:
            QMessageBox.information(self, "Export", "Please select a template to export.")


class APIGatewayWidget(QWidget):
    """Widget for API gateway monitoring"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Gateway Monitor")
        self.setFixedSize(1000, 700)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🌐 API Gateway Monitor")
        title.setStyleSheet("font-size: 24px; color: #ff0000; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not ADVANCED_FEATURES_AVAILABLE:
            error_label = QLabel("Advanced features not available.")
            error_label.setStyleSheet("color: #ff6666; font-size: 16px; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            self.setLayout(layout)
            return
            
        try:
            from utils.api_gateway import get_api_gateway
            self.gateway = get_api_gateway()
            
            # Status overview
            status_group = QGroupBox("Gateway Status")
            status_layout = QVBoxLayout()
            
            self.status_text = QLabel("Loading...")
            status_layout.addWidget(self.status_text)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            # Services health
            services_group = QGroupBox("Services Health")
            services_layout = QVBoxLayout()
            
            self.services_list = QListWidget()
            services_layout.addWidget(self.services_list)
            
            services_group.setLayout(services_layout)
            layout.addWidget(services_group)
            
            # API Keys
            keys_group = QGroupBox("API Keys")
            keys_layout = QVBoxLayout()
            
            self.keys_list = QListWidget()
            keys_layout.addWidget(self.keys_list)
            
            # Key management buttons
            key_buttons = QHBoxLayout()
            create_key_btn = QPushButton("Create API Key")
            create_key_btn.clicked.connect(self.create_api_key)
            key_buttons.addWidget(create_key_btn)
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_data)
            key_buttons.addWidget(refresh_btn)
            
            keys_layout.addLayout(key_buttons)
            keys_group.setLayout(keys_layout)
            layout.addWidget(keys_group)
            
            # Initial data load
            self.refresh_data()
            
            # Auto-refresh timer
            self.timer = QTimer()
            self.timer.timeout.connect(self.refresh_data)
            self.timer.start(5000)  # Refresh every 5 seconds
            
        except Exception as e:
            error_label = QLabel(f"Error initializing API gateway: {str(e)}")
            error_label.setStyleSheet("color: #ff6666; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
        
        self.setLayout(layout)
        
    def refresh_data(self):
        """Refresh all gateway data"""
        # Update status
        status = self.gateway.get_gateway_status()
        status_text = f"""
Gateway Version: {status['gateway_version']}
Active API Keys: {status['active_api_keys']}/{status['total_api_keys']}
Total Requests: {status['total_requests']}
Last Updated: {status['timestamp'][:19]}
"""
        self.status_text.setText(status_text)
        
        # Update services
        self.services_list.clear()
        for service_name, service_status in status['services'].items():
            status_icon = "🟢" if service_status['status'] == "healthy" else "🔴"
            item_text = f"{status_icon} {service_name} - {service_status['status']}"
            self.services_list.addItem(item_text)
            
        # Update API keys
        self.keys_list.clear()
        for key_id, api_key in self.gateway.api_keys.items():
            status_icon = "🟢" if api_key.is_active else "🔴"
            item_text = f"{status_icon} {api_key.name} ({api_key.service}) - Used: {api_key.usage_count}"
            self.keys_list.addItem(item_text)
            
    def create_api_key(self):
        """Create new API key dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create API Key")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("API Key name")
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        
        service_combo = QComboBox()
        service_combo.addItems(["openai", "weather", "news", "email"])
        layout.addWidget(QLabel("Service:"))
        layout.addWidget(service_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        
        def create_key():
            name = name_input.text().strip()
            service = service_combo.currentText()
            if name:
                api_key = self.gateway.create_api_key(service, name)
                dialog.accept()
                self.refresh_data()
                QMessageBox.information(self, "Success", 
                                      f"API Key created successfully!\nKey ID: {api_key.key_id}")
            else:
                QMessageBox.warning(dialog, "Error", "Please enter a key name.")
                
        create_btn.clicked.connect(create_key)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Westfall Assistant")
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