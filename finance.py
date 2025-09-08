"""
Financial Management Module for Westfall Assistant
Designed specifically for entrepreneurs and business owners
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
import calendar

# Optional dependencies with fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from util.app_theme import AppTheme
    HAS_THEME = True
except ImportError:
    HAS_THEME = False
    class AppTheme:
        BACKGROUND = "#000000"
        SECONDARY_BG = "#1a1a1a"
        PRIMARY_COLOR = "#ff0000"
        TEXT_PRIMARY = "#ffffff"
        TEXT_SECONDARY = "#cccccc"

try:
    from util.error_handler import get_error_handler
    HAS_ERROR_HANDLER = True
except ImportError:
    HAS_ERROR_HANDLER = False

class FinanceWindow(QMainWindow):
    """Main finance management window for entrepreneurs"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Management - Westfall Assistant")
        self.setMinimumSize(1000, 700)
        
        # Initialize database and error handler
        self.init_database()
        self.error_handler = get_error_handler(self) if HAS_ERROR_HANDLER else None
        
        # Initialize UI
        self.init_ui()
        self.load_data()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(300000)  # 5 minutes

    def init_database(self):
        """Initialize finance database with comprehensive tables"""
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/finance.db')
        cursor = self.conn.cursor()
        
        # Invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                client_name TEXT NOT NULL,
                client_email TEXT,
                amount DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                currency TEXT DEFAULT 'USD',
                date_created DATE NOT NULL,
                date_due DATE NOT NULL,
                date_paid DATE,
                status TEXT DEFAULT 'draft',
                description TEXT,
                notes TEXT,
                payment_terms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                vendor TEXT,
                date DATE NOT NULL,
                receipt_path TEXT,
                tax_deductible BOOLEAN DEFAULT 1,
                project_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Projects table for time tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                client_name TEXT,
                hourly_rate DECIMAL(10,2),
                total_budget DECIMAL(10,2),
                status TEXT DEFAULT 'active',
                start_date DATE,
                end_date DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Time tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                description TEXT,
                hours DECIMAL(5,2) NOT NULL,
                hourly_rate DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                date DATE NOT NULL,
                billable BOOLEAN DEFAULT 1,
                invoiced BOOLEAN DEFAULT 0,
                invoice_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Financial goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT NOT NULL,
                target_amount DECIMAL(10,2) NOT NULL,
                current_amount DECIMAL(10,2) DEFAULT 0,
                target_date DATE,
                category TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply theme if available
        if HAS_THEME:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {AppTheme.BACKGROUND};
                    color: {AppTheme.TEXT_PRIMARY};
                }}
                QTabWidget::pane {{
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                    background-color: {AppTheme.SECONDARY_BG};
                }}
                QTabBar::tab {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    padding: 8px 16px;
                    margin-right: 2px;
                }}
                QTabBar::tab:selected {{
                    background-color: {AppTheme.PRIMARY_COLOR};
                    color: white;
                }}
            """)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Tab widget for different finance sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_invoices_tab()
        self.create_expenses_tab()
        self.create_time_tracking_tab()
        self.create_reports_tab()
        
        # Status bar
        self.statusBar().showMessage("Financial Management System Ready")

    def create_header(self):
        """Create the header section with key metrics"""
        header_widget = QWidget()
        if HAS_THEME:
            header_widget.setStyleSheet(f"background-color: {AppTheme.SECONDARY_BG}; border-bottom: 2px solid {AppTheme.PRIMARY_COLOR};")
        
        layout = QHBoxLayout(header_widget)
        
        # Title
        title_label = QLabel("💰 Financial Management")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        if HAS_THEME:
            title_label.setStyleSheet(f"color: {AppTheme.PRIMARY_COLOR};")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Quick stats
        self.revenue_label = QLabel("Revenue: $0")
        self.expenses_label = QLabel("Expenses: $0")
        self.profit_label = QLabel("Profit: $0")
        
        for label in [self.revenue_label, self.expenses_label, self.profit_label]:
            label.setFont(QFont("Arial", 12))
            if HAS_THEME:
                label.setStyleSheet(f"color: {AppTheme.TEXT_PRIMARY}; padding: 5px;")
            layout.addWidget(label)
        
        return header_widget

    def create_dashboard_tab(self):
        """Create the financial dashboard tab"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Cards layout
        cards_layout = QHBoxLayout()
        
        # Revenue card
        revenue_card = self.create_metric_card("Monthly Revenue", "$0", "#00cc00")
        cards_layout.addWidget(revenue_card)
        
        # Expenses card
        expenses_card = self.create_metric_card("Monthly Expenses", "$0", "#ff6600")
        cards_layout.addWidget(expenses_card)
        
        # Profit card
        profit_card = self.create_metric_card("Net Profit", "$0", AppTheme.PRIMARY_COLOR if HAS_THEME else "#ff0000")
        cards_layout.addWidget(profit_card)
        
        # Outstanding invoices card
        outstanding_card = self.create_metric_card("Outstanding", "$0", "#ffcc00")
        cards_layout.addWidget(outstanding_card)
        
        layout.addLayout(cards_layout)
        
        # Recent transactions
        recent_group = QGroupBox("Recent Transactions")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_transactions_list = QListWidget()
        if HAS_THEME:
            self.recent_transactions_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                }}
            """)
        recent_layout.addWidget(self.recent_transactions_list)
        
        layout.addWidget(recent_group)
        
        # Store card widgets for updates
        self.revenue_card = revenue_card
        self.expenses_card = expenses_card
        self.profit_card = profit_card
        self.outstanding_card = outstanding_card
        
        self.tab_widget.addTab(dashboard_widget, "📊 Dashboard")

    def create_metric_card(self, title, value, color):
        """Create a metric card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setMinimumHeight(100)
        
        if HAS_THEME:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {AppTheme.SECONDARY_BG};
                    border: 2px solid {color};
                    border-radius: 8px;
                    margin: 5px;
                }}
            """)
        
        layout = QVBoxLayout(card)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 10))
        if HAS_THEME:
            title_label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; border: none;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(value_label)
        
        # Store labels for updating
        card.title_label = title_label
        card.value_label = value_label
        
        return card

    def create_invoices_tab(self):
        """Create the invoices management tab"""
        invoices_widget = QWidget()
        layout = QVBoxLayout(invoices_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        new_invoice_btn = QPushButton("➕ New Invoice")
        new_invoice_btn.clicked.connect(self.create_new_invoice)
        toolbar.addWidget(new_invoice_btn)
        
        edit_invoice_btn = QPushButton("✏️ Edit Invoice")
        edit_invoice_btn.clicked.connect(self.edit_invoice)
        toolbar.addWidget(edit_invoice_btn)
        
        delete_invoice_btn = QPushButton("🗑️ Delete Invoice")
        delete_invoice_btn.clicked.connect(self.delete_invoice)
        toolbar.addWidget(delete_invoice_btn)
        
        toolbar.addStretch()
        
        # Status filter
        status_filter = QComboBox()
        status_filter.addItems(["All Invoices", "Draft", "Sent", "Paid", "Overdue"])
        status_filter.currentTextChanged.connect(self.filter_invoices)
        toolbar.addWidget(QLabel("Filter:"))
        toolbar.addWidget(status_filter)
        
        layout.addLayout(toolbar)
        
        # Invoices table
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(8)
        self.invoices_table.setHorizontalHeaderLabels([
            "Invoice #", "Client", "Amount", "Due Date", "Status", "Created", "Paid Date", "Actions"
        ])
        
        if HAS_THEME:
            self.invoices_table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    gridline-color: {AppTheme.PRIMARY_COLOR};
                }}
                QHeaderView::section {{
                    background-color: {AppTheme.PRIMARY_COLOR};
                    color: white;
                    font-weight: bold;
                    padding: 6px;
                }}
            """)
        
        layout.addWidget(self.invoices_table)
        
        self.tab_widget.addTab(invoices_widget, "📄 Invoices")

    def create_expenses_tab(self):
        """Create the expenses tracking tab"""
        expenses_widget = QWidget()
        layout = QVBoxLayout(expenses_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        new_expense_btn = QPushButton("➕ Add Expense")
        new_expense_btn.clicked.connect(self.add_expense)
        toolbar.addWidget(new_expense_btn)
        
        import_expenses_btn = QPushButton("📁 Import CSV")
        import_expenses_btn.clicked.connect(self.import_expenses)
        toolbar.addWidget(import_expenses_btn)
        
        toolbar.addStretch()
        
        # Category filter
        category_filter = QComboBox()
        category_filter.addItems([
            "All Categories", "Office Supplies", "Software", "Hardware", 
            "Marketing", "Travel", "Meals", "Education", "Professional Services"
        ])
        category_filter.currentTextChanged.connect(self.filter_expenses)
        toolbar.addWidget(QLabel("Category:"))
        toolbar.addWidget(category_filter)
        
        layout.addLayout(toolbar)
        
        # Expenses table
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(7)
        self.expenses_table.setHorizontalHeaderLabels([
            "Date", "Description", "Category", "Vendor", "Amount", "Deductible", "Receipt"
        ])
        
        if HAS_THEME:
            self.expenses_table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    gridline-color: {AppTheme.PRIMARY_COLOR};
                }}
                QHeaderView::section {{
                    background-color: {AppTheme.PRIMARY_COLOR};
                    color: white;
                    font-weight: bold;
                    padding: 6px;
                }}
            """)
        
        layout.addWidget(self.expenses_table)
        
        self.tab_widget.addTab(expenses_widget, "💸 Expenses")

    def create_time_tracking_tab(self):
        """Create the time tracking tab"""
        time_widget = QWidget()
        layout = QVBoxLayout(time_widget)
        
        # Active timer section
        timer_group = QGroupBox("Time Tracker")
        timer_layout = QHBoxLayout(timer_group)
        
        # Project selection
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(200)
        timer_layout.addWidget(QLabel("Project:"))
        timer_layout.addWidget(self.project_combo)
        
        # Timer display
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setFont(QFont("Arial", 20, QFont.Bold))
        if HAS_THEME:
            self.timer_display.setStyleSheet(f"color: {AppTheme.PRIMARY_COLOR};")
        timer_layout.addWidget(self.timer_display)
        
        # Timer controls
        self.start_timer_btn = QPushButton("▶️ Start")
        self.start_timer_btn.clicked.connect(self.start_timer)
        timer_layout.addWidget(self.start_timer_btn)
        
        self.stop_timer_btn = QPushButton("⏹️ Stop")
        self.stop_timer_btn.clicked.connect(self.stop_timer)
        self.stop_timer_btn.setEnabled(False)
        timer_layout.addWidget(self.stop_timer_btn)
        
        layout.addWidget(timer_group)
        
        # Time entries table
        entries_group = QGroupBox("Time Entries")
        entries_layout = QVBoxLayout(entries_group)
        
        # Toolbar for time entries
        entries_toolbar = QHBoxLayout()
        add_entry_btn = QPushButton("➕ Manual Entry")
        add_entry_btn.clicked.connect(self.add_manual_time_entry)
        entries_toolbar.addWidget(add_entry_btn)
        
        generate_invoice_btn = QPushButton("📄 Generate Invoice")
        generate_invoice_btn.clicked.connect(self.generate_invoice_from_time)
        entries_toolbar.addWidget(generate_invoice_btn)
        
        entries_toolbar.addStretch()
        entries_layout.addLayout(entries_toolbar)
        
        # Time entries table
        self.time_entries_table = QTableWidget()
        self.time_entries_table.setColumnCount(7)
        self.time_entries_table.setHorizontalHeaderLabels([
            "Date", "Project", "Description", "Hours", "Rate", "Amount", "Billable"
        ])
        
        if HAS_THEME:
            self.time_entries_table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    gridline-color: {AppTheme.PRIMARY_COLOR};
                }}
                QHeaderView::section {{
                    background-color: {AppTheme.PRIMARY_COLOR};
                    color: white;
                    font-weight: bold;
                    padding: 6px;
                }}
            """)
        
        entries_layout.addWidget(self.time_entries_table)
        layout.addWidget(entries_group)
        
        # Timer state
        self.timer_running = False
        self.timer_start_time = None
        self.timer_seconds = 0
        
        # Update timer display
        self.timer_update_timer = QTimer()
        self.timer_update_timer.timeout.connect(self.update_timer_display)
        
        self.tab_widget.addTab(time_widget, "⏱️ Time Tracking")

    def create_reports_tab(self):
        """Create the financial reports tab"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Report generation toolbar
        toolbar = QHBoxLayout()
        
        # Date range selection
        toolbar.addWidget(QLabel("From:"))
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.report_start_date.setCalendarPopup(True)
        toolbar.addWidget(self.report_start_date)
        
        toolbar.addWidget(QLabel("To:"))
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        toolbar.addWidget(self.report_end_date)
        
        # Report type
        report_type = QComboBox()
        report_type.addItems([
            "Profit & Loss", "Revenue Summary", "Expense Report", 
            "Tax Summary", "Client Report", "Project Report"
        ])
        toolbar.addWidget(QLabel("Report:"))
        toolbar.addWidget(report_type)
        
        # Generate button
        generate_btn = QPushButton("📊 Generate Report")
        generate_btn.clicked.connect(lambda: self.generate_report(report_type.currentText()))
        toolbar.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton("💾 Export PDF")
        export_btn.clicked.connect(self.export_report)
        toolbar.addWidget(export_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Report display area
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        if HAS_THEME:
            self.report_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                    font-family: 'Courier New', monospace;
                }}
            """)
        layout.addWidget(self.report_text)
        
        self.tab_widget.addTab(reports_widget, "📈 Reports")

    def load_data(self):
        """Load and refresh all financial data"""
        self.load_invoices()
        self.load_expenses()
        self.load_time_entries()
        self.load_projects()
        self.update_dashboard_metrics()
        self.load_recent_transactions()

    def load_invoices(self):
        """Load invoices into the table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT invoice_number, client_name, total_amount, date_due, 
                   status, date_created, date_paid, id
            FROM invoices 
            ORDER BY date_created DESC
        """)
        
        invoices = cursor.fetchall()
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            for col, value in enumerate(invoice[:-1]):  # Exclude id
                if col == 2:  # Amount column
                    item = QTableWidgetItem(f"${value:.2f}")
                else:
                    item = QTableWidgetItem(str(value) if value else "")
                self.invoices_table.setItem(row, col, item)
            
            # Actions column
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            view_btn = QPushButton("👁️")
            view_btn.setMaximumWidth(30)
            view_btn.clicked.connect(lambda checked, id=invoice[-1]: self.view_invoice(id))
            actions_layout.addWidget(view_btn)
            
            mark_paid_btn = QPushButton("✅")
            mark_paid_btn.setMaximumWidth(30)
            mark_paid_btn.clicked.connect(lambda checked, id=invoice[-1]: self.mark_invoice_paid(id))
            actions_layout.addWidget(mark_paid_btn)
            
            self.invoices_table.setCellWidget(row, 7, actions_widget)

    def load_expenses(self):
        """Load expenses into the table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT date, description, category, vendor, amount, tax_deductible, receipt_path
            FROM expenses 
            ORDER BY date DESC
        """)
        
        expenses = cursor.fetchall()
        self.expenses_table.setRowCount(len(expenses))
        
        for row, expense in enumerate(expenses):
            for col, value in enumerate(expense):
                if col == 4:  # Amount column
                    item = QTableWidgetItem(f"${value:.2f}")
                elif col == 5:  # Tax deductible
                    item = QTableWidgetItem("Yes" if value else "No")
                elif col == 6:  # Receipt
                    item = QTableWidgetItem("📎" if value else "")
                else:
                    item = QTableWidgetItem(str(value) if value else "")
                self.expenses_table.setItem(row, col, item)

    def load_time_entries(self):
        """Load time entries into the table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT te.date, p.name, te.description, te.hours, 
                   te.hourly_rate, te.total_amount, te.billable
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            ORDER BY te.date DESC
        """)
        
        entries = cursor.fetchall()
        self.time_entries_table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            for col, value in enumerate(entry):
                if col in [3, 4, 5]:  # Hours, rate, amount
                    item = QTableWidgetItem(f"{value:.2f}")
                elif col == 6:  # Billable
                    item = QTableWidgetItem("Yes" if value else "No")
                else:
                    item = QTableWidgetItem(str(value) if value else "")
                self.time_entries_table.setItem(row, col, item)

    def load_projects(self):
        """Load projects into the combo box"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM projects WHERE status = 'active'")
        projects = cursor.fetchall()
        
        self.project_combo.clear()
        for project_id, name in projects:
            self.project_combo.addItem(name, project_id)

    def update_dashboard_metrics(self):
        """Update the dashboard metric cards"""
        cursor = self.conn.cursor()
        
        # Current month revenue
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) 
            FROM invoices 
            WHERE status = 'paid' AND date_paid >= date('now', 'start of month')
        """)
        monthly_revenue = cursor.fetchone()[0]
        
        # Current month expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM expenses 
            WHERE date >= date('now', 'start of month')
        """)
        monthly_expenses = cursor.fetchone()[0]
        
        # Outstanding invoices
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) 
            FROM invoices 
            WHERE status IN ('sent', 'overdue')
        """)
        outstanding = cursor.fetchone()[0]
        
        # Calculate profit
        profit = monthly_revenue - monthly_expenses
        
        # Update cards
        self.revenue_card.value_label.setText(f"${monthly_revenue:.2f}")
        self.expenses_card.value_label.setText(f"${monthly_expenses:.2f}")
        self.profit_card.value_label.setText(f"${profit:.2f}")
        self.outstanding_card.value_label.setText(f"${outstanding:.2f}")
        
        # Update header
        self.revenue_label.setText(f"Revenue: ${monthly_revenue:.2f}")
        self.expenses_label.setText(f"Expenses: ${monthly_expenses:.2f}")
        self.profit_label.setText(f"Profit: ${profit:.2f}")

    def load_recent_transactions(self):
        """Load recent transactions for dashboard"""
        self.recent_transactions_list.clear()
        
        cursor = self.conn.cursor()
        
        # Recent invoices
        cursor.execute("""
            SELECT 'Invoice', invoice_number, client_name, total_amount, date_created
            FROM invoices 
            ORDER BY date_created DESC 
            LIMIT 5
        """)
        recent_invoices = cursor.fetchall()
        
        # Recent expenses
        cursor.execute("""
            SELECT 'Expense', description, vendor, amount, date
            FROM expenses 
            ORDER BY date DESC 
            LIMIT 5
        """)
        recent_expenses = cursor.fetchall()
        
        # Combine and sort
        all_transactions = recent_invoices + recent_expenses
        all_transactions.sort(key=lambda x: x[4], reverse=True)
        
        for trans in all_transactions[:10]:
            if trans[0] == 'Invoice':
                text = f"📄 Invoice {trans[1]} - {trans[2]} - ${trans[3]:.2f}"
            else:
                text = f"💸 {trans[1]} - {trans[2]} - ${trans[3]:.2f}"
            self.recent_transactions_list.addItem(text)

    # Invoice Management Methods
    def create_new_invoice(self):
        """Create a new invoice"""
        dialog = InvoiceDialog(self)
        if dialog.exec_():
            self.load_invoices()
            self.update_dashboard_metrics()

    def edit_invoice(self):
        """Edit selected invoice"""
        current_row = self.invoices_table.currentRow()
        if current_row >= 0:
            # Implementation for editing invoice
            QMessageBox.information(self, "Edit Invoice", "Invoice editing feature coming soon!")

    def delete_invoice(self):
        """Delete selected invoice"""
        current_row = self.invoices_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "Delete Invoice", 
                                       "Are you sure you want to delete this invoice?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Implementation for deleting invoice
                QMessageBox.information(self, "Delete Invoice", "Invoice deletion feature coming soon!")

    def mark_invoice_paid(self, invoice_id):
        """Mark an invoice as paid"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE invoices 
            SET status = 'paid', date_paid = date('now') 
            WHERE id = ?
        """, (invoice_id,))
        self.conn.commit()
        
        self.load_invoices()
        self.update_dashboard_metrics()
        QMessageBox.information(self, "Invoice Updated", "Invoice marked as paid!")

    def view_invoice(self, invoice_id):
        """View invoice details"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        invoice = cursor.fetchone()
        
        if invoice:
            # Create a simple invoice view dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Invoice {invoice[1]}")
            dialog.setMinimumSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Invoice details
            details = f"""
            Invoice Number: {invoice[1]}
            Client: {invoice[2]}
            Amount: ${invoice[4]:.2f}
            Tax: ${invoice[5]:.2f}
            Total: ${invoice[6]:.2f}
            Created: {invoice[8]}
            Due: {invoice[9]}
            Status: {invoice[11]}
            Description: {invoice[12] or 'N/A'}
            """
            
            details_label = QLabel(details)
            layout.addWidget(details_label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec_()

    def filter_invoices(self, status):
        """Filter invoices by status"""
        # Implementation for filtering invoices
        self.load_invoices()  # For now, just reload all

    # Expense Management Methods
    def add_expense(self):
        """Add a new expense"""
        dialog = ExpenseDialog(self)
        if dialog.exec_():
            self.load_expenses()
            self.update_dashboard_metrics()

    def import_expenses(self):
        """Import expenses from CSV"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Expenses", "", "CSV Files (*.csv)")
        if file_path and HAS_PANDAS:
            try:
                df = pd.read_csv(file_path)
                # Implementation for CSV import
                QMessageBox.information(self, "Import", f"CSV import feature coming soon!")
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_file_error(e, "Failed to import CSV file")
                else:
                    QMessageBox.warning(self, "Import Error", f"Failed to import: {e}")

    def filter_expenses(self, category):
        """Filter expenses by category"""
        # Implementation for filtering expenses
        self.load_expenses()  # For now, just reload all

    # Time Tracking Methods
    def start_timer(self):
        """Start the time timer"""
        if self.project_combo.currentData():
            self.timer_running = True
            self.timer_start_time = datetime.now()
            self.timer_seconds = 0
            self.timer_update_timer.start(1000)  # Update every second
            
            self.start_timer_btn.setEnabled(False)
            self.stop_timer_btn.setEnabled(True)

    def stop_timer(self):
        """Stop the time timer and save entry"""
        if self.timer_running:
            self.timer_running = False
            self.timer_update_timer.stop()
            
            # Calculate hours
            elapsed_time = datetime.now() - self.timer_start_time
            hours = elapsed_time.total_seconds() / 3600
            
            # Open dialog to save time entry
            dialog = TimeEntryDialog(self, self.project_combo.currentData(), 
                                   self.project_combo.currentText(), hours)
            if dialog.exec_():
                self.load_time_entries()
                self.update_dashboard_metrics()
            
            self.start_timer_btn.setEnabled(True)
            self.stop_timer_btn.setEnabled(False)
            self.timer_display.setText("00:00:00")

    def update_timer_display(self):
        """Update the timer display"""
        if self.timer_running:
            elapsed = datetime.now() - self.timer_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.timer_display.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def add_manual_time_entry(self):
        """Add a manual time entry"""
        dialog = TimeEntryDialog(self)
        if dialog.exec_():
            self.load_time_entries()
            self.update_dashboard_metrics()

    def generate_invoice_from_time(self):
        """Generate invoice from time entries"""
        QMessageBox.information(self, "Generate Invoice", 
                              "Time-based invoice generation feature coming soon!")

    # Report Methods
    def generate_report(self, report_type):
        """Generate financial report"""
        start_date = self.report_start_date.date().toPyDate()
        end_date = self.report_end_date.date().toPyDate()
        
        if report_type == "Profit & Loss":
            report = self.generate_profit_loss_report(start_date, end_date)
        elif report_type == "Revenue Summary":
            report = self.generate_revenue_report(start_date, end_date)
        elif report_type == "Expense Report":
            report = self.generate_expense_report(start_date, end_date)
        else:
            report = f"{report_type} report generation coming soon!"
        
        self.report_text.setPlainText(report)

    def generate_profit_loss_report(self, start_date, end_date):
        """Generate profit and loss report"""
        cursor = self.conn.cursor()
        
        # Revenue
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices 
            WHERE status = 'paid' AND date_paid BETWEEN ? AND ?
        """, (start_date, end_date))
        revenue = cursor.fetchone()[0]
        
        # Expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses 
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        expenses = cursor.fetchone()[0]
        
        profit = revenue - expenses
        
        report = f"""
