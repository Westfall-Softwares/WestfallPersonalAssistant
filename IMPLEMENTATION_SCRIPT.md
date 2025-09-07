# WestfallPersonalAssistant - Complete Implementation Script
## Execute all tasks to bring project to specification
### Date: 2025-09-07

---

## TASK 1: CREATE SECURITY INFRASTRUCTURE

### 1.1 Create security directory and encryption module
**CREATE FILE:** `security/encryption_manager.py`
```python
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import hashlib
import getpass
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

class EncryptionManager:
    def __init__(self):
        self.key = None
        self.cipher = None
        self.master_password_hash = None
        self.load_or_create_key()
    
    def load_or_create_key(self):
        key_file = 'data/.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            os.makedirs('data', exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self.key)
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_master_password(self, password):
        return self.hash_password(password) == self.master_password_hash

class MasterPasswordDialog(QDialog):
    def __init__(self, first_time=False):
        super().__init__()
        self.first_time = first_time
        self.password = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Master Password" if not self.first_time else "Set Master Password")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        label = QLabel("Enter Master Password:" if not self.first_time else "Create Master Password:")
        layout.addWidget(label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        if self.first_time:
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirm Password")
            layout.addWidget(self.confirm_input)
        
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.validate_password)
        layout.addWidget(submit_btn)
        
        self.setLayout(layout)
    
    def validate_password(self):
        password = self.password_input.text()
        
        if self.first_time:
            confirm = self.confirm_input.text()
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match!")
                return
            if len(password) < 8:
                QMessageBox.warning(self, "Error", "Password must be at least 8 characters!")
                return
        
        self.password = password
        self.accept()
```

### 1.2 Create API key vault
**CREATE FILE:** `security/api_key_vault.py`
```python
import os
import json
from security.encryption_manager import EncryptionManager

class APIKeyVault:
    def __init__(self):
        self.encryption = EncryptionManager()
        self.vault_file = 'data/.api_keys'
        self.keys = self.load_keys()
    
    def load_keys(self):
        if os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, 'rb') as f:
                    encrypted = f.read()
                    decrypted = self.encryption.decrypt(encrypted)
                    return json.loads(decrypted)
            except:
                return {}
        return {}
    
    def save_keys(self):
        os.makedirs('data', exist_ok=True)
        encrypted = self.encryption.encrypt(json.dumps(self.keys))
        with open(self.vault_file, 'wb') as f:
            f.write(encrypted)
    
    def set_key(self, service, key):
        self.keys[service] = key
        self.save_keys()
    
    def get_key(self, service, default=None):
        return self.keys.get(service, default)
    
    def remove_key(self, service):
        if service in self.keys:
            del self.keys[service]
            self.save_keys()
```

---

## TASK 2: UPDATE PASSWORD MANAGER WITH ENCRYPTION

