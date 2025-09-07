"""
KPI Tracker for Business Intelligence
"""

import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import os

class KPITracker(QWidget):
    """Track and visualize Key Performance Indicators"""
    
    def __init__(self):
        super().__init__()
        self.init_db()
        self.init_ui()
    
    def init_db(self):
        """Initialize KPI database"""
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/business_metrics.db')
        cursor = self.conn.cursor()
        
        # KPI definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpi_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                target_value REAL,
                unit TEXT,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # KPI measurements table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpi_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kpi_id INTEGER,
                value REAL NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                FOREIGN KEY (kpi_id) REFERENCES kpi_definitions (id)
            )
        ''')
        
        self.conn.commit()
        self.populate_default_kpis()
    
    def populate_default_kpis(self):
        """Populate default KPIs for small businesses"""
        default_kpis = [
            ("Monthly Revenue", "Financial", 10000, "$", "Total monthly revenue"),
            ("Customer Acquisition Cost", "Marketing", 100, "$", "Cost to acquire a new customer"),
            ("Customer Lifetime Value", "Marketing", 1000, "$", "Total value of a customer"),
            ("Monthly Active Clients", "Business", 50, "count", "Number of active clients"),
            ("Project Completion Rate", "Operations", 90, "%", "Percentage of projects completed on time"),
            ("Invoice Collection Time", "Financial", 30, "days", "Average days to collect payment"),
            ("Lead Conversion Rate", "Sales", 20, "%", "Percentage of leads that become customers"),
            ("Client Satisfaction Score", "Quality", 4.5, "rating", "Average client satisfaction rating")
        ]
        
        cursor = self.conn.cursor()
        for kpi in default_kpis:
            cursor.execute("""
                INSERT OR IGNORE INTO kpi_definitions (name, category, target_value, unit, description)
                VALUES (?, ?, ?, ?, ?)
            """, kpi)
        self.conn.commit()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("KPI Tracker")
        self.setGeometry(100, 100, 1000, 700)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("📊 Key Performance Indicators")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # KPI tabs
        tabs = QTabWidget()
        
        # Dashboard tab
        dashboard_tab = self.create_dashboard_tab()
        tabs.addTab(dashboard_tab, "📈 Dashboard")
        
        # Manage KPIs tab
        manage_tab = self.create_manage_tab()
        tabs.addTab(manage_tab, "⚙️ Manage KPIs")
        
        # Add measurement tab
        measurement_tab = self.create_measurement_tab()
        tabs.addTab(measurement_tab, "➕ Add Measurement")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def create_dashboard_tab(self):
        """Create KPI dashboard"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # KPI overview cards
        cards_layout = QGridLayout()
        
        # Load and display KPIs
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, target_value, unit FROM kpi_definitions WHERE is_active = 1")
        kpis = cursor.fetchall()
        
        row, col = 0, 0
        for kpi_id, name, target, unit in kpis:
            # Get latest measurement
            cursor.execute("""
                SELECT value, date FROM kpi_measurements 
                WHERE kpi_id = ? ORDER BY date DESC LIMIT 1
            """, (kpi_id,))
            measurement = cursor.fetchone()
            
            current_value = measurement[0] if measurement else 0
            last_date = measurement[1] if measurement else "No data"
            
            card = self.create_kpi_card(name, current_value, target, unit, last_date)
            cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        layout.addLayout(cards_layout)
        
        # Trend chart placeholder
        trends_group = QGroupBox("📈 Trends")
        trends_layout = QVBoxLayout()
        trends_text = QTextEdit()
        trends_text.setPlainText("KPI trend charts would appear here\n(Install matplotlib/plotly for visualizations)")
        trends_text.setMaximumHeight(200)
        trends_layout.addWidget(trends_text)
        trends_group.setLayout(trends_layout)
        layout.addWidget(trends_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_kpi_card(self, name, current, target, unit, last_update):
        """Create a KPI display card"""
        card = QGroupBox(name)
        card.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            QGroupBox::title {
                font-weight: bold;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Current value
        if unit == "$":
            current_text = f"${current:,.2f}"
            target_text = f"Target: ${target:,.2f}"
        elif unit == "%":
            current_text = f"{current:.1f}%"
            target_text = f"Target: {target:.1f}%"
        else:
            current_text = f"{current:.1f} {unit}"
            target_text = f"Target: {target:.1f} {unit}"
        
        current_label = QLabel(current_text)
        current_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
        layout.addWidget(current_label)
        
        target_label = QLabel(target_text)
        target_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(target_label)
        
        # Performance indicator
        if current >= target:
            status = "✅ On Track"
            status_color = "#28a745"
        elif current >= target * 0.8:
            status = "⚠️ Below Target"
            status_color = "#ffc107"
        else:
            status = "❌ Needs Attention"
            status_color = "#dc3545"
        
        status_label = QLabel(status)
        status_label.setStyleSheet(f"font-size: 12px; color: {status_color}; font-weight: bold;")
        layout.addWidget(status_label)
        
        # Last update
        update_label = QLabel(f"Updated: {last_update}")
        update_label.setStyleSheet("font-size: 10px; color: #6c757d;")
        layout.addWidget(update_label)
        
        card.setLayout(layout)
        return card
    
    def create_manage_tab(self):
        """Create KPI management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        add_kpi_btn = QPushButton("➕ Add KPI")
        add_kpi_btn.clicked.connect(self.add_kpi)
        controls.addWidget(add_kpi_btn)
        
        edit_kpi_btn = QPushButton("✏️ Edit KPI")
        edit_kpi_btn.clicked.connect(self.edit_kpi)
        controls.addWidget(edit_kpi_btn)
        
        delete_kpi_btn = QPushButton("🗑️ Delete KPI")
        delete_kpi_btn.clicked.connect(self.delete_kpi)
        controls.addWidget(delete_kpi_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # KPI list
        self.kpi_table = QTableWidget()
        self.kpi_table.setColumnCount(5)
        self.kpi_table.setHorizontalHeaderLabels(["Name", "Category", "Target", "Unit", "Status"])
        self.load_kpi_list()
        layout.addWidget(self.kpi_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_measurement_tab(self):
        """Create measurement entry tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Entry form
        form_group = QGroupBox("📊 Add New Measurement")
        form_layout = QFormLayout()
        
        self.kpi_combo = QComboBox()
        self.load_kpi_combo()
        form_layout.addRow("KPI:", self.kpi_combo)
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter value")
        form_layout.addRow("Value:", self.value_input)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.now().date())
        form_layout.addRow("Date:", self.date_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Optional notes...")
        form_layout.addRow("Notes:", self.notes_input)
        
        add_btn = QPushButton("➕ Add Measurement")
        add_btn.clicked.connect(self.add_measurement)
        form_layout.addRow(add_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Recent measurements
        recent_group = QGroupBox("📋 Recent Measurements")
        recent_layout = QVBoxLayout()
        
        self.measurements_table = QTableWidget()
        self.measurements_table.setColumnCount(4)
        self.measurements_table.setHorizontalHeaderLabels(["KPI", "Value", "Date", "Notes"])
        self.load_recent_measurements()
        recent_layout.addWidget(self.measurements_table)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        widget.setLayout(layout)
        return widget
    
    def load_kpi_list(self):
        """Load KPIs into management table"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, category, target_value, unit, is_active FROM kpi_definitions")
        kpis = cursor.fetchall()
        
        self.kpi_table.setRowCount(len(kpis))
        for row, (name, category, target, unit, active) in enumerate(kpis):
            self.kpi_table.setItem(row, 0, QTableWidgetItem(name))
            self.kpi_table.setItem(row, 1, QTableWidgetItem(category or ""))
            self.kpi_table.setItem(row, 2, QTableWidgetItem(str(target)))
            self.kpi_table.setItem(row, 3, QTableWidgetItem(unit or ""))
            self.kpi_table.setItem(row, 4, QTableWidgetItem("Active" if active else "Inactive"))
    
    def load_kpi_combo(self):
        """Load KPIs into combo box"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM kpi_definitions WHERE is_active = 1")
        kpis = cursor.fetchall()
        
        self.kpi_combo.clear()
        for kpi_id, name in kpis:
            self.kpi_combo.addItem(name, kpi_id)
    
    def load_recent_measurements(self):
        """Load recent measurements"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT kd.name, km.value, km.date, km.notes
            FROM kpi_measurements km
            JOIN kpi_definitions kd ON km.kpi_id = kd.id
            ORDER BY km.date DESC
            LIMIT 20
        """)
        measurements = cursor.fetchall()
        
        self.measurements_table.setRowCount(len(measurements))
        for row, (name, value, date, notes) in enumerate(measurements):
            self.measurements_table.setItem(row, 0, QTableWidgetItem(name))
            self.measurements_table.setItem(row, 1, QTableWidgetItem(str(value)))
            self.measurements_table.setItem(row, 2, QTableWidgetItem(date))
            self.measurements_table.setItem(row, 3, QTableWidgetItem(notes or ""))
    
    def add_measurement(self):
        """Add new KPI measurement"""
        if self.kpi_combo.currentData() is None:
            QMessageBox.warning(self, "No KPI Selected", "Please select a KPI")
            return
        
        try:
            value = float(self.value_input.text())
            kpi_id = self.kpi_combo.currentData()
            date = self.date_input.date().toPyDate()
            notes = self.notes_input.toPlainText()
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO kpi_measurements (kpi_id, value, date, notes)
                VALUES (?, ?, ?, ?)
            """, (kpi_id, value, date, notes))
            self.conn.commit()
            
            # Clear form
            self.value_input.clear()
            self.notes_input.clear()
            
            # Refresh displays
            self.load_recent_measurements()
            QMessageBox.information(self, "Success", "Measurement added successfully")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Please enter a valid number")
    
    def add_kpi(self):
        """Add new KPI definition"""
        dialog = KPIDialog(self)
        if dialog.exec_():
            kpi_data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO kpi_definitions (name, category, target_value, unit, description)
                VALUES (?, ?, ?, ?, ?)
            """, (kpi_data['name'], kpi_data['category'], kpi_data['target'], 
                  kpi_data['unit'], kpi_data['description']))
            self.conn.commit()
            self.load_kpi_list()
            self.load_kpi_combo()
    
    def edit_kpi(self):
        """Edit selected KPI"""
        QMessageBox.information(self, "Edit KPI", "KPI editing functionality")
    
    def delete_kpi(self):
        """Delete selected KPI"""
        current_row = self.kpi_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "Delete KPI", 
                                       "Are you sure you want to delete this KPI?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                QMessageBox.information(self, "Delete", "KPI deletion functionality")

class KPIDialog(QDialog):
    """Dialog for adding/editing KPIs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add KPI")
        self.setModal(True)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        layout.addRow("Name:", self.name_input)
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Financial", "Marketing", "Operations", "Sales", "Quality", "Business"])
        self.category_input.setEditable(True)
        layout.addRow("Category:", self.category_input)
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target value")
        layout.addRow("Target Value:", self.target_input)
        
        self.unit_input = QComboBox()
        self.unit_input.addItems(["$", "%", "count", "days", "rating", "hours"])
        self.unit_input.setEditable(True)
        layout.addRow("Unit:", self.unit_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        layout.addRow("Description:", self.description_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Get form data"""
        return {
            'name': self.name_input.text(),
            'category': self.category_input.currentText(),
            'target': float(self.target_input.text()) if self.target_input.text() else 0,
            'unit': self.unit_input.currentText(),
            'description': self.description_input.toPlainText()
        }