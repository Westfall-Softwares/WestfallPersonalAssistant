#!/usr/bin/env python3
"""
Windows 10 Optimization Launcher
Entry point for initializing all Windows 10 optimizations
"""

import os
import sys
import logging
from typing import Dict, Any

# Add project root to path if needed
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


def setup_windows_optimizations() -> Dict[str, Any]:
    """
    Setup and initialize all Windows 10 optimizations
    This is the main entry point for Windows optimization features
    """
    try:
        from utils.windows_integration import initialize_windows_optimizations
        
        logger.info("Initializing Windows 10 optimizations...")
        
        # Initialize all optimization modules
        results = initialize_windows_optimizations()
        
        # Log summary
        initialized = len(results.get('initialized_modules', []))
        failed = len(results.get('failed_modules', []))
        warnings = len(results.get('warnings', []))
        
        logger.info(f"Windows optimizations initialized: {initialized} modules active, {failed} failed, {warnings} warnings")
        
        # Log specific results
        if initialized > 0:
            logger.info(f"Active modules: {', '.join(results.get('initialized_modules', []))}")
        
        if failed > 0:
            logger.warning(f"Failed modules: {', '.join(results.get('failed_modules', []))}")
        
        for warning in results.get('warnings', []):
            logger.warning(f"Windows optimization warning: {warning}")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to initialize Windows optimizations: {e}")
        return {
            'initialized_modules': [],
            'failed_modules': ['all'],
            'warnings': ['Windows optimizations completely unavailable'],
            'error': str(e)
        }


def get_optimization_status() -> Dict[str, Any]:
    """Get current status of Windows optimizations"""
    try:
        from utils.windows_integration import get_windows_optimization_summary
        return get_windows_optimization_summary()
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        return {'error': str(e)}


def apply_optimal_settings() -> Dict[str, Any]:
    """Apply optimal Windows settings for best performance"""
    try:
        from utils.windows_integration import get_windows_integration_manager
        
        manager = get_windows_integration_manager()
        if not manager.initialized:
            return {'error': 'Windows optimizations not initialized'}
        
        return manager.apply_optimal_settings()
        
    except Exception as e:
        logger.error(f"Failed to apply optimal settings: {e}")
        return {'error': str(e)}


def shutdown_optimizations():
    """Shutdown Windows optimization services"""
    try:
        from utils.windows_integration import get_windows_integration_manager
        
        manager = get_windows_integration_manager()
        manager.shutdown()
        logger.info("Windows optimizations shut down successfully")
        
    except Exception as e:
        logger.error(f"Failed to shutdown optimizations: {e}")


def create_daily_report() -> Dict[str, Any]:
    """Create daily optimization report"""
    try:
        from utils.windows_integration import get_windows_integration_manager
        
        manager = get_windows_integration_manager()
        if not manager.initialized:
            return {'error': 'Windows optimizations not initialized'}
        
        return manager.create_daily_summary()
        
    except Exception as e:
        logger.error(f"Failed to create daily report: {e}")
        return {'error': str(e)}


# Integration functions for main application
def integrate_with_main_app() -> bool:
    """
    Integrate Windows optimizations with the main application
    Call this from main.py during application startup
    """
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize optimizations
        results = setup_windows_optimizations()
        
        # Check if any modules were initialized
        if len(results.get('initialized_modules', [])) > 0:
            logger.info("Windows 10 optimizations successfully integrated")
            
            # Apply optimal settings if auto-optimize is enabled
            try:
                from utils.windows_integration import get_windows_integration_manager
                manager = get_windows_integration_manager()
                
                if manager.config.get('auto_optimize', True):
                    optimization_results = apply_optimal_settings()
                    applied_count = len(optimization_results.get('optimizations_applied', []))
                    if applied_count > 0:
                        logger.info(f"Applied {applied_count} automatic optimizations")
            except:
                pass  # Non-critical
            
            return True
        else:
            logger.warning("Windows 10 optimizations integration failed")
            return False
            
    except Exception as e:
        logger.error(f"Failed to integrate Windows optimizations: {e}")
        return False


