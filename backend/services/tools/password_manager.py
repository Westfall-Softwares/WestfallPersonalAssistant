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