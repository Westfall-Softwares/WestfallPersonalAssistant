"""
Unified Model Manager for Westfall Personal Assistant

Consolidates model management functionality from:
- ai_assistant/core/model_manager.py 
- backend/model_handler.py

Provides a single interface for all AI model operations with support for:
- Multiple backends (Ollama, OpenAI, local models)
- Model discovery and loading
- GPU optimization for RTX 2060
- Security and validation
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Import with graceful fallbacks
try:
    from PyQt5.QtCore import QObject, pyqtSignal, QThread
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print("Info: PyQt5 not available. GUI features disabled.")

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("Info: llama-cpp-python not available. GGUF/GGML support disabled.")

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Info: transformers not available. PyTorch model support disabled.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Info: requests not available. Online model support disabled.")


@dataclass
class ModelConfig:
    """Configuration for model loading and inference"""
    gpu_layers: int = -1  # Auto-detect
    context_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 512
    
    # RTX 2060 optimizations
    vram_limit_gb: float = 5.0  # Leave 1GB for system
    batch_size: int = 512
    threads: int = 8


@dataclass
class ModelInfo:
    """Information about a discovered AI model"""
    path: str
    model_type: str = "unknown"
    format_type: str = "unknown"
    quantization: str = "unknown"
    size_gb: float = 0.0
    capabilities: List[str] = None
    framework: str = "unknown"
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class BaseModelProvider(ABC):
    """Abstract base class for model providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.loaded = False
        
    @abstractmethod
    def load(self, model_path: str) -> bool:
        """Load the model"""
        pass
        
    @abstractmethod
    def unload(self):
        """Unload the model to free memory"""
        pass
        
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response to prompt"""
        pass
        
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass


class LocalModelProvider(BaseModelProvider):
    """Provider for local GGUF/GGML models using llama.cpp"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.model = None
        self.model_path = None
        
    def load(self, model_path: str) -> bool:
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python not available")
            return False
            
        try:
            # Calculate optimal GPU layers for RTX 2060
            n_gpu_layers = self._calculate_gpu_layers(model_path)
            
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=self.config.context_length,
                n_batch=self.config.batch_size,
                n_threads=self.config.threads,
                verbose=False
            )
            
            self.model_path = model_path
            self.loaded = True
            logger.info(f"Loaded local model with {n_gpu_layers} GPU layers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            return False
    
    def unload(self):
        if self.model:
            del self.model
            self.model = None
            self.model_path = None
            self.loaded = False
            logger.info("Unloaded local model")
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.loaded or not self.model:
            return "Model not loaded"
        
        try:
            response = self.model(
                prompt,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
                top_k=kwargs.get('top_k', self.config.top_k),
                repeat_penalty=kwargs.get('repeat_penalty', self.config.repeat_penalty),
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error: {e}"
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "local",
            "model_path": self.model_path,
            "loaded": self.loaded,
            "framework": "llama.cpp"
        }
    
    def _calculate_gpu_layers(self, model_path: str) -> int:
        """Calculate optimal GPU layers for RTX 2060"""
        try:
            file_size_gb = Path(model_path).stat().st_size / (1024**3)
            
            # Conservative estimates for RTX 2060 (6GB VRAM)
            if file_size_gb <= 2:
                return -1  # All layers
            elif file_size_gb <= 4:
                return 32  # Most layers
            elif file_size_gb <= 6:
                return 20  # Partial offloading
            else:
                return 10  # Minimal offloading
                
        except Exception:
            return 20  # Default fallback


class OllamaProvider(BaseModelProvider):
    """Provider for Ollama models"""
    
    def __init__(self, config: ModelConfig, base_url: str = "http://localhost:11434"):
        super().__init__(config)
        self.base_url = base_url
        self.current_model = None
        
    def load(self, model_name: str) -> bool:
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available")
            return False
            
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.error("Ollama server not responding")
                return False
                
            # Check if model exists
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if model_name not in model_names:
                logger.error(f"Model {model_name} not found in Ollama")
                return False
                
            self.current_model = model_name
            self.loaded = True
            logger.info(f"Connected to Ollama model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def unload(self):
        self.current_model = None
        self.loaded = False
        logger.info("Disconnected from Ollama model")
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.loaded or not self.current_model:
            return "Model not loaded"
        
        try:
            payload = {
                "model": self.current_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "top_k": kwargs.get('top_k', self.config.top_k),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('response', 'No response')
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"Error: {e}"
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model_name": self.current_model,
            "loaded": self.loaded,
            "base_url": self.base_url
        }


class OpenAIProvider(BaseModelProvider):
    """Provider for OpenAI models"""
    
    def __init__(self, config: ModelConfig, api_key: str = None):
        super().__init__(config)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.current_model = None
        
    def load(self, model_name: str) -> bool:
        if not self.api_key:
            logger.error("OpenAI API key not provided")
            return False
            
        # Just store the model name - no actual loading needed for API
        self.current_model = model_name
        self.loaded = True
        logger.info(f"Connected to OpenAI model: {model_name}")
        return True
    
    def unload(self):
        self.current_model = None
        self.loaded = False
        logger.info("Disconnected from OpenAI model")
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.loaded or not self.current_model:
            return "Model not loaded"
        
        try:
            # This would require the openai library
            # For now, return a placeholder
            return "OpenAI integration requires openai library"
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error: {e}"
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model_name": self.current_model,
            "loaded": self.loaded,
            "api_key_set": bool(self.api_key)
        }


class ModelManager:
    """Unified model manager for all AI providers"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.providers: Dict[str, BaseModelProvider] = {}
        self.active_provider: Optional[str] = None
        self.discovered_models: Dict[str, ModelInfo] = {}
        
        # Initialize providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all available providers"""
        self.providers['local'] = LocalModelProvider(self.config)
        self.providers['ollama'] = OllamaProvider(self.config)
        
        # Only add OpenAI if API key is available
        if os.getenv('OPENAI_API_KEY'):
            self.providers['openai'] = OpenAIProvider(self.config)
    
    def list_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def load_model(self, provider: str, model_identifier: str) -> bool:
        """Load a model using the specified provider"""
        if provider not in self.providers:
            logger.error(f"Provider {provider} not available")
            return False
        
        # Unload current model if any
        if self.active_provider:
            self.unload_current_model()
        
        # Load new model
        success = self.providers[provider].load(model_identifier)
        if success:
            self.active_provider = provider
            logger.info(f"Loaded model {model_identifier} with provider {provider}")
        
        return success
    
    def unload_current_model(self):
        """Unload the currently active model"""
        if self.active_provider:
            self.providers[self.active_provider].unload()
            self.active_provider = None
            logger.info("Unloaded current model")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using the active model"""
        if not self.active_provider:
            return "No model loaded"
        
        return self.providers[self.active_provider].generate(prompt, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current model manager status"""
        status = {
            "active_provider": self.active_provider,
            "providers": {},
            "config": asdict(self.config)
        }
        
        for name, provider in self.providers.items():
            status["providers"][name] = provider.get_info()
        
        return status
    
    def discover_local_models(self, search_dirs: List[str] = None) -> Dict[str, ModelInfo]:
        """Discover local models in specified directories"""
        if search_dirs is None:
            search_dirs = [
                "models",
                os.path.expanduser("~/models"),
                os.path.expanduser("~/.cache/huggingface"),
                os.path.expanduser("~/.cache/ollama"),
            ]
        
        discovered = {}
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(('.gguf', '.ggml', '.bin', '.safetensors')):
                        full_path = os.path.join(root, file)
                        model_info = self._analyze_model_file(full_path)
                        discovered[full_path] = model_info
        
        self.discovered_models.update(discovered)
        return discovered
    
    def _analyze_model_file(self, file_path: str) -> ModelInfo:
        """Analyze a model file and extract information"""
        path = Path(file_path)
        
        # Detect format from extension
        format_type = "unknown"
        if path.suffix.lower() == '.gguf':
            format_type = "gguf"
        elif path.suffix.lower() == '.ggml':
            format_type = "ggml"
        elif path.suffix.lower() in ['.bin', '.safetensors']:
            format_type = "pytorch"
        
        # Detect quantization from filename
        quantization = "unknown"
        name_lower = path.name.lower()
        quant_patterns = ['q2_k', 'q3_k', 'q4_0', 'q4_k', 'q5_0', 'q5_k', 'q6_k', 'q8_0', 'f16', 'f32']
        for pattern in quant_patterns:
            if pattern in name_lower:
                quantization = pattern.upper()
                break
        
        # Get file size
        try:
            size_gb = path.stat().st_size / (1024**3)
        except:
            size_gb = 0.0
        
        # Detect capabilities
        capabilities = []
        if 'llava' in name_lower:
            capabilities.extend(['vision', 'chat', 'multimodal'])
        elif 'chat' in name_lower or 'instruct' in name_lower:
            capabilities.append('chat')
        
        return ModelInfo(
            path=str(path),
            model_type="llm",
            format_type=format_type,
            quantization=quantization,
            size_gb=size_gb,
            capabilities=capabilities,
            framework="llama.cpp" if format_type in ["gguf", "ggml"] else "transformers"
        )


# Singleton instance
_model_manager_instance = None

def get_model_manager() -> ModelManager:
    """Get singleton model manager instance"""
    global _model_manager_instance
    if _model_manager_instance is None:
        _model_manager_instance = ModelManager()
    return _model_manager_instance