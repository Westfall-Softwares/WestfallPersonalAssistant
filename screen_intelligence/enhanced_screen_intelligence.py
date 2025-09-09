"""
Enhanced Screen Intelligence with AI Integration
Provides enhanced multi-monitor support and AI-powered analysis capabilities
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QProgressBar, QTextEdit

try:
    from .capture.multi_monitor_capture import MultiMonitorCapture
    CAPTURE_AVAILABLE = True
except ImportError:
    CAPTURE_AVAILABLE = False
    MultiMonitorCapture = None

try:
    from ..ai_assistant.core.screen_analysis import ScreenAnalysisThread, get_component_registry
    from ..ai_assistant.core.model_manager import get_model_manager
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class EnhancedScreenIntelligence(QObject):
    """Enhanced screen intelligence with AI integration"""
    
    analysis_completed = pyqtSignal(dict)  # analysis_result
    capture_completed = pyqtSignal(bytes)  # screenshot_data
    status_updated = pyqtSignal(str)  # status_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor_capture = None
        self.model_manager = None
        self.component_registry = None
        self.current_analysis = None
        
        # Initialize components
        self._init_capture_system()
        self._init_ai_system()
        self._register_with_ai()
    
    def _init_capture_system(self):
        """Initialize screen capture system"""
        if CAPTURE_AVAILABLE:
            try:
                self.monitor_capture = MultiMonitorCapture()
                logging.info("Screen capture system initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize screen capture: {e}")
        else:
            logging.warning("Screen capture not available")
    
    def _init_ai_system(self):
        """Initialize AI analysis system"""
        if AI_AVAILABLE:
            try:
                self.model_manager = get_model_manager()
                self.component_registry = get_component_registry()
                logging.info("AI analysis system initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize AI system: {e}")
        else:
            logging.warning("AI analysis not available")
    
    def _register_with_ai(self):
        """Register screen intelligence with AI system"""
        if self.component_registry:
            self.component_registry.register_component(
                "screen_intelligence",
                self._get_screen_context
            )
    
    def _get_screen_context(self) -> Dict[str, Any]:
        """Get current screen context for AI"""
        context = {
            'timestamp': time.time(),
            'capture_available': CAPTURE_AVAILABLE,
            'ai_available': AI_AVAILABLE,
            'monitors': self._get_monitor_info(),
            'last_analysis': self._get_last_analysis_summary()
        }
        return context
    
    def _get_monitor_info(self) -> List[Dict[str, Any]]:
        """Get information about available monitors"""
        monitors = []
        if self.monitor_capture:
            try:
                # This would get actual monitor information
                monitors = [
                    {'id': 0, 'width': 1920, 'height': 1080, 'primary': True},
                    {'id': 1, 'width': 1920, 'height': 1080, 'primary': False}
                ]
            except Exception as e:
                logging.warning(f"Failed to get monitor info: {e}")
        return monitors
    
    def _get_last_analysis_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of last analysis"""
        if self.current_analysis:
            return {
                'type': self.current_analysis.get('analysis_type'),
                'confidence': self.current_analysis.get('confidence'),
                'timestamp': self.current_analysis.get('timestamp')
            }
        return None
    
    def capture_screen(self, monitor_id: Optional[int] = None) -> Optional[bytes]:
        """Capture screen from specified monitor"""
        if not self.monitor_capture:
            self.status_updated.emit("Screen capture not available")
            return None
        
        try:
            self.status_updated.emit("Capturing screen...")
            
            # Capture screen (placeholder implementation)
            screenshot_data = b"mock_screenshot_data"  # Would be actual capture
            
            self.capture_completed.emit(screenshot_data)
            self.status_updated.emit("Screen captured successfully")
            return screenshot_data
            
        except Exception as e:
            error_msg = f"Screen capture failed: {e}"
            logging.error(error_msg)
            self.status_updated.emit(error_msg)
            return None
    
    def analyze_screen(self, analysis_type: str = "general", monitor_id: Optional[int] = None) -> bool:
        """Analyze current screen with AI"""
        if not AI_AVAILABLE:
            self.status_updated.emit("AI analysis not available")
            return False
        
        # Capture screen first
        screenshot_data = self.capture_screen(monitor_id)
        if not screenshot_data:
            return False
        
        try:
            # Start AI analysis
            self.status_updated.emit(f"Starting {analysis_type} analysis...")
            
            analysis_thread = ScreenAnalysisThread(
                screenshot_data=screenshot_data,
                analysis_type=analysis_type,
                context=self._get_screen_context()
            )
            
            # Connect signals
            analysis_thread.analysis_completed.connect(self._on_analysis_completed)
            analysis_thread.analysis_failed.connect(self._on_analysis_failed)
            analysis_thread.status_updated.connect(self.status_updated.emit)
            
            # Start analysis
            analysis_thread.start()
            return True
            
        except Exception as e:
            error_msg = f"Failed to start analysis: {e}"
            logging.error(error_msg)
            self.status_updated.emit(error_msg)
            return False
    
    def _on_analysis_completed(self, result: Dict[str, Any]):
        """Handle completed analysis"""
        self.current_analysis = result
        self.analysis_completed.emit(result)
        self.status_updated.emit("Analysis completed successfully")
    
    def _on_analysis_failed(self, error: str):
        """Handle failed analysis"""
        self.status_updated.emit(f"Analysis failed: {error}")
    
    def get_available_analysis_types(self) -> List[Tuple[str, str]]:
        """Get available analysis types"""
        return [
            ("general", "General Content Analysis"),
            ("ui_elements", "UI Element Detection"),
            ("code_analysis", "Code Analysis"),
            ("design_review", "Design Review"),
            ("accessibility", "Accessibility Check")
        ]
    
    def get_monitor_list(self) -> List[Dict[str, Any]]:
        """Get list of available monitors"""
        return self._get_monitor_info()
    
    def is_capture_available(self) -> bool:
        """Check if screen capture is available"""
        return CAPTURE_AVAILABLE and self.monitor_capture is not None
    
    def is_ai_available(self) -> bool:
        """Check if AI analysis is available"""
        return AI_AVAILABLE and self.model_manager is not None


