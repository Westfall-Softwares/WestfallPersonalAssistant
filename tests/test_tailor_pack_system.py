#!/usr/bin/env python3
"""
Testing Infrastructure for Tailor Pack System
Provides unit and integration tests for core functionality
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from utils.tailor_pack_manager import TailorPackManager, TailorPackManifest
from utils.pack_extension_system import (
    PackExtensionManager, FeatureRegistry, UIExtensionRegistry,
    PackCapability, UIComponent, UIExtensionPoint
)
from utils.order_verification import OrderVerificationService, PackLicense, OrderValidationResult


class TestTailorPackManager(unittest.TestCase):
    """Test cases for TailorPackManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.pack_manager = TailorPackManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_manifest_validation(self):
        """Test manifest validation"""
        # Valid manifest
        valid_manifest = {
            "pack_id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "A test pack",
            "author": "Test Author",
            "target_audience": "entrepreneur",
            "business_category": "marketing",
            "features": ["feature1", "feature2"]
        }
        
        result = self.pack_manager._validate_manifest(valid_manifest)
        self.assertTrue(result["valid"])
        
        # Invalid manifest - missing required field
        invalid_manifest = valid_manifest.copy()
        del invalid_manifest["pack_id"]
        
        result = self.pack_manager._validate_manifest(invalid_manifest)
        self.assertFalse(result["valid"])
        self.assertIn("Missing required field", result["error"])
    
    def test_version_compatibility(self):
        """Test version compatibility checking"""
        # Test compatible versions
        self.assertTrue(self.pack_manager._is_version_compatible("1.0.0"))
        self.assertTrue(self.pack_manager._is_version_compatible("0.9.0"))
        
        # Test incompatible versions (future versions)
        self.assertFalse(self.pack_manager._is_version_compatible("2.0.0"))
    
    def test_dependency_resolution(self):
        """Test dependency resolution"""
        # Create mock installed packs
        self.pack_manager.installed_packs = {
            "dep1": Mock(dependencies=[], enabled=True, version="1.0.0"),
            "dep2": Mock(dependencies=[], enabled=True, version="2.0.0")
        }
        
        # Test simple dependencies
        missing = self.pack_manager._check_dependencies(["dep1", "dep2"])
        self.assertEqual(len(missing), 0)
        
        # Test missing dependency
        missing = self.pack_manager._check_dependencies(["dep1", "missing_dep"])
        self.assertEqual(len(missing), 1)
        self.assertIn("missing_dep", missing[0])
    
    def test_pack_statistics(self):
        """Test pack statistics generation"""
        # Add mock packs
        mock_pack1 = Mock(
            business_category="marketing",
            target_audience="entrepreneur",
            license_required=True,
            pack_id="pack1"
        )
        mock_pack2 = Mock(
            business_category="finance",
            target_audience="small_business",
            license_required=False,
            pack_id="pack2"
        )
        
        self.pack_manager.installed_packs = {
            "pack1": mock_pack1,
            "pack2": mock_pack2
        }
        
        # Mock directory size calculation
        with patch.object(self.pack_manager, '_get_directory_size', return_value=1024):
            stats = self.pack_manager.get_pack_statistics()
        
        self.assertEqual(stats["total_installed"], 2)
        self.assertEqual(stats["categories"]["marketing"], 1)
        self.assertEqual(stats["categories"]["finance"], 1)
        self.assertEqual(stats["licensed_packs"], 1)


