"""
Dependency Manager for WestfallPersonalAssistant
Manages package dependencies and system requirements
"""

import sys
import os
import subprocess
import pkg_resources
import platform
import json
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QThread

class DependencyInstallWorker(QThread):
    """Worker thread for installing dependencies"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, packages):
        super().__init__()
        self.packages = packages
    
    def run(self):
        try:
            for package in self.packages:
                self.progress_signal.emit(f"Installing {package}...")
                result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.finished_signal.emit(False, f"Failed to install {package}: {result.stderr}")
                    return
            
            self.finished_signal.emit(True, "All packages installed successfully")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class DependencyManager:
    """Manages dependencies for the application"""
    
    def __init__(self):
        self.required_packages = {
            "core": [
                "PyQt5>=5.15.0",
                "cryptography>=3.0.0",
                "requests>=2.25.0"
            ],
            "screen_intelligence": [
                "mss>=6.0.0",
                "pillow>=8.0.0",
                "opencv-python>=4.5.0",
                "pytesseract>=0.3.8",
                "numpy>=1.20.0"
            ],
            "ai_features": [
                "openai>=0.27.0",
                "transformers>=4.10.0"
            ],
            "business_tools": [
                "pandas>=1.3.0",
                "sqlalchemy>=1.4.0",
                "matplotlib>=3.4.0"
            ]
        }
    
    def check_dependencies(self):
        """Check which dependencies are missing or outdated"""
        missing = []
        outdated = []
        installed = []
        
        all_packages = []
        for category, packages in self.required_packages.items():
            all_packages.extend(packages)
        
        for package_spec in all_packages:
            package_name = package_spec.split(">=")[0].split("==")[0]
            
            try:
                # Check if package is installed
                pkg_resources.get_distribution(package_name)
                installed.append(package_name)
                
                # TODO: Add version checking for outdated packages
                
            except pkg_resources.DistributionNotFound:
                missing.append(package_spec)
        
        return {
            "missing": missing,
            "outdated": outdated,
            "installed": installed
        }
    
    def install_packages(self, packages):
        """Install packages using pip"""
        try:
            for package in packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return True, "Packages installed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Installation failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

class DependencyManagerDialog(QDialog):
    """Dialog for managing dependencies"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dependency_manager = DependencyManager()
        self.worker = None
        self.init_ui()
        self.check_dependencies()
    
    def init_ui(self):
        self.setWindowTitle("Dependency Manager")
        self.setModal(True)
        self.resize(600, 400)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #000000;
                color: white;
            }
            QLabel {
                color: white;
            }
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
            }
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("📦 Dependency Manager")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Create tabs for different categories
        self.tabs = QTabWidget()
        
        # Missing dependencies tab
        self.missing_tab = QWidget()
        missing_layout = QVBoxLayout()
        
        missing_layout.addWidget(QLabel("Missing Dependencies:"))
        self.missing_list = QListWidget()
        missing_layout.addWidget(self.missing_list)
        
        self.install_missing_btn = QPushButton("Install Missing Dependencies")
        self.install_missing_btn.clicked.connect(self.install_missing)
        missing_layout.addWidget(self.install_missing_btn)
        
        self.missing_tab.setLayout(missing_layout)
        self.tabs.addTab(self.missing_tab, "Missing")
        
        # Installed dependencies tab
        self.installed_tab = QWidget()
        installed_layout = QVBoxLayout()
        
        installed_layout.addWidget(QLabel("Installed Dependencies:"))
        self.installed_list = QListWidget()
        installed_layout.addWidget(self.installed_list)
        
        self.installed_tab.setLayout(installed_layout)
        self.tabs.addTab(self.installed_tab, "Installed")
        
        layout.addWidget(self.tabs)
        
        # Progress area
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(100)
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.check_dependencies)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def check_dependencies(self):
        """Check dependency status"""
        self.progress_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Checking dependencies...")
        
        result = self.dependency_manager.check_dependencies()
        
        # Clear lists
        self.missing_list.clear()
        self.installed_list.clear()
        
        # Populate missing
        for package in result["missing"]:
            self.missing_list.addItem(f"❌ {package}")
        
        # Populate installed
        for package in result["installed"]:
            self.installed_list.addItem(f"✅ {package}")
        
        # Update button state
        self.install_missing_btn.setEnabled(len(result["missing"]) > 0)
        
        if result["missing"]:
            self.progress_text.append(f"Found {len(result['missing'])} missing dependencies")
        else:
            self.progress_text.append("All dependencies are installed!")
    
    def install_missing(self):
        """Install missing dependencies"""
        missing_packages = []
        for i in range(self.missing_list.count()):
            item_text = self.missing_list.item(i).text()
            package = item_text.replace("❌ ", "")
            missing_packages.append(package)
        
        if not missing_packages:
            return
        
        self.install_missing_btn.setEnabled(False)
        self.progress_text.append(f"Starting installation of {len(missing_packages)} packages...")
        
        # Create worker thread
        self.worker = DependencyInstallWorker(missing_packages)
        self.worker.progress_signal.connect(self.on_install_progress)
        self.worker.finished_signal.connect(self.on_install_finished)
        self.worker.start()
    
    def on_install_progress(self, message):
        """Handle installation progress"""
        self.progress_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        # Scroll to bottom
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_install_finished(self, success, message):
        """Handle installation completion"""
        self.progress_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.install_missing_btn.setEnabled(True)
        
        if success:
            # Refresh the dependency list
            self.check_dependencies()
            QMessageBox.information(self, "Success", "Dependencies installed successfully!")
        else:
            QMessageBox.critical(self, "Installation Failed", message)