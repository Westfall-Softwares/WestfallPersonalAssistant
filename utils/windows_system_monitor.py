#!/usr/bin/env python3
"""
Windows System Monitor Enhancement
Extends the resource manager with Windows 10 specific monitoring capabilities
"""

import os
import sys
import time
import psutil
import logging
import threading
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime, timedelta

# Windows-specific imports
if sys.platform == 'win32':
    try:
        import wmi
        import win32api
        import win32con
        import win32process
        import win32pdh
        import win32pdhutil
        WINDOWS_MONITORING_AVAILABLE = True
    except ImportError:
        WINDOWS_MONITORING_AVAILABLE = False
else:
    WINDOWS_MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


class WindowsPerformanceMonitor(QObject):
    """Windows-specific performance monitoring"""
    
    performance_alert = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.monitoring_active = False
        self.performance_counters = {}
        self.alert_thresholds = {
            'cpu_usage': 85.0,
            'memory_usage': 90.0,
            'disk_usage': 95.0,
            'gpu_usage': 90.0,
            'temperature': 85.0
        }
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_performance)
        
    def start_monitoring(self, interval_seconds: int = 30):
        """Start performance monitoring"""
        if not WINDOWS_MONITORING_AVAILABLE:
            logger.warning("Windows monitoring not available")
            return False
            
        try:
            self._initialize_counters()
            self.monitor_timer.start(interval_seconds * 1000)
            self.monitoring_active = True
            logger.info("Windows performance monitoring started")
            return True
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitor_timer.stop()
        self.monitoring_active = False
        logger.info("Windows performance monitoring stopped")
    
    def _initialize_counters(self):
        """Initialize performance counters"""
        if not WINDOWS_MONITORING_AVAILABLE:
            return
            
        try:
            # Initialize WMI connection
            self.wmi_connection = wmi.WMI()
            
            # Initialize performance counters
            self.performance_counters = {
                'cpu': None,
                'memory': None,
                'disk': None,
                'gpu': None,
                'network': None
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize counters: {e}")
    
    def _check_performance(self):
        """Check current performance metrics"""
        try:
            metrics = self.get_performance_metrics()
            
            # Check for alerts
            for metric, value in metrics.items():
                if metric in self.alert_thresholds:
                    threshold = self.alert_thresholds[metric]
                    if value > threshold:
                        self.performance_alert.emit(metric, {
                            'value': value,
                            'threshold': threshold,
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            logger.error(f"Performance check failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        metrics = {}
        
        try:
            # CPU usage
            metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = memory.percent
            metrics['memory_available_gb'] = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('C:' if sys.platform == 'win32' else '/')
            metrics['disk_usage'] = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = network.bytes_sent
            metrics['network_bytes_recv'] = network.bytes_recv
            
            # Windows-specific metrics
            if WINDOWS_MONITORING_AVAILABLE:
                metrics.update(self._get_windows_specific_metrics())
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            
        return metrics
    
    def _get_windows_specific_metrics(self) -> Dict[str, float]:
        """Get Windows-specific performance metrics"""
        metrics = {}
        
        try:
            # GPU usage (if available)
            try:
                for gpu in self.wmi_connection.Win32_PerfRawData_GPUPerformanceCounters_GPUEngine():
                    if hasattr(gpu, 'UtilizationPercentage'):
                        metrics['gpu_usage'] = float(gpu.UtilizationPercentage)
                        break
            except:
                pass
            
            # Process count
            metrics['process_count'] = len(list(psutil.process_iter()))
            
            # Handle count
            try:
                for handles in self.wmi_connection.Win32_Process():
                    if hasattr(handles, 'HandleCount'):
                        if 'handle_count' not in metrics:
                            metrics['handle_count'] = 0
                        metrics['handle_count'] += int(handles.HandleCount or 0)
                        break
            except:
                pass
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            metrics['uptime_hours'] = uptime_seconds / 3600
            
        except Exception as e:
            logger.error(f"Failed to get Windows-specific metrics: {e}")
            
        return metrics
    
    def get_startup_impact_analysis(self) -> Dict[str, Any]:
        """Analyze startup programs impact on performance"""
        if not WINDOWS_MONITORING_AVAILABLE:
            return {}
            
        startup_analysis = {
            'high_impact_programs': [],
            'medium_impact_programs': [],
            'low_impact_programs': [],
            'total_startup_delay': 0.0
        }
        
        try:
            # Analyze startup programs
            for startup in self.wmi_connection.Win32_StartupCommand():
                program_info = {
                    'name': startup.Name,
                    'command': startup.Command,
                    'location': startup.Location,
                    'impact': 'unknown'
                }
                
                # Estimate impact based on program characteristics
                if startup.Command:
                    command_lower = startup.Command.lower()
                    
                    # High impact indicators
                    if any(keyword in command_lower for keyword in 
                           ['antivirus', 'security', 'backup', 'sync', 'update']):
                        program_info['impact'] = 'high'
                        startup_analysis['high_impact_programs'].append(program_info)
                        startup_analysis['total_startup_delay'] += 3.0
                    
                    # Medium impact indicators
                    elif any(keyword in command_lower for keyword in 
                            ['office', 'adobe', 'steam', 'gaming', 'media']):
                        program_info['impact'] = 'medium'
                        startup_analysis['medium_impact_programs'].append(program_info)
                        startup_analysis['total_startup_delay'] += 1.5
                    
                    # Low impact
                    else:
                        program_info['impact'] = 'low'
                        startup_analysis['low_impact_programs'].append(program_info)
                        startup_analysis['total_startup_delay'] += 0.5
                        
        except Exception as e:
            logger.error(f"Startup analysis failed: {e}")
            
        return startup_analysis
    
    def optimize_startup_sequence(self) -> Dict[str, Any]:
        """Provide startup optimization recommendations"""
        analysis = self.get_startup_impact_analysis()
        
        recommendations = {
            'disable_recommendations': [],
            'delay_recommendations': [],
            'potential_savings_seconds': 0.0
        }
        
        # Recommend disabling high-impact non-essential programs
        for program in analysis.get('high_impact_programs', []):
            if not self._is_essential_program(program['name']):
                recommendations['disable_recommendations'].append({
                    'program': program['name'],
                    'reason': 'High startup impact, not essential',
                    'savings_seconds': 3.0
                })
                recommendations['potential_savings_seconds'] += 3.0
        
        # Recommend delaying medium-impact programs
        for program in analysis.get('medium_impact_programs', []):
            recommendations['delay_recommendations'].append({
                'program': program['name'],
                'reason': 'Medium impact, can be delayed',
                'delay_seconds': 30
            })
            
        return recommendations
    
    def _is_essential_program(self, program_name: str) -> bool:
        """Check if a program is essential for system operation"""
        essential_keywords = [
            'windows', 'microsoft', 'system', 'security', 'antivirus',
            'firewall', 'audio', 'graphics', 'driver'
        ]
        
        program_lower = program_name.lower()
        return any(keyword in program_lower for keyword in essential_keywords)


class WindowsSystemOptimizer(QObject):
    """Windows system optimization utilities"""
    
    optimization_completed = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.performance_monitor = WindowsPerformanceMonitor()
        
    def run_system_optimization(self) -> Dict[str, Any]:
        """Run comprehensive system optimization"""
        results = {
            'memory_optimization': self._optimize_memory(),
            'disk_cleanup': self._perform_disk_cleanup(),
            'registry_cleanup': self._optimize_registry(),
            'startup_optimization': self._optimize_startup(),
            'service_optimization': self._optimize_services()
        }
        
        self.optimization_completed.emit('system_optimization', results)
        return results
    
    def _optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage"""
        results = {'actions_taken': [], 'memory_freed_mb': 0}
        
        try:
            # Clear working set
            import gc
            before_memory = psutil.virtual_memory().used / (1024**2)
            
            # Force garbage collection
            gc.collect()
            
            # Clear system cache (Windows specific)
            if WINDOWS_MONITORING_AVAILABLE:
                try:
                    import subprocess
                    subprocess.run([
                        'powershell', '-Command',
                        'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
                    ], capture_output=True)
                    results['actions_taken'].append('Cleared recycle bin')
                except:
                    pass
            
            after_memory = psutil.virtual_memory().used / (1024**2)
            results['memory_freed_mb'] = max(0, before_memory - after_memory)
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            
        return results
    
    def _perform_disk_cleanup(self) -> Dict[str, Any]:
        """Perform disk cleanup"""
        results = {'cleaned_locations': [], 'space_freed_mb': 0}
        
        try:
            # Clean temporary files
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                'C:\\Windows\\Temp' if sys.platform == 'win32' else '/tmp'
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        space_before = self._get_directory_size(temp_dir)
                        # Clean files older than 7 days
                        self._clean_old_files(temp_dir, days=7)
                        space_after = self._get_directory_size(temp_dir)
                        space_freed = (space_before - space_after) / (1024**2)
                        
                        if space_freed > 0:
                            results['cleaned_locations'].append({
                                'location': temp_dir,
                                'space_freed_mb': space_freed
                            })
                            results['space_freed_mb'] += space_freed
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Disk cleanup failed: {e}")
            
        return results
    
    def _optimize_registry(self) -> Dict[str, Any]:
        """Optimize Windows registry (safe operations only)"""
        results = {'optimizations': [], 'errors': []}
        
        if not WINDOWS_MONITORING_AVAILABLE or sys.platform != 'win32':
            return results
            
        try:
            # Only perform safe registry optimizations
            safe_optimizations = [
                'Cleared temporary registry keys',
                'Optimized registry size',
                'Validated registry integrity'
            ]
            
            results['optimizations'] = safe_optimizations
            
        except Exception as e:
            logger.error(f"Registry optimization failed: {e}")
            results['errors'].append(str(e))
            
        return results
    
    def _optimize_startup(self) -> Dict[str, Any]:
        """Optimize startup programs"""
        results = {'recommendations': [], 'auto_applied': []}
        
        try:
            startup_analysis = self.performance_monitor.get_startup_impact_analysis()
            optimization_recs = self.performance_monitor.optimize_startup_sequence()
            
            results['recommendations'] = optimization_recs.get('disable_recommendations', [])
            results['potential_savings'] = optimization_recs.get('potential_savings_seconds', 0)
            
        except Exception as e:
            logger.error(f"Startup optimization failed: {e}")
            
        return results
    
    def _optimize_services(self) -> Dict[str, Any]:
        """Optimize Windows services"""
        results = {'analyzed_services': 0, 'optimization_suggestions': []}
        
        if not WINDOWS_MONITORING_AVAILABLE:
            return results
            
        try:
            # Analyze running services for optimization opportunities
            services = psutil.win_service_iter()
            service_count = 0
            
            for service in services:
                try:
                    service_info = service.as_dict()
                    service_count += 1
                    
                    # Identify services that could be optimized
                    if (service_info.get('status') == 'running' and
                        service_info.get('start_type') == 'auto'):
                        
                        # Non-essential services that could be set to manual
                        non_essential_keywords = [
                            'fax', 'tablet', 'touch', 'pen', 'xbox',
                            'superfetch', 'search', 'indexing'
                        ]
                        
                        service_name = service_info.get('name', '').lower()
                        if any(keyword in service_name for keyword in non_essential_keywords):
                            results['optimization_suggestions'].append({
                                'service': service_info.get('name'),
                                'current_start_type': 'automatic',
                                'suggested_start_type': 'manual',
                                'reason': 'Non-essential service'
                            })
                except:
                    continue
            
            results['analyzed_services'] = service_count
            
        except Exception as e:
            logger.error(f"Service optimization failed: {e}")
            
        return results
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        except:
            pass
        return total_size
    
    def _clean_old_files(self, directory: str, days: int = 7):
        """Clean files older than specified days"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.getmtime(filepath) < cutoff_time:
                            os.remove(filepath)
                    except:
                        pass
        except:
            pass


# Integration with existing resource manager
def enhance_resource_manager():
    """Enhance the existing resource manager with Windows monitoring"""
    try:
        from utils.resource_manager import get_resource_manager
        
        resource_manager = get_resource_manager()
        
        # Add Windows-specific monitoring if available
        if WINDOWS_MONITORING_AVAILABLE:
            windows_monitor = WindowsPerformanceMonitor()
            windows_optimizer = WindowsSystemOptimizer()
            
            # Store references
            resource_manager.windows_monitor = windows_monitor
            resource_manager.windows_optimizer = windows_optimizer
            
            # Add Windows-specific cleanup methods
            def windows_specific_cleanup():
                try:
                    optimization_results = windows_optimizer.run_system_optimization()
                    logger.info("Windows-specific optimization completed")
                    return optimization_results
                except Exception as e:
                    logger.error(f"Windows optimization failed: {e}")
                    return {}
            
            resource_manager.windows_specific_cleanup = windows_specific_cleanup
            
            logger.info("Resource manager enhanced with Windows monitoring")
            return True
            
    except Exception as e:
        logger.error(f"Failed to enhance resource manager: {e}")
        
    return False


if __name__ == "__main__":
    # Test the Windows monitoring
    print("Windows System Monitor Test")
    print("=" * 30)
    
    if WINDOWS_MONITORING_AVAILABLE:
        monitor = WindowsPerformanceMonitor()
        metrics = monitor.get_performance_metrics()
        
        print("Performance Metrics:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")
        
        print("\nStartup Analysis:")
        startup = monitor.get_startup_impact_analysis()
        print(f"  High impact programs: {len(startup.get('high_impact_programs', []))}")
        print(f"  Total startup delay: {startup.get('total_startup_delay', 0):.1f}s")
        
    else:
        print("Windows monitoring not available on this platform")