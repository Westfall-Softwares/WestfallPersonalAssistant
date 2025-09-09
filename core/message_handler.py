"""
Message Handler for Westfall Personal Assistant

Processes different types of messages and requests, routing them to appropriate handlers.
Supports text commands, file operations, system queries, and business functions.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path

from core.conversation import get_conversation_manager
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles different types of user messages and commands"""
    
    def __init__(self):
        self.conversation_manager = get_conversation_manager()
        self.settings = get_settings()
        self.command_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        self.command_handlers.update({
            'help': self._handle_help_command,
            'status': self._handle_status_command,
            'history': self._handle_history_command,
            'clear': self._handle_clear_command,
            'save': self._handle_save_command,
            'load': self._handle_load_command,
            'search': self._handle_search_command,
            'settings': self._handle_settings_command,
            'time': self._handle_time_command,
            'weather': self._handle_weather_command,
            'calc': self._handle_calculator_command,
            'file': self._handle_file_command,
            'note': self._handle_note_command,
        })
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process a user message and determine the appropriate response"""
        if not message or not message.strip():
            return "Please provide a message."
        
        message = message.strip()
        context = context or {}
        
        # Check if it's a command (starts with /)
        if message.startswith('/'):
            return self._handle_command(message[1:], context)
        
        # Check for specific patterns or intents
        intent = self._detect_intent(message)
        
        if intent:
            handler = self.command_handlers.get(intent)
            if handler:
                return handler(message, context)
        
        # Default: treat as general conversation
        return self._handle_general_message(message, context)
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """Detect user intent from message content"""
        message_lower = message.lower()
        
        # Time-related queries
        if any(word in message_lower for word in ['time', 'date', 'clock', 'when']):
            if any(word in message_lower for word in ['what', 'current', 'now']):
                return 'time'
        
        # Calculator queries
        if any(word in message_lower for word in ['calculate', 'compute', 'math', 'add', 'subtract', 'multiply', 'divide']):
            return 'calc'
        
        # File operations
        if any(word in message_lower for word in ['file', 'folder', 'directory', 'save', 'open', 'create']):
            return 'file'
        
        # Note-taking
        if any(word in message_lower for word in ['note', 'remember', 'remind', 'write down']):
            return 'note'
        
        # Weather queries
        if any(word in message_lower for word in ['weather', 'temperature', 'forecast', 'rain', 'sunny']):
            return 'weather'
        
        # Help requests
        if any(word in message_lower for word in ['help', 'how', 'what can you', 'commands']):
            return 'help'
        
        return None
    
    def _handle_command(self, command: str, context: Dict[str, Any]) -> str:
        """Handle slash commands"""
        parts = command.split()
        if not parts:
            return "Invalid command. Type /help for available commands."
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        handler = self.command_handlers.get(cmd)
        if handler:
            return handler(' '.join(args), context)
        else:
            return f"Unknown command: /{cmd}. Type /help for available commands."
    
    def _handle_help_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle help command"""
        return """
Available Commands:
  /help - Show this help message
  /status - Show system status
  /history - Show conversation history
  /clear - Clear current conversation
  /save <name> - Save current conversation
  /load <name> - Load a conversation
  /search <query> - Search conversations
  /settings - Show current settings
  /time - Show current time and date
  /calc <expression> - Calculator
  /file <operation> - File operations
  /note <text> - Take a note
  /weather [location] - Get weather information

You can also ask questions naturally without commands.
Examples:
  "What time is it?"
  "Calculate 15 * 24"
  "Take a note: Meeting at 3pm"
  "What's the weather like?"
"""
    
    def _handle_status_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle status command"""
        conv_info = self.conversation_manager.get_current_conversation_info()
        
        status = f"""
System Status:
  Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  
Conversation:
"""
        
        if conv_info:
            status += f"""  ID: {conv_info['id']}
  Title: {conv_info['title']}
  Messages: {conv_info['message_count']}
  Created: {conv_info['created_at']}
  Updated: {conv_info['updated_at']}
