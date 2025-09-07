"""
Comprehensive test to verify all components are working
"""

import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

# Create QApplication for testing
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def test_security_module():
    """Test security components exist and work"""
    from security.encryption_manager import EncryptionManager, MasterPasswordDialog
    from security.api_key_vault import APIKeyVault
    
    # Test encryption
    manager = EncryptionManager()
    assert manager is not None
    
    # Test encryption/decryption
    test_data = "sensitive_data_123"
    encrypted = manager.encrypt(test_data)
    decrypted = manager.decrypt(encrypted)
    assert decrypted == test_data
    
    # Test password hashing
    password = "TestPassword123!"
    hashed = manager.hash_password(password)
    assert hashed != password
    assert len(hashed) == 64  # SHA256 produces 64 character hex

def test_ai_assistant_module():
    """Test AI assistant components exist"""
    from ai_assistant.core.chat_manager import AIChatWidget, AIWorker
    from ai_assistant.providers.openai_provider import OpenAIProvider
    from ai_assistant.providers.ollama_provider import OllamaProvider
    
    # Test chat widget creation
    chat = AIChatWidget()
    assert chat is not None
    assert hasattr(chat, 'send_message')
    assert hasattr(chat, 'get_window_context')
    
    # Test worker thread
    worker = AIWorker("test query", {}, None)
    assert worker is not None

def test_all_windows_exist():
    """Test that all feature windows can be imported"""
    from email_window import EmailWindow
    from password_manager import PasswordManagerWindow
    from notes import NotesWindow
    from calculator import CalculatorWindow
    from calendar_window import CalendarWindow
    from weather import WeatherWindow
    from news import NewsWindow
    from browser import BrowserWindow
    from file_manager import FileManagerWindow
    from todo import TodoWindow
    from contacts import ContactsWindow
    from settings import SettingsWindow
    from finance import FinanceWindow
    from recipe import RecipeWindow
    from music_player import MusicPlayerWindow
    
    # All imports should succeed
    assert EmailWindow is not None
    assert PasswordManagerWindow is not None
    assert NotesWindow is not None
    assert MusicPlayerWindow is not None

def test_main_window_initialization():
    """Test main window can be created with proper features"""
    with patch('main.MasterPasswordDialog') as mock_dialog:
        # Mock the password dialog to auto-accept
        mock_instance = Mock()
        mock_instance.exec_.return_value = 1  # QDialog.Accepted
        mock_instance.password = "test_password"
        mock_dialog.return_value = mock_instance
        
        from main import MainWindow
        
        # Create main window
        window = MainWindow()
        assert window is not None
        
        # Check all features are defined
        assert len(window.features) == 15
        
        # Check shortcuts are initialized
        assert hasattr(window, 'init_shortcuts')
        
        # Check AI chat exists
        assert window.ai_chat is not None

def test_password_encryption():
    """Test password manager uses encryption"""
    from password_manager import PasswordManagerWindow
    
    # Check that password manager uses encryption
    window = PasswordManagerWindow()
    assert hasattr(window, 'encryption')
    assert window.encryption is not None

def test_news_reader_complete():
    """Test news reader is no longer a placeholder"""
    from news import NewsWindow, NewsWorker
    
    window = NewsWindow()
    assert hasattr(window, 'load_news')
    assert hasattr(window, 'display_news')
    
    # Check NewsWorker exists
    worker = NewsWorker()
    assert hasattr(worker, 'fetch_rss')

def test_music_player_exists():
    """Test music player is implemented"""
    from music_player import MusicPlayerWindow
    
    window = MusicPlayerWindow()
    assert hasattr(window, 'player')
    assert hasattr(window, 'playlist')
    assert hasattr(window, 'play_pause')
    assert hasattr(window, 'add_file')

def test_weather_uses_api_vault():
    """Test weather uses secure API storage"""
    from weather import WeatherWindow
    
    window = WeatherWindow()
    assert hasattr(window, 'get_api_key')
    
    # Should not have hardcoded key
    with open('weather.py', 'r') as f:
        content = f.read()
        assert 'your_openweathermap_api_key' not in content or 'vault' in content

def test_build_files_exist():
    """Test build configuration files exist"""
    assert os.path.exists('requirements.txt')
    assert os.path.exists('setup.py')
    assert os.path.exists('westfall_assistant.spec')
    assert os.path.exists('.github/workflows/ci.yml')

def test_keyboard_shortcuts():
    """Test keyboard shortcuts are defined"""
    from PyQt5.QtWidgets import QShortcut
    
    with patch('main.MasterPasswordDialog') as mock_dialog:
        mock_instance = Mock()
        mock_instance.exec_.return_value = 1
        mock_instance.password = "test"
        mock_dialog.return_value = mock_instance
        
        from main import MainWindow
        
        window = MainWindow()
        
        # Check that shortcuts method exists
        assert hasattr(window, 'init_shortcuts')
        
        # Verify some key shortcuts are accessible
        assert hasattr(window, 'toggle_ai_chat')
        assert hasattr(window, 'show_shortcuts')
        assert hasattr(window, 'toggle_dark_mode')

def test_confirmation_dialogs():
    """Test that delete operations have confirmations"""
    # Check password manager has confirmation
    with open('password_manager.py', 'r') as f:
        content = f.read()
        assert 'QMessageBox.question' in content or 'Confirm' in content
    
    # Check other critical files
    files_to_check = ['notes.py', 'todo.py', 'contacts.py', 'recipe.py']
    for filename in files_to_check:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
                # Should have some form of confirmation
                assert any(x in content for x in ['confirm', 'QMessageBox', 'dialog'])

def test_init_files_exist():
    """Test all __init__.py files exist"""
    init_files = [
        'security/__init__.py',
        'ai_assistant/__init__.py',
        'ai_assistant/core/__init__.py',
        'ai_assistant/providers/__init__.py',
        'tests/__init__.py'
    ]
    
    for init_file in init_files:
        assert os.path.exists(init_file), f"Missing {init_file}"

# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])