PROFIT & LOSS STATEMENT
Period: {start_date} to {end_date}

REVENUE
Total Revenue: ${revenue:.2f}

EXPENSES
Total Expenses: ${expenses:.2f}

NET PROFIT: ${profit:.2f}
Profit Margin: {(profit/revenue*100 if revenue > 0 else 0):.1f}%
        """
        
        return report.strip()

    def generate_revenue_report(self, start_date, end_date):
        """Generate revenue summary report"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT client_name, SUM(total_amount) as total
            FROM invoices 
            WHERE status = 'paid' AND date_paid BETWEEN ? AND ?
            GROUP BY client_name
            ORDER BY total DESC
        """, (start_date, end_date))
        
        client_revenue = cursor.fetchall()
        
        report = f"REVENUE SUMMARY\nPeriod: {start_date} to {end_date}\n\n"
        report += "CLIENT BREAKDOWN:\n"
        report += "-" * 40 + "\n"
        
        total = 0
        for client, amount in client_revenue:
            report += f"{client:<25} ${amount:>10.2f}\n"
            total += amount
        
        report += "-" * 40 + "\n"
        report += f"{'TOTAL':<25} ${total:>10.2f}\n"
        
        return report

    def generate_expense_report(self, start_date, end_date):
        """Generate expense report"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses 
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        """, (start_date, end_date))
        
        expense_categories = cursor.fetchall()
        
        report = f"EXPENSE REPORT\nPeriod: {start_date} to {end_date}\n\n"
        report += "CATEGORY BREAKDOWN:\n"
        report += "-" * 40 + "\n"
        
        total = 0
        for category, amount in expense_categories:
            report += f"{category:<25} ${amount:>10.2f}\n"
            total += amount
        
        report += "-" * 40 + "\n"
        report += f"{'TOTAL':<25} ${total:>10.2f}\n"
        
        # Tax deductible expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses 
            WHERE date BETWEEN ? AND ? AND tax_deductible = 1
        """, (start_date, end_date))
        
        deductible = cursor.fetchone()[0]
        report += f"\nTax Deductible: ${deductible:.2f}"
        
        return report

    def export_report(self):
        """Export current report to PDF"""
        QMessageBox.information(self, "Export Report", "PDF export feature coming soon!")

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        self.load_data()
        self.statusBar().showMessage("Dashboard refreshed", 2000)


