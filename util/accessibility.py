"""
WestfallPersonalAssistant Accessibility Manager
Provides accessibility features and improvements for better usability
"""

from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QApplication, QLabel, QPushButton, QMainWindow,
    QToolTip, QShortcut, QAction, QMenu
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import (
    QFont, QFontMetrics, QKeySequence, QPalette, QColor,
    QPixmap, QIcon
)

# Try to import QAccessible, fallback if not available
try:
    from PyQt5.QtWidgets import QAccessibleWidget
    QAccessible = QAccessibleWidget
except ImportError:
    try:
        from PyQt5.QtCore import QObject
        class QAccessible:
            Alert = 0
            @staticmethod
            def updateAccessibility(widget, child, reason):
                pass  # Fallback implementation
    except ImportError:
        QAccessible = None
from util.app_theme import AppTheme


class AccessibilityManager(QObject):
    """Manages accessibility features across the application"""
    
    # Signals
    font_size_changed = pyqtSignal(int)
    contrast_mode_changed = pyqtSignal(bool)
    screen_reader_mode_changed = pyqtSignal(bool)
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(AccessibilityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize accessibility manager"""
        if self._initialized:
            return
            
        super().__init__()
        
        # Settings
        self.base_font_size = AppTheme.FONT_MEDIUM
        self.font_scale_factor = 1.0
        self.high_contrast_mode = False
        self.screen_reader_mode = False
        self.keyboard_navigation_enabled = True
        self.focus_indicators_enhanced = True
        
        # Minimum font sizes for accessibility
        self.min_font_sizes = {
            'small': 14,      # Minimum 14px for small text
            'medium': 16,     # Minimum 16px for medium text
            'large': 18,      # Minimum 18px for large text
            'header': 22      # Minimum 22px for headers
        }
        
        # Color contrast ratios (WCAG AA compliant)
        self.contrast_colors = {
            'background': '#000000',
            'text': '#ffffff',
            'primary': '#ff4444',      # Higher contrast red
            'secondary': '#bb0000',    # Darker red for better contrast
            'border': '#ff6666',       # Lighter red for borders
            'success': '#00dd00',      # Brighter green
            'warning': '#ffdd00',      # Brighter yellow
            'error': '#ff4444',        # High contrast red
            'info': '#00bbff'          # High contrast blue
        }
        
        # Screen reader hints
        self.screen_reader_hints = {}
        
        # Keyboard shortcuts
        self.keyboard_shortcuts = {}
        
        self._initialized = True
    
    def increase_font_size(self, increment: float = 0.1):
        """Increase font size by scale factor"""
        new_scale = min(2.0, self.font_scale_factor + increment)
        self.set_font_scale(new_scale)
    
    def decrease_font_size(self, decrement: float = 0.1):
        """Decrease font size by scale factor"""
        new_scale = max(0.8, self.font_scale_factor - decrement)
        self.set_font_scale(new_scale)
    
    def set_font_scale(self, scale_factor: float):
        """Set font scale factor and update all fonts"""
        self.font_scale_factor = scale_factor
        self.update_application_fonts()
        self.font_size_changed.emit(int(self.base_font_size * scale_factor))
    
    def update_application_fonts(self):
        """Update fonts across the entire application"""
        app = QApplication.instance()
        if not app:
            return
        
        # Calculate scaled font sizes
        scaled_sizes = {}
        for size_name, base_size in {
            'small': AppTheme.FONT_SMALL,
            'medium': AppTheme.FONT_MEDIUM,
            'large': AppTheme.FONT_LARGE,
            'xlarge': AppTheme.FONT_XLARGE,
            'header': AppTheme.FONT_HEADER
        }.items():
            scaled_size = int(base_size * self.font_scale_factor)
            min_size = self.min_font_sizes.get(size_name, base_size)
            scaled_sizes[size_name] = max(min_size, scaled_size)
        
        # Update application font
        app_font = app.font()
        app_font.setPointSize(scaled_sizes['medium'])
        app.setFont(app_font)
        
        # Update theme font sizes
        AppTheme.FONT_SMALL = scaled_sizes['small']
        AppTheme.FONT_MEDIUM = scaled_sizes['medium']
        AppTheme.FONT_LARGE = scaled_sizes['large']
        AppTheme.FONT_XLARGE = scaled_sizes['xlarge']
        AppTheme.FONT_HEADER = scaled_sizes['header']
        
        # Refresh all widgets
        self.refresh_widget_styles()
    
    def toggle_high_contrast_mode(self):
        """Toggle high contrast mode"""
        self.high_contrast_mode = not self.high_contrast_mode
        self.apply_contrast_mode()
        self.contrast_mode_changed.emit(self.high_contrast_mode)
    
    def apply_contrast_mode(self):
        """Apply high contrast colors"""
        if self.high_contrast_mode:
            # Update theme colors for high contrast
            AppTheme.BACKGROUND = self.contrast_colors['background']
            AppTheme.TEXT_PRIMARY = self.contrast_colors['text']
            AppTheme.PRIMARY_COLOR = self.contrast_colors['primary']
            AppTheme.SECONDARY_COLOR = self.contrast_colors['secondary']
            AppTheme.BORDER_COLOR = self.contrast_colors['border']
            AppTheme.SUCCESS_COLOR = self.contrast_colors['success']
            AppTheme.WARNING_COLOR = self.contrast_colors['warning']
            AppTheme.ERROR_COLOR = self.contrast_colors['error']
            AppTheme.INFO_COLOR = self.contrast_colors['info']
        else:
            # Restore original colors
            AppTheme.BACKGROUND = "#000000"
            AppTheme.TEXT_PRIMARY = "#ffffff"
            AppTheme.PRIMARY_COLOR = "#ff0000"
            AppTheme.SECONDARY_COLOR = "#cc0000"
            AppTheme.BORDER_COLOR = "#ff0000"
            AppTheme.SUCCESS_COLOR = "#00cc00"
            AppTheme.WARNING_COLOR = "#ffcc00"
            AppTheme.ERROR_COLOR = "#ff0000"
            AppTheme.INFO_COLOR = "#0099ff"
        
        # Apply theme to application
        AppTheme.apply_to_application()
        self.refresh_widget_styles()
    
    def enable_screen_reader_mode(self, enabled: bool = True):
        """Enable or disable screen reader optimizations"""
        self.screen_reader_mode = enabled
        
        if enabled:
            # Enable accessibility features
            self.enable_enhanced_focus_indicators()
            self.add_screen_reader_hints()
        
        self.screen_reader_mode_changed.emit(enabled)
    
    def enable_enhanced_focus_indicators(self):
        """Enable enhanced focus indicators for keyboard navigation"""
        self.focus_indicators_enhanced = True
        
        # Apply enhanced focus styles
        app = QApplication.instance()
        if app:
            enhanced_focus_style = f"""
                *:focus {{
                    border: 3px solid {AppTheme.PRIMARY_COLOR};
                    outline: 2px solid {AppTheme.TEXT_PRIMARY};
                    outline-offset: 1px;
                }}
                QPushButton:focus {{
                    border: 3px solid {AppTheme.HIGHLIGHT_COLOR};
                    background-color: {AppTheme.SECONDARY_COLOR};
                }}
                QLineEdit:focus, QTextEdit:focus {{
                    border: 3px solid {AppTheme.HIGHLIGHT_COLOR};
                    background-color: {AppTheme.SECONDARY_BG};
                }}
            """
            
            # Apply to existing stylesheet
            current_style = app.styleSheet()
            app.setStyleSheet(current_style + enhanced_focus_style)
    
    def add_screen_reader_hints(self):
        """Add screen reader hints to widgets"""
        app = QApplication.instance()
        if not app:
            return
        
        # Find and enhance widgets
        for widget in app.allWidgets():
            self.enhance_widget_accessibility(widget)
    
    def enhance_widget_accessibility(self, widget: QWidget):
        """Enhance accessibility for a specific widget"""
        if not widget:
            return
        
        # Add accessible names and descriptions
        widget_type = type(widget).__name__
        
        if isinstance(widget, QPushButton):
            if not widget.accessibleName():
                text = widget.text() or "Button"
                widget.setAccessibleName(text)
                widget.setAccessibleDescription(f"Button: {text}")
        
        elif isinstance(widget, QLabel):
            if not widget.accessibleName():
                text = widget.text() or "Label"
                widget.setAccessibleName(text)
                if widget.buddy():
                    widget.setAccessibleDescription(f"Label for {widget.buddy().accessibleName()}")
        
        # Add keyboard shortcuts hints
        if hasattr(widget, 'shortcut') and widget.shortcut():
            shortcut_text = widget.shortcut().toString()
            current_desc = widget.accessibleDescription()
            widget.setAccessibleDescription(f"{current_desc} (Shortcut: {shortcut_text})")
    
    def setup_keyboard_navigation(self, main_window: QMainWindow):
        """Setup comprehensive keyboard navigation"""
        
        # Global shortcuts
        shortcuts = {
            # Font size
            'Ctrl++': lambda: self.increase_font_size(),
            'Ctrl+-': lambda: self.decrease_font_size(),
            'Ctrl+0': lambda: self.set_font_scale(1.0),
            
            # Contrast
            'Ctrl+Shift+C': lambda: self.toggle_high_contrast_mode(),
            
            # Navigation
            'F6': lambda: self.cycle_focus_forward(),
            'Shift+F6': lambda: self.cycle_focus_backward(),
            'Ctrl+Tab': lambda: self.cycle_focus_forward(),
            'Ctrl+Shift+Tab': lambda: self.cycle_focus_backward(),
            
            # Help
            'F1': lambda: self.show_accessibility_help(),
        }
        
        for key_combo, action in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key_combo), main_window)
            shortcut.activated.connect(action)
            self.keyboard_shortcuts[key_combo] = shortcut
    
    def cycle_focus_forward(self):
        """Move focus to next focusable widget"""
        app = QApplication.instance()
        if app:
            app.focusNextChild()
    
    def cycle_focus_backward(self):
        """Move focus to previous focusable widget"""
        app = QApplication.instance()
        if app:
            app.focusPreviousChild()
    
    def show_accessibility_help(self):
        """Show accessibility help dialog"""
        from PyQt5.QtWidgets import QMessageBox
        
        help_text = """
Accessibility Features:

Font Size:
• Ctrl + '+' : Increase font size
• Ctrl + '-' : Decrease font size  
• Ctrl + '0' : Reset font size

Display:
• Ctrl + Shift + C : Toggle high contrast mode

Navigation:
• Tab / Shift+Tab : Navigate between controls
• F6 / Shift+F6 : Cycle through sections
• Ctrl+Tab / Ctrl+Shift+Tab : Alternative navigation
• Enter / Space : Activate buttons and controls
• Arrow keys : Navigate within lists and menus

Help:
• F1 : Show this help
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Accessibility Help")
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QMessageBox QPushButton {{
                {AppTheme.get_button_style()}
            }}
        """)
        msg.exec_()
    
    def refresh_widget_styles(self):
        """Refresh styles for all widgets"""
        app = QApplication.instance()
        if not app:
            return
        
        # Force style refresh
        for widget in app.allWidgets():
            if widget:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
    
    def create_accessible_tooltip(self, widget: QWidget, text: str, 
                                detailed_description: str = ""):
        """Create accessible tooltip with detailed information"""
        if self.screen_reader_mode and detailed_description:
            tooltip_text = f"{text}\n\nDetailed description: {detailed_description}"
        else:
            tooltip_text = text
        
        widget.setToolTip(tooltip_text)
        widget.setAccessibleDescription(detailed_description or text)
    
    def announce_to_screen_reader(self, message: str):
        """Announce message to screen reader"""
        if self.screen_reader_mode and QAccessible:
            # Create temporary widget for announcement
            app = QApplication.instance()
            if app:
                temp_label = QLabel(message)
                temp_label.setAccessibleName("Announcement")
                temp_label.setAccessibleDescription(message)
                temp_label.hide()
                
                # Use QAccessible to announce if available
                try:
                    if hasattr(QAccessible, 'updateAccessibility'):
                        QAccessible.updateAccessibility(temp_label, 0, QAccessible.Alert)
                except Exception:
                    pass  # Fallback silently
                
                # Clean up after a short delay
                QTimer.singleShot(100, temp_label.deleteLater)
    
    def get_accessibility_stats(self) -> Dict[str, Any]:
        """Get accessibility feature statistics"""
        return {
            'font_scale_factor': self.font_scale_factor,
            'high_contrast_mode': self.high_contrast_mode,
            'screen_reader_mode': self.screen_reader_mode,
            'keyboard_navigation_enabled': self.keyboard_navigation_enabled,
            'focus_indicators_enhanced': self.focus_indicators_enhanced,
            'active_shortcuts': len(self.keyboard_shortcuts),
            'min_font_sizes': self.min_font_sizes
        }
    
    def export_accessibility_settings(self) -> Dict[str, Any]:
        """Export accessibility settings for saving"""
        return {
            'font_scale_factor': self.font_scale_factor,
            'high_contrast_mode': self.high_contrast_mode,
            'screen_reader_mode': self.screen_reader_mode,
            'keyboard_navigation_enabled': self.keyboard_navigation_enabled
        }
    
    def import_accessibility_settings(self, settings: Dict[str, Any]):
        """Import accessibility settings"""
        if 'font_scale_factor' in settings:
            self.set_font_scale(settings['font_scale_factor'])
        
        if 'high_contrast_mode' in settings:
            if settings['high_contrast_mode'] != self.high_contrast_mode:
                self.toggle_high_contrast_mode()
        
        if 'screen_reader_mode' in settings:
            self.enable_screen_reader_mode(settings['screen_reader_mode'])
        
        if 'keyboard_navigation_enabled' in settings:
            self.keyboard_navigation_enabled = settings['keyboard_navigation_enabled']


# Accessibility-enhanced widgets
class AccessibleButton(QPushButton):
    """Button with enhanced accessibility features"""
    
    def __init__(self, text="", parent=None, description=""):
        super().__init__(text, parent)
        self.detailed_description = description
        
        # Setup accessibility
        self.setup_accessibility()
    
    def setup_accessibility(self):
        """Setup accessibility features"""
        accessibility_manager = get_accessibility_manager()
        
        # Set accessible name and description
        if self.text():
            self.setAccessibleName(self.text())
        
        if self.detailed_description:
            self.setAccessibleDescription(self.detailed_description)
            accessibility_manager.create_accessible_tooltip(
                self, self.text(), self.detailed_description
            )
        
        # Enhanced focus indicator
        self.setStyleSheet(f"""
            QPushButton {{
                {AppTheme.get_button_style()}
            }}
            QPushButton:focus {{
                border: 3px solid {AppTheme.HIGHLIGHT_COLOR};
                outline: 2px solid {AppTheme.TEXT_PRIMARY};
                outline-offset: 1px;
            }}
        """)


class AccessibleLabel(QLabel):
    """Label with enhanced accessibility features"""
    
    def __init__(self, text="", parent=None, for_widget=None):
        super().__init__(text, parent)
        self.for_widget = for_widget
        
        self.setup_accessibility()
    
    def setup_accessibility(self):
        """Setup accessibility features"""
        if self.text():
            self.setAccessibleName(self.text())
        
        if self.for_widget:
            self.setBuddy(self.for_widget)
            self.setAccessibleDescription(f"Label for {self.for_widget.accessibleName()}")


# Global instance
_accessibility_manager = None

def get_accessibility_manager() -> AccessibilityManager:
    """Get the global accessibility manager instance"""
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager


def setup_application_accessibility(main_window: QMainWindow):
    """Setup accessibility features for the entire application"""
    manager = get_accessibility_manager()
    
    # Setup keyboard navigation
    manager.setup_keyboard_navigation(main_window)
    
    # Enable enhanced focus indicators
    manager.enable_enhanced_focus_indicators()
    
    # Add screen reader hints to existing widgets
    manager.add_screen_reader_hints()
    
    return manager