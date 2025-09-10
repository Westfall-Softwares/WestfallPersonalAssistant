#!/usr/bin/env python3
"""
AI Chat Interface for Westfall Personal Assistant

Floating chat widget accessible from any window with context awareness.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AIChat:
    """Main AI chat interface with floating widget and cross-window context."""
    
    def __init__(self, context_manager, action_executor, response_handler, secure_storage):
        self.context_manager = context_manager
        self.action_executor = action_executor
        self.response_handler = response_handler
        self.secure_storage = secure_storage
        self.ai_provider = None
        self.current_conversation_id = None
        self.is_floating = True
        self.voice_enabled = False
        
        # Chat state
        self.message_history = []
        self.processing = False
        
    def set_ai_provider(self, provider):
        """Set the AI provider for generating responses."""
        self.ai_provider = provider
        logger.info(f"AI provider set to: {type(provider).__name__}")
    
    async def process_message(self, message: str, current_window: str = None, thinking_mode: str = "normal") -> Dict:
        """Process a chat message and return a response."""
        if self.processing:
            return {"error": "Already processing a message"}
        
        self.processing = True
        start_time = time.time()
        
        try:
            # Get current window context
            context = self.context_manager.get_context(current_window) if current_window else {}
            
            # Analyze user intent
            intent = await self.analyze_intent(message, context)
            
            # Store user message
            user_message = {
                "id": len(self.message_history) + 1,
                "type": "user",
                "content": message,
                "timestamp": datetime.now(),
                "context": context,
                "thinking_mode": thinking_mode
            }
            self.message_history.append(user_message)
            
            # Store in secure storage if conversation ID exists
            if self.current_conversation_id:
                self.secure_storage.store_conversation(
                    self.current_conversation_id,
                    "user",
                    message,
                    thinking_mode,
                    {"context": context}
                )
            
            # Process based on intent
            if intent.get("is_action"):
                # Execute action in current window
                result = await self.action_executor.execute_action(
                    intent["action"],
                    context,
                    intent.get("parameters", {})
                )
                
                response_text = f"✓ {intent['action']} completed"
                if result.get("message"):
                    response_text += f": {result['message']}"
                
                response = {
                    "content": response_text,
                    "type": "action_result",
                    "action": intent["action"],
                    "result": result
                }
            else:
                # Generate AI response with context
                response_content = await self.generate_ai_response(message, context, thinking_mode)
                response = {
                    "content": response_content,
                    "type": "ai_response"
                }
            
            # Create response message
            assistant_message = {
                "id": len(self.message_history) + 1,
                "type": "assistant",
                "content": response["content"],
                "timestamp": datetime.now(),
                "thinking_mode": thinking_mode,
                "processing_time": time.time() - start_time,
                "response_type": response["type"]
            }
            self.message_history.append(assistant_message)
            
            # Store in secure storage
            if self.current_conversation_id:
                self.secure_storage.store_conversation(
                    self.current_conversation_id,
                    "assistant",
                    response["content"],
                    thinking_mode,
                    {"processing_time": assistant_message["processing_time"]}
                )
            
            return {
                "success": True,
                "response": assistant_message,
                "intent": intent
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an error processing your message."
            }
            return error_response
        
        finally:
            self.processing = False
    
    async def analyze_intent(self, message: str, context: Dict) -> Dict:
        """Analyze user message to determine intent and extract actions."""
        # Simple keyword-based intent analysis (can be enhanced with ML)
        message_lower = message.lower()
        
        # Action keywords mapping
        action_patterns = {
            "open": ["open", "launch", "start", "run"],
            "close": ["close", "exit", "quit", "stop"],
            "search": ["search", "find", "look for"],
            "create": ["create", "new", "make", "add"],
            "delete": ["delete", "remove", "clear"],
            "save": ["save", "store", "export"],
            "screenshot": ["screenshot", "capture", "screen"],
            "email": ["email", "send email", "compose"],
            "reminder": ["remind", "reminder", "alert"],
            "schedule": ["schedule", "calendar", "meeting"],
            "password": ["password", "generate password"],
            "note": ["note", "write down", "remember"]
        }
        
        # Check for action keywords
        for action, keywords in action_patterns.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return {
                        "is_action": True,
                        "action": action,
                        "parameters": self._extract_parameters(message, action),
                        "confidence": 0.8
                    }
        
        # Check for questions or requests for information
        question_words = ["what", "how", "why", "when", "where", "who", "can you", "please"]
        if any(word in message_lower for word in question_words):
            return {
                "is_action": False,
                "intent": "question",
                "confidence": 0.7
            }
        
        # Default to conversation
        return {
            "is_action": False,
            "intent": "conversation",
            "confidence": 0.5
        }
    
    def _extract_parameters(self, message: str, action: str) -> Dict:
        """Extract parameters for actions from the message."""
        parameters = {}
        
        # Basic parameter extraction (can be enhanced)
        if action == "open":
            # Look for application names or file extensions
            words = message.lower().split()
            for i, word in enumerate(words):
                if word in ["browser", "chrome", "firefox"]:
                    parameters["app"] = "browser"
                elif word in ["notepad", "editor", "text"]:
                    parameters["app"] = "editor"
                elif word.endswith((".txt", ".doc", ".pdf")):
                    parameters["file"] = word
        
        elif action == "search":
            # Extract search terms after "search for" or "find"
            search_phrases = ["search for", "find", "look for"]
            for phrase in search_phrases:
                if phrase in message.lower():
                    start_idx = message.lower().find(phrase) + len(phrase)
                    parameters["query"] = message[start_idx:].strip()
                    break
        
        elif action == "email":
            # Extract email details
            if "to" in message.lower():
                # Simple extraction - can be enhanced
                words = message.split()
                for i, word in enumerate(words):
                    if word.lower() == "to" and i + 1 < len(words):
                        parameters["recipient"] = words[i + 1]
            
            if "about" in message.lower():
                about_idx = message.lower().find("about") + 5
                parameters["subject"] = message[about_idx:].strip()
        
        return parameters
    
    async def generate_ai_response(self, message: str, context: Dict, thinking_mode: str) -> str:
        """Generate AI response using the configured provider."""
        if not self.ai_provider:
            return "AI provider not configured. Please set up an AI provider to enable intelligent responses."
        
        try:
            # Prepare context for AI
            context_prompt = self._format_context_for_ai(context)
            
            # Generate response based on thinking mode
            response = await self.ai_provider.generate_response(
                message,
                context_prompt,
                thinking_mode,
                self.message_history[-10:]  # Last 10 messages for context
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return f"I'm having trouble generating a response right now. Error: {str(e)}"
    
    def _format_context_for_ai(self, context: Dict) -> str:
        """Format context information for AI consumption."""
        if not context:
            return ""
        
        context_parts = []
        
        if context.get("window"):
            context_parts.append(f"Current window: {context['window']}")
        
        if context.get("visible_data"):
            context_parts.append(f"Visible data: {context['visible_data']}")
        
        if context.get("available_actions"):
            context_parts.append(f"Available actions: {', '.join(context['available_actions'])}")
        
        return "\n".join(context_parts)
    
    def start_new_conversation(self, title: str = None) -> str:
        """Start a new conversation session."""
        import uuid
        
        self.current_conversation_id = str(uuid.uuid4())
        self.message_history = []
        
        if title and self.secure_storage:
            # Store conversation metadata
            self.secure_storage.store_conversation(
                self.current_conversation_id,
                "system",
                f"Conversation started: {title}",
                metadata={"title": title, "started_at": datetime.now().isoformat()}
            )
        
        logger.info(f"New conversation started: {self.current_conversation_id}")
        return self.current_conversation_id
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Get conversation history."""
        if self.current_conversation_id and self.secure_storage:
            return self.secure_storage.get_conversation_history(self.current_conversation_id, limit)
        
        return self.message_history[-limit:] if self.message_history else []
    
    def toggle_floating_mode(self):
        """Toggle floating widget mode."""
        self.is_floating = not self.is_floating
        logger.info(f"Floating mode: {'enabled' if self.is_floating else 'disabled'}")
        return self.is_floating
    
    def enable_voice_input(self, enabled: bool = True):
        """Enable or disable voice input."""
        self.voice_enabled = enabled
        logger.info(f"Voice input: {'enabled' if enabled else 'disabled'}")
    
    def get_chat_status(self) -> Dict:
        """Get current chat status and configuration."""
        return {
            "processing": self.processing,
            "conversation_id": self.current_conversation_id,
            "message_count": len(self.message_history),
            "ai_provider": type(self.ai_provider).__name__ if self.ai_provider else None,
            "floating_mode": self.is_floating,
            "voice_enabled": self.voice_enabled
        }