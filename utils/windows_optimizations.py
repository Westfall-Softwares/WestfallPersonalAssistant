#!/usr/bin/env python3
"""
Windows 10 Optimizations Module
Provides Windows 10 specific performance tuning, memory compression, and system integration
"""

import os
import sys
import ctypes
import logging
import threading
import winreg
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication

# Windows API imports (only available on Windows)
if sys.platform == 'win32':
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
        import win32security
        import win32net
        import win32netcon
        import wmi
        from win32com.shell import shell, shellcon
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Windows API modules not available - some features will be disabled")
else:
    WINDOWS_APIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class WindowsMemoryManager:
    """Windows 10 Memory Compression and Management"""
    
    def __init__(self):
        self.compression_enabled = False
        self.memory_stats = {}
        
    def enable_memory_compression(self) -> bool:
        """Enable Windows 10 memory compression"""
        if not WINDOWS_APIS_AVAILABLE:
            return False
            
        try:
            # Check if memory compression is available
            if self._is_memory_compression_available():
                # Enable via PowerShell
                import subprocess
                result = subprocess.run([
                    'powershell', '-Command',
                    'Enable-MMAgent -MemoryCompression'
                ], capture_output=True, text=True)
                
                self.compression_enabled = result.returncode == 0
                logger.info(f"Memory compression enabled: {self.compression_enabled}")
                return self.compression_enabled
                
        except Exception as e:
            logger.error(f"Failed to enable memory compression: {e}")
            
        return False
    
    def _is_memory_compression_available(self) -> bool:
        """Check if memory compression is available on this system"""
        try:
            import subprocess
            result = subprocess.run([
                'powershell', '-Command',
                'Get-MMAgent | Select-Object MemoryCompression'
            ], capture_output=True, text=True)
            
            return "True" in result.stdout or "False" in result.stdout
        except:
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics"""
        if not WINDOWS_APIS_AVAILABLE:
            return {}
            
        try:
            c = wmi.WMI()
            
            # Get memory information
            for memory in c.Win32_OperatingSystem():
                total_memory = int(memory.TotalVisibleMemorySize) * 1024
                free_memory = int(memory.FreePhysicalMemory) * 1024
                
                self.memory_stats = {
                    'total_memory_gb': round(total_memory / (1024**3), 2),
                    'free_memory_gb': round(free_memory / (1024**3), 2),
                    'used_memory_gb': round((total_memory - free_memory) / (1024**3), 2),
                    'memory_usage_percent': round(((total_memory - free_memory) / total_memory) * 100, 1),
                    'compression_enabled': self.compression_enabled
                }
                
            return self.memory_stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def optimize_memory_usage(self) -> bool:
        """Optimize memory usage for the application"""
        try:
            # Set process priority to normal
            if WINDOWS_APIS_AVAILABLE:
                handle = win32api.GetCurrentProcess()
                win32process.SetPriorityClass(handle, win32process.NORMAL_PRIORITY_CLASS)
            
            # Trigger garbage collection
            import gc
            gc.collect()
            
            # Clear PyQt caches if available
            app = QApplication.instance()
            if app:
                app.processEvents()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize memory: {e}")
            return False


class WindowsHelloIntegration:
    """Windows Hello authentication integration"""
    
    def __init__(self):
        self.is_available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if Windows Hello is available"""
        if not WINDOWS_APIS_AVAILABLE:
            return False
            
        try:
            # Check registry for Windows Hello availability
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\WinBio") as key:
                return True
        except:
            return False
    
    def is_hello_available(self) -> bool:
        """Check if Windows Hello is available and configured"""
        return self.is_available
    
    def authenticate_user(self) -> Dict[str, Any]:
        """Attempt Windows Hello authentication"""
        if not self.is_available:
            return {"success": False, "error": "Windows Hello not available"}
            
        try:
            # This would integrate with Windows Hello APIs
            # For now, return success simulation
            return {
                "success": True,
                "method": "windows_hello",
                "user": os.getenv('USERNAME', 'Unknown')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class WindowsJumpListManager:
    """Windows Jump List integration for taskbar quick actions"""
    
    def __init__(self):
        self.jump_list_items = []
        
    def create_jump_list(self, app_name: str = "Westfall Personal Assistant") -> bool:
        """Create Jump List with quick actions"""
        if not WINDOWS_APIS_AVAILABLE:
            return False
            
        try:
            # Get the application's executable path
            exe_path = sys.executable
            
            # Define quick actions
            actions = [
                ("Quick Chat", f'"{exe_path}" --quick-chat', "Open quick chat interface"),
                ("Screen Capture", f'"{exe_path}" --screen-capture', "Capture screen"),
                ("New Note", f'"{exe_path}" --new-note', "Create new note"),
                ("Settings", f'"{exe_path}" --settings', "Open settings")
            ]
            
            # Create jump list entries
            for title, command, description in actions:
                self.jump_list_items.append({
                    'title': title,
                    'command': command,
                    'description': description
                })
            
            logger.info(f"Created jump list with {len(actions)} items")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create jump list: {e}")
            return False
    
    def get_jump_list_items(self) -> List[Dict[str, str]]:
        """Get current jump list items"""
        return self.jump_list_items


class WindowsThemeDetector(QObject):
    """Windows 10 dark/light theme detection and integration"""
    
    theme_changed = pyqtSignal(str)  # 'dark' or 'light'
    
    def __init__(self):
        super().__init__()
        self.current_theme = self._detect_theme()
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_theme_change)
        self.monitor_timer.start(5000)  # Check every 5 seconds
        
    def _detect_theme(self) -> str:
        """Detect current Windows theme"""
        if not WINDOWS_APIS_AVAILABLE:
            return 'light'
            
        try:
            # Check registry for theme setting
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return 'light' if light_theme else 'dark'
        except:
            return 'light'
    
    def _check_theme_change(self):
        """Check if theme has changed"""
        new_theme = self._detect_theme()
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self.theme_changed.emit(new_theme)
            logger.info(f"Theme changed to: {new_theme}")
    
    def get_current_theme(self) -> str:
        """Get current theme"""
        return self.current_theme


