"""
Task Manager UI Component for Westfall Personal Assistant

Provides visual task management interface with red/black theme integration.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QListWidget, QListWidgetItem, QLineEdit,
                           QTextEdit, QComboBox, QDateEdit, QCheckBox,
                           QSplitter, QGroupBox, QFormLayout, QTabWidget,
                           QTreeWidget, QTreeWidgetItem, QProgressBar,
                           QMessageBox, QDialog, QDialogButtonBox,
                           QSpinBox, QScrollArea)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from utils.app_theme import AppTheme
import logging

logger = logging.getLogger(__name__)


class TaskDialog(QDialog):
    """Dialog for creating/editing tasks"""
    
    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()
        self.apply_theme()
        
        if task:
            self.load_task_data()
            
    def init_ui(self):
        """Initialize the task dialog"""
        self.setWindowTitle("Create Task" if not self.task else "Edit Task")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Task title
        self.title_field = QLineEdit()
        self.title_field.setPlaceholderText("Enter task title...")
        form_layout.addRow("Title:", self.title_field)
        
        # Description
        self.description_field = QTextEdit()
        self.description_field.setMaximumHeight(100)
        self.description_field.setPlaceholderText("Task description...")
        form_layout.addRow("Description:", self.description_field)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentIndex(1)  # Default to Medium
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Business", "Learning", "Health", "Other"])
        form_layout.addRow("Category:", self.category_combo)
        
        # Due date
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(1))
        self.due_date.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date)
        
        # Estimated hours
        self.estimated_hours = QSpinBox()
        self.estimated_hours.setRange(0, 100)
        self.estimated_hours.setValue(1)
        self.estimated_hours.setSuffix(" hours")
        form_layout.addRow("Estimated Time:", self.estimated_hours)
        
        # Completed checkbox
        self.completed_check = QCheckBox("Mark as completed")
        form_layout.addRow("Status:", self.completed_check)
        
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
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_SMALL}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {{
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
        
    def load_task_data(self):
        """Load existing task data into form"""
        if self.task:
            self.title_field.setText(self.task.get('title', ''))
            self.description_field.setPlainText(self.task.get('description', ''))
            
            priority = self.task.get('priority', 'Medium')
            priority_index = self.priority_combo.findText(priority)
            if priority_index >= 0:
                self.priority_combo.setCurrentIndex(priority_index)
                
            category = self.task.get('category', 'Work')
            category_index = self.category_combo.findText(category)
            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)
                
            self.completed_check.setChecked(self.task.get('completed', False))
            
    def get_task_data(self):
        """Get task data from form"""
        return {
            'title': self.title_field.text().strip(),
            'description': self.description_field.toPlainText().strip(),
            'priority': self.priority_combo.currentText(),
            'category': self.category_combo.currentText(),
            'due_date': self.due_date.date().toString('yyyy-MM-dd'),
            'estimated_hours': self.estimated_hours.value(),
            'completed': self.completed_check.isChecked()
        }


class TaskManagerUI(QWidget):
    """Task management interface with visual task tracking"""
    
    task_created = pyqtSignal(dict)
    task_updated = pyqtSignal(dict)
    task_deleted = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.filtered_tasks = []
        self.current_filter = "All"
        
        self.init_ui()
        self.apply_theme()
        self.load_sample_tasks()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_displays)
        self.refresh_timer.start(60000)  # Refresh every minute
        
    def init_ui(self):
        """Initialize the task manager interface"""
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("✅ Task Manager")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Task controls
        self.new_task_btn = QPushButton("➕ New Task")
        self.new_task_btn.clicked.connect(self.create_new_task)
        header_layout.addWidget(self.new_task_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filters and search
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Active", "Completed", "Overdue", "Today", "This Week"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories", "Work", "Personal", "Business", "Learning", "Health", "Other"])
        self.category_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Search tasks...")
        self.search_field.textChanged.connect(self.search_tasks)
        filter_layout.addWidget(self.search_field)
        
        layout.addLayout(filter_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - Task list and stats
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Task details and progress
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([600, 400])
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def create_left_panel(self):
        """Create the left panel with task list"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick stats
        stats_group = QGroupBox("📊 Overview")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_tasks_label = QLabel("Total: 0")
        self.active_tasks_label = QLabel("Active: 0")
        self.completed_tasks_label = QLabel("Completed: 0")
        self.overdue_tasks_label = QLabel("Overdue: 0")
        
        stats_layout.addWidget(self.total_tasks_label)
        stats_layout.addWidget(self.active_tasks_label)
        stats_layout.addWidget(self.completed_tasks_label)
        stats_layout.addWidget(self.overdue_tasks_label)
        
        layout.addWidget(stats_group)
        
        # Task list
        list_label = QLabel("📋 Tasks")
        list_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(list_label)
        
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.select_task)
        self.task_list.itemDoubleClicked.connect(self.edit_selected_task)
        layout.addWidget(self.task_list)
        
        # Task actions
        actions_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_selected_task)
        self.edit_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_btn)
        
        self.complete_btn = QPushButton("✅ Complete")
        self.complete_btn.clicked.connect(self.toggle_task_completion)
        self.complete_btn.setEnabled(False)
        actions_layout.addWidget(self.complete_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_selected_task)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def create_right_panel(self):
        """Create the right panel with task details"""
        widget = QTabWidget()
        
        # Task details tab
        details_widget = QScrollArea()
        details_content = QWidget()
        details_layout = QVBoxLayout(details_content)
        
        # Task info display
        self.task_details = QLabel("Select a task to view details")
        self.task_details.setAlignment(Qt.AlignTop)
        self.task_details.setWordWrap(True)
        details_layout.addWidget(self.task_details)
        
        details_layout.addStretch()
        details_widget.setWidget(details_content)
        details_widget.setWidgetResizable(True)
        
        widget.addTab(details_widget, "📝 Details")
        
        # Progress tab
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        
        # Progress charts
        progress_label = QLabel("📈 Progress Overview")
        progress_label.setFont(QFont("Arial", 12, QFont.Bold))
        progress_layout.addWidget(progress_label)
        
        # Completion progress
        completion_group = QGroupBox("Task Completion")
        completion_layout = QVBoxLayout(completion_group)
        
        self.completion_progress = QProgressBar()
        self.completion_progress.setFormat("%p% Complete")
        completion_layout.addWidget(self.completion_progress)
        
        self.completion_label = QLabel("0 of 0 tasks completed")
        completion_layout.addWidget(self.completion_label)
        
        progress_layout.addWidget(completion_group)
        
        # Priority breakdown
        priority_group = QGroupBox("Priority Breakdown")
        priority_layout = QVBoxLayout(priority_group)
        
        self.critical_progress = QProgressBar()
        self.critical_progress.setFormat("Critical: %v")
        priority_layout.addWidget(self.critical_progress)
        
        self.high_progress = QProgressBar()
        self.high_progress.setFormat("High: %v")
        priority_layout.addWidget(self.high_progress)
        
        self.medium_progress = QProgressBar()
        self.medium_progress.setFormat("Medium: %v")
        priority_layout.addWidget(self.medium_progress)
        
        self.low_progress = QProgressBar()
        self.low_progress.setFormat("Low: %v")
        priority_layout.addWidget(self.low_progress)
        
        progress_layout.addWidget(priority_group)
        
        progress_layout.addStretch()
        
        widget.addTab(progress_widget, "📊 Progress")
        
        return widget
        
    def apply_theme(self):
        """Apply red/black theme to task manager"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
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
            QComboBox, QLineEdit {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_SMALL}px;
            }}
            QComboBox:focus, QLineEdit:focus {{
                border-color: {AppTheme.HIGHLIGHT_COLOR};
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
            QProgressBar {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                background-color: {AppTheme.SECONDARY_BG};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {AppTheme.PRIMARY_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
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
        
    def load_sample_tasks(self):
        """Load sample tasks for demonstration"""
        sample_tasks = [
            {
                'title': 'Review quarterly reports',
                'description': 'Analyze Q3 financial data and prepare summary',
                'priority': 'High',
                'category': 'Work',
                'due_date': '2024-12-15',
                'estimated_hours': 4,
                'completed': False
            },
            {
                'title': 'Update project documentation',
                'description': 'Complete API documentation for new features',
                'priority': 'Medium',
                'category': 'Work',
                'due_date': '2024-12-20',
                'estimated_hours': 2,
                'completed': False
            },
            {
                'title': 'Plan holiday vacation',
                'description': 'Book flights and accommodation for December trip',
                'priority': 'Low',
                'category': 'Personal',
                'due_date': '2024-12-10',
                'estimated_hours': 1,
                'completed': True
            }
        ]
        
        self.tasks = sample_tasks
        self.refresh_display()
        
    def refresh_tasks(self):
        """Refresh task display"""
        self.refresh_display()
        self.status_label.setText("Tasks refreshed")
        
    def refresh_display(self):
        """Refresh all display elements"""
        self.apply_filter()
        self.update_stats()
        self.update_progress_charts()
        
    def apply_filter(self):
        """Apply current filter to task list"""
        current_filter = self.filter_combo.currentText()
        category_filter = self.category_filter.currentText()
        
        self.filtered_tasks = []
        
        for task in self.tasks:
            # Apply status filter
            if current_filter == "Active" and task['completed']:
                continue
            elif current_filter == "Completed" and not task['completed']:
                continue
            # Add more filter logic here (Overdue, Today, This Week)
            
            # Apply category filter
            if category_filter != "All Categories" and task['category'] != category_filter:
                continue
                
            self.filtered_tasks.append(task)
            
        self.update_task_list()
        
    def search_tasks(self, text):
        """Search tasks by title and description"""
        if not text:
            self.apply_filter()
            return
            
        search_results = []
        for task in self.filtered_tasks:
            if (text.lower() in task['title'].lower() or 
                text.lower() in task['description'].lower()):
                search_results.append(task)
                
        self.filtered_tasks = search_results
        self.update_task_list()
        
    def update_task_list(self):
        """Update the task list widget"""
        self.task_list.clear()
        
        for i, task in enumerate(self.filtered_tasks):
            status_icon = "✅" if task['completed'] else "⏳"
            priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(task['priority'], "⚪")
            
            item_text = f"{status_icon} {priority_icon} {task['title']} ({task['category']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)  # Store task index
            self.task_list.addItem(item)
            
    def update_stats(self):
        """Update task statistics"""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task['completed'])
        active = total - completed
        overdue = 0  # Would calculate based on due dates
        
        self.total_tasks_label.setText(f"Total: {total}")
        self.active_tasks_label.setText(f"Active: {active}")
        self.completed_tasks_label.setText(f"Completed: {completed}")
        self.overdue_tasks_label.setText(f"Overdue: {overdue}")
        
    def update_progress_charts(self):
        """Update progress visualization"""
        if not self.tasks:
            return
            
        # Completion progress
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task['completed'])
        completion_percent = int((completed / total) * 100) if total > 0 else 0
        
        self.completion_progress.setValue(completion_percent)
        self.completion_label.setText(f"{completed} of {total} tasks completed")
        
        # Priority breakdown
        priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for task in self.tasks:
            priority_counts[task['priority']] += 1
            
        max_count = max(priority_counts.values()) if priority_counts.values() else 1
        
        self.critical_progress.setMaximum(max_count)
        self.critical_progress.setValue(priority_counts["Critical"])
        
        self.high_progress.setMaximum(max_count)
        self.high_progress.setValue(priority_counts["High"])
        
        self.medium_progress.setMaximum(max_count)
        self.medium_progress.setValue(priority_counts["Medium"])
        
        self.low_progress.setMaximum(max_count)
        self.low_progress.setValue(priority_counts["Low"])
        
    def select_task(self, item):
        """Handle task selection"""
        task_index = item.data(Qt.UserRole)
        if task_index is not None and 0 <= task_index < len(self.filtered_tasks):
            task = self.filtered_tasks[task_index]
            self.display_task_details(task)
            
            # Enable action buttons
            self.edit_btn.setEnabled(True)
            self.complete_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
            # Update complete button text
            if task['completed']:
                self.complete_btn.setText("↩️ Reopen")
            else:
                self.complete_btn.setText("✅ Complete")
                
    def display_task_details(self, task):
        """Display detailed task information"""
        status = "✅ Completed" if task['completed'] else "⏳ Active"
        priority_color = {"Critical": "#ff4444", "High": "#ff8844", "Medium": "#ffff44", "Low": "#44ff44"}.get(task['priority'], "#ffffff")
        
        details_html = f"""
        <div style="padding: 10px;">
            <h2 style="color: {AppTheme.PRIMARY_COLOR};">{task['title']}</h2>
            
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Priority:</strong> <span style="color: {priority_color};">⬤ {task['priority']}</span></p>
            <p><strong>Category:</strong> {task['category']}</p>
            <p><strong>Due Date:</strong> {task['due_date']}</p>
            <p><strong>Estimated Time:</strong> {task['estimated_hours']} hours</p>
            
            <h3 style="color: {AppTheme.HIGHLIGHT_COLOR};">Description:</h3>
            <p>{task['description']}</p>
        </div>
        """
        
        self.task_details.setText(details_html)
        
    def create_new_task(self):
        """Create a new task"""
        dialog = TaskDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            task_data = dialog.get_task_data()
            if task_data['title']:
                self.tasks.append(task_data)
                self.refresh_display()
                self.task_created.emit(task_data)
                self.status_label.setText(f"Created task: {task_data['title']}")
                
    def edit_selected_task(self):
        """Edit the selected task"""
        current_item = self.task_list.currentItem()
        if current_item:
            task_index = current_item.data(Qt.UserRole)
            if task_index is not None and 0 <= task_index < len(self.filtered_tasks):
                task = self.filtered_tasks[task_index]
                
                dialog = TaskDialog(task=task, parent=self)
                if dialog.exec_() == QDialog.Accepted:
                    updated_data = dialog.get_task_data()
                    if updated_data['title']:
                        # Find original task and update
                        original_index = self.tasks.index(task)
                        self.tasks[original_index] = updated_data
                        self.refresh_display()
                        self.task_updated.emit(updated_data)
                        self.status_label.setText(f"Updated task: {updated_data['title']}")
                        
    def toggle_task_completion(self):
        """Toggle completion status of selected task"""
        current_item = self.task_list.currentItem()
        if current_item:
            task_index = current_item.data(Qt.UserRole)
            if task_index is not None and 0 <= task_index < len(self.filtered_tasks):
                task = self.filtered_tasks[task_index]
                
                # Find original task and update
                original_index = self.tasks.index(task)
                self.tasks[original_index]['completed'] = not task['completed']
                
                action = "completed" if self.tasks[original_index]['completed'] else "reopened"
                self.refresh_display()
                self.status_label.setText(f"Task {action}: {task['title']}")
                
    def delete_selected_task(self):
        """Delete the selected task"""
        current_item = self.task_list.currentItem()
        if current_item:
            task_index = current_item.data(Qt.UserRole)
            if task_index is not None and 0 <= task_index < len(self.filtered_tasks):
                task = self.filtered_tasks[task_index]
                
                reply = QMessageBox.question(
                    self, "Delete Task",
                    f"Are you sure you want to delete the task '{task['title']}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Find original task and remove
                    original_index = self.tasks.index(task)
                    self.tasks.pop(original_index)
                    
                    self.refresh_display()
                    self.task_deleted.emit(original_index)
                    self.status_label.setText(f"Deleted task: {task['title']}")
                    
                    # Clear selection
                    self.edit_btn.setEnabled(False)
                    self.complete_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    self.task_details.setText("Select a task to view details")
                    
    def update_displays(self):
        """Auto-update displays"""
        self.update_stats()
        self.update_progress_charts()
