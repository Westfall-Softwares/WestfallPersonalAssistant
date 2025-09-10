#!/usr/bin/env python3
"""
SIMPLIFIED Westfall Personal Assistant - ONE WINDOW ONLY
Red/black theme, password first, simple tabs
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                           QHBoxLayout, QWidget, QLabel, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import authentication
from backend.security.auth_manager import AuthManager
from security.encryption_manager import MasterPasswordDialog

class SimpleWestfallWindow(QMainWindow):
    """ONE SIMPLE WINDOW - No complications"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Westfall Personal Assistant")
        self.setGeometry(200, 200, 1000, 700)
        
        # Apply RED/BLACK theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #ff0000;
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #ff0000;
            }
            QTabBar::tab:selected {
                background-color: #ff0000;
                color: #ffffff;
                font-weight: bold;
            }
            QLabel {
                color: #ffffff;
                background-color: #000000;
            }
            QPushButton {
                background-color: #ff0000;
                color: #ffffff;
                border: 1px solid #ff0000;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #ff0000;
            }
        """)
        
        # Create simple tab interface
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add simple tabs
        self.add_dashboard_tab()
        self.add_chat_tab()
        self.add_settings_tab()
        
    def add_dashboard_tab(self):
        """Simple dashboard"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("📊 BUSINESS DASHBOARD")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QLabel("Welcome to your business dashboard")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        self.tabs.addTab(widget, "📊 Dashboard")
        
    def add_chat_tab(self):
        """Simple chat"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("💬 AI CHAT")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        chat_area = QTextEdit()
        chat_area.setPlainText("AI Chat will be here...")
        layout.addWidget(chat_area)
        
        self.tabs.addTab(widget, "💬 Chat")
        
    def add_settings_tab(self):
        """Simple settings"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("⚙️ SETTINGS")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QLabel("Settings will be here...")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        self.tabs.addTab(widget, "⚙️ Settings")


def main():
    """SIMPLE main function"""
    app = QApplication(sys.argv)
    
    # AUTHENTICATION FIRST
    auth_manager = AuthManager()
    
    if not auth_manager.has_master_password():
        # First time setup
        dialog = MasterPasswordDialog(first_time=True)
        if not (dialog.exec_() and dialog.password and auth_manager.set_master_password(dialog.password)):
            print("Authentication setup failed")
            sys.exit(0)
    else:
        # Login
        dialog = MasterPasswordDialog(first_time=False)
        if not (dialog.exec_() and dialog.password and auth_manager.verify_master_password(dialog.password)):
            print("Authentication failed")
            sys.exit(0)
    
    # ONE SIMPLE WINDOW
    window = SimpleWestfallWindow()
    window.show()
    
    print("Westfall Assistant started - ONE WINDOW, RED/BLACK THEME")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
