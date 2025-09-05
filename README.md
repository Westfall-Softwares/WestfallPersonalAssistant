# Westfall Personal Assistant

A local AI assistant with advanced features including screen capture, model management, and three-tier thinking modes.

## Features

### Core Capabilities
- **Three-Tier Thinking System**: Normal, Thinking, and Research modes
- **Local Model Management**: Support for GGUF, GGML, PyTorch, and other formats
- **Screen Capture & Analysis**: Local screen monitoring with OCR and error detection
- **GPU Acceleration**: Optimized for RTX 2060 with smart layer offloading

### Privacy & Security
- All processing done locally
- No external data transmission
- Optional sensitive information masking
- Secure temporary storage and deletion

## Installation

### Prerequisites
- Node.js 16+ 
- Python 3.8+
- Git

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/westfallt13-dot/WestfallPersonalAssistant.git
   cd WestfallPersonalAssistant
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### Optional AI Dependencies
For full functionality, install additional dependencies based on your model format:

```bash
# For PyTorch models
pip install torch>=2.0.0 transformers>=4.35.0

# For GGUF/GGML models (recommended)
pip install llama-cpp-python>=0.2.0

# For screen capture features
pip install opencv-python>=4.8.0 pytesseract>=0.3.10 pillow>=10.0.0
```

## Usage

### Development Mode
```bash
npm run dev
```
This starts both the Electron frontend and Python backend.

### Production Build
```bash
npm run build
```

### Running Components Separately
- Frontend only: `npm start`
- Backend only: `npm run backend`

## Architecture

### Frontend (Electron + React)
- Modern Material-UI based interface
- Real-time chat with the AI assistant
- Model selection and management
- Settings and configuration

### Backend (Python + FastAPI)
- Local model inference server
- Support for multiple AI model formats
- GPU acceleration with automatic optimization
- Screen capture and analysis APIs

## Configuration

The application stores settings locally using Electron Store:
- Model preferences and paths
- Thinking mode defaults
- GPU acceleration settings
- Privacy and security options

## Development

### Project Structure
```
├── main.js              # Electron main process
├── preload.js           # Electron preload script
├── src/                 # React frontend
│   ├── components/      # UI components
│   └── App.js          # Main application
├── backend/             # Python backend
│   ├── server.py       # FastAPI server
│   └── requirements.txt # Python dependencies
├── build/               # Build assets
└── public/              # Static assets
```

### Adding New Features
1. Frontend components go in `src/components/`
2. Backend APIs are added to `backend/server.py`
3. IPC communication is handled in `main.js` and `preload.js`

## Roadmap

### Current Status: Production Ready ✅

**Westfall Personal Assistant** is a fully functional desktop application with comprehensive AI assistant capabilities, screen analysis, and local model management. All core phases have been completed and the application is ready for daily use.

### Phase 1: Core Infrastructure ✅
- [x] Electron application setup
- [x] React-based UI with Material-UI
- [x] Model selection and management
- [x] Basic conversation interface
- [x] Python backend with FastAPI
- [x] Settings management

### Phase 2: Screen Analysis ✅
- [x] Screen capture integration with PIL/ImageGrab
- [x] OCR text extraction using Tesseract
- [x] Error message detection with pattern matching
- [x] UI element analysis framework with OpenCV
- [x] Continuous monitoring capabilities
- [x] Privacy-focused local processing
- [x] Frontend controls and status display

### Phase 3: AI Model Integration
- [x] Model handler architecture with GGUF/PyTorch support
- [x] GPU detection and configuration UI
- [x] Model loading/unloading lifecycle management
- [x] Three thinking modes implementation (Normal/Thinking/Research)
- [x] Context management and conversation handling
- [x] RTX 2060 optimization framework

### Phase 4: Production Features
- [x] Complete Electron application with React frontend
- [x] Material-UI dark theme interface
- [x] Settings persistence with Electron Store
- [x] Cross-platform build configuration
- [x] Development and production build scripts
- [x] Comprehensive API documentation

### Implementation Summary

**🎯 Core Functionality Complete**: All essential features for a local AI assistant are implemented and functional, including three thinking modes, screen capture with OCR, model management, and GPU optimization.

**🔧 Dependency Installation**: To unlock full capabilities, install optional dependencies:
- `pip install llama-cpp-python` for GGUF model support
- `pip install opencv-python pytesseract pillow` for screen capture
- `pip install torch transformers` for PyTorch model support

**🚀 Ready for Use**: The application provides a complete AI assistant experience with local processing, privacy protection, and optimized performance for RTX 2060 systems.

## Contributing

This is a personal project, but feedback and suggestions are welcome through issues.

## License

MIT License - See LICENSE file for details.