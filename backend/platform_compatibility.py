#!/usr/bin/env python3
"""
Cross-Platform Compatibility Module for Westfall Assistant

Provides platform detection, path handling, and platform-specific implementations
to ensure consistent behavior across Windows, macOS, and Linux.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import logging
import tempfile
import shutil

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported platform types."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class Architecture(Enum):
    """System architectures."""
    X86_64 = "x86_64"
    ARM64 = "arm64"
    X86 = "x86"
    UNKNOWN = "unknown"


class PlatformInfo:
    """Platform information and capabilities."""
    
    def __init__(self):
        self._detect_platform()
        self._detect_capabilities()
    
    def _detect_platform(self):
        """Detect the current platform."""
        system = platform.system().lower()
        
        if system == "windows":
            self.platform = PlatformType.WINDOWS
        elif system == "darwin":
            self.platform = PlatformType.MACOS
        elif system == "linux":
            self.platform = PlatformType.LINUX
        else:
            self.platform = PlatformType.UNKNOWN
        
        # Architecture detection
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            self.architecture = Architecture.X86_64
        elif machine in ["arm64", "aarch64"]:
            self.architecture = Architecture.ARM64
        elif machine in ["x86", "i386", "i686"]:
            self.architecture = Architecture.X86
        else:
            self.architecture = Architecture.UNKNOWN
        
        # Python info
        self.python_version = sys.version_info
        self.python_executable = sys.executable
        
        # System info
        self.system_name = platform.system()
        self.system_version = platform.version()
        self.system_release = platform.release()
        
        logger.info(f"Detected platform: {self.platform.value} ({self.architecture.value})")
    
    def _detect_capabilities(self):
        """Detect platform-specific capabilities."""
        self.capabilities = {
            'shell_commands': True,
            'file_associations': True,
            'system_notifications': True,
            'process_monitoring': True,
            'memory_info': True,
            'network_interfaces': True
        }
        
        # Platform-specific capabilities
        if self.platform == PlatformType.WINDOWS:
            self.capabilities.update({
                'windows_registry': True,
                'windows_services': True,
                'powershell': self._check_powershell(),
                'wmi': self._check_wmi(),
                'windows_hello': self._check_windows_hello(),
                'action_center': self._check_action_center(),
                'jump_lists': self._check_jump_lists(),
                'credential_manager': self._check_credential_manager(),
                'memory_compression': self._check_memory_compression(),
                'hardware_acceleration': self._check_hardware_acceleration(),
                'dark_theme_api': self._check_dark_theme_api()
            })
        elif self.platform == PlatformType.MACOS:
            self.capabilities.update({
                'osascript': self._check_osascript(),
                'brew': self._check_brew(),
                'launchctl': True
            })
        elif self.platform == PlatformType.LINUX:
            self.capabilities.update({
                'systemd': self._check_systemd(),
                'dbus': self._check_dbus(),
                'xdg': self._check_xdg()
            })
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            import subprocess
            subprocess.run([command, '--version'], capture_output=True, check=False, timeout=5)
            return True
        except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            return False
    
    def _check_powershell(self) -> bool:
        """Check if PowerShell is available."""
        return self._check_command('powershell')
    
    def _check_wmi(self) -> bool:
        """Check if WMI is available."""
        try:
            import wmi
            return True
        except ImportError:
            return False
    
    def _check_osascript(self) -> bool:
        """Check if osascript is available."""
        return self._check_command('osascript')
    
    def _check_brew(self) -> bool:
        """Check if Homebrew is available."""
        return self._check_command('brew')
    
    def _check_systemd(self) -> bool:
        """Check if systemd is available."""
        return Path('/run/systemd/system').exists()
    
    def _check_dbus(self) -> bool:
        """Check if D-Bus is available."""
        return self._check_command('dbus-send')
    
    def _check_xdg(self) -> bool:
        """Check if XDG utilities are available."""
        return self._check_command('xdg-open')
    
    def _check_windows_hello(self) -> bool:
        """Check if Windows Hello is available."""
        if self.platform != PlatformType.WINDOWS:
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\WinBio") as key:
                return True
        except:
            return False
    
    def _check_action_center(self) -> bool:
        """Check if Windows 10 Action Center is available."""
        if self.platform != PlatformType.WINDOWS:
            return False
        # Check if we're on Windows 10 or later
        version_parts = self.system_version.split('.')
        if len(version_parts) >= 3:
            build = int(version_parts[2])
            return build >= 10240  # Windows 10 build threshold
        return False
    
    def _check_jump_lists(self) -> bool:
        """Check if Windows Jump Lists are supported."""
        if self.platform != PlatformType.WINDOWS:
            return False
        # Jump Lists are available on Windows 7+
        return True
    
    def _check_credential_manager(self) -> bool:
        """Check if Windows Credential Manager is available."""
        if self.platform != PlatformType.WINDOWS:
            return False
        return self._check_command('cmdkey')
    
    def _check_memory_compression(self) -> bool:
        """Check if Windows 10 memory compression is available."""
        if self.platform != PlatformType.WINDOWS:
            return False
        try:
            import subprocess
            result = subprocess.run([
                'powershell', '-Command',
                'Get-Command Get-MMAgent -ErrorAction SilentlyContinue'
            ], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_hardware_acceleration(self) -> bool:
        """Check if hardware acceleration is available."""
        try:
            # Basic check for GPU presence
            if self.platform == PlatformType.WINDOWS and self.capabilities.get('wmi'):
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name and 'Microsoft' not in gpu.Name:
                        return True
        except:
            pass
        return False
    
    def _check_dark_theme_api(self) -> bool:
        """Check if Windows 10 dark theme API is available."""
        if self.platform != PlatformType.WINDOWS:
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                return True
        except:
            return False
    
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.platform == PlatformType.WINDOWS
    
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.platform == PlatformType.MACOS
    
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.platform == PlatformType.LINUX
    
    def has_capability(self, capability: str) -> bool:
        """Check if platform has a specific capability."""
        return self.capabilities.get(capability, False)
    
    def get_info(self) -> Dict:
        """Get complete platform information."""
        return {
            'platform': self.platform.value,
            'architecture': self.architecture.value,
            'system_name': self.system_name,
            'system_version': self.system_version,
            'system_release': self.system_release,
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            'python_executable': self.python_executable,
            'capabilities': self.capabilities
        }


class PathManager:
    """Cross-platform path management."""
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self._setup_base_paths()
    
    def _setup_base_paths(self):
        """Set up platform-specific base paths."""
        if self.platform_info.is_windows():
            self.user_home = Path.home()
            self.app_data = Path(os.environ.get('APPDATA', self.user_home / 'AppData' / 'Roaming'))
            self.local_app_data = Path(os.environ.get('LOCALAPPDATA', self.user_home / 'AppData' / 'Local'))
            self.temp_dir = Path(tempfile.gettempdir())
            self.program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
            
        elif self.platform_info.is_macos():
            self.user_home = Path.home()
            self.app_data = self.user_home / 'Library' / 'Application Support'
            self.local_app_data = self.app_data
            self.temp_dir = Path(tempfile.gettempdir())
            self.program_files = Path('/Applications')
            
        else:  # Linux and others
            self.user_home = Path.home()
            self.app_data = Path(os.environ.get('XDG_CONFIG_HOME', self.user_home / '.config'))
            self.local_app_data = Path(os.environ.get('XDG_DATA_HOME', self.user_home / '.local' / 'share'))
            self.temp_dir = Path(tempfile.gettempdir())
            self.program_files = Path('/usr/local/bin')
    
    def get_app_config_dir(self, app_name: str) -> Path:
        """Get application configuration directory."""
        config_dir = self.app_data / app_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_app_data_dir(self, app_name: str) -> Path:
        """Get application data directory."""
        data_dir = self.local_app_data / app_name
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_app_cache_dir(self, app_name: str) -> Path:
        """Get application cache directory."""
        if self.platform_info.is_windows():
            cache_dir = self.local_app_data / app_name / 'cache'
        elif self.platform_info.is_macos():
            cache_dir = self.user_home / 'Library' / 'Caches' / app_name
        else:  # Linux
            cache_dir = Path(os.environ.get('XDG_CACHE_HOME', self.user_home / '.cache')) / app_name
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_app_log_dir(self, app_name: str) -> Path:
        """Get application log directory."""
        if self.platform_info.is_windows():
            log_dir = self.local_app_data / app_name / 'logs'
        elif self.platform_info.is_macos():
            log_dir = self.user_home / 'Library' / 'Logs' / app_name
        else:  # Linux
            log_dir = self.local_app_data / app_name / 'logs'
        
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def get_temp_file(self, suffix: str = '', prefix: str = 'westfall_') -> Path:
        """Get a temporary file path."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.temp_dir)
        os.close(fd)  # Close the file descriptor
        return Path(path)
    
    def get_temp_dir(self, prefix: str = 'westfall_') -> Path:
        """Get a temporary directory."""
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
        return temp_dir
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize a path for the current platform."""
        path = Path(path)
        
        # Resolve relative paths
        if not path.is_absolute():
            path = Path.cwd() / path
        
        # Resolve symbolic links and relative components
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            # Handle broken symlinks or permission issues
            path = path.absolute()
        
        return path
    
    def is_path_safe(self, path: Union[str, Path], base_path: Union[str, Path] = None) -> bool:
        """Check if a path is safe (no path traversal)."""
        try:
            path_str = str(path)
            
            # Check for obvious path traversal patterns
            dangerous_patterns = ['../', '..\\', '../', '..\\\\']
            for pattern in dangerous_patterns:
                if pattern in path_str:
                    return False
            
            normalized_path = self.normalize_path(path)
            
            if base_path:
                base_path = self.normalize_path(base_path)
                # Check if the path is within the base path
                try:
                    normalized_path.relative_to(base_path)
                    return True
                except ValueError:
                    return False
            
            # Additional safety checks
            path_str = str(normalized_path)
            additional_dangerous = ['~', '$', '/etc/', '/root/', 'C:\\Windows\\']
            
            for pattern in additional_dangerous:
                if pattern in path_str:
                    return False
            
            return True
            
        except Exception:
            return False


class ProcessManager:
    """Cross-platform process management."""
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
    
    def run_command(self, command: List[str], capture_output: bool = True, 
                   timeout: int = 30, cwd: Optional[Path] = None) -> Dict:
        """Run a command with platform-specific handling."""
        try:
            # Prepare command for platform
            if self.platform_info.is_windows() and command[0].endswith('.py'):
                # Use Python executable for .py files on Windows
                command = [sys.executable] + command
            
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=cwd,
                check=False
            )
            
            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout if capture_output else '',
                'stderr': result.stderr if capture_output else '',
                'command': ' '.join(command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(command)
            }
    
    def get_process_info(self, pid: int) -> Optional[Dict]:
        """Get information about a process."""
        try:
            import psutil
            process = psutil.Process(pid)
            
            return {
                'pid': pid,
                'name': process.name(),
                'cmdline': process.cmdline(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'create_time': process.create_time()
            }
        except Exception as e:
            logger.warning(f"Failed to get process info for PID {pid}: {e}")
            return None
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process by PID."""
        try:
            import psutil
            process = psutil.Process(pid)
            
            if force:
                process.kill()
            else:
                process.terminate()
                
            return True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            return False


