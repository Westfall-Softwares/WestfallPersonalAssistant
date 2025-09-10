#!/usr/bin/env python3
"""
Westfall Personal Assistant - Main Application Entry Point

Original PyQt5-based desktop application with authentication, red/black theme,
and tab-based interface with persistent chat functionality.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                           QHBoxLayout, QWidget, QSplitter, QSystemTrayIcon, 
                           QMenu, QAction, QMessageBox, QStatusBar, QMenuBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

# Import existing components
from utils.app_theme import AppTheme
from backend.security.auth_manager import AuthManager
from security.encryption_manager import MasterPasswordDialog
from core.assistant import get_assistant_core
from ai_assistant.core.chat_manager import AIChatWidget
from business_intelligence.dashboard.business_dashboard import BusinessDashboard
from crm_system.crm_manager import CRMManager
from utils.entrepreneur_config import SettingsWindow
from utils.welcome_experience import show_welcome_if_needed

# Import existing components
from backend.services.tools.music_player import MusicPlayerWindow as MusicPlayer
# TODO: Create proper PyQt5 widgets for these components:
# from utils.file_handler import FileHandler as FileManager  # This is just utilities, not a widget
# from core.task_manager import TaskManager as TaskManagerUI  # This is a data model, not a widget

logger = logging.getLogger(__name__)

# Optional dotenv support so devs can set WESTFALL_DEV in a .env file
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    def load_dotenv(*_args, **_kwargs):  # fallback no-op
        return False


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class WestfallMainWindow(QMainWindow):
    """Main application window with tab-based interface and persistent chat"""
    
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.assistant_core = None
        self.chat_widget = None
        self.tray_icon = None
        
        # Initialize UI
        self.init_ui()
        self.setup_system_tray()
        self.setup_auto_lock()
        
        # Initialize assistant core
        self.init_assistant()
        
    def init_ui(self):
        """Initialize the main user interface with red/black theme"""
        self.setWindowTitle("Westfall Personal Assistant")
        self.setGeometry(100, 100, 1200, 800)  # Smaller default size
        self.setMinimumSize(800, 600)  # Set minimum size to prevent compression
        
        # Apply red/black theme
        self.apply_theme()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter for main content and chat
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create tab widget for main content
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.setup_tabs()
        splitter.addWidget(self.tabs)
        
        # Create persistent chat widget
        self.chat_widget = AIChatWidget()
        self.chat_widget.setMaximumWidth(350)  # Slightly smaller
        self.chat_widget.setMinimumWidth(300)
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions (main content 75%, chat 25%)
        splitter.setSizes([900, 300])
        splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def apply_theme(self):
        """Apply the original red/black theme"""
        # Apply theme to entire application first
        AppTheme.apply_to_application()
        
        # Then apply additional specific styling to main window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QTabWidget::pane {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                background-color: {AppTheme.SECONDARY_BG};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTabBar::tab {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_MEDIUM}px {AppTheme.PADDING_LARGE}px;
                margin-right: 2px;
                border-radius: {AppTheme.BORDER_RADIUS}px {AppTheme.BORDER_RADIUS}px 0px 0px;
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
            }}
            QTabBar::tab:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: {AppTheme.HIGHLIGHT_COLOR};
            }}
            QStatusBar {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border-top: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
            }}
            QMenuBar {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border-bottom: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: {AppTheme.PADDING_SMALL}px {AppTheme.PADDING_MEDIUM}px;
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QMenuBar::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QMenu {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
            }}
            QMenu::item {{
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_SMALL}px {AppTheme.PADDING_MEDIUM}px;
            }}
            QMenu::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
        """)
        
    def setup_tabs(self):
        """Setup all application tabs"""
        # Business Dashboard
        try:
            self.business_dashboard = BusinessDashboard()
            self.tabs.addTab(self.business_dashboard, "📊 Dashboard")
        except Exception as e:
            logger.error(f"Failed to load Business Dashboard: {e}")
            
        # CRM Manager
        try:
            self.crm_manager = CRMManager()
            self.tabs.addTab(self.crm_manager, "🤝 CRM")
        except Exception as e:
            logger.error(f"Failed to load CRM Manager: {e}")
            
        # Email Manager - TODO: implement email functionality
        # try:
        #     self.email_manager = EmailManager()
        #     self.tabs.addTab(self.email_manager, "📧 Email")
        # except Exception as e:
        #     logger.error(f"Failed to load Email Manager: {e}")
            
        # Task Manager - TODO: Create PyQt5 widget for task management
        # try:
        #     self.task_manager = TaskManagerUI()
        #     self.tabs.addTab(self.task_manager, "✅ Tasks")
        # except Exception as e:
        #     logger.error(f"Failed to load Task Manager: {e}")
            
        # Calendar - TODO: implement calendar functionality
        # try:
        #     self.calendar_manager = CalendarManager()
        #     self.tabs.addTab(self.calendar_manager, "📅 Calendar")
        # except Exception as e:
        #     logger.error(f"Failed to load Calendar: {e}")
            
        # Notes - TODO: implement notes functionality
        # try:
        #     self.notes_manager = NotesManager()
        #     self.tabs.addTab(self.notes_manager, "📝 Notes")
        # except Exception as e:
        #     logger.error(f"Failed to load Notes Manager: {e}")
            
        # File Manager - TODO: Create PyQt5 widget for file management
        # try:
        #     self.file_manager = FileManager()
        #     self.tabs.addTab(self.file_manager, "📁 Files")
        # except Exception as e:
        #     logger.error(f"Failed to load File Manager: {e}")
            
        # Music Player
        try:
            self.music_player = MusicPlayer()
            self.tabs.addTab(self.music_player, "🎵 Music")
        except Exception as e:
            logger.error(f"Failed to load Music Player: {e}")
            
        # Settings (always last)
        try:
            self.settings_window = SettingsWindow()
            self.tabs.addTab(self.settings_window, "⚙️ Settings")
        except Exception as e:
            logger.error(f"Failed to load Settings: {e}")
            
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Conversation', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_conversation)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open...', self)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu('View')
        
        toggle_chat = QAction('Toggle Chat Panel', self)
        toggle_chat.setShortcut('Ctrl+T')
        toggle_chat.triggered.connect(self.toggle_chat_panel)
        view_menu.addAction(toggle_chat)
        
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        
        lock_action = QAction('Lock Application', self)
        lock_action.setShortcut('Ctrl+L')
        lock_action.triggered.connect(self.lock_application)
        tools_menu.addAction(lock_action)
        
        backup_action = QAction('Backup Data', self)
        backup_action.triggered.connect(self.backup_data)
        tools_menu.addAction(backup_action)
        
        # Help Menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
    def setup_auto_lock(self):
        """Setup automatic locking timer"""
        self.auto_lock_timer = QTimer()
        self.auto_lock_timer.timeout.connect(self.check_auto_lock)
        self.auto_lock_timer.start(60000)  # Check every minute
        
    def init_assistant(self):
        """Initialize the assistant core"""
        try:
            self.assistant_core = get_assistant_core()
            if self.assistant_core:
                self.assistant_core.initialize()
                self.status_bar.showMessage("Assistant initialized")
            else:
                self.status_bar.showMessage("Assistant core not available")
        except Exception as e:
            logger.error(f"Failed to initialize assistant: {e}")
            self.status_bar.showMessage(f"Assistant error: {e}")
            
    def new_conversation(self):
        """Start a new conversation"""
        if self.chat_widget:
            self.chat_widget.clear_conversation()
            
    def toggle_chat_panel(self):
        """Toggle the chat panel visibility"""
        if self.chat_widget:
            self.chat_widget.setVisible(not self.chat_widget.isVisible())
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def lock_application(self):
        """Lock the application"""
        self.auth_manager.logout()
        self.hide()
        # Show login dialog again
        if self.authenticate():
            self.show()
        else:
            QApplication.quit()
            
    def backup_data(self):
        """Backup application data"""
        QMessageBox.information(self, "Backup", "Data backup functionality will be implemented.")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Westfall Personal Assistant", 
                         "Westfall Personal Assistant\n"
                         "AI-powered business companion with Tailor Pack support\n\n"
                         "Version: 1.0.0\n"
                         "© 2025 Westfall Software")
        
    def check_auto_lock(self):
        """Check if application should auto-lock"""
        if not self.auth_manager.is_session_valid():
            self.lock_application()
            
    def closeEvent(self, event):
        """Handle application close event"""
        if self.tray_icon and self.tray_icon.isVisible():
            QMessageBox.information(self, "Westfall Assistant",
                                  "Application will keep running in the system tray. "
                                  "To terminate completely, choose Quit from the context menu.")
            self.hide()
            event.ignore()
        else:
            # Save any pending data
            if self.assistant_core:
                # Save conversation history, etc.
                pass
            event.accept()