class TestPackExtensionSystem(unittest.TestCase):
    """Test cases for Pack Extension System"""
    
    def setUp(self):
        """Set up test environment"""
        self.extension_manager = PackExtensionManager()
    
    def test_feature_registry(self):
        """Test feature registry functionality"""
        registry = self.extension_manager.feature_registry
        
        # Create test capability
        capability = PackCapability(
            pack_id="test-pack",
            capability_id="test-capability",
            name="Test Capability",
            description="A test capability",
            category="testing"
        )
        
        # Register capability
        result = registry.register_capability(capability)
        self.assertTrue(result)
        
        # Check registration
        capabilities = registry.get_pack_capabilities("test-pack")
        self.assertEqual(len(capabilities), 1)
        self.assertEqual(capabilities[0].name, "Test Capability")
        
        # Test category retrieval
        category_caps = registry.get_capabilities_by_category("testing")
        self.assertEqual(len(category_caps), 1)
    
    def test_ui_extension_registry(self):
        """Test UI extension registry"""
        registry = self.extension_manager.ui_registry
        
        # Create test component
        component = UIComponent(
            pack_id="test-pack",
            component_id="test-component",
            extension_point="business_dashboard_widgets",
            component_class="TestWidget",
            priority=50
        )
        
        # Register component
        result = registry.register_ui_component(component)
        self.assertTrue(result)
        
        # Check registration
        components = registry.get_extension_point_components("business_dashboard_widgets")
        self.assertEqual(len(components), 1)
        
        # Test enabled components
        enabled = registry.get_enabled_components("business_dashboard_widgets")
        self.assertEqual(len(enabled), 1)
        
        # Test disable/enable
        registry.disable_component("test-pack", "test-component")
        enabled = registry.get_enabled_components("business_dashboard_widgets")
        self.assertEqual(len(enabled), 0)
    
    def test_extension_points(self):
        """Test default extension points"""
        registry = self.extension_manager.ui_registry
        
        # Check default extension points exist
        self.assertIn("business_dashboard_widgets", registry.extension_points)
        self.assertIn("navigation_menu_items", registry.extension_points)
        self.assertIn("report_generators", registry.extension_points)
        
        # Test extension point properties
        dashboard_point = registry.extension_points["business_dashboard_widgets"]
        self.assertEqual(dashboard_point.component_type, "dashboard_widget")
        self.assertEqual(dashboard_point.max_components, 8)


