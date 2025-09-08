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
from .licensing_system import get_license_manager
from backend.platform_compatibility import PlatformManager


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
        # Initialize with platform-specific tailor pack directory
        if packs_dir is None:
            platform_manager = PlatformManager()
            app_dirs = platform_manager.setup_application_directories("westfall-assistant")
            packs_dir = str(app_dirs['data'] / "tailor_packs")
        
        super().__init__(packs_dir)
        self.base_app_version = base_app_version
        self.installed_packs = {}
        self.active_packs = {}
        self.pack_conflicts = {}
        self.license_manager = get_license_manager()
        
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
        
        # Check required fields
        for field in required_fields:
            if field not in manifest:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate pack_id format (alphanumeric with hyphens/underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', manifest['pack_id']):
            return {"valid": False, "error": "Invalid pack_id format. Use alphanumeric characters, hyphens, and underscores only"}
        
        # Validate version format (semantic versioning)
        if not re.match(r'^\d+\.\d+\.\d+(-\w+)?$', manifest['version']):
            return {"valid": False, "error": "Invalid version format. Use semantic versioning (e.g., 1.0.0)"}
        
        # Validate target_audience
        valid_audiences = ['entrepreneur', 'small_business', 'freelancer', 'enterprise', 'any']
        if manifest['target_audience'] not in valid_audiences:
            return {"valid": False, "error": f"Invalid target_audience. Must be one of: {valid_audiences}"}
        
        # Validate business_category
        valid_categories = ['marketing', 'sales', 'finance', 'operations', 'legal', 'hr', 'analytics', 'productivity', 'integration', 'other']
        if manifest['business_category'] not in valid_categories:
            return {"valid": False, "error": f"Invalid business_category. Must be one of: {valid_categories}"}
        
        # Validate features list
        if not isinstance(manifest['features'], list) or not manifest['features']:
            return {"valid": False, "error": "Features must be a non-empty list"}
        
        # Validate version compatibility
        if 'min_app_version' in manifest:
            if not self._is_version_compatible(manifest['min_app_version']):
                return {"valid": False, "error": f"Requires application version {manifest['min_app_version']} or higher"}
        
        # Validate platform compatibility if specified
        if 'platform_compatibility' in manifest:
            platform_info = manifest['platform_compatibility']
            if not self._is_platform_compatible(platform_info):
                return {"valid": False, "error": "Pack not compatible with current platform"}
        
        # Validate license information if required
        if manifest.get('license_required', False):
            if 'license_type' not in manifest:
                return {"valid": False, "error": "license_type required when license_required is true"}
        
        return {"valid": True}
    
    def _check_pack_conflicts(self, manifest: Dict[str, Any]) -> List[str]:
        """Check for conflicts with installed packs"""
        conflicts = []
        pack_id = manifest['pack_id']
        
        # Check for ID conflicts
        if pack_id in self.installed_packs:
            existing_pack = self.installed_packs[pack_id]
            conflicts.append(f"Pack ID '{pack_id}' already exists (version {existing_pack.version})")
        
        # Check for name conflicts (similar names)
        new_name = manifest['name'].lower()
        for installed_pack in self.installed_packs.values():
            if installed_pack.name.lower() == new_name:
                conflicts.append(f"Pack name '{manifest['name']}' conflicts with existing pack")
        
        # Check for feature conflicts
        new_features = set(manifest.get('features', []))
        for installed_pack in self.installed_packs.values():
            if installed_pack.enabled:
                existing_features = set(installed_pack.feature_list or [])
                feature_overlap = new_features.intersection(existing_features)
                if feature_overlap:
                    conflicts.append(f"Feature conflict with '{installed_pack.name}': {', '.join(feature_overlap)}")
        
        # Check for UI component conflicts
        new_ui_components = set(manifest.get('ui_components', []))
        for installed_pack in self.installed_packs.values():
            if installed_pack.enabled:
                existing_ui = set(installed_pack.ui_extensions or [])
                ui_overlap = new_ui_components.intersection(existing_ui)
                if ui_overlap:
                    conflicts.append(f"UI component conflict with '{installed_pack.name}': {', '.join(ui_overlap)}")
        
        # Check for API endpoint conflicts
        new_endpoints = set(manifest.get('api_endpoints', []))
        for installed_pack in self.installed_packs.values():
            if installed_pack.enabled and hasattr(installed_pack, 'api_endpoints'):
                existing_endpoints = set(getattr(installed_pack, 'api_endpoints', []))
                endpoint_overlap = new_endpoints.intersection(existing_endpoints)
                if endpoint_overlap:
                    conflicts.append(f"API endpoint conflict with '{installed_pack.name}': {', '.join(endpoint_overlap)}")
        
        return conflicts
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check for missing dependencies"""
        missing = []
        
        for dep in dependencies:
            # Handle version-specific dependencies (e.g., "pack-id@1.0.0")
            if '@' in dep:
                pack_id, required_version = dep.split('@', 1)
            else:
                pack_id = dep
                required_version = None
            
            if pack_id not in self.installed_packs:
                missing.append(dep)
            elif not self.installed_packs[pack_id].enabled:
                missing.append(f"{pack_id} (disabled)")
            elif required_version and not self._is_dependency_version_compatible(pack_id, required_version):
                missing.append(f"{pack_id} (version {required_version} required, have {self.installed_packs[pack_id].version})")
        
        return missing
    
    def _is_dependency_version_compatible(self, pack_id: str, required_version: str) -> bool:
        """Check if installed pack version satisfies dependency requirement"""
        if pack_id not in self.installed_packs:
            return False
        
        installed_version = self.installed_packs[pack_id].version
        
        try:
            # Handle version range specifiers (>=, >, <, <=, =, ^, ~)
            if required_version.startswith('>='):
                return self._compare_versions(installed_version, required_version[2:]) >= 0
            elif required_version.startswith('>'):
                return self._compare_versions(installed_version, required_version[1:]) > 0
            elif required_version.startswith('<='):
                return self._compare_versions(installed_version, required_version[2:]) <= 0
            elif required_version.startswith('<'):
                return self._compare_versions(installed_version, required_version[1:]) < 0
            elif required_version.startswith('^'):
                # Caret range: compatible within same major version
                return self._is_caret_compatible(installed_version, required_version[1:])
            elif required_version.startswith('~'):
                # Tilde range: compatible within same minor version
                return self._is_tilde_compatible(installed_version, required_version[1:])
            else:
                # Exact match
                return installed_version == required_version
        except:
            return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions. Returns -1, 0, or 1"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad with zeros if needed
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    def _is_caret_compatible(self, installed: str, required: str) -> bool:
        """Check if versions are compatible using caret range (^1.2.3)"""
        installed_parts = [int(x) for x in installed.split('.')]
        required_parts = [int(x) for x in required.split('.')]
        
        # Same major version required
        if installed_parts[0] != required_parts[0]:
            return False
        
        # Installed version must be >= required
        return self._compare_versions(installed, required) >= 0
    
    def _is_tilde_compatible(self, installed: str, required: str) -> bool:
        """Check if versions are compatible using tilde range (~1.2.3)"""
        installed_parts = [int(x) for x in installed.split('.')]
        required_parts = [int(x) for x in required.split('.')]
        
        # Same major and minor version required
        if installed_parts[0] != required_parts[0] or installed_parts[1] != required_parts[1]:
            return False
        
        # Installed version must be >= required
        return self._compare_versions(installed, required) >= 0
    
    def resolve_dependencies(self, pack_id: str) -> Dict[str, Any]:
        """Resolve all dependencies for a pack and return installation plan"""
        if pack_id not in self.installed_packs:
            return {"success": False, "error": "Pack not found"}
        
        pack = self.installed_packs[pack_id]
        dependencies = pack.dependencies or []
        
        # Build dependency graph
        resolution_plan = []
        visited = set()
        
        def resolve_recursive(dep_pack_id, dep_list, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return {"success": False, "error": "Circular dependency detected"}
            
            for dep in dep_list:
                if '@' in dep:
                    dep_id, _ = dep.split('@', 1)
                else:
                    dep_id = dep
                
                if dep_id not in visited:
                    visited.add(dep_id)
                    
                    if dep_id not in self.installed_packs:
                        resolution_plan.append({
                            "action": "install",
                            "pack_id": dep_id,
                            "dependency": dep,
                            "required_by": dep_pack_id
                        })
                    else:
                        # Check if dependency's dependencies are resolved
                        dep_pack = self.installed_packs[dep_id]
                        if dep_pack.dependencies:
                            resolve_recursive(dep_id, dep_pack.dependencies, depth + 1)
                        
                        if not dep_pack.enabled:
                            resolution_plan.append({
                                "action": "enable",
                                "pack_id": dep_id,
                                "required_by": dep_pack_id
                            })
        
        resolve_recursive(pack_id, dependencies)
        
        return {
            "success": True,
            "plan": resolution_plan,
            "total_actions": len(resolution_plan)
        }
    
    def _is_platform_compatible(self, platform_info: Dict[str, Any]) -> bool:
        """Check if pack is compatible with current platform"""
        try:
            platform_manager = PlatformManager()
            current_platform = platform_manager.info  # Fixed: use .info instead of .platform_info
            
            # Check supported platforms
            if 'supported_platforms' in platform_info:
                supported = platform_info['supported_platforms']
                current_platform_name = current_platform.platform.value
                if current_platform_name not in supported:
                    return False
            
            # Check architecture requirements
            if 'required_architecture' in platform_info:
                required_arch = platform_info['required_architecture']
                current_arch = current_platform.architecture.value
                if current_arch not in required_arch:
                    return False
            
            # Check platform-specific requirements
            platform_reqs = platform_info.get('platform_requirements', {})
            current_platform_name = current_platform.platform.value
            
            if current_platform_name in platform_reqs:
                reqs = platform_reqs[current_platform_name]
                # Check minimum OS version if specified
                if 'min_version' in reqs:
                    # This would need more sophisticated version comparison
                    # for each platform type
                    pass
            
            return True
        except Exception as e:
            logger.warning(f"Error checking platform compatibility: {e}")
            return True  # Default to compatible if check fails
    
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
        license_check = self.license_manager.check_pack_license(pack_id, require_license=True)
        return license_check.get("allowed", False)
    
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
    
    def export_tailor_pack(self, pack_id: str, export_path: str = None) -> Dict[str, Any]:
        """Export a Tailor Pack to a ZIP file"""
        if pack_id not in self.installed_packs:
            return {"success": False, "error": "Pack not found"}
        
        pack = self.installed_packs[pack_id]
        pack_dir = os.path.join(self.extensions_dir, 'installed', pack_id)
        
        if not os.path.exists(pack_dir):
            return {"success": False, "error": "Pack directory not found"}
        
        # Default export path
        if not export_path:
            export_path = os.path.join(self.extensions_dir, 'exports', f"{pack_id}-{pack.version}.zip")
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add all files from pack directory
                for root, dirs, files in os.walk(pack_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, pack_dir)
                        zip_file.write(file_path, arc_path)
                
                # Add export metadata
                export_metadata = {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": "TailorPackManager",
                    "pack_id": pack_id,
                    "pack_version": pack.version,
                    "pack_name": pack.name,
                    "checksum": self._calculate_pack_checksum(pack_dir)
                }
                
                zip_file.writestr("export_metadata.json", json.dumps(export_metadata, indent=2))
            
            return {
                "success": True,
                "export_path": export_path,
                "pack_name": pack.name,
                "pack_version": pack.version
            }
            
        except Exception as e:
            return {"success": False, "error": f"Export failed: {str(e)}"}
    
    def backup_all_packs(self, backup_path: str = None) -> Dict[str, Any]:
        """Create a backup of all installed packs"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.extensions_dir, 'backups', f"pack_backup_{timestamp}.zip")
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        try:
            backup_manifest = {
                "backup_created": datetime.now().isoformat(),
                "total_packs": len(self.installed_packs),
                "packs": []
            }
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for pack_id, pack in self.installed_packs.items():
                    pack_dir = os.path.join(self.extensions_dir, 'installed', pack_id)
                    
                    if os.path.exists(pack_dir):
                        # Add pack files
                        for root, dirs, files in os.walk(pack_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = os.path.join(pack_id, os.path.relpath(file_path, pack_dir))
                                zip_file.write(file_path, arc_path)
                        
                        # Add pack to manifest
                        backup_manifest["packs"].append({
                            "pack_id": pack_id,
                            "name": pack.name,
                            "version": pack.version,
                            "enabled": pack.enabled,
                            "backup_size": self._get_directory_size(pack_dir)
                        })
                
                # Add backup manifest
                zip_file.writestr("backup_manifest.json", json.dumps(backup_manifest, indent=2))
            
            return {
                "success": True,
                "backup_path": backup_path,
                "total_packs": len(self.installed_packs),
                "backup_size": os.path.getsize(backup_path)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Backup failed: {str(e)}"}
    
    def restore_from_backup(self, backup_path: str) -> Dict[str, Any]:
        """Restore packs from a backup file"""
        if not os.path.exists(backup_path):
            return {"success": False, "error": "Backup file not found"}
        
        try:
            restored_packs = []
            failed_packs = []
            
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                # Read backup manifest
                manifest_content = zip_file.read("backup_manifest.json")
                manifest = json.loads(manifest_content.decode())
                
                for pack_info in manifest["packs"]:
                    pack_id = pack_info["pack_id"]
                    
                    try:
                        # Extract pack to temporary directory
                        temp_dir = tempfile.mkdtemp()
                        
                        # Extract pack files
                        for file_info in zip_file.infolist():
                            if file_info.filename.startswith(f"{pack_id}/"):
                                zip_file.extract(file_info, temp_dir)
                        
                        # Move to installed directory
                        pack_temp_dir = os.path.join(temp_dir, pack_id)
                        pack_install_dir = os.path.join(self.extensions_dir, 'installed', pack_id)
                        
                        if os.path.exists(pack_install_dir):
                            shutil.rmtree(pack_install_dir)
                        
                        shutil.move(pack_temp_dir, pack_install_dir)
                        
                        restored_packs.append(pack_id)
                        
                        # Clean up temp directory
                        shutil.rmtree(temp_dir)
                        
                    except Exception as e:
                        failed_packs.append(f"{pack_id}: {str(e)}")
            
            # Reload installed packs
            self._load_installed_packs()
            
            return {
                "success": True,
                "restored_packs": restored_packs,
                "failed_packs": failed_packs,
                "total_restored": len(restored_packs)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Restore failed: {str(e)}"}
    
    def get_pack_statistics(self) -> Dict[str, Any]:
        """Get statistics about installed Tailor Packs"""
        stats = {
            "total_installed": len(self.installed_packs),
            "total_active": len(self.active_packs),
            "categories": {},
            "target_audiences": {},
            "licensed_packs": 0,
            "total_size": 0
        }
        
        for pack in self.installed_packs.values():
            # Category statistics
            category = pack.business_category
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Target audience statistics
            audience = pack.target_audience
            stats["target_audiences"][audience] = stats["target_audiences"].get(audience, 0) + 1
            
            # License statistics
            if pack.license_required:
                stats["licensed_packs"] += 1
            
            # Size calculation
            pack_dir = os.path.join(self.extensions_dir, 'installed', pack.pack_id)
            if os.path.exists(pack_dir):
                stats["total_size"] += self._get_directory_size(pack_dir)
        
        return stats


# Global instance
_tailor_pack_manager = None

def get_tailor_pack_manager() -> TailorPackManager:
    """Get the global TailorPackManager instance"""
    global _tailor_pack_manager
    if _tailor_pack_manager is None:
        _tailor_pack_manager = TailorPackManager()
    return _tailor_pack_manager