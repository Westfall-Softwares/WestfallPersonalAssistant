"""
Core Assistant Module for Westfall Personal Assistant

Extracted from main.py to separate business logic from UI.
Contains the main assistant functionality without GUI dependencies.
"""

import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path

# Import our new modules
from config.settings import get_settings, Settings
from models.model_manager import get_model_manager, ModelManager

logger = logging.getLogger(__name__)


class AssistantCore:
    """Core assistant logic without UI dependencies"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_manager = get_model_manager()
        self.is_initialized = False
        self.conversation_count = 0
        self.session_start_time = datetime.now()
        
        # Event callbacks
        self.on_response_callback: Optional[Callable[[str], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None
        self.on_status_change_callback: Optional[Callable[[str], None]] = None
        
    def initialize(self) -> bool:
        """Initialize the assistant core"""
        try:
            logger.info("Initializing Westfall Personal Assistant Core")
            
            # Setup logging
            self._setup_logging()
            
            # Load default model if configured
            if self.settings.models.default_provider:
                self._load_default_model()
            
            self.is_initialized = True
            self._notify_status("Assistant initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize assistant core: {e}")
            self._notify_error(f"Initialization failed: {e}")
            return False
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.settings.get_logging_config()
        
        # Create logs directory if needed
        if log_config.get('filename'):
            log_file = Path(log_config['filename'])
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=log_config['level'],
            format=log_config['format'],
            filename=log_config.get('filename'),
            filemode='a'
        )
        
        logger.info("Logging configured")
    
    def _load_default_model(self):
        """Load the default model based on settings"""
        try:
            provider = self.settings.models.default_provider
            
            if provider == "ollama":
                model_name = self.settings.models.ollama_default_model
                success = self.model_manager.load_model("ollama", model_name)
            elif provider == "openai":
                model_name = self.settings.models.openai_default_model
                success = self.model_manager.load_model("openai", model_name)
            elif provider == "local":
                # Try to find a local model in the models directory
                models_dir = Path(self.settings.models.local_models_directory)
                if models_dir.exists():
                    model_files = list(models_dir.glob("*.gguf")) + list(models_dir.glob("*.ggml"))
                    if model_files:
                        success = self.model_manager.load_model("local", str(model_files[0]))
                    else:
                        logger.warning("No local models found")
                        success = False
                else:
                    logger.warning("Local models directory not found")
                    success = False
            else:
                logger.warning(f"Unknown provider: {provider}")
                success = False
            
            if success:
                logger.info(f"Loaded default model with provider: {provider}")
                self._notify_status(f"Model loaded: {provider}")
            else:
                logger.warning("Failed to load default model")
                self._notify_status("No model loaded")
                
        except Exception as e:
            logger.error(f"Error loading default model: {e}")
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process a user message and return assistant response"""
        if not self.is_initialized:
            return "Assistant not initialized"
        
        try:
            self.conversation_count += 1
            logger.info(f"Processing message #{self.conversation_count}")
            
            # Prepare context
            context = context or {}
            context.update({
                "conversation_count": self.conversation_count,
                "session_time": (datetime.now() - self.session_start_time).total_seconds()
            })
            
            # Use message handler for command processing and intent detection
            from core.message_handler import get_message_handler
            message_handler = get_message_handler()
            
            # Check if it's a command or special intent
            if message.startswith('/') or any(word in message.lower() for word in ['help', 'status', 'time', 'calculate', 'file', 'note']):
                response = message_handler.process_message(message, context)
            else:
                # Generate AI response using model manager
                response = self._generate_response(message, context)
            
            # Log the interaction (if enabled)
            if self.settings.logging.log_user_inputs:
                logger.info(f"User: {message}")
            if self.settings.logging.log_ai_responses:
                logger.info(f"Assistant: {response}")
            
            # Notify callback if set
            if self.on_response_callback:
                self.on_response_callback(response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return f"Sorry, I encountered an error: {e}"
    
    def _generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate response using the active model"""
        # Prepare the prompt with context
        formatted_prompt = self._format_prompt(message, context)
        
        # Generate response
        response = self.model_manager.generate(
            formatted_prompt,
            temperature=self.settings.models.temperature,
            max_tokens=self.settings.models.max_tokens,
            top_p=self.settings.models.top_p,
            top_k=self.settings.models.top_k,
            repeat_penalty=self.settings.models.repeat_penalty
        )
        
        return response
    
    def _format_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Format the prompt with context and system instructions"""
        system_prompt = """You are Westfall Personal Assistant, a helpful AI assistant designed to help with various tasks including business operations, personal productivity, and general assistance. 

Please provide helpful, accurate, and concise responses. If you're unsure about something, please say so rather than guessing."""
        
        # Add context information if available
        context_info = []
        if context.get("conversation_count"):
            context_info.append(f"This is message #{context['conversation_count']} in this session")
        
        if context_info:
            context_str = "\n".join(context_info)
            formatted_prompt = f"{system_prompt}\n\nContext: {context_str}\n\nUser: {message}\n\nAssistant:"
        else:
            formatted_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
        
        return formatted_prompt
    
    def get_status(self) -> Dict[str, Any]:
        """Get current assistant status"""
        model_status = self.model_manager.get_status()
        
        return {
            "initialized": self.is_initialized,
            "conversation_count": self.conversation_count,
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "model_status": model_status,
            "settings": {
                "default_provider": self.settings.models.default_provider,
                "features_enabled": {
                    "business_dashboard": self.settings.features.business_dashboard_enabled,
                    "voice": self.settings.voice.tts_enabled,
                    "extensions": self.settings.features.extensions_enabled
                }
            }
        }
    
    def switch_model(self, provider: str, model_identifier: str) -> bool:
        """Switch to a different model"""
        try:
            success = self.model_manager.load_model(provider, model_identifier)
            if success:
                logger.info(f"Switched to model: {provider}/{model_identifier}")
                self._notify_status(f"Switched to: {provider}/{model_identifier}")
            else:
                logger.error(f"Failed to switch to model: {provider}/{model_identifier}")
                self._notify_error(f"Failed to switch to model: {provider}/{model_identifier}")
            return success
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            self._notify_error(f"Error switching model: {e}")
            return False
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models by provider"""
        try:
            providers = self.model_manager.list_providers()
            available_models = {}
            
            for provider in providers:
                if provider == "ollama":
                    from models.ollama_client import get_ollama_client
                    client = get_ollama_client()
                    if client.is_available():
                        models = [m.get('name', 'unknown') for m in client.list_models()]
                        available_models[provider] = models
                    else:
                        available_models[provider] = []
                elif provider == "openai":
                    from models.openai_client import OPENAI_MODELS
                    available_models[provider] = list(OPENAI_MODELS.keys())
                elif provider == "local":
                    # Discover local models
                    discovered = self.model_manager.discover_local_models()
                    available_models[provider] = list(discovered.keys())
                else:
                    available_models[provider] = []
            
            return available_models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return {}
    
    def set_response_callback(self, callback: Callable[[str], None]):
        """Set callback for when responses are generated"""
        self.on_response_callback = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback for when errors occur"""
        self.on_error_callback = callback
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status changes"""
        self.on_status_change_callback = callback
    
    def _notify_status(self, message: str):
        """Notify status change"""
        if self.on_status_change_callback:
            self.on_status_change_callback(message)
    
    def _notify_error(self, message: str):
        """Notify error"""
        if self.on_error_callback:
            self.on_error_callback(message)
    
    def shutdown(self):
        """Shutdown the assistant core"""
        logger.info("Shutting down assistant core")
        
        # Unload current model
        self.model_manager.unload_current_model()
        
        # Save settings
        self.settings.save()
        
        self.is_initialized = False
        self._notify_status("Assistant shutdown")


# Singleton instance
_assistant_core_instance = None

def get_assistant_core() -> AssistantCore:
    """Get singleton assistant core instance"""
    global _assistant_core_instance
    if _assistant_core_instance is None:
        _assistant_core_instance = AssistantCore()
    return _assistant_core_instance