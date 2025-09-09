#!/usr/bin/env python3
"""
Westfall Personal Assistant - Dependency Manager

This module handles optional dependency checking and installation.
"""

import importlib
import subprocess
import sys
from typing import Dict, List, Tuple

class DependencyManager:
    """Manages optional dependencies and provides fallbacks."""
    
    def __init__(self):
        self.available_features = {}
        self.check_all_dependencies()
    
    def check_all_dependencies(self):
        """Check all optional dependencies and set availability flags."""
        dependencies = {
            'screen_capture': [
                ('opencv-python', 'cv2'),
                ('pytesseract', 'pytesseract'),
                ('pillow', 'PIL')
            ],
            'ai_models': [
                ('llama-cpp-python', 'llama_cpp'),
                ('torch', 'torch'),
                ('transformers', 'transformers')
            ],
            'advanced_processing': [
                ('numpy', 'numpy'),
                ('requests', 'requests')
            ]
        }
        
        for feature, deps in dependencies.items():
            self.available_features[feature] = all(
                self._check_dependency(package, module) for package, module in deps
            )
    
    def _check_dependency(self, package_name: str, module_name: str) -> bool:
        """Check if a specific dependency is available."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get the status of all features."""
        return self.available_features.copy()
    
    def install_feature_dependencies(self, feature: str) -> bool:
        """Install dependencies for a specific feature."""
        feature_packages = {
            'screen_capture': ['opencv-python', 'pytesseract', 'pillow'],
            'ai_models': ['llama-cpp-python'],  # Install the most common one
            'advanced_processing': ['numpy']
        }
        
        if feature not in feature_packages:
            return False
        
        try:
            packages = feature_packages[feature]
            for package in packages:
                print(f"Installing {package}...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
            
            # Recheck dependencies after installation
            self.check_all_dependencies()
            return self.available_features.get(feature, False)
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {feature} dependencies: {e}")
            return False
    
    def get_missing_dependencies(self) -> Dict[str, List[str]]:
        """Get a list of missing dependencies by feature."""
        missing = {}
        
        feature_deps = {
            'screen_capture': ['opencv-python', 'pytesseract', 'pillow'],
            'ai_models': ['llama-cpp-python', 'torch', 'transformers'],
            'advanced_processing': ['numpy']
        }
        
        for feature, packages in feature_deps.items():
            if not self.available_features.get(feature, False):
                missing[feature] = packages
        
        return missing

# Global dependency manager instance
dependency_manager = DependencyManager()

def get_dependency_status():
    """Get current dependency status for API responses."""
    return {
        'features': dependency_manager.get_feature_status(),
        'missing': dependency_manager.get_missing_dependencies()
    }

def install_dependencies_for_feature(feature: str):
    """Install dependencies for a specific feature."""
    return dependency_manager.install_feature_dependencies(feature)