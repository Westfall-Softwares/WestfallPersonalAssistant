"""
Calendar Manager Component for Westfall Personal Assistant

Provides calendar and scheduling functionality with red/black theme integration.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QCalendarWidget, QListWidget, QListWidgetItem,
                           QSplitter, QGroupBox, QFormLayout, QLineEdit,
                           QTextEdit, QDateTimeEdit, QComboBox, QCheckBox,
                           QDialog, QDialogButtonBox, QMessageBox, QTabWidget,
                           QScrollArea, QTimeEdit)
from PyQt5.QtCore import Qt, QDate, QDateTime, QTime, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCharFormat, QColor
from utils.app_theme import AppTheme
import logging

logger = logging.getLogger(__name__)


class EventDialog(QDialog):
    """Dialog for creating/editing calendar events"""
    
    def __init__(self, event=None, selected_date=None, parent=None):
        super().__init__(parent)
        self.event = event
        self.selected_date = selected_date or QDate.currentDate()
        self.init_ui()
        self.apply_theme()
        
        if event:
            self.load_event_data()
            
    def init_ui(self):
        """Initialize the event dialog"""
        self.setWindowTitle("Create Event" if not self.event else "Edit Event")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Event title
        self.title_field = QLineEdit()
        self.title_field.setPlaceholderText("Enter event title...")
        form_layout.addRow("Title:", self.title_field)
        
        # Description
        self.description_field = QTextEdit()
        self.description_field.setMaximumHeight(100)
        self.description_field.setPlaceholderText("Event description...")
        form_layout.addRow("Description:", self.description_field)
        
        # Start date and time
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(QDateTime(self.selected_date, QTime(9, 0)))
        self.start_datetime.setCalendarPopup(True)
        form_layout.addRow("Start:", self.start_datetime)
        
        # End date and time
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDateTime(QDateTime(self.selected_date, QTime(10, 0)))
        self.end_datetime.setCalendarPopup(True)
        form_layout.addRow("End:", self.end_datetime)
        
        # All day event
        self.all_day_check = QCheckBox("All day event")
        self.all_day_check.toggled.connect(self.toggle_all_day)
        form_layout.addRow("Duration:", self.all_day_check)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Meeting", "Appointment", "Reminder", "Other"])
        form_layout.addRow("Category:", self.category_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentIndex(1)  # Default to Medium
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Location
        self.location_field = QLineEdit()
        self.location_field.setPlaceholderText("Event location...")
        form_layout.addRow("Location:", self.location_field)
        
        # Reminder
        self.reminder_combo = QComboBox()
        self.reminder_combo.addItems(["None", "5 minutes", "15 minutes", "30 minutes", "1 hour", "2 hours", "1 day"])
        form_layout.addRow("Reminder:", self.reminder_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def apply_theme(self):
        """Apply red/black theme to dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_SMALL}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {AppTheme.HIGHLIGHT_COLOR};
            }}
            QPushButton {{
                {AppTheme.get_button_style()}
            }}
            QCheckBox {{
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {AppTheme.PRIMARY_COLOR};
                border: 1px solid {AppTheme.BORDER_COLOR};
            }}
        """)
        
    def toggle_all_day(self, checked):
        """Toggle all day event mode"""
        if checked:
            self.start_datetime.setDisplayFormat("yyyy-MM-dd")
            self.end_datetime.setDisplayFormat("yyyy-MM-dd")
        else:
            self.start_datetime.setDisplayFormat("yyyy-MM-dd hh:mm")
            self.end_datetime.setDisplayFormat("yyyy-MM-dd hh:mm")
            
    def load_event_data(self):
        """Load existing event data into form"""
        if self.event:
            self.title_field.setText(self.event.get('title', ''))
            self.description_field.setPlainText(self.event.get('description', ''))
            self.location_field.setText(self.event.get('location', ''))
            
            category = self.event.get('category', 'Work')
            category_index = self.category_combo.findText(category)
            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)
                
            priority = self.event.get('priority', 'Medium')
            priority_index = self.priority_combo.findText(priority)
            if priority_index >= 0:
                self.priority_combo.setCurrentIndex(priority_index)
                
            self.all_day_check.setChecked(self.event.get('all_day', False))
            
    def get_event_data(self):
        """Get event data from form"""
        return {
            'title': self.title_field.text().strip(),
            'description': self.description_field.toPlainText().strip(),
            'start_datetime': self.start_datetime.dateTime().toString('yyyy-MM-dd hh:mm'),
            'end_datetime': self.end_datetime.dateTime().toString('yyyy-MM-dd hh:mm'),
            'all_day': self.all_day_check.isChecked(),
            'category': self.category_combo.currentText(),
            'priority': self.priority_combo.currentText(),
            'location': self.location_field.text().strip(),
            'reminder': self.reminder_combo.currentText()
        }


class CalendarManager(QWidget):
    """Calendar interface with event management"""
    
    event_created = pyqtSignal(dict)
    event_updated = pyqtSignal(dict)
    event_deleted = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.events = []
        self.selected_date = QDate.currentDate()
        
        self.init_ui()
        self.apply_theme()
        self.load_sample_events()
        
        # Timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_calendar_display)
        self.update_timer.start(60000)  # Update every minute
        
    def init_ui(self):
        """Initialize the calendar interface"""
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("📅 Calendar")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Calendar controls
        self.new_event_btn = QPushButton("➕ New Event")
        self.new_event_btn.clicked.connect(self.create_new_event)
        header_layout.addWidget(self.new_event_btn)
        
        self.today_btn = QPushButton("📍 Today")
        self.today_btn.clicked.connect(self.go_to_today)
        header_layout.addWidget(self.today_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - Calendar widget
        left_panel = self.create_calendar_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Events and details
        right_panel = self.create_events_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([400, 600])
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def create_calendar_panel(self):
        """Create the calendar widget panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Month navigation
        nav_layout = QHBoxLayout()
        
        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.clicked.connect(self.previous_month)
        nav_layout.addWidget(self.prev_month_btn)
        
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setFont(QFont("Arial", 12, QFont.Bold))
        nav_layout.addWidget(self.month_label)
        
        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(self.next_month_btn)
        
        layout.addLayout(nav_layout)
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(self.selected_date)
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.currentPageChanged.connect(self.month_changed)
        layout.addWidget(self.calendar)
        
        # Mini event summary
        summary_group = QGroupBox("📊 Quick Stats")
        summary_layout = QVBoxLayout(summary_group)
        
        self.events_today_label = QLabel("Today: 0 events")
        self.events_week_label = QLabel("This week: 0 events")
        self.events_month_label = QLabel("This month: 0 events")
        
        summary_layout.addWidget(self.events_today_label)
        summary_layout.addWidget(self.events_week_label)
        summary_layout.addWidget(self.events_month_label)
        
        layout.addWidget(summary_group)
        
        return widget
        
    def create_events_panel(self):
        """Create the events panel"""
        widget = QTabWidget()
        
        # Day view tab
        day_widget = QWidget()
        day_layout = QVBoxLayout(day_widget)
        
        # Selected date header
        self.selected_date_label = QLabel()
        self.selected_date_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(self.selected_date_label)
        
        # Events for selected date
        events_label = QLabel("📋 Events")
        events_label.setFont(QFont("Arial", 12, QFont.Bold))
        day_layout.addWidget(events_label)
        
        self.day_events_list = QListWidget()
        self.day_events_list.itemClicked.connect(self.select_event)
        self.day_events_list.itemDoubleClicked.connect(self.edit_selected_event)
        day_layout.addWidget(self.day_events_list)
        
        # Event actions
        day_actions_layout = QHBoxLayout()
        
        self.edit_event_btn = QPushButton("✏️ Edit")
        self.edit_event_btn.clicked.connect(self.edit_selected_event)
        self.edit_event_btn.setEnabled(False)
        day_actions_layout.addWidget(self.edit_event_btn)
        
        self.delete_event_btn = QPushButton("🗑️ Delete")
        self.delete_event_btn.clicked.connect(self.delete_selected_event)
        self.delete_event_btn.setEnabled(False)
        day_actions_layout.addWidget(self.delete_event_btn)
        
        day_layout.addLayout(day_actions_layout)
        
        widget.addTab(day_widget, "📅 Day View")
        
        # Week view tab
        week_widget = QScrollArea()
        week_content = QWidget()
        week_layout = QVBoxLayout(week_content)
        
        week_label = QLabel("📆 Week View")
        week_label.setFont(QFont("Arial", 12, QFont.Bold))
        week_layout.addWidget(week_label)
        
        self.week_events_list = QListWidget()
        week_layout.addWidget(self.week_events_list)
        
        week_layout.addStretch()
        week_widget.setWidget(week_content)
        week_widget.setWidgetResizable(True)
        
        widget.addTab(week_widget, "📆 Week")
        
        # Upcoming events tab
        upcoming_widget = QScrollArea()
        upcoming_content = QWidget()
        upcoming_layout = QVBoxLayout(upcoming_content)
        
        upcoming_label = QLabel("⏰ Upcoming Events")
        upcoming_label.setFont(QFont("Arial", 12, QFont.Bold))
        upcoming_layout.addWidget(upcoming_label)
        
        self.upcoming_events_list = QListWidget()
        upcoming_layout.addWidget(self.upcoming_events_list)
        
        upcoming_layout.addStretch()
        upcoming_widget.setWidget(upcoming_content)
        upcoming_widget.setWidgetResizable(True)
        
        widget.addTab(upcoming_widget, "⏰ Upcoming")
        
        return widget
        
    def apply_theme(self):
        """Apply red/black theme to calendar"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QCalendarWidget {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QCalendarWidget QTableView {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                selection-background-color: {AppTheme.PRIMARY_COLOR};
            }}
            QListWidget {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QListWidget::item {{
                padding: {AppTheme.PADDING_MEDIUM}px;
                border-bottom: 1px solid {AppTheme.BORDER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QPushButton {{
                {AppTheme.get_button_style()}
            }}
            QPushButton:disabled {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_SECONDARY};
                border-color: {AppTheme.BORDER_COLOR};
            }}
            QGroupBox {{
                font-weight: bold;
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
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
            QScrollArea {{
                border: none;
                background-color: {AppTheme.SECONDARY_BG};
            }}
        """)
        
    def load_sample_events(self):
        """Load sample events for demonstration"""
        sample_events = [
            {
                'title': 'Team Meeting',
                'description': 'Weekly team sync and project updates',
                'start_datetime': '2024-12-10 10:00',
                'end_datetime': '2024-12-10 11:00',
                'all_day': False,
                'category': 'Work',
                'priority': 'High',
                'location': 'Conference Room A',
                'reminder': '15 minutes'
            },
            {
                'title': 'Doctor Appointment',
                'description': 'Annual checkup',
                'start_datetime': '2024-12-12 14:30',
                'end_datetime': '2024-12-12 15:30',
                'all_day': False,
                'category': 'Personal',
                'priority': 'Medium',
                'location': 'Medical Center',
                'reminder': '1 hour'
            },
            {
                'title': 'Project Deadline',
                'description': 'Submit final project deliverables',
                'start_datetime': '2024-12-15 00:00',
                'end_datetime': '2024-12-15 23:59',
                'all_day': True,
                'category': 'Work',
                'priority': 'Critical',
                'location': '',
                'reminder': '1 day'
            }
        ]
        
        self.events = sample_events
        self.update_calendar_display()
        self.update_date_display()
        
    def date_selected(self, date):
        """Handle date selection from calendar"""
        self.selected_date = date
        self.update_date_display()
        self.update_day_events()
        
    def month_changed(self, year, month):
        """Handle month navigation"""
        self.month_label.setText(QDate(year, month, 1).toString("MMMM yyyy"))
        self.update_calendar_display()
        
    def previous_month(self):
        """Navigate to previous month"""
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(-1)
        self.calendar.setSelectedDate(new_date)
        
    def next_month(self):
        """Navigate to next month"""
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(1)
        self.calendar.setSelectedDate(new_date)
        
    def go_to_today(self):
        """Navigate to today's date"""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.selected_date = today
        self.update_date_display()
        self.update_day_events()
        
    def update_calendar_display(self):
        """Update calendar display with event indicators"""
        # Clear existing formats
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        
        # Highlight dates with events
        event_format = QTextCharFormat()
        event_format.setBackground(QColor(AppTheme.PRIMARY_COLOR))
        event_format.setForeground(QColor(AppTheme.TEXT_PRIMARY))
        
        for event in self.events:
            start_date = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date()
            self.calendar.setDateTextFormat(start_date, event_format)
            
        self.update_event_stats()
        
    def update_date_display(self):
        """Update selected date display"""
        date_text = self.selected_date.toString("dddd, MMMM d, yyyy")
        self.selected_date_label.setText(date_text)
        
    def update_day_events(self):
        """Update events list for selected date"""
        self.day_events_list.clear()
        
        selected_date_str = self.selected_date.toString('yyyy-MM-dd')
        day_events = []
        
        for event in self.events:
            event_date = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date()
            if event_date.toString('yyyy-MM-dd') == selected_date_str:
                day_events.append(event)
                
        # Sort events by time
        day_events.sort(key=lambda e: e['start_datetime'])
        
        for event in day_events:
            if event['all_day']:
                time_text = "All Day"
            else:
                start_time = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').time()
                time_text = start_time.toString('hh:mm')
                
            priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(event['priority'], "⚪")
            item_text = f"{time_text} - {priority_icon} {event['title']}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, event)
            self.day_events_list.addItem(item)
            
        # Update week and upcoming events
        self.update_week_events()
        self.update_upcoming_events()
        
    def update_week_events(self):
        """Update week events display"""
        self.week_events_list.clear()
        
        # Get week start (Monday)
        week_start = self.selected_date.addDays(-self.selected_date.dayOfWeek() + 1)
        week_end = week_start.addDays(6)
        
        week_events = []
        for event in self.events:
            event_date = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date()
            if week_start <= event_date <= week_end:
                week_events.append(event)
                
        week_events.sort(key=lambda e: e['start_datetime'])
        
        for event in week_events:
            event_date = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date()
            day_name = event_date.toString('dddd')
            
            if event['all_day']:
                time_text = "All Day"
            else:
                start_time = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').time()
                time_text = start_time.toString('hh:mm')
                
            item_text = f"{day_name} {time_text} - {event['title']}"
            self.week_events_list.addItem(item_text)
            
    def update_upcoming_events(self):
        """Update upcoming events display"""
        self.upcoming_events_list.clear()
        
        current_datetime = QDateTime.currentDateTime()
        upcoming_events = []
        
        for event in self.events:
            event_datetime = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm')
            if event_datetime > current_datetime:
                upcoming_events.append(event)
                
        upcoming_events.sort(key=lambda e: e['start_datetime'])
        
        for event in upcoming_events[:10]:  # Show next 10 events
            event_datetime = QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm')
            date_text = event_datetime.toString('MMM d, hh:mm')
            
            priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(event['priority'], "⚪")
            item_text = f"{date_text} - {priority_icon} {event['title']}"
            self.upcoming_events_list.addItem(item_text)
            
    def update_event_stats(self):
        """Update event statistics"""
        today = QDate.currentDate()
        today_str = today.toString('yyyy-MM-dd')
        
        # Count events
        events_today = sum(1 for event in self.events 
                          if QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date().toString('yyyy-MM-dd') == today_str)
        
        week_start = today.addDays(-today.dayOfWeek() + 1)
        week_end = week_start.addDays(6)
        events_week = sum(1 for event in self.events 
                         if week_start <= QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date() <= week_end)
        
        month_start = QDate(today.year(), today.month(), 1)
        month_end = month_start.addMonths(1).addDays(-1)
        events_month = sum(1 for event in self.events 
                          if month_start <= QDateTime.fromString(event['start_datetime'], 'yyyy-MM-dd hh:mm').date() <= month_end)
        
        self.events_today_label.setText(f"Today: {events_today} events")
        self.events_week_label.setText(f"This week: {events_week} events")
        self.events_month_label.setText(f"This month: {events_month} events")
        
    def select_event(self, item):
        """Handle event selection"""
        event = item.data(Qt.UserRole)
        if event:
            self.edit_event_btn.setEnabled(True)
            self.delete_event_btn.setEnabled(True)
            
    def create_new_event(self):
        """Create a new event"""
        dialog = EventDialog(selected_date=self.selected_date, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            event_data = dialog.get_event_data()
            if event_data['title']:
                self.events.append(event_data)
                self.update_calendar_display()
                self.update_day_events()
                self.event_created.emit(event_data)
                self.status_label.setText(f"Created event: {event_data['title']}")
                
    def edit_selected_event(self):
        """Edit the selected event"""
        current_item = self.day_events_list.currentItem()
        if current_item:
            event = current_item.data(Qt.UserRole)
            if event:
                dialog = EventDialog(event=event, parent=self)
                if dialog.exec_() == QDialog.Accepted:
                    updated_data = dialog.get_event_data()
                    if updated_data['title']:
                        # Find and update original event
                        original_index = self.events.index(event)
                        self.events[original_index] = updated_data
                        self.update_calendar_display()
                        self.update_day_events()
                        self.event_updated.emit(updated_data)
                        self.status_label.setText(f"Updated event: {updated_data['title']}")
                        
    def delete_selected_event(self):
        """Delete the selected event"""
        current_item = self.day_events_list.currentItem()
        if current_item:
            event = current_item.data(Qt.UserRole)
            if event:
                reply = QMessageBox.question(
                    self, "Delete Event",
                    f"Are you sure you want to delete the event '{event['title']}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    original_index = self.events.index(event)
                    self.events.remove(event)
                    
                    self.update_calendar_display()
                    self.update_day_events()
                    self.event_deleted.emit(original_index)
                    self.status_label.setText(f"Deleted event: {event['title']}")
                    
                    # Clear selection
                    self.edit_event_btn.setEnabled(False)
                    self.delete_event_btn.setEnabled(False)
