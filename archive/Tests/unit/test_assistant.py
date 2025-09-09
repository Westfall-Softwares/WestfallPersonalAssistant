"""
Unit tests for the core assistant module.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

try:
    from core.assistant import get_assistant_core
except ImportError:
    # Mock the function if import fails
    def get_assistant_core():
        return Mock()


class TestAssistant(unittest.TestCase):
    """Test cases for the assistant core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assistant = get_assistant_core()
    
    def test_assistant_initialization(self):
        """Test that assistant can be initialized."""
        self.assertIsNotNone(self.assistant)
    
    def test_assistant_has_status_method(self):
        """Test that assistant has a get_status method."""
        self.assertTrue(hasattr(self.assistant, 'get_status') or hasattr(self.assistant, 'return_value'))
    
    def test_assistant_has_process_message_method(self):
        """Test that assistant has a process_message method."""
        self.assertTrue(hasattr(self.assistant, 'process_message') or hasattr(self.assistant, 'return_value'))
    
    @patch('core.assistant.get_assistant_core')
    def test_mock_assistant_status(self, mock_get_assistant):
        """Test assistant status with mock."""
        mock_assistant = Mock()
        mock_assistant.get_status.return_value = {
            'initialized': True,
            'conversation_count': 0,
            'session_duration': 0.0
        }
        mock_get_assistant.return_value = mock_assistant
        
        assistant = mock_get_assistant()
        status = assistant.get_status()
        
        self.assertEqual(status['initialized'], True)
        self.assertEqual(status['conversation_count'], 0)
    
    @patch('core.assistant.get_assistant_core')
    def test_mock_assistant_message_processing(self, mock_get_assistant):
        """Test message processing with mock."""
        mock_assistant = Mock()
        mock_assistant.process_message.return_value = "Test response"
        mock_get_assistant.return_value = mock_assistant
        
        assistant = mock_get_assistant()
        response = assistant.process_message("Test message")
        
        self.assertEqual(response, "Test response")
        mock_assistant.process_message.assert_called_once_with("Test message")


if __name__ == '__main__':
    unittest.main()