"""
        else:
            status += "  No active conversation"
        
        return status
    
    def _handle_history_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle history command"""
        try:
            limit = int(args) if args.isdigit() else 5
        except ValueError:
            limit = 5
        
        conversations = self.conversation_manager.list_conversations(limit)
        
        if not conversations:
            return "No conversation history found."
        
        result = f"Recent Conversations (showing {len(conversations)}):\n\n"
        
        for i, conv in enumerate(conversations, 1):
            result += f"{i}. {conv['title']}\n"
            result += f"   ID: {conv['id']}\n"
            result += f"   Messages: {conv['message_count']}\n"
            result += f"   Updated: {conv['updated_at']}\n\n"
        
        return result
    
    def _handle_clear_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle clear command"""
        self.conversation_manager.start_new_conversation("New Conversation")
        return "Started a new conversation. Previous conversation has been saved."
    
    def _handle_save_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle save command"""
        if not args:
            return "Please provide a name for the conversation. Usage: /save <name>"
        
        success = self.conversation_manager.update_conversation_title(args)
        if success:
            return f"Conversation saved as: {args}"
        else:
            return "Failed to save conversation."
    
    def _handle_load_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle load command"""
        if not args:
            return "Please provide a conversation ID. Usage: /load <conversation_id>"
        
        success = self.conversation_manager.load_conversation(args)
        if success:
            return f"Loaded conversation: {args}"
        else:
            return f"Failed to load conversation: {args}"
    
    def _handle_search_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle search command"""
        if not args:
            return "Please provide a search query. Usage: /search <query>"
        
        results = self.conversation_manager.search_conversations(args)
        
        if not results:
            return f"No conversations found matching: {args}"
        
        result = f"Search results for '{args}':\n\n"
        
        for i, conv in enumerate(results, 1):
            result += f"{i}. {conv['title']}\n"
            result += f"   ID: {conv['id']}\n"
            result += f"   Updated: {conv['updated_at']}\n\n"
        
        return result
    
    def _handle_settings_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle settings command"""
        return f"""
Current Settings:
  
Model Settings:
  Default Provider: {self.settings.models.default_provider}
  Temperature: {self.settings.models.temperature}
  Max Tokens: {self.settings.models.max_tokens}
  
Memory Settings:
  Storage Backend: {self.settings.memory.storage_backend}
  Max Conversation Length: {self.settings.memory.max_conversation_length}
  Auto Summarize: {self.settings.memory.auto_summarize_enabled}
  
Voice Settings:
  TTS Enabled: {self.settings.voice.tts_enabled}
  STT Enabled: {self.settings.voice.stt_enabled}
  
Feature Settings:
  Business Dashboard: {self.settings.features.business_dashboard_enabled}
  Extensions: {self.settings.features.extensions_enabled}
"""
    
    def _handle_time_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle time command"""
        now = datetime.now()
        return f"""
Current Date and Time:
  Date: {now.strftime('%A, %B %d, %Y')}
  Time: {now.strftime('%H:%M:%S')}
  Timezone: {now.strftime('%Z %z')}
  Unix Timestamp: {int(now.timestamp())}
"""
    
    def _handle_weather_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle weather command"""
        location = args if args else "current location"
        
        # This is a placeholder - in a real implementation, you'd integrate with a weather API
        return f"""
Weather Information for {location}:
  
Note: Weather integration not yet implemented.
To get weather information, you would need to:
1. Set up a weather API key (OpenWeatherMap, etc.)
2. Add weather service integration
3. Configure location detection

