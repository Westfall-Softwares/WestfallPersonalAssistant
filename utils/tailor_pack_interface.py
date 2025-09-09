"""
Tailor Pack Interface Definitions
Defines the interfaces that Tailor Packs must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from PyQt5.QtWidgets import QWidget


@dataclass
class TailorPackCapability:
    """Defines a capability provided by a Tailor Pack"""
    name: str
    description: str
    category: str
    ui_component: Optional[str] = None
    api_endpoints: List[str] = None
    data_schema: Dict[str, Any] = None


class ITailorPack(ABC):
    """Base interface that all Tailor Packs must implement"""
    
    @property
    @abstractmethod
    def pack_id(self) -> str:
        """Unique identifier for the pack"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the pack"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the pack"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the pack does"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[TailorPackCapability]:
        """List of capabilities provided by this pack"""
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the pack with application context"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up resources when pack is disabled/unloaded"""
        pass
    
    @abstractmethod
    def get_ui_components(self) -> Dict[str, QWidget]:
        """Get UI components provided by this pack"""
        pass
    
    @abstractmethod
    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an action request"""
        pass
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this pack"""
        return {}
    
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate a configuration"""
        return True
    
    def get_data_requirements(self) -> List[str]:
        """Get list of data types this pack requires access to"""
        return []
    
    def get_permissions(self) -> List[str]:
        """Get list of permissions this pack requires"""
        return []


class IBusinessTailorPack(ITailorPack):
    """Interface for business-focused Tailor Packs"""
    
    @property
    @abstractmethod
    def business_category(self) -> str:
        """Business category (marketing, sales, finance, operations, etc.)"""
        pass
    
    @property
    @abstractmethod
    def target_audience(self) -> str:
        """Target audience (entrepreneur, small_business, freelancer, etc.)"""
        pass
    
    @abstractmethod
    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business metrics tracked by this pack"""
        pass
    
    @abstractmethod
    def generate_business_report(self, period: str) -> Dict[str, Any]:
        """Generate a business report for the specified period"""
        pass


class IWorkflowTailorPack(ITailorPack):
    """Interface for workflow automation Tailor Packs"""
    
    @abstractmethod
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows"""
        pass
    
    @abstractmethod
    def execute_workflow(self, workflow_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific workflow"""
        pass
    
    @abstractmethod
    def create_custom_workflow(self, definition: Dict[str, Any]) -> str:
        """Create a custom workflow and return its ID"""
        pass


class IIntegrationTailorPack(ITailorPack):
    """Interface for third-party integration Tailor Packs"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Name of the service being integrated"""
        pass
    
    @property
    @abstractmethod
    def api_version(self) -> str:
        """Version of the API being used"""
        pass
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    def sync_data(self, data_types: List[str]) -> Dict[str, Any]:
        """Sync data with the external service"""
        pass
    
    @abstractmethod
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        pass


class IUITailorPack(ITailorPack):
    """Interface for UI-focused Tailor Packs"""
    
    @abstractmethod
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Get menu items to add to the application"""
        pass
    
    @abstractmethod
    def get_toolbar_buttons(self) -> List[Dict[str, Any]]:
        """Get toolbar buttons to add to the application"""
        pass
    
    @abstractmethod
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Get dashboard widgets provided by this pack"""
        pass
    
    @abstractmethod
    def get_settings_panels(self) -> List[Dict[str, Any]]:
        """Get settings panels for configuration"""
        pass


class TailorPackBase(ITailorPack):
    """Base implementation of ITailorPack with common functionality"""
    
    def __init__(self, pack_id: str, name: str, version: str, description: str):
        self._pack_id = pack_id
        self._name = name
        self._version = version
        self._description = description
        self._initialized = False
        self._context = {}
    
    @property
    def pack_id(self) -> str:
        return self._pack_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def description(self) -> str:
        return self._description
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Default initialization"""
        self._context = context
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """Default cleanup"""
        self._initialized = False
        self._context = {}
        return True
    
    def get_ui_components(self) -> Dict[str, QWidget]:
        """Default UI components (none)"""
        return {}
    
    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Default action handler"""
        return {"success": False, "error": f"Action '{action}' not supported"}
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def context(self) -> Dict[str, Any]:
        return self._context


class BusinessTailorPackBase(TailorPackBase, IBusinessTailorPack):
    """Base implementation for business Tailor Packs"""
    
    def __init__(self, pack_id: str, name: str, version: str, description: str, 
                 business_category: str, target_audience: str):
        super().__init__(pack_id, name, version, description)
        self._business_category = business_category
        self._target_audience = target_audience
    
    @property
    def business_category(self) -> str:
        return self._business_category
    
    @property
    def target_audience(self) -> str:
        return self._target_audience
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Default business metrics"""
        return {}
    
    def generate_business_report(self, period: str) -> Dict[str, Any]:
        """Default business report"""
        return {
            "period": period,
            "metrics": self.get_business_metrics(),
            "pack_id": self.pack_id,
            "generated_at": "timestamp_placeholder"
        }


# Registry for pack types
PACK_TYPE_REGISTRY = {
    'business': IBusinessTailorPack,
    'workflow': IWorkflowTailorPack,
    'integration': IIntegrationTailorPack,
    'ui': IUITailorPack
}


def get_pack_interface(pack_type: str) -> type:
    """Get the appropriate interface for a pack type"""
    return PACK_TYPE_REGISTRY.get(pack_type, ITailorPack)