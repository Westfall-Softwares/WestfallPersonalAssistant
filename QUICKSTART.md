# Quick Start Guide

## Installation

### 1. Prerequisites
- **Node.js 16+** (for Electron frontend)
- **Python 3.8+** (for backend server)
- **Git** (for cloning)

### 2. Clone Repository
```bash
git clone https://github.com/westfallt13-dot/WestfallPersonalAssistant.git
cd WestfallPersonalAssistant
```

### 3. Install Dependencies

#### Quick Setup (Recommended)
Run the automated setup script:
```bash
./setup.sh
```

This single command will:
- Install all Node.js dependencies
- Install all Python dependencies  
- Update dependencies to latest compatible versions
- Apply security fixes
- Verify everything is working

#### Manual Setup (Alternative)
If you prefer manual control:

##### Frontend Dependencies
```bash
npm install
```

##### Backend Dependencies (Core)
```bash
pip install -r backend/requirements.txt
```

##### Update Everything
```bash
npm run setup
```

#### Optional AI Dependencies
For full functionality, install additional packages:

```bash
# For GGUF/GGML models (recommended for RTX 2060)
pip install llama-cpp-python

# For PyTorch/Transformers models
pip install torch transformers

# For screen capture features  
pip install opencv-python pytesseract pillow
```

## Updating Dependencies

### Keep Everything Up to Date
```bash
npm run update-deps
```

This command will:
- Update Node.js packages to latest compatible versions
- Update Python packages to latest versions
- Maintain compatibility with your current setup

### Security Updates Only
```bash
npm run audit-fix
```

### Individual Updates
```bash
# Update Node.js packages only
npm update

# Update Python packages only  
npm run update-python
```

## Usage

### Development Mode
Start both frontend and backend:
```bash
npm run dev
```

### Production Mode
Build and run:
```bash
npm run build-react
npm run build
```

### Individual Components
```bash
# Frontend only
npm start

# Backend only  
npm run backend
# or
python backend/server.py
```

## Features

### ✅ Available Now
- **Chat Interface**: Three thinking modes (Normal/Thinking/Research)
- **Model Management**: File browser integration, server lifecycle
- **Settings**: GPU configuration, privacy options
- **Architecture**: Complete Electron + React + Python FastAPI stack

### 🔧 Requires Dependencies
- **Screen Capture**: Install PIL, OpenCV, Tesseract
- **Real AI Models**: Install llama-cpp-python or transformers
- **GPU Acceleration**: Install PyTorch with CUDA support

### 📋 Planned Features
- Internet search integration
- File system navigation
- System tray integration
- Auto-start functionality

## Configuration

### GPU Settings (RTX 2060 Optimized)
- **Auto GPU Layers**: Automatically calculates optimal offloading
- **VRAM Limit**: Default 80% (leaves room for system)
- **Model Recommendations**: GGUF Q4/Q5 quantized models

### Privacy Settings
- **Local Processing**: All data stays on your machine
- **No External Connections**: Complete offline operation
- **Secure Storage**: Temporary files with automatic cleanup

## Troubleshooting

### Dependency Issues
1. **Outdated dependencies**: Run `npm run update-deps` to update everything
2. **Security vulnerabilities**: Run `npm run audit-fix` for safe fixes
3. **Python dependency conflicts**: Try `pip install --upgrade -r backend/requirements.txt`
4. **Node.js version issues**: Ensure you have Node.js 16+ installed

### Model Loading Issues
1. Check model file format (GGUF, GGML, PyTorch)
2. Verify model file integrity
3. Check available disk space and memory
4. Review GPU memory usage

### Screen Capture Not Working
1. Install required dependencies:
   ```bash
   pip install pillow opencv-python pytesseract
   ```
2. On Windows, install Tesseract OCR executable
3. Check system permissions for screen capture

### Performance Optimization
- Use quantized models (Q4_K_M recommended for RTX 2060)
- Adjust GPU layers in settings based on model size
- Monitor VRAM usage and adjust limits if needed
- Close other GPU-intensive applications

## Model Recommendations

### For RTX 2060 (6GB VRAM)
- **Llama 2 7B Q4_K_M**: Balanced performance/quality
- **Mistral 7B Q5_K_M**: Higher quality, slightly slower
- **CodeLlama 7B Q4_K_M**: For coding assistance
- **Vicuna 7B Q4_K_M**: Strong conversational abilities

### Download Sources
- **Hugging Face**: https://huggingface.co/models
- **GGML Models**: Search for "GGUF" versions
- **TheBloke**: Quantized model specialist on Hugging Face

## Support

### Common Issues
1. **"No model loaded"**: Select a model in Model Manager
2. **"GPU not available"**: Install PyTorch with CUDA support
3. **"Screen capture failed"**: Install PIL/OpenCV dependencies
4. **Slow inference**: Try smaller model or more GPU layers

### Getting Help
- Check DEVELOPMENT.md for technical details
- Review logs in backend console output
- Verify all dependencies are installed correctly

## Next Steps

1. **Download a Model**: Get a GGUF model from Hugging Face
2. **Load Model**: Use Model Manager to select and start
3. **Start Chatting**: Try different thinking modes
4. **Explore Settings**: Optimize for your hardware
5. **Add Screen Capture**: Install optional dependencies