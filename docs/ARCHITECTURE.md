# WestfallPersonalAssistant Architecture

## High-Level Architecture

**Target Architecture**: Electron frontend + Python FastAPI backend + llama.cpp local inference

### Tech Stack Decisions

#### llama.cpp Integration Mode: **B) llama-cpp-python in-process**
- Use llama-cpp-python (GGUF) in-process inside Python service
- Already implemented in `backend/ai_assistant/providers/local_llm_provider.py`
- Supports CPU and GPU acceleration (n_gpu_layers)
- Model family: GGUF quantized models
- Context window: Configurable (default 4096)
- Default params: temp=0.7, top_p=0.9, top_k=40, max_tokens=2048

#### IPC Protocol: **HTTP/REST + WebSocket streaming**
- FastAPI + uvicorn for HTTP server
- WebSocket for streaming responses  
- JSON schema for requests/responses
- Error model with structured error types

#### Configuration Strategy
- Single source: `.env` file + environment variables
- Loading precedence: env vars > .env file > defaults
- Validated using Pydantic settings

#### Package/Distribution Strategy
- electron-builder for Win (NSIS), macOS (DMG), Linux (AppImage)
- Bundle Python runtime using PyInstaller/Briefcase approach
- Models downloaded at first-run with hash verification

#### Data Directory Layout
- **Windows**: `%LOCALAPPDATA%/Westfall/Assistant`
- **macOS**: `~/Library/Application Support/Westfall/Assistant` 
- **Linux**: `~/.local/share/westfall-assistant`

## Directory Structure (Target)

```
backend/                 # Python FastAPI service + llama supervisor
  westfall_backend/
    __init__.py
    app.py              # FastAPI create_app()
    routers/
      llm.py            # LLM endpoints
      tools/            # Domain-specific tools
        finance.py
        time.py
        password.py
        music.py
      health.py         # Health/metrics endpoints
    services/
      llama_supervisor.py # llama.cpp management
      settings.py       # Pydantic settings
      logging.py        # Structured logging
    tests/
electron/               # Electron app
  main.js              # Main process
  preload.js           # Preload script
  renderer/            # React UI components
shared/                 # Shared types/schemas
scripts/               # Dev/build utilities
assets/                # Icons, images
docs/                  # Architecture docs
tests/                 # E2E + integration tests
```

## Process Architecture

1. **Electron Main Process**: 
   - Single-instance lock
   - Spawns Python backend as child process
   - Manages system tray, shortcuts, notifications
   - Handles graceful shutdown

2. **Python Backend**:
   - FastAPI server on 127.0.0.1:8756
   - Manages llama.cpp model loading/inference
   - Provides REST APIs for all features
   - Background task management

3. **Electron Renderer**:
   - React-based UI
   - Communicates with backend via HTTP/WebSocket
   - Sandboxed with contextIsolation

## Security Model

- **Electron**: contextIsolation=true, nodeIntegration=false, sandbox=true
- **Backend**: CORS limited to 127.0.0.1, no external access
- **IPC**: Minimal validated surface in preload.js
- **Secrets**: Environment variables + OS keychain
- **CSP**: Strict content security policy in renderer

## Current Implementation Status

✅ **Implemented**:
- FastAPI backend with health endpoints
- llama-cpp-python integration 
- Electron main process with backend spawning
- Security hardening (per SECURITY_IMPLEMENTATION.md)
- Basic model loading/inference

🚧 **Needs Consolidation**:
- Multiple Python entry points (app.py, main.py, main_backup.py)
- Duplicate directory structure (util/ vs utils/)
- C# Avalonia stack removal
- Proper routing structure

⚠️ **To Be Implemented**:
- Single-instance lock
- System tray
- Model downloader
- Proper error handling
- E2E testing
- Distribution packaging