import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
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