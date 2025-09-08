import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
import json
from datetime import datetime

class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query, context, provider):
        super().__init__()
        self.query = query
        self.context = context
        self.provider = provider
    
    def run(self):
        try:
            response = self.provider.generate_response(self.query, self.context)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AIChatWidget(QWidget):
    command_signal = pyqtSignal(str, dict)
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.provider = None
        self.init_provider()
        self.init_ui()
        self.conversation_history = []
        
    def init_provider(self):
        try:
            from ai_assistant.providers.openai_provider import OpenAIProvider
            self.provider = OpenAIProvider()
        except:
            try:
                from ai_assistant.providers.ollama_provider import OllamaProvider
                self.provider = OllamaProvider()
            except:
                self.provider = None
    
    def init_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setGeometry(1100, 100, 400, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header
        header = QLabel("AI Assistant")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Add user message to display
        self.append_message("You", message)
        self.input_field.clear()
        
        # Get context from parent window
        context = self.get_window_context()
        
        # Check if it's a command
        if self.is_command(message):
            self.execute_command(message, context)
        else:
            # Get AI response
            self.get_ai_response(message, context)
    
    def append_message(self, sender, message):
        timestamp = datetime.now().strftime("%H:%M")
        formatted = f"<b>{sender}</b> [{timestamp}]<br>{message}<br><br>"
        self.chat_display.append(formatted)
        
        # Store in history
        self.conversation_history.append({
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        })
    
    def get_window_context(self):
        if not self.parent_window:
            return {"window": "None", "data": {}}
        
        context = {
            "window": type(self.parent_window).__name__,
            "data": {},
            "business_context": self.get_business_context()
        }
        
        # Get window-specific context
        if hasattr(self.parent_window, 'get_context_for_ai'):
            context["data"] = self.parent_window.get_context_for_ai()
        
        return context
    
    def get_business_context(self):
        """Get entrepreneur and business context for AI responses"""
        try:
            # Get Tailor Pack information
            from util.tailor_pack_manager import get_tailor_pack_manager
            pack_manager = get_tailor_pack_manager()
            active_packs = pack_manager.get_active_packs()
            
            # Get business profile if available
            business_profile = {}
            try:
                from util.entrepreneur_config import get_entrepreneur_config
                config = get_entrepreneur_config()
                business_profile = {
                    "business_name": config.business_profile.business_name,
                    "business_type": config.business_profile.business_type,
                    "industry": config.business_profile.industry
                }
            except:
                pass
            
            return {
                "user_type": "entrepreneur",
                "active_tailor_packs": [{"name": pack.name, "category": pack.business_category} for pack in active_packs],
                "business_profile": business_profile,
                "available_tools": [
                    "Business Dashboard", "CRM Manager", "Finance Tracker", 
                    "Time Tracking", "KPI Monitoring", "Report Generation"
                ],
                "context_focus": "business_productivity_and_growth"
            }
        except Exception as e:
            return {
                "user_type": "entrepreneur",
                "active_tailor_packs": [],
                "business_profile": {},
                "available_tools": [],
                "context_focus": "business_productivity_and_growth"
            }
    
    def is_command(self, message):
        # Enhanced command recognition for entrepreneurs
        command_keywords = [
            "send email", "add password", "create note", "schedule",
            "add expense", "search", "open", "close", "show",
            # Business-specific commands
            "track revenue", "add customer", "create invoice", "schedule meeting",
            "add task", "track time", "generate report", "analyze performance",
            "show dashboard", "import pack", "install tailor pack",
            "check kpis", "view pipeline", "export data"
        ]
        return any(keyword in message.lower() for keyword in command_keywords)
    
    def execute_command(self, command, context):
        self.status_label.setText("Executing command...")
        
        # Parse and execute command
        result = self.parse_and_execute(command, context)
        
        if result["success"]:
            self.append_message("AI", f"✓ Command executed: {result['message']}")
        else:
            self.append_message("AI", f"✗ Command failed: {result['message']}")
        
        self.status_label.setText("Ready")
    
    def parse_and_execute(self, command, context):
        command_lower = command.lower()
        
        try:
            # Email commands
            if "send email" in command_lower:
                # Extract email details and execute
                return {"success": True, "message": "Email command recognized (implementation needed)"}
            
            # Password commands
            elif "add password" in command_lower or "generate password" in command_lower:
                return {"success": True, "message": "Password command recognized (implementation needed)"}
            
            # Note commands
            elif "create note" in command_lower or "add note" in command_lower:
                return {"success": True, "message": "Note command recognized (implementation needed)"}
            
            # Calendar commands
            elif "schedule" in command_lower or "add event" in command_lower:
                return {"success": True, "message": "Calendar command recognized (implementation needed)"}
            
            else:
                return {"success": False, "message": "Command not recognized"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_ai_response(self, message, context):
        if not self.provider:
            self.append_message("AI", "AI provider not configured. Please set up OpenAI or Ollama.")
            return
        
        self.status_label.setText("AI is thinking...")
        self.input_field.setEnabled(False)
        
        # Create worker thread
        self.worker = AIWorker(message, context, self.provider)
        self.worker.response_ready.connect(self.on_response_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_response_ready(self, response):
        self.append_message("AI", response)
        self.status_label.setText("Ready")
        self.input_field.setEnabled(True)
    
    def on_error(self, error):
        self.append_message("AI", f"Error: {error}")
        self.status_label.setText("Error occurred")
        self.input_field.setEnabled(True)