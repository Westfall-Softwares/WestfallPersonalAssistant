#!/usr/bin/env python3
"""
Test script for Phase 2 UI/UX Improvements
Demonstrates the progress indicators and accessibility enhancements
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QTimer

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from util.progress_indicators import (
    ProgressOverlay, LoadingSpinner, ProgressDialog, ProgressTracker,
    progress_context, show_global_progress, hide_global_progress, set_global_progress
)
from util.accessibility import (
    get_accessibility_manager, setup_application_accessibility,
    AccessibleButton, AccessibleLabel
)
from util.app_theme import AppTheme


class TestMainWindow(QMainWindow):
    """Test window for Phase 2 features"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 2 UI/UX Improvements Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Apply theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {AppTheme.BACKGROUND};
                color: {AppTheme.TEXT_PRIMARY};
            }}
        """)
        
        self.setup_ui()
        self.setup_accessibility()
        
        # Test components
        self.progress_overlay = None
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_progress)
        self.test_progress = 0
    
    def setup_ui(self):
        """Setup the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = AccessibleLabel("Phase 2 UI/UX Improvements Test")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {AppTheme.FONT_HEADER}px;
                font-weight: bold;
                color: {AppTheme.PRIMARY_COLOR};
                margin-bottom: 20px;
            }}
        """)
        layout.addWidget(title)
        
        # Progress Indicators Section
        progress_section = QWidget()
        progress_layout = QVBoxLayout(progress_section)
        
        progress_label = AccessibleLabel("Progress Indicators")
        progress_label.setStyleSheet(f"""
            QLabel {{
                font-size: {AppTheme.FONT_LARGE}px;
                font-weight: bold;
                color: {AppTheme.TEXT_PRIMARY};
                margin-bottom: 10px;
            }}
        """)
        progress_layout.addWidget(progress_label)
        
        # Progress buttons
        progress_buttons = QHBoxLayout()
        
        self.overlay_btn = AccessibleButton(
            "Show Progress Overlay", 
            description="Display a full-screen progress overlay with cancel option"
        )
        self.overlay_btn.clicked.connect(self.test_progress_overlay)
        progress_buttons.addWidget(self.overlay_btn)
        
        self.dialog_btn = AccessibleButton(
            "Show Progress Dialog",
            description="Display a progress dialog with percentage and cancel"
        )
        self.dialog_btn.clicked.connect(self.test_progress_dialog)
        progress_buttons.addWidget(self.dialog_btn)
        
        self.context_btn = AccessibleButton(
            "Test Progress Context",
            description="Use context manager for automatic progress tracking"
        )
        self.context_btn.clicked.connect(self.test_progress_context)
        progress_buttons.addWidget(self.context_btn)
        
        progress_layout.addLayout(progress_buttons)
        
        # Spinner test
        spinner_layout = QHBoxLayout()
        
        self.spinner = LoadingSpinner(size=32)
        spinner_layout.addWidget(self.spinner)
        
        self.spinner_btn = AccessibleButton(
            "Toggle Spinner",
            description="Start or stop the loading spinner animation"
        )
        self.spinner_btn.clicked.connect(self.toggle_spinner)
        spinner_layout.addWidget(self.spinner_btn)
        
        spinner_layout.addStretch()
        progress_layout.addLayout(spinner_layout)
        
        layout.addWidget(progress_section)
        
        # Accessibility Section
        accessibility_section = QWidget()
        accessibility_layout = QVBoxLayout(accessibility_section)
        
        accessibility_label = AccessibleLabel("Accessibility Features")
        accessibility_label.setStyleSheet(f"""
            QLabel {{
                font-size: {AppTheme.FONT_LARGE}px;
                font-weight: bold;
                color: {AppTheme.TEXT_PRIMARY};
                margin-bottom: 10px;
            }}
        """)
        accessibility_layout.addWidget(accessibility_label)
        
        # Accessibility buttons
        accessibility_buttons = QHBoxLayout()
        
        self.font_increase_btn = AccessibleButton(
            "Increase Font", 
            description="Increase font size for better readability (Ctrl++)"
        )
        self.font_increase_btn.clicked.connect(self.increase_font_size)
        accessibility_buttons.addWidget(self.font_increase_btn)
        
        self.font_decrease_btn = AccessibleButton(
            "Decrease Font",
            description="Decrease font size (Ctrl+-)"
        )
        self.font_decrease_btn.clicked.connect(self.decrease_font_size)
        accessibility_buttons.addWidget(self.font_decrease_btn)
        
        self.contrast_btn = AccessibleButton(
            "Toggle Contrast",
            description="Toggle high contrast mode for better visibility (Ctrl+Shift+C)"
        )
        self.contrast_btn.clicked.connect(self.toggle_contrast)
        accessibility_buttons.addWidget(self.contrast_btn)
        
        accessibility_layout.addLayout(accessibility_buttons)
        
        # Screen reader button
        screen_reader_layout = QHBoxLayout()
        
        self.screen_reader_btn = AccessibleButton(
            "Toggle Screen Reader Mode",
            description="Enable or disable screen reader optimizations"
        )
        self.screen_reader_btn.clicked.connect(self.toggle_screen_reader)
        screen_reader_layout.addWidget(self.screen_reader_btn)
        
        self.help_btn = AccessibleButton(
            "Show Help",
            description="Display accessibility help and keyboard shortcuts (F1)"
        )
        self.help_btn.clicked.connect(self.show_help)
        screen_reader_layout.addWidget(self.help_btn)
        
        screen_reader_layout.addStretch()
        accessibility_layout.addLayout(screen_reader_layout)
        
        layout.addWidget(accessibility_section)
        
        # Status Section
        status_section = QWidget()
        status_layout = QVBoxLayout(status_section)
        
        status_label = AccessibleLabel("Current Status")
        status_label.setStyleSheet(f"""
            QLabel {{
                font-size: {AppTheme.FONT_LARGE}px;
                font-weight: bold;
                color: {AppTheme.TEXT_PRIMARY};
                margin-bottom: 10px;
            }}
        """)
        status_layout.addWidget(status_label)
        
        self.status_text = AccessibleLabel("Ready")
        self.status_text.setStyleSheet(f"""
            QLabel {{
                font-size: {AppTheme.FONT_MEDIUM}px;
                color: {AppTheme.TEXT_SECONDARY};
                padding: 10px;
                border: 1px solid {AppTheme.BORDER_COLOR};
                border-radius: 5px;
                background-color: {AppTheme.SECONDARY_BG};
            }}
        """)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_section)
        layout.addStretch()
    
    def setup_accessibility(self):
        """Setup accessibility features"""
        setup_application_accessibility(self)
        
        # Connect to accessibility signals
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.font_size_changed.connect(self.on_font_size_changed)
        accessibility_manager.contrast_mode_changed.connect(self.on_contrast_changed)
        accessibility_manager.screen_reader_mode_changed.connect(self.on_screen_reader_changed)
    
    def test_progress_overlay(self):
        """Test progress overlay"""
        self.update_status("Testing progress overlay...")
        
        overlay = show_global_progress(self, "Processing data...", True)
        overlay.cancelled.connect(self.on_progress_cancelled)
        
        # Simulate progress
        self.test_progress = 0
        self.test_timer.start(100)
    
    def test_progress_dialog(self):
        """Test progress dialog"""
        self.update_status("Testing progress dialog...")
        
        dialog = ProgressDialog(self, "Processing", "Loading files...", True, True)
        dialog.cancelled.connect(self.on_progress_cancelled)
        dialog.show()
        
        # Simulate progress
        self.test_progress = 0
        self.current_dialog = dialog
        self.test_timer.start(100)
    
    def test_progress_context(self):
        """Test progress context manager"""
        self.update_status("Testing progress context manager...")
        
        def simulate_work():
            with progress_context(self, "Processing", "Working...", 100, True) as tracker:
                for i in range(100):
                    if tracker.cancelled:
                        break
                    time.sleep(0.05)
                    tracker.step(f"Step {i+1} of 100")
                    QApplication.processEvents()
            
            self.update_status("Progress context test completed")
        
        # Run in a timer to keep UI responsive
        QTimer.singleShot(100, simulate_work)
    
    def update_test_progress(self):
        """Update test progress"""
        self.test_progress += 2
        
        if hasattr(self, 'current_dialog'):
            self.current_dialog.set_progress(self.test_progress, f"Processing... {self.test_progress}%")
        else:
            set_global_progress(self.test_progress, f"Processing... {self.test_progress}%")
        
        if self.test_progress >= 100:
            self.test_timer.stop()
            if hasattr(self, 'current_dialog'):
                self.current_dialog.close()
                delattr(self, 'current_dialog')
            else:
                hide_global_progress()
            self.update_status("Progress test completed")
    
    def on_progress_cancelled(self):
        """Handle progress cancellation"""
        self.test_timer.stop()
        hide_global_progress()
        if hasattr(self, 'current_dialog'):
            self.current_dialog.close()
            delattr(self, 'current_dialog')
        self.update_status("Progress cancelled by user")
    
    def toggle_spinner(self):
        """Toggle spinner animation"""
        if hasattr(self.spinner, '_running') and self.spinner._running:
            self.spinner.stop()
            self.spinner._running = False
            self.spinner_btn.setText("Start Spinner")
            self.update_status("Spinner stopped")
        else:
            self.spinner.start()
            self.spinner._running = True
            self.spinner_btn.setText("Stop Spinner")
            self.update_status("Spinner started")
    
    def increase_font_size(self):
        """Increase font size"""
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.increase_font_size()
    
    def decrease_font_size(self):
        """Decrease font size"""
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.decrease_font_size()
    
    def toggle_contrast(self):
        """Toggle high contrast mode"""
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.toggle_high_contrast_mode()
    
    def toggle_screen_reader(self):
        """Toggle screen reader mode"""
        accessibility_manager = get_accessibility_manager()
        current_mode = accessibility_manager.screen_reader_mode
        accessibility_manager.enable_screen_reader_mode(not current_mode)
    
    def show_help(self):
        """Show accessibility help"""
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.show_accessibility_help()
    
    def on_font_size_changed(self, new_size):
        """Handle font size change"""
        self.update_status(f"Font size changed to {new_size}px")
    
    def on_contrast_changed(self, high_contrast):
        """Handle contrast mode change"""
        mode = "high contrast" if high_contrast else "normal"
        self.update_status(f"Switched to {mode} mode")
    
    def on_screen_reader_changed(self, enabled):
        """Handle screen reader mode change"""
        mode = "enabled" if enabled else "disabled"
        self.update_status(f"Screen reader mode {mode}")
    
    def update_status(self, message):
        """Update status message"""
        self.status_text.setText(message)
        
        # Announce to screen reader if enabled
        accessibility_manager = get_accessibility_manager()
        accessibility_manager.announce_to_screen_reader(message)


def test_phase2_improvements():
    """Test Phase 2 UI/UX improvements"""
    print("Testing Phase 2 UI/UX Improvements...")
    
    app = QApplication(sys.argv)
    
    # Apply base theme
    AppTheme.apply_to_application()
    
    # Create test window
    window = TestMainWindow()
    window.show()
    
    print("✅ Phase 2 test window created successfully")
    print("Features available:")
    print("  - Progress indicators (overlay, dialog, context manager)")
    print("  - Loading spinners with animations")
    print("  - Accessibility features (font scaling, high contrast)")
    print("  - Enhanced keyboard navigation")
    print("  - Screen reader optimizations")
    print("  - Accessible tooltips and descriptions")
    print("\nUse the buttons in the window to test each feature.")
    print("Keyboard shortcuts:")
    print("  Ctrl++ : Increase font size")
    print("  Ctrl+- : Decrease font size")
    print("  Ctrl+Shift+C : Toggle high contrast")
    print("  F1 : Show accessibility help")
    print("  Tab/Shift+Tab : Navigate between controls")
    
    return app.exec_()


def main():
    """Main test function"""
    try:
        return test_phase2_improvements()
    except Exception as e:
        print(f"❌ Phase 2 test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())