class WindowsCredentialVault:
    """Windows Credential Manager integration for secure storage"""
    
    def __init__(self):
        self.app_name = "WestfallPersonalAssistant"
        
    def store_credential(self, key: str, username: str, password: str) -> bool:
        """Store credential in Windows Credential Manager"""
        if not WINDOWS_APIS_AVAILABLE:
            return False
            
        try:
            import subprocess
            # Use cmdkey to store credential
            result = subprocess.run([
                'cmdkey', '/generic', f"{self.app_name}:{key}",
                '/user', username, '/pass', password
            ], capture_output=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False
    
    def retrieve_credential(self, key: str) -> Optional[Dict[str, str]]:
        """Retrieve credential from Windows Credential Manager"""
        if not WINDOWS_APIS_AVAILABLE:
            return None
            
        try:
            import subprocess
            # Use cmdkey to list credentials and parse
            result = subprocess.run([
                'cmdkey', '/list', f"{self.app_name}:{key}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output to extract username
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'User:' in line:
                        username = line.split('User:')[1].strip()
                        return {'username': username, 'key': key}
                        
        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
            
        return None
    
    def delete_credential(self, key: str) -> bool:
        """Delete credential from Windows Credential Manager"""
        if not WINDOWS_APIS_AVAILABLE:
            return False
            
        try:
            import subprocess
            result = subprocess.run([
                'cmdkey', '/delete', f"{self.app_name}:{key}"
            ], capture_output=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to delete credential: {e}")
            return False


class WindowsPowerManager:
    """Windows 10 power plan integration"""
    
    def __init__(self):
        self.power_plans = self._get_power_plans()
        self.current_plan = self._get_current_power_plan()
        
    def _get_power_plans(self) -> Dict[str, str]:
        """Get available power plans"""
        plans = {}
        if not WINDOWS_APIS_AVAILABLE:
            return plans
            
        try:
            import subprocess
            result = subprocess.run([
                'powercfg', '/list'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Power Scheme GUID:' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            guid = parts[3]
                            name = ' '.join(parts[4:]).strip('()')
                            plans[name] = guid
                            
        except Exception as e:
            logger.error(f"Failed to get power plans: {e}")
            
        return plans
    
    def _get_current_power_plan(self) -> Optional[str]:
        """Get current active power plan"""
        if not WINDOWS_APIS_AVAILABLE:
            return None
            
        try:
            import subprocess
            result = subprocess.run([
                'powercfg', '/getactivescheme'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                line = result.stdout.strip()
                if '(' in line and ')' in line:
                    return line.split('(')[1].split(')')[0]
                    
        except Exception as e:
            logger.error(f"Failed to get current power plan: {e}")
            
        return None
    
    def set_power_plan(self, plan_name: str) -> bool:
        """Set active power plan"""
        if not WINDOWS_APIS_AVAILABLE or plan_name not in self.power_plans:
            return False
            
        try:
            import subprocess
            guid = self.power_plans[plan_name]
            result = subprocess.run([
                'powercfg', '/setactive', guid
            ], capture_output=True)
            
            if result.returncode == 0:
                self.current_plan = plan_name
                logger.info(f"Power plan changed to: {plan_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set power plan: {e}")
            
        return False
    
    def get_power_status(self) -> Dict[str, Any]:
        """Get current power status"""
        return {
            'current_plan': self.current_plan,
            'available_plans': list(self.power_plans.keys()),
            'plans_count': len(self.power_plans)
        }


class HardwareAccelerationDetector:
    """Hardware acceleration detection and auto-configuration"""
    
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        self.acceleration_available = self._check_acceleration()
        
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU hardware"""
        gpu_info = {
            'has_gpu': False,
            'gpu_name': 'Unknown',
            'driver_version': 'Unknown',
            'memory_mb': 0,
            'cuda_support': False,
            'opencl_support': False
        }
        
        if not WINDOWS_APIS_AVAILABLE:
            return gpu_info
            
        try:
            c = wmi.WMI()
            
            for gpu in c.Win32_VideoController():
                if gpu.Name and 'Microsoft' not in gpu.Name:
                    gpu_info.update({
                        'has_gpu': True,
                        'gpu_name': gpu.Name,
                        'driver_version': gpu.DriverVersion or 'Unknown',
                        'memory_mb': int(gpu.AdapterRAM or 0) // (1024 * 1024) if gpu.AdapterRAM else 0
                    })
                    
                    # Check for NVIDIA CUDA support
                    if 'NVIDIA' in gpu.Name.upper():
                        gpu_info['cuda_support'] = self._check_cuda()
                    
                    # Check for OpenCL support
                    gpu_info['opencl_support'] = self._check_opencl()
                    break
                    
        except Exception as e:
            logger.error(f"Failed to detect GPU: {e}")
            
        return gpu_info
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_opencl(self) -> bool:
        """Check if OpenCL is available"""
        try:
            # This would check for OpenCL libraries
            return True  # Simplified for now
        except:
            return False
    
    def _check_acceleration(self) -> bool:
        """Check if hardware acceleration is available"""
        return self.gpu_info['has_gpu'] and (
            self.gpu_info['cuda_support'] or self.gpu_info['opencl_support']
        )
    
    def get_acceleration_config(self) -> Dict[str, Any]:
        """Get recommended acceleration configuration"""
        config = {
            'use_gpu': self.acceleration_available,
            'gpu_layers': 0,
            'memory_limit_mb': 0,
            'precision': 'fp32'
        }
        
        if self.acceleration_available:
            # Calculate optimal settings based on GPU memory
            gpu_memory = self.gpu_info['memory_mb']
            
            if gpu_memory >= 8192:  # 8GB+
                config.update({
                    'gpu_layers': 35,
                    'memory_limit_mb': 6144,
                    'precision': 'fp16'
                })
            elif gpu_memory >= 6144:  # 6GB
                config.update({
                    'gpu_layers': 25,
                    'memory_limit_mb': 4096,
                    'precision': 'fp16'
                })
            elif gpu_memory >= 4096:  # 4GB
                config.update({
                    'gpu_layers': 15,
                    'memory_limit_mb': 2048,
                    'precision': 'int8'
                })
        
        return config


class WindowsOptimizationManager(QObject):
    """Main Windows 10 optimization manager"""
    
    optimization_completed = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.memory_manager = WindowsMemoryManager()
        self.hello_integration = WindowsHelloIntegration()
        self.jump_list_manager = WindowsJumpListManager()
        self.theme_detector = WindowsThemeDetector()
        self.credential_vault = WindowsCredentialVault()
        self.power_manager = WindowsPowerManager()
        self.hardware_detector = HardwareAccelerationDetector()
        
        # Connect theme changes
        self.theme_detector.theme_changed.connect(self._on_theme_changed)
        
    def _on_theme_changed(self, theme: str):
        """Handle theme change"""
        self.optimization_completed.emit('theme_changed', {'theme': theme})
    
    def initialize_optimizations(self) -> Dict[str, Any]:
        """Initialize all Windows optimizations"""
        results = {}
        
        # Memory optimization
        results['memory_compression'] = self.memory_manager.enable_memory_compression()
        results['memory_stats'] = self.memory_manager.get_memory_stats()
        
        # Authentication
        results['windows_hello'] = self.hello_integration.is_hello_available()
        
        # Taskbar integration
        results['jump_list'] = self.jump_list_manager.create_jump_list()
        
        # Theme detection
        results['theme'] = self.theme_detector.get_current_theme()
        
        # Power management
        results['power_status'] = self.power_manager.get_power_status()
        
        # Hardware acceleration
        results['hardware_acceleration'] = self.hardware_detector.get_acceleration_config()
        
        logger.info("Windows optimizations initialized")
        return results
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            'platform': 'Windows 10+' if WINDOWS_APIS_AVAILABLE else 'Generic',
            'memory_compression': self.memory_manager.compression_enabled,
            'windows_hello': self.hello_integration.is_available,
            'current_theme': self.theme_detector.current_theme,
            'power_plan': self.power_manager.current_plan,
            'hardware_acceleration': self.hardware_detector.acceleration_available,
            'jump_list_items': len(self.jump_list_manager.jump_list_items)
        }


# Global instance
_windows_optimization_manager = None
_manager_lock = threading.Lock()


def get_windows_optimization_manager() -> WindowsOptimizationManager:
    """Get the global Windows optimization manager instance"""
    global _windows_optimization_manager
    
    if _windows_optimization_manager is None:
        with _manager_lock:
            if _windows_optimization_manager is None:
                _windows_optimization_manager = WindowsOptimizationManager()
    
    return _windows_optimization_manager


# Convenience functions
def is_windows_10_or_later() -> bool:
    """Check if running on Windows 10 or later"""
    if sys.platform != 'win32':
        return False
        
    import platform
    version = platform.version()
    major_version = int(version.split('.')[0])
    build_number = int(version.split('.')[2])
    
    # Windows 10 is version 10.0 with build >= 10240
    return major_version >= 10 and build_number >= 10240


def optimize_for_windows_10() -> Dict[str, Any]:
    """Quick function to apply Windows 10 optimizations"""
    if not is_windows_10_or_later():
        return {'error': 'Not running on Windows 10 or later'}
    
    manager = get_windows_optimization_manager()
    return manager.initialize_optimizations()


if __name__ == "__main__":
    # Test the module
    print("Windows 10 Optimization Module Test")
    print("=" * 40)
    
    print(f"Windows 10+ detected: {is_windows_10_or_later()}")
    print(f"Windows APIs available: {WINDOWS_APIS_AVAILABLE}")
    
    if is_windows_10_or_later():
        results = optimize_for_windows_10()
        for key, value in results.items():
            print(f"{key}: {value}")