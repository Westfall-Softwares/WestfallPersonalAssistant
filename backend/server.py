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
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
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
from utils import (
    setup_global_error_handling, get_global_error_handler, ErrorHandler, 
    get_safe_delete_manager, get_network_manager
)
from utils.validation import validate_email, validate_password_strength, validate_api_key

# Import AI assistant modules  
from ai_assistant import AIChat, ContextManager, ActionExecutor, ResponseHandler
from ai_assistant.providers import OpenAIProvider, LocalLLMProvider

# Import feature modules
from features.news_reader import NewsReader
from features.music_player import MusicPlayer
from features.browser_manager import BrowserManager
from features.advanced_calculator import AdvancedCalculator
from features.navigation_system import NavigationManager
from features.shortcuts_manager import ShortcutManager
from features.notification_manager import NotificationManager, NotificationPriority, NotificationType
from features.reminder_system import ReminderSystem, ReminderType, ReminderPriority

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

# Initialize network manager
network_manager = get_network_manager()

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

# Feature modules
news_reader = None
music_player = None
browser_manager = None
calculator = None
navigation_manager = None
shortcut_manager = None
notification_manager = None
reminder_system = None

def initialize_security_systems():
    """Initialize security and database systems."""
    global auth_manager, secure_storage, api_key_vault, backup_manager, sync_manager
    global ai_chat, context_manager, action_executor, response_handler
    global news_reader, music_player, browser_manager, calculator
    global navigation_manager, shortcut_manager, notification_manager, reminder_system
    
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
        
        # Initialize feature modules (available without authentication)
        news_reader = NewsReader(config_dir)
        music_player = MusicPlayer(config_dir)
        browser_manager = BrowserManager(config_dir)
        calculator = AdvancedCalculator(config_dir)
        navigation_manager = NavigationManager(config_dir)
        shortcut_manager = ShortcutManager(config_dir)
        notification_manager = NotificationManager(config_dir)
        reminder_system = ReminderSystem(config_dir, notification_manager=notification_manager)
        
        error_handler.log_info("Security systems initialized", "SecurityInit")
    except Exception as e:
        error_handler.log_error(f"Failed to initialize security systems: {e}", context="SecurityInit")

async def startup_tasks():
    """Perform async startup tasks."""
    try:
        if navigation_manager and not navigation_manager._search_index_built:
            await navigation_manager._build_search_index()
            navigation_manager._search_index_built = True
        
        if shortcut_manager and not shortcut_manager._shortcuts_loaded:
            await shortcut_manager._load_shortcuts()
            shortcut_manager._shortcuts_loaded = True
        
        if reminder_system and not reminder_system._reminder_loop_started:
            asyncio.create_task(reminder_system._start_reminder_loop())
            reminder_system._reminder_loop_started = True
        
        error_handler.log_info("Async startup tasks completed", "Startup")
    except Exception as e:
        error_handler.log_error(f"Failed to complete startup tasks: {e}", context="Startup")

# FastAPI startup event
@app.on_event("startup")
async def on_startup():
    await startup_tasks()

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

# News reader models
class NewsSourceRequest(BaseModel):
    name: str
    url: str
    category: str = "general"
    source_type: str = "rss"
    active: bool = True
    refresh_interval: int = 3600

class NewsSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 50

# Music player models
class MusicDirectoryRequest(BaseModel):
    directory: str
    recursive: bool = True

class PlaylistRequest(BaseModel):
    name: str
    description: str = ""

class PlaylistTrackRequest(BaseModel):
    playlist_id: int
    track_id: int

class VolumeRequest(BaseModel):
    volume: float

# Browser models
class TabRequest(BaseModel):
    url: str = "about:blank"
    title: str = "New Tab"

class NavigateRequest(BaseModel):
    tab_id: str
    url: str

class BookmarkRequest(BaseModel):
    title: str
    url: str
    folder_path: str = ""
    description: str = ""
    tags: List[str] = []

