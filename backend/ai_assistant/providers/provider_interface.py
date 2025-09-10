#!/usr/bin/env python3
"""
AI Provider Interface for Westfall Personal Assistant

Abstract base class for AI providers (OpenAI, Local LLM, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model_name = self.config.get("model_name", "default")
        self.is_connected = False
        self.capabilities = []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the AI provider."""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: str = "", thinking_mode: str = "normal", 
                              conversation_history: List[Dict] = None) -> str:
        """Generate a response to the given prompt."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the AI service."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass
    
    @abstractmethod
    def set_model(self, model_name: str) -> bool:
        """Set the model to use."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get provider capabilities."""
        return self.capabilities
    
    def is_available(self) -> bool:
        """Check if provider is available and connected."""
        return self.is_connected
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.__class__.__name__
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update provider configuration."""
        self.config.update(new_config)
    
    async def cleanup(self):
        """Cleanup provider resources."""
        self.is_connected = False