class NotificationManager:
    """Cross-platform notification management."""
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
    
    def show_notification(self, title: str, message: str, timeout: int = 5000) -> bool:
        """Show a system notification."""
        try:
            if self.platform_info.is_windows():
                return self._windows_notification(title, message, timeout)
            elif self.platform_info.is_macos():
                return self._macos_notification(title, message)
            else:  # Linux
                return self._linux_notification(title, message, timeout)
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False
    
    def _windows_notification(self, title: str, message: str, timeout: int) -> bool:
        """Show Windows notification with Windows 10 Action Center integration."""
        try:
            # Try using win10toast with enhanced Windows 10 features
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title, 
                    message, 
                    duration=timeout//1000,
                    icon_path=None,  # Use default app icon
                    threaded=True   # Non-blocking
                )
                return True
            except ImportError:
                pass
            
            # Enhanced PowerShell with Windows 10 Action Center
            if self.platform_info.has_capability('powershell'):
                script = f'''
                # Windows 10 Toast Notification with Action Center integration
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                
                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastGeneric">
                            <text>{title}</text>
                            <text>{message}</text>
                        </binding>
                    </visual>
                    <actions>
                        <action content="Open App" arguments="open" />
                        <action content="Dismiss" arguments="dismiss" />
                    </actions>
                </toast>
"@
                
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Westfall Assistant").Show($toast)
                '''
                
                try:
                    subprocess.run(['powershell', '-Command', script], check=False, timeout=10)
                    return True
                except subprocess.TimeoutExpired:
                    # Fallback to simple notification
                    pass
            
            # Fallback to basic system notification
            if self.platform_info.has_capability('powershell'):
                script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $notify = New-Object System.Windows.Forms.NotifyIcon
                $notify.Icon = [System.Drawing.SystemIcons]::Information
                $notify.Visible = $true
                $notify.ShowBalloonTip({timeout}, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
                '''
                subprocess.run(['powershell', '-Command', script], check=False)
                return True
                
            return False
            
        except Exception:
            return False
    
    def _macos_notification(self, title: str, message: str) -> bool:
        """Show macOS notification."""
        try:
            if self.platform_info.has_capability('osascript'):
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(['osascript', '-e', script], check=False)
                return True
            return False
        except Exception:
            return False
    
    def _linux_notification(self, title: str, message: str, timeout: int) -> bool:
        """Show Linux notification."""
        try:
            # Try notify-send
            subprocess.run([
                'notify-send', 
                '-t', str(timeout),
                title, 
                message
            ], check=False)
            return True
        except Exception:
            return False


class BusinessNotificationManager(NotificationManager):
    """Enhanced notification manager for business events."""
    
    def __init__(self, platform_info: PlatformInfo):
        super().__init__(platform_info)
        self.business_icons = {
            'revenue': '💰',
            'customer': '👥',
            'order': '📦',
            'meeting': '📅',
            'task': '✅',
            'alert': '⚠️',
            'success': '🎉',
            'warning': '⚡',
            'error': '❌',
            'info': 'ℹ️'
        }
    
    def show_business_notification(self, notification_type: str, title: str, 
                                 message: str, priority: str = 'normal') -> bool:
        """Show business-specific notification with icon and priority."""
        icon = self.business_icons.get(notification_type, 'ℹ️')
        enhanced_title = f"{icon} {title}"
        
        # Adjust timeout based on priority
        timeout_map = {
            'low': 3000,
            'normal': 5000,
            'high': 8000,
            'critical': 0  # Persistent
        }
        timeout = timeout_map.get(priority, 5000)
        
        return self.show_notification(enhanced_title, message, timeout)
    
    def show_revenue_alert(self, amount: str, change: str) -> bool:
        """Show revenue milestone notification."""
        return self.show_business_notification(
            'revenue',
            'Revenue Milestone',
            f'Monthly revenue reached {amount} ({change})',
            'high'
        )
    
    def show_customer_milestone(self, count: str, milestone: str) -> bool:
        """Show customer milestone notification."""
        return self.show_business_notification(
            'customer',
            'Customer Milestone',
            f'Reached {count} customers - {milestone} achieved!',
            'high'
        )
    
    def show_order_notification(self, customer: str, amount: str) -> bool:
        """Show new order notification."""
        return self.show_business_notification(
            'order',
            'New Order Received',
            f'Order from {customer} - {amount}',
            'normal'
        )
    
    def show_meeting_reminder(self, meeting: str, time: str) -> bool:
        """Show meeting reminder."""
        return self.show_business_notification(
            'meeting',
            'Meeting Reminder',
            f'{meeting} starts in {time}',
            'high'
        )
    
    def show_task_completion(self, task: str) -> bool:
        """Show task completion notification."""
        return self.show_business_notification(
            'task',
            'Task Completed',
            f'✓ {task}',
            'normal'
        )
    
    def show_business_alert(self, alert_type: str, message: str) -> bool:
        """Show business alert (cash flow, runway, etc.)."""
        priority = 'critical' if 'critical' in alert_type.lower() else 'high'
        return self.show_business_notification(
            'alert',
            f'Business Alert: {alert_type}',
            message,
            priority
        )


class AutoUpdateManager:
    """Cross-platform auto-update functionality."""
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.update_url = "https://updates.westfall-software.com/entrepreneur-assistant"
        self.current_version = "1.0.0"  # This should be read from app config
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available."""
        try:
            import requests
            response = requests.get(f"{self.update_url}/version-check", timeout=10)
            
            if response.status_code == 200:
                update_info = response.json()
                latest_version = update_info.get('latest_version')
                
                if self._is_newer_version(latest_version, self.current_version):
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'current_version': self.current_version,
                        'download_url': update_info.get('download_url'),
                        'release_notes': update_info.get('release_notes', []),
                        'security_update': update_info.get('security_update', False)
                    }
                else:
                    return {'update_available': False, 'latest_version': latest_version}
            
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return {'error': str(e)}
        
        return {'update_available': False}
    
    def download_update(self, download_url: str, progress_callback: Optional[Callable] = None) -> str:
        """Download update package."""
        try:
            import requests
            from urllib.parse import urlparse
            
            # Determine file extension based on platform
            if self.platform_info.is_windows():
                file_ext = '.msi'
            elif self.platform_info.is_macos():
                file_ext = '.dmg'
            else:  # Linux
                file_ext = '.deb'  # or .rpm, .AppImage based on detection
            
            filename = f"westfall-assistant-update{file_ext}"
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)
            
            with requests.get(download_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(progress)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download update: {e}")
            raise
    
    def install_update(self, update_file: str) -> bool:
        """Install downloaded update."""
        try:
            if self.platform_info.is_windows():
                return self._install_windows_update(update_file)
            elif self.platform_info.is_macos():
                return self._install_macos_update(update_file)
            else:  # Linux
                return self._install_linux_update(update_file)
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
    
    def _install_windows_update(self, msi_file: str) -> bool:
        """Install Windows MSI update."""
        try:
            # Use msiexec for silent installation
            cmd = ['msiexec', '/i', msi_file, '/quiet', '/norestart']
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_macos_update(self, dmg_file: str) -> bool:
        """Install macOS DMG update."""
        try:
            # Mount DMG and copy app
            mount_result = subprocess.run(
                ['hdiutil', 'attach', dmg_file], 
                capture_output=True, text=True
            )
            
            if mount_result.returncode == 0:
                # Extract mount point from output
                mount_point = None
                for line in mount_result.stdout.split('\n'):
                    if '/Volumes/' in line:
                        mount_point = line.split('\t')[-1].strip()
                        break
                
                if mount_point:
                    # Copy app to Applications
                    app_source = os.path.join(mount_point, 'Westfall Assistant.app')
                    app_dest = '/Applications/Westfall Assistant.app'
                    
                    if os.path.exists(app_source):
                        shutil.copytree(app_source, app_dest, dirs_exist_ok=True)
                        
                        # Unmount DMG
                        subprocess.run(['hdiutil', 'detach', mount_point], check=False)
                        return True
            
            return False
        except Exception:
            return False
    
    def _install_linux_update(self, package_file: str) -> bool:
        """Install Linux package update."""
        try:
            if package_file.endswith('.deb'):
                cmd = ['sudo', 'dpkg', '-i', package_file]
            elif package_file.endswith('.rpm'):
                cmd = ['sudo', 'rpm', '-U', package_file]
            else:
                return False
            
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings."""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except Exception:
            return False


class PlatformManager:
    """Main platform management class."""
    
    def __init__(self):
        self.info = PlatformInfo()
        self.paths = PathManager(self.info)
        self.processes = ProcessManager(self.info)
        self.notifications = NotificationManager(self.info)
        self.business_notifications = BusinessNotificationManager(self.info)
        self.auto_updater = AutoUpdateManager(self.info)
        
        logger.info(f"Platform manager initialized for {self.info.platform.value}")
    
    def show_business_notification(self, notification_type: str, title: str, 
                                 message: str, priority: str = 'normal') -> bool:
        """Show business notification using enhanced manager."""
        return self.business_notifications.show_business_notification(
            notification_type, title, message, priority
        )
    
    def check_for_app_updates(self) -> Dict[str, Any]:
        """Check for application updates."""
        return self.auto_updater.check_for_updates()
    
    def download_and_install_update(self, download_url: str, 
                                  progress_callback: Optional[Callable] = None) -> bool:
        """Download and install application update."""
        try:
            update_file = self.auto_updater.download_update(download_url, progress_callback)
            return self.auto_updater.install_update(update_file)
        except Exception as e:
            logger.error(f"Update installation failed: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information."""
        return {
            'platform': self.info.get_info(),
            'paths': {
                'user_home': str(self.paths.user_home),
                'app_data': str(self.paths.app_data),
                'temp_dir': str(self.paths.temp_dir)
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'platform': sys.platform
            }
        }
    
    def setup_application_directories(self, app_name: str) -> Dict[str, Path]:
        """Set up all application directories for the entrepreneur assistant."""
        directories = {
            'config': self.paths.get_app_config_dir(app_name),
            'data': self.paths.get_app_data_dir(app_name),
            'cache': self.paths.get_app_cache_dir(app_name),
            'logs': self.paths.get_app_log_dir(app_name)
        }
        
        # Create entrepreneur-specific directories
        data_dir = directories['data']
        directories.update({
            'tailor_packs': data_dir / 'tailor_packs',
            'tailor_packs_installed': data_dir / 'tailor_packs' / 'installed',
            'tailor_packs_cache': data_dir / 'tailor_packs' / 'cache',
            'business_data': data_dir / 'business',
            'business_reports': data_dir / 'business' / 'reports',
            'business_exports': data_dir / 'business' / 'exports',
            'templates': data_dir / 'templates',
            'backups': data_dir / 'backups'
        })
        
        # Create directories if they don't exist
        for dir_path in directories.values():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
        
        logger.info(f"Entrepreneur application directories set up for {app_name}")
        return directories
    
    def open_file_with_default_app(self, file_path: Union[str, Path]) -> bool:
        """Open a file with the default application."""
        try:
            file_path = self.paths.normalize_path(file_path)
            
            if self.info.is_windows():
                os.startfile(str(file_path))
            elif self.info.is_macos():
                subprocess.run(['open', str(file_path)], check=False)
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)], check=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to open file {file_path}: {e}")
            return False
    
    def get_available_disk_space(self, path: Union[str, Path]) -> Optional[int]:
        """Get available disk space in bytes."""
        try:
            if self.info.is_windows():
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(path)),
                    ctypes.pointer(free_bytes),
                    None,
                    None
                )
                return free_bytes.value
            else:
                stat = shutil.disk_usage(str(path))
                return stat.free
        except Exception as e:
            logger.error(f"Failed to get disk space for {path}: {e}")
            return None
    
    def get_tailor_pack_directories(self, app_name: str = "westfall-assistant") -> Dict[str, Path]:
        """Get Tailor Pack specific directories."""
        app_dirs = self.setup_application_directories(app_name)
        return {
            'packs_root': app_dirs['tailor_packs'],
            'installed': app_dirs['tailor_packs_installed'],
            'cache': app_dirs['tailor_packs_cache'],
            'temp': app_dirs['cache'] / 'pack_temp'
        }
    
    def get_business_data_directories(self, app_name: str = "westfall-assistant") -> Dict[str, Path]:
        """Get business data specific directories."""
        app_dirs = self.setup_application_directories(app_name)
        return {
            'business_root': app_dirs['business_data'],
            'reports': app_dirs['business_reports'],
            'exports': app_dirs['business_exports'],
            'templates': app_dirs['templates'],
            'backups': app_dirs['backups']
        }
    
    def ensure_tailor_pack_safety(self, pack_path: Union[str, Path]) -> bool:
        """Ensure Tailor Pack path is safe and within allowed directories."""
        try:
            tailor_dirs = self.get_tailor_pack_directories()
            normalized_path = self.paths.normalize_path(pack_path)
            
            # Check if path is within any of the allowed Tailor Pack directories
            for allowed_dir in tailor_dirs.values():
                try:
                    normalized_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue
            
            logger.warning(f"Tailor Pack path {pack_path} is outside allowed directories")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Tailor Pack path safety: {e}")
            return False


# Global platform manager instance
platform_manager = PlatformManager()


def get_platform_manager() -> PlatformManager:
    """Get the global platform manager instance."""
    return platform_manager


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform_manager.info.is_windows()


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform_manager.info.is_macos()


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform_manager.info.is_linux()


def get_app_directories(app_name: str) -> Dict[str, Path]:
    """Get application directories for the current platform."""
    return platform_manager.setup_application_directories(app_name)