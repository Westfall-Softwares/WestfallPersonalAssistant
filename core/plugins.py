"""
Plugin Manager for Westfall Personal Assistant

This module provides plugin management functionality for extending the assistant's capabilities.
"""

import logging
import importlib
import inspect
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class Plugin:
    """Base class for assistant plugins."""
    
    def __init__(self, name: str):
        """Initialize the plugin."""
        self.name = name
        self.enabled = False
        self.version = "1.0.0"
        self.description = ""
        
    def initialize(self) -> bool:
        """Initialize the plugin. Override in subclasses."""
        self.enabled = True
        return True
        
    def shutdown(self) -> bool:
        """Shutdown the plugin. Override in subclasses."""
        self.enabled = False
        return True
        
    def get_commands(self) -> Dict[str, Callable]:
        """Get plugin commands. Override in subclasses."""
        return {}
        
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled
        }


class PluginManager:
    """Manages plugins for the personal assistant."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_commands: Dict[str, Callable] = {}
        self.plugin_directories: List[Path] = []
        
    def add_plugin_directory(self, directory: str) -> bool:
        """
        Add a directory to search for plugins.
        
        Args:
            directory: Path to the plugin directory
            
        Returns:
            True if directory was added successfully, False otherwise
        """
        try:
            plugin_dir = Path(directory)
            if plugin_dir.exists() and plugin_dir.is_dir():
                self.plugin_directories.append(plugin_dir)
                logger.info(f"Added plugin directory: {directory}")
                return True
            else:
                logger.warning(f"Plugin directory not found: {directory}")
                return False
        except Exception as e:
            logger.error(f"Error adding plugin directory: {e}")
            return False
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugin directories.
        
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        for plugin_dir in self.plugin_directories:
            try:
                for plugin_file in plugin_dir.glob("*.py"):
                    if plugin_file.name.startswith("_"):
                        continue
                        
                    plugin_name = plugin_file.stem
                    discovered.append(plugin_name)
                    logger.debug(f"Discovered plugin: {plugin_name}")
                    
            except Exception as e:
                logger.error(f"Error discovering plugins in {plugin_dir}: {e}")
                
        return discovered
    
    def load_plugin(self, plugin_name: str, plugin_path: str = None) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            plugin_path: Optional path to the plugin file
            
        Returns:
            True if plugin was loaded successfully, False otherwise
        """
        try:
            if plugin_name in self.plugins:
                logger.warning(f"Plugin already loaded: {plugin_name}")
                return True
                
            # TODO: Implement actual plugin loading from file
            # For now, create a placeholder plugin
            plugin = Plugin(plugin_name)
            plugin.description = f"Placeholder plugin: {plugin_name}"
            
            if plugin.initialize():
                self.plugins[plugin_name] = plugin
                
                # Register plugin commands
                commands = plugin.get_commands()
                for cmd_name, cmd_func in commands.items():
                    self.plugin_commands[cmd_name] = cmd_func
                    
                logger.info(f"Loaded plugin: {plugin_name}")
                return True
            else:
                logger.error(f"Failed to initialize plugin: {plugin_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if plugin was unloaded successfully, False otherwise
        """
        try:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                return False
                
            plugin = self.plugins[plugin_name]
            
            # Remove plugin commands
            commands = plugin.get_commands()
            for cmd_name in commands.keys():
                if cmd_name in self.plugin_commands:
                    del self.plugin_commands[cmd_name]
            
            # Shutdown and remove plugin
            plugin.shutdown()
            del self.plugins[plugin_name]
            
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a loaded plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a loaded plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        return False
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names."""
        return list(self.plugins.keys())
    
    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugin names."""
        return [name for name, plugin in self.plugins.items() if plugin.enabled]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin."""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_info()
        return None
    
    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded plugins."""
        return {name: plugin.get_info() for name, plugin in self.plugins.items()}
    
    def execute_plugin_command(self, command: str, *args, **kwargs) -> Any:
        """
        Execute a plugin command.
        
        Args:
            command: Command name
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            Command result or None if command not found
        """
        if command in self.plugin_commands:
            try:
                return self.plugin_commands[command](*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing plugin command {command}: {e}")
                return None
        else:
            logger.warning(f"Plugin command not found: {command}")
            return None
    
    def get_available_commands(self) -> List[str]:
        """Get list of available plugin commands."""
        return list(self.plugin_commands.keys())
    
    def shutdown_all_plugins(self) -> bool:
        """Shutdown all loaded plugins."""
        try:
            for plugin_name in list(self.plugins.keys()):
                self.unload_plugin(plugin_name)
            logger.info("All plugins shutdown")
            return True
        except Exception as e:
            logger.error(f"Error shutting down plugins: {e}")
            return False


# Singleton instance
_plugin_manager_instance = None

def get_plugin_manager() -> PluginManager:
    """Get singleton plugin manager instance."""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance