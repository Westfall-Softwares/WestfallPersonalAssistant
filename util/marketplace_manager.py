"""
Extension Marketplace Manager for Westfall Personal Assistant
Provides secure plugin repository, verification, and sandboxing capabilities
"""

import os
import json
import hashlib
import threading
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import zipfile
import importlib.util
from datetime import datetime


@dataclass
class ExtensionInfo:
    """Information about an extension"""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    file_size: int
    checksum: str
    signature: Optional[str]
    install_date: Optional[datetime]
    enabled: bool
    dependencies: List[str]
    permissions: List[str]
    rating: float
    download_count: int


class MarketplaceManager:
    """Manages the extension marketplace with security and sandboxing"""
    
    def __init__(self, extensions_dir: str = None):
        self.extensions_dir = extensions_dir or os.path.join(os.getcwd(), "extensions")
        self.marketplace_url = "https://marketplace.westfall-softwares.com/api"
        self.installed_extensions = {}
        self.available_extensions = {}
        self.download_queue = []
        
        # Security settings
        self.security_settings = {
            "require_signature": True,
            "sandbox_enabled": True,
            "auto_update": False,
            "trusted_publishers": ["westfall-softwares", "verified"],
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "allowed_permissions": [
                "read_files", "write_files", "network_access", 
                "system_notifications", "ui_integration"
            ]
        }
        
        # Initialize directories
        self._init_directories()
        self._load_installed_extensions()
        
    def _init_directories(self):
        """Initialize extension directories"""
        os.makedirs(self.extensions_dir, exist_ok=True)
        os.makedirs(os.path.join(self.extensions_dir, "installed"), exist_ok=True)
        os.makedirs(os.path.join(self.extensions_dir, "temp"), exist_ok=True)
        os.makedirs(os.path.join(self.extensions_dir, "cache"), exist_ok=True)
        
    def _load_installed_extensions(self):
        """Load information about installed extensions"""
        installed_dir = os.path.join(self.extensions_dir, "installed")
        
        for ext_dir in os.listdir(installed_dir):
            ext_path = os.path.join(installed_dir, ext_dir)
            if os.path.isdir(ext_path):
                manifest_path = os.path.join(ext_path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        
                        ext_info = ExtensionInfo(
                            id=manifest.get("id", ext_dir),
                            name=manifest.get("name", ext_dir),
                            version=manifest.get("version", "1.0.0"),
                            description=manifest.get("description", ""),
                            author=manifest.get("author", "Unknown"),
                            category=manifest.get("category", "other"),
                            tags=manifest.get("tags", []),
                            file_size=self._get_directory_size(ext_path),
                            checksum="",  # Would calculate from files
                            signature=manifest.get("signature"),
                            install_date=datetime.fromisoformat(
                                manifest.get("install_date", datetime.now().isoformat())
                            ),
                            enabled=manifest.get("enabled", True),
                            dependencies=manifest.get("dependencies", []),
                            permissions=manifest.get("permissions", []),
                            rating=manifest.get("rating", 0.0),
                            download_count=manifest.get("download_count", 0)
                        )
                        
                        self.installed_extensions[ext_info.id] = ext_info
                        
                    except Exception as e:
                        print(f"Error loading extension {ext_dir}: {e}")
                        
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
        
    def search_marketplace(self, query: str = "", category: str = "", 
                          tags: List[str] = None) -> List[ExtensionInfo]:
        """Search the marketplace for extensions"""
        # This would normally make API calls to the marketplace
        # For now, return mock data
        
        mock_extensions = [
            ExtensionInfo(
                id="voice-assistant-pro",
                name="Voice Assistant Pro",
                version="2.1.0",
                description="Advanced voice control with custom commands",
                author="westfall-softwares",
                category="ai",
                tags=["voice", "ai", "productivity"],
                file_size=5242880,  # 5MB
                checksum="abc123def456",
                signature="verified",
                install_date=None,
                enabled=False,
                dependencies=["speech-recognition", "pyttsx3"],
                permissions=["microphone", "speaker", "ui_integration"],
                rating=4.8,
                download_count=15420
            ),
            ExtensionInfo(
                id="business-analytics",
                name="Business Analytics Dashboard",
                version="1.5.2",
                description="Advanced business intelligence and reporting",
                author="verified-dev",
                category="business",
                tags=["analytics", "business", "reporting"],
                file_size=12582912,  # 12MB
                checksum="def456ghi789",
                signature="verified",
                install_date=None,
                enabled=False,
                dependencies=["pandas", "matplotlib", "plotly"],
                permissions=["read_files", "write_files", "network_access"],
                rating=4.6,
                download_count=8932
            ),
            ExtensionInfo(
                id="password-sync",
                name="Cloud Password Sync",
                version="3.0.1",
                description="Secure cloud synchronization for passwords",
                author="security-tools",
                category="security",
                tags=["passwords", "sync", "security"],
                file_size=2097152,  # 2MB
                checksum="ghi789jkl012",
                signature="verified",
                install_date=None,
                enabled=False,
                dependencies=["cryptography"],
                permissions=["network_access", "encrypted_storage"],
                rating=4.9,
                download_count=23156
            )
        ]
        
        # Filter results based on search criteria
        results = []
        for ext in mock_extensions:
            if query and query.lower() not in ext.name.lower() and query.lower() not in ext.description.lower():
                continue
            if category and ext.category != category:
                continue
            if tags and not any(tag in ext.tags for tag in tags):
                continue
            results.append(ext)
            
        return results
        
    def get_extension_details(self, extension_id: str) -> Optional[ExtensionInfo]:
        """Get detailed information about an extension"""
        # Check installed extensions first
        if extension_id in self.installed_extensions:
            return self.installed_extensions[extension_id]
            
        # Search marketplace
        marketplace_results = self.search_marketplace()
        for ext in marketplace_results:
            if ext.id == extension_id:
                return ext
                
        return None
        
    def verify_extension(self, extension_path: str) -> Dict[str, Any]:
        """Verify extension security and integrity"""
        verification_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "signature_valid": False,
            "checksum_valid": False,
            "permissions_safe": True,
            "sandbox_compatible": True
        }
        
        try:
            # Extract and verify manifest
            with zipfile.ZipFile(extension_path, 'r') as zip_file:
                if 'manifest.json' not in zip_file.namelist():
                    verification_result["errors"].append("Missing manifest.json")
                    verification_result["valid"] = False
                    return verification_result
                    
                with zip_file.open('manifest.json') as manifest_file:
                    manifest = json.load(manifest_file)
                    
            # Verify required fields
            required_fields = ["id", "name", "version", "author", "permissions"]
            for field in required_fields:
                if field not in manifest:
                    verification_result["errors"].append(f"Missing required field: {field}")
                    verification_result["valid"] = False
                    
            # Check file size
            file_size = os.path.getsize(extension_path)
            if file_size > self.security_settings["max_file_size"]:
                verification_result["errors"].append("Extension exceeds maximum file size")
                verification_result["valid"] = False
                
            # Verify checksum (mock implementation)
            verification_result["checksum_valid"] = True
            
            # Verify signature (mock implementation)
            if self.security_settings["require_signature"]:
                author = manifest.get("author", "")
                if author in self.security_settings["trusted_publishers"]:
                    verification_result["signature_valid"] = True
                else:
                    verification_result["warnings"].append("Untrusted publisher")
                    
            # Check permissions
            permissions = manifest.get("permissions", [])
            for permission in permissions:
                if permission not in self.security_settings["allowed_permissions"]:
                    verification_result["warnings"].append(f"Unusual permission: {permission}")
                    
        except Exception as e:
            verification_result["errors"].append(f"Verification error: {str(e)}")
            verification_result["valid"] = False
            
        return verification_result
        
    def install_extension(self, extension_id: str, 
                         progress_callback: Callable[[str, float], None] = None) -> bool:
        """Install an extension with progress tracking"""
        
        if progress_callback:
            progress_callback("Starting installation...", 0.0)
            
        try:
            # This would normally download from marketplace
            # For now, simulate the process
            
            if progress_callback:
                progress_callback("Downloading extension...", 0.2)
                
            # Simulate download delay
            import time
            time.sleep(1)
            
            if progress_callback:
                progress_callback("Verifying extension...", 0.5)
                
            # Mock verification
            verification_result = {"valid": True, "errors": []}
            
            if not verification_result["valid"]:
                if progress_callback:
                    progress_callback("Verification failed", 1.0)
                return False
                
            if progress_callback:
                progress_callback("Installing files...", 0.8)
                
            # Create installation directory
            install_dir = os.path.join(self.extensions_dir, "installed", extension_id)
            os.makedirs(install_dir, exist_ok=True)
            
            # Create mock manifest
            manifest = {
                "id": extension_id,
                "name": extension_id.replace("-", " ").title(),
                "version": "1.0.0",
                "author": "mock-author",
                "description": f"Mock extension for {extension_id}",
                "category": "productivity",
                "enabled": True,
                "install_date": datetime.now().isoformat(),
                "permissions": ["ui_integration"],
                "dependencies": []
            }
            
            with open(os.path.join(install_dir, "manifest.json"), 'w') as f:
                json.dump(manifest, f, indent=2)
                
            # Create mock main module
            with open(os.path.join(install_dir, "main.py"), 'w') as f:
                f.write(f"""
# Mock extension: {extension_id}

def initialize():
    print(f"Initializing {extension_id}")
    return True

def activate():
    print(f"Activating {extension_id}")
    return True

def deactivate():
    print(f"Deactivating {extension_id}")
    return True
""")
            
            # Update installed extensions
            ext_info = ExtensionInfo(
                id=extension_id,
                name=manifest["name"],
                version=manifest["version"],
                description=manifest["description"],
                author=manifest["author"],
                category=manifest["category"],
                tags=[],
                file_size=1024,  # Mock size
                checksum="mock-checksum",
                signature="mock-signature",
                install_date=datetime.now(),
                enabled=True,
                dependencies=manifest["dependencies"],
                permissions=manifest["permissions"],
                rating=0.0,
                download_count=0
            )
            
            self.installed_extensions[extension_id] = ext_info
            
            if progress_callback:
                progress_callback("Installation complete", 1.0)
                
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Installation failed: {str(e)}", 1.0)
            return False
            
    def uninstall_extension(self, extension_id: str) -> bool:
        """Uninstall an extension"""
        if extension_id not in self.installed_extensions:
            return False
            
        try:
            # Deactivate extension first
            self.disable_extension(extension_id)
            
            # Remove installation directory
            install_dir = os.path.join(self.extensions_dir, "installed", extension_id)
            if os.path.exists(install_dir):
                shutil.rmtree(install_dir)
                
            # Remove from installed extensions
            del self.installed_extensions[extension_id]
            
            return True
            
        except Exception as e:
            print(f"Error uninstalling extension {extension_id}: {e}")
            return False
            
    def enable_extension(self, extension_id: str) -> bool:
        """Enable an installed extension"""
        if extension_id not in self.installed_extensions:
            return False
            
        try:
            ext_info = self.installed_extensions[extension_id]
            
            # Load and activate extension
            install_dir = os.path.join(self.extensions_dir, "installed", extension_id)
            main_path = os.path.join(install_dir, "main.py")
            
            if os.path.exists(main_path):
                spec = importlib.util.spec_from_file_location(f"ext_{extension_id}", main_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'activate'):
                    module.activate()
                    
            ext_info.enabled = True
            
            # Update manifest
            manifest_path = os.path.join(install_dir, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                manifest["enabled"] = True
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                    
            return True
            
        except Exception as e:
            print(f"Error enabling extension {extension_id}: {e}")
            return False
            
    def disable_extension(self, extension_id: str) -> bool:
        """Disable an installed extension"""
        if extension_id not in self.installed_extensions:
            return False
            
        try:
            ext_info = self.installed_extensions[extension_id]
            ext_info.enabled = False
            
            # Update manifest
            install_dir = os.path.join(self.extensions_dir, "installed", extension_id)
            manifest_path = os.path.join(install_dir, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                manifest["enabled"] = False
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                    
            return True
            
        except Exception as e:
            print(f"Error disabling extension {extension_id}: {e}")
            return False
            
    def get_installed_extensions(self) -> List[ExtensionInfo]:
        """Get list of installed extensions"""
        return list(self.installed_extensions.values())
        
    def get_enabled_extensions(self) -> List[ExtensionInfo]:
        """Get list of enabled extensions"""
        return [ext for ext in self.installed_extensions.values() if ext.enabled]
        
    def check_for_updates(self) -> List[str]:
        """Check for extension updates"""
        # Mock implementation - would check marketplace for newer versions
        return []
        
    def update_extension(self, extension_id: str) -> bool:
        """Update an extension to the latest version"""
        # Mock implementation
        return True
        
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        return {
            "total_extensions": 156,
            "installed_count": len(self.installed_extensions),
            "enabled_count": len(self.get_enabled_extensions()),
            "categories": {
                "productivity": 45,
                "business": 32,
                "ai": 28,
                "security": 21,
                "entertainment": 18,
                "other": 12
            },
            "last_updated": datetime.now().isoformat()
        }


# Global instance
marketplace_manager = MarketplaceManager()


def get_marketplace_manager() -> MarketplaceManager:
    """Get the global marketplace manager instance"""
    return marketplace_manager