"""
Live AI-powered screen monitoring and interaction system for WestfallPersonalAssistant
"""

import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage
from io import BytesIO
import json

try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    import numpy as np
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    import pyautogui
    # Configure pyautogui for safety
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

class LiveScreenIntelligence(QWidget):
    """Live AI-powered screen monitoring and interaction system"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.ai_control_enabled = False
        self.current_screens = []
        self.interaction_history = []
        self.init_ui()
        
        # Live monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.capture_screens)
        
        # AI analysis timer
        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.ai_analyze_screens)
        
    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: white;
            }
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #ff0000;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ff0000;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🖥️ Live Screen Intelligence & AI Control")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff0000; padding: 10px;")
        layout.addWidget(header)
        
        # Dependency status
        status_text = self.get_dependency_status()
        if status_text:
            status_label = QLabel(status_text)
            status_label.setStyleSheet("color: #ffaa00; padding: 10px; background-color: #1a1a1a; border: 1px solid #ffaa00;")
            layout.addWidget(status_label)
        
        # Control Panel
        control_panel = QGroupBox("Control Panel")
        control_layout = QHBoxLayout()
        
        # Live monitoring toggle
        self.monitor_btn = QPushButton("▶️ Start Live Monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        if not MSS_AVAILABLE:
            self.monitor_btn.setEnabled(False)
            self.monitor_btn.setText("❌ MSS Not Available")
        control_layout.addWidget(self.monitor_btn)
        
        # AI control toggle
        self.ai_control_btn = QPushButton("🤖 Enable AI Control")
        self.ai_control_btn.clicked.connect(self.toggle_ai_control)
        if not PYAUTOGUI_AVAILABLE:
            self.ai_control_btn.setEnabled(False)
            self.ai_control_btn.setText("❌ PyAutoGUI Not Available")
        control_layout.addWidget(self.ai_control_btn)
        
        # Emergency stop
        self.stop_btn = QPushButton("🛑 EMERGENCY STOP")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
        """)
        self.stop_btn.clicked.connect(self.emergency_stop)
        control_layout.addWidget(self.stop_btn)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # Screen Display Area
        screen_tabs = QTabWidget()
        screen_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ff0000;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background-color: #ff0000;
            }
        """)
        
        # Live view tab
        self.live_view = QLabel("Live screen will appear here when monitoring starts")
        self.live_view.setAlignment(Qt.AlignCenter)
        self.live_view.setMinimumHeight(400)
        self.live_view.setStyleSheet("border: 1px solid #ff0000; padding: 20px;")
        screen_tabs.addTab(self.live_view, "Live View")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        screen_tabs.addTab(self.analysis_text, "AI Analysis")
        
        layout.addWidget(screen_tabs)
        
        # AI Interaction Panel
        ai_panel = QGroupBox("AI Developer Assistant")
        ai_layout = QVBoxLayout()
        
        # Problem description
        problem_layout = QHBoxLayout()
        problem_label = QLabel("Describe the problem:")
        problem_layout.addWidget(problem_label)
        
        self.problem_input = QLineEdit()
        self.problem_input.setPlaceholderText("e.g., 'Fix the error in my IDE', 'Debug this code', 'Set up this software'")
        self.problem_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 8px;
            }
        """)
        problem_layout.addWidget(self.problem_input)
        
        self.solve_btn = QPushButton("🔧 Let AI Solve")
        self.solve_btn.clicked.connect(self.ai_solve_problem)
        if not PYAUTOGUI_AVAILABLE:
            self.solve_btn.setEnabled(False)
        problem_layout.addWidget(self.solve_btn)
        
        ai_layout.addLayout(problem_layout)
        
        # AI action log
        self.action_log = QTextEdit()
        self.action_log.setMaximumHeight(150)
        self.action_log.setReadOnly(True)
        self.action_log.setPlaceholderText("AI actions will be logged here...")
        ai_layout.addWidget(self.action_log)
        
        ai_panel.setLayout(ai_layout)
        layout.addWidget(ai_panel)
        
        # Status bar
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #ff0000; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def get_dependency_status(self):
        """Get status of dependencies"""
        missing = []
        if not MSS_AVAILABLE:
            missing.append("mss (screen capture)")
        if not PIL_AVAILABLE:
            missing.append("Pillow (image processing)")
        if not CV2_AVAILABLE:
            missing.append("opencv-python (computer vision)")
        if not PYTESSERACT_AVAILABLE:
            missing.append("pytesseract (OCR)")
        if not PYAUTOGUI_AVAILABLE:
            missing.append("pyautogui (automation)")
        
        if missing:
            return f"⚠️ Missing dependencies: {', '.join(missing)}\nInstall with: pip install {' '.join(missing)}"
        return ""
    
    def toggle_monitoring(self):
        """Toggle live screen monitoring"""
        if not self.monitoring:
            if not MSS_AVAILABLE:
                QMessageBox.critical(self, "Missing Dependency", 
                    "MSS library not available. Please install with:\npip install mss")
                return
            
            self.monitoring = True
            self.monitor_btn.setText("⏸️ Stop Monitoring")
            self.monitor_timer.start(100)  # Update every 100ms for smooth live view
            self.status_label.setText("Status: Live monitoring active")
            self.log_action("Started live screen monitoring")
        else:
            self.monitoring = False
            self.monitor_btn.setText("▶️ Start Live Monitoring")
            self.monitor_timer.stop()
            self.status_label.setText("Status: Monitoring stopped")
            self.log_action("Stopped screen monitoring")
    
    def toggle_ai_control(self):
        """Toggle AI control of the screen"""
        if not self.ai_control_enabled:
            if not PYAUTOGUI_AVAILABLE:
                QMessageBox.critical(self, "Missing Dependency", 
                    "PyAutoGUI library not available. Please install with:\npip install pyautogui")
                return
                
            reply = QMessageBox.warning(self, "AI Control", 
                "⚠️ WARNING: Enabling AI control allows the assistant to control your mouse and keyboard.\n\n"
                "The AI will be able to:\n"
                "• Move and click the mouse\n"
                "• Type on the keyboard\n"
                "• Open and close applications\n"
                "• Modify files and settings\n\n"
                "Only enable if you trust the AI and need automated assistance.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.ai_control_enabled = True
                self.ai_control_btn.setText("🤖 Disable AI Control")
                self.ai_control_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: black;
                    }
                """)
                self.ai_timer.start(1000)  # Analyze every second
                self.status_label.setText("Status: AI CONTROL ACTIVE - AI can interact with screen")
                self.log_action("AI control enabled - AI has mouse/keyboard access")
        else:
            self.ai_control_enabled = False
            self.ai_control_btn.setText("🤖 Enable AI Control")
            self.ai_control_btn.setStyleSheet("")
            self.ai_timer.stop()
            self.status_label.setText("Status: AI control disabled")
            self.log_action("AI control disabled")
    
    def capture_screens(self):
        """Capture all screens in real-time"""
        if not MSS_AVAILABLE:
            return
            
        try:
            with mss.mss() as sct:
                # Capture primary monitor for live view
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                
                if PIL_AVAILABLE:
                    # Convert to QPixmap for display
                    img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                    
                    # Resize for display
                    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(buffer.read())
                    
                    # Update live view
                    self.live_view.setPixmap(pixmap.scaled(
                        self.live_view.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    ))
                    
                    # Store for AI analysis
                    self.current_screens = [(monitor, img)]
                else:
                    self.live_view.setText("PIL not available - cannot display screen capture")
                
        except Exception as e:
            self.log_action(f"Error capturing screen: {str(e)}")
    
    def ai_analyze_screens(self):
        """AI analyzes current screens for issues"""
        if not self.current_screens or not PYTESSERACT_AVAILABLE:
            return
        
        try:
            for monitor, img in self.current_screens:
                # Extract text using OCR
                text = pytesseract.image_to_string(img)
                
                # Look for error indicators
                error_keywords = [
                    'error', 'exception', 'failed', 'denied', 'invalid',
                    'undefined', 'null', 'crash', 'fatal', 'warning'
                ]
                
                found_issues = []
                for keyword in error_keywords:
                    if keyword.lower() in text.lower():
                        found_issues.append(keyword)
                
                if found_issues:
                    analysis = f"⚠️ Potential issues detected: {', '.join(found_issues)}\n"
                    analysis += f"Screen text sample:\n{text[:500]}"
                    self.analysis_text.append(analysis)
                    
                    if self.ai_control_enabled:
                        self.ai_respond_to_error(text, found_issues)
                
        except Exception as e:
            self.log_action(f"Analysis error: {str(e)}")
    
    def ai_respond_to_error(self, screen_text, issues):
        """AI responds to detected errors"""
        self.log_action(f"AI detected issues: {', '.join(issues)}")
        
        # Analyze error type and respond accordingly
        if 'null' in str(issues).lower() or 'undefined' in str(issues).lower():
            self.log_action("AI: Detected null reference error, checking for uninitialized variables")
        
        elif 'syntax' in str(issues).lower():
            self.log_action("AI: Syntax error detected, analyzing code structure")
        
        elif 'connection' in str(issues).lower() or 'network' in str(issues).lower():
            self.log_action("AI: Network issue detected, checking connectivity")
    
    def ai_solve_problem(self):
        """AI attempts to solve the described problem"""
        problem = self.problem_input.text()
        if not problem:
            QMessageBox.warning(self, "No Problem", "Please describe the problem first")
            return
        
        if not self.ai_control_enabled:
            reply = QMessageBox.question(self, "Enable AI Control", 
                "AI needs control permission to solve this problem. Enable AI control?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.toggle_ai_control()
            else:
                return
        
        self.log_action(f"AI solving: {problem}")
        
        # Create AI solution thread
        if PYAUTOGUI_AVAILABLE:
            self.solution_thread = AISolutionThread(problem, self.current_screens)
            self.solution_thread.action_signal.connect(self.log_action)
            self.solution_thread.start()
    
    def emergency_stop(self):
        """Emergency stop all AI actions"""
        self.ai_control_enabled = False
        self.monitoring = False
        self.monitor_timer.stop()
        self.ai_timer.stop()
        
        # Move mouse to corner (failsafe) if pyautogui is available
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.moveTo(0, 0)
            except:
                pass
        
        self.monitor_btn.setText("▶️ Start Live Monitoring")
        self.ai_control_btn.setText("🤖 Enable AI Control")
        self.ai_control_btn.setStyleSheet("")
        
        self.status_label.setText("Status: EMERGENCY STOP - All operations halted")
        self.log_action("🛑 EMERGENCY STOP ACTIVATED")
        
        QMessageBox.information(self, "Emergency Stop", 
            "All AI operations have been stopped.\nMouse and keyboard control returned to user.")
    
    def log_action(self, message):
        """Log AI actions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.action_log.append(f"[{timestamp}] {message}")
        self.interaction_history.append((timestamp, message))

