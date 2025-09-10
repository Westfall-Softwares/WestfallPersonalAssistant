#!/usr/bin/env python3
"""
Pack Extension System for Tailor Packs
Provides UI extension points and feature registry capabilities
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pathlib import Path
import importlib.util
import sys
import threading

logger = logging.getLogger(__name__)


@dataclass
class UIExtensionPoint:
    """Defines a UI extension point where packs can add components"""
    name: str
    location: str  # Where in the UI this appears
    component_type: str  # Type of component expected
    max_components: int = 5  # Maximum components allowed
    priority_order: bool = True  # Whether to order by priority
    data_context: Dict[str, Any] = None  # Data available to components


@dataclass
class PackCapability:
    """Represents a capability provided by a pack"""
    pack_id: str
    capability_id: str
    name: str
    description: str
    category: str
    ui_component: Optional[str] = None
    api_endpoints: List[str] = None
    data_requirements: List[str] = None
    permissions: List[str] = None
    priority: int = 100


@dataclass
class UIComponent:
    """Represents a UI component contributed by a pack"""
    pack_id: str
    component_id: str
    extension_point: str
    component_class: str
    priority: int = 100
    config: Dict[str, Any] = None
    enabled: bool = True


class IPackExtension(ABC):
    """Interface for pack extensions"""
    
    @abstractmethod
    def get_ui_components(self) -> List[UIComponent]:
        """Get UI components provided by this extension"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[PackCapability]:
        """Get capabilities provided by this extension"""
        pass
    
    @abstractmethod
    def initialize_extension(self, context: Dict[str, Any]) -> bool:
        """Initialize the extension with application context"""
        pass
    
    @abstractmethod
    def cleanup_extension(self) -> bool:
        """Clean up extension resources"""
        pass


