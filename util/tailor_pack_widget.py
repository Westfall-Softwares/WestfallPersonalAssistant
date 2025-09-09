"""
Tailor Pack Manager Widget
UI for managing Tailor Packs in the Entrepreneur Assistant
"""

import os
import json
from typing import Dict, List, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from utils.tailor_pack_manager import get_tailor_pack_manager, TailorPackInfo


class PackInstallWorker(QThread):
    """Worker thread for installing Tailor Packs"""
    
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, zip_path: str):
        super().__init__()
        self.zip_path = zip_path
        self.pack_manager = get_tailor_pack_manager()
    
    def run(self):
        try:
            self.progress.emit("Starting pack installation...")
            result = self.pack_manager.import_tailor_pack(self.zip_path)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})


class TailorPackCard(QWidget):
    """Card widget for displaying Tailor Pack information"""
    
    pack_toggled = pyqtSignal(str, bool)  # pack_id, enabled
    
    def __init__(self, pack_info: TailorPackInfo):
        super().__init__()
        self.pack_info = pack_info
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header with pack name and toggle
        header_layout = QHBoxLayout()
        
        # Pack icon and name
        name_layout = QVBoxLayout()
        name_label = QLabel(self.pack_info.name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_layout.addWidget(name_label)
        
        version_label = QLabel(f"v{self.pack_info.version}")
        version_label.setStyleSheet("color: #666; font-size: 10px;")
        name_layout.addWidget(version_label)
        
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        # Enable/Disable toggle
        self.toggle_button = QPushButton("Enabled" if self.pack_info.enabled else "Disabled")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(self.pack_info.enabled)
        self.toggle_button.clicked.connect(self.toggle_pack)
        self.update_toggle_style()
        header_layout.addWidget(self.toggle_button)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(self.pack_info.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #333; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Metadata
        meta_layout = QHBoxLayout()
        
        category_label = QLabel(f"📂 {self.pack_info.business_category}")
        category_label.setStyleSheet("font-size: 10px; color: #666;")
        meta_layout.addWidget(category_label)
        
        audience_label = QLabel(f"👥 {self.pack_info.target_audience}")
        audience_label.setStyleSheet("font-size: 10px; color: #666;")
        meta_layout.addWidget(audience_label)
        
        meta_layout.addStretch()
        
        if self.pack_info.license_required:
            license_label = QLabel("🔒 License Required")
            license_label.setStyleSheet("font-size: 10px; color: #ff6600;")
            meta_layout.addWidget(license_label)
        
        layout.addLayout(meta_layout)
        
        # Features list
        if self.pack_info.feature_list:
            features_label = QLabel("Features: " + ", ".join(self.pack_info.feature_list[:3]))
            if len(self.pack_info.feature_list) > 3:
                features_label.setText(features_label.text() + f" (+{len(self.pack_info.feature_list) - 3} more)")
            features_label.setStyleSheet("font-size: 10px; color: #444;")
            features_label.setWordWrap(True)
            layout.addWidget(features_label)
        
        # Set card styling
        self.setStyleSheet("""
            TailorPackCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            TailorPackCard:hover {
                border-color: #4CAF50;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)
        self.setMaximumHeight(150)
        self.setMinimumHeight(130)
    
    def toggle_pack(self):
        """Toggle pack enabled/disabled state"""
        enabled = self.toggle_button.isChecked()
        self.pack_toggled.emit(self.pack_info.id, enabled)
        self.pack_info.enabled = enabled
        self.toggle_button.setText("Enabled" if enabled else "Disabled")
        self.update_toggle_style()
    
    def update_toggle_style(self):
        """Update toggle button styling based on state"""
        if self.pack_info.enabled:
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)


class TailorPackManagerWidget(QMainWindow):
    """Main widget for managing Tailor Packs"""
    
    def __init__(self):
        super().__init__()
        self.pack_manager = get_tailor_pack_manager()
        self.pack_cards = {}
        self.install_worker = None
        self.init_ui()
        self.load_packs()
    
    def init_ui(self):
        self.setWindowTitle("Tailor Pack Manager - Entrepreneur Assistant")
        self.setGeometry(200, 200, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Tailor Pack Manager")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Import pack button
        import_btn = QPushButton("📦 Import Pack")
        import_btn.clicked.connect(self.import_pack)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        header_layout.addWidget(import_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_packs)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # Tabs
        tab_widget = QTabWidget()
        
        # Installed Packs tab
        installed_tab = QWidget()
        installed_layout = QVBoxLayout(installed_tab)
        
        # Search/filter for installed packs
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search installed packs...")
        self.search_input.textChanged.connect(self.filter_packs)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        category_filter = QComboBox()
        category_filter.addItems(["All Categories", "Marketing", "Sales", "Finance", "Operations", "Integration"])
        category_filter.currentTextChanged.connect(self.filter_packs)
        search_layout.addWidget(QLabel("Category:"))
        search_layout.addWidget(category_filter)
        
        installed_layout.addLayout(search_layout)
        
        # Installed packs list
        self.installed_scroll = QScrollArea()
        self.installed_widget = QWidget()
        self.installed_layout = QVBoxLayout(self.installed_widget)
        self.installed_layout.setAlignment(Qt.AlignTop)
        self.installed_scroll.setWidget(self.installed_widget)
        self.installed_scroll.setWidgetResizable(True)
        installed_layout.addWidget(self.installed_scroll)
        
        tab_widget.addTab(installed_tab, "📦 Installed Packs")
        
        # Marketplace tab (placeholder for future)
        marketplace_tab = QWidget()
        marketplace_layout = QVBoxLayout(marketplace_tab)
        marketplace_placeholder = QLabel("Marketplace coming soon...\nHere you'll be able to browse and download new Tailor Packs.")
        marketplace_placeholder.setAlignment(Qt.AlignCenter)
        marketplace_placeholder.setStyleSheet("color: #666; font-size: 14px;")
        marketplace_layout.addWidget(marketplace_placeholder)
        tab_widget.addTab(marketplace_tab, "🛍️ Marketplace")
        
        main_layout.addWidget(tab_widget)
        
        # Set window styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
        """)
    
    def load_packs(self):
        """Load and display installed Tailor Packs"""
        self.status_label.setText("Loading packs...")
        
        # Clear existing cards
        for card in self.pack_cards.values():
            card.setParent(None)
        self.pack_cards.clear()
        
        # Get installed packs
        installed_packs = self.pack_manager.get_installed_packs()
        
        if not installed_packs:
            no_packs_label = QLabel("No Tailor Packs installed.\nClick 'Import Pack' to add your first pack.")
            no_packs_label.setAlignment(Qt.AlignCenter)
            no_packs_label.setStyleSheet("color: #666; font-size: 14px; padding: 50px;")
            self.installed_layout.addWidget(no_packs_label)
        else:
            for pack in installed_packs:
                card = TailorPackCard(pack)
                card.pack_toggled.connect(self.toggle_pack)
                self.pack_cards[pack.id] = card
                self.installed_layout.addWidget(card)
        
        self.status_label.setText(f"Loaded {len(installed_packs)} pack(s)")
    
    def import_pack(self):
        """Import a new Tailor Pack from ZIP file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tailor Pack ZIP file",
            "",
            "ZIP files (*.zip);;All files (*.*)"
        )
        
        if file_path:
            self.status_label.setText("Installing pack...")
            
            # Create progress dialog
            progress_dialog = QProgressDialog("Installing Tailor Pack...", "Cancel", 0, 0, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()
            
            # Start installation worker
            self.install_worker = PackInstallWorker(file_path)
            self.install_worker.progress.connect(progress_dialog.setLabelText)
            self.install_worker.finished.connect(lambda result: self.on_install_finished(result, progress_dialog))
            self.install_worker.start()
    
    def on_install_finished(self, result: Dict[str, Any], progress_dialog: QProgressDialog):
        """Handle pack installation completion"""
        progress_dialog.close()
        
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.load_packs()  # Reload packs list
            self.status_label.setText("Pack installed successfully")
        else:
            QMessageBox.critical(self, "Installation Failed", result["error"])
            self.status_label.setText("Pack installation failed")
    
    def toggle_pack(self, pack_id: str, enabled: bool):
        """Toggle pack enabled/disabled state"""
        if enabled:
            result = self.pack_manager.enable_pack(pack_id)
        else:
            result = self.pack_manager.disable_pack(pack_id)
        
        if result["success"]:
            self.status_label.setText(result["message"])
        else:
            QMessageBox.warning(self, "Error", result["error"])
            # Revert the toggle state in UI
            if pack_id in self.pack_cards:
                card = self.pack_cards[pack_id]
                card.toggle_button.setChecked(not enabled)
                card.pack_info.enabled = not enabled
                card.toggle_button.setText("Enabled" if not enabled else "Disabled")
                card.update_toggle_style()
    
    def filter_packs(self):
        """Filter displayed packs based on search criteria"""
        search_text = self.search_input.text().lower()
        
        for pack_id, card in self.pack_cards.items():
            pack = card.pack_info
            visible = (
                search_text in pack.name.lower() or
                search_text in pack.description.lower() or
                search_text in pack.business_category.lower()
            )
            card.setVisible(visible)


# For compatibility with the main application
def TailorPackManagerWindow():
    """Factory function for TailorPackManagerWidget"""
    return TailorPackManagerWidget()