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
        
        # Show welcome screen with enhanced Tailor Pack introduction
        welcome = EnhancedWelcomeScreen(self.parent)
        welcome.tour_requested.connect(self.show_tour)
        welcome.tailor_pack_intro_requested.connect(self.show_tailor_pack_introduction)
        
        result = welcome.exec_()
        
        if result == QDialog.Accepted:
            # User chose quick setup
            self.show_setup_wizard()
            return True
        
        return False
    
    def show_tailor_pack_introduction(self):
        """Show comprehensive Tailor Pack introduction"""
        intro_dialog = TailorPackIntroductionDialog(self.parent)
        intro_dialog.exec_()
    
    def show_setup_wizard(self):
        """Show the enhanced setup wizard"""
        try:
            from util.entrepreneur_config import FirstRunWizard, get_entrepreneur_config
            config = get_entrepreneur_config()
            wizard = EnhancedFirstRunWizard(config)
            wizard.exec_()
        except Exception as e:
            print(f"Error showing setup wizard: {e}")
    
    def show_tour(self):
        """Show the interactive application tour"""
        tour = InteractiveQuickTour(self.parent)
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


class EnhancedWelcomeScreen(QDialog):
    """Enhanced welcome screen with better Tailor Pack introduction"""
    
    tour_requested = pyqtSignal()
    tailor_pack_intro_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Westfall Assistant - Entrepreneur Edition")
        self.setFixedSize(700, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the enhanced UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("🚀 Welcome to Your Business Growth Journey!")
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2563eb; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Your AI-powered business assistant with extensible Tailor Packs")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Key benefits
        benefits_frame = QFrame()
        benefits_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        benefits_layout = QVBoxLayout(benefits_frame)
        
        benefits_title = QLabel("✨ What makes this assistant special:")
        benefits_title.setFont(QFont("Arial", 14, QFont.Bold))
        benefits_title.setStyleSheet("color: #1e293b; margin-bottom: 10px;")
        benefits_layout.addWidget(benefits_title)
        
        benefits = [
            "🎯 Tailored specifically for entrepreneurs and small businesses",
            "📦 Tailor Packs: Industry-specific tools that adapt to your business",
            "🤖 AI-powered insights to help grow your business",
            "📊 Real-time dashboard with key business metrics",
            "🔧 Customizable workflows that match your processes"
        ]
        
        for benefit in benefits:
            benefit_label = QLabel(benefit)
            benefit_label.setFont(QFont("Arial", 11))
            benefit_label.setStyleSheet("color: #475569; margin: 3px 0; padding-left: 10px;")
            benefits_layout.addWidget(benefit_label)
        
        layout.addWidget(benefits_frame)
        
        # Tailor Pack highlight
        tailor_pack_frame = QFrame()
        tailor_pack_frame.setStyleSheet("""
            QFrame {
                background-color: #ecfdf5;
                border: 2px solid #10b981;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        tailor_pack_layout = QVBoxLayout(tailor_pack_frame)
        
        tailor_pack_title = QLabel("📦 About Tailor Packs")
        tailor_pack_title.setFont(QFont("Arial", 14, QFont.Bold))
        tailor_pack_title.setStyleSheet("color: #065f46;")
        tailor_pack_layout.addWidget(tailor_pack_title)
        
        tailor_pack_desc = QLabel(
            "Tailor Packs are specialized functionality modules that add industry-specific "
            "tools and automations to your assistant. Think of them as professional "
            "software extensions designed specifically for your type of business."
        )
        tailor_pack_desc.setFont(QFont("Arial", 11))
        tailor_pack_desc.setWordWrap(True)
        tailor_pack_desc.setStyleSheet("color: #047857; margin: 10px 0;")
        tailor_pack_layout.addWidget(tailor_pack_desc)
        
        learn_more_btn = QPushButton("Learn More About Tailor Packs")
        learn_more_btn.clicked.connect(self.show_tailor_pack_intro)
        learn_more_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        tailor_pack_layout.addWidget(learn_more_btn)
        
        layout.addWidget(tailor_pack_frame)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        tour_btn = QPushButton("Take a Quick Tour")
        tour_btn.clicked.connect(self.start_tour)
        tour_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        
        setup_btn = QPushButton("Start Quick Setup")
        setup_btn.clicked.connect(self.start_setup)
        setup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        
        skip_btn = QPushButton("Skip for Now")
        skip_btn.clicked.connect(self.reject)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        
        button_layout.addWidget(tour_btn)
        button_layout.addWidget(setup_btn)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
    
    def show_tailor_pack_intro(self):
        """Show Tailor Pack introduction"""
        self.tailor_pack_intro_requested.emit()
    
    def start_setup(self):
        """Start the quick setup process"""
        self.accept()
    
    def start_tour(self):
        """Start the application tour"""
        self.tour_requested.emit()
        self.accept()


class TailorPackIntroductionDialog(QDialog):
    """Comprehensive Tailor Pack introduction dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tailor Packs - Your Business Advantage")
        self.setFixedSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("📦 Tailor Packs: Specialized Business Tools")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #1e293b; margin-bottom: 15px;")
        layout.addWidget(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # What are Tailor Packs section
        what_section = self.create_section(
            "What are Tailor Packs?",
            "Tailor Packs are specialized software modules that extend your assistant "
            "with industry-specific tools, automations, and workflows. Each pack is "
            "designed by experts in specific business domains to solve real challenges "
            "entrepreneurs face every day."
        )
        content_layout.addWidget(what_section)
        
        # Benefits section
        benefits_section = self.create_section(
            "Key Benefits",
            "",
            [
                "🎯 Industry-Specific: Tools designed for your exact business type",
                "⚡ Ready-to-Use: Pre-configured workflows that work immediately",
                "🔧 Customizable: Adapt tools to match your unique processes",
                "📈 Growth-Focused: Features that scale with your business",
                "🔄 Regular Updates: New features and improvements over time"
            ]
        )
        content_layout.addWidget(benefits_section)
        
        # Popular packs section
        packs_section = self.create_popular_packs_section()
        content_layout.addWidget(packs_section)
        
        # How it works section
        how_section = self.create_section(
            "How It Works",
            "",
            [
                "1️⃣ Choose packs relevant to your business",
                "2️⃣ Install with a simple order number or trial",
                "3️⃣ Configure tools to match your workflow",
                "4️⃣ Start using powerful business features immediately"
            ]
        )
        content_layout.addWidget(how_section)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Got it! Let's get started")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        layout.addWidget(close_btn)
    
    def create_section(self, title, description, bullet_points=None):
        """Create a content section"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin: 5px 0;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Arial", 11))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #475569; margin-bottom: 10px; line-height: 1.4;")
            layout.addWidget(desc_label)
        
        # Bullet points
        if bullet_points:
            for point in bullet_points:
                point_label = QLabel(point)
                point_label.setFont(QFont("Arial", 11))
                point_label.setStyleSheet("color: #475569; margin: 3px 0; padding-left: 10px;")
                layout.addWidget(point_label)
        
        return frame
    
    def create_popular_packs_section(self):
        """Create the popular packs section"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f0f9ff;
                border: 1px solid #0ea5e9;
                border-radius: 8px;
                padding: 15px;
                margin: 5px 0;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        title_label = QLabel("🌟 Popular Tailor Packs")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #0c4a6e; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        packs = [
            ("Marketing Essentials", "Campaign tracking, social media management, lead generation"),
            ("Sales Pipeline Pro", "Advanced CRM, deal tracking, sales analytics"),
            ("Finance Master", "Accounting integration, expense tracking, financial reporting"),
            ("Legal Essentials", "Contract templates, compliance tracking, legal document management")
        ]
        
        for pack_name, pack_desc in packs:
            pack_frame = QFrame()
            pack_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 3px 0;
                }
            """)
            pack_layout = QVBoxLayout(pack_frame)
            pack_layout.setSpacing(5)
            
            name_label = QLabel(pack_name)
            name_label.setFont(QFont("Arial", 12, QFont.Bold))
            name_label.setStyleSheet("color: #1e293b;")
            pack_layout.addWidget(name_label)
            
            desc_label = QLabel(pack_desc)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setStyleSheet("color: #64748b;")
            desc_label.setWordWrap(True)
            pack_layout.addWidget(desc_label)
            
            layout.addWidget(pack_frame)
        
        return frame


class EnhancedFirstRunWizard(QDialog):
    """Enhanced first-run wizard with better guidance"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Business Setup Wizard")
        self.setFixedSize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize enhanced wizard UI"""
        # This would be implemented with step-by-step guidance
        # For now, fall back to the existing wizard
        from util.entrepreneur_config import FirstRunWizard
        wizard = FirstRunWizard(self.config)
        wizard.exec_()
        self.accept()


class InteractiveQuickTour(QDialog):
    """Interactive application tour"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Tour")
        self.setFixedSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize tour UI"""
        layout = QVBoxLayout(self)
        
        # Tour content would be implemented here
        # For now, show a simple overview
        title = QLabel("🎯 Quick Tour")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        tour_text = QLabel(
            "This assistant helps entrepreneurs like you manage and grow your business.\n\n"
            "Key areas to explore:\n"
            "• Dashboard - Your business overview\n"
            "• Tailor Packs - Specialized business tools\n"
            "• Analytics - Data-driven insights\n"
            "• AI Assistant - Smart business help\n\n"
            "Take your time to explore each section!"
        )
        tour_text.setWordWrap(True)
        tour_text.setStyleSheet("padding: 20px; line-height: 1.5;")
        layout.addWidget(tour_text)
        
        close_btn = QPushButton("Start Exploring!")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        layout.addWidget(close_btn)