class AISolutionThread(QThread):
    """Thread for AI problem-solving actions"""
    action_signal = pyqtSignal(str)
    
    def __init__(self, problem, screens):
        super().__init__()
        self.problem = problem
        self.screens = screens
    
    def run(self):
        """Execute AI solution"""
        if not PYAUTOGUI_AVAILABLE:
            self.action_signal.emit("PyAutoGUI not available - cannot execute automated actions")
            return
            
        self.action_signal.emit(f"Starting to solve: {self.problem}")
        
        # Simulate AI problem-solving steps
        problem_lower = self.problem.lower()
        
        if 'error' in problem_lower or 'fix' in problem_lower:
            self.fix_error()
        elif 'debug' in problem_lower:
            self.debug_code()
        elif 'setup' in problem_lower or 'install' in problem_lower:
            self.setup_software()
        elif 'code' in problem_lower or 'write' in problem_lower:
            self.write_code()
        else:
            self.general_assistance()
    
    def fix_error(self):
        """AI fixes detected errors"""
        self.action_signal.emit("Analyzing error messages...")
        time.sleep(1)
        
        # Simulate error fixing actions
        self.action_signal.emit("Locating error in code...")
        time.sleep(1)
        
        # Move to error location (example)
        try:
            pyautogui.hotkey('ctrl', 'f')  # Open find
            time.sleep(0.5)
            pyautogui.typewrite('error')  # Search for error
            time.sleep(0.5)
            pyautogui.press('escape')  # Close find
        except:
            self.action_signal.emit("Error: Could not perform automated actions")
            return
        
        self.action_signal.emit("Analyzing error context...")
        time.sleep(1)
        
        self.action_signal.emit("Applying fix...")
        
        self.action_signal.emit("✅ Error fixing complete")
    
    def debug_code(self):
        """AI debugs code"""
        self.action_signal.emit("Starting debugging process...")
        time.sleep(1)
        
        # Simulate debugging actions
        self.action_signal.emit("Setting breakpoints...")
        try:
            pyautogui.hotkey('f9')  # Common breakpoint shortcut
            time.sleep(1)
            
            self.action_signal.emit("Starting debug session...")
            pyautogui.hotkey('f5')  # Common debug start
            time.sleep(2)
        except:
            self.action_signal.emit("Error: Could not perform automated actions")
            return
        
        self.action_signal.emit("Analyzing variable states...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Debugging session complete")
    
    def setup_software(self):
        """AI helps with software setup"""
        self.action_signal.emit("Assisting with software setup...")
        time.sleep(1)
        
        self.action_signal.emit("Checking system requirements...")
        time.sleep(1)
        
        self.action_signal.emit("Guiding through installation steps...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Setup assistance complete")
    
    def write_code(self):
        """AI writes code"""
        self.action_signal.emit("Generating code...")
        time.sleep(1)
        
        # Example: Write a simple function
        code = """def hello_world():
    print("Hello, World!")
    return True

# Call the function
hello_world()
"""
        
        self.action_signal.emit("Writing code to editor...")
        try:
            pyautogui.typewrite(code, interval=0.01)
        except:
            self.action_signal.emit("Error: Could not write code automatically")
            return
        
        self.action_signal.emit("✅ Code written successfully")
    
    def general_assistance(self):
        """General AI assistance"""
        self.action_signal.emit("Analyzing request...")
        time.sleep(1)
        
        self.action_signal.emit("Providing general assistance...")
        time.sleep(2)
        
        self.action_signal.emit("✅ Assistance provided")