class ScreenIntelligenceWidget(QWidget):
    """Widget for screen intelligence control"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen_intelligence = EnhancedScreenIntelligence()
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Screen Intelligence")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff0000; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Monitor selection
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Monitor:"))
        
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItem("Primary Monitor", 0)
        # Add additional monitors if available
        for i, monitor in enumerate(self.screen_intelligence.get_monitor_list()[1:], 1):
            self.monitor_combo.addItem(f"Monitor {i+1}", monitor['id'])
        monitor_layout.addWidget(self.monitor_combo)
        layout.addLayout(monitor_layout)
        
        # Analysis type selection
        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel("Analysis Type:"))
        
        self.analysis_combo = QComboBox()
        for analysis_id, analysis_name in self.screen_intelligence.get_available_analysis_types():
            self.analysis_combo.addItem(analysis_name, analysis_id)
        analysis_layout.addWidget(self.analysis_combo)
        layout.addLayout(analysis_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture Screen")
        self.capture_btn.clicked.connect(self.capture_screen)
        button_layout.addWidget(self.capture_btn)
        
        self.analyze_btn = QPushButton("🔍 Analyze Screen")
        self.analyze_btn.clicked.connect(self.analyze_screen)
        button_layout.addWidget(self.analyze_btn)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        layout.addWidget(self.results_text)
        
        # Capabilities info
        capabilities = []
        if self.screen_intelligence.is_capture_available():
            capabilities.append("📸 Screen Capture")
        if self.screen_intelligence.is_ai_available():
            capabilities.append("🤖 AI Analysis")
        
        if capabilities:
            caps_label = QLabel(f"Available: {' • '.join(capabilities)}")
        else:
            caps_label = QLabel("⚠️ Limited functionality - install dependencies for full features")
        
        caps_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 10px;")
        layout.addWidget(caps_label)
    
    def connect_signals(self):
        """Connect screen intelligence signals"""
        self.screen_intelligence.status_updated.connect(self.update_status)
        self.screen_intelligence.analysis_completed.connect(self.display_analysis_results)
        self.screen_intelligence.capture_completed.connect(self.on_capture_completed)
    
    def capture_screen(self):
        """Capture screen from selected monitor"""
        monitor_id = self.monitor_combo.currentData()
        self.show_progress("Capturing screen...")
        self.screen_intelligence.capture_screen(monitor_id)
    
    def analyze_screen(self):
        """Analyze screen with selected analysis type"""
        monitor_id = self.monitor_combo.currentData()
        analysis_type = self.analysis_combo.currentData()
        
        self.show_progress("Analyzing screen...")
        success = self.screen_intelligence.analyze_screen(analysis_type, monitor_id)
        
        if not success:
            self.hide_progress()
    
    def show_progress(self, message: str):
        """Show progress indication"""
        self.status_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.capture_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
    
    def hide_progress(self):
        """Hide progress indication"""
        self.progress_bar.setVisible(False)
        self.capture_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
    
    def update_status(self, status: str):
        """Update status message"""
        self.status_label.setText(status)
        if "completed" in status.lower() or "failed" in status.lower():
            self.hide_progress()
    
    def on_capture_completed(self, screenshot_data: bytes):
        """Handle completed screen capture"""
        self.results_text.append(f"📸 Screen captured: {len(screenshot_data)} bytes")
        self.hide_progress()
    
    def display_analysis_results(self, results: Dict[str, Any]):
        """Display analysis results"""
        self.results_text.clear()
        
        # Display analysis summary
        analysis_type = results.get('analysis_type', 'Unknown')
        confidence = results.get('confidence', 0)
        timestamp = results.get('timestamp', time.time())
        
        self.results_text.append(f"🔍 Analysis Type: {analysis_type.title()}")
        self.results_text.append(f"📊 Confidence: {confidence:.1%}")
        self.results_text.append(f"🕒 Completed: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
        self.results_text.append("")
        
        # Display findings
        findings = results.get('findings', {})
        if findings:
            self.results_text.append("📋 Findings:")
            for category, content in findings.items():
                if isinstance(content, str):
                    self.results_text.append(f"  • {category.title()}: {content}")
                elif isinstance(content, list):
                    self.results_text.append(f"  • {category.title()}: {len(content)} items")
                elif isinstance(content, dict):
                    self.results_text.append(f"  • {category.title()}: {len(content)} categories")
            self.results_text.append("")
        
        # Display suggestions
        suggestions = results.get('suggestions', [])
        if suggestions:
            self.results_text.append("💡 Suggestions:")
            for suggestion in suggestions[:5]:  # Show top 5 suggestions
                self.results_text.append(f"  • {suggestion}")
        
        self.hide_progress()


# For backward compatibility
LiveScreenIntelligence = EnhancedScreenIntelligence