"""
Email Manager Component for Westfall Personal Assistant

Provides email management functionality with red/black theme integration.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QTextEdit, QPushButton, QLineEdit,
                           QLabel, QSplitter, QComboBox, QSpinBox, QCheckBox,
                           QGroupBox, QFormLayout, QTabWidget, QListWidget,
                           QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from utils.app_theme import AppTheme
import logging

logger = logging.getLogger(__name__)


class EmailThread(QThread):
    """Background thread for email operations"""
    emails_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, action, **kwargs):
        super().__init__()
        self.action = action
        self.kwargs = kwargs
        
    def run(self):
        """Run email operation in background"""
        try:
            if self.action == "fetch":
                # Simulate email fetching
                emails = [
                    {"from": "client@example.com", "subject": "Project Update", "date": "2025-09-09", "read": False},
                    {"from": "team@company.com", "subject": "Meeting Tomorrow", "date": "2025-09-09", "read": True},
                    {"from": "support@service.com", "subject": "Your Account", "date": "2025-09-08", "read": False},
                ]
                self.emails_loaded.emit(emails)
        except Exception as e:
            self.error_occurred.emit(str(e))


class EmailManager(QWidget):
    """Email management interface with integrated compose and inbox"""
    
    def __init__(self):
        super().__init__()
        self.emails = []
        self.current_email = None
        self.init_ui()
        self.apply_theme()
        self.load_emails()
        
    def init_ui(self):
        """Initialize the email interface"""
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("📧 Email Manager")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Email controls
        self.compose_btn = QPushButton("✍️ Compose")
        self.compose_btn.clicked.connect(self.compose_email)
        header_layout.addWidget(self.compose_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_emails)
        header_layout.addWidget(self.refresh_btn)
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Email list and folders
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Folders
        folders_label = QLabel("Folders")
        folders_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(folders_label)
        
        self.folders_tree = QTreeWidget()
        self.folders_tree.setHeaderHidden(True)
        self.setup_folders()
        left_layout.addWidget(self.folders_tree)
        
        # Email list
        emails_label = QLabel("Emails")
        emails_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(emails_label)
        
        self.email_list = QListWidget()
        self.email_list.itemClicked.connect(self.select_email)
        left_layout.addWidget(self.email_list)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel - Email content and compose
        right_panel = QTabWidget()
        
        # Email view tab
        self.email_view = QTextEdit()
        self.email_view.setReadOnly(True)
        right_panel.addTab(self.email_view, "📖 View")
        
        # Compose tab
        self.compose_widget = self.create_compose_widget()
        right_panel.addTab(self.compose_widget, "✍️ Compose")
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 800])
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def create_compose_widget(self):
        """Create the email composition interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Recipients
        form_layout = QFormLayout()
        
        self.to_field = QLineEdit()
        self.to_field.setPlaceholderText("recipient@example.com")
        form_layout.addRow("To:", self.to_field)
        
        self.cc_field = QLineEdit()
        self.cc_field.setPlaceholderText("cc@example.com")
        form_layout.addRow("CC:", self.cc_field)
        
        self.subject_field = QLineEdit()
        self.subject_field.setPlaceholderText("Email subject")
        form_layout.addRow("Subject:", self.subject_field)
        
        layout.addLayout(form_layout)
        
        # Message body
        body_label = QLabel("Message:")
        body_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(body_label)
        
        self.message_body = QTextEdit()
        self.message_body.setPlaceholderText("Type your message here...")
        layout.addWidget(self.message_body)
        
        # Send controls
        send_layout = QHBoxLayout()
        
        send_layout.addStretch()
        
        self.save_draft_btn = QPushButton("💾 Save Draft")
        self.save_draft_btn.clicked.connect(self.save_draft)
        send_layout.addWidget(self.save_draft_btn)
        
        self.send_btn = QPushButton("📤 Send")
        self.send_btn.clicked.connect(self.send_email)
        send_layout.addWidget(self.send_btn)
        
        layout.addLayout(send_layout)
        
        return widget
        
    def setup_folders(self):
        """Setup email folders tree"""
        # Inbox
        inbox = QTreeWidgetItem(self.folders_tree, ["📥 Inbox (3)"])
        
        # Sent
        sent = QTreeWidgetItem(self.folders_tree, ["📤 Sent"])
        
        # Drafts
        drafts = QTreeWidgetItem(self.folders_tree, ["📝 Drafts"])
        
        # Trash
        trash = QTreeWidgetItem(self.folders_tree, ["🗑️ Trash"])
        
        # Custom folders
        work = QTreeWidgetItem(self.folders_tree, ["💼 Work"])
        personal = QTreeWidgetItem(self.folders_tree, ["👤 Personal"])
        
        self.folders_tree.expandAll()
        
    def apply_theme(self):
        """Apply red/black theme to email interface"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QTreeWidget, QListWidget {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTreeWidget::item:selected, QListWidget::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QTextEdit, QLineEdit {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_MEDIUM}px;
            }}
            QTextEdit:focus, QLineEdit:focus {{
                border-color: {AppTheme.HIGHLIGHT_COLOR};
            }}
            QPushButton {{
                {AppTheme.get_button_style()}
            }}
            QTabWidget::pane {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                background-color: {AppTheme.SECONDARY_BG};
            }}
            QTabBar::tab {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_SMALL}px {AppTheme.PADDING_MEDIUM}px;
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTabBar::tab:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
        """)
        
    def load_emails(self):
        """Load emails from server"""
        self.status_label.setText("Loading emails...")
        self.refresh_btn.setEnabled(False)
        
        # Start email loading thread
        self.email_thread = EmailThread("fetch")
        self.email_thread.emails_loaded.connect(self.on_emails_loaded)
        self.email_thread.error_occurred.connect(self.on_error)
        self.email_thread.start()
        
    def on_emails_loaded(self, emails):
        """Handle emails loaded from server"""
        self.emails = emails
        self.update_email_list()
        self.status_label.setText(f"Loaded {len(emails)} emails")
        self.refresh_btn.setEnabled(True)
        
    def on_error(self, error):
        """Handle email loading error"""
        self.status_label.setText(f"Error: {error}")
        self.refresh_btn.setEnabled(True)
        QMessageBox.warning(self, "Email Error", f"Failed to load emails: {error}")
        
    def update_email_list(self):
        """Update the email list widget"""
        self.email_list.clear()
        
        for email in self.emails:
            status = "🔴" if not email["read"] else "📖"
            item_text = f"{status} {email['from']} - {email['subject']} ({email['date']})"
            self.email_list.addItem(item_text)
            
    def select_email(self, item):
        """Handle email selection"""
        index = self.email_list.row(item)
        if 0 <= index < len(self.emails):
            self.current_email = self.emails[index]
            self.display_email(self.current_email)
            
    def display_email(self, email):
        """Display email content"""
        content = f"""
        <div style="background-color: {AppTheme.SECONDARY_BG}; padding: 10px; margin-bottom: 10px;">
            <h3 style="color: {AppTheme.PRIMARY_COLOR};">Subject: {email['subject']}</h3>
            <p><strong>From:</strong> {email['from']}</p>
            <p><strong>Date:</strong> {email['date']}</p>
        </div>
        <div style="padding: 10px;">
            <p>This is a sample email content. In a real implementation, this would show the actual email body.</p>
            <p>Email functionality would integrate with services like:</p>
            <ul>
                <li>Gmail API</li>
                <li>Outlook/Exchange</li>
                <li>IMAP/POP3 servers</li>
            </ul>
        </div>
        """
        self.email_view.setHtml(content)
        
        # Mark as read
        email["read"] = True
        self.update_email_list()
        
    def compose_email(self):
        """Start composing a new email"""
        # Clear compose fields
        self.to_field.clear()
        self.cc_field.clear()
        self.subject_field.clear()
        self.message_body.clear()
        
        # Switch to compose tab
        parent = self.compose_widget.parent()
        if hasattr(parent, 'setCurrentWidget'):
            parent.setCurrentWidget(self.compose_widget)
            
    def send_email(self):
        """Send the composed email"""
        to = self.to_field.text().strip()
        subject = self.subject_field.text().strip()
        body = self.message_body.toPlainText().strip()
        
        if not to or not subject or not body:
            QMessageBox.warning(self, "Incomplete Email", 
                              "Please fill in all required fields (To, Subject, Message).")
            return
            
        # Simulate sending
        QMessageBox.information(self, "Email Sent", 
                              f"Email sent to {to}\nSubject: {subject}")
        
        # Clear fields
        self.compose_email()
        
    def save_draft(self):
        """Save email as draft"""
        QMessageBox.information(self, "Draft Saved", "Email saved as draft.")
        
    def show_settings(self):
        """Show email settings dialog"""
        QMessageBox.information(self, "Email Settings", 
                              "Email settings panel will be implemented here.\n\n"
                              "Features to include:\n"
                              "- Account configuration\n"
                              "- Server settings\n"
                              "- Signature management\n"
                              "- Notification preferences")
