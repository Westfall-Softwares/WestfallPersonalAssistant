#!/usr/bin/env python3
"""
OpenAI Provider for Westfall Personal Assistant

Integrates with OpenAI's GPT models for AI responses.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from .provider_interface import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.model_name = self.config.get("model_name", "gpt-3.5-turbo")
        self.max_tokens = self.config.get("max_tokens", 1000)
        self.temperature = self.config.get("temperature", 0.7)
        self.client = None
        
        self.capabilities = [
            "text_generation",
            "conversation",
            "code_analysis",
            "reasoning",
            "creative_writing",
            "question_answering"
        ]
        
        # Available OpenAI models
        self.available_models = [
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client."""
        try:
            # Try to import OpenAI (optional dependency)
            try:
                import openai
                self.openai = openai
            except ImportError:
                logger.error("OpenAI library not installed. Install with: pip install openai")
                return False
            
            if not self.api_key:
                logger.error("OpenAI API key not provided")
                return False
            
            # Initialize client
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            
            # Test connection
            test_result = await self.test_connection()
            self.is_connected = test_result.get("success", False)
            
            if self.is_connected:
                logger.info(f"OpenAI provider initialized with model: {self.model_name}")
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "", thinking_mode: str = "normal", 
                              conversation_history: List[Dict] = None) -> str:
        """Generate response using OpenAI GPT."""
        if not self.is_connected or not self.client:
            return "OpenAI provider not connected. Please check your API key and connection."
        
        try:
            # Prepare messages
            messages = self._prepare_messages(prompt, context, thinking_mode, conversation_history)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Apply thinking mode formatting if needed
            if thinking_mode == "thinking":
                response_text = self._format_thinking_response(response_text)
            elif thinking_mode == "research":
                response_text = self._format_research_response(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"OpenAI response generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _prepare_messages(self, prompt: str, context: str, thinking_mode: str, 
                         conversation_history: List[Dict] = None) -> List[Dict]:
        """Prepare messages for OpenAI API."""
        messages = []
        
        # System message with context and thinking mode
        system_prompt = self._create_system_prompt(thinking_mode, context)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                if msg.get("type") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("type") == "assistant":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
        
        # Add current user message
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _create_system_prompt(self, thinking_mode: str, context: str) -> str:
        """Create system prompt based on thinking mode and context."""
        base_prompt = """You are Westfall Personal Assistant, an intelligent AI assistant that helps users with various tasks. You have access to the user's desktop environment and can help with file management, applications, and general questions."""
        
        if context:
            base_prompt += f"\n\nCurrent context: {context}"
        
        if thinking_mode == "thinking":
            base_prompt += "\n\nPlease show your thinking process and reasoning steps when responding to complex questions."
        elif thinking_mode == "research":
            base_prompt += "\n\nPlease provide a comprehensive, research-grade analysis with multiple perspectives, detailed reasoning, and well-structured conclusions."
        
        base_prompt += "\n\nBe helpful, accurate, and concise in your responses."
        
        return base_prompt
    
    def _format_thinking_response(self, response: str) -> str:
        """Format response for thinking mode."""
        if not response.startswith("🤔"):
            return f"🤔 **My Reasoning:**\n\n{response}"
        return response
    
    def _format_research_response(self, response: str) -> str:
        """Format response for research mode."""
        if not response.startswith("🔬"):
            return f"🔬 **Research Analysis:**\n\n{response}"
        return response
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to OpenAI API."""
        if not self.client:
            return {"success": False, "error": "Client not initialized"}
        
        try:
            # Try a simple completion
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            return {
                "success": True,
                "model": self.model_name,
                "response_id": response.id,
                "usage": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        return {
            "provider": "OpenAI",
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "capabilities": self.capabilities,
            "connected": self.is_connected
        }
    
    def set_model(self, model_name: str) -> bool:
        """Set the OpenAI model to use."""
        if model_name in self.available_models:
            self.model_name = model_name
            self.config["model_name"] = model_name
            logger.info(f"OpenAI model set to: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not available")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return self.available_models.copy()
    
    def set_api_key(self, api_key: str) -> bool:
        """Set OpenAI API key."""
        if not api_key:
            return False
        
        self.api_key = api_key
        self.config["api_key"] = api_key
        
        # Reinitialize if needed
        if self.client:
            self.client.api_key = api_key
        
        return True
    
    def set_parameters(self, max_tokens: int = None, temperature: float = None) -> bool:
        """Set generation parameters."""
        try:
            if max_tokens is not None:
                self.max_tokens = max(1, min(4000, max_tokens))
                self.config["max_tokens"] = self.max_tokens
            
            if temperature is not None:
                self.temperature = max(0.0, min(2.0, temperature))
                self.config["temperature"] = self.temperature
            
            return True
        except Exception as e:
            logger.error(f"Failed to set parameters: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup OpenAI provider."""
        if self.client:
            await self.client.close()
            self.client = None
        
        await super().cleanup()
        logger.info("OpenAI provider cleaned up")