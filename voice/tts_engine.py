"""
TTS Engine for Westfall Personal Assistant

Provides text-to-speech functionality with multiple backend support.
"""

import logging
import platform
from typing import Optional, Dict, Any, List
from config.settings import get_settings

logger = logging.getLogger(__name__)


class TTSBackend:
    """Base class for TTS backends"""
    
    def __init__(self):
        self.available = False
        self.voices = []
        self._initialize()
    
    def _initialize(self):
        """Initialize the TTS backend"""
        pass
    
    def speak(self, text: str, voice: str = None, speed: float = 1.0, volume: float = 0.8) -> bool:
        """Speak the given text"""
        raise NotImplementedError
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """Get available voices"""
        return self.voices
    
    def stop(self):
        """Stop current speech"""
        pass


class WindowsTTSBackend(TTSBackend):
    """Windows SAPI TTS backend"""
    
    def _initialize(self):
        try:
            if platform.system() == "Windows":
                import win32com.client
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.available = True
                self._load_voices()
            else:
                self.available = False
        except ImportError:
            logger.warning("Windows TTS: win32com not available")
            self.available = False
        except Exception as e:
            logger.error(f"Windows TTS initialization failed: {e}")
            self.available = False
    
    def _load_voices(self):
        """Load available Windows voices"""
        try:
            voices = self.engine.GetVoices()
            self.voices = []
            
            for i in range(voices.Count):
                voice = voices.Item(i)
                self.voices.append({
                    'id': i,
                    'name': voice.GetDescription(),
                    'gender': 'unknown',  # Would need to parse description
                    'language': 'en-US'  # Default, would need to detect
                })
        except Exception as e:
            logger.error(f"Failed to load Windows voices: {e}")
    
    def speak(self, text: str, voice: str = None, speed: float = 1.0, volume: float = 0.8) -> bool:
        if not self.available:
            return False
        
        try:
            # Set voice if specified
            if voice and voice.isdigit():
                voice_id = int(voice)
                if 0 <= voice_id < len(self.voices):
                    voices = self.engine.GetVoices()
                    self.engine.Voice = voices.Item(voice_id)
            
            # Set rate (speed)
            self.engine.Rate = int((speed - 1.0) * 10)  # Convert to SAPI range
            
            # Set volume
            self.engine.Volume = int(volume * 100)
            
            # Speak
            self.engine.Speak(text)
            return True
            
        except Exception as e:
            logger.error(f"Windows TTS speak failed: {e}")
            return False


