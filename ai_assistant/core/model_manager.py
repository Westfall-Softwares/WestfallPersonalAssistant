"""
WestfallPersonalAssistant AI Model Manager
Handles LLaVA model discovery, loading, and management with flexible quantization support
"""

import os
import sys
import json
import glob
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QProgressDialog, QApplication

# Common model directories to search
COMMON_MODEL_DIRS = [
    "models",
    "~/models",
    "~/.cache/huggingface",
    "~/.cache/ollama",
    "/usr/local/share/ollama/models",
    "/opt/models",
    "C:\\models",
    "C:\\Users\\{username}\\AppData\\Local\\ollama\\models",
    "D:\\models"
]

# Supported model formats and their characteristics
MODEL_FORMATS = {
    'gguf': {
        'extensions': ['.gguf'],
        'framework': 'llama.cpp',
        'supports_gpu': True,
        'memory_efficient': True
    },
    'onnx': {
        'extensions': ['.onnx'],
        'framework': 'onnxruntime',
        'supports_gpu': True,
        'memory_efficient': False
    },
    'pytorch': {
        'extensions': ['.bin', '.pt', '.pth'],
        'framework': 'transformers',
        'supports_gpu': True,
        'memory_efficient': False
    },
    'safetensors': {
        'extensions': ['.safetensors'],
        'framework': 'transformers',
        'supports_gpu': True,
        'memory_efficient': False
    }
}

class ModelInfo:
    """Information about a discovered AI model"""
    
    def __init__(self, path: str, model_type: str = "unknown"):
        self.path = Path(path)
        self.model_type = model_type
        self.format_type = self._detect_format()
        self.quantization = self._detect_quantization()
        self.size_gb = self._get_size()
        self.capabilities = self._detect_capabilities()
        
    def _detect_format(self) -> str:
        """Detect model format from file extension"""
        extension = self.path.suffix.lower()
        for format_name, info in MODEL_FORMATS.items():
            if extension in info['extensions']:
                return format_name
        return 'unknown'
    
    def _detect_quantization(self) -> str:
        """Detect quantization level from filename"""
        name_lower = self.path.name.lower()
        
        # GGUF quantization patterns
        gguf_quants = ['q2_k', 'q3_k_s', 'q3_k_m', 'q3_k_l', 'q4_0', 'q4_1', 'q4_k_s', 'q4_k_m', 'q5_0', 'q5_1', 'q5_k_s', 'q5_k_m', 'q6_k', 'q8_0', 'f16', 'f32']
        for quant in gguf_quants:
            if quant in name_lower:
                return quant.upper()
        
        # General quantization patterns
        if 'int8' in name_lower or '8bit' in name_lower:
            return 'INT8'
        elif 'int4' in name_lower or '4bit' in name_lower:
            return 'INT4'
        elif 'fp16' in name_lower or 'half' in name_lower:
            return 'FP16'
        elif 'fp32' in name_lower or 'float32' in name_lower:
            return 'FP32'
        
        return 'unknown'
    
    def _get_size(self) -> float:
        """Get model size in GB"""
        try:
            return self.path.stat().st_size / (1024**3)
        except:
            return 0.0
    
    def _detect_capabilities(self) -> List[str]:
        """Detect model capabilities based on name and type"""
        capabilities = []
        name_lower = self.path.name.lower()
        
        if 'llava' in name_lower:
            capabilities.extend(['vision', 'chat', 'multimodal'])
        elif 'vision' in name_lower:
            capabilities.extend(['vision', 'multimodal'])
        elif 'chat' in name_lower or 'instruct' in name_lower:
            capabilities.append('chat')
        
        # Format-specific capabilities
        format_info = MODEL_FORMATS.get(self.format_type, {})
        if format_info.get('supports_gpu'):
            capabilities.append('gpu_acceleration')
        if format_info.get('memory_efficient'):
            capabilities.append('memory_efficient')
            
        return capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'path': str(self.path),
            'model_type': self.model_type,
            'format_type': self.format_type,
            'quantization': self.quantization,
            'size_gb': self.size_gb,
            'capabilities': self.capabilities,
            'framework': MODEL_FORMATS.get(self.format_type, {}).get('framework', 'unknown')
        }


