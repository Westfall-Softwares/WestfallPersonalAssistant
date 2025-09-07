#!/usr/bin/env python3
"""
Demo script showing how to use the new utility modules
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_theme_usage():
    """Demo how to use the AppTheme module"""
    print("🎨 Theme Module Demo")
    print("-" * 40)
    
    from util.app_theme import AppTheme
    
    print(f"Primary Color: {AppTheme.PRIMARY_COLOR}")
    print(f"Background Color: {AppTheme.BACKGROUND}")
    print(f"Success Color: {AppTheme.SUCCESS_COLOR}")
    
    print("\nButton Styles:")
    print("Primary Button Style (first 200 chars):")
    print(AppTheme.get_button_style(primary=True)[:200] + "...")
    
    print("\nSecondary Button Style (first 200 chars):")
    print(AppTheme.get_button_style(primary=False)[:200] + "...")
    
    print("\nMessage Styles available:")
    message_styles = AppTheme.get_message_styles()
    for style_type in message_styles.keys():
        print(f"  - {style_type}")

def demo_error_handler_usage():
    """Demo how to use the ErrorHandler module"""
    print("\n🚨 Error Handler Module Demo")
    print("-" * 40)
    
    from util.error_handler import get_error_handler
    
    # Get the global error handler
    handler = get_error_handler()
    
    print("Initial error statistics:")
    stats = handler.get_error_statistics()
    print(f"  Total errors: {stats['total']}")
    print(f"  Error breakdown: {stats['counts']}")
    
    # Simulate different types of errors (without actually showing dialogs)
    print("\nSimulating error detection:")
    
    import requests
    import sqlite3
    
    # Test error type detection
    network_error = requests.exceptions.ConnectionError("Simulated network error")
    if handler.is_network_error(network_error):
        print("  ✅ Network error detected correctly")
    
    db_error = sqlite3.Error("Simulated database error")
    if handler.is_database_error(db_error):
        print("  ✅ Database error detected correctly")
    
    file_error = FileNotFoundError("Simulated file error")
    if handler.is_file_error(file_error):
        print("  ✅ File error detected correctly")

def demo_network_manager_usage():
    """Demo how to use the NetworkManager module"""
    print("\n🌐 Network Manager Module Demo")
    print("-" * 40)
    
    from util.network_manager import get_network_manager
    
    # Get a network manager instance
    manager = get_network_manager()
    
    print(f"Initial pending requests: {manager.get_pending_requests_count()}")
    
    # Demo creating a request (but don't actually send it)
    print("\nDemo request creation:")
    print("  - manager.get() for GET requests")
    print("  - manager.post() for POST requests")
    print("  - manager.put() for PUT requests")
    print("  - manager.delete() for DELETE requests")
    print("  - manager.patch() for PATCH requests")
    print("  - manager.download_file() for file downloads")
    print("  - manager.upload_file() for file uploads")
    
    print("\nFeatures:")
    print("  ✅ Automatic retries on failure")
    print("  ✅ Configurable timeouts")
    print("  ✅ Progress tracking for downloads/uploads")
    print("  ✅ Error handling integration")
    print("  ✅ Thread-safe operations")

def demo_integration_example():
    """Demo how all modules work together"""
    print("\n🔗 Integration Example")
    print("-" * 40)
    
    from util.app_theme import AppTheme
    from util.error_handler import get_error_handler
    from util.network_manager import get_network_manager
    
    print("Example: Creating a themed button with error handling and network functionality")
    
    # Get theme colors
    bg_color = AppTheme.PRIMARY_COLOR
    text_color = AppTheme.TEXT_PRIMARY
    
    # Get error handler for user feedback
    error_handler = get_error_handler()
    
    # Get network manager for API calls
    network_manager = get_network_manager()
    
    # Example button style
    button_style = f"""
    QPushButton {{
        background-color: {bg_color};
        color: {text_color};
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }}
    """
    
    print(f"Button styled with theme colors:")
    print(f"  Background: {bg_color}")
    print(f"  Text: {text_color}")
    
    print(f"\nError handler ready for user feedback")
    print(f"Network manager ready for API calls")
    
    print("\nIn a real application, you would:")
    print("  1. Apply AppTheme.get_complete_stylesheet() to your QApplication")
    print("  2. Use get_error_handler() for consistent error messages")
    print("  3. Use get_network_manager() for all HTTP requests")
    print("  4. Combine them for a professional, robust application")

def main():
    """Run all demos"""
    print("🚀 WestfallPersonalAssistant Utility Modules Demo")
    print("=" * 60)
    
    demo_theme_usage()
    demo_error_handler_usage() 
    demo_network_manager_usage()
    demo_integration_example()
    
    print("\n" + "=" * 60)
    print("✨ Demo completed! The modules are ready to enhance your application.")
    print("\n📚 Usage in your code:")
    print("   from util.app_theme import AppTheme")
    print("   from util.error_handler import get_error_handler")
    print("   from util.network_manager import get_network_manager")

if __name__ == "__main__":
    main()