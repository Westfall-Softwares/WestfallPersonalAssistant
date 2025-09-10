"""
Licensing System for Entrepreneur Assistant
Manages licenses for Tailor Packs and premium features
"""

import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LicenseType(Enum):
    """License types"""
    FREE = "free"
    TRIAL = "trial"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    PACK_SPECIFIC = "pack_specific"


class LicenseStatus(Enum):
    """License status"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    SUSPENDED = "suspended"
    TRIAL_EXPIRED = "trial_expired"


@dataclass
class License:
    """License information"""
    license_key: str
    license_type: LicenseType
    product_id: str  # Tailor Pack ID or feature ID
    issued_to: str  # Business name or email
    issued_date: datetime
    expiry_date: Optional[datetime]
    features: List[str]
    max_users: int = 1
    is_trial: bool = False
    metadata: Dict[str, Any] = None


class LicenseValidator:
    """Validates and manages licenses"""
    
    def __init__(self, license_dir: str = None):
        self.license_dir = license_dir or os.path.join(os.getcwd(), "data", "licenses")
        os.makedirs(self.license_dir, exist_ok=True)
        
        self.licenses = {}
        self.load_licenses()
    
    def load_licenses(self):
        """Load existing licenses from storage"""
        license_file = os.path.join(self.license_dir, "licenses.json")
        if os.path.exists(license_file):
            try:
                with open(license_file, 'r') as f:
                    license_data = json.load(f)
                
                for key, data in license_data.items():
                    # Convert datetime strings back to datetime objects
                    issued_date = datetime.fromisoformat(data['issued_date'])
                    expiry_date = None
                    if data.get('expiry_date'):
                        expiry_date = datetime.fromisoformat(data['expiry_date'])
                    
                    license_obj = License(
                        license_key=data['license_key'],
                        license_type=LicenseType(data['license_type']),
                        product_id=data['product_id'],
                        issued_to=data['issued_to'],
                        issued_date=issued_date,
                        expiry_date=expiry_date,
                        features=data.get('features', []),
                        max_users=data.get('max_users', 1),
                        is_trial=data.get('is_trial', False),
                        metadata=data.get('metadata', {})
                    )
                    
                    self.licenses[key] = license_obj
                    
            except Exception as e:
                print(f"Error loading licenses: {e}")
    
    def save_licenses(self):
        """Save licenses to storage"""
        license_file = os.path.join(self.license_dir, "licenses.json")
        
        try:
            license_data = {}
            for key, license_obj in self.licenses.items():
                data = {
                    'license_key': license_obj.license_key,
                    'license_type': license_obj.license_type.value,
                    'product_id': license_obj.product_id,
                    'issued_to': license_obj.issued_to,
                    'issued_date': license_obj.issued_date.isoformat(),
                    'expiry_date': license_obj.expiry_date.isoformat() if license_obj.expiry_date else None,
                    'features': license_obj.features,
                    'max_users': license_obj.max_users,
                    'is_trial': license_obj.is_trial,
                    'metadata': license_obj.metadata or {}
                }
                license_data[key] = data
            
            with open(license_file, 'w') as f:
                json.dump(license_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving licenses: {e}")
    
    def validate_license(self, license_key: str) -> Dict[str, Any]:
        """Validate a license key"""
        if license_key not in self.licenses:
            return {
                "valid": False,
                "status": LicenseStatus.INVALID,
                "message": "License key not found"
            }
        
        license_obj = self.licenses[license_key]
        
        # Check if license is expired
        if license_obj.expiry_date and datetime.now() > license_obj.expiry_date:
            status = LicenseStatus.TRIAL_EXPIRED if license_obj.is_trial else LicenseStatus.EXPIRED
            return {
                "valid": False,
                "status": status,
                "message": "License has expired",
                "expiry_date": license_obj.expiry_date
            }
        
        return {
            "valid": True,
            "status": LicenseStatus.VALID,
            "license": license_obj,
            "message": "License is valid"
        }
    
    def add_license(self, license_key: str, product_id: str, issued_to: str, 
                   license_type: LicenseType = LicenseType.BASIC,
                   expiry_days: Optional[int] = None,
                   features: List[str] = None,
                   is_trial: bool = False) -> bool:
        """Add a new license"""
        try:
            issued_date = datetime.now()
            expiry_date = None
            
            if expiry_days is not None:
                expiry_date = issued_date + timedelta(days=expiry_days)
            
            license_obj = License(
                license_key=license_key,
                license_type=license_type,
                product_id=product_id,
                issued_to=issued_to,
                issued_date=issued_date,
                expiry_date=expiry_date,
                features=features or [],
                is_trial=is_trial
            )
            
            self.licenses[license_key] = license_obj
            self.save_licenses()
            return True
            
        except Exception as e:
            print(f"Error adding license: {e}")
            return False
    
    def create_trial_license(self, product_id: str, issued_to: str, 
                           trial_days: int = 30) -> Optional[str]:
        """Create a trial license"""
        # Generate trial license key
        trial_key = self.generate_license_key(f"TRIAL_{product_id}_{issued_to}")
        
        if self.add_license(
            license_key=trial_key,
            product_id=product_id,
            issued_to=issued_to,
            license_type=LicenseType.TRIAL,
            expiry_days=trial_days,
            is_trial=True
        ):
            return trial_key
        
        return None
    
    def import_license_file(self, license_file_path: str) -> Dict[str, Any]:
        """Import a license from a file"""
        try:
            with open(license_file_path, 'r') as f:
                license_data = json.load(f)
            
            # Validate license file format
            required_fields = ['license_key', 'product_id', 'issued_to', 'signature']
            for field in required_fields:
                if field not in license_data:
                    return {"success": False, "error": f"Missing field: {field}"}
            
            # TODO: Implement signature verification for production
            # For now, we'll accept any properly formatted license
            
            license_key = license_data['license_key']
            
            # Add the license
            success = self.add_license(
                license_key=license_key,
                product_id=license_data['product_id'],
                issued_to=license_data['issued_to'],
                license_type=LicenseType(license_data.get('license_type', 'basic')),
                expiry_days=license_data.get('expiry_days'),
                features=license_data.get('features', [])
            )
            
            if success:
                return {
                    "success": True,
                    "license_key": license_key,
                    "message": "License imported successfully"
                }
            else:
                return {"success": False, "error": "Failed to add license"}
                
        except Exception as e:
            return {"success": False, "error": f"Error importing license: {str(e)}"}
    
    def get_pack_license_status(self, pack_id: str) -> Dict[str, Any]:
        """Get license status for a specific Tailor Pack"""
        for license_key, license_obj in self.licenses.items():
            if license_obj.product_id == pack_id:
                validation = self.validate_license(license_key)
                return {
                    "has_license": True,
                    "license_key": license_key,
                    "license_type": license_obj.license_type.value,
                    "is_trial": license_obj.is_trial,
                    "valid": validation["valid"],
                    "status": validation["status"].value,
                    "expiry_date": license_obj.expiry_date
                }
        
        return {
            "has_license": False,
            "trial_available": True  # Assume trials are available by default
        }
    
    def get_feature_access(self, feature_name: str) -> bool:
        """Check if user has access to a specific feature"""
        # Free features (always available)
        free_features = [
            "basic_notes", "basic_calendar", "basic_todo", "basic_contacts",
            "basic_finance", "basic_time_tracking", "password_manager"
        ]
        
        if feature_name in free_features:
            return True
        
        # Check licensed features
        for license_obj in self.licenses.values():
            validation = self.validate_license(license_obj.license_key)
            if validation["valid"] and feature_name in license_obj.features:
                return True
        
        return False
    
    def get_license_summary(self) -> Dict[str, Any]:
        """Get summary of all licenses"""
        summary = {
            "total_licenses": len(self.licenses),
            "valid_licenses": 0,
            "trial_licenses": 0,
            "expired_licenses": 0,
            "products": []
        }
        
        for license_obj in self.licenses.values():
            validation = self.validate_license(license_obj.license_key)
            
            if validation["valid"]:
                summary["valid_licenses"] += 1
            else:
                summary["expired_licenses"] += 1
            
            if license_obj.is_trial:
                summary["trial_licenses"] += 1
            
            # Add product info
            product_info = {
                "product_id": license_obj.product_id,
                "license_type": license_obj.license_type.value,
                "is_trial": license_obj.is_trial,
                "valid": validation["valid"],
                "expiry_date": license_obj.expiry_date
            }
            summary["products"].append(product_info)
        
        return summary
    
    @staticmethod
    def generate_license_key(seed: str) -> str:
        """Generate a license key based on a seed"""
        # Simple key generation for demo purposes
        # In production, this would be more sophisticated
        hash_obj = hashlib.sha256(seed.encode())
        hash_bytes = hash_obj.digest()
        encoded = base64.b64encode(hash_bytes).decode('utf-8')
        
        # Format as license key
        key = encoded[:20].upper().replace('/', '').replace('+', '')
        return f"{key[:5]}-{key[5:10]}-{key[10:15]}-{key[15:20]}"
    
    def remove_license(self, license_key: str) -> bool:
        """Remove a license"""
        if license_key in self.licenses:
            del self.licenses[license_key]
            self.save_licenses()
            return True
        return False


class LicenseManager:
    """High-level license management"""
    
    def __init__(self):
        self.validator = LicenseValidator()
        self.trial_tracking = {}
    
    def check_pack_license(self, pack_id: str, require_license: bool = True) -> Dict[str, Any]:
        """Check if a pack can be used based on licensing"""
        if not require_license:
            return {"allowed": True, "reason": "No license required"}
        
        status = self.validator.get_pack_license_status(pack_id)
        
        if status["has_license"]:
            if status["valid"]:
                return {"allowed": True, "license_type": status["license_type"]}
            else:
                return {"allowed": False, "reason": "License expired"}
        else:
            # Offer trial if available
            if status.get("trial_available", False):
                return {
                    "allowed": False, 
                    "reason": "No license", 
                    "trial_available": True
                }
            else:
                return {"allowed": False, "reason": "License required"}
    
    def start_trial(self, pack_id: str, business_name: str) -> Dict[str, Any]:
        """Start a trial for a pack"""
        # Check if trial already exists
        status = self.validator.get_pack_license_status(pack_id)
        if status["has_license"]:
            return {"success": False, "error": "License already exists"}
        
        # Create trial license
        trial_key = self.validator.create_trial_license(pack_id, business_name)
        
        if trial_key:
            return {
                "success": True,
                "trial_key": trial_key,
                "trial_days": 30,
                "message": "Trial started successfully"
            }
        else:
            return {"success": False, "error": "Failed to create trial"}
    
    def import_license(self, license_file_path: str) -> Dict[str, Any]:
        """Import a license file"""
        return self.validator.import_license_file(license_file_path)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get license data for dashboard display"""
        summary = self.validator.get_license_summary()
        
        # Add trial status
        active_trials = [
            p for p in summary["products"] 
            if p["is_trial"] and p["valid"]
        ]
        
        summary["active_trials"] = len(active_trials)
        summary["trial_details"] = active_trials
        
        return summary


# Global license manager instance
_license_manager = None

def get_license_manager() -> LicenseManager:
    """Get the global license manager instance"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager