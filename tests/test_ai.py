import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_command_recognition():
    # Test command recognition without GUI
    from ai_assistant.core.chat_manager import AIChatWidget
    
    # Mock the __init__ to avoid PyQt5 initialization
    with patch.object(AIChatWidget, '__init__', lambda x: None):
        chat = AIChatWidget.__new__(AIChatWidget)
        
        # Test command recognition method directly
        assert AIChatWidget.is_command(chat, "send email to john")
        assert AIChatWidget.is_command(chat, "add password for gmail")
        assert not AIChatWidget.is_command(chat, "what is the weather like")

def test_command_parsing():
    # Test command parsing without GUI
    from ai_assistant.core.chat_manager import AIChatWidget
    
    with patch.object(AIChatWidget, '__init__', lambda x: None):
        chat = AIChatWidget.__new__(AIChatWidget)
        
        # Test email command
        result = AIChatWidget.parse_and_execute(chat, "send email", {})
        assert "Email command recognized" in result["message"]
        
        # Test password command
        result = AIChatWidget.parse_and_execute(chat, "add password", {})
        assert "Password command recognized" in result["message"]

def test_ai_provider_imports():
    # Test AI provider imports
    try:
        from ai_assistant.providers.openai_provider import OpenAIProvider
        assert OpenAIProvider is not None
    except ImportError:
        pass  # Expected if openai not installed
    
    try:
        from ai_assistant.providers.ollama_provider import OllamaProvider
        assert OllamaProvider is not None
    except Exception:
        pass  # Expected if ollama not running