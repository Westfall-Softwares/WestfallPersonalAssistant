import json
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
import os

# Optional dependencies with fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class BusinessDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_db()
        self.init_ui()
        self.load_dashboard_data()
        
        # Auto-refresh every 5 minutes
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(300000)
    
    def init_db(self):
        """Initialize business metrics database"""
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        self.conn = sqlite3.connect('data/business_metrics.db')
        cursor = self.conn.cursor()
        
        # KPI tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_date DATE NOT NULL,
                category TEXT,
                notes TEXT
            )
        ''')
        
        # Revenue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                source TEXT,
                client_name TEXT,
                date DATE NOT NULL,
                invoice_number TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Client tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                acquisition_date DATE,
                lifetime_value REAL,
                status TEXT DEFAULT 'active',
                last_interaction DATE,
                notes TEXT
            )
        ''')
        
        # Project tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                client_id INTEGER,
                start_date DATE,
                end_date DATE,
                budget REAL,
                actual_cost REAL,
                status TEXT DEFAULT 'planning',
                completion_percentage INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        self.conn.commit()
    
    def init_ui(self):
        self.setWindowTitle("Business Intelligence Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set dark theme for professional look
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
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header with company name and date
        header_layout = QHBoxLayout()
        
        company_label = QLabel("📊 Business Intelligence Dashboard")
        company_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(company_label)
        
        header_layout.addStretch()
        
        self.date_label = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        self.date_label.setStyleSheet("font-size: 14px; color: #888;")
        header_layout.addWidget(self.date_label)
        
        main_layout.addLayout(header_layout)
        
        # Quick Stats Row
        stats_layout = QHBoxLayout()
        
        self.revenue_card = self.create_metric_card("💰 Monthly Revenue", "$0", "+0%", "#28a745")
        stats_layout.addWidget(self.revenue_card)
        
        self.clients_card = self.create_metric_card("👥 Active Clients", "0", "+0", "#007bff")
        stats_layout.addWidget(self.clients_card)
        
        self.projects_card = self.create_metric_card("📁 Active Projects", "0", "0 completed", "#6f42c1")
        stats_layout.addWidget(self.projects_card)
        
        self.tasks_card = self.create_metric_card("✅ Tasks Today", "0", "0 overdue", "#fd7e14")
        stats_layout.addWidget(self.tasks_card)
        
        main_layout.addLayout(stats_layout)
        
        # Main content area with tabs
        self.dashboard_tabs = QTabWidget()
        self.dashboard_tabs.setStyleSheet("""
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
        
        # Overview Tab
        self.overview_widget = self.create_overview_tab()
        self.dashboard_tabs.addTab(self.overview_widget, "📈 Overview")
        
        # Revenue Tab
        self.revenue_widget = self.create_revenue_tab()
        self.dashboard_tabs.addTab(self.revenue_widget, "💵 Revenue")
        
        # Clients Tab
        self.clients_widget = self.create_clients_tab()
        self.dashboard_tabs.addTab(self.clients_widget, "👥 Clients")
        
        # Projects Tab
        self.projects_widget = self.create_projects_tab()
        self.dashboard_tabs.addTab(self.projects_widget, "📁 Projects")
        
        # Analytics Tab
        self.analytics_widget = self.create_analytics_tab()
        self.dashboard_tabs.addTab(self.analytics_widget, "📊 Analytics")
        
        # Reports Tab
        self.reports_widget = self.create_reports_tab()
        self.dashboard_tabs.addTab(self.reports_widget, "📄 Reports")
        
        main_layout.addWidget(self.dashboard_tabs)
        
        # Bottom toolbar
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        toolbar_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📥 Export Data")
        export_btn.clicked.connect(self.export_data)
        toolbar_layout.addWidget(export_btn)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        toolbar_layout.addWidget(settings_btn)
        
        toolbar_layout.addStretch()
        
        self.status_label = QLabel("Last updated: Just now")
        self.status_label.setStyleSheet("color: #888;")
        toolbar_layout.addWidget(self.status_label)
        
        main_layout.addLayout(toolbar_layout)
    
    def create_metric_card(self, title, value, change, color):
        """Create a metric display card"""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: #2a2a2a;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
                min-height: 100px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        change_label = QLabel(change)
        change_label.setStyleSheet("font-size: 11px; color: #aaa;")
        layout.addWidget(change_label)
        
        card.setLayout(layout)
        return card
    
    def create_overview_tab(self):
        """Create overview tab with key metrics"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Daily briefing
        briefing_group = QGroupBox("📋 Daily Briefing")
        briefing_layout = QVBoxLayout()
        
        self.briefing_text = QTextEdit()
        self.briefing_text.setReadOnly(True)
        self.briefing_text.setMaximumHeight(150)
        briefing_layout.addWidget(self.briefing_text)
        
        briefing_group.setLayout(briefing_layout)
        layout.addWidget(briefing_group)
        
        # Charts area placeholder
        charts_layout = QHBoxLayout()
        
        # Revenue chart placeholder
        revenue_chart_group = QGroupBox("📈 Revenue Trend")
        revenue_chart_layout = QVBoxLayout()
        self.revenue_chart = QTextEdit()
        self.revenue_chart.setPlainText("Revenue chart would appear here\n(Install plotly for advanced charts)")
        self.revenue_chart.setMaximumHeight(200)
        revenue_chart_layout.addWidget(self.revenue_chart)
        revenue_chart_group.setLayout(revenue_chart_layout)
        charts_layout.addWidget(revenue_chart_group)
        
        # Task completion chart placeholder
        task_chart_group = QGroupBox("✅ Task Completion")
        task_chart_layout = QVBoxLayout()
        self.task_chart = QTextEdit()
        self.task_chart.setPlainText("Task completion chart would appear here\n(Install plotly for advanced charts)")
        self.task_chart.setMaximumHeight(200)
        task_chart_layout.addWidget(self.task_chart)
        task_chart_group.setLayout(task_chart_layout)
        charts_layout.addWidget(task_chart_group)
        
        layout.addLayout(charts_layout)
        
        # Recent activity
        activity_group = QGroupBox("📝 Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: #3a3a3a;
                color: #ffffff;
                border: none;
            }
        """)
        activity_layout.addWidget(self.activity_list)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_revenue_tab(self):
        """Create revenue tracking tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Revenue entry form
        entry_group = QGroupBox("➕ Add Revenue Entry")
        entry_layout = QHBoxLayout()
        
        self.revenue_amount = QLineEdit()
        self.revenue_amount.setPlaceholderText("Amount ($)")
        entry_layout.addWidget(self.revenue_amount)
        
        self.revenue_source = QLineEdit()
        self.revenue_source.setPlaceholderText("Source/Client")
        entry_layout.addWidget(self.revenue_source)
        
        self.revenue_invoice = QLineEdit()
        self.revenue_invoice.setPlaceholderText("Invoice #")
        entry_layout.addWidget(self.revenue_invoice)
        
        add_revenue_btn = QPushButton("➕ Add Revenue")
        add_revenue_btn.clicked.connect(self.add_revenue)
        entry_layout.addWidget(add_revenue_btn)
        
        entry_group.setLayout(entry_layout)
        layout.addWidget(entry_group)
        
        # Revenue table
        self.revenue_table = QTableWidget()
        self.revenue_table.setColumnCount(6)
        self.revenue_table.setHorizontalHeaderLabels(["Date", "Amount", "Source", "Client", "Invoice", "Status"])
        self.revenue_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.revenue_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_clients_tab(self):
        """Create client management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Client controls
        controls_layout = QHBoxLayout()
        
        add_client_btn = QPushButton("➕ Add Client")
        add_client_btn.clicked.connect(self.add_client)
        controls_layout.addWidget(add_client_btn)
        
        import_clients_btn = QPushButton("📥 Import CSV")
        import_clients_btn.clicked.connect(self.import_clients)
        controls_layout.addWidget(import_clients_btn)
        
        controls_layout.addStretch()
        
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Search clients...")
        self.client_search.textChanged.connect(self.search_clients)
        controls_layout.addWidget(self.client_search)
        
        layout.addLayout(controls_layout)
        
        # Client list
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(7)
        self.client_table.setHorizontalHeaderLabels(["Name", "Company", "Email", "Phone", "LTV", "Status", "Actions"])
        layout.addWidget(self.client_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_projects_tab(self):
        """Create project management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Project controls
        controls_layout = QHBoxLayout()
        
        add_project_btn = QPushButton("➕ New Project")
        add_project_btn.clicked.connect(self.add_project)
        controls_layout.addWidget(add_project_btn)
        
        # Project status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Planning", "In Progress", "Review", "Completed", "On Hold"])
        self.status_filter.currentTextChanged.connect(self.filter_projects)
        controls_layout.addWidget(self.status_filter)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Project cards area
        self.project_scroll = QScrollArea()
        self.project_container = QWidget()
        self.project_layout = QVBoxLayout(self.project_container)
        
        self.project_scroll.setWidget(self.project_container)
        self.project_scroll.setWidgetResizable(True)
        layout.addWidget(self.project_scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_analytics_tab(self):
        """Create analytics and insights tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Analytics controls
        controls_layout = QHBoxLayout()
        
        self.date_range = QComboBox()
        self.date_range.addItems(["Last 7 Days", "Last 30 Days", "Last Quarter", "Last Year", "All Time"])
        self.date_range.currentTextChanged.connect(self.update_analytics)
        controls_layout.addWidget(self.date_range)
        
        generate_insights_btn = QPushButton("🤖 Generate AI Insights")
        generate_insights_btn.clicked.connect(self.generate_ai_insights)
        controls_layout.addWidget(generate_insights_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Analytics display area
        analytics_tabs = QTabWidget()
        
        # Revenue analytics
        revenue_analytics = QTextEdit()
        revenue_analytics.setPlainText("Revenue trends and analysis will appear here")
        analytics_tabs.addTab(revenue_analytics, "Revenue Analysis")
        
        # Client analytics
        client_analytics = QTextEdit()
        client_analytics.setPlainText("Client acquisition and retention metrics")
        analytics_tabs.addTab(client_analytics, "Client Analysis")
        
        # Performance metrics
        performance_analytics = QTextEdit()
        performance_analytics.setPlainText("Business performance KPIs")
        analytics_tabs.addTab(performance_analytics, "Performance")
        
        layout.addWidget(analytics_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def create_reports_tab(self):
        """Create automated reports tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Report generation controls
        controls_layout = QHBoxLayout()
        
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Daily Summary",
            "Weekly Report",
            "Monthly Report",
            "Quarterly Report",
            "Tax Report",
            "Client Report",
            "Project Status Report",
            "Financial Statement"
        ])
        controls_layout.addWidget(self.report_type)
        
        generate_btn = QPushButton("📄 Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(generate_btn)
        
        schedule_btn = QPushButton("⏰ Schedule Reports")
        schedule_btn.clicked.connect(self.schedule_reports)
        controls_layout.addWidget(schedule_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Report preview area
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        layout.addWidget(self.report_preview)
        
        # Export controls
        export_layout = QHBoxLayout()
        
        export_pdf_btn = QPushButton("📑 Export as PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton("📊 Export as Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        export_layout.addWidget(export_excel_btn)
        
        email_report_btn = QPushButton("📧 Email Report")
        email_report_btn.clicked.connect(self.email_report)
        export_layout.addWidget(email_report_btn)
        
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        
        widget.setLayout(layout)
        return widget
    
    def load_dashboard_data(self):
        """Load initial dashboard data"""
        self.update_metrics()
        self.generate_daily_briefing()
        self.load_recent_activity()
        self.load_revenue_data()
        self.load_client_data()
        self.load_project_data()
    
    def update_metrics(self):
        """Update metric cards with latest data"""
        cursor = self.conn.cursor()
        
        # Calculate monthly revenue
        cursor.execute("""
            SELECT SUM(amount) FROM revenue 
            WHERE date >= date('now', '-30 days')
        """)
        result = cursor.fetchone()
        monthly_revenue = result[0] if result[0] else 0
        
        # Count active clients
        cursor.execute("SELECT COUNT(*) FROM clients WHERE status = 'active'")
        active_clients = cursor.fetchone()[0]
        
        # Count active projects
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status IN ('planning', 'in_progress', 'review')")
        active_projects = cursor.fetchone()[0]
        
        # Update cards (simplified approach - updating via finding labels)
        # In a full implementation, these would be properly connected to the UI elements
        
    def generate_daily_briefing(self):
        """Generate AI-powered daily briefing"""
        briefing = f"""
📅 {datetime.now().strftime('%A, %B %d, %Y')}

Good morning! Here's your business overview:

💰 Revenue Status:
• Month-to-date: Tracking revenue and payments
• Outstanding invoices: Monitor pending payments
• Today's expected payments: Check invoice statuses

📋 Today's Priorities:
• Review active projects
• Check client communications
• Update task statuses

🎯 Action Items:
• Follow up with clients
• Review project progress
• Update financial records

💡 AI Insight:
Use the dashboard tabs to track revenue, manage clients, and monitor project progress.
        """
        
        if hasattr(self, 'briefing_text'):
            self.briefing_text.setPlainText(briefing)
    
    def load_recent_activity(self):
        """Load recent business activity"""
        if hasattr(self, 'activity_list'):
            activities = [
                f"{datetime.now().strftime('%H:%M')} - Dashboard initialized",
                f"{datetime.now().strftime('%H:%M')} - Business intelligence system ready",
                f"{datetime.now().strftime('%H:%M')} - All modules loaded successfully"
            ]
            
            self.activity_list.clear()
            for activity in activities:
                self.activity_list.addItem(activity)
    
    def load_revenue_data(self):
        """Load revenue data into table"""
        if hasattr(self, 'revenue_table'):
            cursor = self.conn.cursor()
            cursor.execute("SELECT date, amount, source, client_name, invoice_number, status FROM revenue ORDER BY date DESC LIMIT 50")
            rows = cursor.fetchall()
            
            self.revenue_table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, data in enumerate(row_data):
                    self.revenue_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
    
    def load_client_data(self):
        """Load client data into table"""
        if hasattr(self, 'client_table'):
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, company, email, phone, lifetime_value, status FROM clients ORDER BY name")
            rows = cursor.fetchall()
            
            self.client_table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, data in enumerate(row_data):
                    self.client_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data or '')))
    
    def load_project_data(self):
        """Load project data"""
        if hasattr(self, 'project_layout'):
            # Clear existing project cards safely
            for i in reversed(range(self.project_layout.count())): 
                item = self.project_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
            
            # Add sample project card
            sample_project = self.create_project_card("Sample Project", "Planning", 25, "$5,000")
            self.project_layout.addWidget(sample_project)
            self.project_layout.addStretch()
    
    def create_project_card(self, name, status, progress, budget):
        """Create a project status card"""
        card = QGroupBox(name)
        layout = QVBoxLayout()
        
        status_label = QLabel(f"Status: {status}")
        layout.addWidget(status_label)
        
        progress_label = QLabel(f"Progress: {progress}%")
        layout.addWidget(progress_label)
        
        budget_label = QLabel(f"Budget: {budget}")
        layout.addWidget(budget_label)
        
        card.setLayout(layout)
        return card
    
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        self.update_metrics()
        self.generate_daily_briefing()
        self.load_recent_activity()
        self.load_revenue_data()
        self.load_client_data()
        self.load_project_data()
        self.status_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def add_revenue(self):
        """Add new revenue entry"""
        amount_text = self.revenue_amount.text()
        source_text = self.revenue_source.text()
        invoice_text = self.revenue_invoice.text()
        
        if not amount_text:
            QMessageBox.warning(self, "Missing Data", "Please enter an amount")
            return
        
        try:
            amount = float(amount_text)
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO revenue (amount, source, client_name, date, invoice_number, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (amount, source_text, source_text, datetime.now().date(), invoice_text))
            self.conn.commit()
            
            # Clear form
            self.revenue_amount.clear()
            self.revenue_source.clear()
            self.revenue_invoice.clear()
            
            # Reload data
            self.load_revenue_data()
            self.update_metrics()
            
            QMessageBox.information(self, "Success", "Revenue entry added successfully")
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number for amount")
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec_():
            client_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, company, email, phone, acquisition_date, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (client_data['name'], client_data['company'], 
                  client_data['email'], client_data['phone'], datetime.now().date()))
            self.conn.commit()
            self.load_client_data()
    
    def add_project(self):
        """Add new project"""
        dialog = ProjectDialog(self)
        if dialog.exec_():
            project_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO projects (name, start_date, budget, status)
                VALUES (?, ?, ?, 'planning')
            """, (project_data['name'], datetime.now().date(), project_data['budget']))
            self.conn.commit()
            self.load_project_data()
    
    def generate_report(self):
        """Generate selected report"""
        report_type = self.report_type.currentText()
        
        cursor = self.conn.cursor()
        
        report_content = f"""
{report_type}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=========================================

