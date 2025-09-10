#!/usr/bin/env python3
"""
Windows 10 Integration Module
Integrates all Windows optimizations with the main application
"""

import os
import sys
import json
import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class WindowsIntegrationManager:
    """Manages integration of all Windows 10 optimizations"""
    
    def __init__(self):
        self.managers = {}
        self.initialized = False
        self.config = {}
        self.load_config()
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize all Windows optimization managers"""
        results = {'initialized_modules': [], 'failed_modules': [], 'warnings': []}
        
        # Try to initialize Windows optimizations
        try:
            from utils.windows_optimizations import get_windows_optimization_manager
            self.managers['windows_optimization'] = get_windows_optimization_manager()
            init_result = self.managers['windows_optimization'].initialize_optimizations()
            results['initialized_modules'].append('windows_optimization')
            results['windows_optimization'] = init_result
        except Exception as e:
            results['failed_modules'].append(f'windows_optimization: {str(e)}')
            results['warnings'].append('Windows optimization features disabled')
        
        # Try to initialize system monitoring
        try:
            from utils.windows_system_monitor import enhance_resource_manager
            enhancement_success = enhance_resource_manager()
            if enhancement_success:
                results['initialized_modules'].append('system_monitoring')
                results['system_monitoring'] = {'enhanced': True}
            else:
                results['warnings'].append('System monitoring enhancement unavailable')
        except Exception as e:
            results['failed_modules'].append(f'system_monitoring: {str(e)}')
        
        # Try to initialize task automation
        try:
            from utils.task_automation import get_productivity_manager
            self.managers['productivity'] = get_productivity_manager()
            productivity_init = self.managers['productivity'].initialize()
            results['initialized_modules'].append('task_automation')
            results['task_automation'] = productivity_init
        except Exception as e:
            results['failed_modules'].append(f'task_automation: {str(e)}')
            results['warnings'].append('Task automation features disabled')
        
        # Try to initialize local AI optimization
        try:
            from utils.local_ai_optimization import get_local_ai_manager
            self.managers['local_ai'] = get_local_ai_manager()
            ai_init = self.managers['local_ai'].initialize()
            results['initialized_modules'].append('local_ai_optimization')
            results['local_ai_optimization'] = ai_init
        except Exception as e:
            results['failed_modules'].append(f'local_ai_optimization: {str(e)}')
            results['warnings'].append('Local AI optimization features disabled')
        
        # Enhance platform compatibility
        try:
            from backend.platform_compatibility import get_platform_manager
            platform_manager = get_platform_manager()
            self.managers['platform'] = platform_manager
            results['initialized_modules'].append('platform_compatibility')
            results['platform_compatibility'] = {'enhanced': True}
        except Exception as e:
            results['failed_modules'].append(f'platform_compatibility: {str(e)}')
        
        self.initialized = len(results['initialized_modules']) > 0
        
        if self.initialized:
            logger.info(f"Windows integration initialized with {len(results['initialized_modules'])} modules")
        else:
            logger.warning("Windows integration failed to initialize any modules")
        
        return results
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all Windows optimizations"""
        status = {
            'integration_active': self.initialized,
            'modules_loaded': len(self.managers),
            'timestamp': datetime.now().isoformat()
        }
        
        # Get status from each manager
        for name, manager in self.managers.items():
            try:
                if name == 'windows_optimization':
                    status[name] = manager.get_optimization_status()
                elif name == 'productivity':
                    status[name] = manager.get_productivity_summary()
                elif name == 'local_ai':
                    status[name] = manager.get_ai_status_summary()
                elif name == 'platform':
                    status[name] = {'platform_enhanced': True}
                else:
                    status[name] = {'status': 'active'}
            except Exception as e:
                status[name] = {'error': str(e)}
        
        return status
    
    def apply_optimal_settings(self) -> Dict[str, Any]:
        """Apply optimal settings across all modules"""
        results = {'optimizations_applied': [], 'errors': []}
        
        try:
            # Windows optimization settings
            if 'windows_optimization' in self.managers:
                windows_manager = self.managers['windows_optimization']
                
                # Enable memory compression if available
                if hasattr(windows_manager, 'memory_manager'):
                    try:
                        compression_enabled = windows_manager.memory_manager.enable_memory_compression()
                        if compression_enabled:
                            results['optimizations_applied'].append('memory_compression')
                    except Exception as e:
                        results['errors'].append(f'memory_compression: {str(e)}')
                
                # Optimize power plan for performance
                if hasattr(windows_manager, 'power_manager'):
                    try:
                        power_status = windows_manager.power_manager.get_power_status()
                        current_plan = power_status.get('current_plan', '')
                        available_plans = power_status.get('available_plans', [])
                        
                        # Set to high performance if available
                        if 'High performance' in available_plans and current_plan != 'High performance':
                            if windows_manager.power_manager.set_power_plan('High performance'):
                                results['optimizations_applied'].append('high_performance_mode')
                    except Exception as e:
                        results['errors'].append(f'power_optimization: {str(e)}')
            
            # AI optimization settings
            if 'local_ai' in self.managers:
                ai_manager = self.managers['local_ai']
                
                # Record optimization as user interaction
                try:
                    ai_manager.record_user_interaction(
                        'system_optimization',
                        'Windows 10 optimization applied',
                        'System optimized for Windows 10',
                        1.0
                    )
                    results['optimizations_applied'].append('ai_personalization_updated')
                except Exception as e:
                    results['errors'].append(f'ai_personalization: {str(e)}')
            
            # Productivity optimizations
            if 'productivity' in self.managers:
                productivity_manager = self.managers['productivity']
                
                # Ensure hotkeys are registered
                try:
                    if hasattr(productivity_manager, 'quick_capture'):
                        hotkey_success = productivity_manager.quick_capture.register_hotkeys()
                        if hotkey_success:
                            results['optimizations_applied'].append('productivity_hotkeys')
                except Exception as e:
                    results['errors'].append(f'productivity_hotkeys: {str(e)}')
        
        except Exception as e:
            results['errors'].append(f'general_optimization: {str(e)}')
        
        return results
    
    def create_daily_summary(self) -> Dict[str, Any]:
        """Create daily summary of Windows optimization impact"""
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'optimizations_active': self.initialized,
            'modules_status': {},
            'recommendations': []
        }
        
        # Collect data from each module
        for name, manager in self.managers.items():
            try:
                if name == 'windows_optimization':
                    optimization_status = manager.get_optimization_status()
                    summary['modules_status'][name] = {
                        'memory_compression': optimization_status.get('memory_compression', False),
                        'hardware_acceleration': optimization_status.get('hardware_acceleration', False),
                        'theme': optimization_status.get('current_theme', 'unknown')
                    }
                    
                    # Add recommendations
                    if not optimization_status.get('memory_compression', False):
                        summary['recommendations'].append('Enable memory compression for better performance')
                    
                elif name == 'productivity':
                    productivity_summary = manager.get_productivity_summary()
                    template_count = productivity_summary.get('templates', {}).get('total_templates', 0)
                    capture_count = productivity_summary.get('captures', {}).get('total_captures', 0)
                    
                    summary['modules_status'][name] = {
                        'templates_used': template_count,
                        'captures_made': capture_count
                    }
                    
                    # Add recommendations
                    if template_count < 5:
                        summary['recommendations'].append('Create more task templates to improve productivity')
                
                elif name == 'local_ai':
                    ai_status = manager.get_ai_status_summary()
                    personalization_level = ai_status.get('personalization', {}).get('personalization_level', 0)
                    
                    summary['modules_status'][name] = {
                        'personalization_level': personalization_level,
                        'models_optimized': len(ai_status.get('model_optimizer', {}).get('cached_optimizations', {}))
                    }
                    
                    # Add recommendations
                    if personalization_level < 0.5:
                        summary['recommendations'].append('Use the AI assistant more to improve personalization')
                        
            except Exception as e:
                summary['modules_status'][name] = {'error': str(e)}
        
        return summary
    
    def shutdown(self):
        """Shutdown all Windows optimization managers"""
        for name, manager in self.managers.items():
            try:
                if hasattr(manager, 'shutdown'):
                    manager.shutdown()
                elif name == 'productivity' and hasattr(manager, 'quick_capture'):
                    manager.quick_capture.unregister_hotkeys()
            except Exception as e:
                logger.error(f"Failed to shutdown {name}: {e}")
        
        self.initialized = False
        logger.info("Windows integration managers shut down")
    
    def load_config(self):
        """Load integration configuration"""
        try:
            config_path = Path.home() / '.westfall_assistant' / 'windows_integration.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Default configuration
                self.config = {
                    'auto_optimize': True,
                    'enable_hotkeys': True,
                    'memory_compression': True,
                    'gpu_acceleration': True,
                    'daily_summaries': True
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
    
    def save_config(self):
        """Save integration configuration"""
        try:
            config_path = Path.home() / '.westfall_assistant' / 'windows_integration.json'
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration settings"""
        self.config.update(updates)
        self.save_config()


# Global instance
_integration_manager = None
_manager_lock = threading.Lock()


def get_windows_integration_manager() -> WindowsIntegrationManager:
    """Get the global Windows integration manager instance"""
    global _integration_manager
    
    if _integration_manager is None:
        with _manager_lock:
            if _integration_manager is None:
                _integration_manager = WindowsIntegrationManager()
    
    return _integration_manager


def initialize_windows_optimizations() -> Dict[str, Any]:
    """Quick function to initialize all Windows optimizations"""
    manager = get_windows_integration_manager()
    init_results = manager.initialize()
    
    # Apply optimal settings if auto-optimize is enabled
    if manager.config.get('auto_optimize', True):
        optimization_results = manager.apply_optimal_settings()
        init_results['auto_optimizations'] = optimization_results
    
    return init_results


def get_windows_optimization_summary() -> Dict[str, Any]:
    """Get comprehensive summary of Windows optimizations"""
    manager = get_windows_integration_manager()
    
    if not manager.initialized:
        return {'error': 'Windows optimizations not initialized'}
    
    return {
        'status': manager.get_comprehensive_status(),
        'daily_summary': manager.create_daily_summary(),
        'configuration': manager.config
    }


# Integration with main application
def integrate_with_main_app():
    """Integrate Windows optimizations with main application"""
    try:
        # This would be called from main.py to initialize Windows optimizations
        logger.info("Integrating Windows optimizations with main application")
        
        # Initialize optimizations
        init_results = initialize_windows_optimizations()
        
        # Log results
        initialized_count = len(init_results.get('initialized_modules', []))
        failed_count = len(init_results.get('failed_modules', []))
        
        logger.info(f"Windows integration: {initialized_count} modules initialized, {failed_count} failed")
        
        # Show warnings if any
        warnings = init_results.get('warnings', [])
        for warning in warnings:
            logger.warning(f"Windows integration: {warning}")
        
        return init_results
        
    except Exception as e:
        logger.error(f"Failed to integrate Windows optimizations: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test the integration
    print("Windows 10 Integration Test")
    print("=" * 30)
    
    # Initialize
    results = initialize_windows_optimizations()
    
    print("Initialization Results:")
    for key, value in results.items():
        if isinstance(value, list) and key.endswith('_modules'):
            print(f"  {key}: {len(value)} items")
            for item in value:
                print(f"    - {item}")
        elif isinstance(value, dict):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")
    
    # Get summary
    manager = get_windows_integration_manager()
    if manager.initialized:
        print(f"\nIntegration Status: ✅ Active ({len(manager.managers)} managers)")
        
        summary = get_windows_optimization_summary()
        print(f"Summary generated: {len(summary)} sections")
        
        # Create daily summary
        daily_summary = manager.create_daily_summary()
        print(f"\nDaily Summary:")
        print(f"  Date: {daily_summary['date']}")
        print(f"  Active modules: {len(daily_summary['modules_status'])}")
        print(f"  Recommendations: {len(daily_summary['recommendations'])}")
        
        for rec in daily_summary['recommendations'][:3]:  # Show first 3
            print(f"    - {rec}")
    else:
        print("\nIntegration Status: ❌ Not active")
    
    # Cleanup
    manager.shutdown()