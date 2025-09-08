#!/usr/bin/env python3
"""
Demonstration of Advanced Features Implementation
Shows the capabilities of the new Phase 1 modules
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_voice_control():
    """Demonstrate voice control capabilities"""
    print("\n🎤 VOICE CONTROL SYSTEM DEMO")
    print("=" * 50)
    
    from util.voice_control import get_voice_manager
    
    voice_manager = get_voice_manager()
    
    print("📋 Voice Control Status:")
    status = voice_manager.get_status()
    for key, value in status.items():
        if key != "settings":
            print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    print("\n🗣️ Available Voice Commands:")
    commands = voice_manager.get_available_commands()
    for i, command in enumerate(commands, 1):
        print(f"  {i:2d}. {command}")
    
    print("\n🧪 Testing Command Processing:")
    test_commands = [
        "open financial dashboard",
        "create new invoice", 
        "what's my profit margin",
        "stop listening"
    ]
    
    for command in test_commands:
        result = voice_manager.process_command(command)
        print(f"  Command: '{command}'")
        print(f"  Result:  {result['action']} → {result.get('target', result.get('type', 'N/A'))}")
        print()

def demo_marketplace():
    """Demonstrate marketplace capabilities"""
    print("\n🛍️ EXTENSION MARKETPLACE DEMO")
    print("=" * 50)
    
    from util.marketplace_manager import get_marketplace_manager
    
    marketplace = get_marketplace_manager()
    
    print("📊 Marketplace Statistics:")
    stats = marketplace.get_marketplace_stats()
    print(f"  • Total Extensions: {stats['total_extensions']}")
    print(f"  • Installed: {stats['installed_count']}")
    print(f"  • Enabled: {stats['enabled_count']}")
    
    print("\n📱 Available Extensions:")
    extensions = marketplace.search_marketplace()[:3]  # Show first 3
    for ext in extensions:
        print(f"  • {ext.name} v{ext.version}")
        print(f"    Author: {ext.author} | Rating: ⭐{ext.rating}")
        print(f"    Category: {ext.category} | Downloads: {ext.download_count:,}")
        print(f"    Description: {ext.description}")
        print()
    
    print("🔧 Testing Extension Installation:")
    success = marketplace.install_extension("test-extension")
    print(f"  Installation Result: {'✅ Success' if success else '❌ Failed'}")
    
    installed = marketplace.get_installed_extensions()
    print(f"  Installed Extensions: {len(installed)}")
    for ext in installed:
        status = "🟢 Enabled" if ext.enabled else "🔴 Disabled"
        print(f"    • {ext.name} - {status}")

def demo_templates():
    """Demonstrate template exchange capabilities"""
    print("\n📋 TEMPLATE EXCHANGE DEMO")
    print("=" * 50)
    
    from util.template_exchange import get_template_manager
    
    template_manager = get_template_manager()
    
    print("📊 Template Statistics:")
    stats = template_manager.get_template_statistics()
    print(f"  • Total Templates: {stats['total_templates']}")
    print(f"  • Categories: {len(stats['categories'])}")
    print(f"  • Public Templates: {stats['public_templates']}")
    print(f"  • Forked Templates: {stats['forked_templates']}")
    
    print("\n📝 Available Templates:")
    for template_id, template_info in list(template_manager.local_templates.items())[:3]:
        print(f"  • {template_info.name}")
        print(f"    Category: {template_info.category} | Version: {template_info.version}")
        print(f"    Variables: {len(template_info.variables)} | Tags: {', '.join(template_info.tags)}")
        print(f"    Created: {template_info.created_date.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    print("🧪 Testing Template Operations:")
    # Find an existing template to demonstrate
    if template_manager.local_templates:
        template_id = list(template_manager.local_templates.keys())[0]
        template_info = template_manager.get_template(template_id)
        
        print(f"  Template: {template_info.name}")
        
        # Test rendering with sample data
        sample_vars = {
            "client_name": "Demo Client",
            "amount": "$5,000.00",
            "date": "2024-01-15"
        }
        
        rendered = template_manager.render_template(template_id, sample_vars)
        if rendered:
            print("  Rendered Preview:")
            print("  " + "─" * 40)
            for line in rendered.split('\n')[:5]:  # Show first 5 lines
                print(f"  {line}")
            print("  " + "─" * 40)
        
        # Test forking
        fork_id = template_manager.fork_template(template_id, "Demo Fork")
        print(f"  Fork Created: {'✅ Success' if fork_id else '❌ Failed'}")
        
        # Test export
        export_path = template_manager.export_template(template_id)
        print(f"  Export: {'✅ Success' if export_path else '❌ Failed'}")
        if export_path:
            file_size = os.path.getsize(export_path) / 1024  # KB
            print(f"    File: {os.path.basename(export_path)} ({file_size:.1f} KB)")

def demo_api_gateway():
    """Demonstrate API gateway capabilities"""
    print("\n🌐 API GATEWAY DEMO")
    print("=" * 50)
    
    from util.api_gateway import get_api_gateway
    
    gateway = get_api_gateway()
    
    print("📊 Gateway Status:")
    status = gateway.get_gateway_status()
    print(f"  • Gateway Version: {status['gateway_version']}")
    print(f"  • Active API Keys: {status['active_api_keys']}/{status['total_api_keys']}")
    print(f"  • Total Requests: {status['total_requests']}")
    
    print("\n🔑 API Keys:")
    for key_id, api_key in list(gateway.api_keys.items())[:3]:
        status_icon = "🟢" if api_key.is_active else "🔴"
        print(f"  {status_icon} {api_key.name} ({api_key.service})")
        print(f"     Usage: {api_key.usage_count} requests | Rate Limit: {api_key.rate_limit}/hour")
    
    print("\n🏥 Service Health:")
    services = ["openai", "weather", "news", "email"]
    for service in services:
        health = gateway.get_service_health(service)
        status_icon = "🟢" if health['status'] == "healthy" else "🟡" if health['status'] == "degraded" else "🔴"
        print(f"  {status_icon} {service.upper()}: {health['status']}")
        print(f"     Success Rate: {health['success_rate']:.1f}% | Avg Response: {health['average_response_time']:.2f}s")
    
    print("\n🧪 Testing API Requests:")
    test_requests = [
        ("openai", "chat/completions"),
        ("weather", "weather"),
        ("news", "top-headlines")
    ]
    
    for service, endpoint in test_requests:
        response = gateway.make_request(service, endpoint)
        status = "✅ Success" if response['success'] else "❌ Failed"
        print(f"  {service.upper()} {endpoint}: {status}")
        if not response['success']:
            print(f"    Error: {response['error']}")

def demo_integration():
    """Demonstrate cross-module integration"""
    print("\n🔗 INTEGRATION DEMO")
    print("=" * 50)
    
    # Show how modules work together
    from util.voice_control import get_voice_manager
    from util.marketplace_manager import get_marketplace_manager
    from util.template_exchange import get_template_manager
    from util.api_gateway import get_api_gateway
    
    print("🤖 Voice-Activated Template Creation:")
    voice_manager = get_voice_manager()
    template_manager = get_template_manager()
    
    # Simulate voice command to create template
    command_result = voice_manager.process_command("create new invoice")
    print(f"  Voice Command: 'create new invoice'")
    print(f"  Processed As: {command_result['action']} → {command_result.get('type', 'N/A')}")
    
    # Show templates that could be used
    invoice_templates = template_manager.search_templates(query="invoice")
    print(f"  Available Invoice Templates: {len(invoice_templates)}")
    
    print("\n🛍️ AI-Powered Extension Recommendations:")
    marketplace = get_marketplace_manager()
    ai_extensions = marketplace.search_marketplace(category="ai")
    print(f"  AI Extensions Available: {len(ai_extensions)}")
    for ext in ai_extensions[:2]:
        print(f"    • {ext.name} - {ext.description}")
    
    print("\n🌐 API Integration Example:")
    gateway = get_api_gateway()
    
    # Example: Voice command triggers API call
    print("  Scenario: Voice asks 'What's the weather?'")
    weather_response = gateway.make_request("weather", "weather")
    print(f"  API Call Result: {'✅ Success' if weather_response['success'] else '❌ Failed'}")
    
    # Show usage analytics
    analytics = gateway.get_usage_analytics(hours=1)
    print(f"  API Usage (Last Hour): {analytics['total_requests']} requests")
    print(f"  Success Rate: {analytics['success_rate']:.1f}%")

def main():
    """Run the complete demonstration"""
    print("🚀 WESTFALL PERSONAL ASSISTANT")
    print("🔥 ADVANCED FEATURES DEMONSTRATION")
    print("=" * 60)
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print()
    
    demos = [
        ("Voice Control System", demo_voice_control),
        ("Extension Marketplace", demo_marketplace), 
        ("Template Exchange", demo_templates),
        ("API Gateway", demo_api_gateway),
        ("Cross-Module Integration", demo_integration)
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
            print(f"\n✅ {demo_name} demo completed successfully")
        except Exception as e:
            print(f"\n❌ {demo_name} demo failed: {str(e)}")
        
        time.sleep(0.5)  # Brief pause between demos
    
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRATION COMPLETE")
    print("\n🏗️ Phase 1 Foundation Features:")
    print("  ✅ Voice Control System - Ready for speech recognition integration")
    print("  ✅ Extension Marketplace - Ready for plugin ecosystem")
    print("  ✅ Template Exchange - Ready for document automation")  
    print("  ✅ API Gateway - Ready for external service integration")
    print("\n🚀 Next: Phase 2 - Business Intelligence Features")
    print("  📊 Business Network Graph")
    print("  🤖 Automated Proposal Generation")
    print("  📈 Market Opportunity Detection")
    print("  💡 Personalized Business Intelligence")
    print("  🎯 Client Success Predictions")

if __name__ == "__main__":
    main()