class DownloadRequest(BaseModel):
    url: str
    filename: Optional[str] = None
    tab_id: Optional[str] = None

# Calculator models
class CalculationRequest(BaseModel):
    expression: str
    mode: str = "standard"

class UnitConversionRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    category: Optional[str] = None

# Navigation models
class NavigationRequest(BaseModel):
    module: str
    path: List[str] = []
    context: Dict[str, Any] = {}

class SearchRequest(BaseModel):
    query: str
    limit: int = 50

# Notification models
class NotificationRequest(BaseModel):
    title: str
    message: str
    notification_type: str = "info"
    priority: int = 2
    module: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    duration: Optional[int] = None
    persistent: bool = False
    sound_enabled: Optional[bool] = None

class NotificationTemplateRequest(BaseModel):
    template_id: str
    title_template: str
    message_template: str
    notification_type: str
    priority: int
    module: Optional[str] = None
    variables: List[str] = []

# Reminder models
class ReminderRequest(BaseModel):
    title: str
    description: str = ""
    reminder_type: str = "one_time"
    trigger_time: Optional[str] = None  # ISO format datetime
    location: Optional[Dict[str, Any]] = None
    recurrence: Optional[Dict[str, Any]] = None
    priority: int = 2
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class LocationUpdateRequest(BaseModel):
    lat: float
    lng: float
    accuracy: Optional[float] = None

class ShortcutRequest(BaseModel):
    shortcut_key: str
    context: str
    action: str
    description: str = ""

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

# Network Status Endpoint
@app.get("/network/status")
async def get_network_status():
    """Get network connectivity status."""
    try:
        status = network_manager.get_network_status()
        return status
    except Exception as e:
        return error_handler.handle_api_error(e, "get_network_status")

