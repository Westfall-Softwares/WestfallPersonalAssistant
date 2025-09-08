#!/usr/bin/env python3
"""
Test script for Windows 10 optimizations and features
Validates all implemented Windows-specific functionality
"""

import sys
import os
import time
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_windows_optimizations():
    """Test Windows optimization module"""
    print("🔧 Testing Windows Optimizations...")
    print("-" * 40)
    
    try:
        from util.windows_optimizations import (
            get_windows_optimization_manager,
            is_windows_10_or_later,
            optimize_for_windows_10
        )
        
        # Test platform detection
        print(f"Windows 10+ detected: {is_windows_10_or_later()}")
        
        # Test optimization manager
        manager = get_windows_optimization_manager()
        print(f"Optimization manager created: {manager is not None}")
        
        # Test optimization status
        status = manager.get_optimization_status()
        print("Optimization Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test individual components
        print("\nTesting Components:")
        
        # Memory manager
        memory_stats = manager.memory_manager.get_memory_stats()
        print(f"  Memory stats: {len(memory_stats)} metrics")
        
        # Theme detector
        current_theme = manager.theme_detector.get_current_theme()
        print(f"  Current theme: {current_theme}")
        
        # Hardware detector
        gpu_config = manager.hardware_detector.get_acceleration_config()
        print(f"  GPU acceleration: {gpu_config.get('use_gpu', False)}")
        
        # Power manager
        power_status = manager.power_manager.get_power_status()
        print(f"  Power plans: {power_status.get('plans_count', 0)}")
        
        print("✅ Windows Optimizations: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Windows Optimizations: FAILED - {e}")
        return False


def test_windows_system_monitor():
    """Test Windows system monitoring"""
    print("\n🖥️ Testing Windows System Monitor...")
    print("-" * 40)
    
    try:
        from util.windows_system_monitor import (
            WindowsPerformanceMonitor,
            WindowsSystemOptimizer,
            enhance_resource_manager
        )
        
        # Test performance monitor
        monitor = WindowsPerformanceMonitor()
        print(f"Performance monitor created: {monitor is not None}")
        
        # Test metrics collection
        metrics = monitor.get_performance_metrics()
        print(f"Performance metrics collected: {len(metrics)} metrics")
        for key, value in list(metrics.items())[:5]:  # Show first 5
            print(f"  {key}: {value}")
        
        # Test startup analysis
        startup_analysis = monitor.get_startup_impact_analysis()
        total_programs = (
            len(startup_analysis.get('high_impact_programs', [])) +
            len(startup_analysis.get('medium_impact_programs', [])) +
            len(startup_analysis.get('low_impact_programs', []))
        )
        print(f"Startup programs analyzed: {total_programs}")
        print(f"Estimated startup delay: {startup_analysis.get('total_startup_delay', 0):.1f}s")
        
        # Test system optimizer
        optimizer = WindowsSystemOptimizer()
        print(f"System optimizer created: {optimizer is not None}")
        
        # Test resource manager enhancement
        enhancement_success = enhance_resource_manager()
        print(f"Resource manager enhanced: {enhancement_success}")
        
        print("✅ Windows System Monitor: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Windows System Monitor: FAILED - {e}")
        return False


def test_task_automation():
    """Test task automation and productivity features"""
    print("\n📋 Testing Task Automation...")
    print("-" * 40)
    
    try:
        from util.task_automation import (
            get_productivity_manager,
            PersonalTaskTemplateManager,
            QuickCaptureManager,
            AutomationRecipeManager
        )
        
        # Test productivity manager
        manager = get_productivity_manager()
        print(f"Productivity manager created: {manager is not None}")
        
        # Initialize
        init_results = manager.initialize()
        print("Initialization results:")
        for key, value in init_results.items():
            print(f"  {key}: {value}")
        
        # Test template manager
        template_manager = manager.template_manager
        print(f"Templates loaded: {len(template_manager.templates)}")
        
        # Test template creation
        success = template_manager.create_template(
            "Test Template",
            "testing",
            {
                'title': 'Test Task - {date}',
                'description': 'Created at {time}',
                'tags': ['test', 'automation']
            }
        )
        print(f"Template creation: {'✅' if success else '❌'}")
        
        # Test template usage
        result = template_manager.use_template("Test Template")
        print(f"Template usage: {'✅' if result else '❌'}")
        
        # Test analytics
        analytics = template_manager.get_template_analytics()
        print(f"Template analytics: {analytics.get('total_templates', 0)} templates")
        
        # Test quick capture (without actual hotkeys)
        capture_manager = manager.quick_capture
        print(f"Quick capture manager: {capture_manager is not None}")
        
        # Test automation recipes
        automation_manager = manager.automation_manager
        print(f"Automation recipes: {len(automation_manager.recipes)}")
        
        # Get productivity summary
        summary = manager.get_productivity_summary()
        print("Productivity summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print("✅ Task Automation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Task Automation: FAILED - {e}")
        return False


def test_local_ai_optimization():
    """Test local AI optimization and personalization"""
    print("\n🤖 Testing Local AI Optimization...")
    print("-" * 40)
    
    try:
        from util.local_ai_optimization import (
            get_local_ai_manager,
            AIModelOptimizer,
            AIModelHotSwapper,
            PersonalizationEngine
        )
        
        # Test AI manager
        manager = get_local_ai_manager()
        print(f"AI manager created: {manager is not None}")
        
        # Initialize
        init_results = manager.initialize()
        print("Initialization results:")
        for key, value in init_results.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
        
        # Test model optimizer
        optimizer = manager.model_optimizer
        print(f"Model optimizer ready: {optimizer is not None}")
        
        # Test system specs detection
        system_specs = manager._get_system_specs()
        print("System specifications:")
        for key, value in system_specs.items():
            print(f"  {key}: {value}")
        
        # Test model optimization (with mock model)
        test_model_path = "/mock/model/path.gguf"
        optimization_config = manager.optimize_model(test_model_path)
        print("Model optimization config:")
        for key, value in optimization_config.items():
            print(f"  {key}: {value}")
        
        # Test hot swapper
        hot_swapper = manager.model_hot_swapper
        memory_summary = hot_swapper.get_memory_usage_summary()
        print(f"Hot swapper memory usage: {memory_summary}")
        
        # Test personalization engine
        personalization = manager.personalization_engine
        print(f"Personalization engine ready: {personalization is not None}")
        
        # Test user interaction recording
        manager.record_user_interaction(
            "test_interaction",
            "Test context for optimization",
            "This is a test response",
            0.8
        )
        print("User interaction recorded ✅")
        
        # Test personalized suggestions
        suggestions = manager.get_personalized_suggestions("I need help with testing")
        print(f"Personalized suggestions: {len(suggestions)} suggestions")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. {suggestion}")
        
        # Get AI status summary
        status = manager.get_ai_status_summary()
        print("AI Status Summary:")
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
        
        print("✅ Local AI Optimization: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Local AI Optimization: FAILED - {e}")
        return False


def test_enhanced_platform_compatibility():
    """Test enhanced platform compatibility"""
    print("\n🔌 Testing Enhanced Platform Compatibility...")
    print("-" * 40)
    
    try:
        from backend.platform_compatibility import get_platform_manager
        
        # Test platform manager
        platform_manager = get_platform_manager()
        print(f"Platform manager created: {platform_manager is not None}")
        
        # Test platform info
        platform_info = platform_manager.platform_info
        print(f"Platform: {platform_info.platform.value}")
        print(f"Architecture: {platform_info.architecture.value}")
        
        # Test Windows-specific capabilities
        if platform_info.is_windows():
            capabilities = [
                'windows_hello',
                'action_center',
                'jump_lists',
                'credential_manager',
                'memory_compression',
                'hardware_acceleration',
                'dark_theme_api'
            ]
            
            print("Windows 10 capabilities:")
            for capability in capabilities:
                available = platform_info.has_capability(capability)
                print(f"  {capability}: {'✅' if available else '❌'}")
        
        # Test notification manager
        notification_manager = platform_manager.notification_manager
        print(f"Notification manager ready: {notification_manager is not None}")
        
        # Test enhanced notification (dry run)
        print("Testing enhanced Windows notifications...")
        # Note: We can't actually test notifications in headless environment
        
        print("✅ Enhanced Platform Compatibility: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Platform Compatibility: FAILED - {e}")
        return False


def test_integration():
    """Test integration between all modules"""
    print("\n🔗 Testing Module Integration...")
    print("-" * 40)
    
    try:
        # Test that all managers can be created together
        from util.windows_optimizations import get_windows_optimization_manager
        from util.task_automation import get_productivity_manager
        from util.local_ai_optimization import get_local_ai_manager
        from backend.platform_compatibility import get_platform_manager
        
        managers = {
            'windows_optimization': get_windows_optimization_manager(),
            'productivity': get_productivity_manager(),
            'local_ai': get_local_ai_manager(),
            'platform': get_platform_manager()
        }
        
        print("Manager integration:")
        for name, manager in managers.items():
            print(f"  {name}: {'✅' if manager is not None else '❌'}")
        
        # Test cross-manager communication
        print("\nTesting cross-manager features:")
        
        # Windows optimization + AI optimization
        windows_manager = managers['windows_optimization']
        ai_manager = managers['local_ai']
        
        # Get system specs for AI optimization
        system_specs = ai_manager._get_system_specs()
        windows_status = windows_manager.get_optimization_status()
        
        # Combine information
        combined_info = {
            'hardware_acceleration': (
                system_specs.get('gpu_available', False) and
                windows_status.get('hardware_acceleration', False)
            ),
            'memory_optimization': (
                windows_status.get('memory_compression', False) or
                system_specs.get('available_memory_gb', 0) > 8
            ),
            'performance_mode': windows_status.get('power_plan', 'balanced')
        }
        
        print("Combined optimization info:")
        for key, value in combined_info.items():
            print(f"  {key}: {value}")
        
        # Productivity + AI personalization
        productivity_manager = managers['productivity']
        productivity_summary = productivity_manager.get_productivity_summary()
        ai_status = ai_manager.get_ai_status_summary()
        
        integration_score = (
            productivity_summary.get('templates', {}).get('total_usage', 0) +
            ai_status.get('personalization', {}).get('total_interactions', 0)
        ) / 10.0
        
        print(f"Integration score: {integration_score:.1f}")
        
        print("✅ Module Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Module Integration: FAILED - {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive test of all Windows optimization features"""
    print("🚀 Westfall Personal Assistant - Windows 10 Optimizations Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Windows Optimizations", test_windows_optimizations),
        ("Windows System Monitor", test_windows_system_monitor),
        ("Task Automation", test_task_automation),
        ("Local AI Optimization", test_local_ai_optimization),
        ("Enhanced Platform Compatibility", test_enhanced_platform_compatibility),
        ("Module Integration", test_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: CRITICAL FAILURE - {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<35} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Windows 10 optimizations are ready.")
        return 0
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_comprehensive_test()
    sys.exit(exit_code)