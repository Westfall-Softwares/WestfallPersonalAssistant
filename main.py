#!/usr/bin/env python3
"""
Westfall Personal Assistant - Main Entry Point

Simplified entry point that uses the new reorganized structure.
The original 2695-line main.py has been backed up as main_original.py.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import new modules
from config.settings import get_settings
from utils.logger import setup_logging
from core.assistant import get_assistant_core

def setup_environment():
    """Setup the application environment"""
    try:
        # Check critical paths exist
        required_paths = ['models', 'data', 'logs', 'tmp']
        for path in required_paths:
            if not os.path.exists(path):
                print(f"Creating missing directory: {path}")
                os.makedirs(path, exist_ok=True)
        
        # Load settings
        settings = get_settings()
        
        # Setup logging
        logger = setup_logging()
        logger.info("Starting Westfall Personal Assistant")
        
        # Initialize core assistant
        assistant = get_assistant_core()
        success = assistant.initialize()
        
        if not success:
            logger.error("Failed to initialize assistant core")
            return False
        
        return True
        
    except Exception as e:
        print(f"Failed to setup environment: {e}")
        return False


def launch_gui():
    """Launch the GUI application"""
    try:
        # Try to import PyQt5
        from PyQt5.QtWidgets import QApplication
        
        # Import the original main window class from the backup
        # This is a temporary solution until we extract the UI components
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Create a simple launcher that imports from the original file
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_original", "main_original.py")
        main_original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_original)
        
        # Create and run the Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Westfall Personal Assistant")
        app.setApplicationVersion("2.0")
        
        # Create main window using original code
        main_window = main_original.MainWindow()
        main_window.show()
        
        logger = logging.getLogger(__name__)
        logger.info("GUI application started successfully")
        
        return app.exec_()
        
    except ImportError as e:
        print(f"GUI dependencies not available: {e}")
        print("Falling back to command line interface...")
        return launch_cli()
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        return launch_cli()


def launch_cli():
    """Launch the command line interface"""
    print("=" * 60)
    print("WESTFALL PERSONAL ASSISTANT - Command Line Interface")
    print("=" * 60)
    
    assistant = get_assistant_core()
    
    if not assistant.is_initialized:
        print("Error: Assistant not initialized properly")
        return 1
    
    print(f"Assistant Status: {assistant.get_status()}")
    print("\nType 'help' for commands, 'exit' to quit")
    print("-" * 60)
    
    try:
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Assistant: Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print_help()
                elif user_input.lower() == 'status':
                    print_status(assistant)
                elif user_input.lower().startswith('switch '):
                    handle_switch_model(assistant, user_input)
                elif user_input.lower() == 'models':
                    list_models(assistant)
                else:
                    # Process as regular message
                    response = assistant.process_message(user_input)
                    print(f"Assistant: {response}")
                    
            except KeyboardInterrupt:
                print("\n\nReceived interrupt signal. Goodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
                
    except Exception as e:
        print(f"CLI error: {e}")
        return 1
    finally:
        assistant.shutdown()
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
Available Commands:
  help        - Show this help message
  status      - Show assistant status
  models      - List available models
  switch <provider> <model> - Switch to different model
  exit/quit   - Exit the application
  
For regular conversation, just type your message and press Enter.
""")


def print_status(assistant):
    """Print assistant status"""
    status = assistant.get_status()
    print(f"""
Assistant Status:
  Initialized: {status['initialized']}
  Conversation Count: {status['conversation_count']}
  Session Duration: {status['session_duration']:.1f} seconds
  Active Provider: {status['model_status']['active_provider']}
  
Settings:
  Default Provider: {status['settings']['default_provider']}
  Business Dashboard: {status['settings']['features_enabled']['business_dashboard']}
  Voice Enabled: {status['settings']['features_enabled']['voice']}
  Extensions Enabled: {status['settings']['features_enabled']['extensions']}
""")


def handle_switch_model(assistant, command):
    """Handle model switching command"""
    parts = command.split()
    if len(parts) != 3:
        print("Usage: switch <provider> <model>")
        print("Example: switch ollama llama2")
        return
    
    provider = parts[1]
    model = parts[2]
    
    print(f"Switching to {provider}/{model}...")
    success = assistant.switch_model(provider, model)
    
    if success:
        print("Model switched successfully!")
    else:
        print("Failed to switch model. Check logs for details.")


def list_models(assistant):
    """List available models"""
    print("Available Models:")
    models = assistant.list_available_models()
    
    for provider, model_list in models.items():
        print(f"\n{provider.upper()}:")
        if model_list:
            for model in model_list:
                print(f"  - {model}")
        else:
            print("  (No models available)")


def main():
    """Main entry point"""
    print("Westfall Personal Assistant v2.0")
    
    # Setup environment
    if not setup_environment():
        print("Failed to setup environment. Exiting.")
        return 1
    
    # Determine interface mode
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--cli', '-c']:
            return launch_cli()
        elif sys.argv[1] in ['--gui', '-g']:
            return launch_gui()
        elif sys.argv[1] in ['--help', '-h']:
            print("""
Usage: python main.py [options]

Options:
  --gui, -g     Launch GUI interface (default)
  --cli, -c     Launch command line interface
  --help, -h    Show this help message

If no options are provided, the application will try to launch the GUI
and fall back to CLI if GUI dependencies are not available.
""")
            return 0
    
    # Default behavior: try GUI first, fallback to CLI
    try:
        from PyQt5.QtWidgets import QApplication
        return launch_gui()
    except ImportError:
        print("GUI not available, launching CLI interface...")
        return launch_cli()


if __name__ == "__main__":
    sys.exit(main())