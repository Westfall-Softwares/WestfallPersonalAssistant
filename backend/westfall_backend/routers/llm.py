from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
from westfall_backend.services.settings import Settings
from westfall_backend.services.llama_runtime import LlamaRuntime

router = APIRouter()
_settings = Settings()
_rt = LlamaRuntime(_settings)

class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 256

@router.post("/llm/generate")
def generate(req: PromptRequest):
    return {"text": _rt.generate(req.prompt, req.max_tokens)}

@router.websocket("/llm/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    prompt = await ws.receive_text()
    for piece in _rt.stream(prompt):
        await ws.send_text(piece)
    await ws.close()