# Optional dependencies with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import base64
from io import BytesIO
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage
import json

# Optional dependencies with fallbacks
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class ScreenCaptureWorker(QThread):
    screenshot_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, monitor_indices=None):
        super().__init__()
        self.monitor_indices = monitor_indices
    
    def run(self):
        try:
            if not HAS_MSS:
                self.error_occurred.emit("MSS library not available. Install with: pip install mss")
                return
            
            if not HAS_PIL:
                self.error_occurred.emit("PIL library not available. Install with: pip install Pillow")
                return
                
            captures = []
            with mss.mss() as sct:
                monitors = sct.monitors
                
                # Capture specified monitors or all
                indices = self.monitor_indices or range(1, len(monitors))
                
                for i in indices:
                    if i < len(monitors):
                        monitor = monitors[i]
                        screenshot = sct.grab(monitor)
                        
                        # Convert to PIL Image
                        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                        
                        # Add monitor info overlay
                        draw = ImageDraw.Draw(img)
                        text = f"Monitor {i}: {monitor['width']}x{monitor['height']}"
                        draw.rectangle([0, 0, 300, 30], fill='black')
                        draw.text((10, 5), text, fill='white')
                        
                        captures.append({
                            'monitor_id': i,
                            'image': img,
                            'dimensions': (monitor['width'], monitor['height']),
                            'position': (monitor['left'], monitor['top'])
                        })
                
                self.screenshot_ready.emit(captures)
        except Exception as e:
            self.error_occurred.emit(str(e))