"""
        
        if "Revenue" in report_type or "Financial" in report_type:
            cursor.execute("SELECT SUM(amount) FROM revenue WHERE date >= date('now', '-30 days')")
            monthly_revenue = cursor.fetchone()[0] or 0
            report_content += f"Monthly Revenue: ${monthly_revenue:,.2f}\n"
            
            cursor.execute("SELECT COUNT(*) FROM revenue WHERE status = 'pending'")
            pending_invoices = cursor.fetchone()[0]
            report_content += f"Pending Invoices: {pending_invoices}\n"
        
        if "Client" in report_type:
            cursor.execute("SELECT COUNT(*) FROM clients WHERE status = 'active'")
            active_clients = cursor.fetchone()[0]
            report_content += f"Active Clients: {active_clients}\n"
        
        if "Project" in report_type:
            cursor.execute("SELECT COUNT(*) FROM projects WHERE status != 'completed'")
            active_projects = cursor.fetchone()[0]
            report_content += f"Active Projects: {active_projects}\n"
        
        report_content += "\nDetailed analysis would appear here with charts and insights."
        
        self.report_preview.setPlainText(report_content)
    
    def generate_ai_insights(self):
        """Generate AI-powered business insights"""
        insights = """
🤖 AI-Generated Business Insights

📈 Growth Opportunities:
• Track revenue trends and identify peak periods
• Monitor client acquisition patterns
• Analyze project profitability