class ModelDiscoveryThread(QThread):
    """Background thread for model discovery"""
    
    model_found = pyqtSignal(str, dict)  # path, model_info
    discovery_completed = pyqtSignal(int)  # total_models_found
    progress_updated = pyqtSignal(str)  # status_message
    
    def __init__(self, search_dirs: List[str] = None):
        super().__init__()
        self.search_dirs = search_dirs or COMMON_MODEL_DIRS
        self.stop_requested = False
    
    def stop(self):
        """Request thread to stop"""
        self.stop_requested = True
    
    def run(self):
        """Run model discovery"""
        found_models = 0
        
        for search_dir in self.search_dirs:
            if self.stop_requested:
                break
                
            try:
                # Expand user path
                expanded_dir = os.path.expanduser(search_dir)
                if '{username}' in expanded_dir:
                    expanded_dir = expanded_dir.format(username=os.getenv('USERNAME', os.getenv('USER', 'user')))
                
                if not os.path.exists(expanded_dir):
                    continue
                
                self.progress_updated.emit(f"Scanning {expanded_dir}...")
                
                # Search for model files
                search_patterns = []
                for format_info in MODEL_FORMATS.values():
                    for ext in format_info['extensions']:
                        search_patterns.append(f"**/*{ext}")
                
                for pattern in search_patterns:
                    if self.stop_requested:
                        break
                        
                    for file_path in glob.glob(os.path.join(expanded_dir, pattern), recursive=True):
                        if self.stop_requested:
                            break
                            
                        if self._is_likely_model(file_path):
                            model_info = ModelInfo(file_path)
                            self.model_found.emit(file_path, model_info.to_dict())
                            found_models += 1
                            
            except Exception as e:
                logging.warning(f"Error scanning {search_dir}: {e}")
        
        self.discovery_completed.emit(found_models)
    
    def _is_likely_model(self, file_path: str) -> bool:
        """Check if file is likely an AI model"""
        name_lower = os.path.basename(file_path).lower()
        
        # Size check - models are typically large
        try:
            size_mb = os.path.getsize(file_path) / (1024**2)
            if size_mb < 10:  # Less than 10MB is unlikely to be a model
                return False
        except:
            return False
        
        # Name pattern checks
        model_indicators = [
            'llava', 'llama', 'mistral', 'vicuna', 'alpaca', 'chatglm',
            'baichuan', 'qwen', 'internlm', 'openchat', 'neural-chat',
            'starling', 'solar', 'mixtral', 'phi', 'gemma', 'codellama'
        ]
        
        return any(indicator in name_lower for indicator in model_indicators)


