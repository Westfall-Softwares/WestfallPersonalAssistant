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

### Phase 1: Core Infrastructure ✅
- [x] Electron application setup
- [x] React-based UI with Material-UI
- [x] Model selection and management
- [x] Basic conversation interface
- [x] Python backend with FastAPI
- [x] Settings management

### Phase 2: Screen Analysis
- [ ] Screen capture integration
- [ ] OCR text extraction
- [ ] Error message detection
- [ ] UI state recognition

### Phase 3: Advanced Features  
- [ ] Internet search integration
- [ ] File system navigation
- [ ] Advanced GPU optimization
- [ ] System tray integration
- [ ] Auto-start functionality

## Contributing

This is a personal project, but feedback and suggestions are welcome through issues.

## License

MIT License - See LICENSE file for details.