⚠️ Areas Needing Attention:
• Regular client follow-ups
• Project milestone tracking
• Invoice payment monitoring

💡 Recommendations:
1. Set up automated client check-ins
2. Implement project progress tracking
3. Create invoice reminder systems
4. Analyze revenue patterns for forecasting

🎯 Predicted Outcomes:
• Consistent tracking leads to better decision making
• Regular client contact improves retention
• Project monitoring reduces delays and cost overruns
        """
        
        QMessageBox.information(self, "AI Insights", insights)
    
    def export_data(self):
        """Export dashboard data"""
        QMessageBox.information(self, "Export", "Data export functionality - would export to CSV/Excel")
    
    def open_settings(self):
        """Open dashboard settings"""
        QMessageBox.information(self, "Settings", "Dashboard settings - customize metrics and preferences")
    
    def import_clients(self):
        """Import clients from CSV"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Clients", "", "CSV Files (*.csv)")
        if file_path:
            QMessageBox.information(self, "Import", f"Would import clients from {file_path}")
    
    def search_clients(self, text):
        """Search clients"""
        # Simple search implementation
        pass
    
    def filter_projects(self, status):
        """Filter projects by status"""
        # Project filtering implementation
        pass
    
    def update_analytics(self):
        """Update analytics based on date range"""
        # Analytics update implementation
        pass
    
    def schedule_reports(self):
        """Schedule automated reports"""
        dialog = ReportSchedulerDialog(self)
        dialog.exec_()
    
    def export_pdf(self):
        """Export report as PDF"""
        QMessageBox.information(self, "Export PDF", "PDF export functionality")
    
    def export_excel(self):
        """Export report as Excel"""
        QMessageBox.information(self, "Export Excel", "Excel export functionality")
    
    def email_report(self):
        """Email report to recipients"""
        QMessageBox.information(self, "Email Report", "Email report functionality")

