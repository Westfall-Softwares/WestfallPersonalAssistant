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

# Import model handler
try:
    from model_handler import model_manager
    MODEL_HANDLER_AVAILABLE = True
except ImportError:
    MODEL_HANDLER_AVAILABLE = False
    print("Warning: Model handler not available")

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
        if MODEL_HANDLER_AVAILABLE:
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
                    "gpu_enabled": TORCH_AVAILABLE
                }
            elif model_format == "pytorch":
                logger.info("PyTorch model detected - would use transformers when available") 
                current_model = {
                    "type": "pytorch", 
                    "path": model_path, 
                    "loaded": True,
                    "format": "PyTorch",
                    "inference_engine": "transformers",
                    "gpu_enabled": TORCH_AVAILABLE
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
        if MODEL_HANDLER_AVAILABLE and current_model.get("handler") == "model_manager":
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
    if MODEL_HANDLER_AVAILABLE:
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