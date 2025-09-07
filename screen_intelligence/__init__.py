"""
Screen Intelligence Module for WestfallPersonalAssistant
Multi-monitor capture, analysis, and AI-powered assistance
"""

# Import the new live screen intelligence module
try:
    from .live_screen_intelligence import LiveScreenIntelligence
    LIVE_SCREEN_AVAILABLE = True
except ImportError:
    LIVE_SCREEN_AVAILABLE = False

# Try to import optional modules
try:
    from .capture.multi_monitor_capture import MultiMonitorCapture
    MULTI_MONITOR_AVAILABLE = True
except ImportError:
    MULTI_MONITOR_AVAILABLE = False

try:
    from .capture.screen_analyzer import ScreenAnalyzer
    SCREEN_ANALYZER_AVAILABLE = True
except ImportError:
    SCREEN_ANALYZER_AVAILABLE = False

try:
    from .ai_vision.vision_assistant import VisionAssistant
    VISION_ASSISTANT_AVAILABLE = True
except ImportError:
    VISION_ASSISTANT_AVAILABLE = False

__all__ = []
if LIVE_SCREEN_AVAILABLE:
    __all__.append('LiveScreenIntelligence')
if MULTI_MONITOR_AVAILABLE:
    __all__.append('MultiMonitorCapture')
if SCREEN_ANALYZER_AVAILABLE:
    __all__.append('ScreenAnalyzer')
if VISION_ASSISTANT_AVAILABLE:
    __all__.append('VisionAssistant')

__version__ = '1.0.0'