class FeatureRegistry:
    """Registry for pack capabilities and features"""
    
    def __init__(self):
        self.capabilities: Dict[str, PackCapability] = {}
        self.capabilities_by_category: Dict[str, List[PackCapability]] = {}
        self.pack_capabilities: Dict[str, List[PackCapability]] = {}
        self.conflicts: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
    
    def register_capability(self, capability: PackCapability) -> bool:
        """Register a new capability"""
        with self._lock:
            capability_key = f"{capability.pack_id}:{capability.capability_id}"
            
            # Check for conflicts
            if self._has_capability_conflict(capability):
                conflicts = self._get_capability_conflicts(capability)
                self.conflicts[capability_key] = conflicts
                logger.warning(f"Capability conflict detected for {capability_key}: {conflicts}")
                return False
            
            # Register capability
            self.capabilities[capability_key] = capability
            
            # Update category index
            category = capability.category
            if category not in self.capabilities_by_category:
                self.capabilities_by_category[category] = []
            self.capabilities_by_category[category].append(capability)
            
            # Update pack index
            if capability.pack_id not in self.pack_capabilities:
                self.pack_capabilities[capability.pack_id] = []
            self.pack_capabilities[capability.pack_id].append(capability)
            
            logger.info(f"Registered capability: {capability_key}")
            return True
    
    def unregister_pack_capabilities(self, pack_id: str) -> bool:
        """Unregister all capabilities for a pack"""
        with self._lock:
            if pack_id not in self.pack_capabilities:
                return True
            
            capabilities = self.pack_capabilities[pack_id].copy()
            
            for capability in capabilities:
                capability_key = f"{capability.pack_id}:{capability.capability_id}"
                
                # Remove from main registry
                if capability_key in self.capabilities:
                    del self.capabilities[capability_key]
                
                # Remove from category index
                if capability.category in self.capabilities_by_category:
                    self.capabilities_by_category[capability.category] = [
                        c for c in self.capabilities_by_category[capability.category]
                        if c.pack_id != pack_id
                    ]
                
                # Remove conflicts
                if capability_key in self.conflicts:
                    del self.conflicts[capability_key]
            
            # Remove pack from index
            del self.pack_capabilities[pack_id]
            
            logger.info(f"Unregistered all capabilities for pack: {pack_id}")
            return True
    
    def get_capabilities_by_category(self, category: str) -> List[PackCapability]:
        """Get all capabilities in a category"""
        with self._lock:
            return self.capabilities_by_category.get(category, []).copy()
    
    def get_pack_capabilities(self, pack_id: str) -> List[PackCapability]:
        """Get all capabilities for a pack"""
        with self._lock:
            return self.pack_capabilities.get(pack_id, []).copy()
    
    def has_capability(self, pack_id: str, capability_id: str) -> bool:
        """Check if a pack has a specific capability"""
        capability_key = f"{pack_id}:{capability_id}"
        return capability_key in self.capabilities
    
    def get_capability_conflicts(self, pack_id: str) -> Dict[str, List[str]]:
        """Get all conflicts for a pack's capabilities"""
        with self._lock:
            pack_conflicts = {}
            for capability in self.pack_capabilities.get(pack_id, []):
                capability_key = f"{capability.pack_id}:{capability.capability_id}"
                if capability_key in self.conflicts:
                    pack_conflicts[capability_key] = self.conflicts[capability_key]
            return pack_conflicts
    
    def _has_capability_conflict(self, capability: PackCapability) -> bool:
        """Check if capability conflicts with existing ones"""
        # Check for same capability ID from different packs
        for existing_key, existing_cap in self.capabilities.items():
            if (existing_cap.capability_id == capability.capability_id and
                existing_cap.pack_id != capability.pack_id):
                return True
            
            # Check for API endpoint conflicts
            if capability.api_endpoints and existing_cap.api_endpoints:
                if set(capability.api_endpoints) & set(existing_cap.api_endpoints):
                    return True
        
        return False
    
    def _get_capability_conflicts(self, capability: PackCapability) -> List[str]:
        """Get list of conflicting capabilities"""
        conflicts = []
        
        for existing_key, existing_cap in self.capabilities.items():
            if (existing_cap.capability_id == capability.capability_id and
                existing_cap.pack_id != capability.pack_id):
                conflicts.append(f"Capability ID conflict with {existing_key}")
            
            if capability.api_endpoints and existing_cap.api_endpoints:
                overlapping_endpoints = set(capability.api_endpoints) & set(existing_cap.api_endpoints)
                if overlapping_endpoints:
                    conflicts.append(f"API endpoint conflict with {existing_key}: {overlapping_endpoints}")
        
        return conflicts


