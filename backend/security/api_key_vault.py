#!/usr/bin/env python3
"""
API Key Vault for Westfall Personal Assistant

Secure management of API keys and sensitive credentials using system keyring.
"""

import keyring
import json
from typing import Dict, List, Optional, Any
import logging
from .encryption import EncryptionManager

logger = logging.getLogger(__name__)


class APIKeyVault:
    """Secure API key management using system keyring and encryption."""
    
    SERVICE_NAME = "Westfall Assistant"
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
        self._ensure_keyring_available()
    
    def _ensure_keyring_available(self):
        """Check if keyring is available and functional."""
        try:
            # Test keyring functionality
            test_key = "test_keyring_access"
            keyring.set_password(self.SERVICE_NAME, test_key, "test_value")
            retrieved = keyring.get_password(self.SERVICE_NAME, test_key)
            keyring.delete_password(self.SERVICE_NAME, test_key)
            
            if retrieved != "test_value":
                raise Exception("Keyring test failed")
                
            logger.info("Keyring service available and functional")
        except Exception as e:
            logger.warning(f"Keyring not available or functional: {e}")
            logger.warning("API keys will be stored with basic encryption only")
    
    def _get_keyring_key(self, service: str) -> str:
        """Generate keyring key for a service."""
        return f"apikey_{service}"
    
    def store_api_key(self, service: str, api_key: str, metadata: Dict = None) -> bool:
        """Store an API key securely."""
        try:
            # Prepare the data to store
            key_data = {
                "api_key": api_key,
                "metadata": metadata or {}
            }
            
            # Double encryption: first with our encryption manager, then keyring
            encrypted_data = self.encryption_manager.encrypt(json.dumps(key_data))
            
            # Store in system keyring
            keyring_key = self._get_keyring_key(service)
            keyring.set_password(self.SERVICE_NAME, keyring_key, encrypted_data)
            
            logger.info(f"API key stored for service: {service}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store API key for {service}: {e}")
            return False
    
    def get_api_key(self, service: str) -> Optional[Dict]:
        """Retrieve an API key."""
        try:
            keyring_key = self._get_keyring_key(service)
            encrypted_data = keyring.get_password(self.SERVICE_NAME, keyring_key)
            
            if not encrypted_data:
                return None
            
            # Decrypt the data
            decrypted_json = self.encryption_manager.decrypt(encrypted_data)
            key_data = json.loads(decrypted_json)
            
            return {
                "service": service,
                "api_key": key_data["api_key"],
                "metadata": key_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service}: {e}")
            return None
    
    def delete_api_key(self, service: str) -> bool:
        """Delete an API key."""
        try:
            keyring_key = self._get_keyring_key(service)
            keyring.delete_password(self.SERVICE_NAME, keyring_key)
            
            logger.info(f"API key deleted for service: {service}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key for {service}: {e}")
            return False
    
    def list_services(self) -> List[str]:
        """List all services with stored API keys."""
        # Note: keyring doesn't provide a native way to list all keys
        # We'll maintain a separate index for this
        try:
            index_key = "service_index"
            encrypted_index = keyring.get_password(self.SERVICE_NAME, index_key)
            
            if not encrypted_index:
                return []
            
            decrypted_index = self.encryption_manager.decrypt(encrypted_index)
            return json.loads(decrypted_index)
            
        except Exception as e:
            logger.error(f"Failed to retrieve service list: {e}")
            return []
    
    def _update_service_index(self, service: str, add: bool = True):
        """Update the service index."""
        try:
            services = self.list_services()
            
            if add and service not in services:
                services.append(service)
            elif not add and service in services:
                services.remove(service)
            
            index_key = "service_index"
            encrypted_index = self.encryption_manager.encrypt(json.dumps(services))
            keyring.set_password(self.SERVICE_NAME, index_key, encrypted_index)
            
        except Exception as e:
            logger.error(f"Failed to update service index: {e}")
    
    def store_api_key_with_index(self, service: str, api_key: str, metadata: Dict = None) -> bool:
        """Store API key and update service index."""
        success = self.store_api_key(service, api_key, metadata)
        if success:
            self._update_service_index(service, add=True)
        return success
    
    def delete_api_key_with_index(self, service: str) -> bool:
        """Delete API key and update service index."""
        success = self.delete_api_key(service)
        if success:
            self._update_service_index(service, add=False)
        return success
    
    def validate_api_key(self, service: str, test_endpoint: str = None) -> Dict:
        """Validate an API key (placeholder for future implementation)."""
        key_data = self.get_api_key(service)
        if not key_data:
            return {"valid": False, "error": "API key not found"}
        
        # TODO: Implement actual validation based on service type
        # For now, just check if the key exists and is not empty
        api_key = key_data.get("api_key", "")
        if not api_key.strip():
            return {"valid": False, "error": "API key is empty"}
        
        return {"valid": True, "message": "API key format appears valid"}
    
    def get_api_key_info(self, service: str) -> Optional[Dict]:
        """Get API key metadata without exposing the actual key."""
        key_data = self.get_api_key(service)
        if not key_data:
            return None
        
        return {
            "service": service,
            "has_key": bool(key_data.get("api_key")),
            "key_length": len(key_data.get("api_key", "")),
            "metadata": key_data.get("metadata", {}),
            "key_preview": key_data.get("api_key", "")[:8] + "..." if key_data.get("api_key") else ""
        }
    
    def export_keys(self, include_keys: bool = False) -> Dict:
        """Export API key data (optionally including actual keys)."""
        export_data = {}
        
        for service in self.list_services():
            if include_keys:
                key_data = self.get_api_key(service)
                export_data[service] = key_data
            else:
                key_info = self.get_api_key_info(service)
                export_data[service] = key_info
        
        return export_data
    
    def import_keys(self, key_data: Dict) -> Dict:
        """Import API key data."""
        results = {"success": [], "failed": []}
        
        for service, data in key_data.items():
            try:
                api_key = data.get("api_key")
                metadata = data.get("metadata", {})
                
                if api_key:
                    success = self.store_api_key_with_index(service, api_key, metadata)
                    if success:
                        results["success"].append(service)
                    else:
                        results["failed"].append(service)
                else:
                    results["failed"].append(service)
                    
            except Exception as e:
                logger.error(f"Failed to import key for {service}: {e}")
                results["failed"].append(service)
        
        return results
    
    def clear_all_keys(self) -> bool:
        """Clear all stored API keys (use with caution)."""
        try:
            services = self.list_services()
            failed_deletions = []
            
            for service in services:
                if not self.delete_api_key(service):
                    failed_deletions.append(service)
            
            # Clear the service index
            try:
                keyring.delete_password(self.SERVICE_NAME, "service_index")
            except:
                pass
            
            if failed_deletions:
                logger.warning(f"Failed to delete keys for: {failed_deletions}")
                return False
            
            logger.info("All API keys cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear API keys: {e}")
            return False