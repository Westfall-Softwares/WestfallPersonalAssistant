#!/usr/bin/env python3
"""
Model Security Manager for Westfall Personal Assistant

Provides SHA-256 checksum verification, signature validation, and trusted sources
for AI models to ensure integrity and authenticity.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional dependencies with fallbacks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available - URL validation limited")

# For GPG signature verification (optional)
GPG_AVAILABLE = False
try:
    import gpg
    GPG_AVAILABLE = True
except ImportError:
    logger.info("GPG not available - signature verification disabled")


class ModelSecurityManager:
    """Manages model security including checksum verification and signature validation."""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.trusted_sources_file = self.config_dir / "trusted_model_sources.json"
        self.checksums_file = self.config_dir / "model_checksums.json"
        self.signatures_dir = self.config_dir / "model_signatures"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.signatures_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.trusted_sources = self._load_trusted_sources()
        self.model_checksums = self._load_model_checksums()
        
        # GPG context for signature verification
        self.gpg_context = None
        self._init_gpg()
    
    def _init_gpg(self):
        """Initialize GPG context for signature verification."""
        if not GPG_AVAILABLE:
            logger.info("GPG not available, signature verification disabled")
            return
            
        try:
            gpg_home = self.config_dir / "gpg"
            gpg_home.mkdir(exist_ok=True)
            self.gpg_context = gpg.Context(home_dir=str(gpg_home))
            logger.info("GPG context initialized for model signature verification")
        except Exception as e:
            logger.warning(f"GPG initialization failed: {e}. Signature verification will be disabled.")
    
    def _load_trusted_sources(self) -> Dict:
        """Load trusted model sources configuration."""
        default_sources = {
            "huggingface.co": {
                "enabled": True,
                "require_signature": False,
                "trusted_publishers": [
                    "microsoft",
                    "openai", 
                    "meta-llama",
                    "mistralai",
                    "google"
                ]
            },
            "ollama.ai": {
                "enabled": True,
                "require_signature": False,
                "trusted_publishers": []
            },
            "models.westfall-softwares.com": {
                "enabled": True,
                "require_signature": True,
                "trusted_publishers": ["westfall-softwares"]
            }
        }
        
        if self.trusted_sources_file.exists():
            try:
                with open(self.trusted_sources_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load trusted sources: {e}")
                return default_sources
        else:
            self._save_trusted_sources(default_sources)
            return default_sources
    
    def _save_trusted_sources(self, sources: Dict):
        """Save trusted sources configuration."""
        try:
            with open(self.trusted_sources_file, 'w') as f:
                json.dump(sources, f, indent=2)
            logger.info("Trusted sources configuration saved")
        except Exception as e:
            logger.error(f"Failed to save trusted sources: {e}")
    
    def _load_model_checksums(self) -> Dict:
        """Load known model checksums."""
        if self.checksums_file.exists():
            try:
                with open(self.checksums_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load model checksums: {e}")
                return {}
        return {}
    
    def _save_model_checksums(self):
        """Save model checksums to file."""
        try:
            with open(self.checksums_file, 'w') as f:
                json.dump(self.model_checksums, f, indent=2)
            logger.info("Model checksums saved")
        except Exception as e:
            logger.error(f"Failed to save model checksums: {e}")
    
    def calculate_file_checksum(self, file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        file_path = Path(file_path)
        
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            
            checksum = sha256_hash.hexdigest()
            logger.debug(f"Calculated checksum for {file_path.name}: {checksum}")
            return checksum
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise
    
    def verify_model_checksum(self, model_path: Union[str, Path], expected_checksum: str = None) -> bool:
        """Verify model file checksum against known good checksum."""
        model_path = Path(model_path)
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
        
        # Calculate actual checksum
        actual_checksum = self.calculate_file_checksum(model_path)
        
        # Use provided checksum or look up in database
        if expected_checksum is None:
            model_name = model_path.name
            expected_checksum = self.model_checksums.get(model_name)
            
            if expected_checksum is None:
                logger.warning(f"No known checksum for model {model_name}")
                # Store the calculated checksum for future reference
                self.store_model_checksum(model_name, actual_checksum)
                return True  # Allow unknown models but store their checksum
        
        # Verify checksum
        is_valid = actual_checksum == expected_checksum
        
        if is_valid:
            logger.info(f"Model checksum verified: {model_path.name}")
        else:
            logger.error(f"Model checksum mismatch for {model_path.name}. Expected: {expected_checksum}, Got: {actual_checksum}")
        
        return is_valid
    
    def store_model_checksum(self, model_name: str, checksum: str, source_url: str = None):
        """Store a model checksum in the database."""
        self.model_checksums[model_name] = {
            "checksum": checksum,
            "stored_at": datetime.now().isoformat(),
            "source_url": source_url
        }
        self._save_model_checksums()
        logger.info(f"Stored checksum for model: {model_name}")
    
    def verify_model_signature(self, model_path: Union[str, Path], signature_path: Union[str, Path] = None) -> bool:
        """Verify model GPG signature."""
        if self.gpg_context is None:
            logger.warning("GPG not available, skipping signature verification")
            return True  # Allow if GPG is not available
        
        model_path = Path(model_path)
        
        if signature_path is None:
            # Look for signature file with common extensions
            for ext in ['.sig', '.asc', '.gpg']:
                sig_path = model_path.with_suffix(model_path.suffix + ext)
                if sig_path.exists():
                    signature_path = sig_path
                    break
        
        if signature_path is None:
            logger.warning(f"No signature file found for {model_path}")
            return True  # Allow if no signature is found
        
        signature_path = Path(signature_path)
        
        try:
            with open(model_path, 'rb') as data_file, open(signature_path, 'rb') as sig_file:
                verified_data = self.gpg_context.verify(data_file, signature=sig_file)
                
                if verified_data.valid:
                    logger.info(f"Model signature verified: {model_path.name}")
                    return True
                else:
                    logger.error(f"Model signature verification failed: {model_path.name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error verifying signature for {model_path}: {e}")
            return False
    
    def is_source_trusted(self, source_url: str, publisher: str = None) -> bool:
        """Check if a model source is trusted."""
        try:
            parsed_url = urlparse(source_url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check if domain is in trusted sources
            source_config = self.trusted_sources.get(domain)
            if source_config is None:
                logger.warning(f"Unknown source domain: {domain}")
                return False
            
            if not source_config.get("enabled", False):
                logger.warning(f"Source disabled: {domain}")
                return False
            
            # Check publisher if specified
            if publisher is not None:
                trusted_publishers = source_config.get("trusted_publishers", [])
                if trusted_publishers and publisher.lower() not in [p.lower() for p in trusted_publishers]:
                    logger.warning(f"Untrusted publisher {publisher} for source {domain}")
                    return False
            
            logger.info(f"Source verified as trusted: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking source trust: {e}")
            return False
    
    def add_trusted_source(self, domain: str, require_signature: bool = False, trusted_publishers: List[str] = None):
        """Add a new trusted source."""
        if trusted_publishers is None:
            trusted_publishers = []
        
        self.trusted_sources[domain.lower()] = {
            "enabled": True,
            "require_signature": require_signature,
            "trusted_publishers": trusted_publishers
        }
        self._save_trusted_sources(self.trusted_sources)
        logger.info(f"Added trusted source: {domain}")
    
    def remove_trusted_source(self, domain: str):
        """Remove a trusted source."""
        domain = domain.lower()
        if domain in self.trusted_sources:
            del self.trusted_sources[domain]
            self._save_trusted_sources(self.trusted_sources)
            logger.info(f"Removed trusted source: {domain}")
    
    def validate_model_before_load(self, model_path: Union[str, Path], source_url: str = None, 
                                 publisher: str = None, expected_checksum: str = None) -> Dict:
        """Comprehensive model validation before loading."""
        model_path = Path(model_path)
        results = {
            "valid": True,
            "checksum_valid": False,
            "signature_valid": False,
            "source_trusted": False,
            "errors": [],
            "warnings": []
        }
        
        # Check if file exists
        if not model_path.exists():
            results["valid"] = False
            results["errors"].append(f"Model file not found: {model_path}")
            return results
        
        # Verify checksum
        try:
            results["checksum_valid"] = self.verify_model_checksum(model_path, expected_checksum)
            if not results["checksum_valid"]:
                results["errors"].append("Model checksum verification failed")
                results["valid"] = False
        except Exception as e:
            results["errors"].append(f"Checksum verification error: {e}")
            results["valid"] = False
        
        # Verify signature if available
        try:
            results["signature_valid"] = self.verify_model_signature(model_path)
            if not results["signature_valid"]:
                results["warnings"].append("Model signature verification failed")
        except Exception as e:
            results["warnings"].append(f"Signature verification error: {e}")
        
        # Check source trust
        if source_url:
            try:
                results["source_trusted"] = self.is_source_trusted(source_url, publisher)
                if not results["source_trusted"]:
                    results["warnings"].append("Model source is not trusted")
            except Exception as e:
                results["warnings"].append(f"Source trust check error: {e}")
        
        logger.info(f"Model validation complete for {model_path.name}: Valid={results['valid']}")
        return results
    
    def get_security_status(self) -> Dict:
        """Get current security configuration status."""
        return {
            "trusted_sources_count": len(self.trusted_sources),
            "known_checksums_count": len(self.model_checksums),
            "gpg_available": self.gpg_context is not None,
            "trusted_sources": list(self.trusted_sources.keys()),
            "config_dir": str(self.config_dir)
        }
    
    def import_trusted_checksums(self, checksums_file: Union[str, Path]):
        """Import checksums from an external file."""
        try:
            with open(checksums_file, 'r') as f:
                imported_checksums = json.load(f)
            
            # Merge with existing checksums
            self.model_checksums.update(imported_checksums)
            self._save_model_checksums()
            
            logger.info(f"Imported {len(imported_checksums)} checksums from {checksums_file}")
        except Exception as e:
            logger.error(f"Failed to import checksums: {e}")
            raise
    
    def export_checksums(self, output_file: Union[str, Path]):
        """Export known checksums to a file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.model_checksums, f, indent=2)
            logger.info(f"Exported checksums to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export checksums: {e}")
            raise