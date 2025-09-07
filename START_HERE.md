# Westfall Personal Assistant - Quick Start

> **Zero-Dependency Installation** - Just download and run!

## 🚀 Instant Start (Recommended)

### For All Platforms:
1. **Download** this repository
2. **Double-click** the launcher for your platform:
   - **Windows**: `run.bat`
   - **Linux/macOS**: `run.sh`

That's it! The launcher will automatically:
- Install all required dependencies
- Build the application
- Launch Westfall Personal Assistant

### Alternative Start Methods:
```bash
# Using Node.js directly
node launcher.js

# Or using npm
npm run launch
```

## 🎯 What You Get

**Westfall Personal Assistant** is a powerful desktop AI assistant that runs entirely on your local machine:

- **🤖 Local AI Chat** - Three thinking modes (Normal/Thinking/Research)
- **📱 Modern Interface** - Clean Material-UI design with dark theme
- **🔒 Complete Privacy** - All processing happens locally, no data sent anywhere
- **⚙️ Easy Model Management** - Built-in file browser for AI models
- **🖥️ Screen Analysis** - Capture and analyze your screen (optional dependencies)
- **⚡ GPU Acceleration** - Optimized for RTX 2060 and other GPUs

## 📋 Prerequisites

The launcher requires these to be installed on your system:
- **Node.js 16+** (Download from [nodejs.org](https://nodejs.org/))
- **Python 3.8+** (Download from [python.org](https://python.org/))

Everything else is installed automatically!

## 🔧 Optional Features

For enhanced functionality, the launcher can optionally install:
- **llama-cpp-python** - For GGUF/GGML model support
- **opencv-python** - For screen capture
- **pytesseract** - For OCR text extraction
- **pillow** - For image processing

These will be installed automatically when you first use the features that need them.

## 🏗️ Developer Mode

If you want to modify the code:

```bash
# Manual setup (one-time)
npm run setup-deps

# Start development mode
npm run dev

# Build for production
npm run build
```

## 📖 Full Documentation

- See `DEVELOPMENT.md` for technical details
- See `QUICKSTART.md` for advanced configuration
- See `README.md` for complete feature documentation

## 🐛 Troubleshooting

If the launcher doesn't work:

1. **Check prerequisites**: Ensure Node.js and Python are installed
2. **Run manually**: Try `npm install` then `npm run dev`
3. **Check permissions**: Make sure the launcher script is executable
4. **Clear cache**: Delete `.first-run-complete` to reset setup

---

**Ready to start?** Just double-click your platform's launcher file! 🎉