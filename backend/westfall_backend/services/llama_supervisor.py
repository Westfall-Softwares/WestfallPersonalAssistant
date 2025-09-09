"""
LLM supervisor service for managing llama.cpp models and inference.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime

from .settings import get_settings, Settings


class LlamaSupervisor:
    """Supervisor for managing llama.cpp model loading and inference."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_path: Optional[Path] = None
        self.model_info: Dict[str, Any] = {}
        self.is_loading = False
        self.load_time: Optional[float] = None
        
        # Try to import llama_cpp
        try:
            from llama_cpp import Llama
            self.Llama = Llama
            self.llama_cpp_available = True
            self.logger.info("llama-cpp-python is available")
        except ImportError:
            self.Llama = None
            self.llama_cpp_available = False
            self.logger.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")
    
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.model is not None and not self.is_loading
    
    def get_model_name(self) -> Optional[str]:
        """Get the name of the currently loaded model."""
        if self.model_path:
            return self.model_path.name
        return None
    
    def get_model_size(self) -> Optional[str]:
        """Get the size of the currently loaded model."""
        if self.model_path and self.model_path.exists():
            size_bytes = self.model_path.stat().st_size
            # Convert to human-readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the current model."""
        if not self.is_model_loaded():
            return {"loaded": False}
        
        return {
            "loaded": True,
            "name": self.get_model_name(),
            "path": str(self.model_path) if self.model_path else None,
            "size": self.get_model_size(),
            "context_length": self.settings.llm.context_length,
            "gpu_layers": self.settings.llm.gpu_layers,
            "load_time": self.load_time,
            **self.model_info
        }
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Get current model info in API format."""
        info = self.get_model_info()
        if not info.get("loaded"):
            raise ValueError("No model loaded")
        
        return {
            "name": info.get("name", "unknown"),
            "size": info.get("size"),
            "type": "gguf",
            "loaded": True,
            "context_length": info.get("context_length", 4096),
            "parameters": {
                "gpu_layers": info.get("gpu_layers", 0),
                "temperature": self.settings.llm.temperature,
                "top_p": self.settings.llm.top_p,
                "top_k": self.settings.llm.top_k,
                "max_tokens": self.settings.llm.max_tokens
            }
        }
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in the models directory."""
        models = []
        
        if self.settings.data.models_dir.exists():
            for model_file in self.settings.data.models_dir.glob("*.gguf"):
                size = model_file.stat().st_size
                models.append({
                    "name": model_file.name,
                    "path": str(model_file),
                    "size": size,
                    "type": "gguf",
                    "loaded": str(model_file) == str(self.model_path)
                })
        
        return models
    
    async def load_model(self, model_path: str, gpu_layers: Optional[int] = None, context_length: Optional[int] = None) -> bool:
        """Load a model for inference."""
        if not self.llama_cpp_available:
            self.logger.error("Cannot load model: llama-cpp-python not available")
            return False
        
        if self.is_loading:
            self.logger.warning("Model loading already in progress")
            return False
        
        self.is_loading = True
        start_time = time.time()
        
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Unload current model if any
            if self.model:
                await self.unload_model()
            
            # Use provided settings or defaults
            gpu_layers = gpu_layers if gpu_layers is not None else self.settings.llm.gpu_layers
            context_length = context_length if context_length is not None else self.settings.llm.context_length
            
            self.logger.info(f"Loading model: {model_path} with {gpu_layers} GPU layers")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                self._load_model_sync,
                str(model_path),
                gpu_layers,
                context_length
            )
            
            self.model_path = model_path
            self.load_time = time.time() - start_time
            
            # Store model info
            self.model_info = {
                "loaded_at": datetime.utcnow().isoformat(),
                "load_duration": self.load_time,
                "gpu_layers_used": gpu_layers,
                "context_length_used": context_length
            }
            
            self.logger.info(f"Model loaded successfully in {self.load_time:.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self.model = None
            self.model_path = None
            self.model_info = {}
            return False
        
        finally:
            self.is_loading = False
    
    def _load_model_sync(self, model_path: str, gpu_layers: int, context_length: int):
        """Synchronous model loading (run in thread pool)."""
        return self.Llama(
            model_path=model_path,
            n_gpu_layers=gpu_layers,
            n_ctx=context_length,
            n_batch=512,
            verbose=False
        )
    
    async def unload_model(self) -> bool:
        """Unload the current model."""
        if self.model:
            try:
                # Clean up model
                del self.model
                self.model = None
                self.model_path = None
                self.model_info = {}
                self.load_time = None
                
                self.logger.info("Model unloaded successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error unloading model: {e}")
                return False
        
        return True
    
    async def generate_response(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]] = None,
        thinking_mode: str = "normal",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> tuple[str, Optional[int]]:
        """Generate a response using the loaded model."""
        
        if not self.is_model_loaded():
            raise ValueError("No model loaded")
        
        # Prepare the full prompt
        full_prompt = self._prepare_prompt(prompt, conversation_history, thinking_mode)
        
        # Use provided parameters or defaults
        max_tokens = max_tokens or self.settings.llm.max_tokens
        temperature = temperature if temperature is not None else self.settings.llm.temperature
        
        try:
            # Generate in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._generate_sync,
                full_prompt,
                max_tokens,
                temperature
            )
            
            response_text = result['choices'][0]['text'].strip()
            tokens_used = result.get('usage', {}).get('total_tokens')
            
            return response_text, tokens_used
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def _generate_sync(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Synchronous generation (run in thread pool)."""
        return self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=self.settings.llm.top_p,
            top_k=self.settings.llm.top_k,
            repeat_penalty=self.settings.llm.repeat_penalty,
            echo=False
        )
    
    async def stream_response(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]] = None,
        thinking_mode: str = "normal",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a response using the loaded model."""
        
        if not self.is_model_loaded():
            raise ValueError("No model loaded")
        
        # For now, yield the full response (streaming would require more complex implementation)
        response, _ = await self.generate_response(
            prompt, conversation_history, thinking_mode, max_tokens, temperature
        )
        
        # Simulate streaming by yielding chunks
        chunk_size = 10
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
    
    def _prepare_prompt(self, prompt: str, conversation_history: List[Dict[str, Any]] = None, thinking_mode: str = "normal") -> str:
        """Prepare the full prompt with context and instructions."""
        
        # Build conversation context
        context_parts = []
        
        # Add system prompt based on thinking mode
        if thinking_mode == "deep":
            context_parts.append("You are a thoughtful AI assistant. Take time to think deeply about each question and provide comprehensive, well-reasoned responses.")
        elif thinking_mode == "creative":
            context_parts.append("You are a creative AI assistant. Think outside the box and provide innovative, imaginative responses.")
        else:
            context_parts.append("You are a helpful AI assistant. Provide clear, accurate, and helpful responses.")
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 10 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    context_parts.append(f"User: {content}")
                elif role == 'assistant':
                    context_parts.append(f"Assistant: {content}")
        
        # Add current prompt
        context_parts.append(f"User: {prompt}")
        context_parts.append("Assistant:")
        
        return "\n".join(context_parts)
    
    async def shutdown(self) -> None:
        """Shutdown the supervisor and clean up resources."""
        self.logger.info("Shutting down LLM supervisor...")
        await self.unload_model()
        self.logger.info("LLM supervisor shutdown complete")