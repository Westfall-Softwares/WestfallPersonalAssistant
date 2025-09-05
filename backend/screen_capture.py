"""
Screen capture and analysis module for Westfall Personal Assistant

This module provides cross-platform screen capture capabilities with OCR
and error detection features. All processing is done locally for privacy.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import time

# Screen capture dependencies (would need to be installed)
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not available. Screen capture disabled.")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: Tesseract not available. OCR disabled.")

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Some image processing features disabled.")

logger = logging.getLogger(__name__)

class ScreenCaptureEngine:
    """Handles screen capture and analysis functionality"""
    
    def __init__(self, capture_dir: str = "/tmp/westfall_captures"):
        self.capture_dir = Path(capture_dir)
        self.capture_dir.mkdir(exist_ok=True)
        self.monitoring = False
        self.last_capture = None
        
        # Error patterns for detection
        self.error_patterns = [
            "error", "exception", "failed", "crash", "abort",
            "segmentation fault", "access violation", "stack overflow",
            "null pointer", "memory error", "timeout", "connection failed"
        ]
    
    def capture_screen(self, monitor: int = 0) -> Optional[Dict[str, Any]]:
        """Capture the current screen"""
        if not PIL_AVAILABLE:
            return {
                "success": False,
                "message": "PIL not available for screen capture"
            }
        
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"capture_{timestamp}.png"
            filepath = self.capture_dir / filename
            
            # Save screenshot
            screenshot.save(filepath)
            
            self.last_capture = {
                "success": True,
                "filepath": str(filepath),
                "timestamp": timestamp,
                "size": os.path.getsize(filepath),
                "dimensions": screenshot.size
            }
            
            logger.info(f"Screen captured: {filepath}")
            return self.last_capture
            
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return {
                "success": False,
                "message": f"Capture failed: {str(e)}"
            }
    
    def extract_text(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Extract text from image using OCR"""
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            return {
                "success": False,
                "message": "OCR dependencies not available"
            }
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Get detailed data (bounding boxes, confidence)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            return {
                "success": True,
                "text": text,
                "word_count": len(text.split()),
                "confidence": self._calculate_average_confidence(data),
                "detected_words": self._extract_words_with_positions(data)
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "success": False,
                "message": f"OCR failed: {str(e)}"
            }
    
    def detect_errors(self, text: str) -> Dict[str, Any]:
        """Detect error messages in extracted text"""
        text_lower = text.lower()
        detected_errors = []
        
        for pattern in self.error_patterns:
            if pattern in text_lower:
                # Find the line containing the error
                lines = text.split('\n')
                for line_num, line in enumerate(lines):
                    if pattern in line.lower():
                        detected_errors.append({
                            "pattern": pattern,
                            "line": line.strip(),
                            "line_number": line_num + 1
                        })
        
        return {
            "has_errors": len(detected_errors) > 0,
            "error_count": len(detected_errors),
            "errors": detected_errors,
            "severity": self._assess_error_severity(detected_errors)
        }
    
    def analyze_ui_elements(self, image_path: str) -> Dict[str, Any]:
        """Analyze UI elements in the captured image"""
        if not OPENCV_AVAILABLE:
            return {
                "success": False,
                "message": "OpenCV not available for UI analysis"
            }
        
        try:
            # Load image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect buttons (rectangles)
            button_contours = self._detect_rectangles(gray)
            
            # Detect windows/dialogs
            window_contours = self._detect_windows(gray)
            
            return {
                "success": True,
                "buttons_detected": len(button_contours),
                "windows_detected": len(window_contours),
                "ui_elements": {
                    "buttons": button_contours,
                    "windows": window_contours
                }
            }
            
        except Exception as e:
            logger.error(f"UI analysis failed: {e}")
            return {
                "success": False,
                "message": f"UI analysis failed: {str(e)}"
            }
    
    def full_analysis(self, image_path: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of a captured image"""
        results = {
            "image_path": image_path,
            "timestamp": time.time()
        }
        
        # Extract text
        ocr_result = self.extract_text(image_path)
        results["ocr"] = ocr_result
        
        # Detect errors if OCR was successful
        if ocr_result.get("success") and ocr_result.get("text"):
            error_analysis = self.detect_errors(ocr_result["text"])
            results["error_detection"] = error_analysis
        
        # Analyze UI elements
        ui_analysis = self.analyze_ui_elements(image_path)
        results["ui_analysis"] = ui_analysis
        
        return results
    
    async def start_monitoring(self, interval: int = 30):
        """Start continuous screen monitoring"""
        self.monitoring = True
        logger.info(f"Starting screen monitoring with {interval}s interval")
        
        while self.monitoring:
            try:
                # Capture screen
                capture_result = self.capture_screen()
                
                if capture_result and capture_result.get("success"):
                    # Perform analysis
                    analysis = self.full_analysis(capture_result["filepath"])
                    
                    # Check for errors
                    if analysis.get("error_detection", {}).get("has_errors"):
                        logger.warning(f"Errors detected in screen capture: {analysis['error_detection']}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop continuous screen monitoring"""
        self.monitoring = False
        logger.info("Screen monitoring stopped")
    
    def cleanup_old_captures(self, max_age_hours: int = 24):
        """Clean up old capture files"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in self.capture_dir.glob("capture_*.png"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    logger.info(f"Cleaned up old capture: {file_path}")
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def _calculate_average_confidence(self, tesseract_data: dict) -> float:
        """Calculate average OCR confidence"""
        confidences = [conf for conf in tesseract_data['conf'] if conf > 0]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _extract_words_with_positions(self, tesseract_data: dict) -> List[Dict]:
        """Extract words with their positions and confidence"""
        words = []
        for i, word in enumerate(tesseract_data['text']):
            if word.strip():
                words.append({
                    "text": word,
                    "x": tesseract_data['left'][i],
                    "y": tesseract_data['top'][i],
                    "width": tesseract_data['width'][i],
                    "height": tesseract_data['height'][i],
                    "confidence": tesseract_data['conf'][i]
                })
        return words
    
    def _assess_error_severity(self, errors: List[Dict]) -> str:
        """Assess the severity of detected errors"""
        if not errors:
            return "none"
        
        critical_patterns = ["crash", "abort", "segmentation fault", "access violation"]
        high_patterns = ["exception", "error", "failed"]
        
        for error in errors:
            if any(pattern in error["pattern"] for pattern in critical_patterns):
                return "critical"
        
        for error in errors:
            if any(pattern in error["pattern"] for pattern in high_patterns):
                return "high"
        
        return "medium"
    
    def _detect_rectangles(self, gray_image):
        """Detect rectangular UI elements (buttons, etc.)"""
        # This would contain OpenCV rectangle detection logic
        # Placeholder implementation
        return []
    
    def _detect_windows(self, gray_image):
        """Detect window/dialog elements"""
        # This would contain OpenCV window detection logic
        # Placeholder implementation
        return []

# Global screen capture engine instance
screen_engine = ScreenCaptureEngine()