#!/bin/bash

# Cross-Platform Compatibility Test Script for Westfall Assistant

echo "Building Westfall Assistant..."
dotnet build

if [ $? -eq 0 ]; then
    echo "Build successful. Running platform compatibility test..."
    echo ""
    
    # Run the platform test
    dotnet run --project . -- --platform-test
    
    echo ""
    echo "Platform test completed."
else
    echo "Build failed. Please check for compilation errors."
    exit 1
fi