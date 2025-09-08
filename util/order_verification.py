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