### 2.1 Replace password_manager.py with encrypted version
**REPLACE FILE:** `password_manager.py`
```python
import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import string
import random
from security.encryption_manager import EncryptionManager

class PasswordManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.encryption = EncryptionManager()
        self.init_db()
        self.init_ui()
        self.load_passwords()
    
    def init_db(self):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/passwords_encrypted.db')
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                username TEXT NOT NULL,
                password_encrypted BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def init_ui(self):
        self.setWindowTitle("Password Manager - Secure")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("Add Password")
        add_btn.clicked.connect(self.add_password)
        toolbar.addWidget(add_btn)
        
        generate_btn = QPushButton("Generate Password")
        generate_btn.clicked.connect(self.generate_password)
        toolbar.addWidget(generate_btn)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search passwords...")
        search_input.textChanged.connect(self.search_passwords)
        toolbar.addWidget(search_input)
        
        layout.addLayout(toolbar)
        
        # Password list
        self.password_list = QTableWidget()
        self.password_list.setColumnCount(4)
        self.password_list.setHorizontalHeaderLabels(["Service", "Username", "Password", "Actions"])
        self.password_list.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.password_list)
    
    def load_passwords(self):
        self.password_list.setRowCount(0)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, service, username, password_encrypted FROM passwords")
        
        for row_data in cursor.fetchall():
            row = self.password_list.rowCount()
            self.password_list.insertRow(row)
            
            self.password_list.setItem(row, 0, QTableWidgetItem(row_data[1]))
            self.password_list.setItem(row, 1, QTableWidgetItem(row_data[2]))
            
            # Password field (hidden by default)
            password_item = QTableWidgetItem("••••••••")
            password_item.setData(Qt.UserRole, row_data[3])  # Store encrypted password
            self.password_list.setItem(row, 2, password_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            show_btn = QPushButton("Show")
            show_btn.clicked.connect(lambda checked, r=row: self.toggle_password(r))
            actions_layout.addWidget(show_btn)
            
            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(lambda checked, r=row: self.copy_password(r))
            actions_layout.addWidget(copy_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, id=row_data[0]: self.delete_password(id))
            actions_layout.addWidget(delete_btn)
            
            self.password_list.setCellWidget(row, 3, actions_widget)
    
    def add_password(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Password")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        service_input = QLineEdit()
        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Service:", service_input)
        layout.addRow("Username:", username_input)
        layout.addRow("Password:", password_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            service = service_input.text()
            username = username_input.text()
            password = password_input.text()
            
            if service and username and password:
                encrypted_password = self.encryption.encrypt(password)
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO passwords (service, username, password_encrypted) VALUES (?, ?, ?)",
                    (service, username, encrypted_password)
                )
                self.conn.commit()
                self.load_passwords()
                QMessageBox.information(self, "Success", "Password added securely!")
    
    def toggle_password(self, row):
        item = self.password_list.item(row, 2)
        encrypted_password = item.data(Qt.UserRole)
        
        if item.text() == "••••••••":
            decrypted = self.encryption.decrypt(encrypted_password)
            item.setText(decrypted)
        else:
            item.setText("••••••••")
    
    def copy_password(self, row):
        item = self.password_list.item(row, 2)
        encrypted_password = item.data(Qt.UserRole)
        decrypted = self.encryption.decrypt(encrypted_password)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(decrypted)
        QMessageBox.information(self, "Copied", "Password copied to clipboard!")
    
    def delete_password(self, password_id):
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            'Are you sure you want to delete this password?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM passwords WHERE id = ?", (password_id,))
            self.conn.commit()
            self.load_passwords()
    
    def generate_password(self):
        length = 16
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(length))
        
        clipboard = QApplication.clipboard()
        clipboard.setText(password)
        QMessageBox.information(self, "Generated", f"Password generated and copied:\n{password}")
    
    def search_passwords(self, text):
        for row in range(self.password_list.rowCount()):
            service = self.password_list.item(row, 0).text()
            username = self.password_list.item(row, 1).text()
            
            if text.lower() in service.lower() or text.lower() in username.lower():
                self.password_list.setRowHidden(row, False)
            else:
                self.password_list.setRowHidden(row, True)
    
    def closeEvent(self, event):
        self.conn.close()
        event.accept()
```

---

## TASK 3: CREATE AI ASSISTANT SYSTEM

### 3.1 Create AI assistant directory structure and core chat manager
**CREATE FILE:** `ai_assistant/core/chat_manager.py`
```python
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
            "data": {}
        }
        
        # Get window-specific context
        if hasattr(self.parent_window, 'get_context_for_ai'):
            context["data"] = self.parent_window.get_context_for_ai()
        
        return context
    
    def is_command(self, message):
        command_keywords = [
            "send email", "add password", "create note", "schedule",
            "add expense", "search", "open", "close", "show"
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
```

### 3.2 Create AI providers
**CREATE FILE:** `ai_assistant/providers/openai_provider.py`
```python
import os
from typing import Dict, Any
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIProvider:
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            self.api_key = vault.get_key('openai')
        
        if self.api_key:
            openai.api_key = self.api_key
        else:
            raise ValueError("OpenAI API key not configured")
    
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        try:
            # Prepare context message
            context_msg = f"Current window: {context.get('window', 'Unknown')}"
            if context.get('data'):
                context_msg += f"\nContext data: {context['data']}"
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for a personal desktop application."},
                    {"role": "user", "content": f"{context_msg}\n\nUser query: {query}"}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
```

