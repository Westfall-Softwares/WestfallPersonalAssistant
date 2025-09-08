"""
Enhanced Time Tracking System for Westfall Assistant - Entrepreneur Edition
Designed for solo developers with project-based billing and productivity analytics
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread
from PyQt5.QtGui import QFont, QPalette, QColor

# Optional dependencies with fallbacks
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

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class TimeTrackingWindow(QMainWindow):
    """Main time tracking window with productivity analytics"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracking - WestfallPersonalAssistant")
        self.setMinimumSize(1200, 800)
        
        # Initialize database and error handler
        self.init_database()
        self.error_handler = get_error_handler(self) if HAS_ERROR_HANDLER else None
        
        # Time tracking state
        self.current_session = None
        self.timer_running = False
        self.session_start_time = None
        self.total_session_seconds = 0
        self.idle_threshold = 300  # 5 minutes idle threshold
        self.last_activity_time = datetime.now()
        
        # Initialize UI
        self.init_ui()
        self.load_data()
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        self.idle_check_timer = QTimer()
        self.idle_check_timer.timeout.connect(self.check_idle)
        self.idle_check_timer.start(60000)  # Check idle every minute
        
        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save_session)
        self.autosave_timer.start(300000)  # Auto-save every 5 minutes

    def init_database(self):
        """Initialize time tracking database"""
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/time_tracking.db')
        cursor = self.conn.cursor()
        
        # Projects table (sync with finance module)
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
                color TEXT DEFAULT '#ff0000',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Time sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0,
                description TEXT,
                tags TEXT,
                billable BOOLEAN DEFAULT 1,
                invoiced BOOLEAN DEFAULT 0,
                invoice_id INTEGER,
                productivity_score INTEGER DEFAULT 100,
                break_time_seconds INTEGER DEFAULT 0,
                idle_time_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Activity tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                activity_type TEXT NOT NULL,
                application_name TEXT,
                window_title TEXT,
                url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0,
                productivity_category TEXT DEFAULT 'neutral',
                FOREIGN KEY (session_id) REFERENCES time_sessions (id)
            )
        ''')
        
        # Break tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                break_type TEXT DEFAULT 'manual',
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0,
                reason TEXT,
                FOREIGN KEY (session_id) REFERENCES time_sessions (id)
            )
        ''')
        
        # Daily goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                target_hours DECIMAL(4,2) NOT NULL,
                target_billable_hours DECIMAL(4,2),
                target_revenue DECIMAL(10,2),
                actual_hours DECIMAL(4,2) DEFAULT 0,
                actual_billable_hours DECIMAL(4,2) DEFAULT 0,
                actual_revenue DECIMAL(10,2) DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply theme
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
        
        # Header with timer and controls
        header = self.create_header()
        layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_timer_tab()
        self.create_sessions_tab()
        self.create_analytics_tab()
        self.create_projects_tab()
        self.create_goals_tab()
        
        # Status bar
        self.statusBar().showMessage("Time Tracking System Ready")

    def create_header(self):
        """Create the header with timer and controls"""
        header_widget = QWidget()
        if HAS_THEME:
            header_widget.setStyleSheet(f"""
                background-color: {AppTheme.SECONDARY_BG}; 
                border-bottom: 2px solid {AppTheme.PRIMARY_COLOR};
                padding: 10px;
            """)
        
        layout = QHBoxLayout(header_widget)
        
        # Title and timer display
        title_layout = QVBoxLayout()
        
        title_label = QLabel("⏱️ Time Tracking")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        if HAS_THEME:
            title_label.setStyleSheet(f"color: {AppTheme.PRIMARY_COLOR};")
        title_layout.addWidget(title_label)
        
        # Current session timer
        self.timer_display = QLabel("00:00:00")
        timer_font = QFont()
        timer_font.setPointSize(24)
        timer_font.setBold(True)
        self.timer_display.setFont(timer_font)
        if HAS_THEME:
            self.timer_display.setStyleSheet(f"color: {AppTheme.TEXT_PRIMARY};")
        title_layout.addWidget(self.timer_display)
        
        layout.addLayout(title_layout)
        
        # Project selection
        project_layout = QVBoxLayout()
        project_layout.addWidget(QLabel("Current Project:"))
        
        self.current_project_combo = QComboBox()
        self.current_project_combo.setMinimumWidth(250)
        if HAS_THEME:
            self.current_project_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                    padding: 5px;
                }}
            """)
        project_layout.addWidget(self.current_project_combo)
        layout.addLayout(project_layout)
        
        # Timer controls
        controls_layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.clicked.connect(self.start_session)
        self.start_btn.setMinimumHeight(40)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.pause_session)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(40)
        button_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_session)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        button_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(button_layout)
        
        # Today's stats
        stats_layout = QHBoxLayout()
        self.today_hours_label = QLabel("Today: 0h 0m")
        self.today_billable_label = QLabel("Billable: $0")
        stats_layout.addWidget(self.today_hours_label)
        stats_layout.addWidget(self.today_billable_label)
        controls_layout.addLayout(stats_layout)
        
        layout.addLayout(controls_layout)
        
        return header_widget

    def create_timer_tab(self):
        """Create the active timer tab"""
        timer_widget = QWidget()
        layout = QVBoxLayout(timer_widget)
        
        # Current session info
        session_group = QGroupBox("Current Session")
        session_layout = QVBoxLayout(session_group)
        
        # Session details
        details_layout = QHBoxLayout()
        
        # Project info
        project_info = QVBoxLayout()
        self.session_project_label = QLabel("No active session")
        self.session_start_label = QLabel("")
        project_info.addWidget(self.session_project_label)
        project_info.addWidget(self.session_start_label)
        details_layout.addLayout(project_info)
        
        # Session stats
        stats_layout = QVBoxLayout()
        self.session_duration_label = QLabel("Duration: 00:00:00")
        self.session_breaks_label = QLabel("Breaks: 0")
        self.session_productivity_label = QLabel("Productivity: 100%")
        stats_layout.addWidget(self.session_duration_label)
        stats_layout.addWidget(self.session_breaks_label)
        stats_layout.addWidget(self.session_productivity_label)
        details_layout.addLayout(stats_layout)
        
        session_layout.addLayout(details_layout)
        
        # Session description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.session_description = QLineEdit()
        self.session_description.setPlaceholderText("What are you working on?")
        desc_layout.addWidget(self.session_description)
        session_layout.addLayout(desc_layout)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        self.session_tags = QLineEdit()
        self.session_tags.setPlaceholderText("bug-fix, feature, meeting, etc.")
        tags_layout.addWidget(self.session_tags)
        session_layout.addLayout(tags_layout)
        
        layout.addWidget(session_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        break_btn = QPushButton("☕ Take Break")
        break_btn.clicked.connect(self.take_break)
        actions_layout.addWidget(break_btn)
        
        meeting_btn = QPushButton("👥 Meeting Mode")
        meeting_btn.clicked.connect(self.start_meeting_mode)
        actions_layout.addWidget(meeting_btn)
        
        pomodoro_btn = QPushButton("🍅 Pomodoro (25min)")
        pomodoro_btn.clicked.connect(self.start_pomodoro)
        actions_layout.addWidget(pomodoro_btn)
        
        layout.addWidget(actions_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.recent_activity_list = QListWidget()
        if HAS_THEME:
            self.recent_activity_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                }}
            """)
        activity_layout.addWidget(self.recent_activity_list)
        
        layout.addWidget(activity_group)
        
        self.tab_widget.addTab(timer_widget, "⏱️ Timer")

    def create_sessions_tab(self):
        """Create the sessions history tab"""
        sessions_widget = QWidget()
        layout = QVBoxLayout(sessions_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Date filter
        toolbar.addWidget(QLabel("From:"))
        self.sessions_start_date = QDateEdit()
        self.sessions_start_date.setDate(QDate.currentDate().addDays(-7))
        self.sessions_start_date.setCalendarPopup(True)
        toolbar.addWidget(self.sessions_start_date)
        
        toolbar.addWidget(QLabel("To:"))
        self.sessions_end_date = QDateEdit()
        self.sessions_end_date.setDate(QDate.currentDate())
        self.sessions_end_date.setCalendarPopup(True)
        toolbar.addWidget(self.sessions_end_date)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_sessions)
        toolbar.addWidget(filter_btn)
        
        toolbar.addStretch()
        
        # Export options
        export_btn = QPushButton("📊 Export CSV")
        export_btn.clicked.connect(self.export_sessions)
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        # Sessions table
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(9)
        self.sessions_table.setHorizontalHeaderLabels([
            "Date", "Project", "Start", "End", "Duration", "Billable", 
            "Revenue", "Productivity", "Description"
        ])
        
        if HAS_THEME:
            self.sessions_table.setStyleSheet(f"""
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
        
        layout.addWidget(self.sessions_table)
        
        self.tab_widget.addTab(sessions_widget, "📋 Sessions")

    def create_analytics_tab(self):
        """Create the analytics and reports tab"""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Analytics cards
        cards_layout = QHBoxLayout()
        
        # Weekly stats card
        weekly_card = self.create_analytics_card("This Week", {
            "Hours": "0h 0m",
            "Billable": "$0",
            "Projects": "0",
            "Avg/Day": "0h 0m"
        })
        cards_layout.addWidget(weekly_card)
        
        # Monthly stats card
        monthly_card = self.create_analytics_card("This Month", {
            "Hours": "0h 0m", 
            "Billable": "$0",
            "Projects": "0",
            "Avg/Day": "0h 0m"
        })
        cards_layout.addWidget(monthly_card)
        
        # Productivity card
        productivity_card = self.create_analytics_card("Productivity", {
            "Score": "100%",
            "Focus Time": "0%",
            "Break Time": "0%",
            "Idle Time": "0%"
        })
        cards_layout.addWidget(productivity_card)
        
        layout.addLayout(cards_layout)
        
        # Charts section (placeholder for now)
        charts_group = QGroupBox("Analytics Charts")
        charts_layout = QVBoxLayout(charts_group)
        
        chart_placeholder = QLabel("📊 Analytics charts will be displayed here\n\n" +
                                 "• Daily/Weekly/Monthly time distribution\n" +
                                 "• Project profitability analysis\n" +
                                 "• Productivity trends\n" +
                                 "• Break patterns\n" +
                                 "• Focus vs distraction time")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setMinimumHeight(300)
        if HAS_THEME:
            chart_placeholder.setStyleSheet(f"""
                background-color: {AppTheme.SECONDARY_BG};
                border: 1px solid {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_SECONDARY};
                font-size: 14px;
            """)
        
        charts_layout.addWidget(chart_placeholder)
        layout.addWidget(charts_group)
        
        # Store card references
        self.weekly_card = weekly_card
        self.monthly_card = monthly_card
        self.productivity_card = productivity_card
        
        self.tab_widget.addTab(analytics_widget, "📊 Analytics")

    def create_analytics_card(self, title, metrics):
        """Create an analytics card"""
        card = QGroupBox(title)
        card.setMaximumWidth(250)
        
        if HAS_THEME:
            card.setStyleSheet(f"""
                QGroupBox {{
                    background-color: {AppTheme.SECONDARY_BG};
                    border: 2px solid {AppTheme.PRIMARY_COLOR};
                    border-radius: 8px;
                    font-weight: bold;
                    color: {AppTheme.TEXT_PRIMARY};
                }}
            """)
        
        layout = QVBoxLayout(card)
        
        # Store metric labels for updates
        card.metric_labels = {}
        
        for metric, value in metrics.items():
            metric_layout = QHBoxLayout()
            
            metric_label = QLabel(metric + ":")
            value_label = QLabel(value)
            value_label.setFont(QFont("Arial", 10, QFont.Bold))
            
            metric_layout.addWidget(metric_label)
            metric_layout.addStretch()
            metric_layout.addWidget(value_label)
            
            layout.addLayout(metric_layout)
            
            # Store reference for updates
            card.metric_labels[metric] = value_label
        
        return card

    def create_projects_tab(self):
        """Create the projects management tab"""
        projects_widget = QWidget()
        layout = QVBoxLayout(projects_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        new_project_btn = QPushButton("➕ New Project")
        new_project_btn.clicked.connect(self.create_new_project)
        toolbar.addWidget(new_project_btn)
        
        edit_project_btn = QPushButton("✏️ Edit Project")
        edit_project_btn.clicked.connect(self.edit_project)
        toolbar.addWidget(edit_project_btn)
        
        archive_project_btn = QPushButton("📦 Archive Project")
        archive_project_btn.clicked.connect(self.archive_project)
        toolbar.addWidget(archive_project_btn)
        
        toolbar.addStretch()
        
        sync_btn = QPushButton("🔄 Sync with Finance")
        sync_btn.clicked.connect(self.sync_with_finance)
        toolbar.addWidget(sync_btn)
        
        layout.addLayout(toolbar)
        
        # Projects table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(7)
        self.projects_table.setHorizontalHeaderLabels([
            "Name", "Client", "Rate/Hour", "Budget", "Status", "Total Hours", "Revenue"
        ])
        
        if HAS_THEME:
            self.projects_table.setStyleSheet(f"""
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
        
        layout.addWidget(self.projects_table)
        
        self.tab_widget.addTab(projects_widget, "📁 Projects")

    def create_goals_tab(self):
        """Create the daily goals and targets tab"""
        goals_widget = QWidget()
        layout = QVBoxLayout(goals_widget)
        
        # Today's goals
        today_group = QGroupBox("Today's Goals")
        today_layout = QVBoxLayout(today_group)
        
        # Goals input
        goals_input_layout = QHBoxLayout()
        
        goals_input_layout.addWidget(QLabel("Target Hours:"))
        self.target_hours = QDoubleSpinBox()
        self.target_hours.setRange(0, 24)
        self.target_hours.setValue(8.0)
        self.target_hours.setSuffix(" hours")
        goals_input_layout.addWidget(self.target_hours)
        
        goals_input_layout.addWidget(QLabel("Target Revenue:"))
        self.target_revenue = QDoubleSpinBox()
        self.target_revenue.setRange(0, 99999)
        self.target_revenue.setPrefix("$")
        self.target_revenue.setValue(1000.0)
        goals_input_layout.addWidget(self.target_revenue)
        
        set_goals_btn = QPushButton("📌 Set Goals")
        set_goals_btn.clicked.connect(self.set_daily_goals)
        goals_input_layout.addWidget(set_goals_btn)
        
        goals_input_layout.addStretch()
        
        today_layout.addLayout(goals_input_layout)
        
        # Progress bars
        progress_layout = QVBoxLayout()
        
        # Hours progress
        hours_layout = QHBoxLayout()
        hours_layout.addWidget(QLabel("Hours Progress:"))
        self.hours_progress = QProgressBar()
        self.hours_progress.setMaximum(100)
        hours_layout.addWidget(self.hours_progress)
        self.hours_progress_label = QLabel("0 / 8 hours")
        hours_layout.addWidget(self.hours_progress_label)
        progress_layout.addLayout(hours_layout)
        
        # Revenue progress
        revenue_layout = QHBoxLayout()
        revenue_layout.addWidget(QLabel("Revenue Progress:"))
        self.revenue_progress = QProgressBar()
        self.revenue_progress.setMaximum(100)
        revenue_layout.addWidget(self.revenue_progress)
        self.revenue_progress_label = QLabel("$0 / $1000")
        revenue_layout.addWidget(self.revenue_progress_label)
        progress_layout.addLayout(revenue_layout)
        
        today_layout.addLayout(progress_layout)
        layout.addWidget(today_group)
        
        # Goals history
        history_group = QGroupBox("Goals History")
        history_layout = QVBoxLayout(history_group)
        
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(6)
        self.goals_table.setHorizontalHeaderLabels([
            "Date", "Target Hours", "Actual Hours", "Target Revenue", "Actual Revenue", "Achievement"
        ])
        
        if HAS_THEME:
            self.goals_table.setStyleSheet(f"""
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
        
        history_layout.addWidget(self.goals_table)
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(goals_widget, "🎯 Goals")

    def load_data(self):
        """Load all data for the interface"""
        self.load_projects()
        self.load_sessions()
        self.load_analytics()
        self.load_goals()
        self.update_today_stats()

    def load_projects(self):
        """Load projects into combo box and table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, client_name, hourly_rate, total_budget, status
            FROM projects 
            ORDER BY status, name
        """)
        projects = cursor.fetchall()
        
        # Update combo box
        self.current_project_combo.clear()
        for project in projects:
            if project[5] == 'active':  # Only active projects in combo
                display_text = f"{project[1]} ({project[2] or 'No Client'})"
                self.current_project_combo.addItem(display_text, project[0])
        
        # Update projects table
        self.projects_table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            # Calculate total hours and revenue for this project
            cursor.execute("""
                SELECT COALESCE(SUM(duration_seconds), 0) / 3600.0,
                       COALESCE(SUM(duration_seconds * hourly_rate / 3600.0), 0)
                FROM time_sessions ts
                JOIN projects p ON ts.project_id = p.id
                WHERE ts.project_id = ? AND ts.billable = 1
            """, (project[0],))
            hours_revenue = cursor.fetchone()
            total_hours = hours_revenue[0] if hours_revenue[0] else 0
            total_revenue = hours_revenue[1] if hours_revenue[1] else 0
            
            # Populate table
            items = [
                project[1],  # Name
                project[2] or "",  # Client
                f"${project[3]:.2f}" if project[3] else "N/A",  # Rate
                f"${project[4]:.2f}" if project[4] else "N/A",  # Budget
                project[5],  # Status
                f"{total_hours:.1f}h",  # Total hours
                f"${total_revenue:.2f}"  # Revenue
            ]
            
            for col, item in enumerate(items):
                self.projects_table.setItem(row, col, QTableWidgetItem(str(item)))

    def load_sessions(self):
        """Load time sessions into the table"""
        start_date = self.sessions_start_date.date().toPyDate()
        end_date = self.sessions_end_date.date().toPyDate()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ts.start_time, p.name, ts.start_time, ts.end_time,
                   ts.duration_seconds, ts.billable, 
                   (ts.duration_seconds * p.hourly_rate / 3600.0) as revenue,
                   ts.productivity_score, ts.description
            FROM time_sessions ts
            JOIN projects p ON ts.project_id = p.id
            WHERE DATE(ts.start_time) BETWEEN ? AND ?
            ORDER BY ts.start_time DESC
        """, (start_date, end_date))
        
        sessions = cursor.fetchall()
        self.sessions_table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            # Format the data
            start_time = datetime.fromisoformat(session[2])
            end_time = datetime.fromisoformat(session[3]) if session[3] else None
            duration_hours = session[4] / 3600 if session[4] else 0
            
            items = [
                start_time.strftime("%Y-%m-%d"),
                session[1],  # Project name
                start_time.strftime("%H:%M"),
                end_time.strftime("%H:%M") if end_time else "Active",
                f"{duration_hours:.1f}h",
                "Yes" if session[5] else "No",
                f"${session[6]:.2f}" if session[6] else "$0",
                f"{session[7]}%" if session[7] else "N/A",
                session[8] or ""
            ]
            
            for col, item in enumerate(items):
                self.sessions_table.setItem(row, col, QTableWidgetItem(str(item)))

    def load_analytics(self):
        """Load analytics data"""
        cursor = self.conn.cursor()
        today = date.today()
        
        # This week stats
        week_start = today - timedelta(days=today.weekday())
        cursor.execute("""
            SELECT COALESCE(SUM(duration_seconds), 0) / 3600.0,
                   COALESCE(SUM(CASE WHEN ts.billable = 1 THEN duration_seconds * p.hourly_rate / 3600.0 ELSE 0 END), 0),
                   COUNT(DISTINCT ts.project_id)
            FROM time_sessions ts
            JOIN projects p ON ts.project_id = p.id
            WHERE DATE(ts.start_time) >= ?
        """, (week_start,))
        
        week_stats = cursor.fetchone()
        week_hours = week_stats[0] if week_stats[0] else 0
        week_revenue = week_stats[1] if week_stats[1] else 0
        week_projects = week_stats[2] if week_stats[2] else 0
        
        # Update weekly card
        self.weekly_card.metric_labels["Hours"].setText(f"{week_hours:.1f}h")
        self.weekly_card.metric_labels["Billable"].setText(f"${week_revenue:.0f}")
        self.weekly_card.metric_labels["Projects"].setText(str(week_projects))
        self.weekly_card.metric_labels["Avg/Day"].setText(f"{week_hours/7:.1f}h")
        
        # This month stats
        month_start = today.replace(day=1)
        cursor.execute("""
            SELECT COALESCE(SUM(duration_seconds), 0) / 3600.0,
                   COALESCE(SUM(CASE WHEN ts.billable = 1 THEN duration_seconds * p.hourly_rate / 3600.0 ELSE 0 END), 0),
                   COUNT(DISTINCT ts.project_id)
            FROM time_sessions ts
            JOIN projects p ON ts.project_id = p.id
            WHERE DATE(ts.start_time) >= ?
        """, (month_start,))
        
        month_stats = cursor.fetchone()
        month_hours = month_stats[0] if month_stats[0] else 0
        month_revenue = month_stats[1] if month_stats[1] else 0
        month_projects = month_stats[2] if month_stats[2] else 0
        days_in_month = (today - month_start).days + 1
        
        # Update monthly card
        self.monthly_card.metric_labels["Hours"].setText(f"{month_hours:.1f}h")
        self.monthly_card.metric_labels["Billable"].setText(f"${month_revenue:.0f}")
        self.monthly_card.metric_labels["Projects"].setText(str(month_projects))
        self.monthly_card.metric_labels["Avg/Day"].setText(f"{month_hours/days_in_month:.1f}h")

    def load_goals(self):
        """Load daily goals"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT date, target_hours, actual_hours, target_revenue, actual_revenue
            FROM daily_goals
            ORDER BY date DESC
            LIMIT 30
        """)
        
        goals = cursor.fetchall()
        self.goals_table.setRowCount(len(goals))
        
        for row, goal in enumerate(goals):
            achievement_hours = (goal[2] / goal[1] * 100) if goal[1] > 0 else 0
            achievement_revenue = (goal[4] / goal[3] * 100) if goal[3] > 0 else 0
            overall_achievement = (achievement_hours + achievement_revenue) / 2
            
            items = [
                goal[0],
                f"{goal[1]:.1f}h",
                f"{goal[2]:.1f}h" if goal[2] else "0h",
                f"${goal[3]:.0f}",
                f"${goal[4]:.0f}" if goal[4] else "$0",
                f"{overall_achievement:.0f}%"
            ]
            
            for col, item in enumerate(items):
                self.goals_table.setItem(row, col, QTableWidgetItem(str(item)))

    def update_today_stats(self):
        """Update today's statistics"""
        cursor = self.conn.cursor()
        today = date.today()
        
        cursor.execute("""
            SELECT COALESCE(SUM(duration_seconds), 0) / 3600.0,
                   COALESCE(SUM(CASE WHEN ts.billable = 1 THEN duration_seconds * p.hourly_rate / 3600.0 ELSE 0 END), 0)
            FROM time_sessions ts
            JOIN projects p ON ts.project_id = p.id
            WHERE DATE(ts.start_time) = ?
        """, (today,))
        
        today_stats = cursor.fetchone()
        today_hours = today_stats[0] if today_stats[0] else 0
        today_revenue = today_stats[1] if today_stats[1] else 0
        
        self.today_hours_label.setText(f"Today: {today_hours:.1f}h")
        self.today_billable_label.setText(f"Billable: ${today_revenue:.0f}")
        
        # Update goals progress
        cursor.execute("SELECT target_hours, target_revenue FROM daily_goals WHERE date = ?", (today,))
        goal = cursor.fetchone()
        
        if goal:
            target_hours, target_revenue = goal
            hours_percent = min(100, (today_hours / target_hours * 100)) if target_hours > 0 else 0
            revenue_percent = min(100, (today_revenue / target_revenue * 100)) if target_revenue > 0 else 0
            
            self.hours_progress.setValue(int(hours_percent))
            self.revenue_progress.setValue(int(revenue_percent))
            self.hours_progress_label.setText(f"{today_hours:.1f} / {target_hours:.1f} hours")
            self.revenue_progress_label.setText(f"${today_revenue:.0f} / ${target_revenue:.0f}")

    # Timer control methods
    def start_session(self):
        """Start a new time tracking session"""
        project_id = self.current_project_combo.currentData()
        if not project_id:
            QMessageBox.warning(self, "No Project", "Please select a project before starting!")
            return
        
        # Create new session
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO time_sessions (project_id, start_time, description, tags)
            VALUES (?, ?, ?, ?)
        """, (project_id, datetime.now(), 
              self.session_description.text(), self.session_tags.text()))
        
        self.current_session = cursor.lastrowid
        self.conn.commit()
        
        # Update state
        self.timer_running = True
        self.session_start_time = datetime.now()
        self.total_session_seconds = 0
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        project_name = self.current_project_combo.currentText()
        self.session_project_label.setText(f"Project: {project_name}")
        self.session_start_label.setText(f"Started: {self.session_start_time.strftime('%H:%M:%S')}")
        
        self.statusBar().showMessage("Time tracking started")

    def pause_session(self):
        """Pause the current session"""
        if self.timer_running and self.current_session:
            self.timer_running = False
            
            # Calculate duration and save
            duration = (datetime.now() - self.session_start_time).total_seconds()
            self.total_session_seconds += duration
            
            # Update session in database
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_sessions 
                SET duration_seconds = ? 
                WHERE id = ?
            """, (self.total_session_seconds, self.current_session))
            self.conn.commit()
            
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.statusBar().showMessage("Session paused")

    def stop_session(self):
        """Stop the current session"""
        if self.current_session:
            # Calculate final duration
            if self.timer_running:
                duration = (datetime.now() - self.session_start_time).total_seconds()
                self.total_session_seconds += duration
            
            # Update session in database
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_sessions 
                SET end_time = ?, duration_seconds = ?, description = ?, tags = ?
                WHERE id = ?
            """, (datetime.now(), self.total_session_seconds,
                  self.session_description.text(), self.session_tags.text(),
                  self.current_session))
            self.conn.commit()
            
            # Reset state
            self.current_session = None
            self.timer_running = False
            self.session_start_time = None
            self.total_session_seconds = 0
            
            # Update UI
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
            self.session_project_label.setText("No active session")
            self.session_start_label.setText("")
            self.timer_display.setText("00:00:00")
            
            # Refresh data
            self.load_sessions()
            self.update_today_stats()
            self.statusBar().showMessage("Session completed")

    def update_display(self):
        """Update timer display and session info"""
        if self.timer_running and self.session_start_time:
            # Calculate current duration
            current_duration = (datetime.now() - self.session_start_time).total_seconds()
            total_duration = self.total_session_seconds + current_duration
            
            # Format time display
            hours = int(total_duration // 3600)
            minutes = int((total_duration % 3600) // 60)
            seconds = int(total_duration % 60)
            
            self.timer_display.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.session_duration_label.setText(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def check_idle(self):
        """Check for idle time and handle accordingly"""
        # This is a placeholder - in a real implementation you'd monitor system activity
        pass

    def auto_save_session(self):
        """Auto-save current session progress"""
        if self.current_session and self.timer_running:
            duration = (datetime.now() - self.session_start_time).total_seconds()
            total_duration = self.total_session_seconds + duration
            
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_sessions 
                SET duration_seconds = ?, description = ?, tags = ?
                WHERE id = ?
            """, (total_duration, self.session_description.text(), 
                  self.session_tags.text(), self.current_session))
            self.conn.commit()

    # Additional methods for features
    def take_break(self):
        """Start a break"""
        QMessageBox.information(self, "Break Time", "Break tracking feature coming soon!")

    def start_meeting_mode(self):
        """Start meeting mode"""
        QMessageBox.information(self, "Meeting Mode", "Meeting mode feature coming soon!")

    def start_pomodoro(self):
        """Start a 25-minute pomodoro session"""
        QMessageBox.information(self, "Pomodoro", "Pomodoro timer feature coming soon!")

    def filter_sessions(self):
        """Filter sessions by date range"""
        self.load_sessions()

    def export_sessions(self):
        """Export sessions to CSV"""
        if HAS_PANDAS:
            QMessageBox.information(self, "Export", "CSV export feature coming soon!")
        else:
            QMessageBox.warning(self, "Export", "Pandas not available for CSV export")

    def create_new_project(self):
        """Create a new project"""
        dialog = ProjectDialog(self)
        if dialog.exec_():
            self.load_projects()

    def edit_project(self):
        """Edit selected project"""
        QMessageBox.information(self, "Edit Project", "Project editing feature coming soon!")

    def archive_project(self):
        """Archive selected project"""
        QMessageBox.information(self, "Archive Project", "Project archiving feature coming soon!")

    def sync_with_finance(self):
        """Sync projects with finance module"""
        try:
            # Try to import and sync with finance database
            finance_conn = sqlite3.connect('data/finance.db')
            finance_cursor = finance_conn.cursor()
            
            # Get projects from finance database
            finance_cursor.execute("SELECT name, client_name, hourly_rate, total_budget FROM projects")
            finance_projects = finance_cursor.fetchall()
            
            # Insert into time tracking database
            cursor = self.conn.cursor()
            for project in finance_projects:
                cursor.execute("""
                    INSERT OR IGNORE INTO projects (name, client_name, hourly_rate, total_budget)
                    VALUES (?, ?, ?, ?)
                """, project)
            
            self.conn.commit()
            finance_conn.close()
            
            self.load_projects()
            QMessageBox.information(self, "Sync Complete", f"Synced {len(finance_projects)} projects from Finance module!")
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_database_error(e, "Failed to sync with finance database")
            else:
                QMessageBox.warning(self, "Sync Error", f"Failed to sync: {e}")

    def set_daily_goals(self):
        """Set daily goals"""
        today = date.today()
        target_hours = self.target_hours.value()
        target_revenue = self.target_revenue.value()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_goals 
            (date, target_hours, target_revenue)
            VALUES (?, ?, ?)
        """, (today, target_hours, target_revenue))
        self.conn.commit()
        
        self.load_goals()
        self.update_today_stats()
        QMessageBox.information(self, "Goals Set", f"Daily goals set: {target_hours}h, ${target_revenue}")


class ProjectDialog(QDialog):
    """Dialog for creating/editing projects"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("New Project")
        self.setMinimumSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form fields
        form_layout = QFormLayout()
        
        self.name = QLineEdit()
        form_layout.addRow("Project Name:", self.name)
        
        self.client_name = QLineEdit()
        form_layout.addRow("Client Name:", self.client_name)
        
        self.hourly_rate = QDoubleSpinBox()
        self.hourly_rate.setRange(0, 9999)
        self.hourly_rate.setPrefix("$")
        self.hourly_rate.setValue(100.0)
        form_layout.addRow("Hourly Rate:", self.hourly_rate)
        
        self.total_budget = QDoubleSpinBox()
        self.total_budget.setRange(0, 999999)
        self.total_budget.setPrefix("$")
        form_layout.addRow("Total Budget:", self.total_budget)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date)
        
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Project")
        save_btn.clicked.connect(self.save_project)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def save_project(self):
        """Save the project to database"""
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project name is required!")
            return
        
        cursor = self.parent_window.conn.cursor()
        cursor.execute("""
            INSERT INTO projects (
                name, client_name, hourly_rate, total_budget, start_date, description
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.name.text(), self.client_name.text(), self.hourly_rate.value(),
            self.total_budget.value(), self.start_date.date().toPyDate(),
            self.description.toPlainText()
        ))
        
        self.parent_window.conn.commit()
        self.accept()


# Widget wrapper for main application integration
class TimeTrackingWidget(QWidget):
    """Widget wrapper for the time tracking window"""
    
    def __init__(self):
        super().__init__()
        self.time_window = TimeTrackingWindow()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.time_window.centralWidget())


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Apply theme if available
    if HAS_THEME:
        AppTheme.apply_to_application()
    
    window = TimeTrackingWindow()
    window.show()
    
    sys.exit(app.exec_())