class UIExtensionRegistry:
    """Registry for UI extension points and components"""
    
    def __init__(self):
        self.extension_points: Dict[str, UIExtensionPoint] = {}
        self.components: Dict[str, List[UIComponent]] = {}
        self.component_classes: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Initialize default extension points
        self._initialize_default_extension_points()
    
    def _initialize_default_extension_points(self):
        """Initialize built-in extension points"""
        default_points = [
            UIExtensionPoint(
                name="business_dashboard_widgets",
                location="main_dashboard",
                component_type="dashboard_widget",
                max_components=8,
                data_context={"business_metrics": True, "time_range": True}
            ),
            UIExtensionPoint(
                name="navigation_menu_items",
                location="sidebar_navigation",
                component_type="menu_item",
                max_components=10,
                data_context={"user_permissions": True}
            ),
            UIExtensionPoint(
                name="report_generators",
                location="reports_section",
                component_type="report_generator",
                max_components=15,
                data_context={"business_data": True, "date_range": True}
            ),
            UIExtensionPoint(
                name="quick_actions",
                location="dashboard_actions",
                component_type="action_button",
                max_components=12,
                data_context={"current_context": True}
            ),
            UIExtensionPoint(
                name="settings_panels",
                location="settings_tabs",
                component_type="settings_panel",
                max_components=20,
                data_context={"user_settings": True}
            )
        ]
        
        for point in default_points:
            self.extension_points[point.name] = point
    
    def register_extension_point(self, extension_point: UIExtensionPoint) -> bool:
        """Register a new extension point"""
        with self._lock:
            if extension_point.name in self.extension_points:
                logger.warning(f"Extension point {extension_point.name} already exists")
                return False
            
            self.extension_points[extension_point.name] = extension_point
            self.components[extension_point.name] = []
            
            logger.info(f"Registered extension point: {extension_point.name}")
            return True
    
    def register_ui_component(self, component: UIComponent) -> bool:
        """Register a UI component for an extension point"""
        with self._lock:
            extension_point_name = component.extension_point
            
            if extension_point_name not in self.extension_points:
                logger.error(f"Extension point {extension_point_name} not found")
                return False
            
            extension_point = self.extension_points[extension_point_name]
            
            # Check if we've reached the maximum components
            current_components = self.components.get(extension_point_name, [])
            if len(current_components) >= extension_point.max_components:
                logger.warning(f"Maximum components reached for {extension_point_name}")
                return False
            
            # Check for duplicate component ID
            component_key = f"{component.pack_id}:{component.component_id}"
            for existing_comp in current_components:
                existing_key = f"{existing_comp.pack_id}:{existing_comp.component_id}"
                if existing_key == component_key:
                    logger.warning(f"Component {component_key} already registered")
                    return False
            
            # Add component
            if extension_point_name not in self.components:
                self.components[extension_point_name] = []
            
            self.components[extension_point_name].append(component)
            
            # Sort by priority if required
            if extension_point.priority_order:
                self.components[extension_point_name].sort(key=lambda c: c.priority)
            
            logger.info(f"Registered UI component: {component_key} for {extension_point_name}")
            return True
    
    def unregister_pack_components(self, pack_id: str) -> bool:
        """Unregister all UI components for a pack"""
        with self._lock:
            removed_count = 0
            
            for extension_point_name, components in self.components.items():
                original_count = len(components)
                self.components[extension_point_name] = [
                    comp for comp in components if comp.pack_id != pack_id
                ]
                removed_count += original_count - len(self.components[extension_point_name])
            
            logger.info(f"Unregistered {removed_count} UI components for pack: {pack_id}")
            return True
    
    def get_extension_point_components(self, extension_point_name: str) -> List[UIComponent]:
        """Get all components for an extension point"""
        with self._lock:
            return self.components.get(extension_point_name, []).copy()
    
    def get_enabled_components(self, extension_point_name: str) -> List[UIComponent]:
        """Get only enabled components for an extension point"""
        with self._lock:
            all_components = self.components.get(extension_point_name, [])
            return [comp for comp in all_components if comp.enabled]
    
    def enable_component(self, pack_id: str, component_id: str) -> bool:
        """Enable a specific component"""
        with self._lock:
            for components in self.components.values():
                for comp in components:
                    if comp.pack_id == pack_id and comp.component_id == component_id:
                        comp.enabled = True
                        return True
            return False
    
    def disable_component(self, pack_id: str, component_id: str) -> bool:
        """Disable a specific component"""
        with self._lock:
            for components in self.components.values():
                for comp in components:
                    if comp.pack_id == pack_id and comp.component_id == component_id:
                        comp.enabled = False
                        return True
            return False


