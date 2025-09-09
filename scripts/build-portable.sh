#!/bin/bash

# Westfall Personal Assistant - Complete Build Script
# This script creates a production-ready, portable application

set -e

echo "🏗️  Building Westfall Personal Assistant for distribution..."
echo "=============================================================="
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
rm -rf build/
rm -f .first-run-complete

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🐍 Checking Python dependencies..."
pip install -r backend/requirements.txt

# Build React frontend
echo "⚛️  Building React frontend..."
npm run build-react

# Create portable distribution
echo "📦 Creating portable distribution..."
mkdir -p dist/portable

# Copy all necessary files for portable version
echo "  Copying application files..."
cp -r build/ dist/portable/
cp main.js preload.js dist/portable/
cp -r backend/ dist/portable/
cp package.json dist/portable/
cp westfall.png dist/portable/
cp launcher.js dist/portable/
cp run.sh dist/portable/
cp run.bat dist/portable/
cp START_HERE.md dist/portable/README.md

# Copy selected node_modules (only runtime dependencies)
echo "  Copying runtime dependencies..."
mkdir -p dist/portable/node_modules
cp -r node_modules/electron dist/portable/node_modules/
cp -r node_modules/@* dist/portable/node_modules/ 2>/dev/null || true
cp -r node_modules/react* dist/portable/node_modules/
cp -r node_modules/axios dist/portable/node_modules/
cp -r node_modules/electron-store dist/portable/node_modules/

# Create a minimal package.json for the portable version
cat > dist/portable/package.json << 'EOF'
{
  "name": "westfall-personal-assistant-portable",
  "version": "1.0.0",
  "description": "A portable AI assistant with zero-dependency installation",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "launch": "node launcher.js"
  },
  "author": "Westfall",
  "license": "MIT"
}
EOF

# Make scripts executable
chmod +x dist/portable/run.sh
chmod +x dist/portable/launcher.js

# Create final archive
echo "📦 Creating distribution archive..."
cd dist
tar -czf westfall-personal-assistant-portable.tar.gz portable/
zip -r westfall-personal-assistant-portable.zip portable/ > /dev/null
cd ..

# Build electron packages for different platforms if electron-builder is available
if command -v electron-builder &> /dev/null; then
    echo "🔧 Building Electron packages..."
    npm run build > /dev/null 2>&1 || echo "  ⚠️  Electron build skipped (may require platform-specific tools)"
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Portable Distribution:"
echo "   dist/portable/                      - Ready-to-run folder"
echo "   dist/westfall-personal-assistant-portable.tar.gz"
echo "   dist/westfall-personal-assistant-portable.zip"
echo ""
echo "🚀 To run the portable version:"
echo "   1. Extract the archive"
echo "   2. Run ./run.sh (Linux/macOS) or run.bat (Windows)"
echo "   3. The application will auto-install dependencies and start"
echo ""
echo "💡 Users only need Node.js and Python pre-installed!"
echo ""