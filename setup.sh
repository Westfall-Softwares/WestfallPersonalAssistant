#!/bin/bash

# Westfall Personal Assistant - One-Command Setup Script
# This script installs and updates all dependencies

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

echo "📦 Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo ""
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "⬆️  Updating dependencies to latest compatible versions..."
npm update

echo ""
echo "⬆️  Updating Python dependencies..."
pip install --upgrade -r backend/requirements.txt || echo "⚠️  Python update may have failed due to network issues"

echo ""
echo "🔒 Checking for security issues (non-breaking fixes only)..."
npm audit fix || echo "⚠️  Some security fixes may require manual intervention"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "  npm run dev    # Start both frontend and backend"
echo "  npm start      # Start frontend only"
echo "  npm run backend # Start backend only"
echo ""
echo "To update dependencies in the future:"
echo "  npm run update-deps"
echo ""