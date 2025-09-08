"""
Welcome Screen and Onboarding for Entrepreneur Assistant
Provides first-run experience and quick tour of features
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPixmap, QPainter, QLinearGradient, QColor, QPen


class WelcomeScreen(QDialog):
    """Welcome screen for new users"""
    
    tour_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Welcome to Entrepreneur Assistant")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Icon area (placeholder)
        logo_label = QLabel("🚀")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 64px; margin: 20px;")
        layout.addWidget(logo_label)
        
        # Welcome title
        title = QLabel("Welcome to Entrepreneur Assistant")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; margin: 10px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Your AI-powered business companion with Tailor Pack support")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.9); margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Feature highlights
        features_widget = QWidget()
        features_layout = QVBoxLayout(features_widget)
        features_layout.setSpacing(15)
        
        features = [
            ("📊", "Business Dashboard", "Track KPIs, revenue, and growth metrics"),
            ("🤝", "CRM Integration", "Manage customers and sales pipeline"),
            ("📦", "Tailor Packs", "Extend functionality with business-specific features"),
            ("🔒", "Secure & Private", "Your business data stays local and encrypted"),
            ("⚡", "AI-Powered", "Get intelligent insights and automation")
        ]
        
        for icon, title, description in features:
            feature_widget = self.create_feature_widget(icon, title, description)
            features_layout.addWidget(feature_widget)
        
        layout.addWidget(features_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Quick setup button
        setup_btn = QPushButton("🚀 Quick Setup")
        setup_btn.setFont(QFont("Arial", 12, QFont.Bold))
        setup_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.9);
                color: #333;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        setup_btn.clicked.connect(self.start_setup)
        button_layout.addWidget(setup_btn)
        
        # Take tour button
        tour_btn = QPushButton("👁 Take Tour")
        tour_btn.setFont(QFont("Arial", 12))
        tour_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.5);
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
                border-color: white;
            }
        """)
        tour_btn.clicked.connect(self.start_tour)
        button_layout.addWidget(tour_btn)
        
        # Skip button
        skip_btn = QPushButton("Skip")
        skip_btn.setFont(QFont("Arial", 10))
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255,255,255,0.7);
                border: none;
                padding: 8px 16px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
    
    def create_feature_widget(self, icon, title, description):
        """Create a feature highlight widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        icon_label.setFixedWidth(40)
        layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: rgba(255,255,255,0.8);")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return widget
    
    def start_setup(self):
        """Start the quick setup process"""
        self.accept()
        # The main application will handle showing the setup wizard
    
    def start_tour(self):
        """Start the application tour"""
        self.tour_requested.emit()
        self.accept()


class QuickTour(QDialog):
    """Interactive tour of application features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 0
        self.steps = [
            {
                "title": "Business Dashboard",
                "description": "Your central hub for tracking business metrics, KPIs, and performance indicators. Get insights at a glance.",
                "tip": "💡 Tip: Pin your most important metrics to the top for quick access."
            },
            {
                "title": "Tailor Packs",
                "description": "Extend your assistant with specialized business functionality. Install packs for marketing, sales, finance, and more.",
                "tip": "💡 Tip: Start with the Marketing Essentials pack for lead tracking and campaign management."
            },
            {
                "title": "CRM Integration",
                "description": "Manage your customer relationships, track sales pipeline, and never miss a follow-up opportunity.",
                "tip": "💡 Tip: Connect your email to automatically track customer communications."
            },
            {
                "title": "Time & Finance Tracking",
                "description": "Track billable hours, monitor expenses, and get real-time insights into your business profitability.",
                "tip": "💡 Tip: Set up project codes to categorize your time tracking by client or project."
            },
            {
                "title": "AI Assistant",
                "description": "Get intelligent help with business tasks, data analysis, and workflow automation using context-aware AI.",
                "tip": "💡 Tip: Try asking 'What should I focus on today?' for AI-powered business insights."
            }
        ]
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Entrepreneur Assistant Tour")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Progress indicator
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.progress_label)
        
        # Content area
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(15)
        
        # Step title
        self.step_title = QLabel()
        self.step_title.setFont(QFont("Arial", 18, QFont.Bold))
        self.step_title.setStyleSheet("color: #333;")
        content_layout.addWidget(self.step_title)
        
        # Step description
        self.step_description = QLabel()
        self.step_description.setFont(QFont("Arial", 12))
        self.step_description.setWordWrap(True)
        self.step_description.setStyleSheet("color: #555; line-height: 1.4;")
        content_layout.addWidget(self.step_description)
        
        # Step tip
        self.step_tip = QLabel()
        self.step_tip.setFont(QFont("Arial", 11))
        self.step_tip.setWordWrap(True)
        self.step_tip.setStyleSheet("""
            color: #007ACC;
            background-color: #f0f8ff;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #007ACC;
        """)
        content_layout.addWidget(self.step_tip)
        
        layout.addWidget(self.content_widget)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.previous_step)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)
        
        self.finish_btn = QPushButton("Get Started! 🚀")
        self.finish_btn.clicked.connect(self.accept)
        self.finish_btn.setVisible(False)
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        nav_layout.addWidget(self.finish_btn)
        
        layout.addLayout(nav_layout)
        
        # Show first step
        self.update_step()
    
    def update_step(self):
        """Update the display for the current step"""
        step = self.steps[self.current_step]
        
        self.progress_label.setText(f"Step {self.current_step + 1} of {len(self.steps)}")
        self.step_title.setText(step["title"])
        self.step_description.setText(step["description"])
        self.step_tip.setText(step["tip"])
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_step > 0)
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.setVisible(False)
            self.finish_btn.setVisible(True)
        else:
            self.next_btn.setVisible(True)
            self.finish_btn.setVisible(False)
    
    def next_step(self):
        """Go to next step"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_step()
    
    def previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step()


class FirstRunExperience:
    """Manages the first-run experience for new users"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config_manager = None
    
    def check_first_run(self) -> bool:
        """Check if this is the first run"""
        # Check if user has completed setup
        try:
            from util.entrepreneur_config import get_entrepreneur_config
            config = get_entrepreneur_config()
            return config.get_first_run_wizard_needed()
        except:
            return True
    
    def show_welcome_flow(self):
        """Show the complete welcome flow"""
        if not self.check_first_run():
            return False  # Not first run
        
        # Show welcome screen
        welcome = WelcomeScreen(self.parent)
        welcome.tour_requested.connect(self.show_tour)
        
        result = welcome.exec_()
        
        if result == QDialog.Accepted:
            # User chose quick setup
            self.show_setup_wizard()
            return True
        
        return False
    
    def show_setup_wizard(self):
        """Show the setup wizard"""
        try:
            from util.entrepreneur_config import FirstRunWizard, get_entrepreneur_config
            config = get_entrepreneur_config()
            wizard = FirstRunWizard(config)
            wizard.exec_()
        except Exception as e:
            print(f"Error showing setup wizard: {e}")
    
    def show_tour(self):
        """Show the application tour"""
        tour = QuickTour(self.parent)
        tour.exec_()
    
    def show_tips_dialog(self):
        """Show productivity tips for entrepreneurs"""
        tips = [
            "💡 Set up your business profile first for personalized insights",
            "📦 Install Tailor Packs relevant to your industry for specialized tools",
            "⏱️ Use time tracking to identify your most profitable activities",
            "📊 Check your dashboard daily to stay on top of key metrics",
            "🤖 Ask the AI assistant for help with data analysis and insights",
            "🔒 Enable auto-backup to protect your business data",
            "📧 Connect your email for automatic contact and lead tracking"
        ]
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Productivity Tips for Entrepreneurs")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("🎯 Productivity Tips")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        tips_list = QListWidget()
        for tip in tips:
            tips_list.addItem(tip)
        layout.addWidget(tips_list)
        
        close_btn = QPushButton("Got it!")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()


def show_welcome_if_needed(parent=None) -> bool:
    """Show welcome flow if this is the first run"""
    first_run = FirstRunExperience(parent)
    return first_run.show_welcome_flow()