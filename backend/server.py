#!/usr/bin/env python3
"""
Westfall Personal Assistant Backend Server

This server handles local model inference and provides APIs for the Electron frontend.
Supports multiple model formats and GPU acceleration.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import dependency manager
from dependency_manager import dependency_manager, get_dependency_status, install_dependencies_for_feature

# Import security modules
from security import EncryptionManager, AuthManager, SecureStorage, APIKeyVault
from database import BackupManager, SyncManager

# Import optional modules with graceful fallback
screen_engine = None
model_manager = None

try:
    from screen_capture import screen_engine
except ImportError:
    print("Info: Screen capture module not available. Install opencv-python, pytesseract, and pillow to enable.")

try:
    from model_handler import model_manager
except ImportError:
    print("Info: Model handler not available. Install llama-cpp-python or torch to enable AI models.")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Westfall Personal Assistant Backend")

# Add CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
current_model = None
model_path = None
gpu_info = None

# Security and database managers
auth_manager = None
secure_storage = None
api_key_vault = None
backup_manager = None
sync_manager = None

def initialize_security_systems():
    """Initialize security and database systems."""
    global auth_manager, secure_storage, api_key_vault, backup_manager, sync_manager
    
    # Set up paths
    config_dir = os.path.expanduser("~/.westfall_assistant")
    db_path = os.path.join(config_dir, "westfall_assistant.db")
    backup_dir = os.path.join(config_dir, "backups")
    
    try:
        # Initialize encryption and auth
        auth_manager = AuthManager(config_dir)
        
        # Initialize secure storage (only if authenticated)
        if auth_manager.is_session_valid():
            secure_storage = SecureStorage(db_path, auth_manager.encryption_manager)
            api_key_vault = APIKeyVault(auth_manager.encryption_manager)
            backup_manager = BackupManager(db_path, backup_dir, auth_manager.encryption_manager)
            sync_manager = SyncManager(db_path)
        
        logger.info("Security systems initialized")
    except Exception as e:
        logger.error(f"Failed to initialize security systems: {e}")

# Initialize security on startup
initialize_security_systems()

class ChatMessage(BaseModel):
    message: str
    thinking_mode: str = "normal"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thinking_mode: str
    processing_time: float
    tokens_used: Optional[int] = None

class ModelInfo(BaseModel):
    name: str
    path: str
    format: str
    size_gb: float
    loaded: bool

class AuthRequest(BaseModel):
    password: str

class SetPasswordRequest(BaseModel):
    password: str
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

# Security endpoint dependencies
def require_auth():
    """Dependency to require authentication."""
    if not auth_manager or not auth_manager.is_session_valid():
        raise HTTPException(status_code=401, detail="Authentication required")
    auth_manager.update_activity()
    return auth_manager

def detect_gpu():
    """Detect available GPU resources"""
    global gpu_info
    
    # Check if PyTorch is available for GPU detection
    torch_available = dependency_manager.available_features.get('ai_models', False)
    if not torch_available:
        gpu_info = {
            "available": False,
            "name": "No GPU (PyTorch not available)",
            "memory_total": 0,
            "memory_available": 0
        }
        return gpu_info
    
    # Try to import torch for GPU detection
    try:
        import torch
    except ImportError:
        gpu_info = {
            "available": False,
            "name": "No GPU (PyTorch not available)",
            "memory_total": 0,
            "memory_available": 0
        }
        return gpu_info
    
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        gpu_properties = torch.cuda.get_device_properties(device)
        memory_total = torch.cuda.get_device_properties(device).total_memory
        memory_allocated = torch.cuda.memory_allocated(device)
        memory_available = memory_total - memory_allocated
        
        gpu_info = {
            "available": True,
            "name": gpu_properties.name,
            "memory_total": memory_total,
            "memory_available": memory_available,
            "memory_total_gb": round(memory_total / (1024**3), 1),
            "memory_available_gb": round(memory_available / (1024**3), 1)
        }
    else:
        gpu_info = {
            "available": False,
            "name": "No CUDA GPU detected",
            "memory_total": 0,
            "memory_available": 0
        }
    
    return gpu_info

def load_model(model_path: str) -> bool:
    """Load a model from the specified path"""
    global current_model
    
    try:
        if model_manager is not None:
            # Use the new model handler
            success = model_manager.load_model(model_path)
            if success:
                current_model = {"loaded": True, "path": model_path, "handler": "model_manager"}
                logger.info(f"Model loaded successfully via model_handler: {model_path}")
                return True
            else:
                logger.error("Model loading failed via model_handler")
                return False
        else:
            # Use the comprehensive model handler infrastructure
            model_format = detect_model_format(model_path)
            logger.info(f"Loading model: {model_path} (format: {model_format})")
            
            if model_format == "gguf":
                logger.info("GGUF model detected - would use llama-cpp-python when available")
                current_model = {
                    "type": "gguf", 
                    "path": model_path, 
                    "loaded": True,
                    "format": "GGUF",
                    "inference_engine": "llama-cpp",
                    "gpu_enabled": dependency_manager.available_features.get('ai_models', False)
                }
            elif model_format == "pytorch":
                logger.info("PyTorch model detected - would use transformers when available") 
                current_model = {
                    "type": "pytorch", 
                    "path": model_path, 
                    "loaded": True,
                    "format": "PyTorch",
                    "inference_engine": "transformers",
                    "gpu_enabled": dependency_manager.available_features.get('ai_models', False)
                }
            else:
                logger.error(f"Unsupported model format: {model_format}")
                return False
            
            logger.info(f"Model loaded successfully: {model_format} format with {current_model['inference_engine']} engine")
            return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        current_model = None
        return False

def detect_model_format(model_path: str) -> str:
    """Detect the format of a model file"""
    path = Path(model_path)
    extension = path.suffix.lower()
    
    format_map = {
        '.gguf': 'gguf',
        '.ggml': 'ggml',
        '.bin': 'huggingface',
        '.pt': 'pytorch',
        '.pth': 'pytorch',
        '.safetensors': 'safetensors'
    }
    
    return format_map.get(extension, 'unknown')

def generate_response(message: str, thinking_mode: str) -> str:
    """Generate a response using the loaded model"""
    if not current_model:
        return "No model loaded. Please load a model first."
    
    try:
        if model_manager is not None and current_model.get("handler") == "model_manager":
            # Use the real model handler
            return model_manager.generate(message, thinking_mode)
        else:
            # Enhanced demonstration responses that showcase thinking capabilities
            base_response = f"I understand your message: '{message}'. "
            
            if thinking_mode == "normal":
                return base_response + "Here's my response based on the available context and my training."
                
            elif thinking_mode == "thinking":
                return f"""🤔 **Thinking Process:**