class ModelManager(QObject):
    """Manages AI model discovery, loading, and configuration"""
    
    model_loaded = pyqtSignal(str, dict)  # model_path, model_info
    loading_failed = pyqtSignal(str, str)  # model_path, error_message
    discovery_progress = pyqtSignal(str)  # status_message
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        self.discovered_models: Dict[str, ModelInfo] = {}
        self.loaded_model: Optional[ModelInfo] = None
        self.model_cache_file = "data/model_cache.json"
        self.discovery_thread: Optional[ModelDiscoveryThread] = None
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Load cached model information
        self._load_model_cache()
        
        self._initialized = True
    
    def discover_models(self, progress_callback=None) -> None:
        """Start model discovery in background thread"""
        if self.discovery_thread and self.discovery_thread.isRunning():
            return
        
        self.discovery_thread = ModelDiscoveryThread()
        self.discovery_thread.model_found.connect(self._on_model_found)
        self.discovery_thread.discovery_completed.connect(self._on_discovery_completed)
        self.discovery_thread.progress_updated.connect(self.discovery_progress.emit)
        
        if progress_callback:
            self.discovery_thread.progress_updated.connect(progress_callback)
        
        self.discovery_thread.start()
    
    def _on_model_found(self, path: str, model_dict: Dict[str, Any]):
        """Handle discovered model"""
        model_info = ModelInfo(path)
        model_info.__dict__.update(model_dict)
        self.discovered_models[path] = model_info
        logging.info(f"Discovered model: {path} ({model_info.quantization}, {model_info.size_gb:.1f}GB)")
    
    def _on_discovery_completed(self, total_found: int):
        """Handle discovery completion"""
        self._save_model_cache()
        logging.info(f"Model discovery completed. Found {total_found} models.")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of discovered models"""
        return [model.to_dict() for model in self.discovered_models.values()]
    
    def get_llava_models(self) -> List[Dict[str, Any]]:
        """Get specifically LLaVA models with vision capabilities"""
        llava_models = []
        for model in self.discovered_models.values():
            if 'vision' in model.capabilities and 'llava' in model.path.name.lower():
                llava_models.append(model.to_dict())
        return llava_models
    
    def get_recommended_model(self) -> Optional[Dict[str, Any]]:
        """Get the recommended model based on capabilities and size"""
        llava_models = self.get_llava_models()
        if not llava_models:
            return None
        
        # Prefer models with good balance of size and capabilities
        def model_score(model):
            score = 0
            # Prefer GGUF format (more efficient)
            if model['format_type'] == 'gguf':
                score += 10
            # Prefer quantized models (faster)
            if model['quantization'] != 'unknown':
                score += 5
            # Prefer medium-sized models (not too big, not too small)
            if 3 <= model['size_gb'] <= 15:
                score += 5
            # Bonus for vision capabilities
            if 'vision' in model['capabilities']:
                score += 15
            return score
        
        return max(llava_models, key=model_score)
    
    def load_model(self, model_path: str) -> bool:
        """Load a specific model (placeholder - actual loading depends on framework)"""
        try:
            if model_path not in self.discovered_models:
                raise ValueError(f"Model not found: {model_path}")
            
            model_info = self.discovered_models[model_path]
            
            # For now, just mark as loaded (actual loading would depend on framework)
            self.loaded_model = model_info
            self.model_loaded.emit(model_path, model_info.to_dict())
            
            logging.info(f"Model loaded: {model_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load model {model_path}: {e}"
            logging.error(error_msg)
            self.loading_failed.emit(model_path, error_msg)
            return False
    
    def unload_model(self):
        """Unload currently loaded model"""
        if self.loaded_model:
            logging.info(f"Unloading model: {self.loaded_model.path}")
            self.loaded_model = None
    
    def get_loaded_model(self) -> Optional[Dict[str, Any]]:
        """Get information about currently loaded model"""
        return self.loaded_model.to_dict() if self.loaded_model else None
    
    def _load_model_cache(self):
        """Load cached model information from disk"""
        try:
            if os.path.exists(self.model_cache_file):
                with open(self.model_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                for path, model_dict in cache_data.items():
                    if os.path.exists(path):  # Only load if file still exists
                        model_info = ModelInfo(path)
                        model_info.__dict__.update(model_dict)
                        self.discovered_models[path] = model_info
        except Exception as e:
            logging.warning(f"Failed to load model cache: {e}")
    
    def _save_model_cache(self):
        """Save discovered models to cache"""
        try:
            cache_data = {path: model.to_dict() for path, model in self.discovered_models.items()}
            with open(self.model_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save model cache: {e}")
    
    def add_custom_model_directory(self, directory: str):
        """Add a custom directory to search for models"""
        if directory not in COMMON_MODEL_DIRS:
            COMMON_MODEL_DIRS.append(directory)
    
    def download_model(self, model_url: str, progress_callback=None) -> bool:
        """Download a model from URL (placeholder implementation)"""
        # This would implement actual model downloading
        # For now, just a placeholder
        logging.info(f"Model download requested: {model_url}")
        return False


def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    return ModelManager()


class AIAssistantManager(QObject):
    """High-level manager for AI assistant integration across the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_manager = get_model_manager()
        self.active_providers = {}
        
    def init_ai_system(self):
        """Initialize the AI system with model discovery"""
        self.model_manager.discover_models()
        
        # Try to auto-load a recommended model
        recommended = self.model_manager.get_recommended_model()
        if recommended:
            self.model_manager.load_model(recommended['path'])
    
    def register_component(self, component_name: str, context_extractor: callable):
        """Register a component that can provide context to AI"""
        # This allows components to register themselves for AI integration
        pass
    
    def get_system_context(self) -> Dict[str, Any]:
        """Get current system context for AI queries"""
        context = {
            'loaded_model': self.model_manager.get_loaded_model(),
            'available_models': len(self.model_manager.discovered_models),
            'timestamp': datetime.now().isoformat()
        }
        return context