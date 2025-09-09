#!/usr/bin/env python3
"""
Context Manager for Westfall Personal Assistant

Tracks context across windows and provides intelligent context awareness.
"""

import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages cross-window context tracking and intelligent context awareness."""
    
    def __init__(self):
        self.current_contexts = {}
        self.context_history = []
        self.window_tracking = {}
        self.last_activity = {}
        
        # Context tracking settings
        self.max_history_length = 100
        self.context_timeout = 300  # 5 minutes
        
    def get_context(self, window_identifier: str = None) -> Dict[str, Any]:
        """Get comprehensive context for a window or current system state."""
        if not window_identifier:
            window_identifier = "system"
        
        try:
            context = {
                "window": window_identifier,
                "timestamp": datetime.now(),
                "system_info": self._get_system_context(),
                "window_info": self._get_window_context(window_identifier),
                "recent_activity": self._get_recent_activity(),
                "available_actions": self._get_available_actions(window_identifier)
            }
            
            # Update tracking
            self.current_contexts[window_identifier] = context
            self.last_activity[window_identifier] = time.time()
            
            # Add to history
            self._add_to_history(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for {window_identifier}: {e}")
            return {"window": window_identifier, "error": str(e)}
    
    def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context."""
        try:
            # Get system information
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "active_processes": len(psutil.pids()),
                "uptime": time.time() - psutil.boot_time()
            }
            
            # Get network status
            try:
                network_stats = psutil.net_io_counters()
                system_info["network_active"] = network_stats.bytes_sent > 0 or network_stats.bytes_recv > 0
            except:
                system_info["network_active"] = False
            
            return system_info
            
        except Exception as e:
            logger.error(f"Error getting system context: {e}")
            return {"error": "Unable to get system context"}
    
    def _get_window_context(self, window_identifier: str) -> Dict[str, Any]:
        """Get context specific to a window."""
        window_context = {
            "identifier": window_identifier,
            "type": self._classify_window_type(window_identifier),
            "capabilities": self._get_window_capabilities(window_identifier),
            "data_summary": self._get_window_data_summary(window_identifier)
        }
        
        return window_context
    
    def _classify_window_type(self, window_identifier: str) -> str:
        """Classify the type of window based on identifier."""
        window_lower = window_identifier.lower()
        
        if "chat" in window_lower or "conversation" in window_lower:
            return "chat_interface"
        elif "model" in window_lower or "ai" in window_lower:
            return "model_manager"
        elif "screen" in window_lower or "capture" in window_lower:
            return "screen_capture"
        elif "settings" in window_lower or "config" in window_lower:
            return "settings_panel"
        elif "browser" in window_lower or "web" in window_lower:
            return "web_browser"
        elif "music" in window_lower or "audio" in window_lower:
            return "music_player"
        elif "news" in window_lower or "feed" in window_lower:
            return "news_reader"
        elif "password" in window_lower or "vault" in window_lower:
            return "password_manager"
        else:
            return "unknown"
    
    def _get_window_capabilities(self, window_identifier: str) -> List[str]:
        """Get available capabilities for a window type."""
        window_type = self._classify_window_type(window_identifier)
        
        capability_map = {
            "chat_interface": [
                "send_message", "change_thinking_mode", "start_conversation",
                "export_chat", "voice_input", "screen_analysis"
            ],
            "model_manager": [
                "load_model", "unload_model", "configure_gpu", "test_model",
                "model_info", "performance_metrics"
            ],
            "screen_capture": [
                "take_screenshot", "start_monitoring", "stop_monitoring",
                "analyze_screen", "ocr_text", "detect_errors"
            ],
            "settings_panel": [
                "update_settings", "export_settings", "import_settings",
                "reset_defaults", "backup_config"
            ],
            "web_browser": [
                "navigate_url", "bookmark_page", "search_page", "download_file",
                "manage_tabs", "clear_history"
            ],
            "music_player": [
                "play_music", "pause_music", "next_track", "previous_track",
                "create_playlist", "shuffle_mode", "volume_control"
            ],
            "news_reader": [
                "refresh_feeds", "read_article", "bookmark_article",
                "search_news", "filter_by_source", "export_articles"
            ],
            "password_manager": [
                "store_password", "retrieve_password", "generate_password",
                "delete_password", "export_vault", "security_audit"
            ],
            "unknown": ["general_assistance", "information_lookup", "task_help"]
        }
        
        return capability_map.get(window_type, ["general_assistance"])
    
    def _get_window_data_summary(self, window_identifier: str) -> Dict[str, Any]:
        """Get a summary of visible/relevant data in the window."""
        # This would be populated by the actual window/component
        # For now, return a placeholder structure
        
        window_type = self._classify_window_type(window_identifier)
        
        summary_templates = {
            "chat_interface": {
                "message_count": 0,
                "current_mode": "normal",
                "conversation_active": False
            },
            "model_manager": {
                "model_loaded": False,
                "model_name": None,
                "gpu_available": False
            },
            "screen_capture": {
                "monitoring_active": False,
                "last_capture": None,
                "errors_detected": 0
            },
            "settings_panel": {
                "sections_visible": [],
                "unsaved_changes": False
            }
        }
        
        return summary_templates.get(window_type, {"data_available": False})
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity across all tracked contexts."""
        recent_activity = []
        
        current_time = time.time()
        cutoff_time = current_time - self.context_timeout
        
        # Filter recent contexts
        for context in self.context_history[-20:]:  # Last 20 contexts
            if context.get("timestamp"):
                context_time = context["timestamp"].timestamp()
                if context_time > cutoff_time:
                    activity = {
                        "window": context.get("window"),
                        "timestamp": context["timestamp"],
                        "activity_type": "context_switch"
                    }
                    recent_activity.append(activity)
        
        return recent_activity[-10:]  # Return last 10 activities
    
    def _get_available_actions(self, window_identifier: str) -> List[str]:
        """Get currently available actions for the window."""
        capabilities = self._get_window_capabilities(window_identifier)
        
        # Filter capabilities based on current state
        # This would normally check actual window state
        available_actions = []
        
        for capability in capabilities:
            # Add basic availability logic
            if capability in ["general_assistance", "information_lookup"]:
                available_actions.append(capability)
            elif window_identifier == "system":
                # System-level actions always available
                available_actions.append(capability)
            else:
                # Assume other actions are available (would check real state)
                available_actions.append(capability)
        
        return available_actions
    
    def _add_to_history(self, context: Dict[str, Any]):
        """Add context to history with size management."""
        self.context_history.append(context)
        
        # Maintain history size
        if len(self.context_history) > self.max_history_length:
            self.context_history = self.context_history[-self.max_history_length:]
    
    def update_window_data(self, window_identifier: str, data: Dict[str, Any]):
        """Update specific window data for context tracking."""
        if window_identifier in self.current_contexts:
            if "window_info" not in self.current_contexts[window_identifier]:
                self.current_contexts[window_identifier]["window_info"] = {}
            
            self.current_contexts[window_identifier]["window_info"]["data_summary"].update(data)
            self.last_activity[window_identifier] = time.time()
            
            logger.debug(f"Updated context data for {window_identifier}")
    
    def get_context_summary(self, window_identifier: str = None) -> Dict[str, Any]:
        """Get a summary of context for a specific window or all windows."""
        if window_identifier:
            context = self.current_contexts.get(window_identifier)
            if context:
                return {
                    "window": window_identifier,
                    "last_updated": context.get("timestamp"),
                    "type": context.get("window_info", {}).get("type"),
                    "available_actions": len(context.get("available_actions", [])),
                    "has_data": bool(context.get("window_info", {}).get("data_summary"))
                }
            return {"error": "Window context not found"}
        
        # Return summary for all windows
        summary = {
            "total_windows": len(self.current_contexts),
            "active_windows": [],
            "recent_activity_count": len(self._get_recent_activity())
        }
        
        current_time = time.time()
        for window, last_time in self.last_activity.items():
            if current_time - last_time < self.context_timeout:
                summary["active_windows"].append(window)
        
        return summary
    
    def cleanup_old_contexts(self):
        """Clean up old context data to manage memory."""
        current_time = time.time()
        cutoff_time = current_time - (self.context_timeout * 2)  # 2x timeout for cleanup
        
        # Remove old contexts
        windows_to_remove = []
        for window, last_time in self.last_activity.items():
            if last_time < cutoff_time:
                windows_to_remove.append(window)
        
        for window in windows_to_remove:
            self.current_contexts.pop(window, None)
            self.last_activity.pop(window, None)
        
        # Clean history
        cutoff_datetime = datetime.now() - timedelta(seconds=self.context_timeout * 3)
        self.context_history = [
            ctx for ctx in self.context_history
            if ctx.get("timestamp", datetime.min) > cutoff_datetime
        ]
        
        if windows_to_remove:
            logger.info(f"Cleaned up contexts for {len(windows_to_remove)} inactive windows")
    
    def get_context_for_ai(self, window_identifier: str = None) -> str:
        """Get context formatted for AI consumption."""
        context = self.get_context(window_identifier)
        
        # Format context as natural language
        context_parts = []
        
        if context.get("window"):
            window_type = context.get("window_info", {}).get("type", "unknown")
            context_parts.append(f"Current window type: {window_type}")
        
        system_info = context.get("system_info", {})
        if system_info:
            context_parts.append(f"System status: CPU {system_info.get('cpu_percent', 0):.1f}%, Memory {system_info.get('memory_percent', 0):.1f}%")
        
        available_actions = context.get("available_actions", [])
        if available_actions:
            context_parts.append(f"Available actions: {', '.join(available_actions[:5])}")  # First 5 actions
        
        recent_activity = context.get("recent_activity", [])
        if recent_activity:
            context_parts.append(f"Recent activity: {len(recent_activity)} actions in the last few minutes")
        
        return ". ".join(context_parts) if context_parts else "No specific context available."