"""
Vision Assistant for AI-powered screen analysis
"""

from typing import Dict, Any, List

# Optional dependencies with fallbacks
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class VisionAssistant:
    """AI-powered vision assistant for screen analysis"""
    
    def __init__(self):
        self.capabilities = [
            "Screen content analysis",
            "Error detection and troubleshooting",
            "Code review and suggestions",
            "UI/UX analysis",
            "Workflow optimization"
        ]
    
    def analyze_image(self, image: "Image.Image", context: str = "") -> Dict[str, Any]:
        """
        Analyze an image and provide AI insights
        
        Args:
            image: PIL Image to analyze
            context: Additional context about the image
            
        Returns:
            Dictionary with analysis results and suggestions
        """
        if not HAS_PIL:
            return {
                'error': 'PIL not available for image analysis',
                'suggestions': ['Install PIL with: pip install Pillow'],
                'confidence': 0.0,
                'elements_detected': [],
                'context_analysis': {}
            }
        
        # This is a placeholder for AI vision analysis
        # In a full implementation, this would integrate with vision models
        
        analysis = {
            "summary": "Screen analysis complete",
            "detected_elements": [
                "Text content",
                "UI elements", 
                "Potential code structures"
            ],
            "suggestions": [
                "Consider improving code readability",
                "Check for error messages or warnings",
                "Verify UI accessibility"
            ],
            "confidence": 0.85,
            "requires_attention": [],
            "action_items": []
        }
        
        # Add context-specific analysis
        if "error" in context.lower():
            analysis["suggestions"].insert(0, "Focus on error resolution and debugging")
            analysis["requires_attention"].append("Error detection priority")
        
        if "code" in context.lower():
            analysis["suggestions"].insert(0, "Review code for best practices and optimization")
            analysis["action_items"].append("Code quality assessment")
        
        return analysis
    
    def get_help_suggestions(self, screen_content: str, user_query: str = "") -> List[str]:
        """
        Get contextual help suggestions based on screen content
        
        Args:
            screen_content: Text content extracted from screen
            user_query: Optional user query for more targeted help
            
        Returns:
            List of helpful suggestions
        """
        suggestions = []
        
        # Analyze content for common issues
        if "error" in screen_content.lower():
            suggestions.append("🔍 I can help debug this error - describe what you were trying to do")
            suggestions.append("📝 Check the error message for specific details about what went wrong")
        
        if "exception" in screen_content.lower():
            suggestions.append("🐛 Exception detected - I can help trace the root cause")
            suggestions.append("💡 Consider adding try-catch blocks for better error handling")
        
        if any(lang in screen_content.lower() for lang in ["python", "javascript", "java", "c#"]):
            suggestions.append("💻 Code detected - I can review for improvements and best practices")
            suggestions.append("🔧 Need help with debugging or optimization?")
        
        if "404" in screen_content or "not found" in screen_content.lower():
            suggestions.append("🌐 Resource not found - check URLs and file paths")
            suggestions.append("📂 Verify that files and endpoints exist")
        
        # Add general suggestions if no specific content detected
        if not suggestions:
            suggestions.extend([
                "💬 I can help analyze what's on your screen",
                "🤖 Ask me about any errors, code, or workflow questions",
                "📊 I can provide insights on productivity and best practices"
            ])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def generate_action_plan(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Generate actionable steps based on analysis results
        
        Args:
            analysis_results: Results from image analysis
            
        Returns:
            List of actionable steps
        """
        action_plan = []
        
        if analysis_results.get("requires_attention"):
            action_plan.append("🔴 **Priority Issues:**")
            for item in analysis_results["requires_attention"]:
                action_plan.append(f"   • {item}")
        
        if analysis_results.get("suggestions"):
            action_plan.append("💡 **Recommendations:**")
            for suggestion in analysis_results["suggestions"][:3]:
                action_plan.append(f"   • {suggestion}")
        
        if analysis_results.get("action_items"):
            action_plan.append("✅ **Next Steps:**")
            for item in analysis_results["action_items"]:
                action_plan.append(f"   • {item}")
        
        # Add general guidance
        action_plan.extend([
            "",
            "🤝 **Need More Help?**",
            "   • Share more context about what you're working on",
            "   • Ask specific questions about errors or challenges",
            "   • Request code review or optimization suggestions"
        ])
        
        return action_plan