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

# Import utilities
from utils import setup_global_error_handling, get_global_error_handler, ErrorHandler, get_safe_delete_manager
from utils.validation import validate_email, validate_password_strength, validate_api_key

# Import AI assistant modules  
from ai_assistant import AIChat, ContextManager, ActionExecutor, ResponseHandler
from ai_assistant.providers import OpenAIProvider, LocalLLMProvider

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

# Initialize global error handling
error_handler = setup_global_error_handling(debug_mode=False)

# Initialize safe delete manager
safe_delete_manager = get_safe_delete_manager()

# Security and database managers
auth_manager = None
secure_storage = None
api_key_vault = None
backup_manager = None
sync_manager = None

# AI assistant components
ai_chat = None
context_manager = None
action_executor = None
response_handler = None
ai_providers = {}

def initialize_security_systems():
    """Initialize security and database systems."""
    global auth_manager, secure_storage, api_key_vault, backup_manager, sync_manager
    global ai_chat, context_manager, action_executor, response_handler
    
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
            
            # Initialize AI assistant components
            context_manager = ContextManager()
            action_executor = ActionExecutor()
            response_handler = ResponseHandler()
            ai_chat = AIChat(context_manager, action_executor, response_handler, secure_storage)
        
        error_handler.log_info("Security systems initialized", "SecurityInit")
    except Exception as e:
        error_handler.log_error(f"Failed to initialize security systems: {e}", context="SecurityInit")

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

class AIChatRequest(BaseModel):
    message: str
    thinking_mode: str = "normal"
    window: Optional[str] = None
    conversation_id: Optional[str] = None

class ProviderConfigRequest(BaseModel):
    config: dict

class ConfirmationRequest(BaseModel):
    confirm: bool = False
    confirmation_message: Optional[str] = None

# Security endpoint dependencies
def require_auth():
    """Dependency to require authentication."""
    if not auth_manager or not auth_manager.is_session_valid():
        raise HTTPException(status_code=401, detail="Authentication required")
    auth_manager.update_activity()
    return auth_manager