This is a placeholder response demonstrating the message handling structure.
"""
    
    def _handle_calculator_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle calculator command"""
        if not args:
            return "Please provide an expression to calculate. Example: /calc 15 * 24"
        
        try:
            # Simple and safe evaluation
            # Only allow basic mathematical operations
            allowed_chars = set('0123456789+-*/(). ')
            
            if not all(c in allowed_chars for c in args):
                return "Invalid characters in expression. Only numbers and +, -, *, /, (, ) are allowed."
            
            # Basic security check
            if any(word in args.lower() for word in ['import', 'exec', 'eval', '__']):
                return "Invalid expression."
            
            result = eval(args)
            return f"Result: {args} = {result}"
            
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error calculating expression: {e}"
    
    def _handle_file_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle file command"""
        if not args:
            return """
File Operations:
  /file list [directory] - List files
  /file info <filename> - Get file information
  /file create <filename> - Create a new file
  /file read <filename> - Read file contents (text files only)
  
Examples:
  /file list
  /file info document.txt
  /file create notes.txt
"""
        
        parts = args.split()
        if not parts:
            return "Please specify a file operation."
        
        operation = parts[0].lower()
        
        if operation == 'list':
            directory = parts[1] if len(parts) > 1 else '.'
            try:
                path = Path(directory)
                if not path.exists():
                    return f"Directory not found: {directory}"
                
                files = list(path.iterdir())
                if not files:
                    return f"Directory is empty: {directory}"
                
                result = f"Files in {directory}:\n\n"
                for file_path in sorted(files):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        result += f"📄 {file_path.name} ({size} bytes)\n"
                    elif file_path.is_dir():
                        result += f"📁 {file_path.name}/\n"
                
                return result
                
            except Exception as e:
                return f"Error listing files: {e}"
        
        elif operation == 'info':
            if len(parts) < 2:
                return "Please specify a filename."
            
            filename = parts[1]
            try:
                from utils.file_handler import get_file_info
                info = get_file_info(filename)
                
                if 'error' in info:
                    return f"Error: {info['error']}"
                
                return f"""
File Information for {filename}:
  Size: {info['size_mb']:.2f} MB ({info['size_bytes']} bytes)
  Type: {info['mime_type'] or 'Unknown'}
  Created: {info['created']}
  Modified: {info['modified']}
  Extension: {info['extension']}
"""
            except Exception as e:
                return f"Error getting file info: {e}"
        
        else:
            return f"Unknown file operation: {operation}"
    
    def _handle_note_command(self, args: str, context: Dict[str, Any]) -> str:
        """Handle note command"""
        if not args:
            return "Please provide text for the note. Example: /note Meeting at 3pm tomorrow"
        
        try:
            # Save note to conversation metadata
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            note_text = f"[{timestamp}] {args}"
            
            # Add as a special message in conversation
            self.conversation_manager.add_message(
                'system', 
                f"Note taken: {note_text}",
                {'type': 'note', 'original_text': args, 'timestamp': timestamp}
            )
            
            return f"Note saved: {note_text}"
            
        except Exception as e:
            return f"Error saving note: {e}"
    
    def _handle_general_message(self, message: str, context: Dict[str, Any]) -> str:
        """Handle general conversation messages"""
        # Add user message to conversation
        self.conversation_manager.add_message('user', message, context)
        
        # This would typically be handled by the AI model
        # For now, return a placeholder response
        return "I understand you're saying: " + message + "\n\nNote: This is a placeholder response. In the full implementation, this would be processed by the AI model for a more intelligent response."
    
    def register_handler(self, command: str, handler: Callable[[str, Dict[str, Any]], str]):
        """Register a custom command handler"""
        self.command_handlers[command] = handler
    
    def unregister_handler(self, command: str):
        """Unregister a command handler"""
        if command in self.command_handlers:
            del self.command_handlers[command]


# Singleton instance
_message_handler_instance = None

def get_message_handler() -> MessageHandler:
    """Get singleton message handler instance"""
    global _message_handler_instance
    if _message_handler_instance is None:
        _message_handler_instance = MessageHandler()
    return _message_handler_instance