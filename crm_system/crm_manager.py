import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
import os

# Optional dependencies with fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class CRMManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_db()
        self.init_ui()
    
    def init_db(self):
        """Initialize CRM database with advanced features"""
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/crm.db')
        cursor = self.conn.cursor()
        
        # Enhanced client profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                website TEXT,
                social_media TEXT,
                industry TEXT,
                company_size TEXT,
                acquisition_date DATE,
                acquisition_source TEXT,
                lifetime_value REAL DEFAULT 0,
                average_order_value REAL DEFAULT 0,
                purchase_frequency INTEGER DEFAULT 0,
                last_purchase_date DATE,
                preferred_contact_method TEXT,
                timezone TEXT,
                language TEXT,
                tags TEXT,
                notes TEXT,
                status TEXT DEFAULT 'lead',
                lead_score INTEGER DEFAULT 0,
                assigned_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interaction history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                interaction_type TEXT,
                interaction_date TIMESTAMP,
                duration INTEGER,
                subject TEXT,
                description TEXT,
                outcome TEXT,
                next_action TEXT,
                next_action_date DATE,
                attachments TEXT,
                FOREIGN KEY (client_id) REFERENCES client_profiles (id)
            )
        ''')
        
        # Deal pipeline
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                deal_name TEXT,
                deal_value REAL,
                probability INTEGER,
                expected_close_date DATE,
                actual_close_date DATE,
                stage TEXT DEFAULT 'prospecting',
                source TEXT,
                competitor TEXT,
                loss_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES client_profiles (id)
            )
        ''')
        
        # Email campaigns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT,
                subject TEXT,
                content TEXT,
                recipients TEXT,
                sent_date TIMESTAMP,
                open_rate REAL,
                click_rate REAL,
                conversion_rate REAL,
                status TEXT DEFAULT 'draft'
            )
        ''')
        
        # Follow-up automation rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follow_up_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT,
                trigger_event TEXT,
                delay_days INTEGER,
                action_type TEXT,
                template_id INTEGER,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        self.conn.commit()
    
    def init_ui(self):
        self.setWindowTitle("CRM & Client Management System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QTextEdit, QLineEdit, QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                gridline-color: #555;
                border: 1px solid #555;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 10px 20px;
                margin-right: 2px;
                border-radius: 4px 4px 0px 0px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🤝 Customer Relationship Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Quick stats
        self.stats_label = QLabel("Leads: 0 | Prospects: 0 | Customers: 0 | Total Value: $0")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Main CRM tabs
        self.crm_tabs = QTabWidget()
        
        # Pipeline view
        self.pipeline_widget = self.create_pipeline_view()
        self.crm_tabs.addTab(self.pipeline_widget, "📊 Sales Pipeline")
        
        # Client list
        self.clients_widget = self.create_clients_view()
        self.crm_tabs.addTab(self.clients_widget, "👥 Clients")
        
        # Interactions
        self.interactions_widget = self.create_interactions_view()
        self.crm_tabs.addTab(self.interactions_widget, "💬 Interactions")
        
        # Campaigns
        self.campaigns_widget = self.create_campaigns_view()
        self.crm_tabs.addTab(self.campaigns_widget, "📧 Campaigns")
        
        # Automation
        self.automation_widget = self.create_automation_view()
        self.crm_tabs.addTab(self.automation_widget, "⚡ Automation")
        
        layout.addWidget(self.crm_tabs)
        
        # Load initial data
        self.refresh_stats()
    
    def create_pipeline_view(self):
        """Create sales pipeline kanban view"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Pipeline controls
        controls = QHBoxLayout()
        
        add_deal_btn = QPushButton("➕ New Deal")
        add_deal_btn.clicked.connect(self.add_deal)
        controls.addWidget(add_deal_btn)
        
        self.pipeline_filter = QComboBox()
        self.pipeline_filter.addItems(["All Deals", "My Deals", "This Month", "This Quarter"])
        controls.addWidget(self.pipeline_filter)
        
        controls.addStretch()
        
        self.pipeline_value = QLabel("Total Pipeline: $0")
        self.pipeline_value.setStyleSheet("font-weight: bold;")
        controls.addWidget(self.pipeline_value)
        
        layout.addLayout(controls)
        
        # Kanban board
        kanban_scroll = QScrollArea()
        kanban_widget = QWidget()
        kanban_layout = QHBoxLayout(kanban_widget)
        
        # Pipeline stages
        stages = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
        
        for stage in stages:
            stage_widget = self.create_pipeline_stage(stage)
            kanban_layout.addWidget(stage_widget)
        
        kanban_scroll.setWidget(kanban_widget)
        kanban_scroll.setWidgetResizable(True)
        layout.addWidget(kanban_scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_pipeline_stage(self, stage_name):
        """Create a pipeline stage column"""
        stage = QGroupBox(stage_name)
        stage.setMinimumWidth(250)
        
        layout = QVBoxLayout()
        
        # Stage header with count and value
        header = QLabel(f"0 deals - $0")
        header.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(header)
        
        # Deal cards area
        deals_area = QScrollArea()
        deals_widget = QWidget()
        deals_layout = QVBoxLayout(deals_widget)
        
        # Sample deal card (would be populated from database)
        if stage_name == "Prospecting":
            deal_card = self.create_deal_card("Sample Deal", "$10,000", "Sample Client")
            deals_layout.addWidget(deal_card)
        
        deals_layout.addStretch()
        deals_area.setWidget(deals_widget)
        layout.addWidget(deals_area)
        
        stage.setLayout(layout)
        return stage
    
    def create_deal_card(self, title, value, client):
        """Create a deal card widget"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
            }
            QFrame:hover {
                border-color: #007bff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: #28a745; font-size: 14px;")
        layout.addWidget(value_label)
        
        client_label = QLabel(client)
        client_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(client_label)
        
        card.setLayout(layout)
        return card
    
    def create_clients_view(self):
        """Create clients list view"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Client controls
        controls = QHBoxLayout()
        
        add_client_btn = QPushButton("➕ Add Client")
        add_client_btn.clicked.connect(self.add_client)
        controls.addWidget(add_client_btn)
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_clients)
        controls.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_clients)
        controls.addWidget(export_btn)
        
        controls.addStretch()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search clients...")
        search_input.textChanged.connect(self.search_clients)
        controls.addWidget(search_input)
        
        layout.addLayout(controls)
        
        # Client table with advanced features
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(10)
        self.client_table.setHorizontalHeaderLabels([
            "Name", "Company", "Email", "Phone", "Status",
            "Lead Score", "LTV", "Last Contact", "Assigned To", "Actions"
        ])
        
        layout.addWidget(self.client_table)
        self.load_clients()
        
        widget.setLayout(layout)
        return widget
    
    def create_interactions_view(self):
        """Create interactions timeline view"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Interaction controls
        controls = QHBoxLayout()
        
        log_interaction_btn = QPushButton("➕ Log Interaction")
        log_interaction_btn.clicked.connect(self.log_interaction)
        controls.addWidget(log_interaction_btn)
        
        self.interaction_filter = QComboBox()
        self.interaction_filter.addItems(["All", "Calls", "Emails", "Meetings", "Notes"])
        controls.addWidget(self.interaction_filter)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Interactions table
        self.interactions_table = QTableWidget()
        self.interactions_table.setColumnCount(7)
        self.interactions_table.setHorizontalHeaderLabels([
            "Date", "Client", "Type", "Subject", "Duration", "Outcome", "Next Action"
        ])
        
        layout.addWidget(self.interactions_table)
        self.load_interactions()
        
        widget.setLayout(layout)
        return widget
    
    def create_campaigns_view(self):
        """Create email campaigns view"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Campaign controls
        controls = QHBoxLayout()
        
        new_campaign_btn = QPushButton("📧 New Campaign")
        new_campaign_btn.clicked.connect(self.create_campaign)
        controls.addWidget(new_campaign_btn)
        
        templates_btn = QPushButton("📋 Templates")
        templates_btn.clicked.connect(self.manage_templates)
        controls.addWidget(templates_btn)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Campaigns table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Campaign", "Subject", "Recipients", "Sent Date", "Open Rate", "Status"
        ])
        
        layout.addWidget(self.campaigns_table)
        self.load_campaigns()
        
        widget.setLayout(layout)
        return widget
    
    def create_automation_view(self):
        """Create automation rules view"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Automation controls
        controls = QHBoxLayout()
        
        new_rule_btn = QPushButton("⚡ New Rule")
        new_rule_btn.clicked.connect(self.create_automation_rule)
        controls.addWidget(new_rule_btn)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Automation rules
        rules_group = QGroupBox("Follow-up Automation Rules")
        rules_layout = QVBoxLayout()
        
        # Sample automation rules
        sample_rules = [
            "📧 Send welcome email 1 day after lead creation",
            "📞 Schedule follow-up call 7 days after proposal sent",
            "📋 Send project update request 14 days after project start",
            "🎯 Move to nurture campaign after 30 days of inactivity"
        ]
        
        for rule in sample_rules:
            rule_label = QLabel(rule)
            rule_label.setStyleSheet("padding: 8px; border: 1px solid #555; margin: 2px;")
            rules_layout.addWidget(rule_label)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        widget.setLayout(layout)
        return widget
    
    def load_clients(self):
        """Load clients into table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, company, email, phone, status, lead_score, lifetime_value, 
                   updated_at, assigned_to
            FROM client_profiles 
            ORDER BY updated_at DESC
        """)
        clients = cursor.fetchall()
        
        self.client_table.setRowCount(len(clients))
        for row, client_data in enumerate(clients):
            for col, data in enumerate(client_data):
                if col == 6:  # LTV column - format as currency
                    self.client_table.setItem(row, col, QTableWidgetItem(f"${data:.2f}" if data else "$0.00"))
                else:
                    self.client_table.setItem(row, col, QTableWidgetItem(str(data) if data else ""))
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda: self.edit_client(row))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda: self.delete_client(row))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.client_table.setCellWidget(row, 9, actions_widget)
    
    def load_interactions(self):
        """Load interactions into table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.interaction_date, c.name, i.interaction_type, i.subject, 
                   i.duration, i.outcome, i.next_action
            FROM interactions i
            JOIN client_profiles c ON i.client_id = c.id
            ORDER BY i.interaction_date DESC
            LIMIT 50
        """)
        interactions = cursor.fetchall()
        
        self.interactions_table.setRowCount(len(interactions))
        for row, interaction_data in enumerate(interactions):
            for col, data in enumerate(interaction_data):
                self.interactions_table.setItem(row, col, QTableWidgetItem(str(data) if data else ""))
    
    def load_campaigns(self):
        """Load campaigns into table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT campaign_name, subject, recipients, sent_date, open_rate, status
            FROM email_campaigns
            ORDER BY sent_date DESC
        """)
        campaigns = cursor.fetchall()
        
        self.campaigns_table.setRowCount(len(campaigns))
        for row, campaign_data in enumerate(campaigns):
            for col, data in enumerate(campaign_data):
                if col == 4 and data:  # Open rate column
                    self.campaigns_table.setItem(row, col, QTableWidgetItem(f"{data:.1f}%"))
                else:
                    self.campaigns_table.setItem(row, col, QTableWidgetItem(str(data) if data else ""))
    
    def refresh_stats(self):
        """Refresh CRM statistics"""
        cursor = self.conn.cursor()
        
        # Count clients by status
        cursor.execute("SELECT COUNT(*) FROM client_profiles WHERE status = 'lead'")
        leads = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_profiles WHERE status = 'prospect'")
        prospects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_profiles WHERE status = 'customer'")
        customers = cursor.fetchone()[0]
        
        # Calculate total pipeline value
        cursor.execute("SELECT SUM(deal_value) FROM deals WHERE stage NOT IN ('closed_won', 'closed_lost')")
        pipeline_value = cursor.fetchone()[0] or 0
        
        self.stats_label.setText(f"Leads: {leads} | Prospects: {prospects} | Customers: {customers} | Total Value: ${pipeline_value:,.2f}")
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec_():
            client_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO client_profiles (name, company, email, phone, status, notes, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (client_data['name'], client_data['company'], client_data['email'],
                  client_data['phone'], client_data['status'], client_data['notes'], 
                  client_data['assigned_to']))
            self.conn.commit()
            self.load_clients()
            self.refresh_stats()
    
    def add_deal(self):
        """Add new deal"""
        dialog = DealDialog(self)
        if dialog.exec_():
            deal_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO deals (client_id, deal_name, deal_value, probability, 
                                 expected_close_date, stage, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (deal_data['client_id'], deal_data['deal_name'], deal_data['deal_value'],
                  deal_data['probability'], deal_data['expected_close_date'], 
                  deal_data['stage'], deal_data['notes']))
            self.conn.commit()
            self.refresh_stats()
    
    def log_interaction(self):
        """Log new interaction"""
        dialog = InteractionDialog(self)
        if dialog.exec_():
            interaction_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO interactions (client_id, interaction_type, interaction_date,
                                        duration, subject, description, outcome, next_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (interaction_data['client_id'], interaction_data['interaction_type'],
                  interaction_data['interaction_date'], interaction_data['duration'],
                  interaction_data['subject'], interaction_data['description'],
                  interaction_data['outcome'], interaction_data['next_action']))
            self.conn.commit()
            self.load_interactions()
    
    def search_clients(self, text):
        """Search clients based on text"""
        # Simple search implementation - filter table rows
        for row in range(self.client_table.rowCount()):
            match = False
            for col in range(5):  # Search in first 5 columns
                item = self.client_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.client_table.setRowHidden(row, not match)
    
    def edit_client(self, row):
        """Edit selected client"""
        QMessageBox.information(self, "Edit Client", f"Edit client functionality for row {row}")
    
    def delete_client(self, row):
        """Delete selected client"""
        reply = QMessageBox.question(self, "Delete Client", 
                                   "Are you sure you want to delete this client?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Delete", "Client deletion functionality")
    
    def import_clients(self):
        """Import clients from CSV"""
        QMessageBox.information(self, "Import", "CSV import functionality")
    
    def export_clients(self):
        """Export clients to CSV"""
        QMessageBox.information(self, "Export", "CSV export functionality")
    
    def create_campaign(self):
        """Create new email campaign"""
        QMessageBox.information(self, "Campaign", "Email campaign creation functionality")
    
    def manage_templates(self):
        """Manage email templates"""
        QMessageBox.information(self, "Templates", "Email template management functionality")
    
    def create_automation_rule(self):
        """Create new automation rule"""
        QMessageBox.information(self, "Automation", "Automation rule creation functionality")

# Dialog classes for data entry
class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add Client")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        layout.addRow("Name*:", self.name_input)
        
        self.company_input = QLineEdit()
        layout.addRow("Company:", self.company_input)
        
        self.email_input = QLineEdit()
        layout.addRow("Email*:", self.email_input)
        
        self.phone_input = QLineEdit()
        layout.addRow("Phone:", self.phone_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["lead", "prospect", "customer", "inactive"])
        layout.addRow("Status:", self.status_combo)
        
        self.assigned_to_input = QLineEdit()
        layout.addRow("Assigned To:", self.assigned_to_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'company': self.company_input.text(),
            'email': self.email_input.text(),
            'phone': self.phone_input.text(),
            'status': self.status_combo.currentText(),
            'assigned_to': self.assigned_to_input.text(),
            'notes': self.notes_input.toPlainText()
        }

class DealDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_crm = parent
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add Deal")
        self.setModal(True)
        
        layout = QFormLayout()
        
        self.client_combo = QComboBox()
        self.load_clients()
        layout.addRow("Client*:", self.client_combo)
        
        self.deal_name_input = QLineEdit()
        layout.addRow("Deal Name*:", self.deal_name_input)
        
        self.deal_value_input = QLineEdit()
        self.deal_value_input.setPlaceholderText("0.00")
        layout.addRow("Deal Value:", self.deal_value_input)
        
        self.probability_input = QSpinBox()
        self.probability_input.setRange(0, 100)
        self.probability_input.setSuffix("%")
        layout.addRow("Probability:", self.probability_input)
        
        self.close_date_input = QDateEdit()
        self.close_date_input.setDate(datetime.now().date())
        layout.addRow("Expected Close:", self.close_date_input)
        
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["prospecting", "qualification", "proposal", "negotiation"])
        layout.addRow("Stage:", self.stage_combo)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_clients(self):
        if self.parent_crm:
            cursor = self.parent_crm.conn.cursor()
            cursor.execute("SELECT id, name FROM client_profiles ORDER BY name")
            clients = cursor.fetchall()
            
            for client_id, name in clients:
                self.client_combo.addItem(name, client_id)
    
    def get_data(self):
        try:
            deal_value = float(self.deal_value_input.text()) if self.deal_value_input.text() else 0.0
        except ValueError:
            deal_value = 0.0
        
        return {
            'client_id': self.client_combo.currentData(),
            'deal_name': self.deal_name_input.text(),
            'deal_value': deal_value,
            'probability': self.probability_input.value(),
            'expected_close_date': self.close_date_input.date().toPyDate(),
            'stage': self.stage_combo.currentText(),
            'notes': self.notes_input.toPlainText()
        }

class InteractionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_crm = parent
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Log Interaction")
        self.setModal(True)
        
        layout = QFormLayout()
        
        self.client_combo = QComboBox()
        self.load_clients()
        layout.addRow("Client*:", self.client_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["call", "email", "meeting", "note", "proposal"])
        layout.addRow("Type:", self.type_combo)
        
        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(datetime.now())
        layout.addRow("Date/Time:", self.date_input)
        
        self.duration_input = QSpinBox()
        self.duration_input.setSuffix(" minutes")
        self.duration_input.setRange(0, 999)
        layout.addRow("Duration:", self.duration_input)
        
        self.subject_input = QLineEdit()
        layout.addRow("Subject:", self.subject_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        layout.addRow("Description:", self.description_input)
        
        self.outcome_input = QLineEdit()
        layout.addRow("Outcome:", self.outcome_input)
        
        self.next_action_input = QLineEdit()
        layout.addRow("Next Action:", self.next_action_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_clients(self):
        if self.parent_crm:
            cursor = self.parent_crm.conn.cursor()
            cursor.execute("SELECT id, name FROM client_profiles ORDER BY name")
            clients = cursor.fetchall()
            
            for client_id, name in clients:
                self.client_combo.addItem(name, client_id)
    
    def get_data(self):
        return {
            'client_id': self.client_combo.currentData(),
            'interaction_type': self.type_combo.currentText(),
            'interaction_date': self.date_input.dateTime().toPyDateTime(),
            'duration': self.duration_input.value(),
            'subject': self.subject_input.text(),
            'description': self.description_input.toPlainText(),
            'outcome': self.outcome_input.text(),
            'next_action': self.next_action_input.text()
        }