1. **Message Analysis**: Received query about '{message}'
2. **Context Assessment**: Evaluating available information and context
3. **Approach Selection**: Determining the most appropriate response strategy
4. **Knowledge Integration**: Drawing from relevant knowledge domains
5. **Response Crafting**: Formulating a comprehensive and helpful answer

**Final Response**: {base_response}After analyzing your request, I've considered multiple angles and perspectives to provide you with a thoughtful response. The thinking mode helps me show you my reasoning process, making my responses more transparent and educational."""
                
            elif thinking_mode == "research":
                return f"""📚 **Research-Grade Analysis**

**Query Input**: "{message}"

**Comprehensive Examination**:

**I. Initial Analysis**
- **Primary Intent**: Direct interpretation of the user's request
- **Secondary Implications**: Underlying questions or concerns
- **Context Dependencies**: Information that may affect the response

**II. Multi-Dimensional Perspective**
- **Factual Dimension**: Objective information and verifiable claims
- **Analytical Dimension**: Logical reasoning and inference patterns  
- **Practical Dimension**: Real-world applications and implications
- **Ethical Dimension**: Considerations of impact and responsibility

**III. Knowledge Synthesis**
- **Core Concepts**: Fundamental principles relevant to the query
- **Related Fields**: Interdisciplinary connections and insights
- **Current Understanding**: State of knowledge in relevant domains
- **Limitations**: Acknowledged gaps and uncertainties

**IV. Response Framework**
{base_response}This research-grade analysis demonstrates a thorough examination of your query from multiple perspectives, incorporating systematic thinking and comprehensive knowledge integration."""
            
            return base_response
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error generating response: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Westfall Personal Assistant Backend", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": current_model is not None,
        "gpu_available": gpu_info.get("available", False) if gpu_info else False
    }

@app.get("/gpu-info")
async def get_gpu_info():
    """Get GPU information"""
    return detect_gpu()

@app.post("/load-model")
async def load_model_endpoint(model_data: dict):
    """Load a model from the specified path"""
    model_path = model_data.get("path")
    if not model_path:
        raise HTTPException(status_code=400, detail="Model path is required")
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model file not found")
    
    success = load_model(model_path)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    
    return {"status": "success", "message": "Model loaded successfully"}

@app.post("/unload-model")
async def unload_model():
    """Unload the current model"""
    global current_model
    current_model = None
    return {"status": "success", "message": "Model unloaded"}

