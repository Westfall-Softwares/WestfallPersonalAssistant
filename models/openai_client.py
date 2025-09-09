"""
OpenAI Client for Westfall Personal Assistant

Consolidated from existing OpenAI provider implementations
Provides a clean interface to OpenAI models
"""

import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not available. OpenAI support disabled.")


class OpenAIClient:
    """Client for interacting with OpenAI API"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available and configured"""
        return OPENAI_AVAILABLE and self.client is not None and bool(self.api_key)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        if not self.is_available():
            return []
            
        try:
            response = self.client.models.list()
            return [model.dict() for model in response.data]
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {e}")
            return []
    
    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Generate response from model using completion"""
        if not self.is_available():
            return "OpenAI client not available or not configured"
            
        try:
            # Use chat completion for all models (recommended approach)
            messages = [{"role": "user", "content": prompt}]
            return self.chat(model, messages, **kwargs)
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error: {e}"
    
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with model using message format"""
        if not self.is_available():
            return "OpenAI client not available or not configured"
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 512),
                top_p=kwargs.get('top_p', 0.9),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
                timeout=kwargs.get('timeout', 60)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return f"Error: {e}"
    
    def get_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Get embeddings for text"""
        if not self.is_available():
            return []
            
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {e}")
            return []
    
    def moderate_content(self, text: str) -> Dict[str, Any]:
        """Check content for policy violations"""
        if not self.is_available():
            return {}
            
        try:
            response = self.client.moderations.create(input=text)
            return response.results[0].dict()
            
        except Exception as e:
            logger.error(f"OpenAI moderation error: {e}")
            return {}
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get API usage information (if available)"""
        # Note: This requires additional API access that may not be available
        # with all account types
        return {
            "api_key_set": bool(self.api_key),
            "client_configured": bool(self.client),
            "available": self.is_available()
        }


# Common model configurations
OPENAI_MODELS = {
    "gpt-4": {
        "max_tokens": 8192,
        "context_window": 8192,
        "cost_per_token": 0.00003,  # Approximate
        "description": "Most capable GPT-4 model"
    },
    "gpt-4-turbo": {
        "max_tokens": 4096,
        "context_window": 128000,
        "cost_per_token": 0.00001,
        "description": "Latest GPT-4 Turbo model"
    },
    "gpt-3.5-turbo": {
        "max_tokens": 4096,
        "context_window": 16384,
        "cost_per_token": 0.000002,
        "description": "Fast and efficient GPT-3.5 model"
    }
}


def get_model_info(model_name: str) -> Dict[str, Any]:
    """Get information about an OpenAI model"""
    return OPENAI_MODELS.get(model_name, {
        "max_tokens": 2048,
        "context_window": 4096,
        "cost_per_token": 0.00001,
        "description": "Unknown model"
    })


# Default client instance
_openai_client = None

def get_openai_client(api_key: str = None, base_url: str = None) -> OpenAIClient:
    """Get singleton OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient(api_key, base_url)
    return _openai_client