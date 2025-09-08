"""
TailorPack Manager for Entrepreneur Assistant
Extends the existing plugin system to support Tailor Packs - specialized business functionality packages
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
from .marketplace_manager import MarketplaceManager, ExtensionInfo


@dataclass
class TailorPackInfo(ExtensionInfo):
    """Extended information for Tailor Packs"""
    pack_type: str  # 'business', 'industry', 'workflow', 'integration'
    target_audience: str  # 'entrepreneur', 'small_business', 'freelancer'
    business_category: str  # 'marketing', 'sales', 'finance', 'operations'
    license_required: bool = False
    license_key: Optional[str] = None
    trial_period_days: int = 30
    feature_list: List[str] = None
    ui_extensions: List[str] = None
    data_requirements: List[str] = None


@dataclass
class TailorPackManifest:
    """Tailor Pack manifest structure"""
    pack_id: str
    name: str
    version: str
    description: str
    author: str
    target_audience: str
    business_category: str
    license_required: bool
    features: List[str]
    ui_components: List[str]
    dependencies: List[str]
    permissions: List[str]
    min_app_version: str
    data_schema: Dict[str, Any]
    configuration: Dict[str, Any]


class TailorPackManager(MarketplaceManager):
    """
    Manages Tailor Packs for the Entrepreneur Assistant
    Extends the base marketplace manager with business-specific functionality
    """
    
    def __init__(self, packs_dir: str = None, base_app_version: str = "1.0.0"):
        # Initialize with tailor-specific directory structure
        if packs_dir is None:
            packs_dir = os.path.join(os.getcwd(), "tailor_packs")
        
        super().__init__(packs_dir)
        self.base_app_version = base_app_version
        self.installed_packs = {}
        self.active_packs = {}
        self.pack_conflicts = {}
        self.license_validator = None
        
        # Create directory structure
        self._create_directory_structure()
        
        # Load installed packs
        self._load_installed_packs()
    
    def _create_directory_structure(self):
        """Create the Tailor Pack directory structure"""
        dirs = [
            'installed',
            'cache',
            'licenses',
            'data',
            'backups',
            'temp'
        ]
        
        for dir_name in dirs:
            os.makedirs(os.path.join(self.extensions_dir, dir_name), exist_ok=True)
    
    def _load_installed_packs(self):
        """Load information about installed Tailor Packs"""
        installed_dir = os.path.join(self.extensions_dir, 'installed')
        
        for pack_dir in os.listdir(installed_dir):
            pack_path = os.path.join(installed_dir, pack_dir)
            if os.path.isdir(pack_path):
                manifest_path = os.path.join(pack_path, 'manifest.json')
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest_data = json.load(f)
                        
                        pack_info = TailorPackInfo(
                            id=manifest_data['pack_id'],
                            name=manifest_data['name'],
                            version=manifest_data['version'],
                            description=manifest_data['description'],
                            author=manifest_data['author'],
                            category=manifest_data['business_category'],
                            tags=manifest_data.get('features', []),
                            file_size=self._get_directory_size(pack_path),
                            checksum=self._calculate_pack_checksum(pack_path),
                            signature=None,  # TODO: Implement digital signatures
                            install_date=datetime.fromtimestamp(os.path.getctime(pack_path)),
                            enabled=self._is_pack_enabled(manifest_data['pack_id']),
                            dependencies=manifest_data.get('dependencies', []),
                            permissions=manifest_data.get('permissions', []),
                            rating=0.0,  # TODO: Implement rating system
                            download_count=0,
                            pack_type=manifest_data.get('pack_type', 'business'),
                            target_audience=manifest_data['target_audience'],
                            business_category=manifest_data['business_category'],
                            license_required=manifest_data.get('license_required', False),
                            feature_list=manifest_data.get('features', []),
                            ui_extensions=manifest_data.get('ui_components', []),
                            data_requirements=manifest_data.get('data_requirements', [])
                        )
                        
                        self.installed_packs[pack_info.id] = pack_info
                        
                    except Exception as e:
                        print(f"Error loading pack {pack_dir}: {e}")
    
    def import_tailor_pack(self, zip_path: str) -> Dict[str, Any]:
        """Import a Tailor Pack from a ZIP file"""
        try:
            # Validate ZIP file
            if not zipfile.is_zipfile(zip_path):
                return {"success": False, "error": "Invalid ZIP file"}
            
            # Extract to temporary directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Validate manifest
                manifest_path = os.path.join(temp_dir, 'manifest.json')
                if not os.path.exists(manifest_path):
                    return {"success": False, "error": "Missing manifest.json"}
                
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Validate manifest structure
                validation_result = self._validate_manifest(manifest)
                if not validation_result["valid"]:
                    return {"success": False, "error": validation_result["error"]}
                
                # Check for conflicts
                conflicts = self._check_pack_conflicts(manifest)
                if conflicts:
                    return {"success": False, "error": f"Conflicts detected: {conflicts}"}
                
                # Check dependencies
                missing_deps = self._check_dependencies(manifest.get('dependencies', []))
                if missing_deps:
                    return {"success": False, "error": f"Missing dependencies: {missing_deps}"}
                
                # Install the pack
                pack_id = manifest['pack_id']
                install_dir = os.path.join(self.extensions_dir, 'installed', pack_id)
                
                # Remove existing installation if present
                if os.path.exists(install_dir):
                    shutil.rmtree(install_dir)
                
                # Copy pack to installation directory
                shutil.copytree(temp_dir, install_dir)
                
                # Update installed packs registry
                self._load_installed_packs()
                
                return {
                    "success": True, 
                    "pack_id": pack_id,
                    "message": f"Successfully imported {manifest['name']}"
                }
                
            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            return {"success": False, "error": f"Import failed: {str(e)}"}
    
    def _validate_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Tailor Pack manifest structure"""
        required_fields = [
            'pack_id', 'name', 'version', 'description', 'author',
            'target_audience', 'business_category', 'features'
        ]
        
        for field in required_fields:
            if field not in manifest:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate version compatibility
        if 'min_app_version' in manifest:
            if not self._is_version_compatible(manifest['min_app_version']):
                return {"valid": False, "error": "Incompatible application version"}
        
        return {"valid": True}
    
    def _check_pack_conflicts(self, manifest: Dict[str, Any]) -> List[str]:
        """Check for conflicts with installed packs"""
        conflicts = []
        pack_id = manifest['pack_id']
        
        # Check for ID conflicts
        if pack_id in self.installed_packs:
            conflicts.append(f"Pack ID {pack_id} already exists")
        
        # Check for feature conflicts
        new_features = set(manifest.get('features', []))
        for installed_pack in self.installed_packs.values():
            if installed_pack.enabled:
                existing_features = set(installed_pack.feature_list or [])
                feature_overlap = new_features.intersection(existing_features)
                if feature_overlap:
                    conflicts.append(f"Feature conflict with {installed_pack.name}: {feature_overlap}")
        
        return conflicts
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check for missing dependencies"""
        missing = []
        
        for dep in dependencies:
            if dep not in self.installed_packs:
                missing.append(dep)
            elif not self.installed_packs[dep].enabled:
                missing.append(f"{dep} (disabled)")
        
        return missing
    
    def _is_version_compatible(self, min_version: str) -> bool:
        """Check if the minimum version requirement is met"""
        # Simple version comparison (assumes semantic versioning)
        try:
            min_parts = [int(x) for x in min_version.split('.')]
            current_parts = [int(x) for x in self.base_app_version.split('.')]
            
            for i in range(max(len(min_parts), len(current_parts))):
                min_part = min_parts[i] if i < len(min_parts) else 0
                current_part = current_parts[i] if i < len(current_parts) else 0
                
                if current_part > min_part:
                    return True
                elif current_part < min_part:
                    return False
            
            return True
        except:
            return False
    
    def enable_pack(self, pack_id: str) -> Dict[str, Any]:
        """Enable a Tailor Pack"""
        if pack_id not in self.installed_packs:
            return {"success": False, "error": "Pack not installed"}
        
        pack = self.installed_packs[pack_id]
        
        # Check license if required
        if pack.license_required and not self._validate_license(pack_id):
            return {"success": False, "error": "Valid license required"}
        
        # Check dependencies
        missing_deps = self._check_dependencies(pack.dependencies)
        if missing_deps:
            return {"success": False, "error": f"Missing dependencies: {missing_deps}"}
        
        # Enable the pack
        pack.enabled = True
        self.active_packs[pack_id] = pack
        
        # Save state
        self._save_pack_state()
        
        return {"success": True, "message": f"Enabled {pack.name}"}
    
    def disable_pack(self, pack_id: str) -> Dict[str, Any]:
        """Disable a Tailor Pack"""
        if pack_id not in self.installed_packs:
            return {"success": False, "error": "Pack not installed"}
        
        pack = self.installed_packs[pack_id]
        pack.enabled = False
        
        if pack_id in self.active_packs:
            del self.active_packs[pack_id]
        
        # Save state
        self._save_pack_state()
        
        return {"success": True, "message": f"Disabled {pack.name}"}
    
    def get_pack_configuration(self, pack_id: str) -> Dict[str, Any]:
        """Get configuration for a specific pack"""
        if pack_id not in self.installed_packs:
            return {}
        
        config_path = os.path.join(self.extensions_dir, 'installed', pack_id, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    def update_pack_configuration(self, pack_id: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific pack"""
        if pack_id not in self.installed_packs:
            return False
        
        config_path = os.path.join(self.extensions_dir, 'installed', pack_id, 'config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except:
            return False
    
    def _validate_license(self, pack_id: str) -> bool:
        """Validate license for a pack"""
        # TODO: Implement license validation
        return True
    
    def _is_pack_enabled(self, pack_id: str) -> bool:
        """Check if a pack is enabled"""
        state_path = os.path.join(self.extensions_dir, 'pack_state.json')
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
            return state.get(pack_id, {}).get('enabled', False)
        return False
    
    def _save_pack_state(self):
        """Save the current pack state"""
        state = {}
        for pack_id, pack in self.installed_packs.items():
            state[pack_id] = {
                'enabled': pack.enabled,
                'last_updated': datetime.now().isoformat()
            }
        
        state_path = os.path.join(self.extensions_dir, 'pack_state.json')
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of directory"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total
    
    def _calculate_pack_checksum(self, pack_path: str) -> str:
        """Calculate checksum for pack integrity verification"""
        hasher = hashlib.sha256()
        
        for root, dirs, files in os.walk(pack_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def get_installed_packs(self) -> List[TailorPackInfo]:
        """Get list of all installed Tailor Packs"""
        return list(self.installed_packs.values())
    
    def get_active_packs(self) -> List[TailorPackInfo]:
        """Get list of currently active Tailor Packs"""
        return list(self.active_packs.values())


# Global instance
_tailor_pack_manager = None

def get_tailor_pack_manager() -> TailorPackManager:
    """Get the global TailorPackManager instance"""
    global _tailor_pack_manager
    if _tailor_pack_manager is None:
        _tailor_pack_manager = TailorPackManager()
    return _tailor_pack_manager