class InvoiceDialog(QDialog):
    """Dialog for creating/editing invoices"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("New Invoice")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form fields
        form_layout = QFormLayout()
        
        self.client_name = QLineEdit()
        form_layout.addRow("Client Name:", self.client_name)
        
        self.client_email = QLineEdit()
        form_layout.addRow("Client Email:", self.client_email)
        
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 999999)
        self.amount.setDecimals(2)
        form_layout.addRow("Amount:", self.amount)
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(0)
        self.tax_rate.setSuffix("%")
        form_layout.addRow("Tax Rate:", self.tax_rate)
        
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(30))
        self.due_date.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date)
        
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Invoice")
        save_btn.clicked.connect(self.save_invoice)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def save_invoice(self):
        """Save the invoice to database"""
        if not self.client_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Client name is required!")
            return
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        # Calculate tax and total
        amount = self.amount.value()
        tax_amount = amount * (self.tax_rate.value() / 100)
        total_amount = amount + tax_amount
        
        # Save to database
        cursor = self.parent_window.conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, client_name, client_email, amount, 
                tax_amount, total_amount, date_created, date_due, 
                status, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number, self.client_name.text(), self.client_email.text(),
            amount, tax_amount, total_amount, date.today(), 
            self.due_date.date().toPyDate(), 'draft', self.description.toPlainText()
        ))
        
        self.parent_window.conn.commit()
        self.accept()


class ExpenseDialog(QDialog):
    """Dialog for adding expenses"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Add Expense")
        self.setMinimumSize(400, 350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form fields
        form_layout = QFormLayout()
        
        self.description = QLineEdit()
        form_layout.addRow("Description:", self.description)
        
        self.category = QComboBox()
        self.category.addItems([
            "Office Supplies", "Software", "Hardware", "Marketing", 
            "Travel", "Meals", "Education", "Professional Services", "Other"
        ])
        form_layout.addRow("Category:", self.category)
        
        self.vendor = QLineEdit()
        form_layout.addRow("Vendor:", self.vendor)
        
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 999999)
        self.amount.setDecimals(2)
        form_layout.addRow("Amount:", self.amount)
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date)
        
        self.tax_deductible = QCheckBox()
        self.tax_deductible.setChecked(True)
        form_layout.addRow("Tax Deductible:", self.tax_deductible)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Expense")
        save_btn.clicked.connect(self.save_expense)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def save_expense(self):
        """Save the expense to database"""
        if not self.description.text().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required!")
            return
        
        cursor = self.parent_window.conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (
                description, category, vendor, amount, date, 
                tax_deductible, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.description.text(), self.category.currentText(),
            self.vendor.text(), self.amount.value(), 
            self.date.date().toPyDate(), self.tax_deductible.isChecked(),
            self.notes.toPlainText()
        ))
        
        self.parent_window.conn.commit()
        self.accept()


