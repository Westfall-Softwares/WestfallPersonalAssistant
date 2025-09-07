"""
Screen Intelligence Module for WestfallPersonalAssistant
Multi-monitor capture, analysis, and AI-powered assistance
"""

from .capture.multi_monitor_capture import MultiMonitorCapture
from .capture.screen_analyzer import ScreenAnalyzer
from .ai_vision.vision_assistant import VisionAssistant

__all__ = ['MultiMonitorCapture', 'ScreenAnalyzer', 'VisionAssistant']
__version__ = '1.0.0'