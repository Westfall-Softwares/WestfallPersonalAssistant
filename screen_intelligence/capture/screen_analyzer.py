import numpy as np
from PIL import Image
import re
from typing import List, Dict, Tuple

# Optional dependencies with fallbacks
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

class ScreenAnalyzer:
    def __init__(self):
        self.code_patterns = {
            'python': r'(def |class |import |from |if |for |while |try:|except:)',
            'javascript': r'(function |const |let |var |=>|console\.|document\.)',
            'java': r'(public class |private |protected |static void |System\.out)',
            'csharp': r'(public class |private |namespace |using |void |string )',
            'sql': r'(SELECT |FROM |WHERE |INSERT |UPDATE |DELETE |CREATE TABLE)',
            'html': r'(<html|<div|<span|<body|<head|<script|<style)',
            'css': r'(\{[\s\S]*?:[\s\S]*?;[\s\S]*?\}|\.[\w-]+\s*\{|#[\w-]+\s*\{)'
        }
        
        self.ide_patterns = {
            'vscode': ['Visual Studio Code', 'VS Code', '.vscode'],
            'pycharm': ['PyCharm', 'JetBrains'],
            'visual_studio': ['Visual Studio', 'Microsoft Visual'],
            'sublime': ['Sublime Text'],
            'atom': ['Atom Editor'],
            'intellij': ['IntelliJ IDEA'],
            'eclipse': ['Eclipse IDE'],
            'unity': ['Unity', 'Unity Editor'],
            'unreal': ['Unreal Engine', 'UE4', 'UE5']
        }
    
    def detect_code_on_screen(self, image: Image.Image) -> Dict:
        """Detect and extract code from screenshot"""
        if not HAS_PYTESSERACT:
            return {
                'languages_detected': [],
                'code_blocks': [],
                'has_code': False,
                'error': 'PyTesseract not available'
            }
        
        text = pytesseract.image_to_string(image)
        
        detected_languages = []
        code_blocks = []
        
        # Detect programming languages
        for lang, pattern in self.code_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected_languages.append(lang)
        
        # Extract potential code blocks
        lines = text.split('\n')
        code_block = []
        in_code = False
        
        for line in lines:
            # Simple heuristic: lines with indentation are likely code
            if line.startswith(('    ', '\t')) or any(re.search(pattern, line) for pattern in self.code_patterns.values()):
                in_code = True
                code_block.append(line)
            elif in_code and line.strip() == '':
                code_block.append(line)
            elif in_code and not line.startswith(('    ', '\t')):
                if len(code_block) > 3:  # Minimum 3 lines to be considered a code block
                    code_blocks.append('\n'.join(code_block))
                code_block = []
                in_code = False
        
        # Add last block if exists
        if code_block and len(code_block) > 3:
            code_blocks.append('\n'.join(code_block))
        
        return {
            'languages_detected': detected_languages,
            'code_blocks': code_blocks,
            'has_code': len(code_blocks) > 0
        }
    
    def detect_ide(self, image: Image.Image) -> Dict:
        """Detect which IDE or editor is visible"""
        if not HAS_PYTESSERACT:
            return {
                'detected_ides': [],
                'is_development_environment': False,
                'error': 'PyTesseract not available'
            }
            
        text = pytesseract.image_to_string(image)
        
        detected_ides = []
        
        for ide, patterns in self.ide_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    detected_ides.append(ide)
                    break
        
        # Also try to detect from window title area (usually at top)
        # This would require more sophisticated image processing
        
        return {
            'detected_ides': detected_ides,
            'is_development_environment': len(detected_ides) > 0
        }
    
    def detect_ui_elements(self, image: Image.Image) -> Dict:
        """Detect UI elements like buttons, dialogs, error messages"""
        if not HAS_CV2:
            return {
                'buttons': [],
                'dialogs': [],
                'error_messages': [],
                'forms': [],
                'error': 'OpenCV not available'
            }
            
        # Convert PIL Image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        ui_elements = {
            'buttons': [],
            'dialogs': [],
            'error_messages': [],
            'forms': []
        }
        
        # Detect rectangles (potential buttons/dialogs)
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # Heuristics for UI elements
            if 2 < aspect_ratio < 5 and 20 < h < 100:  # Likely a button
                ui_elements['buttons'].append((x, y, w, h))
            elif 0.8 < aspect_ratio < 1.2 and h > 200:  # Likely a dialog
                ui_elements['dialogs'].append((x, y, w, h))
        
        # Detect error messages using color analysis (red text/backgrounds)
        hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
        
        # Red color range
        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        
        # Find red regions
        red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in red_contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Significant red area
                x, y, w, h = cv2.boundingRect(contour)
                ui_elements['error_messages'].append((x, y, w, h))
        
        return ui_elements
    
    def analyze_screen_context(self, image: Image.Image) -> Dict:
        """Comprehensive screen analysis"""
        analysis = {
            'code_analysis': self.detect_code_on_screen(image),
            'ide_detection': self.detect_ide(image),
            'ui_elements': self.detect_ui_elements(image),
            'text_content': '',
            'suggestions': []
        }
        
        # Get text content if available
        if HAS_PYTESSERACT:
            analysis['text_content'] = pytesseract.image_to_string(image)
        else:
            analysis['text_content'] = 'Text extraction requires pytesseract library'
        
        # Generate suggestions based on analysis
        if analysis['code_analysis']['has_code']:
            analysis['suggestions'].append("Code detected - I can help debug or explain it")
        
        if analysis['ide_detection']['is_development_environment']:
            analysis['suggestions'].append(f"IDE detected: {', '.join(analysis['ide_detection']['detected_ides'])}")
        
        if analysis['ui_elements'].get('error_messages'):
            analysis['suggestions'].append("Error indicators found - I can help troubleshoot")
        
        # Add dependency information
        missing_deps = []
        if not HAS_PYTESSERACT:
            missing_deps.append("pytesseract (for text extraction)")
        if not HAS_CV2:
            missing_deps.append("opencv-python (for UI element detection)")
        
        if missing_deps:
            analysis['missing_dependencies'] = missing_deps
        
        return analysis