class TimeEntryDialog(QDialog):
    """Dialog for adding time entries"""
    
    def __init__(self, parent, project_id=None, project_name="", hours=0):
        super().__init__(parent)
        self.parent_window = parent
        self.project_id = project_id
        self.setWindowTitle("Time Entry")
        self.setMinimumSize(400, 300)
        self.init_ui()
        
        if project_name:
            # Find and select the project
            index = self.project_combo.findText(project_name)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        
        if hours > 0:
            self.hours.setValue(hours)

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form fields
        form_layout = QFormLayout()
        
        self.project_combo = QComboBox()
        self.load_projects()
        form_layout.addRow("Project:", self.project_combo)
        
        self.description = QLineEdit()
        form_layout.addRow("Description:", self.description)
        
        self.hours = QDoubleSpinBox()
        self.hours.setRange(0, 24)
        self.hours.setDecimals(2)
        self.hours.setSuffix(" hours")
        form_layout.addRow("Hours:", self.hours)
        
        self.hourly_rate = QDoubleSpinBox()
        self.hourly_rate.setRange(0, 9999)
        self.hourly_rate.setDecimals(2)
        self.hourly_rate.setPrefix("$")
        self.hourly_rate.setValue(100.00)  # Default rate
        form_layout.addRow("Hourly Rate:", self.hourly_rate)
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date)
        
        self.billable = QCheckBox()
        self.billable.setChecked(True)
        form_layout.addRow("Billable:", self.billable)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Entry")
        save_btn.clicked.connect(self.save_time_entry)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def load_projects(self):
        """Load projects into combo box"""
        cursor = self.parent_window.conn.cursor()
        cursor.execute("SELECT id, name FROM projects WHERE status = 'active'")
        projects = cursor.fetchall()
        
        for project_id, name in projects:
            self.project_combo.addItem(name, project_id)

    def save_time_entry(self):
        """Save the time entry to database"""
        project_id = self.project_combo.currentData()
        if not project_id:
            QMessageBox.warning(self, "Validation Error", "Please select a project!")
            return
        
        hours = self.hours.value()
        rate = self.hourly_rate.value()
        total = hours * rate
        
        cursor = self.parent_window.conn.cursor()
        cursor.execute("""
            INSERT INTO time_entries (
                project_id, description, hours, hourly_rate, 
                total_amount, date, billable
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, self.description.text(), hours, rate, total,
            self.date.date().toPyDate(), self.billable.isChecked()
        ))
        
        self.parent_window.conn.commit()
        self.accept()


# Widget wrapper for main application integration
class FinanceWidget(QWidget):
    """Widget wrapper for the finance window"""
    
    def __init__(self):
        super().__init__()
        self.finance_window = FinanceWindow()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.finance_window.centralWidget())


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Apply theme if available
    if HAS_THEME:
        AppTheme.apply_to_application()
    
    window = FinanceWindow()
    window.show()
    
    sys.exit(app.exec_())