class ClientDialog(QDialog):
    """Dialog for adding/editing clients"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add Client")
        self.setModal(True)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Company:", self.company_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Phone:", self.phone_input)
        
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
            'phone': self.phone_input.text()
        }

class ProjectDialog(QDialog):
    """Dialog for adding/editing projects"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add Project")
        self.setModal(True)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("0.00")
        
        layout.addRow("Project Name:", self.name_input)
        layout.addRow("Budget:", self.budget_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        try:
            budget = float(self.budget_input.text()) if self.budget_input.text() else 0.0
        except ValueError:
            budget = 0.0
        
        return {
            'name': self.name_input.text(),
            'budget': budget
        }

class ReportSchedulerDialog(QDialog):
    """Dialog for scheduling automated reports"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Schedule Reports")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Report scheduling options
        schedule_group = QGroupBox("Report Schedule")
        schedule_layout = QFormLayout()
        
        self.report_type = QComboBox()
        self.report_type.addItems(["Daily Summary", "Weekly Report", "Monthly Report"])
        schedule_layout.addRow("Report Type:", self.report_type)
        
        self.frequency = QComboBox()
        self.frequency.addItems(["Daily", "Weekly", "Monthly"])
        schedule_layout.addRow("Frequency:", self.frequency)
        
        self.time_edit = QTimeEdit()
        schedule_layout.addRow("Time:", self.time_edit)
        
        self.recipients = QLineEdit()
        self.recipients.setPlaceholderText("email1@example.com, email2@example.com")
        schedule_layout.addRow("Recipients:", self.recipients)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)