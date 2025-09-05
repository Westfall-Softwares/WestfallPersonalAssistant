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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import screen capture module
try:
    from screen_capture import screen_engine
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False
    print("Warning: Screen capture module not available")

# Model inference imports (these would need to be installed)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. GPU acceleration disabled.")

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

# Global model state
current_model = None
model_path = None
gpu_info = None

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

def detect_gpu():
    """Detect available GPU resources"""
    global gpu_info
    
    if not TORCH_AVAILABLE:
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
        # Determine model format
        model_format = detect_model_format(model_path)
        logger.info(f"Loading model: {model_path} (format: {model_format})")
        
        # This is a placeholder - actual implementation would depend on the model format
        # For GGUF/GGML models, you'd use llama-cpp-python
        # For PyTorch models, you'd use transformers or direct PyTorch loading
        
        if model_format == "gguf":
            # Placeholder for llama.cpp integration
            logger.info("GGUF model loading would be implemented here")
            current_model = {"type": "gguf", "path": model_path, "loaded": True}
        elif model_format == "pytorch":
            # Placeholder for PyTorch model loading
            logger.info("PyTorch model loading would be implemented here")
            current_model = {"type": "pytorch", "path": model_path, "loaded": True}
        else:
            logger.error(f"Unsupported model format: {model_format}")
            return False
        
        logger.info("Model loaded successfully")
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
    
    # This is a placeholder - actual implementation would call the loaded model
    responses = {
        "normal": f"I understand your message: '{message}'. This is a normal response from the AI assistant.",
        "thinking": f"""🤔 **Thinking Process:**

1. **Message Analysis**: You asked about '{message}'
2. **Context Consideration**: Analyzing the request in context
3. **Response Formulation**: Crafting an appropriate response

**Final Response**: Based on my analysis, here's my response to your message.""",
        "research": f"""📚 **Research-Grade Analysis**

**Input Analysis**: "{message}"

**Multi-Perspective Examination**:
1. **Primary Interpretation**: Direct analysis of the query
2. **Alternative Angles**: Consider different approaches to the question
3. **Contextual Factors**: Relevant background information

**Detailed Investigation**:
- Key concepts and their relationships
- Potential implications and considerations
- Supporting evidence and reasoning

**Comprehensive Response**: After thorough analysis, my detailed response addresses all aspects of your query.

*Note: This analysis is based on the loaded model's knowledge and should be verified with authoritative sources when appropriate.*"""
    }
    
    return responses.get(thinking_mode, responses["normal"])

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
    if not current_model:
        return {"loaded": False}
    
    model_file = Path(current_model["path"])
    return {
        "loaded": True,
        "name": model_file.name,
        "path": current_model["path"],
        "type": current_model["type"],
        "size_gb": round(model_file.stat().st_size / (1024**3), 2)
    }

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
        if SCREEN_CAPTURE_AVAILABLE:
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
    if not SCREEN_CAPTURE_AVAILABLE:
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
    if not SCREEN_CAPTURE_AVAILABLE:
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
    if not SCREEN_CAPTURE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Screen capture not available")
    
    try:
        screen_engine.stop_monitoring()
        return {"status": "monitoring_stopped"}
    except Exception as e:
        logger.error(f"Monitoring stop error: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

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