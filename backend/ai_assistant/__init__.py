"""
AI Assistant module for Westfall Personal Assistant

This module provides the core AI assistant framework with floating chat interface,
context management, and cross-window capabilities.
"""

from .core.chat_interface import AIChat
from .core.context_manager import ContextManager
from .core.action_executor import ActionExecutor
from .core.response_handler import ResponseHandler
from .providers.provider_interface import AIProvider
from .providers.openai_provider import OpenAIProvider
from .providers.local_llm_provider import LocalLLMProvider

__all__ = [
    'AIChat', 'ContextManager', 'ActionExecutor', 'ResponseHandler',
    'AIProvider', 'OpenAIProvider', 'LocalLLMProvider'
]