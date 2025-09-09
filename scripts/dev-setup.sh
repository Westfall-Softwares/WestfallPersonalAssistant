#!/bin/bash
# Development setup script for Westfall Personal Assistant

echo "🔧 Westfall Personal Assistant - Development Setup"
echo "=================================================="

# Check requirements
echo "Checking requirements..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install from https://python.org/"
    exit 1
fi

echo "✅ Node.js $(node --version)"
echo "✅ Python $(python3 --version)"

# Install Node.js dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
if [ -f "backend/requirements-minimal.txt" ]; then
    pip3 install -r backend/requirements-minimal.txt
else
    echo "⚠️  Minimal requirements not found, installing basic FastAPI..."
    pip3 install fastapi uvicorn psutil
fi

# Optional: Install AI dependencies
echo ""
echo "🤖 AI Dependencies (optional):"
echo "To install llama-cpp-python for local AI:"
echo "  CPU only: pip install llama-cpp-python"
echo "  CUDA:     pip install llama-cpp-python[cuda]"
echo "  Metal:    pip install llama-cpp-python[metal]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Development commands:"
echo "  npm run dev       - Start both frontend and backend"
echo "  npm run start     - Start Electron frontend only"
echo "  npm run backend   - Start Python backend only"
echo ""
echo "Testing backend directly:"
echo "  python backend/server.py --port 8756"
echo ""