#!/bin/bash

# Westfall Personal Assistant - Linux/macOS Launcher
# This script automatically sets up and runs the application

echo "🚀 Westfall Personal Assistant - Zero-Dependency Launcher"
echo "=================================================================="
echo ""

# Check for required tools
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js 16+ from: https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ from: https://python.org/"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"
echo "✅ Python $(python3 --version | cut -d' ' -f2) detected"
echo ""

# Use the Node.js launcher with updated path
node electron/launcher.js