class TestOrderVerificationService(unittest.TestCase):
    """Test cases for Order Verification Service"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        # Mock the data directory
        self.original_license_file = None
        
        # Create a temporary order service
        self.order_service = OrderVerificationService()
        # Override the license file path for testing
        self.order_service.local_license_file = os.path.join(self.test_dir, "test_licenses.json")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_order_format_validation(self):
        """Test order number format validation"""
        # Valid formats
        self.assertTrue(self.order_service._is_valid_order_format("WF-12345678"))
        self.assertTrue(self.order_service._is_valid_order_format("TRIAL-test-pack-123456"))
        self.assertTrue(self.order_service._is_valid_order_format("ABC123DEF"))
        
        # Invalid formats
        self.assertFalse(self.order_service._is_valid_order_format("123"))
        self.assertFalse(self.order_service._is_valid_order_format(""))
        self.assertFalse(self.order_service._is_valid_order_format("AB"))
    
    def test_trial_license_generation(self):
        """Test trial license generation"""
        result = self.order_service.start_trial("test-pack", "test@example.com")
        
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.license)
        self.assertEqual(result.license.license_type, "trial")
        self.assertEqual(result.license.pack_id, "test-pack")
        self.assertIsNotNone(result.license.expiry_date)
    
    def test_license_storage_and_retrieval(self):
        """Test license storage and retrieval"""
        # Create test license
        license = PackLicense(
            order_number="TEST-123",
            pack_id="test-pack",
            license_key="TEST-KEY",
            customer_email="test@example.com",
            purchase_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            license_type="monthly",
            max_installations=1,
            current_installations=1,
            is_valid=True,
            features_enabled=["feature1", "feature2"]
        )
        
        # Store license
        self.order_service._store_local_license(license)
        
        # Retrieve license
        retrieved = self.order_service._get_local_license("TEST-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.pack_id, "test-pack")
        self.assertEqual(retrieved.license_type, "monthly")
    
    def test_license_expiry(self):
        """Test license expiry checking"""
        # Non-expired license
        valid_license = PackLicense(
            order_number="VALID-123",
            pack_id="test-pack",
            license_key="VALID-KEY",
            customer_email="test@example.com",
            purchase_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            license_type="monthly",
            max_installations=1,
            current_installations=1,
            is_valid=True,
            features_enabled=[]
        )
        
        self.assertFalse(self.order_service._is_license_expired(valid_license))
        
        # Expired license
        expired_license = PackLicense(
            order_number="EXPIRED-123",
            pack_id="test-pack",
            license_key="EXPIRED-KEY",
            customer_email="test@example.com",
            purchase_date=datetime.now() - timedelta(days=60),
            expiry_date=datetime.now() - timedelta(days=30),
            license_type="monthly",
            max_installations=1,
            current_installations=1,
            is_valid=True,
            features_enabled=[]
        )
        
        self.assertTrue(self.order_service._is_license_expired(expired_license))
        
        # Lifetime license (no expiry)
        lifetime_license = PackLicense(
            order_number="LIFETIME-123",
            pack_id="test-pack",
            license_key="LIFETIME-KEY",
            customer_email="test@example.com",
            purchase_date=datetime.now(),
            expiry_date=None,
            license_type="lifetime",
            max_installations=1,
            current_installations=1,
            is_valid=True,
            features_enabled=[]
        )
        
        self.assertFalse(self.order_service._is_license_expired(lifetime_license))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.pack_manager = TailorPackManager(self.test_dir)
        self.extension_manager = PackExtensionManager()
        self.order_service = OrderVerificationService()
        self.order_service.local_license_file = os.path.join(self.test_dir, "integration_licenses.json")
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_pack_workflow(self):
        """Test complete pack installation and activation workflow"""
        # 1. Start with trial license
        trial_result = self.order_service.start_trial("integration-pack", "test@example.com")
        self.assertTrue(trial_result.is_valid)
        
        # 2. Mock pack installation (would normally be ZIP import)
        manifest = {
            "pack_id": "integration-pack",
            "name": "Integration Test Pack",
            "version": "1.0.0",
            "description": "A pack for integration testing",
            "author": "Test Author",
            "target_audience": "entrepreneur",
            "business_category": "other",  # Changed from "testing" to "other"
            "features": ["test-feature-1", "test-feature-2"],
            "dependencies": []
        }
        
        # Validate manifest
        validation_result = self.pack_manager._validate_manifest(manifest)
        self.assertTrue(validation_result["valid"])
        
        # 3. Register pack capabilities
        capability = PackCapability(
            pack_id="integration-pack",
            capability_id="test-capability",
            name="Test Capability",
            description="Integration test capability",
            category="testing"
        )
        
        result = self.extension_manager.feature_registry.register_capability(capability)
        self.assertTrue(result)
        
        # 4. Register UI components
        component = UIComponent(
            pack_id="integration-pack",
            component_id="test-widget",
            extension_point="business_dashboard_widgets",
            component_class="TestWidget"
        )
        
        result = self.extension_manager.ui_registry.register_ui_component(component)
        self.assertTrue(result)
        
        # 5. Mock the pack as loaded (since we're not actually loading an extension file)
        self.extension_manager.loaded_extensions["integration-pack"] = Mock()
        
        # Verify complete integration
        pack_status = self.extension_manager.get_pack_status("integration-pack")
        self.assertTrue(pack_status["loaded"])
        self.assertEqual(pack_status["capabilities_count"], 1)
        
        license_status = self.order_service.get_license_status("integration-pack")
        self.assertTrue(license_status["licensed"])
        self.assertEqual(license_status["license_type"], "trial")


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestTailorPackManager))
    test_suite.addTest(unittest.makeSuite(TestPackExtensionSystem))
    test_suite.addTest(unittest.makeSuite(TestOrderVerificationService))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)