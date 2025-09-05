"""
Model integration module for various AI model formats

This module provides unified interfaces for different model types:
- GGUF/GGML models via llama.cpp
- PyTorch/Transformers models
- Other formats as needed

Optimized for RTX 2060 with smart GPU layer offloading.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
import asyncio

logger = logging.getLogger(__name__)

# Import model libraries with graceful fallbacks
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

class ModelConfig:
    """Configuration for model loading and inference"""
    
    def __init__(self):
        self.gpu_layers = -1  # Auto-detect
        self.context_length = 4096
        self.temperature = 0.7
        self.top_p = 0.9
        self.top_k = 40
        self.repeat_penalty = 1.1
        self.max_tokens = 512
        
        # RTX 2060 optimizations
        self.vram_limit_gb = 5.0  # Leave 1GB for system
        self.batch_size = 512
        self.threads = 8

class BaseModel:
    """Base class for all model implementations"""
    
    def __init__(self, model_path: str, config: ModelConfig):
        self.model_path = model_path
        self.config = config
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
    def load(self) -> bool:
        """Load the model"""
        raise NotImplementedError
        
    def unload(self):
        """Unload the model to free memory"""
        raise NotImplementedError
        
    def generate(self, prompt: str, thinking_mode: str = "normal") -> str:
        """Generate response to prompt"""
        raise NotImplementedError
        
    def get_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "path": self.model_path,
            "loaded": self.loaded,
            "type": self.__class__.__name__
        }

class LlamaCppModel(BaseModel):
    """llama.cpp model implementation for GGUF/GGML files"""
    
    def load(self) -> bool:
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python not available")
            return False
            
        try:
            # Calculate optimal GPU layers for RTX 2060
            n_gpu_layers = self._calculate_gpu_layers()
            
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=self.config.context_length,
                n_batch=self.config.batch_size,
                n_threads=self.config.threads,
                verbose=False
            )
            
            self.loaded = True
            logger.info(f"Loaded llama.cpp model with {n_gpu_layers} GPU layers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load llama.cpp model: {e}")
            return False
    
    def unload(self):
        if self.model:
            # llama.cpp models are freed when the object is deleted
            del self.model
            self.model = None
            self.loaded = False
            logger.info("Unloaded llama.cpp model")
    
    def generate(self, prompt: str, thinking_mode: str = "normal") -> str:
        if not self.loaded or not self.model:
            return "Model not loaded"
        
        try:
            # Modify prompt based on thinking mode
            formatted_prompt = self._format_prompt(prompt, thinking_mode)
            
            # Generate response
            response = self.model(
                formatted_prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repeat_penalty=self.config.repeat_penalty,
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _calculate_gpu_layers(self) -> int:
        """Calculate optimal number of GPU layers for RTX 2060"""
        if self.config.gpu_layers == -1:
            # Auto-detect based on model size and available VRAM
            model_size_gb = os.path.getsize(self.model_path) / (1024**3)
            
            if model_size_gb <= 2.0:
                return 35  # Small models can use more layers
            elif model_size_gb <= 4.0:
                return 28  # Medium models
            elif model_size_gb <= 7.0:
                return 20  # Larger models like 7B
            else:
                return 15  # Very large models
        else:
            return self.config.gpu_layers
    
    def _format_prompt(self, prompt: str, thinking_mode: str) -> str:
        """Format prompt based on thinking mode"""
        if thinking_mode == "thinking":
            return f"""Think step by step about this question:

{prompt}

Let me think through this:
1. First, I'll analyze what you're asking
2. Then I'll consider the relevant information
3. Finally, I'll provide a comprehensive response

"""
        elif thinking_mode == "research":
            return f"""Please provide a research-grade analysis of this question:

{prompt}

I'll examine this from multiple perspectives:

**Analysis:**
- Primary interpretation
- Alternative viewpoints
- Key considerations

**Research approach:**
1. Examining available information
2. Considering different angles
3. Synthesizing comprehensive insights

**Response:**
"""
        else:
            return prompt

class TransformersModel(BaseModel):
    """Transformers/PyTorch model implementation"""
    
    def load(self) -> bool:
        if not TRANSFORMERS_AVAILABLE:
            logger.error("transformers not available")
            return False
            
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Configure for RTX 2060
            device_map = "auto" if torch.cuda.is_available() else "cpu"
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=device_map,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )
            
            self.loaded = True
            logger.info(f"Loaded transformers model on {device_map}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load transformers model: {e}")
            return False
    
    def unload(self):
        if self.model:
            del self.model
            del self.tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
            self.loaded = False
            logger.info("Unloaded transformers model")
    
    def generate(self, prompt: str, thinking_mode: str = "normal") -> str:
        if not self.loaded or not self.model or not self.tokenizer:
            return "Model not loaded"
        
        try:
            # Format prompt
            formatted_prompt = self._format_prompt(prompt, thinking_mode)
            
            # Tokenize
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the input prompt from the response
            response = response[len(formatted_prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _format_prompt(self, prompt: str, thinking_mode: str) -> str:
        """Format prompt for transformers models"""
        # Similar to LlamaCppModel but may need model-specific formatting
        return LlamaCppModel._format_prompt(self, prompt, thinking_mode)

class ModelManager:
    """Manages different model types and provides unified interface"""
    
    def __init__(self):
        self.current_model: Optional[BaseModel] = None
        self.config = ModelConfig()
    
    def detect_model_type(self, model_path: str) -> str:
        """Detect model type from file extension"""
        path = Path(model_path)
        extension = path.suffix.lower()
        
        if extension in ['.gguf', '.ggml']:
            return 'llama_cpp'
        elif extension in ['.bin', '.safetensors'] or path.is_dir():
            return 'transformers'
        else:
            return 'unknown'
    
    def load_model(self, model_path: str) -> bool:
        """Load a model automatically detecting its type"""
        # Unload current model if any
        if self.current_model:
            self.unload_model()
        
        model_type = self.detect_model_type(model_path)
        
        if model_type == 'llama_cpp' and LLAMA_CPP_AVAILABLE:
            self.current_model = LlamaCppModel(model_path, self.config)
        elif model_type == 'transformers' and TRANSFORMERS_AVAILABLE:
            self.current_model = TransformersModel(model_path, self.config)
        else:
            logger.error(f"Unsupported model type or dependencies not available: {model_type}")
            return False
        
        return self.current_model.load()
    
    def unload_model(self):
        """Unload the current model"""
        if self.current_model:
            self.current_model.unload()
            self.current_model = None
    
    def generate(self, prompt: str, thinking_mode: str = "normal") -> str:
        """Generate response using current model"""
        if not self.current_model or not self.current_model.loaded:
            return "No model loaded"
        
        return self.current_model.generate(prompt, thinking_mode)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        if not self.current_model:
            return {"loaded": False}
        
        info = self.current_model.get_info()
        info.update({
            "config": {
                "gpu_layers": self.config.gpu_layers,
                "context_length": self.config.context_length,
                "temperature": self.config.temperature
            }
        })
        return info
    
    def update_config(self, **kwargs):
        """Update model configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

# Global model manager instance
model_manager = ModelManager()