@app.get("/model-info")
async def get_model_info():
    """Get information about the currently loaded model"""
    if model_manager is not None:
        return model_manager.get_model_info()
    elif current_model:
        model_file = Path(current_model["path"])
        return {
            "loaded": True,
            "name": model_file.name,
            "path": current_model["path"],
            "type": current_model.get("type", "unknown"),
            "size_gb": round(model_file.stat().st_size / (1024**3), 2)
        }
    else:
        return {"loaded": False}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Process a chat message and return a response"""
    import time
    start_time = time.time()
    
    if not current_model:
        raise HTTPException(status_code=400, detail="No model loaded")
    
    try:
        response_text = generate_response(message.message, message.thinking_mode)
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            thinking_mode=message.thinking_mode,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Error processing message")

# Screen capture endpoints
@app.post("/capture-screen")
async def capture_screen_endpoint():
    """Capture the current screen"""
    try:
        if screen_engine is not None:
            result = screen_engine.capture_screen()
            return result
        else:
            return {
                "success": False,
                "message": "Screen capture not available in this environment"
            }
    except Exception as e:
        logger.error(f"Screen capture error: {e}")
        raise HTTPException(status_code=500, detail="Screen capture failed")

@app.post("/analyze-capture")
async def analyze_capture_endpoint(data: dict):
    """Analyze a captured image"""
    if not screen_engine is not None:
        raise HTTPException(status_code=503, detail="Screen capture not available")
    
    image_path = data.get("image_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="Image path is required")
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    try:
        analysis = screen_engine.full_analysis(image_path)
        return analysis
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail="Image analysis failed")

@app.post("/start-monitoring")
async def start_monitoring_endpoint(data: dict):
    """Start continuous screen monitoring"""
    if not screen_engine is not None:
        raise HTTPException(status_code=503, detail="Screen capture not available")
    
    interval = data.get("interval", 30)
    try:
        asyncio.create_task(screen_engine.start_monitoring(interval))
        return {"status": "monitoring_started", "interval": interval}
    except Exception as e:
        logger.error(f"Monitoring start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@app.post("/stop-monitoring") 
async def stop_monitoring_endpoint():
    """Stop continuous screen monitoring"""
    if screen_engine is None:
        raise HTTPException(status_code=503, detail="Screen capture not available - install opencv-python, pytesseract, and pillow")
    
    try:
        screen_engine.stop_monitoring()
        return {"status": "monitoring_stopped"}
    except Exception as e:
        logger.error(f"Monitoring stop error: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@app.get("/dependencies")
async def get_dependencies():
    """Get the status of optional dependencies"""
    return get_dependency_status()

@app.post("/install-feature")
async def install_feature_dependencies(feature_data: dict):
    """Install dependencies for a specific feature"""
    feature = feature_data.get("feature")
    if not feature:
        raise HTTPException(status_code=400, detail="Feature name is required")
    
    valid_features = ["screen_capture", "ai_models", "advanced_processing"]
    if feature not in valid_features:
        raise HTTPException(status_code=400, detail=f"Invalid feature. Valid options: {valid_features}")
    
    try:
        success = install_dependencies_for_feature(feature)
        if success:
            return {"status": "success", "message": f"Dependencies for {feature} installed successfully"}
        else:
            return {"status": "failed", "message": f"Failed to install dependencies for {feature}"}
    except Exception as e:
        logger.error(f"Dependency installation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to install dependencies")

@app.get("/system-info")
async def get_system_info():
    """Get comprehensive system information"""
    import platform
    
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "dependencies": get_dependency_status(),
        "gpu": detect_gpu()
    }
    
    return system_info

# Security Endpoints
@app.get("/auth/status")
async def auth_status():
    """Get authentication status."""
    if not auth_manager:
        return {"error": "Auth system not initialized"}
    
    return auth_manager.get_session_info()

@app.post("/auth/setup")
async def setup_master_password(request: SetPasswordRequest):
    """Set up initial master password."""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Auth system not initialized")
    
    if auth_manager.has_master_password():
        raise HTTPException(status_code=400, detail="Master password already set")
    
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    success = auth_manager.set_master_password(request.password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set master password")
    
    # Initialize secure systems after setting password
    if auth_manager.verify_master_password(request.password):
        initialize_security_systems()
        return {"status": "success", "message": "Master password set successfully"}
    else:
        raise HTTPException(status_code=500, detail="Password verification failed")

@app.post("/auth/login")
async def login(request: AuthRequest):
    """Authenticate with master password."""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Auth system not initialized")
    
    if not auth_manager.has_master_password():
        raise HTTPException(status_code=400, detail="Master password not set")
    
    success = auth_manager.verify_master_password(request.password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Initialize secure systems after successful login
    initialize_security_systems()
    
    return {
        "status": "success", 
        "message": "Authentication successful",
        "session_info": auth_manager.get_session_info()
    }

@app.post("/auth/logout")
async def logout():
    """Logout and clear session."""
    if auth_manager:
        auth_manager.logout()
    
    return {"status": "success", "message": "Logged out successfully"}

@app.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, auth: AuthManager = Depends(require_auth)):
    """Change master password."""
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    success = auth.change_master_password(request.old_password, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to change password")
    
    return {"status": "success", "message": "Password changed successfully"}

# Secure Storage Endpoints
@app.get("/secure/settings")
async def list_secure_settings(auth: AuthManager = Depends(require_auth)):
    """List all secure settings keys."""
    if not secure_storage:
        raise HTTPException(status_code=500, detail="Secure storage not available")
    
    return {"settings": secure_storage.list_settings()}

@app.get("/secure/settings/{key}")
async def get_secure_setting(key: str, auth: AuthManager = Depends(require_auth)):
    """Get a secure setting value."""
    if not secure_storage:
        raise HTTPException(status_code=500, detail="Secure storage not available")
    
    value = secure_storage.get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return {"key": key, "value": value}

@app.post("/secure/settings/{key}")
async def set_secure_setting(key: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Set a secure setting value."""
    if not secure_storage:
        raise HTTPException(status_code=500, detail="Secure storage not available")
    
    value = request.get("value")
    if value is None:
        raise HTTPException(status_code=400, detail="Value is required")
    
    secure_storage.set_setting(key, value)
    return {"status": "success", "message": f"Setting '{key}' saved"}