class MultiMonitorCapture(QWidget):
    def __init__(self):
        super().__init__()
        self.captures = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Screen Intelligence - Multi-Monitor Capture")
        self.setGeometry(100, 100, 1200, 800)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🖥️ Multi-Monitor Screen Intelligence")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        header.setToolTip("Capture and analyze content from all your monitors")
        layout.addWidget(header)
        
        # Control panel
        control_panel = QHBoxLayout()
        
        capture_all_btn = QPushButton("📸 Capture All Monitors")
        capture_all_btn.setToolTip("Take screenshots of all connected monitors")
        capture_all_btn.clicked.connect(self.capture_all_monitors)
        control_panel.addWidget(capture_all_btn)
        
        capture_active_btn = QPushButton("📷 Capture Active Window")
        capture_active_btn.setToolTip("Capture only the currently active window")
        capture_active_btn.clicked.connect(self.capture_active_window)
        control_panel.addWidget(capture_active_btn)
        
        analyze_btn = QPushButton("🔍 Analyze for Errors")
        analyze_btn.setToolTip("Scan all screens for error messages and issues")
        analyze_btn.clicked.connect(self.analyze_for_errors)
        control_panel.addWidget(analyze_btn)
        
        help_btn = QPushButton("🤖 Get AI Help")
        help_btn.setToolTip("Get AI assistance for what's on your screen")
        help_btn.clicked.connect(self.get_ai_help)
        control_panel.addWidget(help_btn)
        
        control_panel.addStretch()
        layout.addLayout(control_panel)
        
        # Monitor tabs
        self.monitor_tabs = QTabWidget()
        layout.addWidget(self.monitor_tabs)
        
        # Analysis results
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        layout.addWidget(self.results_text)
        
        self.setLayout(layout)
    
    def capture_all_monitors(self):
        if not HAS_MSS:
            QMessageBox.warning(self, "Missing Dependency", 
                              "MSS library not available. Please install with:\npip install mss")
            return
        
        if not HAS_PIL:
            QMessageBox.warning(self, "Missing Dependency", 
                              "PIL library not available. Please install with:\npip install Pillow")
            return
            
        self.worker = ScreenCaptureWorker()
        self.worker.screenshot_ready.connect(self.display_captures)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()
        
        self.results_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Capturing all monitors...")
    
    def capture_active_window(self):
        # Simplified active window capture without platform-specific dependencies
        try:
            self.results_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Active window capture feature requires platform-specific implementation")
        except Exception as e:
            self.show_error(str(e))
    
    def display_captures(self, captures):
        self.captures = captures
        self.monitor_tabs.clear()
        
        for capture in captures:
            # Create widget for each monitor
            monitor_widget = QWidget()
            monitor_layout = QVBoxLayout()
            
            # Convert PIL Image to QPixmap
            img = capture['image']
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_byte_arr)
            
            # Scale to fit
            scaled_pixmap = pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            img_label = QLabel()
            img_label.setPixmap(scaled_pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            
            scroll_area = QScrollArea()
            scroll_area.setWidget(img_label)
            monitor_layout.addWidget(scroll_area)
            
            # Add monitor info
            info_label = QLabel(f"Resolution: {capture['dimensions'][0]}x{capture['dimensions'][1]} | Position: {capture['position']}")
            monitor_layout.addWidget(info_label)
            
            monitor_widget.setLayout(monitor_layout)
            self.monitor_tabs.addTab(monitor_widget, f"Monitor {capture['monitor_id']}")
        
        self.results_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Captured {len(captures)} monitors successfully")
    
    def analyze_for_errors(self):
        if not self.captures:
            QMessageBox.warning(self, "No Captures", "Please capture screens first")
            return
        
        if not HAS_PYTESSERACT:
            QMessageBox.warning(self, "Missing Dependency", 
                              "PyTesseract library not available. Please install with:\npip install pytesseract")
            return
        
        self.results_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing screens for errors...")
        
        errors_found = []
        
        for capture in self.captures:
            # Extract text using OCR
            img = capture['image']
            text = pytesseract.image_to_string(img)
            
            # Common error patterns
            error_patterns = [
                ('Error', 'Generic error detected'),
                ('Exception', 'Exception found'),
                ('Failed', 'Operation failure detected'),
                ('Cannot', 'Unable to perform action'),
                ('Invalid', 'Invalid input or state'),
                ('Undefined', 'Undefined reference'),
                ('404', 'Page not found'),
                ('500', 'Server error'),
                ('NullReferenceException', 'Null reference in code'),
                ('SyntaxError', 'Syntax error in code'),
                ('TypeError', 'Type error in code'),
                ('Access Denied', 'Permission issue'),
                ('Connection refused', 'Network connection issue')
            ]
            
            for pattern, description in error_patterns:
                if pattern.lower() in text.lower():
                    errors_found.append({
                        'monitor': capture['monitor_id'],
                        'error': pattern,
                        'description': description,
                        'context': self.extract_error_context(text, pattern)
                    })
        
        if errors_found:
            self.results_text.append(f"\n⚠️ Found {len(errors_found)} potential issues:")
            for error in errors_found:
                self.results_text.append(f"  Monitor {error['monitor']}: {error['description']}")
                self.results_text.append(f"    Context: {error['context'][:100]}...")
                
                # Suggest solutions
                solution = self.suggest_solution(error['error'])
                if solution:
                    self.results_text.append(f"    💡 Suggestion: {solution}")
        else:
            self.results_text.append("✅ No obvious errors detected on any screen")
    
    def extract_error_context(self, text, pattern):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if pattern.lower() in line.lower():
                # Get surrounding lines for context
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context_lines = lines[start:end]
                return ' '.join(context_lines)
        return ""
    
    def suggest_solution(self, error_type):
        solutions = {
            'Error': 'Check the error message details and stack trace',
            'Exception': 'Review the exception details and check for null values',
            'Failed': 'Verify prerequisites and retry the operation',
            'Cannot': 'Check permissions and resource availability',
            'Invalid': 'Validate input data and parameters',
            'Undefined': 'Ensure all variables and references are properly defined',
            '404': 'Check the URL or file path',
            '500': 'Check server logs or contact support',
            'NullReferenceException': 'Add null checks before accessing objects',
            'SyntaxError': 'Check for missing brackets, quotes, or semicolons',
            'TypeError': 'Verify data types match expected values',
            'Access Denied': 'Check user permissions and authentication',
            'Connection refused': 'Verify network connectivity and firewall settings'
        }
        return solutions.get(error_type, 'Review the error context for more details')
    
    def get_ai_help(self):
        if not self.captures:
            QMessageBox.warning(self, "No Captures", "Please capture screens first")
            return
        
        # Send to AI for analysis
        try:
            from ai_assistant.core.chat_manager import AIChatWidget
            
            # Create or get AI chat instance
            if hasattr(self.parent(), 'ai_chat'):
                ai_chat = self.parent().ai_chat
                
                # Prepare context with screen information
                context = "I need help with what's on my screen. "
                
                for capture in self.captures:
                    # Extract text from image if possible
                    if HAS_PYTESSERACT:
                        text = pytesseract.image_to_string(capture['image'])
                        if text.strip():
                            context += f"\nMonitor {capture['monitor_id']} shows: {text[:500]}..."
                    else:
                        context += f"\nMonitor {capture['monitor_id']}: Screenshot captured but text extraction requires pytesseract library"
                
                # Send to AI
                ai_chat.show()
                if hasattr(ai_chat, 'input_field'):
                    ai_chat.input_field.setText(context)
                    if hasattr(ai_chat, 'send_message'):
                        ai_chat.send_message()
                
                self.results_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Sent screen context to AI Assistant")
            else:
                QMessageBox.information(self, "AI Help", "AI Assistant will analyze your screens and provide guidance")
        except ImportError:
            QMessageBox.information(self, "AI Help", "AI Assistant module not available")
    
    def show_error(self, error):
        self.results_text.append(f"❌ Error: {error}")
        QMessageBox.critical(self, "Error", f"Failed to capture screens: {error}")

# Alias for import compatibility
LiveScreenIntelligence = MultiMonitorCapture
LiveScreenIntelligence = MultiMonitorCapture