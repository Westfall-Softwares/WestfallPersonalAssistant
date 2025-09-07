"""
WestfallPersonalAssistant Progress Indicators
Provides visual feedback for user actions and long-running operations
"""

import math
import time
from typing import Optional, Callable, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFrame, QApplication, QDialog, QDialogButtonBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, 
    QRect, QPoint, QSize, QThread
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from util.app_theme import AppTheme


class ProgressOverlay(QWidget):
    """Overlay widget that shows progress over the entire application"""
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, message="Loading...", show_cancel=True):
        super().__init__(parent)
        self.message = message
        self.progress_value = 0
        self.is_indeterminate = True
        self.show_cancel = show_cancel
        
        # Setup widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Create layout
        self.setup_ui()
        
        # Animation for spinning indicator
        self.angle = 0
        self.spin_timer = QTimer()
        self.spin_timer.timeout.connect(self.update_spinner)
        self.spin_timer.start(50)  # 20 FPS
        
        # Fade animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Create central frame
        self.frame = QFrame()
        self.frame.setFixedSize(300, 150)
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {AppTheme.SECONDARY_BG};
                border: 2px solid {AppTheme.PRIMARY_COLOR};
                border-radius: 10px;
            }}
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setSpacing(15)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
                font-size: {AppTheme.FONT_MEDIUM}px;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)
        frame_layout.addWidget(self.message_label)
        
        # Progress area
        self.progress_widget = QWidget()
        self.progress_widget.setFixedHeight(40)
        frame_layout.addWidget(self.progress_widget)
        
        # Cancel button
        if self.show_cancel:
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self.cancelled.emit)
            self.cancel_button.setStyleSheet(AppTheme.get_button_style(primary=False, size="small"))
            frame_layout.addWidget(self.cancel_button)
        
        layout.addWidget(self.frame)
        self.setLayout(layout)
    
    def paintEvent(self, event):
        """Custom paint event for background and spinner"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
        
        # Draw spinner or progress bar
        if self.is_indeterminate:
            self.draw_spinner(painter)
        else:
            self.draw_progress_bar(painter)
    
    def draw_spinner(self, painter):
        """Draw animated spinner"""
        center = self.progress_widget.geometry().center()
        
        # Spinner properties
        radius = 15
        dot_radius = 3
        num_dots = 8
        
        painter.setPen(Qt.NoPen)
        
        for i in range(num_dots):
            # Calculate dot position
            angle = (self.angle + i * 45) * math.pi / 180
            x = center.x() + radius * math.cos(angle) - dot_radius
            y = center.y() + radius * math.sin(angle) - dot_radius
            
            # Fade effect for trailing dots
            opacity = max(0.2, 1.0 - (i / num_dots))
            color = QColor(AppTheme.PRIMARY_COLOR)
            color.setAlphaF(opacity)
            
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x), int(y), dot_radius * 2, dot_radius * 2)
    
    def draw_progress_bar(self, painter):
        """Draw progress bar"""
        progress_rect = self.progress_widget.geometry()
        progress_rect.moveCenter(self.frame.geometry().center())
        progress_rect.setHeight(6)
        
        # Background
        painter.setPen(QPen(QColor(AppTheme.SECONDARY_BG), 1))
        painter.setBrush(QBrush(QColor(AppTheme.TERTIARY_BG)))
        painter.drawRoundedRect(progress_rect, 3, 3)
        
        # Progress fill
        if self.progress_value > 0:
            fill_width = int((progress_rect.width() * self.progress_value) / 100)
            fill_rect = QRect(progress_rect.left(), progress_rect.top(), fill_width, progress_rect.height())
            
            painter.setBrush(QBrush(QColor(AppTheme.PRIMARY_COLOR)))
            painter.drawRoundedRect(fill_rect, 3, 3)
    
    def update_spinner(self):
        """Update spinner animation"""
        if self.is_indeterminate:
            self.angle = (self.angle + 10) % 360
            self.update()
    
    def set_progress(self, value: int):
        """Set progress value (0-100) and switch to determinate mode"""
        self.progress_value = max(0, min(100, value))
        self.is_indeterminate = False
        self.update()
    
    def set_indeterminate(self, indeterminate: bool = True):
        """Switch between determinate and indeterminate progress"""
        self.is_indeterminate = indeterminate
        self.update()
    
    def set_message(self, message: str):
        """Update the progress message"""
        self.message = message
        self.message_label.setText(message)
    
    def show_animated(self):
        """Show the overlay with fade-in animation"""
        self.show()
        self.raise_()
        
        # Resize to parent
        if self.parent():
            self.resize(self.parent().size())
        
        # Fade in
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def hide_animated(self):
        """Hide the overlay with fade-out animation"""
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Keep frame centered
        self.frame.move(
            (self.width() - self.frame.width()) // 2,
            (self.height() - self.frame.height()) // 2
        )


class LoadingSpinner(QWidget):
    """Standalone loading spinner widget"""
    
    def __init__(self, parent=None, size=32, color=None):
        super().__init__(parent)
        self.size = size
        self.color = QColor(color or AppTheme.PRIMARY_COLOR)
        self.angle = 0
        
        self.setFixedSize(size, size)
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
    
    def start(self):
        """Start the spinner animation"""
        self.timer.start(50)  # 20 FPS
        self.show()
    
    def stop(self):
        """Stop the spinner animation"""
        self.timer.stop()
        self.hide()
    
    def update_animation(self):
        """Update animation frame"""
        self.angle = (self.angle + 15) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw spinner
        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 2
        
        painter.setPen(Qt.NoPen)
        
        # Draw dots
        num_dots = 8
        dot_radius = max(2, radius // 6)
        
        for i in range(num_dots):
            angle = (self.angle + i * 45) * math.pi / 180
            x = center.x() + (radius - dot_radius) * math.cos(angle) - dot_radius
            y = center.y() + (radius - dot_radius) * math.sin(angle) - dot_radius
            
            # Fade effect
            opacity = max(0.3, 1.0 - (i / num_dots))
            color = QColor(self.color)
            color.setAlphaF(opacity)
            
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x), int(y), dot_radius * 2, dot_radius * 2)


class ProgressDialog(QDialog):
    """Progress dialog with cancel support"""
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, title="Progress", message="Processing...", 
                 show_cancel=True, show_percentage=True):
        super().__init__(parent)
        self.show_cancel = show_cancel
        self.show_percentage = show_percentage
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        # Apply theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
        """)
        
        self.setup_ui(message)
    
    def setup_ui(self, message):
        """Setup the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {AppTheme.TEXT_PRIMARY};
                font-size: {AppTheme.FONT_MEDIUM}px;
            }}
        """)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {AppTheme.BORDER_COLOR};
                border-radius: 5px;
                text-align: center;
                background-color: {AppTheme.SECONDARY_BG};
            }}
            QProgressBar::chunk {{
                background-color: {AppTheme.PRIMARY_COLOR};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Percentage label
        if self.show_percentage:
            self.percentage_label = QLabel("0%")
            self.percentage_label.setAlignment(Qt.AlignCenter)
            self.percentage_label.setStyleSheet(f"""
                QLabel {{
                    color: {AppTheme.TEXT_SECONDARY};
                    font-size: {AppTheme.FONT_SMALL}px;
                }}
            """)
            layout.addWidget(self.percentage_label)
        
        # Buttons
        if self.show_cancel:
            button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
            button_box.rejected.connect(self.cancelled.emit)
            button_box.setStyleSheet(AppTheme.get_button_style(primary=False))
            layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def set_progress(self, value: int, message: str = None):
        """Update progress value and optional message"""
        self.progress_bar.setValue(value)
        
        if self.show_percentage:
            self.percentage_label.setText(f"{value}%")
        
        if message:
            self.message_label.setText(message)
        
        QApplication.processEvents()  # Keep UI responsive
    
    def set_indeterminate(self, indeterminate: bool = True):
        """Set indeterminate progress mode"""
        if indeterminate:
            self.progress_bar.setRange(0, 0)  # Indeterminate mode
        else:
            self.progress_bar.setRange(0, 100)


class ProgressTracker:
    """Utility class for tracking progress of long-running operations"""
    
    def __init__(self, total_steps: int, callback: Callable[[int, str], None] = None):
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.start_time = time.time()
        
    def step(self, message: str = "", increment: int = 1):
        """Advance progress by one or more steps"""
        self.current_step = min(self.total_steps, self.current_step + increment)
        percentage = int((self.current_step / self.total_steps) * 100)
        
        if self.callback:
            self.callback(percentage, message)
    
    def set_step(self, step: int, message: str = ""):
        """Set current step directly"""
        self.current_step = min(self.total_steps, max(0, step))
        percentage = int((self.current_step / self.total_steps) * 100)
        
        if self.callback:
            self.callback(percentage, message)
    
    def get_progress(self) -> int:
        """Get current progress percentage"""
        return int((self.current_step / self.total_steps) * 100)
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def get_estimated_remaining(self) -> float:
        """Get estimated remaining time in seconds"""
        if self.current_step == 0:
            return 0
        
        elapsed = self.get_elapsed_time()
        rate = self.current_step / elapsed
        remaining_steps = self.total_steps - self.current_step
        
        return remaining_steps / rate if rate > 0 else 0


# Context manager for progress tracking
class progress_context:
    """Context manager for automatic progress tracking"""
    
    def __init__(self, parent=None, title="Progress", message="Processing...", 
                 total_steps=100, show_cancel=True):
        self.parent = parent
        self.title = title
        self.message = message
        self.total_steps = total_steps
        self.show_cancel = show_cancel
        self.dialog = None
        self.tracker = None
        self.cancelled = False
    
    def __enter__(self):
        # Create progress dialog
        self.dialog = ProgressDialog(
            self.parent, self.title, self.message, self.show_cancel
        )
        
        if self.show_cancel:
            self.dialog.cancelled.connect(self._on_cancelled)
        
        # Create tracker
        self.tracker = ProgressTracker(
            self.total_steps, 
            lambda progress, msg: self.dialog.set_progress(progress, msg)
        )
        
        self.dialog.show()
        return self.tracker
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dialog:
            self.dialog.close()
    
    def _on_cancelled(self):
        self.cancelled = True


# Global progress overlay instance
_global_progress_overlay = None

def show_global_progress(parent=None, message="Loading...", show_cancel=True):
    """Show global progress overlay"""
    global _global_progress_overlay
    
    if _global_progress_overlay is None:
        _global_progress_overlay = ProgressOverlay(parent, message, show_cancel)
    else:
        _global_progress_overlay.set_message(message)
    
    _global_progress_overlay.show_animated()
    return _global_progress_overlay

def hide_global_progress():
    """Hide global progress overlay"""
    global _global_progress_overlay
    
    if _global_progress_overlay:
        _global_progress_overlay.hide_animated()

def set_global_progress(value: int, message: str = None):
    """Update global progress"""
    global _global_progress_overlay
    
    if _global_progress_overlay:
        _global_progress_overlay.set_progress(value)
        if message:
            _global_progress_overlay.set_message(message)