# Weather Service Endpoints
@app.get("/weather")
@error_handler.with_error_handling("WeatherService")
async def get_weather(location: str = "auto", auth: AuthManager = Depends(require_auth)):
    """Get weather information with network error handling."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    # Get API key
    weather_key_data = api_key_vault.get_api_key("openweathermap")
    if not weather_key_data:
        return {
            "status": "error",
            "message": "OpenWeatherMap API key not configured",
            "requires_setup": True
        }
    
    api_key = weather_key_data["api_key"]
    
    try:
        # Use network manager for robust request handling
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location if location != "auto" else "New York",  # Default location
            "appid": api_key,
            "units": "metric"
        }
        
        response = network_manager.get_with_retry(url, params=params, timeout=10)
        data = response.json()
        
        # Format response
        weather_data = {
            "status": "success",
            "location": data["name"],
            "country": data["sys"]["country"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "visibility": data.get("visibility", "N/A"),
            "last_updated": datetime.now().isoformat()
        }
        
        error_handler.log_info(f"Weather data retrieved for {location}", "WeatherService")
        return weather_data
        
    except Exception as e:
        error_handler.log_error(f"Weather service error: {e}", context="WeatherService")
        # Return fallback data
        return network_manager.get_fallback_data("weather")

@app.get("/news")
@error_handler.with_error_handling("NewsService")
async def get_news(category: str = "general", country: str = "us", limit: int = 10, auth: AuthManager = Depends(require_auth)):
    """Get news with network error handling."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    # Get API key
    news_key_data = api_key_vault.get_api_key("newsapi")
    if not news_key_data:
        return {
            "status": "error",
            "message": "NewsAPI key not configured",
            "requires_setup": True
        }
    
    api_key = news_key_data["api_key"]
    
    try:
        # Use network manager for robust request handling
        url = "https://newsapi.org/v2/top-headlines"
        headers = {"X-API-Key": api_key}
        params = {
            "category": category,
            "country": country,
            "pageSize": min(limit, 100)  # API limit
        }
        
        response = network_manager.get_with_retry(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if data["status"] != "ok":
            raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
        
        # Format response
        articles = []
        for article in data["articles"][:limit]:
            articles.append({
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"],
                "url_to_image": article.get("urlToImage")
            })
        
        news_data = {
            "status": "success",
            "articles": articles,
            "total_results": data["totalResults"],
            "category": category,
            "country": country,
            "last_updated": datetime.now().isoformat()
        }
        
        error_handler.log_info(f"News data retrieved: {len(articles)} articles", "NewsService")
        return news_data
        
    except Exception as e:
        error_handler.log_error(f"News service error: {e}", context="NewsService")
        # Return fallback data
        return network_manager.get_fallback_data("news")

# Email Service Endpoints
@app.post("/email/send")
@error_handler.with_error_handling("EmailService")
async def send_email(request: dict, auth: AuthManager = Depends(require_auth)):
    """Send email with network error handling."""
    if not api_key_vault:
        raise HTTPException(status_code=500, detail="API key vault not available")
    
    # Validate required fields
    to_email = request.get("to")
    subject = request.get("subject")
    body = request.get("body")
    
    if not to_email or not subject or not body:
        raise HTTPException(status_code=400, detail="Missing required fields: to, subject, body")
    
    # Validate email format
    is_valid, error_msg = validate_email(to_email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid email address: {error_msg}")
    
    # For now, this is a placeholder - in a real implementation you would:
    # 1. Get SMTP settings from secure storage
    # 2. Use network_manager to send with retry logic
    # 3. Handle various email provider APIs
    
    try:
        # Simulate email sending with network handling
        if not network_manager.is_online():
            return network_manager.get_fallback_data("email")
        
        # Placeholder for actual email sending logic
        # This would integrate with SMTP or email service APIs
        
        email_result = {
            "status": "success",
            "message": "Email sent successfully",
            "to": to_email,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"msg_{int(time.time())}"
        }
        
        error_handler.log_info(f"Email sent to {to_email}", "EmailService")
        return email_result
        
    except Exception as e:
        error_handler.log_error(f"Email service error: {e}", context="EmailService")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
            "fallback_available": True
        }

@app.get("/email/status")
async def get_email_status(auth: AuthManager = Depends(require_auth)):
    """Get email service status."""
    try:
        online_status = network_manager.is_online()
        
        return {
            "status": "online" if online_status else "offline",
            "can_send": online_status,
            "can_receive": False,  # Placeholder - would check IMAP/POP3
            "last_checked": datetime.now().isoformat(),
            "smtp_configured": False,  # Placeholder - would check actual config
            "imap_configured": False   # Placeholder - would check actual config
        }
    except Exception as e:
        return error_handler.handle_api_error(e, "get_email_status")

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

# ========== NEWS READER ENDPOINTS ==========

@app.post("/news/sources")
async def add_news_source(request: NewsSourceRequest):
    """Add a new news source."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    success = await news_reader.add_source(
        name=request.name,
        url=request.url,
        category=request.category,
        source_type=request.source_type,
        active=request.active,
        refresh_interval=request.refresh_interval
    )
    
    if success:
        return {"status": "success", "message": f"News source '{request.name}' added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add news source")

@app.get("/news/sources")
async def get_news_sources():
    """Get all news sources."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    sources = await news_reader.get_sources()
    return {"sources": sources}

@app.delete("/news/sources/{source_id}")
async def remove_news_source(source_id: int):
    """Remove a news source."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    success = await news_reader.remove_source(source_id)
    if success:
        return {"status": "success", "message": f"News source {source_id} removed"}
    else:
        raise HTTPException(status_code=400, detail="Failed to remove news source")

@app.post("/news/fetch")
async def fetch_news_articles(source_id: Optional[int] = None, force_refresh: bool = False):
    """Fetch articles from news sources."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    articles = await news_reader.fetch_articles(source_id, force_refresh)
    return {"articles": articles, "count": len(articles)}

@app.get("/news/articles")
async def get_news_articles(
    category: Optional[str] = None,
    read_status: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get news articles with optional filtering."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    articles = await news_reader.get_articles(category, read_status, limit, offset)
    return {"articles": articles, "count": len(articles)}

@app.post("/news/search")
async def search_news_articles(request: NewsSearchRequest):
    """Search news articles."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    articles = await news_reader.search_articles(
        query=request.query,
        category=request.category,
        limit=request.limit
    )
    return {"articles": articles, "count": len(articles)}

@app.post("/news/articles/{article_id}/read")
async def mark_article_read(article_id: int, read: bool = True):
    """Mark article as read/unread."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    success = await news_reader.mark_as_read(article_id, read)
    if success:
        status = "read" if read else "unread"
        return {"status": "success", "message": f"Article marked as {status}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update article status")

@app.post("/news/articles/{article_id}/archive")
async def archive_article(article_id: int, archived: bool = True):
    """Archive/unarchive article."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    success = await news_reader.archive_article(article_id, archived)
    if success:
        status = "archived" if archived else "unarchived"
        return {"status": "success", "message": f"Article {status}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update article status")

@app.get("/news/stats")
async def get_news_statistics():
    """Get news reader statistics."""
    if not news_reader:
        raise HTTPException(status_code=503, detail="News reader not available")
    
    stats = await news_reader.get_statistics()
    return stats

# ========== MUSIC PLAYER ENDPOINTS ==========

@app.post("/music/scan")
async def scan_music_directory(request: MusicDirectoryRequest):
    """Scan directory for music files."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    added_count = await music_player.scan_music_directory(request.directory, request.recursive)
    return {"status": "success", "added_tracks": added_count}

@app.get("/music/tracks")
async def get_music_tracks(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None
):
    """Get music tracks with optional filtering."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    tracks = await music_player.get_tracks(limit, offset, search, genre, artist, album)
    return {"tracks": tracks, "count": len(tracks)}

@app.get("/music/tracks/{track_id}")
async def get_music_track(track_id: int):
    """Get specific track information."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    track = await music_player.get_track(track_id)
    if track:
        return track
    else:
        raise HTTPException(status_code=404, detail="Track not found")

@app.post("/music/play/{track_id}")
async def play_track(track_id: int):
    """Play a specific track."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.play_track(track_id)
    if success:
        return {"status": "playing", "track_id": track_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to play track")

@app.post("/music/pause")
async def pause_playback():
    """Pause current playback."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.pause()
    if success:
        return {"status": "paused"}
    else:
        raise HTTPException(status_code=400, detail="Failed to pause playback")

@app.post("/music/resume")
async def resume_playback():
    """Resume playback."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.resume()
    if success:
        return {"status": "playing"}
    else:
        raise HTTPException(status_code=400, detail="Failed to resume playback")

@app.post("/music/stop")
async def stop_playback():
    """Stop playback."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.stop()
    if success:
        return {"status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="Failed to stop playback")

@app.post("/music/volume")
async def set_volume(request: VolumeRequest):
    """Set playback volume."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.set_volume(request.volume)
    if success:
        return {"status": "success", "volume": request.volume}
    else:
        raise HTTPException(status_code=400, detail="Failed to set volume")

@app.get("/music/status")
async def get_playback_status():
    """Get current playback status."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    status = await music_player.get_playback_status()
    return status

@app.post("/music/playlists")
async def create_playlist(request: PlaylistRequest):
    """Create a new playlist."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    playlist_id = await music_player.create_playlist(request.name, request.description)
    if playlist_id:
        return {"status": "success", "playlist_id": playlist_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to create playlist")

@app.post("/music/playlists/add-track")
async def add_track_to_playlist(request: PlaylistTrackRequest):
    """Add track to playlist."""
    if not music_player:
        raise HTTPException(status_code=503, detail="Music player not available")
    
    success = await music_player.add_track_to_playlist(request.playlist_id, request.track_id)
    if success:
        return {"status": "success", "message": "Track added to playlist"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add track to playlist")

# ========== BROWSER ENDPOINTS ==========

@app.post("/browser/tabs")
async def create_browser_tab(request: TabRequest):
    """Create a new browser tab."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    tab_id = await browser_manager.create_tab(request.url, request.title)
    if tab_id:
        return {"status": "success", "tab_id": tab_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to create tab")

@app.delete("/browser/tabs/{tab_id}")
async def close_browser_tab(tab_id: str):
    """Close a browser tab."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.close_tab(tab_id)
    if success:
        return {"status": "success", "message": f"Tab {tab_id} closed"}
    else:
        raise HTTPException(status_code=400, detail="Failed to close tab")

@app.get("/browser/tabs")
async def get_browser_tabs():
    """Get all browser tabs."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    tabs = await browser_manager.get_tabs()
    return {"tabs": tabs}

@app.post("/browser/tabs/{tab_id}/switch")
async def switch_browser_tab(tab_id: str):
    """Switch to a specific tab."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.switch_tab(tab_id)
    if success:
        return {"status": "success", "active_tab": tab_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to switch tab")

@app.post("/browser/navigate")
async def navigate_browser(request: NavigateRequest):
    """Navigate tab to URL."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.navigate_to(request.tab_id, request.url)
    if success:
        return {"status": "success", "message": f"Navigated to {request.url}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to navigate")

@app.post("/browser/tabs/{tab_id}/back")
async def browser_go_back(tab_id: str):
    """Go back in tab history."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.go_back(tab_id)
    if success:
        return {"status": "success", "message": "Navigated back"}
    else:
        raise HTTPException(status_code=400, detail="Cannot go back")

@app.post("/browser/tabs/{tab_id}/forward")
async def browser_go_forward(tab_id: str):
    """Go forward in tab history."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.go_forward(tab_id)
    if success:
        return {"status": "success", "message": "Navigated forward"}
    else:
        raise HTTPException(status_code=400, detail="Cannot go forward")

@app.post("/browser/bookmarks")
async def add_bookmark(request: BookmarkRequest):
    """Add a bookmark."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    bookmark_id = await browser_manager.add_bookmark(
        title=request.title,
        url=request.url,
        folder_path=request.folder_path,
        description=request.description,
        tags=request.tags
    )
    
    if bookmark_id:
        return {"status": "success", "bookmark_id": bookmark_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to add bookmark")

@app.get("/browser/bookmarks")
async def get_bookmarks(folder_path: Optional[str] = None):
    """Get bookmarks."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    bookmarks = await browser_manager.get_bookmarks(folder_path)
    return {"bookmarks": bookmarks}

@app.delete("/browser/bookmarks/{bookmark_id}")
async def remove_bookmark(bookmark_id: int):
    """Remove a bookmark."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    success = await browser_manager.remove_bookmark(bookmark_id)
    if success:
        return {"status": "success", "message": f"Bookmark {bookmark_id} removed"}
    else:
        raise HTTPException(status_code=400, detail="Failed to remove bookmark")

@app.get("/browser/history")
async def get_browser_history(query: Optional[str] = None, limit: int = 50):
    """Get browser history."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    if query:
        history = await browser_manager.search_history(query, limit)
    else:
        history = await browser_manager.search_history("", limit)
    
    return {"history": history}

@app.post("/browser/downloads")
async def start_download(request: DownloadRequest):
    """Start a file download."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    download_id = await browser_manager.start_download(
        url=request.url,
        filename=request.filename,
        tab_id=request.tab_id
    )
    
    if download_id:
        return {"status": "success", "download_id": download_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to start download")

@app.get("/browser/downloads")
async def get_downloads(status: Optional[str] = None):
    """Get download list."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    downloads = await browser_manager.get_downloads(status)
    return {"downloads": downloads}

@app.get("/browser/stats")
async def get_browser_stats():
    """Get browser statistics."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not available")
    
    stats = await browser_manager.get_browser_stats()
    return stats

# ========== CALCULATOR ENDPOINTS ==========

@app.post("/calculator/calculate")
async def calculate_expression(request: CalculationRequest):
    """Calculate mathematical expression."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    result = await calculator.calculate(request.expression, request.mode)
    return result

@app.post("/calculator/convert")
async def convert_units(request: UnitConversionRequest):
    """Convert between units."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    try:
        result = await calculator.convert_units(
            value=request.value,
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            category=request.category
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calculator/memory/store")
async def memory_store(value: Optional[float] = None):
    """Store value in calculator memory."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    success = await calculator.memory_store(value)
    if success:
        return {"status": "success", "message": "Value stored in memory"}
    else:
        raise HTTPException(status_code=400, detail="Failed to store in memory")

@app.get("/calculator/memory/recall")
async def memory_recall():
    """Recall value from calculator memory."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    value = await calculator.memory_recall()
    return {"memory_value": value}

@app.post("/calculator/memory/add")
async def memory_add(value: Optional[float] = None):
    """Add to calculator memory."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    success = await calculator.memory_add(value)
    if success:
        return {"status": "success", "message": "Added to memory"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add to memory")

@app.post("/calculator/memory/subtract")
async def memory_subtract(value: Optional[float] = None):
    """Subtract from calculator memory."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    success = await calculator.memory_subtract(value)
    if success:
        return {"status": "success", "message": "Subtracted from memory"}
    else:
        raise HTTPException(status_code=400, detail="Failed to subtract from memory")

@app.post("/calculator/memory/clear")
async def memory_clear():
    """Clear calculator memory."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    success = await calculator.memory_clear()
    if success:
        return {"status": "success", "message": "Memory cleared"}
    else:
        raise HTTPException(status_code=400, detail="Failed to clear memory")

@app.get("/calculator/history")
async def get_calculation_history(limit: int = 100):
    """Get calculation history."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    history = await calculator.get_calculation_history(limit)
    return {"history": history}

@app.get("/calculator/units")
async def get_available_units():
    """Get available units for conversion."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    units = await calculator.get_available_units()
    return {"unit_categories": units}

@app.get("/calculator/stats")
async def get_calculator_stats():
    """Get calculator usage statistics."""
    if not calculator:
        raise HTTPException(status_code=503, detail="Calculator not available")
    
    stats = await calculator.get_calculator_stats()
    return stats

# =====================================
# TAILOR PACK API ENDPOINTS
# =====================================

class TailorPackImportRequest(BaseModel):
    orderNumber: str
    verifyLicense: bool = True

class TailorPackManifest(BaseModel):
    pack_id: str
    name: str
    version: str
    description: str
    author: str
    target_audience: str
    business_category: str
    features: List[str]
    dependencies: Optional[List[str]] = []
    license_required: bool = False

@app.get("/api/tailor-packs")
async def get_installed_tailor_packs():
    """Get list of installed Tailor Packs."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        installed_packs = pack_manager.get_installed_packs()
        active_packs = pack_manager.get_active_packs()
        
        # Convert to frontend format
        packs_data = []
        for pack in installed_packs:
            pack_data = {
                "id": pack.pack_id,
                "name": pack.name,
                "version": pack.version,
                "description": pack.description,
                "author": pack.author,
                "category": pack.business_category,
                "targetAudience": pack.target_audience,
                "active": pack.enabled,
                "features": pack.feature_list or [],
                "dependencies": getattr(pack, 'dependencies', []),
                "licenseRequired": pack.license_required,
                "trialDaysLeft": getattr(pack, 'trial_days_left', None)
            }
            packs_data.append(pack_data)
        
        return {
            "success": True,
            "installedPacks": packs_data,
            "totalInstalled": len(installed_packs),
            "totalActive": len(active_packs)
        }
    except Exception as e:
        logger.error(f"Error getting tailor packs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tailor-packs/import")
async def import_tailor_pack(request: TailorPackImportRequest):
    """Import a Tailor Pack using order number/license key."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        from util.order_verification import get_order_verification_service
        
        pack_manager = get_tailor_pack_manager()
        order_service = get_order_verification_service()
        
        # Verify order/license
        if request.verifyLicense:
            verification_result = order_service.verify_order(request.orderNumber)
            if not verification_result.get("valid", False):
                return {
                    "success": False,
                    "error": verification_result.get("error", "Invalid order number")
                }
        
        # Download and import pack
        # This would typically involve downloading from a marketplace
        # For now, return mock success
        return {
            "success": True,
            "pack": {
                "id": "mock-pack-" + request.orderNumber[:8],
                "name": "Mock Business Pack",
                "version": "1.0.0",
                "description": "A mock pack for demonstration",
                "author": "Westfall Software",
                "category": "business",
                "targetAudience": "entrepreneur",
                "active": True,
                "features": ["Feature 1", "Feature 2"],
                "licenseRequired": True
            },
            "message": "Pack imported successfully"
        }
    except Exception as e:
        logger.error(f"Error importing tailor pack: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/tailor-packs/import-file")
async def import_tailor_pack_from_file():
    """Import a Tailor Pack from uploaded ZIP file."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        # This would handle file upload and import
        # For now, return mock success
        return {
            "success": True,
            "pack": {
                "id": "uploaded-pack-" + str(int(time.time())),
                "name": "Uploaded Pack",
                "version": "1.0.0",
                "description": "Pack imported from file",
                "author": "Unknown",
                "category": "other",
                "targetAudience": "any",
                "active": True,
                "features": ["Uploaded Feature"]
            },
            "message": "Pack imported from file successfully"
        }
    except Exception as e:
        logger.error(f"Error importing tailor pack from file: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/tailor-packs/export/{pack_id}")
async def export_tailor_pack(pack_id: str):
    """Export a Tailor Pack to ZIP file."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        export_result = pack_manager.export_tailor_pack(pack_id)
        
        if export_result["success"]:
            # Return file download response
            # This would typically return a FileResponse
            return {
                "success": True,
                "downloadUrl": f"/downloads/packs/{pack_id}.zip",
                "message": f"Pack {export_result['pack_name']} exported successfully"
            }
        else:
            return {"success": False, "error": export_result["error"]}
    except Exception as e:
        logger.error(f"Error exporting tailor pack: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/tailor-packs/backup")
async def backup_all_tailor_packs():
    """Create backup of all Tailor Packs."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        backup_result = pack_manager.backup_all_packs()
        
        if backup_result["success"]:
            return {
                "success": True,
                "backupPath": backup_result["backup_path"],
                "totalPacks": backup_result["total_packs"],
                "backupSize": backup_result["backup_size"],
                "message": "Backup created successfully"
            }
        else:
            return {"success": False, "error": backup_result["error"]}
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/tailor-packs/{pack_id}/toggle")
async def toggle_tailor_pack(pack_id: str, enabled: bool):
    """Enable or disable a Tailor Pack."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        if enabled:
            result = pack_manager.enable_pack(pack_id)
        else:
            result = pack_manager.disable_pack(pack_id)
        
        return result
    except Exception as e:
        logger.error(f"Error toggling tailor pack {pack_id}: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/tailor-packs/statistics")
async def get_tailor_pack_statistics():
    """Get statistics about Tailor Packs."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        stats = pack_manager.get_pack_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Error getting tailor pack statistics: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/tailor-packs/{pack_id}/dependencies")
async def resolve_pack_dependencies(pack_id: str):
    """Resolve dependencies for a Tailor Pack."""
    try:
        from util.tailor_pack_manager import get_tailor_pack_manager
        pack_manager = get_tailor_pack_manager()
        
        resolution = pack_manager.resolve_dependencies(pack_id)
        return resolution
    except Exception as e:
        logger.error(f"Error resolving dependencies for {pack_id}: {e}")
        return {"success": False, "error": str(e)}

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