class WestfallApplication(QApplication):
    """Main application class with initialization"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Westfall Personal Assistant")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Westfall Software")
        
        # Set application icon
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup application logging"""
        log_dir = Path.home() / ".westfall_assistant" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "westfall.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )


def main():
    """Main application entry point"""
    # Load .env early so WESTFALL_DEV is available
    try:
        load_dotenv()
    except Exception:
        pass

    app = WestfallApplication(sys.argv)
    
    # Prevent multiple instances
    if app.applicationPid() != os.getpid():
        logger.error("Another instance is already running")
        sys.exit(1)
    
    # Handle authentication FIRST before creating any windows, unless in dev
    dev_mode = _is_truthy(os.environ.get("WESTFALL_DEV", ""))
    if not dev_mode:
        auth_manager = AuthManager()
        if not auth_manager.has_master_password():
            # First time setup
            dialog = MasterPasswordDialog(first_time=True)
            if not (dialog.exec_() and dialog.password and auth_manager.set_master_password(dialog.password)):
                logger.info("Authentication setup failed or cancelled")
                sys.exit(0)
        else:
            # Existing user login
            dialog = MasterPasswordDialog(first_time=False)
            if not (dialog.exec_() and dialog.password and auth_manager.verify_master_password(dialog.password)):
                logger.info("Authentication failed or cancelled")
                sys.exit(0)
    else:
        logger.info("WESTFALL_DEV is set - bypassing authentication for development.")
    
    # Only create main window AFTER successful authentication
    window = WestfallMainWindow()
    
    # Skip welcome screen for now - just show main window
    # show_welcome_if_needed(window)
    
    # Show main window
    window.show()
    
    logger.info("Westfall Personal Assistant started successfully")
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
