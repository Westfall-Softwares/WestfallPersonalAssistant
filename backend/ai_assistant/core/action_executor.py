#!/usr/bin/env python3
"""
Action Executor for Westfall Personal Assistant

Executes commands across windows and applications.
"""

import asyncio
import logging
import subprocess
import os
import webbrowser
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes actions across different windows and applications."""
    
    def __init__(self):
        self.action_handlers = {
            "open": self._handle_open,
            "close": self._handle_close,
            "search": self._handle_search,
            "create": self._handle_create,
            "delete": self._handle_delete,
            "save": self._handle_save,
            "screenshot": self._handle_screenshot,
            "email": self._handle_email,
            "reminder": self._handle_reminder,
            "schedule": self._handle_schedule,
            "password": self._handle_password,
            "note": self._handle_note,
            "navigate": self._handle_navigate,
            "system": self._handle_system
        }
        
        # Track action history
        self.action_history = []
        self.max_history = 100
    
    async def execute_action(self, action: str, context: Dict, parameters: Dict = None) -> Dict[str, Any]:
        """Execute an action with given parameters and context."""
        if parameters is None:
            parameters = {}
        
        try:
            logger.info(f"Executing action: {action} with parameters: {parameters}")
            
            # Check if action handler exists
            handler = self.action_handlers.get(action.lower())
            if not handler:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "message": f"Action '{action}' is not supported"
                }
            
            # Execute the action
            result = await handler(context, parameters)
            
            # Record action in history
            self._record_action(action, parameters, result, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute {action}"
            }
            self._record_action(action, parameters, error_result, context)
            return error_result
    
    async def _handle_open(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle opening applications or files."""
        target = parameters.get("app") or parameters.get("file") or parameters.get("url")
        
        if not target:
            return {"success": False, "message": "No target specified to open"}
        
        try:
            if target in ["browser", "web"]:
                url = parameters.get("url", "https://www.google.com")
                webbrowser.open(url)
                return {"success": True, "message": f"Opened browser with {url}"}
            
            elif target in ["notepad", "editor", "text"]:
                if os.name == "nt":  # Windows
                    subprocess.run(["notepad.exe"], check=False)
                else:  # Linux/Mac
                    subprocess.run(["gedit"], check=False)
                return {"success": True, "message": "Opened text editor"}
            
            elif target.startswith("http"):
                webbrowser.open(target)
                return {"success": True, "message": f"Opened URL: {target}"}
            
            elif os.path.exists(target):
                if os.name == "nt":
                    os.startfile(target)
                else:
                    subprocess.run(["xdg-open", target], check=False)
                return {"success": True, "message": f"Opened file: {target}"}
            
            else:
                # Try to run as command
                subprocess.run([target], check=False)
                return {"success": True, "message": f"Launched: {target}"}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to open {target}: {str(e)}"}
    
    async def _handle_close(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle closing applications or windows."""
        target = parameters.get("app") or parameters.get("window") or "current"
        
        # This would normally interface with the actual window management
        # For now, return a simulated response
        return {
            "success": True,
            "message": f"Close request sent for {target}",
            "action_needed": "Manual confirmation may be required"
        }
    
    async def _handle_search(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle search operations."""
        query = parameters.get("query")
        search_type = parameters.get("type", "web")
        
        if not query:
            return {"success": False, "message": "No search query provided"}
        
        try:
            if search_type == "web":
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(search_url)
                return {"success": True, "message": f"Searched web for: {query}"}
            
            elif search_type == "local":
                # Local file search - would integrate with OS search
                return {
                    "success": True,
                    "message": f"Local search initiated for: {query}",
                    "note": "Integration with file system search pending"
                }
            
            else:
                return {"success": False, "message": f"Unknown search type: {search_type}"}
                
        except Exception as e:
            return {"success": False, "message": f"Search failed: {str(e)}"}
    
    async def _handle_create(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle creation of files, notes, etc."""
        item_type = parameters.get("type", "file")
        name = parameters.get("name")
        content = parameters.get("content", "")
        
        try:
            if item_type == "file":
                if not name:
                    name = f"new_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(name, 'w') as f:
                    f.write(content)
                
                return {"success": True, "message": f"Created file: {name}"}
            
            elif item_type == "note":
                # Would integrate with notes system
                return {
                    "success": True,
                    "message": f"Note created: {name or 'Untitled'}",
                    "note": "Integration with notes system pending"
                }
            
            elif item_type == "reminder":
                # Would integrate with reminder system
                return {
                    "success": True,
                    "message": f"Reminder created: {name or 'Untitled'}",
                    "note": "Integration with reminder system pending"
                }
            
            else:
                return {"success": False, "message": f"Cannot create item of type: {item_type}"}
                
        except Exception as e:
            return {"success": False, "message": f"Creation failed: {str(e)}"}
    
    async def _handle_delete(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle deletion operations."""
        target = parameters.get("target")
        confirm = parameters.get("confirm", False)
        
        if not target:
            return {"success": False, "message": "No target specified for deletion"}
        
        if not confirm:
            return {
                "success": False,
                "message": "Deletion requires confirmation",
                "requires_confirmation": True,
                "target": target
            }
        
        try:
            if os.path.exists(target):
                os.remove(target)
                return {"success": True, "message": f"Deleted: {target}"}
            else:
                return {"success": False, "message": f"Target not found: {target}"}
                
        except Exception as e:
            return {"success": False, "message": f"Deletion failed: {str(e)}"}
    
    async def _handle_save(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle save operations."""
        target = parameters.get("target", "current_document")
        format_type = parameters.get("format", "default")
        
        # This would normally interface with the current application
        return {
            "success": True,
            "message": f"Save request sent for {target}",
            "format": format_type,
            "note": "Integration with application save functions pending"
        }
    
    async def _handle_screenshot(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle screenshot operations."""
        try:
            # This would integrate with the screen capture module
            region = parameters.get("region", "full")
            filename = parameters.get("filename")
            
            return {
                "success": True,
                "message": f"Screenshot taken ({region})",
                "filename": filename or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "note": "Integration with screen capture module pending"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Screenshot failed: {str(e)}"}
    
    async def _handle_email(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle email operations."""
        recipient = parameters.get("recipient")
        subject = parameters.get("subject", "")
        body = parameters.get("body", "")
        
        try:
            # Create mailto URL
            mailto_url = f"mailto:{recipient}?subject={subject}&body={body}"
            webbrowser.open(mailto_url)
            
            return {
                "success": True,
                "message": f"Email composer opened for {recipient}",
                "subject": subject
            }
            
        except Exception as e:
            return {"success": False, "message": f"Email composition failed: {str(e)}"}
    
    async def _handle_reminder(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle reminder creation."""
        text = parameters.get("text", "")
        when = parameters.get("when", "now")
        
        return {
            "success": True,
            "message": f"Reminder set: {text}",
            "scheduled_for": when,
            "note": "Integration with reminder system pending"
        }
    
    async def _handle_schedule(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle calendar/scheduling operations."""
        event = parameters.get("event", "")
        date = parameters.get("date", "")
        time = parameters.get("time", "")
        
        return {
            "success": True,
            "message": f"Calendar event created: {event}",
            "date": date,
            "time": time,
            "note": "Integration with calendar system pending"
        }
    
    async def _handle_password(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle password operations."""
        action = parameters.get("action", "generate")
        service = parameters.get("service", "")
        
        if action == "generate":
            import secrets
            import string
            
            length = parameters.get("length", 12)
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(chars) for _ in range(length))
            
            return {
                "success": True,
                "message": f"Password generated for {service or 'general use'}",
                "password": password,
                "length": length
            }
        
        else:
            return {
                "success": True,
                "message": f"Password {action} requested for {service}",
                "note": "Integration with password manager pending"
            }
    
    async def _handle_note(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle note-taking operations."""
        content = parameters.get("content", "")
        title = parameters.get("title", "")
        
        return {
            "success": True,
            "message": f"Note created: {title or 'Untitled'}",
            "content_length": len(content),
            "note": "Integration with notes system pending"
        }
    
    async def _handle_navigate(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle navigation operations."""
        url = parameters.get("url", "")
        
        if not url:
            return {"success": False, "message": "No URL provided"}
        
        try:
            webbrowser.open(url)
            return {"success": True, "message": f"Navigated to: {url}"}
        except Exception as e:
            return {"success": False, "message": f"Navigation failed: {str(e)}"}
    
    async def _handle_system(self, context: Dict, parameters: Dict) -> Dict[str, Any]:
        """Handle system-level operations."""
        command = parameters.get("command", "")
        
        # Only allow safe system commands
        safe_commands = ["volume", "brightness", "time", "date", "weather"]
        
        if not any(safe_cmd in command.lower() for safe_cmd in safe_commands):
            return {"success": False, "message": "System command not allowed for security"}
        
        return {
            "success": True,
            "message": f"System command processed: {command}",
            "note": "System integration pending"
        }
    
    def _record_action(self, action: str, parameters: Dict, result: Dict, context: Dict):
        """Record action in history for learning and debugging."""
        record = {
            "timestamp": datetime.now(),
            "action": action,
            "parameters": parameters,
            "result": result,
            "context_summary": {
                "window": context.get("window"),
                "window_type": context.get("window_info", {}).get("type")
            }
        }
        
        self.action_history.append(record)
        
        # Maintain history size
        if len(self.action_history) > self.max_history:
            self.action_history = self.action_history[-self.max_history:]
    
    def get_action_history(self, limit: int = 20) -> List[Dict]:
        """Get recent action history."""
        return self.action_history[-limit:]
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return list(self.action_handlers.keys())
    
    def get_action_info(self, action: str) -> Dict[str, Any]:
        """Get information about a specific action."""
        action_descriptions = {
            "open": "Open applications, files, or URLs",
            "close": "Close applications or windows",
            "search": "Search web or local files",
            "create": "Create files, notes, or reminders",
            "delete": "Delete files or items (with confirmation)",
            "save": "Save current document or data",
            "screenshot": "Take screenshots of screen or regions",
            "email": "Compose and send emails",
            "reminder": "Create reminders or alerts",
            "schedule": "Schedule calendar events",
            "password": "Generate or manage passwords",
            "note": "Create and manage notes",
            "navigate": "Navigate to web URLs",
            "system": "Execute safe system commands"
        }
        
        return {
            "action": action,
            "description": action_descriptions.get(action, "Unknown action"),
            "available": action in self.action_handlers
        }