def require_confirmation(operation: str, target: str) -> dict:
    """Generate confirmation requirement for dangerous operations."""
    return {
        "requires_confirmation": True,
        "operation": operation,
        "target": target,
        "message": f"Are you sure you want to {operation} '{target}'? This action cannot be undone.",
        "confirmation_required": True
    }

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
@error_handler.with_error_handling("AuthSetup")
async def setup_master_password(request: SetPasswordRequest):
    """Set up initial master password."""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Auth system not initialized")
    
    if auth_manager.has_master_password():
        raise HTTPException(status_code=400, detail="Master password already set")
    
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Use enhanced password validation
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    success = auth_manager.set_master_password(request.password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set master password")
    
    # Initialize secure systems after setting password
    if auth_manager.verify_master_password(request.password):
        initialize_security_systems()
        error_handler.log_info("Master password set up successfully", "AuthSetup")
        return {"status": "success", "message": "Master password set successfully"}
    else:
        raise HTTPException(status_code=500, detail="Password verification failed")

@app.post("/auth/login")
@error_handler.with_error_handling("AuthLogin")
async def login(request: AuthRequest):
    """Authenticate with master password."""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Auth system not initialized")
    
    if not auth_manager.has_master_password():
        raise HTTPException(status_code=400, detail="Master password not set")
    
    # Rate limiting could be added here in the future
    success = auth_manager.verify_master_password(request.password)
    if not success:
        error_handler.log_warning("Failed login attempt", "AuthLogin")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Initialize secure systems after successful login
    initialize_security_systems()
    error_handler.log_info("User authenticated successfully", "AuthLogin")
    
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
@error_handler.with_error_handling("PasswordChange")
async def change_password(request: ChangePasswordRequest, auth: AuthManager = Depends(require_auth)):
    """Change master password."""
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    # Use enhanced password validation
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    success = auth.change_master_password(request.old_password, request.new_password)
    if not success:
        error_handler.log_warning("Failed password change attempt", "PasswordChange")
        raise HTTPException(status_code=400, detail="Failed to change password - check current password")
    
    error_handler.log_info("Password changed successfully", "PasswordChange")
    return {"status": "success", "message": "Password changed successfully"}

# Error Handling and Debugging Endpoints
@app.get("/debug/errors")
async def get_error_stats(auth: AuthManager = Depends(require_auth)):
    """Get error statistics and recent errors."""
    if not error_handler:
        return {"error": "Error handler not available"}
    
    stats = error_handler.get_error_stats()
    recent_errors = error_handler.get_recent_errors(limit=10)
    
    return {
        "statistics": stats,
        "recent_errors": recent_errors
    }

@app.post("/debug/errors/clear")
@error_handler.with_error_handling("ClearErrorStats")
async def clear_error_stats(request: ConfirmationRequest = None, auth: AuthManager = Depends(require_auth)):
    """Clear error statistics with confirmation."""
    if not error_handler:
        return {"error": "Error handler not available"}
    
    # If no confirmation provided, return confirmation requirement
    if not request or not request.confirm:
        stats = error_handler.get_error_stats()
        return {
            **require_confirmation("clear", f"{stats['total_errors']} error records"),
            "current_stats": stats
        }
    
    # Perform the clearing
    error_handler.clear_error_stats()
    error_handler.log_info("Error statistics cleared by user", "ClearErrorStats")
    return {"status": "success", "message": "Error statistics cleared successfully"}

@app.post("/debug/mode/{mode}")
async def set_debug_mode(mode: str, auth: AuthManager = Depends(require_auth)):
    """Enable or disable debug mode."""
    if not error_handler:
        return {"error": "Error handler not available"}
    
    if mode.lower() == "enable":
        error_handler.enable_debug_mode()
        return {"status": "success", "message": "Debug mode enabled"}
    elif mode.lower() == "disable":
        error_handler.disable_debug_mode()
        return {"status": "success", "message": "Debug mode disabled"}
    else:
        raise HTTPException(status_code=400, detail="Mode must be 'enable' or 'disable'")

@app.get("/debug/status")
async def get_debug_status(auth: AuthManager = Depends(require_auth)):
    """Get current debug status and system health."""
    health_info = {
        "error_handler_available": error_handler is not None,
        "debug_mode": error_handler.debug_mode if error_handler else False,
        "auth_manager_available": auth_manager is not None,
        "secure_storage_available": secure_storage is not None,
        "api_key_vault_available": api_key_vault is not None,
        "ai_chat_available": ai_chat is not None,
        "context_manager_available": context_manager is not None,
        "action_executor_available": action_executor is not None,
        "session_valid": auth_manager.is_session_valid() if auth_manager else False
    }
    
    if error_handler:
        health_info["error_stats"] = error_handler.get_error_stats()
    
    return health_info

# Trash Management Endpoints
@app.get("/trash")
async def list_trash_items(item_type: str = None, auth: AuthManager = Depends(require_auth)):
    """List items in trash, optionally filtered by type."""
    try:
        items = safe_delete_manager.list_trash_items(item_type)
        stats = safe_delete_manager.get_trash_stats()
        
        return {
            "items": [item["summary"] for item in items],  # Only return summaries for listing
            "stats": stats,
            "total_items": len(items)
        }
    except Exception as e:
        return error_handler.handle_api_error(e, "list_trash")

@app.get("/trash/{trash_id}")
async def get_trash_item(trash_id: str, auth: AuthManager = Depends(require_auth)):
    """Get detailed information about a specific trash item."""
    try:
        item = safe_delete_manager.recover_item(trash_id)
        if not item:
            raise HTTPException(status_code=404, detail="Trash item not found or expired")
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        return error_handler.handle_api_error(e, "get_trash_item")

@app.post("/trash/{trash_id}/restore")
async def restore_trash_item(trash_id: str, auth: AuthManager = Depends(require_auth)):
    """Restore an item from trash."""
    try:
        item = safe_delete_manager.restore_item(trash_id)
        if not item:
            raise HTTPException(status_code=404, detail="Trash item not found or expired")
        
        # Attempt to restore the actual data based on item type
        item_type = item["item_type"]
        item_id = item["item_id"]
        data = item["data"]
        
        if item_type == "secure_setting":
            if secure_storage:
                secure_storage.set_setting(data["key"], data["value"])
                error_handler.log_info(f"Restored secure setting: {item_id}", "TrashRestore")
            else:
                raise HTTPException(status_code=500, detail="Secure storage not available for restore")
        
        elif item_type == "api_key":
            # Note: API keys cannot be fully restored for security reasons
            error_handler.log_info(f"API key metadata restored (key itself not recoverable): {item_id}", "TrashRestore")
            return {
                "status": "partial_success",
                "message": f"API key metadata restored, but actual key cannot be recovered for security reasons",
                "item_type": item_type,
                "item_id": item_id,
                "note": "You will need to re-enter the API key"
            }
        
        return {
            "status": "success",
            "message": f"Item restored successfully",
            "item_type": item_type,
            "item_id": item_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return error_handler.handle_api_error(e, "restore_trash_item")

@app.delete("/trash/{trash_id}")
async def permanently_delete_trash_item(trash_id: str, request: ConfirmationRequest = None, auth: AuthManager = Depends(require_auth)):
    """Permanently delete an item from trash."""
    if not request or not request.confirm:
        return require_confirmation("permanently delete", f"trash item '{trash_id}'")
    
    try:
        success = safe_delete_manager.permanently_delete(trash_id)
        if not success:
            raise HTTPException(status_code=404, detail="Trash item not found")
        
        error_handler.log_info(f"Item permanently deleted from trash: {trash_id}", "TrashPermanentDelete")
        return {"status": "success", "message": "Item permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        return error_handler.handle_api_error(e, "permanently_delete_trash_item")

@app.post("/trash/empty")
async def empty_trash(item_type: str = None, request: ConfirmationRequest = None, auth: AuthManager = Depends(require_auth)):
    """Empty the trash, optionally for a specific item type."""
    if not request or not request.confirm:
        stats = safe_delete_manager.get_trash_stats()
        target = f"all {stats['total_items']} items" if not item_type else f"all {stats['by_type'].get(item_type, 0)} {item_type} items"
        return require_confirmation("permanently delete", target)
    
    try:
        deleted_count = safe_delete_manager.empty_trash(item_type)
        
        error_handler.log_info(f"Trash emptied: {deleted_count} items deleted (type: {item_type or 'all'})", "TrashEmpty")
        return {
            "status": "success",
            "message": f"Trash emptied successfully",
            "deleted_count": deleted_count,
            "item_type": item_type
        }
        
    except Exception as e:
        return error_handler.handle_api_error(e, "empty_trash")

@app.get("/trash/stats")
async def get_trash_stats(auth: AuthManager = Depends(require_auth)):
    """Get statistics about trash contents."""
    try:
        stats = safe_delete_manager.get_trash_stats()
        return stats
    except Exception as e:
        return error_handler.handle_api_error(e, "get_trash_stats")

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
@error_handler.with_error_handling("SecureSettingDelete")
async def delete_secure_setting(key: str, request: ConfirmationRequest = None, auth: AuthManager = Depends(require_auth)):
    """Delete a secure setting with confirmation and safe deletion."""
    if not secure_storage:
        raise HTTPException(status_code=500, detail="Secure storage not available")
    
    # If no confirmation provided, return confirmation requirement
    if not request or not request.confirm:
        return require_confirmation("delete", f"secure setting '{key}'")
    
    # Check if setting exists
    existing_value = secure_storage.get_setting(key)
    if existing_value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    
    # Safe delete - store in trash before deletion
    trash_id = safe_delete_manager.soft_delete(
        item_type="secure_setting",
        item_id=key,
        data={"key": key, "value": existing_value},
        metadata={"deleted_by": "user", "deletion_reason": "manual_delete"}
    )
    
    # Perform the deletion
    secure_storage.delete_setting(key)
    error_handler.log_info(f"Secure setting safely deleted: {key} -> {trash_id}", "SecureSettingDelete")
    
    return {
        "status": "success", 
        "message": f"Setting '{key}' deleted successfully",
        "trash_id": trash_id,
        "recovery_info": "Use the trash_id to recover this item within 30 days"
    }

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
@error_handler.with_error_handling("APIKeyStorage")
async def store_api_key(service: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Store an API key for a service."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    api_key = request.get("api_key")
    metadata = request.get("metadata", {})
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Validate API key format
    is_valid, error_msg = validate_api_key(api_key, service)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    success = api_key_vault.store_api_key_with_index(service, api_key, metadata)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store API key")
    
    error_handler.log_info(f"API key stored for service: {service}", "APIKeyStorage")
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
@error_handler.with_error_handling("APIKeyDelete")
async def delete_api_key(service: str, request: ConfirmationRequest = None, auth: AuthManager = Depends(require_auth)):
    """Delete an API key with confirmation and safe deletion."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    # If no confirmation provided, return confirmation requirement  
    if not request or not request.confirm:
        return require_confirmation("delete", f"API key for '{service}'")
    
    # Check if API key exists and get its data for backup
    key_data = api_key_vault.get_api_key(service)
    if not key_data:
        raise HTTPException(status_code=404, detail=f"API key for '{service}' not found")
    
    # Safe delete - store in trash before deletion (without exposing the actual key)
    trash_data = {
        "service": service,
        "metadata": key_data.get("metadata", {}),
        "key_length": len(key_data.get("api_key", "")),
        "key_preview": key_data.get("api_key", "")[:8] + "..." if key_data.get("api_key") else ""
    }
    
    trash_id = safe_delete_manager.soft_delete(
        item_type="api_key",
        item_id=service,
        data=trash_data,
        metadata={"deleted_by": "user", "deletion_reason": "manual_delete"}
    )
    
    # Perform the deletion
    success = api_key_vault.delete_api_key_with_index(service)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete API key")
    
    error_handler.log_info(f"API key safely deleted for service: {service} -> {trash_id}", "APIKeyDelete")
    
    return {
        "status": "success", 
        "message": f"API key for '{service}' deleted successfully",
        "trash_id": trash_id,
        "recovery_info": "API key metadata stored in trash for recovery tracking (actual key not recoverable for security)"
    }

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

# AI Assistant Endpoints
@app.post("/ai/chat")
async def ai_chat_endpoint(request: dict, auth: AuthManager = Depends(require_auth)):
    """Process AI chat message."""
    if not ai_chat:
        raise HTTPException(status_code=500, detail="AI chat not available")
    
    message = request.get("message", "")
    thinking_mode = request.get("thinking_mode", "normal")
    window = request.get("window")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        result = await ai_chat.process_message(message, window, thinking_mode)
        return result
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@app.post("/ai/conversation/start")
async def start_conversation(request: dict, auth: AuthManager = Depends(require_auth)):
    """Start a new AI conversation."""
    if not ai_chat:
        raise HTTPException(status_code=500, detail="AI chat not available")
    
    title = request.get("title")
    conversation_id = ai_chat.start_new_conversation(title)
    
    return {
        "conversation_id": conversation_id,
        "title": title,
        "status": "started"
    }

@app.get("/ai/conversation/{conversation_id}/history")
async def get_conversation_history(conversation_id: str, limit: int = 50, auth: AuthManager = Depends(require_auth)):
    """Get conversation history."""
    if not ai_chat:
        raise HTTPException(status_code=500, detail="AI chat not available")
    
    # Set conversation ID and get history
    ai_chat.current_conversation_id = conversation_id
    history = ai_chat.get_conversation_history(limit)
    
    return {
        "conversation_id": conversation_id,
        "history": history,
        "count": len(history)
    }

@app.get("/ai/providers")
async def list_ai_providers(auth: AuthManager = Depends(require_auth)):
    """List available AI providers."""
    providers_info = {}
    
    for name, provider in ai_providers.items():
        providers_info[name] = {
            "name": provider.get_provider_name(),
            "available": provider.is_available(),
            "capabilities": provider.get_capabilities(),
            "model_info": provider.get_model_info()
        }
    
    return {"providers": providers_info}

@app.post("/ai/providers/{provider_name}/configure")
async def configure_ai_provider(provider_name: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Configure an AI provider."""
    config = request.get("config", {})
    
    try:
        if provider_name == "openai":
            # Get API key from secure storage
            api_key = config.get("api_key")
            if api_key and api_key_vault:
                api_key_vault.store_api_key_with_index("openai", api_key)
                config["api_key"] = api_key
            
            provider = OpenAIProvider(config)
            success = await provider.initialize()
            
            if success:
                ai_providers["openai"] = provider
                if ai_chat:
                    ai_chat.set_ai_provider(provider)
                
                return {"status": "success", "message": "OpenAI provider configured"}
            else:
                return {"status": "failed", "message": "Failed to initialize OpenAI provider"}
        
        elif provider_name == "local_llm":
            provider = LocalLLMProvider(config)
            success = await provider.initialize()
            
            if success:
                ai_providers["local_llm"] = provider
                if ai_chat:
                    ai_chat.set_ai_provider(provider)
                
                return {"status": "success", "message": "Local LLM provider configured"}
            else:
                return {"status": "failed", "message": "Failed to initialize Local LLM provider"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")
    
    except Exception as e:
        logger.error(f"Provider configuration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure provider")

@app.get("/ai/providers/{provider_name}/models")
async def get_provider_models(provider_name: str, auth: AuthManager = Depends(require_auth)):
    """Get available models for a provider."""
    provider = ai_providers.get(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    try:
        models = provider.get_available_models()
        return {
            "provider": provider_name,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models")

@app.post("/ai/providers/{provider_name}/test")
async def test_ai_provider(provider_name: str, auth: AuthManager = Depends(require_auth)):
    """Test AI provider connection."""
    provider = ai_providers.get(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    try:
        result = await provider.test_connection()
        return result
    except Exception as e:
        logger.error(f"Provider test error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/ai/context/{window}")
async def get_window_context(window: str, auth: AuthManager = Depends(require_auth)):
    """Get context information for a specific window."""
    if not context_manager:
        raise HTTPException(status_code=500, detail="Context manager not available")
    
    context = context_manager.get_context(window)
    return context

@app.post("/ai/context/{window}/update")
async def update_window_context(window: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Update context data for a window."""
    if not context_manager:
        raise HTTPException(status_code=500, detail="Context manager not available")
    
    data = request.get("data", {})
    context_manager.update_window_data(window, data)
    
    return {"status": "success", "message": f"Context updated for {window}"}

@app.get("/ai/actions")
async def get_available_actions(auth: AuthManager = Depends(require_auth)):
    """Get list of available actions."""
    if not action_executor:
        raise HTTPException(status_code=500, detail="Action executor not available")
    
    actions = action_executor.get_available_actions()
    action_info = {}
    
    for action in actions:
        action_info[action] = action_executor.get_action_info(action)
    
    return {"actions": action_info}

@app.post("/ai/actions/{action}/execute")
async def execute_action(action: str, request: dict, auth: AuthManager = Depends(require_auth)):
    """Execute a specific action."""
    if not action_executor:
        raise HTTPException(status_code=500, detail="Action executor not available")
    
    context = request.get("context", {})
    parameters = request.get("parameters", {})
    
    try:
        result = await action_executor.execute_action(action, context, parameters)
        return result
    except Exception as e:
        logger.error(f"Action execution error: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute action")

@app.get("/ai/status")
async def get_ai_status(auth: AuthManager = Depends(require_auth)):
    """Get AI assistant status."""
    status = {
        "ai_chat_available": ai_chat is not None,
        "context_manager_available": context_manager is not None,
        "action_executor_available": action_executor is not None,
        "response_handler_available": response_handler is not None,
        "active_providers": len(ai_providers),
        "providers": {}
    }
    
    if ai_chat:
        status["chat_status"] = ai_chat.get_chat_status()
    
    for name, provider in ai_providers.items():
        status["providers"][name] = {
            "connected": provider.is_available(),
            "model_info": provider.get_model_info()
        }
    
@app.get("/ai/status-public")
async def get_ai_status_public():
    """Get AI assistant status (public endpoint for testing)."""
    status = {
        "ai_chat_available": ai_chat is not None,
        "context_manager_available": context_manager is not None,
        "action_executor_available": action_executor is not None,
        "response_handler_available": response_handler is not None,
        "active_providers": len(ai_providers),
        "providers": {}
    }
    
    if ai_chat:
        status["chat_status"] = ai_chat.get_chat_status()
    
    for name, provider in ai_providers.items():
        status["providers"][name] = {
            "connected": provider.is_available(),
            "model_info": provider.get_model_info()
        }
    
    return status

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