class LinuxTTSBackend(TTSBackend):
    """Linux espeak/espeak-ng TTS backend"""
    
    def _initialize(self):
        try:
            if platform.system() == "Linux":
                import subprocess
                # Test if espeak is available
                result = subprocess.run(['espeak', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.available = True
                    self._load_voices()
                else:
                    self.available = False
            else:
                self.available = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("Linux TTS: espeak not found")
            self.available = False
        except Exception as e:
            logger.error(f"Linux TTS initialization failed: {e}")
            self.available = False
    
    def _load_voices(self):
        """Load available espeak voices"""
        try:
            import subprocess
            result = subprocess.run(['espeak', '--voices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                self.voices = []
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        self.voices.append({
                            'id': parts[1],
                            'name': parts[3],
                            'language': parts[1],
                            'gender': 'unknown'
                        })
        except Exception as e:
            logger.error(f"Failed to load Linux voices: {e}")
    
    def speak(self, text: str, voice: str = None, speed: float = 1.0, volume: float = 0.8) -> bool:
        if not self.available:
            return False
        
        try:
            import subprocess
            
            cmd = ['espeak']
            
            # Set voice/language
            if voice:
                cmd.extend(['-v', voice])
            
            # Set speed (words per minute)
            speed_wpm = int(175 * speed)  # Base 175 WPM
            cmd.extend(['-s', str(speed_wpm)])
            
            # Set amplitude (volume)
            amplitude = int(100 * volume)
            cmd.extend(['-a', str(amplitude)])
            
            # Add text
            cmd.append(text)
            
            # Execute
            subprocess.run(cmd, timeout=30)
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Linux TTS speak timeout")
            return False
        except Exception as e:
            logger.error(f"Linux TTS speak failed: {e}")
            return False


class MacOSTTSBackend(TTSBackend):
    """macOS say command TTS backend"""
    
    def _initialize(self):
        try:
            if platform.system() == "Darwin":
                import subprocess
                # Test if say command is available
                result = subprocess.run(['say', '-v', '?'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.available = True
                    self._load_voices()
                else:
                    self.available = False
            else:
                self.available = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("macOS TTS: say command not found")
            self.available = False
        except Exception as e:
            logger.error(f"macOS TTS initialization failed: {e}")
            self.available = False
    
    def _load_voices(self):
        """Load available macOS voices"""
        try:
            import subprocess
            result = subprocess.run(['say', '-v', '?'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                self.voices = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            voice_name = parts[0]
                            language = parts[1] if len(parts) > 1 else 'en-US'
                            
                            self.voices.append({
                                'id': voice_name,
                                'name': voice_name,
                                'language': language,
                                'gender': 'unknown'
                            })
        except Exception as e:
            logger.error(f"Failed to load macOS voices: {e}")
    
    def speak(self, text: str, voice: str = None, speed: float = 1.0, volume: float = 0.8) -> bool:
        if not self.available:
            return False
        
        try:
            import subprocess
            
            cmd = ['say']
            
            # Set voice
            if voice:
                cmd.extend(['-v', voice])
            
            # Set rate (words per minute)
            rate = int(175 * speed)  # Base 175 WPM
            cmd.extend(['-r', str(rate)])
            
            # Add text
            cmd.append(text)
            
            # Execute
            subprocess.run(cmd, timeout=30)
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("macOS TTS speak timeout")
            return False
        except Exception as e:
            logger.error(f"macOS TTS speak failed: {e}")
            return False


class TTSEngine:
    """Main TTS engine that manages backends"""
    
    def __init__(self):
        self.settings = get_settings()
        self.backends = []
        self.current_backend = None
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize available TTS backends"""
        # Try different backends based on platform
        backend_classes = [WindowsTTSBackend, LinuxTTSBackend, MacOSTTSBackend]
        
        for backend_class in backend_classes:
            try:
                backend = backend_class()
                if backend.available:
                    self.backends.append(backend)
                    if self.current_backend is None:
                        self.current_backend = backend
                        logger.info(f"Using TTS backend: {backend.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to initialize {backend_class.__name__}: {e}")
        
        if not self.backends:
            logger.warning("No TTS backends available")
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.current_backend is not None and self.settings.voice.tts_enabled
    
    def speak(self, text: str) -> bool:
        """Speak the given text using current settings"""
        if not self.is_available():
            logger.debug("TTS not available or disabled")
            return False
        
        if not text or not text.strip():
            return False
        
        # Clean text for speech
        clean_text = self._clean_text_for_speech(text)
        
        return self.current_backend.speak(
            clean_text,
            voice=self.settings.voice.tts_voice,
            speed=self.settings.voice.tts_speed,
            volume=self.settings.voice.tts_volume
        )
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        import re
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                     'link', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     'email address', text)
        
        # Replace newlines with pauses
        text = text.replace('\n', '. ')
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        if self.current_backend:
            return self.current_backend.get_voices()
        return []
    
    def set_voice(self, voice: str) -> bool:
        """Set the TTS voice"""
        try:
            self.settings.voice.tts_voice = voice
            return True
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
            return False
    
    def set_speed(self, speed: float) -> bool:
        """Set the TTS speed"""
        try:
            if 0.1 <= speed <= 3.0:
                self.settings.voice.tts_speed = speed
                return True
            else:
                logger.error("Speed must be between 0.1 and 3.0")
                return False
        except Exception as e:
            logger.error(f"Failed to set speed: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set the TTS volume"""
        try:
            if 0.0 <= volume <= 1.0:
                self.settings.voice.tts_volume = volume
                return True
            else:
                logger.error("Volume must be between 0.0 and 1.0")
                return False
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    def stop(self):
        """Stop current speech"""
        if self.current_backend:
            self.current_backend.stop()


# Singleton instance
_tts_engine_instance = None

def get_tts_engine() -> TTSEngine:
    """Get singleton TTS engine instance"""
    global _tts_engine_instance
    if _tts_engine_instance is None:
        _tts_engine_instance = TTSEngine()
    return _tts_engine_instance