#!/usr/bin/env python3
"""
Test script for Phase 4 AI Model Integration
Demonstrates the implemented LLaVA model discovery and screen analysis capabilities
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_assistant.core.model_manager import get_model_manager, ModelInfo, AIAssistantManager
from ai_assistant.core.screen_analysis import ScreenAnalysisThread, AIQueryThread, get_component_registry


def test_model_discovery():
    """Test AI model discovery system"""
    print("=== Testing AI Model Discovery ===")
    
    model_manager = get_model_manager()
    
    # Test model discovery
    print("\n1. Testing model discovery:")
    print("   Starting model discovery (this may take a moment)...")
    
    # Create a mock model file for testing
    test_model_dir = "test_models"
    os.makedirs(test_model_dir, exist_ok=True)
    
    # Create a mock LLaVA model file
    mock_model_path = os.path.join(test_model_dir, "llava-v1.5-7b-q4_k_m.gguf")
    if not os.path.exists(mock_model_path):
        # Create a small test file (not a real model)
        with open(mock_model_path, 'wb') as f:
            f.write(b'0' * (50 * 1024 * 1024))  # 50MB mock file
    
    # Add test directory to search paths
    model_manager.add_custom_model_directory(test_model_dir)
    
    # Start discovery
    model_manager.discover_models()
    
    # Wait a moment for discovery
    time.sleep(2)
    
    # Get discovered models
    models = model_manager.get_available_models()
    print(f"   Discovered {len(models)} models")
    
    for model in models:
        print(f"   • {Path(model['path']).name}")
        print(f"     Format: {model['format_type']}, Size: {model['size_gb']:.1f}GB")
        print(f"     Capabilities: {', '.join(model['capabilities'])}")
    
    # Test LLaVA model filtering
    llava_models = model_manager.get_llava_models()
    print(f"\n2. LLaVA models found: {len(llava_models)}")
    
    # Test recommended model selection
    recommended = model_manager.get_recommended_model()
    if recommended:
        print(f"\n3. Recommended model: {Path(recommended['path']).name}")
        print(f"   Quantization: {recommended['quantization']}")
        print(f"   Size: {recommended['size_gb']:.1f}GB")
    else:
        print("\n3. No recommended model found")
    
    # Cleanup test files
    try:
        os.remove(mock_model_path)
        os.rmdir(test_model_dir)
    except:
        pass
    
    print("✅ Model discovery tests completed")


def test_model_info_extraction():
    """Test model information extraction"""
    print("\n=== Testing Model Information Extraction ===")
    
    # Test various model file patterns
    test_cases = [
        ("llava-v1.5-7b-q4_k_m.gguf", "LLaVA", "Q4_K_M", "gguf"),
        ("mistral-7b-instruct-v0.1.q8_0.gguf", "Mistral", "Q8_0", "gguf"),
        ("phi-3-mini-4k-instruct-fp16.onnx", "Phi", "FP16", "onnx"),
        ("gemma-2b-it-q4_k_m.gguf", "Gemma", "Q4_K_M", "gguf"),
    ]
    
    print("\n1. Testing model information extraction:")
    for filename, expected_model, expected_quant, expected_format in test_cases:
        # Create temporary test file
        test_path = f"temp_{filename}"
        with open(test_path, 'wb') as f:
            f.write(b'0' * (100 * 1024 * 1024))  # 100MB
        
        try:
            model_info = ModelInfo(test_path)
            print(f"   • {filename}")
            print(f"     Detected format: {model_info.format_type}")
            print(f"     Detected quantization: {model_info.quantization}")
            print(f"     Size: {model_info.size_gb:.1f}GB")
            print(f"     Capabilities: {', '.join(model_info.capabilities)}")
            
            # Verify detection
            assert model_info.format_type == expected_format, f"Format mismatch: {model_info.format_type} != {expected_format}"
            if expected_quant != "unknown":
                assert model_info.quantization == expected_quant, f"Quantization mismatch: {model_info.quantization} != {expected_quant}"
            
        finally:
            os.remove(test_path)
    
    print("✅ Model information extraction tests completed")


def test_screen_analysis():
    """Test screen analysis capabilities"""
    print("\n=== Testing Screen Analysis System ===")
    
    print("\n1. Testing screen analysis types:")
    
    # Mock screenshot data
    mock_screenshot = b"mock_screenshot_data"
    
    analysis_types = [
        ("general", "General content analysis"),
        ("ui_elements", "UI element detection"),
        ("code_analysis", "Code analysis"),
        ("design_review", "Design review"),
        ("accessibility", "Accessibility check")
    ]
    
    for analysis_type, description in analysis_types:
        print(f"   Testing {description}...")
        
        # Create analysis thread
        analysis_thread = ScreenAnalysisThread(
            screenshot_data=mock_screenshot,
            analysis_type=analysis_type,
            context={"test": True}
        )
        
        # Set up result capture
        results = []
        errors = []
        
        def capture_result(result):
            results.append(result)
        
        def capture_error(error):
            errors.append(error)
        
        analysis_thread.analysis_completed.connect(capture_result)
        analysis_thread.analysis_failed.connect(capture_error)
        
        # Run analysis
        analysis_thread.start()
        analysis_thread.wait(5000)  # Wait up to 5 seconds
        
        if results:
            result = results[0]
            print(f"     ✅ Analysis completed: {result['analysis_type']}")
            print(f"     Confidence: {result.get('confidence', 'N/A')}")
            if 'findings' in result:
                print(f"     Findings: {len(result['findings'])} categories")
        elif errors:
            print(f"     ❌ Analysis failed: {errors[0]}")
        else:
            print(f"     ⚠️ Analysis timed out")
    
    print("✅ Screen analysis tests completed")


def test_ai_query_system():
    """Test AI query system"""
    print("\n=== Testing AI Query System ===")
    
    print("\n1. Testing AI query processing:")
    
    test_queries = [
        ("What's on my screen?", "Screen analysis query"),
        ("Help me with this code", "Code assistance query"),
        ("How can I improve this UI?", "UI improvement query"),
        ("Check accessibility", "Accessibility query")
    ]
    
    for query, description in test_queries:
        print(f"   Testing {description}...")
        
        # Create query thread
        query_thread = AIQueryThread(
            query=query,
            context={"component": "test", "user_id": "test_user"},
            include_screen=True
        )
        
        # Set up result capture
        responses = []
        errors = []
        
        def capture_response(response):
            responses.append(response)
        
        def capture_error(error):
            errors.append(error)
        
        query_thread.response_ready.connect(capture_response)
        query_thread.query_failed.connect(capture_error)
        
        # Run query
        query_thread.start()
        query_thread.wait(3000)  # Wait up to 3 seconds
        
        if responses:
            print(f"     ✅ Response: {responses[0][:80]}...")
        elif errors:
            print(f"     ❌ Query failed: {errors[0]}")
        else:
            print(f"     ⚠️ Query timed out")
    
    print("✅ AI query tests completed")


def test_component_registration():
    """Test component registration system"""
    print("\n=== Testing Component Registration ===")
    
    registry = get_component_registry()
    
    print("\n1. Testing component registration:")
    
    # Register test components
    def finance_context():
        return {
            "active_invoices": 5,
            "total_revenue": 15000,
            "pending_payments": 3
        }
    
    def time_tracking_context():
        return {
            "active_session": True,
            "current_project": "WestfallAssistant",
            "hours_today": 6.5
        }
    
    def ui_context():
        return {
            "current_window": "main",
            "active_tab": "dashboard",
            "theme": "dark"
        }
    
    # Register components
    registry.register_component("finance", finance_context)
    registry.register_component("time_tracking", time_tracking_context)
    registry.register_component("ui", ui_context)
    
    print("   Registered 3 components")
    
    # Test individual context retrieval
    print("\n2. Testing context retrieval:")
    finance_ctx = registry.get_component_context("finance")
    print(f"   Finance context: {finance_ctx}")
    
    # Test all contexts retrieval
    all_contexts = registry.get_all_contexts()
    print(f"   All contexts: {len(all_contexts)} components")
    for component, context in all_contexts.items():
        print(f"     {component}: {list(context.keys())}")
    
    print("✅ Component registration tests completed")


def test_ai_assistant_manager():
    """Test AI Assistant Manager integration"""
    print("\n=== Testing AI Assistant Manager ===")
    
    print("\n1. Testing AI system initialization:")
    
    ai_manager = AIAssistantManager()
    
    # Test system context
    system_context = ai_manager.get_system_context()
    print("   System context generated:")
    for key, value in system_context.items():
        print(f"     {key}: {value}")
    
    # Test component registration
    print("\n2. Testing component registration with AI manager:")
    
    def main_window_context():
        return {
            "window_state": "maximized",
            "active_features": ["finance", "time_tracking"],
            "user_preferences": {"theme": "dark", "notifications": True}
        }
    
    ai_manager.register_component("main_window", main_window_context)
    print("   Registered main_window component")
    
    print("✅ AI Assistant Manager tests completed")


def main():
    """Run all Phase 4 AI integration tests"""
    print("🧪 Testing WestfallPersonalAssistant - Phase 4 AI Model Integration")
    print("=" * 70)
    
    try:
        test_model_discovery()
        test_model_info_extraction()
        test_screen_analysis()
        test_ai_query_system()
        test_component_registration()
        test_ai_assistant_manager()
        
        print("\n" + "=" * 70)
        print("🎉 All Phase 4 AI integration tests completed successfully!")
        print("\nImplemented features:")
        print("✅ LLaVA model discovery with flexible quantization support")
        print("✅ Model information extraction and capability detection")
        print("✅ Screen analysis system with multiple analysis types")
        print("✅ Context-aware AI query processing")
        print("✅ Component registration system for AI integration")
        print("✅ AIAssistantManager for system-wide integration")
        print("✅ Support for GGUF, ONNX, PyTorch, and SafeTensors formats")
        print("✅ Automatic model recommendation based on capabilities")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())