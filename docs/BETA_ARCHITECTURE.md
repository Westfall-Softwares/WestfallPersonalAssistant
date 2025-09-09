# WestfallPersonalAssistant Architecture

## High-Level Overview

**WestfallPersonalAssistant** is a privacy-first desktop AI assistant built with Electron + Python FastAPI + llama.cpp. All processing happens locally on the user's machine.

### Technology Stack
- **Frontend**: Electron with React UI (secure, sandboxed)
- **Backend**: Python FastAPI service running on 127.0.0.1
- **AI Engine**: llama-cpp-python with GGUF model support
- **Security**: Context isolation, local-only processing, CORS restrictions

## Process Architecture

1. **Electron Main Process**: 
   - Single-instance lock
   - Spawns Python backend as child process
   - Manages system tray, shortcuts, notifications
   - Handles graceful shutdown

2. **Python Backend**:
   - FastAPI server on 127.0.0.1 (ephemeral port)
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

## API Endpoints

### Health & Status
- `GET /api/health` - System health and metrics
- `GET /api/metrics` - Prometheus-style metrics
- `GET /api/ready` - Readiness check

### LLM Inference
- `POST /api/llm/chat` - Generate chat response
- `POST /api/llm/chat/stream` - Stream chat response
- `GET /api/llm/models` - List available models
- `POST /api/llm/models/load` - Load a model
- `POST /api/llm/models/unload` - Unload current model

### Tools & Services
- `GET /api/tools/` - List available tools
- `POST /api/tools/finance` - Financial tools
- `POST /api/tools/time` - Time tracking
- `POST /api/tools/password` - Password management
- `POST /api/tools/music` - Music control

## Data Directory Layout

- **Windows**: `%LOCALAPPDATA%/Westfall/Assistant`
- **macOS**: `~/Library/Application Support/Westfall/Assistant` 
- **Linux**: `~/.local/share/westfall-assistant`

### Directory Structure
```
data/
├── models/              # GGUF model files
├── logs/               # Application logs
├── conversations/      # Chat history
└── config/            # User configuration
```

## Configuration

Environment variables (prefix: `WESTFALL_`):

- `WESTFALL_HOST` - Server bind address (default: 127.0.0.1)
- `WESTFALL_PORT` - Server port (default: 0 = auto)
- `WESTFALL_MODEL_PATH` - Path to default model
- `WESTFALL_N_CTX` - Context window size (default: 4096)
- `WESTFALL_N_GPU_LAYERS` - GPU acceleration layers (default: 0)
- `WESTFALL_LOG_LEVEL` - Logging level (default: INFO)

## Development Workflow

### Backend Development
```bash
# Start backend
python -m backend.westfall_backend.app

# Run tests
python backend/tests/test_smoke.py

# Access API docs
curl http://127.0.0.1:8756/api/docs
```

### Electron Development
```bash
cd electron

# Development with hot reload
npm run dev

# Build for distribution
npm run build
```

### Integration Testing
```bash
# Test full integration
cd electron
node scripts/start-backend.js
```

## Security Considerations

1. **Local Processing Only**: No data sent to external services
2. **Port Binding**: Backend only binds to 127.0.0.1
3. **Process Isolation**: Electron renderer is sandboxed
4. **Input Validation**: All API inputs validated via Pydantic
5. **Error Handling**: Graceful degradation without data leaks

## Performance Characteristics

- **Cold Start**: ~2-5 seconds for backend startup
- **Model Loading**: Varies by model size (1-30 seconds)
- **Response Time**: ~100ms-2s depending on model and prompt
- **Memory Usage**: 2-8GB depending on model size
- **CPU Usage**: Varies with model complexity and context length

## Deployment & Distribution

Built using electron-builder with:
- **Windows**: NSIS installer
- **macOS**: DMG with code signing
- **Linux**: AppImage and DEB packages

Backend packaged with PyInstaller for self-contained distribution.