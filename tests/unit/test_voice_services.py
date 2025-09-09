"""
Tests for new voice services functionality.
"""

import unittest
import sys
import os

# Add project root to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from services.voice_recognition import VoiceRecognition, get_voice_recognition
from services.text_to_speech import TextToSpeech, get_text_to_speech


class TestVoiceServices(unittest.TestCase):
    """Test cases for voice services."""
    
    def test_voice_recognition_initialization(self):
        """Test voice recognition service initialization."""
        vr = VoiceRecognition()
        self.assertIsNotNone(vr)
        self.assertFalse(vr.is_available)
        self.assertFalse(vr.is_listening)
        
    def test_voice_recognition_singleton(self):
        """Test voice recognition singleton pattern."""
        vr1 = get_voice_recognition()
        vr2 = get_voice_recognition()
        self.assertIs(vr1, vr2)
        
    def test_text_to_speech_initialization(self):
        """Test text-to-speech service initialization."""
        tts = TextToSpeech()
        self.assertIsNotNone(tts)
        self.assertFalse(tts.is_available)
        self.assertEqual(len(tts.available_voices), 0)
        
    def test_text_to_speech_singleton(self):
        """Test text-to-speech singleton pattern."""
        tts1 = get_text_to_speech()
        tts2 = get_text_to_speech()
        self.assertIs(tts1, tts2)
        
    def test_voice_recognition_initialize(self):
        """Test voice recognition initialization method."""
        vr = VoiceRecognition()
        result = vr.initialize()
        self.assertTrue(result)
        self.assertTrue(vr.is_available)
        
    def test_text_to_speech_initialize(self):
        """Test text-to-speech initialization method."""
        tts = TextToSpeech()
        result = tts.initialize()
        self.assertTrue(result)
        self.assertTrue(tts.is_available)
        self.assertGreater(len(tts.available_voices), 0)


if __name__ == '__main__':
    unittest.main()