#!/usr/bin/env python3
"""
Local LLM Provider for Westfall Personal Assistant

Integrates with local LLM models using llama.cpp or similar backends.
"""

import asyncio
import logging
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from .provider_interface import AIProvider

logger = logging.getLogger(__name__)


class LocalLLMProvider(AIProvider):
    """Local LLM provider implementation using llama.cpp or compatible backends."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_path = self.config.get("model_path")
        self.backend = self.config.get("backend", "llama_cpp")  # llama_cpp, ollama, etc.
        self.context_length = self.config.get("context_length", 4096)
        self.max_tokens = self.config.get("max_tokens", 512)
        self.temperature = self.config.get("temperature", 0.7)
        self.gpu_layers = self.config.get("gpu_layers", 0)
        
        self.llm_instance = None
        self.backend_process = None
        
        self.capabilities = [
            "text_generation",
            "conversation",
            "local_inference",
            "offline_operation",
            "privacy_focused"
        ]
        
        # Supported model formats
        self.supported_formats = [".gguf", ".ggml", ".bin"]
    
    async def initialize(self) -> bool:
        """Initialize local LLM backend."""
        try:
            if self.backend == "llama_cpp":
                return await self._initialize_llama_cpp()
            elif self.backend == "ollama":
                return await self._initialize_ollama()
            else:
                logger.error(f"Unsupported backend: {self.backend}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize local LLM provider: {e}")
            return False
    
    async def _initialize_llama_cpp(self) -> bool:
        """Initialize with llama-cpp-python."""
        try:
            # Try to import llama_cpp
            try:
                from llama_cpp import Llama
                self.Llama = Llama
            except ImportError:
                logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
                return False
            
            if not self.model_path or not Path(self.model_path).exists():
                logger.error(f"Model file not found: {self.model_path}")
                return False
            
            # Initialize Llama model
            self.llm_instance = self.Llama(
                model_path=self.model_path,
                n_ctx=self.context_length,
                n_gpu_layers=self.gpu_layers,
                verbose=False
            )
            
            self.is_connected = True
            logger.info(f"Local LLM initialized with model: {Path(self.model_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize llama.cpp: {e}")
            return False
    
    async def _initialize_ollama(self) -> bool:
        """Initialize with Ollama backend."""
        try:
            # Check if Ollama is available
            result = subprocess.run(["ollama", "version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Ollama not installed or not in PATH")
                return False
            
            # For Ollama, model_path is actually the model name
            model_name = self.config.get("model_name", "llama2")
            
            # Test if model is available
            test_result = await self._test_ollama_model(model_name)
            if not test_result:
                logger.error(f"Ollama model {model_name} not available")
                return False
            
            self.model_name = model_name
            self.is_connected = True
            logger.info(f"Ollama initialized with model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            return False
    
    async def _test_ollama_model(self, model_name: str) -> bool:
        """Test if Ollama model is available."""
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                models_output = stdout.decode()
                return model_name in models_output
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing Ollama model: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "", thinking_mode: str = "normal", 
                              conversation_history: List[Dict] = None) -> str:
        """Generate response using local LLM."""
        if not self.is_connected:
            return "Local LLM provider not connected. Please check your model configuration."
        
        try:
            # Prepare the full prompt
            full_prompt = self._prepare_prompt(prompt, context, thinking_mode, conversation_history)
            
            if self.backend == "llama_cpp":
                return await self._generate_llama_cpp_response(full_prompt)
            elif self.backend == "ollama":
                return await self._generate_ollama_response(full_prompt)
            else:
                return "Unsupported backend for response generation."
                
        except Exception as e:
            logger.error(f"Local LLM response generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _prepare_prompt(self, prompt: str, context: str, thinking_mode: str, 
                       conversation_history: List[Dict] = None) -> str:
        """Prepare the full prompt for local LLM."""
        prompt_parts = []
        
        # System prompt
        system_prompt = "You are Westfall Personal Assistant, a helpful AI assistant."
        
        if context:
            system_prompt += f" Current context: {context}"
        
        if thinking_mode == "thinking":
            system_prompt += " Please show your reasoning process."
        elif thinking_mode == "research":
            system_prompt += " Please provide a comprehensive analysis."
        
        prompt_parts.append(system_prompt)
        
        # Conversation history
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                if msg.get("type") == "user":
                    prompt_parts.append(f"User: {msg.get('content', '')}")
                elif msg.get("type") == "assistant":
                    prompt_parts.append(f"Assistant: {msg.get('content', '')}")
        
        # Current user message
        prompt_parts.append(f"User: {prompt}")
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_llama_cpp_response(self, prompt: str) -> str:
        """Generate response using llama-cpp-python."""
        try:
            # Generate response
            response = self.llm_instance(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=["User:", "Human:"],
                echo=False
            )
            
            response_text = response["choices"][0]["text"].strip()
            return response_text
            
        except Exception as e:
            logger.error(f"llama.cpp generation error: {e}")
            return "Error generating response with local model."
    
    async def _generate_ollama_response(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            # Prepare Ollama request
            ollama_request = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            # Run Ollama generate command
            process = await asyncio.create_subprocess_exec(
                "ollama", "generate", "--format", "json",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            request_data = json.dumps(ollama_request).encode()
            stdout, stderr = await process.communicate(input=request_data)
            
            if process.returncode == 0:
                response_data = json.loads(stdout.decode())
                return response_data.get("response", "No response from Ollama")
            else:
                logger.error(f"Ollama error: {stderr.decode()}")
                return "Error generating response with Ollama."
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return "Error generating response with Ollama."
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test local LLM connection."""
        if not self.is_connected:
            return {"success": False, "error": "Provider not initialized"}
        
        try:
            # Generate a simple test response
            test_response = await self.generate_response("Hello", "", "normal", [])
            
            return {
                "success": bool(test_response and "Error" not in test_response),
                "backend": self.backend,
                "model": self.model_path or self.model_name,
                "response_preview": test_response[:50] + "..." if len(test_response) > 50 else test_response
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        model_info = {
            "provider": "Local LLM",
            "backend": self.backend,
            "model_path": self.model_path,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "gpu_layers": self.gpu_layers,
            "capabilities": self.capabilities,
            "connected": self.is_connected
        }
        
        if self.backend == "ollama":
            model_info["model_name"] = getattr(self, "model_name", "unknown")
        
        # Add model file info if available
        if self.model_path and Path(self.model_path).exists():
            model_file = Path(self.model_path)
            model_info.update({
                "model_name": model_file.name,
                "model_size_gb": round(model_file.stat().st_size / (1024**3), 2),
                "model_format": model_file.suffix
            })
        
        return model_info
    
    def set_model(self, model_path: str) -> bool:
        """Set the local model to use."""
        if self.backend == "ollama":
            # For Ollama, this is a model name
            self.model_name = model_path
            self.config["model_name"] = model_path
            logger.info(f"Ollama model set to: {model_path}")
            return True
        else:
            # For other backends, this is a file path
            if not Path(model_path).exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            if not any(model_path.endswith(fmt) for fmt in self.supported_formats):
                logger.error(f"Unsupported model format. Supported: {self.supported_formats}")
                return False
            
            self.model_path = model_path
            self.config["model_path"] = model_path
            
            # Reinitialize if needed
            if self.is_connected:
                asyncio.create_task(self.initialize())
            
            logger.info(f"Local model set to: {Path(model_path).name}")
            return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available local models."""
        if self.backend == "ollama":
            # Get Ollama models
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    return [line.split()[0] for line in lines if line.strip()]
            except Exception as e:
                logger.error(f"Error getting Ollama models: {e}")
            
            return []
        else:
            # Scan for local model files
            models = []
            common_paths = [
                Path.home() / "models",
                Path.cwd() / "models",
                Path("/models")  # Common Docker path
            ]
            
            for path in common_paths:
                if path.exists():
                    for fmt in self.supported_formats:
                        models.extend([str(f) for f in path.glob(f"*{fmt}")])
            
            return models
    
    def set_parameters(self, context_length: int = None, max_tokens: int = None, 
                      temperature: float = None, gpu_layers: int = None) -> bool:
        """Set generation parameters."""
        try:
            if context_length is not None:
                self.context_length = max(512, min(32768, context_length))
                self.config["context_length"] = self.context_length
            
            if max_tokens is not None:
                self.max_tokens = max(1, min(4000, max_tokens))
                self.config["max_tokens"] = self.max_tokens
            
            if temperature is not None:
                self.temperature = max(0.0, min(2.0, temperature))
                self.config["temperature"] = self.temperature
            
            if gpu_layers is not None:
                self.gpu_layers = max(0, gpu_layers)
                self.config["gpu_layers"] = self.gpu_layers
            
            return True
        except Exception as e:
            logger.error(f"Failed to set parameters: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup local LLM provider."""
        if self.llm_instance:
            # For llama.cpp, there's no explicit cleanup needed
            self.llm_instance = None
        
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
        
        await super().cleanup()
        logger.info("Local LLM provider cleaned up")