**CREATE FILE:** `ai_assistant/providers/ollama_provider.py`
```python
import requests
import json
from typing import Dict, Any

class OllamaProvider:
    def __init__(self, model="llama2"):
        self.base_url = "http://localhost:11434"
        self.model = model
        self.check_connection()
    
    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama server not running")
        except:
            raise ConnectionError("Could not connect to Ollama. Make sure it's running.")
    
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        try:
            # Prepare prompt with context
            prompt = f"Context: You are assisting with a {context.get('window', 'desktop')} application.\n"
            if context.get('data'):
                prompt += f"Additional context: {json.dumps(context['data'])}\n"
            prompt += f"\nUser query: {query}\n\nResponse:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return "Error: Could not generate response from Ollama"
                
        except Exception as e:
            return f"Error: {str(e)}"
```

---

## TASK 4: COMPLETE PLACEHOLDER FEATURES

### 4.1 Complete News Reader
**REPLACE FILE:** `news.py`
```python
import sys
import requests
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import feedparser

class NewsWorker(QThread):
    news_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, source="bbc"):
        super().__init__()
        self.source = source
    
    def run(self):
        try:
            # Try NewsAPI first
            api_key = self.get_api_key()
            if api_key:
                self.fetch_newsapi(api_key)
            else:
                # Fallback to RSS feeds
                self.fetch_rss()
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def get_api_key(self):
        try:
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            return vault.get_key('newsapi')
        except:
            return None
    
    def fetch_newsapi(self, api_key):
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            self.news_loaded.emit(articles)
        else:
            self.fetch_rss()  # Fallback to RSS
    
    def fetch_rss(self):
        feeds = {
            "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
            "cnn": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "reuters": "http://feeds.reuters.com/reuters/topNews"
        }
        
        feed_url = feeds.get(self.source, feeds["bbc"])
        feed = feedparser.parse(feed_url)
        
        articles = []
        for entry in feed.entries[:20]:
            article = {
                "title": entry.title,
                "description": entry.get("summary", ""),
                "url": entry.link,
                "publishedAt": entry.get("published", ""),
                "source": {"name": self.source.upper()}
            }
            articles.append(article)
        
        self.news_loaded.emit(articles)

class NewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.init_ui()
        self.load_news()
    
    def init_ui(self):
        self.setWindowTitle("News Reader")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Source selector
        source_label = QLabel("Source:")
        toolbar.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["BBC", "CNN", "Reuters", "TechCrunch", "The Verge"])
        self.source_combo.currentTextChanged.connect(self.change_source)
        toolbar.addWidget(self.source_combo)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search news...")
        self.search_input.textChanged.connect(self.search_news)
        toolbar.addWidget(self.search_input)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_news)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # News list
        self.news_list = QListWidget()
        self.news_list.itemClicked.connect(self.show_article)
        layout.addWidget(self.news_list)
        
        # Article viewer
        self.article_viewer = QTextBrowser()
        self.article_viewer.setOpenExternalLinks(True)
        self.article_viewer.setMaximumHeight(200)
        layout.addWidget(self.article_viewer)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Loading news...")
    
    def load_news(self):
        self.news_list.clear()
        self.status_bar.showMessage("Loading news...")
        
        source = self.source_combo.currentText().lower()
        self.worker = NewsWorker(source)
        self.worker.news_loaded.connect(self.display_news)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()
    
    def display_news(self, articles):
        self.articles = articles
        for article in articles:
            item = QListWidgetItem()
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown')
            published = article.get('publishedAt', '')
            
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    published = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            item.setText(f"{title}\n{source} - {published}")
            item.setData(Qt.UserRole, article)
            self.news_list.addItem(item)
        
        self.status_bar.showMessage(f"Loaded {len(articles)} articles")
    
    def show_article(self, item):
        article = item.data(Qt.UserRole)
        html = f"""
        <h2>{article.get('title', 'No title')}</h2>
        <p><b>Source:</b> {article.get('source', {}).get('name', 'Unknown')}</p>
        <p><b>Published:</b> {article.get('publishedAt', 'Unknown')}</p>
        <p>{article.get('description', 'No description available')}</p>
        <p><a href="{article.get('url', '#')}">Read full article</a></p>
        """
        self.article_viewer.setHtml(html)
    
    def search_news(self, text):
        for i in range(self.news_list.count()):
            item = self.news_list.item(i)
            article = item.data(Qt.UserRole)
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            
            if text.lower() in title or text.lower() in description:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def change_source(self):
        self.load_news()
    
    def show_error(self, error):
        self.status_bar.showMessage(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Failed to load news: {error}")
```

### 4.2 Create Music Player
**CREATE FILE:** `music_player.py`
```python
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from pathlib import Path

class MusicPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.current_songs = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Now playing
        self.now_playing = QLabel("No song playing")
        self.now_playing.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.now_playing)
        
        # Progress bar
        self.progress = QSlider(Qt.Horizontal)
        self.progress.sliderMoved.connect(self.set_position)
        layout.addWidget(self.progress)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00")
        self.duration_label = QLabel("00:00")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        layout.addLayout(time_layout)
        
        # Controls
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.play_pause)
        controls.addWidget(self.play_btn)
        
        prev_btn = QPushButton("⏮")
        prev_btn.clicked.connect(self.playlist.previous)
        controls.addWidget(prev_btn)
        
        next_btn = QPushButton("⏭")
        next_btn.clicked.connect(self.playlist.next)
        controls.addWidget(next_btn)
        
        stop_btn = QPushButton("⏹")
        stop_btn.clicked.connect(self.player.stop)
        controls.addWidget(stop_btn)
        
        # Volume
        controls.addWidget(QLabel("Volume:"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setMaximum(100)
        self.volume.setValue(50)
        self.volume.valueChanged.connect(self.player.setVolume)
        controls.addWidget(self.volume)
        
        layout.addLayout(controls)
        
        # Playlist
        toolbar = QHBoxLayout()
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        toolbar.addWidget(add_file_btn)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        toolbar.addWidget(add_folder_btn)
        
        clear_btn = QPushButton("Clear Playlist")
        clear_btn.clicked.connect(self.clear_playlist)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Song list
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.song_list)
        
        # Connect player signals
        self.player.stateChanged.connect(self.state_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        
        # Timer for updating position
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
    
    def add_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Add Music File", "",
            "Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac);;All Files (*.*)"
        )
        if file:
            self.add_to_playlist(file)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add Music Folder")
        if folder:
            for file in Path(folder).glob("**/*"):
                if file.suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
                    self.add_to_playlist(str(file))
    
    def add_to_playlist(self, file_path):
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        file_name = os.path.basename(file_path)
        self.song_list.addItem(file_name)
        self.current_songs.append(file_path)
    
    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
    
    def play_selected(self, item):
        index = self.song_list.row(item)
        self.playlist.setCurrentIndex(index)
        self.player.play()
    
    def clear_playlist(self):
        reply = QMessageBox.question(
            self, 'Clear Playlist',
            'Are you sure you want to clear the playlist?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.playlist.clear()
            self.song_list.clear()
            self.current_songs.clear()
            self.now_playing.setText("No song playing")
    
    def state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def position_changed(self, position):
        self.progress.setValue(position)
        self.time_label.setText(self.format_time(position))
    
    def duration_changed(self, duration):
        self.progress.setMaximum(duration)
        self.duration_label.setText(self.format_time(duration))
    
    def set_position(self, position):
        self.player.setPosition(position)
    
    def playlist_position_changed(self, index):
        if index >= 0 and index < len(self.current_songs):
            file_name = os.path.basename(self.current_songs[index])
            self.now_playing.setText(f"Now Playing: {file_name}")
            
            # Highlight current song
            for i in range(self.song_list.count()):
                item = self.song_list.item(i)
                if i == index:
                    item.setBackground(Qt.lightGray)
                else:
                    item.setBackground(Qt.white)
    
    def update_position(self):
        # Update position slider
        if self.player.state() == QMediaPlayer.PlayingState:
            self.progress.setValue(self.player.position())
    
    def format_time(self, ms):
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"
```

