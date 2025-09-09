#!/bin/bash
# Cross-Platform Deployment Script for Westfall Personal Assistant
# Builds and packages the application for Windows, macOS, and Linux

set -e

echo "🚀 Starting cross-platform deployment for Westfall Personal Assistant"
echo "======================================================================"

# Configuration
APP_NAME="WestfallPersonalAssistant"
VERSION="1.0.0"
OUTPUT_DIR="dist"
RUNTIMES=("win-x64" "osx-x64" "linux-x64")

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Build for each runtime
for runtime in "${RUNTIMES[@]}"; do
    echo ""
    echo "🔨 Building for $runtime..."
    
    # Create runtime-specific output directory
    runtime_dir="$OUTPUT_DIR/$runtime"
    mkdir -p "$runtime_dir"
    
    # Publish the application
    dotnet publish \
        --runtime "$runtime" \
        --configuration Release \
        --self-contained true \
        --output "$runtime_dir" \
        --framework net8.0 \
        -p:PublishSingleFile=true \
        -p:PublishTrimmed=false \
        -p:IncludeNativeLibrariesForSelfExtract=true
    
    # Create platform-specific packages
    case $runtime in
        "win-x64")
            echo "📦 Creating Windows package..."
            cd "$runtime_dir"
            zip -r "../${APP_NAME}-${VERSION}-Windows-x64.zip" .
            cd - > /dev/null
            ;;
        "osx-x64")
            echo "📦 Creating macOS package..."
            cd "$runtime_dir"
            tar -czf "../${APP_NAME}-${VERSION}-macOS-x64.tar.gz" .
            cd - > /dev/null
            ;;
        "linux-x64")
            echo "📦 Creating Linux package..."
            cd "$runtime_dir"
            tar -czf "../${APP_NAME}-${VERSION}-Linux-x64.tar.gz" .
            cd - > /dev/null
            ;;
    esac
    
    echo "✅ $runtime build complete"
done

echo ""
echo "🎉 Cross-platform deployment complete!"
echo ""
echo "📦 Generated packages:"
ls -la "$OUTPUT_DIR"/*.zip "$OUTPUT_DIR"/*.tar.gz 2>/dev/null || true

echo ""
echo "📋 Deployment Summary:"
echo "- Windows: ${APP_NAME}-${VERSION}-Windows-x64.zip"
echo "- macOS: ${APP_NAME}-${VERSION}-macOS-x64.tar.gz"
echo "- Linux: ${APP_NAME}-${VERSION}-Linux-x64.tar.gz"

echo ""
echo "🎯 Ready for distribution!"