"""
Entrepreneur Assistant Configuration System
Simplified settings management for business users
"""

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


@dataclass
class BusinessProfile:
    """Business profile information"""
    business_name: str = ""
    business_type: str = ""  # "entrepreneur", "small_business", "freelancer"
    industry: str = ""
    owner_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    website: str = ""
    tax_id: str = ""


@dataclass
class AppearanceSettings:
    """Appearance and UI settings"""
    theme: str = "dark"  # "dark", "light", "auto"
    font_size: int = 12
    compact_mode: bool = False
    show_tooltips: bool = True
    startup_dashboard: str = "business"  # "business", "tasks", "dashboard"


@dataclass
class SecuritySettings:
    """Security and privacy settings"""
    auto_lock_minutes: int = 30
    require_password_for_sensitive: bool = True
    backup_frequency: str = "daily"  # "never", "daily", "weekly"
    data_retention_days: int = 365
    encrypted_storage: bool = True


@dataclass
class IntegrationSettings:
    """Third-party integration settings"""
    email_sync_enabled: bool = True
    calendar_sync_enabled: bool = True
    cloud_backup_enabled: bool = False
    api_rate_limiting: bool = True
    offline_mode: bool = False


@dataclass
class TailorPackSettings:
    """Tailor Pack system settings"""
    auto_update_packs: bool = True
    allow_unsigned_packs: bool = False
    pack_data_isolation: bool = True
    marketplace_enabled: bool = True
    trial_mode_enabled: bool = True


