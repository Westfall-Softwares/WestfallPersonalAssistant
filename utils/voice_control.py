"""
Voice Control System for Westfall Personal Assistant
Provides speech recognition, wake word detection, and voice feedback capabilities
"""

import threading
import time
import queue
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass


@dataclass
class VoiceCommand:
    """Represents a voice command with its context"""
    command: str
    confidence: float
    timestamp: float
    context: Dict[str, Any]


class VoiceControlManager:
    """Manages voice control functionality with graceful fallbacks"""
    
    def __init__(self):
        self.enabled = False
        self.listening = False
        self.wake_words = ["hey assistant", "computer", "westfall"]
        self.command_queue = queue.Queue()
        self.listeners = []
        self.voice_profiles = {}
        
        # Voice settings
        self.settings = {
            "wake_word_enabled": True,
            "continuous_listening": False,
            "voice_feedback": True,
            "noise_threshold": 0.5,
            "confidence_threshold": 0.7,
            "language": "en-US"
        }
        
        # Initialize voice engines with fallbacks
        self._init_speech_recognition()
        self._init_text_to_speech()
        
    def _init_speech_recognition(self):
        """Initialize speech recognition with fallback handling"""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.sr_available = True
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                
        except ImportError:
            print("⚠️ SpeechRecognition not available - voice input disabled")
            self.sr_available = False
            self.recognizer = None
            self.microphone = None
        except Exception as e:
            print(f"⚠️ Error initializing speech recognition: {e}")
            self.sr_available = False
            
    def _init_text_to_speech(self):
        """Initialize text-to-speech with fallback handling"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_available = True
            
            # Configure voice settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
            self.tts_engine.setProperty('rate', 200)
            self.tts_engine.setProperty('volume', 0.8)
            
        except ImportError:
            print("⚠️ pyttsx3 not available - voice feedback disabled")
            self.tts_available = False
            self.tts_engine = None
        except Exception as e:
            print(f"⚠️ Error initializing text-to-speech: {e}")
            self.tts_available = False
            
    def enable_voice_control(self) -> bool:
        """Enable voice control system"""
        if not self.sr_available:
            return False
            
        self.enabled = True
        if self.settings["continuous_listening"]:
            self.start_listening()
        return True
        
    def disable_voice_control(self):
        """Disable voice control system"""
        self.enabled = False
        self.stop_listening()
        
    def start_listening(self):
        """Start continuous listening for voice commands"""
        if not self.enabled or not self.sr_available:
            return False
            
        if self.listening:
            return True
            
        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        return True
        
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.listening = False
        
    def _listen_loop(self):
        """Main listening loop running in background thread"""
        while self.listening and self.sr_available:
            try:
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                try:
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio).lower()
                    confidence = 0.8  # Google API doesn't provide confidence directly
                    
                    # Check for wake words or process command
                    if self._contains_wake_word(text) or not self.settings["wake_word_enabled"]:
                        command = VoiceCommand(
                            command=text,
                            confidence=confidence,
                            timestamp=time.time(),
                            context=self._get_current_context()
                        )
                        
                        self.command_queue.put(command)
                        self._notify_listeners(command)
                        
                except Exception as e:
                    # Recognition failed - continue listening
                    continue
                    
            except Exception as e:
                # Timeout or other error - continue listening
                time.sleep(0.1)
                continue
                
    def _contains_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word"""
        text = text.lower()
        return any(wake_word in text for wake_word in self.wake_words)
        
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current application context for voice commands"""
        return {
            "timestamp": time.time(),
            "active_window": "main",  # Would get from main app
            "user_profile": "default",
            "listening_mode": "continuous" if self.settings["continuous_listening"] else "wake_word"
        }
        
    def add_command_listener(self, callback: Callable[[VoiceCommand], None]):
        """Add a listener for voice commands"""
        self.listeners.append(callback)
        
    def remove_command_listener(self, callback: Callable[[VoiceCommand], None]):
        """Remove a voice command listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
            
    def _notify_listeners(self, command: VoiceCommand):
        """Notify all listeners of a new voice command"""
        for listener in self.listeners:
            try:
                listener(command)
            except Exception as e:
                print(f"Error in voice command listener: {e}")
                
    def speak(self, text: str, priority: str = "normal"):
        """Convert text to speech with priority handling"""
        if not self.tts_available or not self.settings["voice_feedback"]:
            return False
            
        def _speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Error in text-to-speech: {e}")
                
        # Run in separate thread to avoid blocking
        speak_thread = threading.Thread(target=_speak, daemon=True)
        speak_thread.start()
        return True
        
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process a voice command and return action result"""
        command = command.lower().strip()
        
        # Navigation commands
        if "open" in command and "dashboard" in command:
            return {"action": "navigate", "target": "dashboard", "success": True}
        elif "open" in command and "financial" in command:
            return {"action": "navigate", "target": "finance", "success": True}
        elif "show" in command and "projects" in command:
            return {"action": "navigate", "target": "projects", "success": True}
            
        # Action commands
        elif "create" in command and "invoice" in command:
            return {"action": "create", "type": "invoice", "success": True}
        elif "start" in command and "tracking" in command:
            return {"action": "start", "type": "time_tracking", "success": True}
            
        # Query commands
        elif "profit margin" in command:
            return {"action": "query", "type": "profit_margin", "success": True}
        elif "today" in command and "tasks" in command:
            return {"action": "query", "type": "daily_tasks", "success": True}
            
        # Control commands
        elif "stop listening" in command:
            self.stop_listening()
            return {"action": "control", "type": "stop_listening", "success": True}
        elif "pause voice" in command:
            self.settings["voice_feedback"] = False
            return {"action": "control", "type": "pause_voice", "success": True}
            
        # Unknown command
        return {"action": "unknown", "command": command, "success": False}
        
    def get_available_commands(self) -> List[str]:
        """Get list of available voice commands"""
        return [
            "Open financial dashboard",
            "Show projects", 
            "Create new invoice",
            "Start time tracking",
            "What's my profit margin?",
            "Show today's tasks",
            "Stop listening",
            "Pause voice control"
        ]
        
    def add_voice_profile(self, profile_name: str, settings: Dict[str, Any]):
        """Add a voice profile for multi-user support"""
        self.voice_profiles[profile_name] = settings
        
    def switch_voice_profile(self, profile_name: str) -> bool:
        """Switch to a different voice profile"""
        if profile_name in self.voice_profiles:
            self.settings.update(self.voice_profiles[profile_name])
            return True
        return False
        
    def get_status(self) -> Dict[str, Any]:
        """Get current voice control status"""
        return {
            "enabled": self.enabled,
            "listening": self.listening,
            "sr_available": self.sr_available,
            "tts_available": self.tts_available,
            "queue_size": self.command_queue.qsize(),
            "settings": self.settings.copy(),
            "profiles": list(self.voice_profiles.keys())
        }


# Global instance
voice_manager = VoiceControlManager()


def get_voice_manager() -> VoiceControlManager:
    """Get the global voice control manager instance"""
    return voice_manager