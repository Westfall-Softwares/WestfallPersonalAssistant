#!/bin/bash

# Westfall Personal Assistant - Simplified Setup Script
echo "🚀 Setting up Westfall Personal Assistant..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Node.js $(node --version) detected"
echo "✅ Python $(python3 --version | cut -d' ' -f2) detected"
echo ""

echo "📦 Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "🏗️ Building React frontend..."
npm run build-react
if [ $? -ne 0 ]; then
    echo "❌ Failed to build React frontend"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "  ./run.sh           # Use the zero-dependency launcher"
echo "  npm run dev        # Start development mode"
echo "  npm run launch     # Use Node.js launcher"
echo ""