"""
LLM inference endpoints for chat and text generation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: List[ChatMessage] = Field(default=[], description="Previous conversation history")
    thinking_mode: str = Field(default="normal", description="Thinking mode: normal, deep, creative")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")
    stream: bool = Field(default=False, description="Whether to stream the response")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    conversation_id: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time: float
    thinking_mode: str
    model_info: Dict[str, Any]

class ModelInfo(BaseModel):
    name: str
    size: Optional[str] = None
    type: str
    loaded: bool
    context_length: int
    parameters: Dict[str, Any]

class ModelLoadRequest(BaseModel):
    model_path: str = Field(..., description="Path to the model file")
    gpu_layers: Optional[int] = Field(default=None, description="Number of GPU layers")
    context_length: Optional[int] = Field(default=4096, description="Context window size")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """
    Generate a chat response using the loaded LLM.
    """
    start_time = asyncio.get_event_loop().time()
    
    # Get LLM supervisor
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor or not supervisor.is_model_loaded():
        raise HTTPException(status_code=503, detail="No model loaded")
    
    try:
        # Generate response
        response_text, tokens_used = await supervisor.generate_response(
            prompt=request.message,
            conversation_history=request.conversation_history,
            thinking_mode=request.thinking_mode,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return ChatResponse(
            response=response_text,
            tokens_used=tokens_used,
            processing_time=processing_time,
            thinking_mode=request.thinking_mode,
            model_info=supervisor.get_model_info()
        )
        
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, http_request: Request):
    """
    Stream a chat response using the loaded LLM.
    """
    # Get LLM supervisor
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor or not supervisor.is_model_loaded():
        raise HTTPException(status_code=503, detail="No model loaded")
    
    async def generate():
        try:
            async for chunk in supervisor.stream_response(
                prompt=request.message,
                conversation_history=request.conversation_history,
                thinking_mode=request.thinking_mode,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                yield f"data: {chunk}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")

@router.get("/models", response_model=List[ModelInfo])
async def list_models(http_request: Request):
    """
    List available models.
    """
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        return []
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor:
        return []
    
    return supervisor.list_models()

@router.get("/models/current", response_model=ModelInfo)
async def get_current_model(http_request: Request):
    """
    Get information about the currently loaded model.
    """
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor or not supervisor.is_model_loaded():
        raise HTTPException(status_code=404, detail="No model loaded")
    
    return supervisor.get_current_model_info()

@router.post("/models/load")
async def load_model(request: ModelLoadRequest, background_tasks: BackgroundTasks, http_request: Request):
    """
    Load a model for inference.
    """
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor:
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    # Add model loading as background task
    background_tasks.add_task(
        supervisor.load_model,
        request.model_path,
        request.gpu_layers,
        request.context_length
    )
    
    return {
        "message": "Model loading started",
        "model_path": request.model_path,
        "status": "loading"
    }

@router.post("/models/unload")
async def unload_model(http_request: Request):
    """
    Unload the current model.
    """
    if not hasattr(http_request.app.state, 'llama_supervisor'):
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    supervisor = http_request.app.state.llama_supervisor
    if not supervisor:
        raise HTTPException(status_code=503, detail="LLM supervisor not available")
    
    success = await supervisor.unload_model()
    
    if success:
        return {"message": "Model unloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to unload model")