"""
Enhanced Order Verification System for Tailor Packs
Provides secure order number validation and license management for business packs
"""

import os
import json
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


@dataclass
class PackLicense:
    """Represents a Tailor Pack license"""
    order_number: str
    pack_id: str
    license_key: str
    customer_email: str
    purchase_date: datetime
    expiry_date: Optional[datetime]
    license_type: str  # 'trial', 'monthly', 'yearly', 'lifetime'
    max_installations: int
    current_installations: int
    is_valid: bool
    features_enabled: List[str]


@dataclass
class OrderValidationResult:
    """Result of order number validation"""
    is_valid: bool
    pack_info: Optional[Dict]
    license: Optional[PackLicense]
    error_message: Optional[str]
    trial_available: bool


class OrderVerificationService:
    """
    Handles order number verification and license management for Tailor Packs
    """
    
    def __init__(self, license_server_url: str = None):
        self.license_server_url = license_server_url or "https://licensing.westfall-software.com"
        self.local_license_file = "data/licenses.json"
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.local_license_file), exist_ok=True)
        
        # Load existing licenses
        self.licenses: Dict[str, PackLicense] = self._load_local_licenses()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for local license storage"""
        key_file = "data/.license_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def verify_order(self, order_number: str) -> OrderValidationResult:
        """
        Verify an order number and return validation result
        """
        try:
            # Clean and validate format
            order_number = order_number.strip().upper()
            if not self._is_valid_order_format(order_number):
                return OrderValidationResult(
                    is_valid=False,
                    pack_info=None,
                    license=None,
                    error_message="Invalid order number format",
                    trial_available=False
                )
            
            # Check if already licensed locally
            existing_license = self._get_local_license(order_number)
            if existing_license and existing_license.is_valid:
                # Verify license is still valid
                if self._is_license_expired(existing_license):
                    existing_license.is_valid = False
                    self._save_local_licenses()
                    return OrderValidationResult(
                        is_valid=False,
                        pack_info=None,
                        license=existing_license,
                        error_message="License has expired",
                        trial_available=False
                    )
                
                return OrderValidationResult(
                    is_valid=True,
                    pack_info=self._get_pack_info_for_license(existing_license),
                    license=existing_license,
                    error_message=None,
                    trial_available=False
                )
            
            # Verify with remote server
            remote_result = self._verify_with_server(order_number)
            if remote_result.is_valid and remote_result.license:
                # Store license locally
                self._store_local_license(remote_result.license)
                return remote_result
            
            # Check if trial is available
            trial_available = self._is_trial_available(order_number)
            
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message=remote_result.error_message or "Order not found",
                trial_available=trial_available
            )
            
        except Exception as e:
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message=f"Verification failed: {str(e)}",
                trial_available=True  # Allow trial on verification errors
            )
    
    def start_trial_license(self, pack_id: str, business_email: str = None) -> OrderValidationResult:
        """
        Start a trial license for entrepreneurs to test business packs
        """
        try:
            # Check if trial already exists
            trial_order = f"TRIAL-{pack_id}-{int(time.time())}"
            
            # Create trial license
            trial_license = PackLicense(
                order_number=trial_order,
                pack_id=pack_id,
                license_key=self._generate_trial_key(pack_id),
                customer_email=business_email or "trial@entrepreneur.local",
                purchase_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=30),  # 30-day trial
                license_type="trial",
                max_installations=1,
                current_installations=1,
                is_valid=True,
                features_enabled=["basic", "trial"]  # Limited features for trial
            )
            
            # Store trial license
            self._store_local_license(trial_license)
            
            return OrderValidationResult(
                is_valid=True,
                pack_info=self._get_pack_info_for_license(trial_license),
                license=trial_license,
                error_message=None,
                trial_available=False  # Trial now active
            )
            
        except Exception as e:
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message=f"Failed to start trial: {str(e)}",
                trial_available=True
            )
    
    def get_entrepreneur_purchase_info(self, pack_id: str) -> Dict:
        """
        Get purchase information and pricing for entrepreneurs
        """
        pack_pricing = {
            "marketing-essentials": {
                "name": "Marketing Essentials Pack",
                "monthly_price": 29.99,
                "yearly_price": 299.99,
                "lifetime_price": 599.99,
                "description": "Complete marketing automation and campaign management",
                "target_businesses": ["startups", "small_business", "entrepreneurs"],
                "roi_benefit": "Typically saves 10+ hours/week on marketing tasks"
            },
            "sales-pipeline-pro": {
                "name": "Sales Pipeline Pro",
                "monthly_price": 49.99,
                "yearly_price": 499.99,
                "lifetime_price": 999.99,
                "description": "Advanced CRM and sales automation tools",
                "target_businesses": ["sales_teams", "growing_businesses"],
                "roi_benefit": "Increase sales conversion by 25-40%"
            },
            "finance-master": {
                "name": "Finance Master Suite",
                "monthly_price": 39.99,
                "yearly_price": 399.99,
                "lifetime_price": 799.99,
                "description": "Complete financial management and reporting",
                "target_businesses": ["solo_entrepreneurs", "small_business"],
                "roi_benefit": "Save $1000s on accounting fees annually"
            }
        }
        
        pack_info = pack_pricing.get(pack_id, {
            "name": "Business Pack",
            "monthly_price": 19.99,
            "yearly_price": 199.99,
            "lifetime_price": 399.99,
            "description": "Professional business functionality",
            "target_businesses": ["entrepreneurs"],
            "roi_benefit": "Boost productivity and efficiency"
        })
        
        pack_info["purchase_url"] = f"https://westfallsoftwares.com/purchase/{pack_id}"
        pack_info["trial_available"] = True
        pack_info["money_back_guarantee"] = "30-day money-back guarantee"
        
        return pack_info
    
    def start_trial(self, pack_id: str, customer_email: str) -> OrderValidationResult:
        """Start a trial license for a pack"""
        try:
            # Check if trial already used
            if self._has_used_trial(pack_id, customer_email):
                return OrderValidationResult(
                    is_valid=False,
                    pack_info=None,
                    license=None,
                    error_message="Trial already used for this pack",
                    trial_available=False
                )
            
            # Create trial license
            trial_order = f"TRIAL-{pack_id}-{int(time.time())}"
            trial_license = PackLicense(
                order_number=trial_order,
                pack_id=pack_id,
                license_key=self._generate_trial_key(pack_id),
                customer_email=customer_email,
                purchase_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=30),
                license_type="trial",
                max_installations=1,
                current_installations=1,
                is_valid=True,
                features_enabled=self._get_trial_features(pack_id)
            )
            
            # Store trial license
            self._store_local_license(trial_license)
            
            return OrderValidationResult(
                is_valid=True,
                pack_info=self._get_pack_info_for_license(trial_license),
                license=trial_license,
                error_message=None,
                trial_available=False  # Already used
            )
            
        except Exception as e:
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message=f"Trial activation failed: {str(e)}",
                trial_available=True
            )
    
    def get_license_status(self, pack_id: str) -> Dict[str, any]:
        """Get current license status for a pack"""
        pack_licenses = [lic for lic in self.licenses.values() if lic.pack_id == pack_id]
        
        if not pack_licenses:
            return {
                "licensed": False,
                "license_type": None,
                "days_remaining": None,
                "trial_available": self._is_trial_available_for_pack(pack_id)
            }
        
        # Get most recent valid license
        valid_licenses = [lic for lic in pack_licenses if lic.is_valid and not self._is_license_expired(lic)]
        
        if not valid_licenses:
            return {
                "licensed": False,
                "license_type": None,
                "days_remaining": None,
                "trial_available": self._is_trial_available_for_pack(pack_id),
                "expired_licenses": len(pack_licenses)
            }
        
        current_license = max(valid_licenses, key=lambda x: x.purchase_date)
        days_remaining = None
        
        if current_license.expiry_date:
            days_remaining = (current_license.expiry_date - datetime.now()).days
            if days_remaining < 0:
                days_remaining = 0
        
        return {
            "licensed": True,
            "license_type": current_license.license_type,
            "days_remaining": days_remaining,
            "order_number": current_license.order_number,
            "features_enabled": current_license.features_enabled,
            "max_installations": current_license.max_installations,
            "current_installations": current_license.current_installations
        }
    
    def _is_valid_order_format(self, order_number: str) -> bool:
        """Validate order number format"""
        # Basic format validation
        if len(order_number) < 6:
            return False
        
        # Check for common patterns
        if order_number.startswith("WF-") and len(order_number) >= 10:
            return True
        if order_number.startswith("TRIAL-") and len(order_number) >= 15:
            return True
        if order_number.isalnum() and len(order_number) >= 8:
            return True
        
        return False
    
    def _verify_with_server(self, order_number: str) -> OrderValidationResult:
        """Verify order with remote licensing server"""
        try:
            import requests
            
            response = requests.post(
                f"{self.license_server_url}/verify",
                json={
                    "order_number": order_number,
                    "product": "tailor_packs",
                    "version": "1.0.0"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("valid"):
                    license_data = data.get("license")
                    license = PackLicense(
                        order_number=order_number,
                        pack_id=license_data.get("pack_id"),
                        license_key=license_data.get("license_key"),
                        customer_email=license_data.get("customer_email"),
                        purchase_date=datetime.fromisoformat(license_data.get("purchase_date")),
                        expiry_date=datetime.fromisoformat(license_data.get("expiry_date")) if license_data.get("expiry_date") else None,
                        license_type=license_data.get("license_type"),
                        max_installations=license_data.get("max_installations", 1),
                        current_installations=license_data.get("current_installations", 0),
                        is_valid=True,
                        features_enabled=license_data.get("features_enabled", [])
                    )
                    
                    return OrderValidationResult(
                        is_valid=True,
                        pack_info=data.get("pack_info"),
                        license=license,
                        error_message=None,
                        trial_available=data.get("trial_available", False)
                    )
                else:
                    return OrderValidationResult(
                        is_valid=False,
                        pack_info=None,
                        license=None,
                        error_message=data.get("error", "Invalid order number"),
                        trial_available=data.get("trial_available", False)
                    )
            else:
                return OrderValidationResult(
                    is_valid=False,
                    pack_info=None,
                    license=None,
                    error_message=f"Server error: {response.status_code}",
                    trial_available=False
                )
                
        except requests.RequestException:
            # Offline mode - use local validation only
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message="Unable to verify online (offline mode)",
                trial_available=True
            )
        except Exception as e:
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message=f"Verification error: {str(e)}",
                trial_available=False
            )
    
    def _load_local_licenses(self) -> Dict[str, PackLicense]:
        """Load licenses from local encrypted storage"""
        if not os.path.exists(self.local_license_file):
            return {}
        
        try:
            with open(self.local_license_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            licenses_data = json.loads(decrypted_data.decode())
            
            licenses = {}
            for order_number, license_dict in licenses_data.items():
                # Convert datetime strings back to datetime objects
                license_dict['purchase_date'] = datetime.fromisoformat(license_dict['purchase_date'])
                if license_dict['expiry_date']:
                    license_dict['expiry_date'] = datetime.fromisoformat(license_dict['expiry_date'])
                
                licenses[order_number] = PackLicense(**license_dict)
            
            return licenses
            
        except Exception as e:
            print(f"Error loading licenses: {e}")
            return {}
    
    def _save_local_licenses(self):
        """Save licenses to local encrypted storage"""
        try:
            # Convert to serializable format
            licenses_data = {}
            for order_number, license in self.licenses.items():
                license_dict = asdict(license)
                # Convert datetime objects to strings
                license_dict['purchase_date'] = license.purchase_date.isoformat()
                if license.expiry_date:
                    license_dict['expiry_date'] = license.expiry_date.isoformat()
                else:
                    license_dict['expiry_date'] = None
                
                licenses_data[order_number] = license_dict
            
            # Encrypt and save
            json_data = json.dumps(licenses_data).encode()
            encrypted_data = self.cipher_suite.encrypt(json_data)
            
            with open(self.local_license_file, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            print(f"Error saving licenses: {e}")
    
    def _store_local_license(self, license: PackLicense):
        """Store a license locally"""
        self.licenses[license.order_number] = license
        self._save_local_licenses()
    
    def _get_local_license(self, order_number: str) -> Optional[PackLicense]:
        """Get license from local storage"""
        return self.licenses.get(order_number)
    
    def _is_license_expired(self, license: PackLicense) -> bool:
        """Check if license is expired"""
        if not license.expiry_date:
            return False  # Lifetime license
        return datetime.now() > license.expiry_date
    
    def _is_trial_available(self, order_number: str) -> bool:
        """Check if trial is available for this order/email"""
        # For now, always return True for demonstration
        # In real implementation, this would check against used trials
        return True
    
    def _is_trial_available_for_pack(self, pack_id: str) -> bool:
        """Check if trial is available for a specific pack"""
        # Check if any trial licenses exist for this pack
        for license in self.licenses.values():
            if license.pack_id == pack_id and license.license_type == "trial":
                return False  # Trial already used
        return True
    
    def _has_used_trial(self, pack_id: str, customer_email: str) -> bool:
        """Check if customer has already used trial for this pack"""
        for license in self.licenses.values():
            if (license.pack_id == pack_id and 
                license.customer_email == customer_email and
                license.license_type == "trial"):
                return True
        return False
    
    def _generate_trial_key(self, pack_id: str) -> str:
        """Generate a trial license key"""
        timestamp = str(int(time.time()))
        data = f"TRIAL-{pack_id}-{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def _get_trial_features(self, pack_id: str) -> List[str]:
        """Get trial features for a pack"""
        # Default trial features - in real implementation, this would be pack-specific
        return ["basic_features", "limited_usage", "watermark"]
    
    def _get_pack_info_for_license(self, license: PackLicense) -> Dict[str, any]:
        """Get pack information for a license"""
        # Mock pack info - in real implementation, this would come from pack registry
        return {
            "pack_id": license.pack_id,
            "name": f"Pack {license.pack_id}",
            "version": "1.0.0",
            "description": f"Business pack for {license.pack_id}",
            "category": "business"
        }


# Global instance
_order_verification_service = None

def get_order_verification_service() -> OrderVerificationService:
    """Get the global OrderVerificationService instance"""
    global _order_verification_service
    if _order_verification_service is None:
        _order_verification_service = OrderVerificationService()
    return _order_verification_service
    def __init__(self, data_dir: str = None):
        """Initialize the order verification service"""
        from backend.platform_compatibility import PlatformManager
        
        if data_dir is None:
            platform_manager = PlatformManager()
            app_dirs = platform_manager.setup_application_directories("westfall-assistant")
            self.data_dir = str(app_dirs['data'] / "licenses")
        else:
            self.data_dir = data_dir
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize encryption for license storage
        self.key_file = os.path.join(self.data_dir, '.license_key')
        self.licenses_file = os.path.join(self.data_dir, 'licenses.enc')
        self.trial_file = os.path.join(self.data_dir, 'trials.json')
        
        self._init_encryption()
        self.licenses = self._load_licenses()
        self.trials = self._load_trials()
    
    def _init_encryption(self):
        """Initialize encryption key for license storage"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new encryption key
            password = b"westfall_tailor_pack_system"  # In production, use better key derivation
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
        self.cipher_suite = Fernet(key)
    
    def _load_licenses(self) -> Dict[str, PackLicense]:
        """Load encrypted licenses from disk"""
        if not os.path.exists(self.licenses_file):
            return {}
        
        try:
            with open(self.licenses_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            licenses_data = json.loads(decrypted_data.decode())
            
            licenses = {}
            for order_number, license_data in licenses_data.items():
                # Convert datetime strings back to datetime objects
                license_data['purchase_date'] = datetime.fromisoformat(license_data['purchase_date'])
                if license_data['expiry_date']:
                    license_data['expiry_date'] = datetime.fromisoformat(license_data['expiry_date'])
                else:
                    license_data['expiry_date'] = None
                
                licenses[order_number] = PackLicense(**license_data)
            
            return licenses
        except Exception as e:
            print(f"Error loading licenses: {e}")
            return {}
    
    def _save_licenses(self):
        """Save encrypted licenses to disk"""
        try:
            # Convert licenses to serializable format
            licenses_data = {}
            for order_number, license in self.licenses.items():
                license_dict = asdict(license)
                license_dict['purchase_date'] = license.purchase_date.isoformat()
                if license.expiry_date:
                    license_dict['expiry_date'] = license.expiry_date.isoformat()
                else:
                    license_dict['expiry_date'] = None
                licenses_data[order_number] = license_dict
            
            json_data = json.dumps(licenses_data).encode()
            encrypted_data = self.cipher_suite.encrypt(json_data)
            
            with open(self.licenses_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error saving licenses: {e}")
    
    def _load_trials(self) -> Dict[str, Dict]:
        """Load trial information"""
        if not os.path.exists(self.trial_file):
            return {}
        
        try:
            with open(self.trial_file, 'r') as f:
                trials_data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            for trial_id, trial_info in trials_data.items():
                trial_info['start_date'] = datetime.fromisoformat(trial_info['start_date'])
                trial_info['end_date'] = datetime.fromisoformat(trial_info['end_date'])
            
            return trials_data
        except Exception as e:
            print(f"Error loading trials: {e}")
            return {}
    
    def _save_trials(self):
        """Save trial information"""
        try:
            # Convert trials to serializable format
            trials_data = {}
            for trial_id, trial_info in self.trials.items():
                trial_dict = trial_info.copy()
                trial_dict['start_date'] = trial_info['start_date'].isoformat()
                trial_dict['end_date'] = trial_info['end_date'].isoformat()
                trials_data[trial_id] = trial_dict
            
            with open(self.trial_file, 'w') as f:
                json.dump(trials_data, f, indent=2)
        except Exception as e:
            print(f"Error saving trials: {e}")
    
    def validate_order_number(self, order_number: str, pack_id: str) -> OrderValidationResult:
        """
        Validate an order number for a specific pack
        
        Args:
            order_number: The order number to validate
            pack_id: The pack ID being activated
        
        Returns:
            OrderValidationResult with validation details
        """
        # Check if we already have a valid license for this order
        if order_number in self.licenses:
            license = self.licenses[order_number]
            if license.pack_id == pack_id and license.is_valid:
                if self._is_license_valid(license):
                    return OrderValidationResult(
                        is_valid=True,
                        pack_info=self._get_pack_info(pack_id),
                        license=license,
                        error_message=None,
                        trial_available=False
                    )
        
        # In a real implementation, this would contact the license server
        # For demonstration, we'll simulate validation based on order format
        validation_result = self._simulate_order_validation(order_number, pack_id)
        
        if validation_result['is_valid']:
            # Create and store license
            license = PackLicense(
                order_number=order_number,
                pack_id=pack_id,
                license_key=validation_result['license_key'],
                customer_email=validation_result['customer_email'],
                purchase_date=datetime.now(),
                expiry_date=validation_result.get('expiry_date'),
                license_type=validation_result['license_type'],
                max_installations=validation_result['max_installations'],
                current_installations=1,
                is_valid=True,
                features_enabled=validation_result['features_enabled']
            )
            
            self.licenses[order_number] = license
            self._save_licenses()
            
            return OrderValidationResult(
                is_valid=True,
                pack_info=self._get_pack_info(pack_id),
                license=license,
                error_message=None,
                trial_available=False
            )
        else:
            # Check if trial is available
            trial_available = self._is_trial_available(pack_id)
            
            return OrderValidationResult(
                is_valid=False,
                pack_info=self._get_pack_info(pack_id) if trial_available else None,
                license=None,
                error_message=validation_result.get('error'),
                trial_available=trial_available
            )
    
    def start_trial(self, pack_id: str, customer_email: str = "") -> OrderValidationResult:
        """
        Start a trial for a Tailor Pack
        
        Args:
            pack_id: The pack ID to start trial for
            customer_email: Optional customer email
        
        Returns:
            OrderValidationResult with trial details
        """
        if not self._is_trial_available(pack_id):
            return OrderValidationResult(
                is_valid=False,
                pack_info=None,
                license=None,
                error_message="Trial not available for this pack or already used",
                trial_available=False
            )
        
        # Create trial license
        trial_order = f"TRIAL_{pack_id}_{int(time.time())}"
        trial_end = datetime.now() + timedelta(days=30)  # 30-day trial
        
        license = PackLicense(
            order_number=trial_order,
            pack_id=pack_id,
            license_key=f"TRIAL_{hashlib.md5(trial_order.encode()).hexdigest()[:16]}",
            customer_email=customer_email,
            purchase_date=datetime.now(),
            expiry_date=trial_end,
            license_type='trial',
            max_installations=1,
            current_installations=1,
            is_valid=True,
            features_enabled=self._get_trial_features(pack_id)
        )
        
        # Store trial and license
        self.trials[pack_id] = {
            'start_date': datetime.now(),
            'end_date': trial_end,
            'customer_email': customer_email,
            'trial_order': trial_order
        }
        
        self.licenses[trial_order] = license
        self._save_trials()
        self._save_licenses()
        
        return OrderValidationResult(
            is_valid=True,
            pack_info=self._get_pack_info(pack_id),
            license=license,
            error_message=None,
            trial_available=False
        )
    
    def _simulate_order_validation(self, order_number: str, pack_id: str) -> Dict:
        """
        Simulate order validation (replace with real API call in production)
        """
        # Mock validation logic based on order number format
        if len(order_number) < 10:
            return {
                'is_valid': False,
                'error': 'Invalid order number format'
            }
        
        # Simulate different order types
        if order_number.startswith('WF-'):
            # Valid Westfall order
            return {
                'is_valid': True,
                'license_key': f"LIC_{hashlib.md5(order_number.encode()).hexdigest()[:16]}",
                'customer_email': 'customer@example.com',
                'license_type': 'yearly',
                'max_installations': 3,
                'expiry_date': datetime.now() + timedelta(days=365),
                'features_enabled': self._get_full_features(pack_id)
            }
        elif order_number.startswith('WF-LIFE-'):
            # Lifetime license
            return {
                'is_valid': True,
                'license_key': f"LIC_{hashlib.md5(order_number.encode()).hexdigest()[:16]}",
                'customer_email': 'customer@example.com',
                'license_type': 'lifetime',
                'max_installations': 5,
                'expiry_date': None,
                'features_enabled': self._get_full_features(pack_id)
            }
        else:
            return {
                'is_valid': False,
                'error': 'Order number not found in our system'
            }
    
    def _is_license_valid(self, license: PackLicense) -> bool:
        """Check if a license is still valid"""
        if not license.is_valid:
            return False
        
        if license.expiry_date and datetime.now() > license.expiry_date:
            return False
        
        return True
    
    def _is_trial_available(self, pack_id: str) -> bool:
        """Check if trial is available for a pack"""
        # Check if trial was already used
        if pack_id in self.trials:
            return False
        
        # Check if pack supports trials
        pack_info = self._get_pack_info(pack_id)
        return pack_info and pack_info.get('trial_available', True)
    
    def _get_pack_info(self, pack_id: str) -> Optional[Dict]:
        """Get pack information (mock data)"""
        pack_catalog = {
            'marketing-essentials': {
                'name': 'Marketing Essentials',
                'description': 'Essential marketing tools for entrepreneurs',
                'price': '$19.99/month',
                'trial_available': True,
                'features': ['Campaign Tracking', 'Social Media Management', 'Lead Generation']
            },
            'sales-pipeline-pro': {
                'name': 'Sales Pipeline Pro',
                'description': 'Advanced sales pipeline management and CRM tools',
                'price': '$29.99/month',
                'trial_available': True,
                'features': ['Advanced CRM', 'Deal Tracking', 'Sales Analytics']
            },
            'finance-master': {
                'name': 'Finance Master',
                'description': 'Complete financial management suite',
                'price': '$39.99/month',
                'trial_available': True,
                'features': ['Advanced Accounting', 'Tax Preparation', 'Financial Planning']
            }
        }
        
        return pack_catalog.get(pack_id)
    
    def _get_full_features(self, pack_id: str) -> List[str]:
        """Get full feature list for a pack"""
        pack_info = self._get_pack_info(pack_id)
        return pack_info['features'] if pack_info else []
    
    def _get_trial_features(self, pack_id: str) -> List[str]:
        """Get limited feature list for trial"""
        full_features = self._get_full_features(pack_id)
        # Return limited features for trial (first 2 features)
        return full_features[:2] if len(full_features) > 2 else full_features
    
    def get_license_status(self, pack_id: str) -> Optional[PackLicense]:
        """Get license status for a specific pack"""
        for license in self.licenses.values():
            if license.pack_id == pack_id and self._is_license_valid(license):
                return license
        return None
    
    def get_trial_status(self, pack_id: str) -> Optional[Dict]:
        """Get trial status for a specific pack"""
        if pack_id in self.trials:
            trial_info = self.trials[pack_id].copy()
            trial_info['days_remaining'] = (trial_info['end_date'] - datetime.now()).days
            trial_info['is_active'] = trial_info['days_remaining'] > 0
            return trial_info
        return None
    
    def _generate_trial_key(self, pack_id: str) -> str:
        """Generate a trial license key for a pack"""
        import secrets
        timestamp = str(int(time.time()))
        random_suffix = secrets.token_hex(8)
        return f"TRIAL-{pack_id.upper()}-{timestamp}-{random_suffix}"
    
    def revoke_license(self, order_number: str) -> bool:
        """Revoke a license"""
        if order_number in self.licenses:
            self.licenses[order_number].is_valid = False
            self._save_licenses()
            return True
        return False


# Global instance
_order_verification_service = None

def get_order_verification_service() -> OrderVerificationService:
    """Get the global OrderVerificationService instance"""
    global _order_verification_service
    if _order_verification_service is None:
        _order_verification_service = OrderVerificationService()
    return _order_verification_service