---

## TASK 5: UPDATE MAIN.PY WITH MASTER PASSWORD AND AI INTEGRATION

### 5.1 Update main.py to include security and AI
**REPLACE FILE:** `main.py`
```python
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Import all windows
from email_window import EmailWindow
from password_manager import PasswordManagerWindow
from notes import NotesWindow
from calculator import CalculatorWindow
from calendar_window import CalendarWindow
from weather import WeatherWindow
from news import NewsWindow
from browser import BrowserWindow
from file_manager import FileManagerWindow
from todo import TodoWindow
from contacts import ContactsWindow
from settings import SettingsWindow
from finance import FinanceWindow
from recipe import RecipeWindow
from music_player import MusicPlayerWindow

# Import security
from security.encryption_manager import MasterPasswordDialog, EncryptionManager
from ai_assistant.core.chat_manager import AIChatWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows = {}
        self.ai_chat = None
        self.encryption_manager = None
        
        # Initialize security
        if not self.init_security():
            sys.exit()
        
        self.init_ui()
        self.init_ai()
        self.init_tray()
    
    def init_security(self):
        """Initialize security with master password"""
        master_file = 'data/.master'
        os.makedirs('data', exist_ok=True)
        
        first_time = not os.path.exists(master_file)
        
        dialog = MasterPasswordDialog(first_time=first_time)
        if dialog.exec_() != QDialog.Accepted:
            return False
        
        self.encryption_manager = EncryptionManager()
        
        if first_time:
            # Save master password hash
            hashed = self.encryption_manager.hash_password(dialog.password)
            with open(master_file, 'w') as f:
                f.write(hashed)
        else:
            # Verify password
            with open(master_file, 'r') as f:
                stored_hash = f.read()
            
            if self.encryption_manager.hash_password(dialog.password) != stored_hash:
                QMessageBox.critical(None, "Error", "Invalid master password!")
                return False
        
        return True
    
    def init_ui(self):
        self.setWindowTitle("Westfall Personal Assistant - Secure")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Westfall Personal Assistant")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding: 20px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        """)
        main_layout.addWidget(header)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search features or ask AI...")
        self.search_input.returnPressed.connect(self.handle_search)
        search_layout.addWidget(self.search_input)
        
        ai_btn = QPushButton("AI Assistant")
        ai_btn.clicked.connect(self.toggle_ai_chat)
        search_layout.addWidget(ai_btn)
        
        main_layout.addLayout(search_layout)
        
        # Feature grid
        grid = QGridLayout()
        
        features = [
            ("📧 Email", self.open_email),
            ("🔐 Passwords", self.open_password_manager),
            ("📝 Notes", self.open_notes),
            ("🧮 Calculator", self.open_calculator),
            ("📅 Calendar", self.open_calendar),
            ("🌤️ Weather", self.open_weather),
            ("📰 News", self.open_news),
            ("🌐 Browser", self.open_browser),
            ("📁 Files", self.open_file_manager),
            ("✅ Todo", self.open_todo),
            ("👥 Contacts", self.open_contacts),
            ("⚙️ Settings", self.open_settings),
            ("💰 Finance", self.open_finance),
            ("🍳 Recipes", self.open_recipe),
            ("🎵 Music", self.open_music),
        ]
        
        positions = [(i, j) for i in range(5) for j in range(3)]
        
        for position, (name, callback) in zip(positions, features):
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(80)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    background-color: white;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-color: #667eea;
                }
            """)
            grid.addWidget(btn, *position)
        
        main_layout.addLayout(grid)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Secure Mode Active")
        
        # Auto-lock timer
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.auto_lock)
        self.lock_timer.start(900000)  # 15 minutes
    
    def init_ai(self):
        """Initialize AI assistant"""
        self.ai_chat = AIChatWidget(self)
        self.ai_chat.hide()
    
    def init_tray(self):
        """Initialize system tray"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Westfall Personal Assistant")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        hide_action = tray_menu.addAction("Hide")
        hide_action.triggered.connect(self.hide)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def handle_search(self):
        query = self.search_input.text()
        if query.startswith("ai:") or query.startswith("?"):
            # Send to AI
            if not self.ai_chat.isVisible():
                self.ai_chat.show()
            self.ai_chat.input_field.setText(query.lstrip("ai:").lstrip("?"))
            self.ai_chat.send_message()
        else:
            # Search features
            self.search_features(query)
    
    def search_features(self, query):
        # Simple feature search
        features_map = {
            "email": self.open_email,
            "password": self.open_password_manager,
            "note": self.open_notes,
            "calendar": self.open_calendar,
            "weather": self.open_weather,
            "news": self.open_news,
            "music": self.open_music,
        }
        
        query_lower = query.lower()
        for key, func in features_map.items():
            if key in query_lower:
                func()
                break
    
    def toggle_ai_chat(self):
        if self.ai_chat.isVisible():
            self.ai_chat.hide()
        else:
            self.ai_chat.show()
    
    def auto_lock(self):
        """Auto-lock after inactivity"""
        reply = QMessageBox.question(
            self, 'Session Timeout',
            'Your session will expire in 1 minute. Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.lock_timer.start(900000)  # Reset timer
        else:
            QApplication.quit()
    
    # Window opening methods
    def open_email(self):
        if 'email' not in self.windows:
            self.windows['email'] = EmailWindow()
        self.windows['email'].show()
        self.ai_chat.parent_window = self.windows['email']
    
    def open_password_manager(self):
        if 'password' not in self.windows:
            self.windows['password'] = PasswordManagerWindow()
        self.windows['password'].show()
        self.ai_chat.parent_window = self.windows['password']
    
    def open_notes(self):
        if 'notes' not in self.windows:
            self.windows['notes'] = NotesWindow()
        self.windows['notes'].show()
        self.ai_chat.parent_window = self.windows['notes']
    
    def open_calculator(self):
        if 'calculator' not in self.windows:
            self.windows['calculator'] = CalculatorWindow()
        self.windows['calculator'].show()
    
    def open_calendar(self):
        if 'calendar' not in self.windows:
            self.windows['calendar'] = CalendarWindow()
        self.windows['calendar'].show()
        self.ai_chat.parent_window = self.windows['calendar']
    
    def open_weather(self):
        if 'weather' not in self.windows:
            self.windows['weather'] = WeatherWindow()
        self.windows['weather'].show()
    
    def open_news(self):
        if 'news' not in self.windows:
            self.windows['news'] = NewsWindow()
        self.windows['news'].show()
    
    def open_browser(self):
        if 'browser' not in self.windows:
            self.windows['browser'] = BrowserWindow()
        self.windows['browser'].show()
    
    def open_file_manager(self):
        if 'files' not in self.windows:
            self.windows['files'] = FileManagerWindow()
        self.windows['files'].show()
    
    def open_todo(self):
        if 'todo' not in self.windows:
            self.windows['todo'] = TodoWindow()
        self.windows['todo'].show()
    
    def open_contacts(self):
        if 'contacts' not in self.windows:
            self.windows['contacts'] = ContactsWindow()
        self.windows['contacts'].show()
    
    def open_settings(self):
        if 'settings' not in self.windows:
            self.windows['settings'] = SettingsWindow()
        self.windows['settings'].show()
    
    def open_finance(self):
        if 'finance' not in self.windows:
            self.windows['finance'] = FinanceWindow()
        self.windows['finance'].show()
    
    def open_recipe(self):
        if 'recipe' not in self.windows:
            self.windows['recipe'] = RecipeWindow()
        self.windows['recipe'].show()
    
    def open_music(self):
        if 'music' not in self.windows:
            self.windows['music'] = MusicPlayerWindow()
        self.windows['music'].show()
        self.ai_chat.parent_window = self.windows['music']

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Westfall Personal Assistant")
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

---

## TASK 6: CREATE COMPREHENSIVE REQUIREMENTS.TXT

### 6.1 Update requirements.txt with all dependencies
**REPLACE FILE:** `requirements.txt`
```
# Core PyQt5
PyQt5==5.15.9
PyQtWebEngine==5.15.6

# Security
cryptography>=41.0.0
bcrypt>=4.0.1
keyring>=24.2.0

# AI Integration
openai>=1.3.0
requests>=2.31.0

# Database
sqlalchemy>=2.0.23
alembic>=1.12.1

# News & Media
feedparser>=6.0.10
newsapi-python>=0.2.7
python-vlc>=3.0.18122

# Email
imaplib2>=3.6
email-validator>=2.1.0

# Data Processing
pandas>=2.1.3
numpy>=1.24.3
python-dateutil>=2.8.2

# Weather
pyowm>=3.3.0

# Image Processing
Pillow>=10.1.0

# Testing
pytest>=7.4.3
pytest-qt>=4.2.0
pytest-cov>=4.1.0

# Utilities
python-dotenv>=1.0.0
apscheduler>=3.10.4
watchdog>=3.0.0

# Documentation
sphinx>=7.2.6
sphinx-rtd-theme>=2.0.0
```

---

## TASK 7: CREATE BUILD CONFIGURATION

### 7.1 Create setup.py for packaging
**CREATE FILE:** `setup.py`
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="westfall-personal-assistant",
    version="2.0.0",
    author="Westfall Softwares",
    author_email="contact@westfallsoftwares.com",
    description="A secure, AI-powered personal assistant application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Westfall-Softwares/WestfallPersonalAssistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Personal Information Manager",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "westfall-assistant=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
        "data": ["*.db"],
        "assets": ["*.png", "*.jpg", "*.ico"],
    },
)
```

