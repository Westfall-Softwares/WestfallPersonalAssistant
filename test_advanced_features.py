#!/usr/bin/env python3
"""
Test script for Advanced Features Implementation
Validates the core modules without requiring GUI dependencies
"""

import sys
import os
import tempfile
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_voice_control():
    """Test voice control module"""
    print("🎤 Testing Voice Control System...")
    
    try:
        from util.voice_control import get_voice_manager, VoiceCommand
        
        voice_manager = get_voice_manager()
        
        # Test basic functionality
        status = voice_manager.get_status()
        assert isinstance(status, dict)
        assert "enabled" in status
        print("  ✅ Voice manager initialized")
        
        # Test command processing
        result = voice_manager.process_command("open financial dashboard")
        assert result["action"] == "navigate"
        assert result["target"] == "dashboard"
        print("  ✅ Command processing working")
        
        # Test command list
        commands = voice_manager.get_available_commands()
        assert len(commands) > 0
        print("  ✅ Available commands retrieved")
        
        # Test voice profiles
        voice_manager.add_voice_profile("test_profile", {"language": "en-GB"})
        success = voice_manager.switch_voice_profile("test_profile")
        assert success
        print("  ✅ Voice profiles working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_marketplace_manager():
    """Test extension marketplace manager"""
    print("🛍️ Testing Extension Marketplace...")
    
    try:
        from util.marketplace_manager import get_marketplace_manager, ExtensionInfo
        
        marketplace = get_marketplace_manager()
        
        # Test search functionality
        results = marketplace.search_marketplace(query="voice")
        assert len(results) > 0
        assert isinstance(results[0], ExtensionInfo)
        print("  ✅ Marketplace search working")
        
        # Test extension verification
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            # Create mock extension file
            import zipfile
            import json
            
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                manifest = {
                    "id": "test-extension",
                    "name": "Test Extension",
                    "version": "1.0.0",
                    "author": "test",
                    "permissions": ["ui_integration"]
                }
                zip_file.writestr("manifest.json", json.dumps(manifest))
                
            verification = marketplace.verify_extension(tmp_file.name)
            assert isinstance(verification, dict)
            assert "valid" in verification
            print("  ✅ Extension verification working")
            
            os.unlink(tmp_file.name)
        
        # Test installation
        success = marketplace.install_extension("test-extension")
        assert success
        print("  ✅ Extension installation working")
        
        # Test installed extensions
        installed = marketplace.get_installed_extensions()
        assert len(installed) > 0
        print("  ✅ Installed extensions tracking working")
        
        # Test marketplace stats
        stats = marketplace.get_marketplace_stats()
        assert isinstance(stats, dict)
        assert "total_extensions" in stats
        print("  ✅ Marketplace statistics working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_template_exchange():
    """Test template exchange system"""
    print("📝 Testing Template Exchange System...")
    
    try:
        from util.template_exchange import get_template_manager, TemplateInfo
        
        template_manager = get_template_manager()
        
        # Test template creation
        template_id = template_manager.create_template(
            name="Test Invoice Template",
            category="business",
            content="Invoice for {{client_name}}\nAmount: {{amount}}\nDate: {{date}}",
            variables=[
                {"name": "client_name", "type": "text", "required": True},
                {"name": "amount", "type": "currency", "required": True},
                {"name": "date", "type": "date", "required": True}
            ],
            description="A simple invoice template",
            tags=["invoice", "business", "billing"]
        )
        assert template_id is not None
        print("  ✅ Template creation working")
        
        # Test template retrieval
        template_info = template_manager.get_template(template_id)
        assert template_info is not None
        assert template_info.name == "Test Invoice Template"
        print("  ✅ Template retrieval working")
        
        # Test template rendering
        rendered = template_manager.render_template(template_id, {
            "client_name": "John Doe",
            "amount": "$1,000.00",
            "date": "2024-01-01"
        })
        assert "John Doe" in rendered
        assert "$1,000.00" in rendered
        print("  ✅ Template rendering working")
        
        # Test template search
        results = template_manager.search_templates(query="invoice")
        assert len(results) > 0
        print("  ✅ Template search working")
        
        # Test template forking
        fork_id = template_manager.fork_template(template_id, "Forked Invoice")
        assert fork_id is not None
        assert fork_id != template_id
        print("  ✅ Template forking working")
        
        # Test template export
        export_path = template_manager.export_template(template_id)
        assert export_path is not None
        assert os.path.exists(export_path)
        print("  ✅ Template export working")
        
        # Test template import
        imported_id = template_manager.import_template(export_path)
        assert imported_id is not None
        print("  ✅ Template import working")
        
        # Test statistics
        stats = template_manager.get_template_statistics()
        assert isinstance(stats, dict)
        assert stats["total_templates"] > 0
        print("  ✅ Template statistics working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_api_gateway():
    """Test API gateway system"""
    print("🌐 Testing API Gateway...")
    
    try:
        from util.api_gateway import get_api_gateway, APIKey
        
        gateway = get_api_gateway()
        
        # Test API key creation
        api_key = gateway.create_api_key(
            service="test_service",
            name="Test API Key",
            permissions=["read", "write"]
        )
        assert isinstance(api_key, APIKey)
        assert api_key.service == "test_service"
        print("  ✅ API key creation working")
        
        # Test API request
        response = gateway.make_request(
            service="openai",
            endpoint="chat/completions",
            method="POST",
            data={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert isinstance(response, dict)
        assert "success" in response
        print("  ✅ API request handling working")
        
        # Test rate limiting
        rate_limit_key = "test_service"
        allowed = gateway.rate_limiter.is_allowed(rate_limit_key, 1)
        assert allowed == True
        
        # Second request should be blocked
        allowed = gateway.rate_limiter.is_allowed(rate_limit_key, 1)
        assert allowed == False
        print("  ✅ Rate limiting working")
        
        # Test service health
        health = gateway.get_service_health("openai")
        assert isinstance(health, dict)
        assert "status" in health
        print("  ✅ Service health monitoring working")
        
        # Test usage analytics
        analytics = gateway.get_usage_analytics()
        assert isinstance(analytics, dict)
        assert "total_requests" in analytics
        print("  ✅ Usage analytics working")
        
        # Test API key usage
        key_usage = gateway.get_api_key_usage(api_key.key_id)
        assert isinstance(key_usage, dict)
        assert "key_id" in key_usage
        print("  ✅ API key usage tracking working")
        
        # Test gateway status
        status = gateway.get_gateway_status()
        assert isinstance(status, dict)
        assert "gateway_version" in status
        print("  ✅ Gateway status reporting working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_integration():
    """Test integration between modules"""
    print("🔗 Testing Module Integration...")
    
    try:
        # Test that all managers can be imported together
        from util.voice_control import get_voice_manager
        from util.marketplace_manager import get_marketplace_manager
        from util.template_exchange import get_template_manager
        from util.api_gateway import get_api_gateway
        
        voice_manager = get_voice_manager()
        marketplace = get_marketplace_manager()
        template_manager = get_template_manager()
        gateway = get_api_gateway()
        
        # Test basic integration scenario
        # Voice command to create template
        command_result = voice_manager.process_command("create new invoice")
        assert command_result["action"] == "create"
        
        # Search for related templates
        templates = template_manager.search_templates(query="invoice")
        
        # Check marketplace for extensions
        extensions = marketplace.search_marketplace(category="business")
        assert len(extensions) > 0
        
        # Test API gateway with multiple services
        openai_response = gateway.make_request("openai", "chat/completions")
        weather_response = gateway.make_request("weather", "weather")
        
        assert openai_response["success"]
        assert weather_response["success"]
        
        print("  ✅ Cross-module integration working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Advanced Features Implementation")
    print("=" * 60)
    
    tests = [
        ("Voice Control", test_voice_control),
        ("Marketplace Manager", test_marketplace_manager),
        ("Template Exchange", test_template_exchange),
        ("API Gateway", test_api_gateway),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            success = test_func()
            execution_time = time.time() - start_time
            results[test_name] = {
                "success": success,
                "time": execution_time,
                "error": None
            }
            
            if success:
                print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
            else:
                print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
                
        except Exception as e:
            execution_time = time.time() - start_time
            results[test_name] = {
                "success": False,
                "time": execution_time,
                "error": str(e)
            }
            print(f"💥 {test_name} CRASHED: {e} ({execution_time:.2f}s)")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    total_time = sum(r["time"] for r in results.values())
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Total Time: {total_time:.2f}s")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Advanced features foundation is ready!")
        return 0
    else:
        print(f"\n⚠️  {total-passed} tests failed - review implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())