def add_to_main_menu(main_window):
    """
    Add Windows optimization options to main application menu
    Call this from main.py to add menu items
    """
    try:
        # This would integrate with the main application's menu system
        # Example implementation for PyQt5
        
        optimization_menu = main_window.menuBar().addMenu("Windows Optimizations")
        
        # Status action
        def show_status():
            status = get_optimization_status()
            # Show status dialog or window
            print("Windows Optimization Status:", status)
        
        status_action = optimization_menu.addAction("Show Status")
        status_action.triggered.connect(show_status)
        
        # Apply settings action
        def apply_settings():
            results = apply_optimal_settings()
            # Show results dialog
            print("Optimization Results:", results)
        
        settings_action = optimization_menu.addAction("Apply Optimal Settings")
        settings_action.triggered.connect(apply_settings)
        
        # Daily report action
        def show_report():
            report = create_daily_report()
            # Show report dialog or window
            print("Daily Report:", report)
        
        report_action = optimization_menu.addAction("Daily Report")
        report_action.triggered.connect(show_report)
        
        logger.info("Windows optimization menu items added")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add menu items: {e}")
        return False


def add_system_tray_options(system_tray):
    """
    Add Windows optimization options to system tray menu
    Call this to add tray menu items
    """
    try:
        # Add separator
        system_tray.addSeparator()
        
        # Quick status
        def quick_status():
            status = get_optimization_status()
            modules_active = len(status.get('status', {}).get('modules_loaded', 0))
            # Show tooltip or notification
            return f"Windows Optimizations: {modules_active} modules active"
        
        status_action = system_tray.addAction("Windows Status")
        status_action.triggered.connect(lambda: print(quick_status()))
        
        # Quick optimize
        def quick_optimize():
            results = apply_optimal_settings()
            applied = len(results.get('optimizations_applied', []))
            # Show notification
            return f"Applied {applied} optimizations"
        
        optimize_action = system_tray.addAction("Quick Optimize")
        optimize_action.triggered.connect(lambda: print(quick_optimize()))
        
        logger.info("Windows optimization tray items added")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add tray items: {e}")
        return False


# CLI interface for testing and manual operation
def main():
    """Command-line interface for Windows optimizations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Windows 10 Optimization Manager')
    parser.add_argument('--init', action='store_true', help='Initialize optimizations')
    parser.add_argument('--status', action='store_true', help='Show optimization status')
    parser.add_argument('--optimize', action='store_true', help='Apply optimal settings')
    parser.add_argument('--report', action='store_true', help='Generate daily report')
    parser.add_argument('--shutdown', action='store_true', help='Shutdown optimizations')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.test:
        print("Running Windows optimization test suite...")
        os.system(f"{sys.executable} test_windows_simplified.py")
        return
    
    if args.init:
        print("Initializing Windows optimizations...")
        results = setup_windows_optimizations()
        print(f"Results: {results}")
    
    if args.status:
        print("Getting optimization status...")
        status = get_optimization_status()
        print(f"Status: {status}")
    
    if args.optimize:
        print("Applying optimal settings...")
        results = apply_optimal_settings()
        print(f"Optimization results: {results}")
    
    if args.report:
        print("Generating daily report...")
        report = create_daily_report()
        print(f"Daily report: {report}")
    
    if args.shutdown:
        print("Shutting down optimizations...")
        shutdown_optimizations()
        print("Shutdown complete")
    
    if not any([args.init, args.status, args.optimize, args.report, args.shutdown]):
        # Default action - show help and status
        parser.print_help()
        print("\nCurrent status:")
        try:
            status = get_optimization_status()
            if 'error' in status:
                print(f"Error: {status['error']}")
            else:
                modules_active = len(status.get('status', {}).get('modules_loaded', []))
                print(f"Windows optimizations: {modules_active} modules active")
        except:
            print("Windows optimizations: Not initialized")


if __name__ == "__main__":
    main()