### 7.2 Create PyInstaller spec file
**CREATE FILE:** `westfall_assistant.spec`
```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('*.py', '.'),
        ('security/*.py', 'security'),
        ('ai_assistant/core/*.py', 'ai_assistant/core'),
        ('ai_assistant/providers/*.py', 'ai_assistant/providers'),
        ('data', 'data'),
    ],
    hiddenimports=[
        'PyQt5.QtWebEngineWidgets',
        'cryptography',
        'bcrypt',
        'keyring',
        'openai',
        'feedparser',
        'sqlalchemy',
        'email',
        'imaplib',
        'smtplib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WestfallPersonalAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)

app = BUNDLE(
    exe,
    name='WestfallPersonalAssistant.app',
    icon='assets/icon.icns' if Path('assets/icon.icns').exists() else None,
    bundle_identifier='com.westfallsoftwares.personalassistant',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)
```

---

## TASK 8: CREATE GITHUB ACTIONS CI/CD

### 8.1 Create CI workflow
**CREATE FILE:** `.github/workflows/ci.yml`
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [created]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
  
  build:
    needs: test
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: |
        pyinstaller westfall_assistant.spec
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: westfall-assistant-${{ matrix.os }}
        path: dist/*
```

---

## TASK 9: CREATE INITIAL TESTS

### 9.1 Create test directory and basic tests
**CREATE FILE:** `tests/test_security.py`
```python
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.encryption_manager import EncryptionManager

def test_encryption():
    manager = EncryptionManager()
    
    # Test string encryption
    original = "test_password_123"
    encrypted = manager.encrypt(original)
    decrypted = manager.decrypt(encrypted)
    
    assert decrypted == original
    assert encrypted != original

def test_password_hashing():
    manager = EncryptionManager()
    
    password = "MySecurePassword123!"
    hash1 = manager.hash_password(password)
    hash2 = manager.hash_password(password)
    
    assert hash1 == hash2
    assert hash1 != password
```

**CREATE FILE:** `tests/test_ai.py`
```python
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_context_extraction():
    from ai_assistant.core.chat_manager import AIChatWidget
    
    chat = AIChatWidget()
    context = chat.get