class PackExtensionManager:
    """Main manager for pack extension system"""
    
    def __init__(self):
        self.feature_registry = FeatureRegistry()
        self.ui_registry = UIExtensionRegistry()
        self.loaded_extensions: Dict[str, IPackExtension] = {}
        self.extension_contexts: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def load_pack_extension(self, pack_id: str, extension_path: Path) -> bool:
        """Load a pack extension from a Python module"""
        with self._lock:
            try:
                # Load the extension module
                spec = importlib.util.spec_from_file_location(f"{pack_id}_extension", extension_path)
                if spec is None or spec.loader is None:
                    logger.error(f"Failed to load extension spec for {pack_id}")
                    return False
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the extension class
                extension_class = None
                for name in dir(module):
                    obj = getattr(module, name)
                    if (isinstance(obj, type) and 
                        issubclass(obj, IPackExtension) and 
                        obj != IPackExtension):
                        extension_class = obj
                        break
                
                if extension_class is None:
                    logger.error(f"No extension class found in {extension_path}")
                    return False
                
                # Create extension instance
                extension = extension_class()
                
                # Initialize extension
                context = self._get_extension_context(pack_id)
                if not extension.initialize_extension(context):
                    logger.error(f"Failed to initialize extension for {pack_id}")
                    return False
                
                # Register capabilities
                capabilities = extension.get_capabilities()
                for capability in capabilities:
                    self.feature_registry.register_capability(capability)
                
                # Register UI components
                ui_components = extension.get_ui_components()
                for component in ui_components:
                    self.ui_registry.register_ui_component(component)
                
                # Store extension
                self.loaded_extensions[pack_id] = extension
                
                logger.info(f"Successfully loaded extension for pack: {pack_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load extension for {pack_id}: {e}")
                return False
    
    def unload_pack_extension(self, pack_id: str) -> bool:
        """Unload a pack extension"""
        with self._lock:
            if pack_id not in self.loaded_extensions:
                return True
            
            try:
                # Cleanup extension
                extension = self.loaded_extensions[pack_id]
                extension.cleanup_extension()
                
                # Unregister capabilities and UI components
                self.feature_registry.unregister_pack_capabilities(pack_id)
                self.ui_registry.unregister_pack_components(pack_id)
                
                # Remove extension
                del self.loaded_extensions[pack_id]
                
                # Clean up context
                if pack_id in self.extension_contexts:
                    del self.extension_contexts[pack_id]
                
                logger.info(f"Successfully unloaded extension for pack: {pack_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload extension for {pack_id}: {e}")
                return False
    
    def _get_extension_context(self, pack_id: str) -> Dict[str, Any]:
        """Get extension context for a pack"""
        if pack_id not in self.extension_contexts:
            self.extension_contexts[pack_id] = {
                'pack_id': pack_id,
                'feature_registry': self.feature_registry,
                'ui_registry': self.ui_registry,
                'api_base_url': '/api',
                'data_access': True,
                'ui_access': True
            }
        
        return self.extension_contexts[pack_id]
    
    def get_pack_status(self, pack_id: str) -> Dict[str, Any]:
        """Get status of a pack's extensions"""
        with self._lock:
            is_loaded = pack_id in self.loaded_extensions
            capabilities = self.feature_registry.get_pack_capabilities(pack_id)
            conflicts = self.feature_registry.get_capability_conflicts(pack_id)
            
            return {
                'loaded': is_loaded,
                'capabilities_count': len(capabilities),
                'capabilities': [asdict(cap) for cap in capabilities],
                'conflicts': conflicts,
                'has_conflicts': len(conflicts) > 0
            }
    
    def get_extension_points_summary(self) -> Dict[str, Any]:
        """Get summary of all extension points and their components"""
        with self._lock:
            summary = {}
            
            for point_name, point in self.ui_registry.extension_points.items():
                components = self.ui_registry.get_extension_point_components(point_name)
                enabled_components = self.ui_registry.get_enabled_components(point_name)
                
                summary[point_name] = {
                    'description': point.location,
                    'component_type': point.component_type,
                    'max_components': point.max_components,
                    'total_components': len(components),
                    'enabled_components': len(enabled_components),
                    'available_slots': point.max_components - len(components)
                }
            
            return summary


# Global instance
_pack_extension_manager = None

def get_pack_extension_manager() -> PackExtensionManager:
    """Get the global PackExtensionManager instance"""
    global _pack_extension_manager
    if _pack_extension_manager is None:
        _pack_extension_manager = PackExtensionManager()
    return _pack_extension_manager