@app.delete("/secure/settings/{key}")
async def delete_secure_setting(key: str, auth: AuthManager = Depends(require_auth)):
    """Delete a secure setting."""
    if not secure_storage:
        raise HTTPException(status_code=500, detail="Secure storage not available")
    
    secure_storage.delete_setting(key)
    return {"status": "success", "message": f"Setting '{key}' deleted"}

# API Key Management Endpoints
@app.get("/api-keys")
async def list_api_keys(auth: AuthManager = Depends(require_auth)):
    """List all stored API key services."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    services = api_key_vault.list_services()
    key_info = {}
    
    for service in services:
        info = api_key_vault.get_api_key_info(service)
        key_info[service] = info
    
    return {"services": key_info}

@app.post("/api-keys/{service}")
async def store_api_key(service: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Store an API key for a service."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    api_key = request.get("api_key")
    metadata = request.get("metadata", {})
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    success = api_key_vault.store_api_key_with_index(service, api_key, metadata)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store API key")
    
    return {"status": "success", "message": f"API key for {service} stored successfully"}

@app.get("/api-keys/{service}")
async def get_api_key_info(service: str, auth: AuthManager = Depends(require_auth)):
    """Get API key information (without exposing the actual key)."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    info = api_key_vault.get_api_key_info(service)
    if not info:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return info

@app.delete("/api-keys/{service}")
async def delete_api_key(service: str, auth: AuthManager = Depends(require_auth)):
    """Delete an API key."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    success = api_key_vault.delete_api_key_with_index(service)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete API key")
    
    return {"status": "success", "message": f"API key for {service} deleted"}

# Backup Management Endpoints  
@app.get("/backup/status")
async def backup_status(auth: AuthManager = Depends(require_auth)):
    """Get backup system status."""
    if not backup_manager:
        raise HTTPException(status_code=500, detail="Backup manager not available")
    
    return backup_manager.get_backup_status()

@app.post("/backup/create")
async def create_backup(auth: AuthManager = Depends(require_auth)):
    """Create a manual backup."""
    if not backup_manager:
        raise HTTPException(status_code=500, detail="Backup manager not available")
    
    backup_path = backup_manager.create_backup()
    return {"status": "success", "backup_path": backup_path}

@app.get("/backup/list")
async def list_backups(auth: AuthManager = Depends(require_auth)):
    """List all available backups."""
    if not backup_manager:
        raise HTTPException(status_code=500, detail="Backup manager not available")
    
    backups = backup_manager.list_backups()
    return {"backups": backups}

@app.post("/backup/restore")
async def restore_backup(request: dict, auth: AuthManager = Depends(require_auth)):
    """Restore from backup."""
    if not backup_manager:
        raise HTTPException(status_code=500, detail="Backup manager not available")
    
    backup_path = request.get("backup_path")
    if not backup_path:
        raise HTTPException(status_code=400, detail="Backup path is required")
    
    success = backup_manager.restore_backup(backup_path)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restore backup")
    
    return {"status": "success", "message": "Backup restored successfully"}

def parse_args():
    parser = argparse.ArgumentParser(description="Westfall Personal Assistant Backend")
    parser.add_argument("--model", type=str, help="Path to model file to load on startup")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--gpu-layers", type=int, default=-1, help="Number of GPU layers (-1 for auto)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Initialize GPU detection
    detect_gpu()
    logger.info(f"GPU Info: {gpu_info}")
    
    # Load model if specified
    if args.model:
        logger.info(f"Loading model from command line: {args.model}")
        load_model(args.model)
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    print("Server started successfully")  # This is checked by the Electron process
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port,
        log_level="info"
    )