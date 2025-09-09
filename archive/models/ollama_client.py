"""
Ollama Client for Westfall Personal Assistant

Consolidated from existing Ollama provider implementations
Provides a clean interface to Ollama models
"""

import os
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available. Ollama support disabled.")


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
        
    def is_available(self) -> bool:
        """Check if Ollama server is available"""
        if not REQUESTS_AVAILABLE:
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        if not self.is_available():
            return []
            
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json().get('models', [])
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Generate response from model"""
        if not self.is_available():
            return "Ollama server not available"
            
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "top_p": kwargs.get('top_p', 0.9),
                    "top_k": kwargs.get('top_k', 40),
                    "num_predict": kwargs.get('max_tokens', 512),
                    "repeat_penalty": kwargs.get('repeat_penalty', 1.1)
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=kwargs.get('timeout', 60)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                logger.error(f"Generation failed: {response.status_code}")
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {e}"
    
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with model using message format"""
        if not self.is_available():
            return "Ollama server not available"
            
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "top_p": kwargs.get('top_p', 0.9),
                    "top_k": kwargs.get('top_k', 40),
                    "num_predict": kwargs.get('max_tokens', 512)
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=kwargs.get('timeout', 60)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', 'No response generated')
            else:
                logger.error(f"Chat failed: {response.status_code}")
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error: {e}"
    
    def pull_model(self, model: str) -> bool:
        """Pull/download a model"""
        if not self.is_available():
            return False
            
        try:
            payload = {"name": model}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutes for download
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Pull model error: {e}")
            return False
    
    def show_model_info(self, model: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        if not self.is_available():
            return {}
            
        try:
            payload = {"name": model}
            response = self.session.post(
                f"{self.base_url}/api/show",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Show model error: {e}")
            return {}
    
    def delete_model(self, model: str) -> bool:
        """Delete a model"""
        if not self.is_available():
            return False
            
        try:
            payload = {"name": model}
            response = self.session.delete(
                f"{self.base_url}/api/delete",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Delete model error: {e}")
            return False


# Default client instance
_ollama_client = None

def get_ollama_client(base_url: str = "http://localhost:11434") -> OllamaClient:
    """Get singleton Ollama client instance"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(base_url)
    return _ollama_client