class EntrepreneurConfig:
    """Main configuration manager for Entrepreneur Assistant"""
    
    def __init__(self, config_dir: str = None):
        # Use platform-specific configuration directory
        if config_dir is None:
            platform_manager = PlatformManager()
            app_dirs = platform_manager.setup_application_directories("westfall-assistant")
            self.config_dir = str(app_dirs['config'])
        else:
            self.config_dir = config_dir
        
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize settings
        self.business_profile = BusinessProfile()
        self.appearance = AppearanceSettings()
        self.security = SecuritySettings()
        self.integration = IntegrationSettings()
        self.tailor_packs = TailorPackSettings()
        
        # Load existing configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from files"""
        try:
            # Load business profile
            profile_path = os.path.join(self.config_dir, "business_profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    profile_data = json.load(f)
                    self.business_profile = BusinessProfile(**profile_data)
            
            # Load appearance settings
            appearance_path = os.path.join(self.config_dir, "appearance.json")
            if os.path.exists(appearance_path):
                with open(appearance_path, 'r') as f:
                    appearance_data = json.load(f)
                    self.appearance = AppearanceSettings(**appearance_data)
            
            # Load security settings
            security_path = os.path.join(self.config_dir, "security.json")
            if os.path.exists(security_path):
                with open(security_path, 'r') as f:
                    security_data = json.load(f)
                    self.security = SecuritySettings(**security_data)
            
            # Load integration settings
            integration_path = os.path.join(self.config_dir, "integration.json")
            if os.path.exists(integration_path):
                with open(integration_path, 'r') as f:
                    integration_data = json.load(f)
                    self.integration = IntegrationSettings(**integration_data)
            
            # Load Tailor Pack settings
            packs_path = os.path.join(self.config_dir, "tailor_packs.json")
            if os.path.exists(packs_path):
                with open(packs_path, 'r') as f:
                    packs_data = json.load(f)
                    self.tailor_packs = TailorPackSettings(**packs_data)
                    
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to files"""
        try:
            # Save business profile
            profile_path = os.path.join(self.config_dir, "business_profile.json")
            with open(profile_path, 'w') as f:
                json.dump(asdict(self.business_profile), f, indent=2)
            
            # Save appearance settings
            appearance_path = os.path.join(self.config_dir, "appearance.json")
            with open(appearance_path, 'w') as f:
                json.dump(asdict(self.appearance), f, indent=2)
            
            # Save security settings
            security_path = os.path.join(self.config_dir, "security.json")
            with open(security_path, 'w') as f:
                json.dump(asdict(self.security), f, indent=2)
            
            # Save integration settings
            integration_path = os.path.join(self.config_dir, "integration.json")
            with open(integration_path, 'w') as f:
                json.dump(asdict(self.integration), f, indent=2)
            
            # Save Tailor Pack settings
            packs_path = os.path.join(self.config_dir, "tailor_packs.json")
            with open(packs_path, 'w') as f:
                json.dump(asdict(self.tailor_packs), f, indent=2)
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_first_run_wizard_needed(self) -> bool:
        """Check if first-run wizard is needed"""
        return not self.business_profile.business_name
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a backup file"""
        try:
            config_data = {
                "business_profile": asdict(self.business_profile),
                "appearance": asdict(self.appearance),
                "security": asdict(self.security),
                "integration": asdict(self.integration),
                "tailor_packs": asdict(self.tailor_packs)
            }
            
            with open(export_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a backup file"""
        try:
            with open(import_path, 'r') as f:
                config_data = json.load(f)
            
            # Restore settings
            if "business_profile" in config_data:
                self.business_profile = BusinessProfile(**config_data["business_profile"])
            if "appearance" in config_data:
                self.appearance = AppearanceSettings(**config_data["appearance"])
            if "security" in config_data:
                self.security = SecuritySettings(**config_data["security"])
            if "integration" in config_data:
                self.integration = IntegrationSettings(**config_data["integration"])
            if "tailor_packs" in config_data:
                self.tailor_packs = TailorPackSettings(**config_data["tailor_packs"])
            
            # Save imported settings
            self.save_config()
            return True
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False


class SettingsWindow(QMainWindow):
    """Business-focused settings window"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.config = EntrepreneurConfig()
        self.init_ui()
        
        # Check if first-run wizard is needed
        if self.config.get_first_run_wizard_needed():
            self.show_first_run_wizard()
    
    def init_ui(self):
        self.setWindowTitle("Entrepreneur Assistant Settings")
        self.setGeometry(200, 200, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Settings categories list
        self.categories_list = QListWidget()
        self.categories_list.setMaximumWidth(200)
        self.categories_list.addItems([
            "🏢 Business Profile",
            "🎨 Appearance",
            "🔒 Security & Privacy",
            "🔗 Integrations", 
            "📦 Tailor Packs",
            "💾 Backup & Export"
        ])
        self.categories_list.currentRowChanged.connect(self.change_category)
        main_layout.addWidget(self.categories_list)
        
        # Settings content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create settings pages
        self.create_business_profile_page()
        self.create_appearance_page()
        self.create_security_page()
        self.create_integration_page()
        self.create_tailor_packs_page()
        self.create_backup_page()
        
        # Set default category
        self.categories_list.setCurrentRow(0)
    
    def create_business_profile_page(self):
        """Create business profile settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Header
        header = QLabel("Business Profile")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Business information
        self.business_name_edit = QLineEdit(self.config.business_profile.business_name)
        form_layout.addRow("Business Name:", self.business_name_edit)
        
        self.business_type_combo = QComboBox()
        self.business_type_combo.addItems(["entrepreneur", "small_business", "freelancer", "consultant"])
        self.business_type_combo.setCurrentText(self.config.business_profile.business_type)
        form_layout.addRow("Business Type:", self.business_type_combo)
        
        self.industry_edit = QLineEdit(self.config.business_profile.industry)
        form_layout.addRow("Industry:", self.industry_edit)
        
        self.owner_name_edit = QLineEdit(self.config.business_profile.owner_name)
        form_layout.addRow("Owner Name:", self.owner_name_edit)
        
        self.email_edit = QLineEdit(self.config.business_profile.email)
        form_layout.addRow("Email:", self.email_edit)
        
        self.phone_edit = QLineEdit(self.config.business_profile.phone)
        form_layout.addRow("Phone:", self.phone_edit)
        
        self.website_edit = QLineEdit(self.config.business_profile.website)
        form_layout.addRow("Website:", self.website_edit)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Profile")
        save_btn.clicked.connect(self.save_business_profile)
        layout.addWidget(save_btn)
        
        self.content_stack.addWidget(page)
    
    def create_appearance_page(self):
        """Create appearance settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Appearance & Interface")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_dark = QRadioButton("Dark Theme (Recommended for Business)")
        self.theme_light = QRadioButton("Light Theme")
        self.theme_auto = QRadioButton("Auto (Follow System)")
        
        theme_layout.addWidget(self.theme_dark)
        theme_layout.addWidget(self.theme_light)
        theme_layout.addWidget(self.theme_auto)
        
        # Set current theme
        theme_map = {"dark": self.theme_dark, "light": self.theme_light, "auto": self.theme_auto}
        theme_map.get(self.config.appearance.theme, self.theme_dark).setChecked(True)
        
        layout.addWidget(theme_group)
        
        # UI options
        ui_group = QGroupBox("Interface Options")
        ui_layout = QVBoxLayout(ui_group)
        
        self.compact_mode_check = QCheckBox("Compact Mode (More features visible)")
        self.compact_mode_check.setChecked(self.config.appearance.compact_mode)
        ui_layout.addWidget(self.compact_mode_check)
        
        self.tooltips_check = QCheckBox("Show Tooltips")
        self.tooltips_check.setChecked(self.config.appearance.show_tooltips)
        ui_layout.addWidget(self.tooltips_check)
        
        layout.addWidget(ui_group)
        
        # Startup options
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.startup_dashboard_combo = QComboBox()
        self.startup_dashboard_combo.addItems(["business", "tasks", "dashboard"])
        self.startup_dashboard_combo.setCurrentText(self.config.appearance.startup_dashboard)
        startup_layout.addRow("Default View:", self.startup_dashboard_combo)
        
        layout.addWidget(startup_group)
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Appearance")
        save_btn.clicked.connect(self.save_appearance)
        layout.addWidget(save_btn)
        
        self.content_stack.addWidget(page)
    
    def create_security_page(self):
        """Create security settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Security & Privacy")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Security options
        security_group = QGroupBox("Security Options")
        security_layout = QFormLayout(security_group)
        
        self.auto_lock_spin = QSpinBox()
        self.auto_lock_spin.setRange(5, 120)
        self.auto_lock_spin.setValue(self.config.security.auto_lock_minutes)
        self.auto_lock_spin.setSuffix(" minutes")
        security_layout.addRow("Auto-lock after:", self.auto_lock_spin)
        
        self.require_password_check = QCheckBox("Require password for sensitive operations")
        self.require_password_check.setChecked(self.config.security.require_password_for_sensitive)
        security_layout.addRow("", self.require_password_check)
        
        self.encrypted_storage_check = QCheckBox("Encrypt local data storage")
        self.encrypted_storage_check.setChecked(self.config.security.encrypted_storage)
        security_layout.addRow("", self.encrypted_storage_check)
        
        layout.addWidget(security_group)
        
        # Backup options
        backup_group = QGroupBox("Data Backup")
        backup_layout = QFormLayout(backup_group)
        
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["never", "daily", "weekly"])
        self.backup_frequency_combo.setCurrentText(self.config.security.backup_frequency)
        backup_layout.addRow("Backup Frequency:", self.backup_frequency_combo)
        
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(30, 3650)
        self.retention_spin.setValue(self.config.security.data_retention_days)
        self.retention_spin.setSuffix(" days")
        backup_layout.addRow("Keep data for:", self.retention_spin)
        
        layout.addWidget(backup_group)
        layout.addStretch()
        
        save_btn = QPushButton("💾 Save Security Settings")
        save_btn.clicked.connect(self.save_security)
        layout.addWidget(save_btn)
        
        self.content_stack.addWidget(page)
    
    def create_integration_page(self):
        """Create integration settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Third-party Integrations")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Integration options
        integrations_group = QGroupBox("Sync Options")
        integrations_layout = QVBoxLayout(integrations_group)
        
        self.email_sync_check = QCheckBox("Enable email synchronization")
        self.email_sync_check.setChecked(self.config.integration.email_sync_enabled)
        integrations_layout.addWidget(self.email_sync_check)
        
        self.calendar_sync_check = QCheckBox("Enable calendar synchronization")
        self.calendar_sync_check.setChecked(self.config.integration.calendar_sync_enabled)
        integrations_layout.addWidget(self.calendar_sync_check)
        
        self.cloud_backup_check = QCheckBox("Enable cloud backup")
        self.cloud_backup_check.setChecked(self.config.integration.cloud_backup_enabled)
        integrations_layout.addWidget(self.cloud_backup_check)
        
        layout.addWidget(integrations_group)
        
        # API options
        api_group = QGroupBox("API Settings")
        api_layout = QVBoxLayout(api_group)
        
        self.rate_limiting_check = QCheckBox("Enable API rate limiting")
        self.rate_limiting_check.setChecked(self.config.integration.api_rate_limiting)
        api_layout.addWidget(self.rate_limiting_check)
        
        self.offline_mode_check = QCheckBox("Offline mode (reduce external API calls)")
        self.offline_mode_check.setChecked(self.config.integration.offline_mode)
        api_layout.addWidget(self.offline_mode_check)
        
        layout.addWidget(api_group)
        layout.addStretch()
        
        save_btn = QPushButton("💾 Save Integration Settings")
        save_btn.clicked.connect(self.save_integration)
        layout.addWidget(save_btn)
        
        self.content_stack.addWidget(page)
    
    def create_tailor_packs_page(self):
        """Create Tailor Pack settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Tailor Pack Settings")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Tailor Pack options
        packs_group = QGroupBox("Pack Management")
        packs_layout = QVBoxLayout(packs_group)
        
        self.auto_update_check = QCheckBox("Automatically update installed packs")
        self.auto_update_check.setChecked(self.config.tailor_packs.auto_update_packs)
        packs_layout.addWidget(self.auto_update_check)
        
        self.unsigned_packs_check = QCheckBox("Allow unsigned packs (Not recommended)")
        self.unsigned_packs_check.setChecked(self.config.tailor_packs.allow_unsigned_packs)
        packs_layout.addWidget(self.unsigned_packs_check)
        
        self.pack_isolation_check = QCheckBox("Enable pack data isolation")
        self.pack_isolation_check.setChecked(self.config.tailor_packs.pack_data_isolation)
        packs_layout.addWidget(self.pack_isolation_check)
        
        self.marketplace_check = QCheckBox("Enable Tailor Pack Marketplace")
        self.marketplace_check.setChecked(self.config.tailor_packs.marketplace_enabled)
        packs_layout.addWidget(self.marketplace_check)
        
        self.trial_mode_check = QCheckBox("Enable trial mode for paid packs")
        self.trial_mode_check.setChecked(self.config.tailor_packs.trial_mode_enabled)
        packs_layout.addWidget(self.trial_mode_check)
        
        layout.addWidget(packs_group)
        layout.addStretch()
        
        save_btn = QPushButton("💾 Save Tailor Pack Settings")
        save_btn.clicked.connect(self.save_tailor_packs)
        layout.addWidget(save_btn)
        
        self.content_stack.addWidget(page)
    
    def create_backup_page(self):
        """Create backup and export page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Backup & Export")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Export section
        export_group = QGroupBox("Export Configuration")
        export_layout = QVBoxLayout(export_group)
        
        export_btn = QPushButton("📤 Export Settings")
        export_btn.clicked.connect(self.export_settings)
        export_layout.addWidget(export_btn)
        
        import_btn = QPushButton("📥 Import Settings")
        import_btn.clicked.connect(self.import_settings)
        export_layout.addWidget(import_btn)
        
        layout.addWidget(export_group)
        
        # Reset section
        reset_group = QGroupBox("Reset")
        reset_layout = QVBoxLayout(reset_group)
        
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        reset_layout.addWidget(reset_btn)
        
        layout.addWidget(reset_group)
        layout.addStretch()
        
        self.content_stack.addWidget(page)
    
    def change_category(self, index):
        """Change the displayed settings category"""
        self.content_stack.setCurrentIndex(index)
    
    def save_business_profile(self):
        """Save business profile settings"""
        self.config.business_profile.business_name = self.business_name_edit.text()
        self.config.business_profile.business_type = self.business_type_combo.currentText()
        self.config.business_profile.industry = self.industry_edit.text()
        self.config.business_profile.owner_name = self.owner_name_edit.text()
        self.config.business_profile.email = self.email_edit.text()
        self.config.business_profile.phone = self.phone_edit.text()
        self.config.business_profile.website = self.website_edit.text()
        
        self.config.save_config()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Business profile saved successfully!")
    
    def save_appearance(self):
        """Save appearance settings"""
        if self.theme_dark.isChecked():
            self.config.appearance.theme = "dark"
        elif self.theme_light.isChecked():
            self.config.appearance.theme = "light"
        else:
            self.config.appearance.theme = "auto"
        
        self.config.appearance.compact_mode = self.compact_mode_check.isChecked()
        self.config.appearance.show_tooltips = self.tooltips_check.isChecked()
        self.config.appearance.startup_dashboard = self.startup_dashboard_combo.currentText()
        
        self.config.save_config()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Appearance settings saved successfully!")
    
    def save_security(self):
        """Save security settings"""
        self.config.security.auto_lock_minutes = self.auto_lock_spin.value()
        self.config.security.require_password_for_sensitive = self.require_password_check.isChecked()
        self.config.security.encrypted_storage = self.encrypted_storage_check.isChecked()
        self.config.security.backup_frequency = self.backup_frequency_combo.currentText()
        self.config.security.data_retention_days = self.retention_spin.value()
        
        self.config.save_config()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Security settings saved successfully!")
    
    def save_integration(self):
        """Save integration settings"""
        self.config.integration.email_sync_enabled = self.email_sync_check.isChecked()
        self.config.integration.calendar_sync_enabled = self.calendar_sync_check.isChecked()
        self.config.integration.cloud_backup_enabled = self.cloud_backup_check.isChecked()
        self.config.integration.api_rate_limiting = self.rate_limiting_check.isChecked()
        self.config.integration.offline_mode = self.offline_mode_check.isChecked()
        
        self.config.save_config()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Integration settings saved successfully!")
    
    def save_tailor_packs(self):
        """Save Tailor Pack settings"""
        self.config.tailor_packs.auto_update_packs = self.auto_update_check.isChecked()
        self.config.tailor_packs.allow_unsigned_packs = self.unsigned_packs_check.isChecked()
        self.config.tailor_packs.pack_data_isolation = self.pack_isolation_check.isChecked()
        self.config.tailor_packs.marketplace_enabled = self.marketplace_check.isChecked()
        self.config.tailor_packs.trial_mode_enabled = self.trial_mode_check.isChecked()
        
        self.config.save_config()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Tailor Pack settings saved successfully!")
    
    def export_settings(self):
        """Export all settings to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "entrepreneur_assistant_config.json", "JSON files (*.json)"
        )
        
        if file_path:
            if self.config.export_config(file_path):
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to export settings.")
    
    def import_settings(self):
        """Import settings from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON files (*.json)"
        )
        
        if file_path:
            if self.config.import_config(file_path):
                QMessageBox.information(self, "Success", "Settings imported successfully! Please restart the application.")
                self.settings_changed.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to import settings.")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self.config.business_profile = BusinessProfile()
            self.config.appearance = AppearanceSettings()
            self.config.security = SecuritySettings()
            self.config.integration = IntegrationSettings()
            self.config.tailor_packs = TailorPackSettings()
            
            self.config.save_config()
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Reset", "Settings reset to defaults! Please restart the application.")
    
    def show_first_run_wizard(self):
        """Show first-run wizard for new users"""
        wizard = FirstRunWizard(self.config)
        if wizard.exec_() == QDialog.Accepted:
            self.config.save_config()
            self.settings_changed.emit()


class FirstRunWizard(QDialog):
    """First-run wizard for setting up business profile"""
    
    def __init__(self, config: EntrepreneurConfig):
        super().__init__()
        self.config = config
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Welcome to Entrepreneur Assistant")
        self.setGeometry(300, 300, 600, 400)
        
        layout = QVBoxLayout(self)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Entrepreneur Assistant!")
        welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        subtitle_label = QLabel("Let's set up your business profile to get started.")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Business setup form
        form_layout = QFormLayout()
        
        self.business_name_edit = QLineEdit()
        form_layout.addRow("Business Name:", self.business_name_edit)
        
        self.business_type_combo = QComboBox()
        self.business_type_combo.addItems(["entrepreneur", "small_business", "freelancer", "consultant"])
        form_layout.addRow("Business Type:", self.business_type_combo)
        
        self.owner_name_edit = QLineEdit()
        form_layout.addRow("Your Name:", self.owner_name_edit)
        
        self.email_edit = QLineEdit()
        form_layout.addRow("Email:", self.email_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        skip_btn = QPushButton("Skip for Now")
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)
        
        button_layout.addStretch()
        
        setup_btn = QPushButton("Complete Setup")
        setup_btn.clicked.connect(self.complete_setup)
        setup_btn.setDefault(True)
        button_layout.addWidget(setup_btn)
        
        layout.addLayout(button_layout)
    
    def complete_setup(self):
        """Complete the initial setup"""
        if not self.business_name_edit.text().strip():
            QMessageBox.warning(self, "Required", "Please enter your business name.")
            return
        
        # Update config
        self.config.business_profile.business_name = self.business_name_edit.text()
        self.config.business_profile.business_type = self.business_type_combo.currentText()
        self.config.business_profile.owner_name = self.owner_name_edit.text()
        self.config.business_profile.email = self.email_edit.text()
        
        self.accept()


# Global config instance
_entrepreneur_config = None

def get_entrepreneur_config() -> EntrepreneurConfig:
    """Get the global entrepreneur configuration instance"""
    global _entrepreneur_config
    if _entrepreneur_config is None:
        _entrepreneur_config = EntrepreneurConfig()
    return _entrepreneur_config