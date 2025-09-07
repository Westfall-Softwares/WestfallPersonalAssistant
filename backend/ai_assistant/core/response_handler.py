#!/usr/bin/env python3
"""
Response Handler for Westfall Personal Assistant

Processes AI responses and formats them for different thinking modes.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Handles AI response processing and formatting for different thinking modes."""
    
    def __init__(self):
        self.response_cache = {}
        self.formatting_rules = {
            "normal": self._format_normal_response,
            "thinking": self._format_thinking_response,
            "research": self._format_research_response
        }
        
        # Response enhancement settings
        self.max_response_length = 2000
        self.enable_markdown = True
        self.enable_emojis = True
    
    def process_response(self, raw_response: str, thinking_mode: str, context: Dict = None) -> Dict[str, Any]:
        """Process and format AI response based on thinking mode."""
        try:
            # Clean and validate response
            cleaned_response = self._clean_response(raw_response)
            
            # Apply thinking mode formatting
            formatter = self.formatting_rules.get(thinking_mode, self._format_normal_response)
            formatted_response = formatter(cleaned_response, context or {})
            
            # Apply enhancements
            enhanced_response = self._enhance_response(formatted_response, thinking_mode)
            
            # Extract metadata
            metadata = self._extract_metadata(enhanced_response)
            
            return {
                "content": enhanced_response,
                "thinking_mode": thinking_mode,
                "metadata": metadata,
                "processed_at": datetime.now(),
                "word_count": len(enhanced_response.split()),
                "character_count": len(enhanced_response)
            }
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "content": raw_response,
                "thinking_mode": thinking_mode,
                "error": str(e),
                "processed_at": datetime.now()
            }
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize response text."""
        if not response:
            return "I'm having trouble generating a response right now."
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', response.strip())
        
        # Remove potential harmful content
        cleaned = self._sanitize_content(cleaned)
        
        # Ensure reasonable length
        if len(cleaned) > self.max_response_length:
            cleaned = cleaned[:self.max_response_length] + "..."
        
        return cleaned
    
    def _sanitize_content(self, content: str) -> str:
        """Remove potentially harmful content from response."""
        # Remove script tags and similar
        content = re.sub(r'<script.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<iframe.*?</iframe>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove potential file paths that could be sensitive
        content = re.sub(r'[A-Za-z]:\\[^\s]*', '[FILE_PATH]', content)
        content = re.sub(r'/[a-zA-Z0-9_./]+', '[FILE_PATH]', content)
        
        return content
    
    def _format_normal_response(self, response: str, context: Dict) -> str:
        """Format response for normal thinking mode."""
        # Simple, direct formatting
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        # Add context awareness if relevant
        window_type = context.get("window_info", {}).get("type")
        if window_type and window_type != "unknown":
            response = self._add_context_awareness(response, window_type)
        
        return response
    
    def _format_thinking_response(self, response: str, context: Dict) -> str:
        """Format response for thinking mode with reasoning process."""
        # Add thinking process structure
        thinking_response = "🤔 **Thinking Process:**\n\n"
        
        # Break down the response into reasoning steps
        steps = self._extract_reasoning_steps(response)
        
        for i, step in enumerate(steps, 1):
            thinking_response += f"{i}. {step}\n"
        
        thinking_response += "\n**Conclusion:**\n"
        thinking_response += self._extract_conclusion(response)
        
        return thinking_response
    
    def _format_research_response(self, response: str, context: Dict) -> str:
        """Format response for research grade with comprehensive analysis."""
        research_response = "🔬 **Research-Grade Analysis:**\n\n"
        
        # Add structured analysis sections
        sections = {
            "Overview": self._extract_overview(response),
            "Key Points": self._extract_key_points(response),
            "Analysis": self._extract_analysis(response),
            "Implications": self._extract_implications(response),
            "Recommendations": self._extract_recommendations(response)
        }
        
        for section_name, content in sections.items():
            if content:
                research_response += f"**{section_name}:**\n{content}\n\n"
        
        # Add research metadata
        research_response += "**Research Metadata:**\n"
        research_response += f"- Analysis conducted: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        research_response += f"- Context: {context.get('window_info', {}).get('type', 'General')}\n"
        research_response += f"- Confidence level: High\n"
        
        return research_response
    
    def _extract_reasoning_steps(self, response: str) -> List[str]:
        """Extract reasoning steps from response."""
        # Look for numbered lists, bullet points, or natural reasoning flow
        steps = []
        
        # Try to find explicit steps
        step_patterns = [
            r'(\d+\.?\s+[^.]+\.)',  # Numbered steps
            r'(First[^.]+\.)',      # First, Second, etc.
            r'(Second[^.]+\.)',
            r'(Third[^.]+\.)',
            r'(Next[^.]+\.)',
            r'(Then[^.]+\.)',
            r'(Finally[^.]+\.)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            steps.extend(matches)
        
        # If no explicit steps found, break into sentences
        if not steps:
            sentences = response.split('.')
            steps = [s.strip() + '.' for s in sentences[:3] if s.strip()]  # First 3 sentences
        
        return steps[:5]  # Limit to 5 steps
    
    def _extract_conclusion(self, response: str) -> str:
        """Extract conclusion from response."""
        # Look for conclusion indicators
        conclusion_patterns = [
            r'In conclusion[^.]*\.',
            r'Therefore[^.]*\.',
            r'To summarize[^.]*\.',
            r'Overall[^.]*\.'
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # If no explicit conclusion, use last sentence
        sentences = response.split('.')
        return sentences[-2] + '.' if len(sentences) > 1 else response
    
    def _extract_overview(self, response: str) -> str:
        """Extract overview for research format."""
        # First 1-2 sentences as overview
        sentences = response.split('.')
        overview = '. '.join(sentences[:2])
        return overview + '.' if overview and not overview.endswith('.') else overview
    
    def _extract_key_points(self, response: str) -> str:
        """Extract key points from response."""
        # Look for important statements
        sentences = response.split('.')
        key_points = []
        
        important_words = ['important', 'key', 'significant', 'crucial', 'essential', 'main', 'primary']
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in important_words):
                key_points.append(f"• {sentence.strip()}")
        
        # If no important sentences found, use first few sentences
        if not key_points:
            key_points = [f"• {s.strip()}" for s in sentences[:3] if s.strip()]
        
        return '\n'.join(key_points)
    
    def _extract_analysis(self, response: str) -> str:
        """Extract analysis section."""
        # Look for analytical language
        analytical_sentences = []
        sentences = response.split('.')
        
        analytical_words = ['because', 'since', 'due to', 'analysis', 'indicates', 'suggests', 'implies']
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in analytical_words):
                analytical_sentences.append(sentence.strip())
        
        return '. '.join(analytical_sentences) + '.' if analytical_sentences else "Further analysis required."
    
    def _extract_implications(self, response: str) -> str:
        """Extract implications from response."""
        # Look for forward-looking statements
        implication_words = ['will', 'would', 'could', 'might', 'may', 'likely', 'potential', 'future']
        
        sentences = response.split('.')
        implications = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in implication_words):
                implications.append(f"• {sentence.strip()}")
        
        return '\n'.join(implications) if implications else "• No immediate implications identified"
    
    def _extract_recommendations(self, response: str) -> str:
        """Extract recommendations from response."""
        # Look for action-oriented language
        recommendation_words = ['should', 'recommend', 'suggest', 'advise', 'propose', 'consider']
        
        sentences = response.split('.')
        recommendations = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in recommendation_words):
                recommendations.append(f"• {sentence.strip()}")
        
        return '\n'.join(recommendations) if recommendations else "• No specific recommendations at this time"
    
    def _add_context_awareness(self, response: str, window_type: str) -> str:
        """Add context awareness to response based on window type."""
        context_prefixes = {
            "chat_interface": "In this chat interface, ",
            "model_manager": "For model management, ",
            "screen_capture": "Regarding screen capture, ",
            "settings_panel": "In the settings, ",
            "web_browser": "For web browsing, ",
            "music_player": "For music playback, ",
            "news_reader": "Regarding news, ",
            "password_manager": "For password management, "
        }
        
        prefix = context_prefixes.get(window_type, "")
        if prefix and not response.lower().startswith(prefix.lower()):
            response = prefix + response.lower()
        
        return response
    
    def _enhance_response(self, response: str, thinking_mode: str) -> str:
        """Apply various enhancements to the response."""
        enhanced = response
        
        if self.enable_markdown:
            enhanced = self._apply_markdown_formatting(enhanced)
        
        if self.enable_emojis and thinking_mode != "research":
            enhanced = self._add_contextual_emojis(enhanced)
        
        return enhanced
    
    def _apply_markdown_formatting(self, response: str) -> str:
        """Apply markdown formatting to enhance readability."""
        # Bold important words
        important_words = ['important', 'note', 'warning', 'error', 'success', 'complete']
        for word in important_words:
            pattern = f'\\b{word}\\b'
            replacement = f'**{word}**'
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Format code or file mentions
        response = re.sub(r'`([^`]+)`', r'`\1`', response)
        
        return response
    
    def _add_contextual_emojis(self, response: str) -> str:
        """Add contextual emojis to enhance expression."""
        emoji_map = {
            r'\bsuccess\b': '✅',
            r'\berror\b': '❌',
            r'\bwarning\b': '⚠️',
            r'\binfo\b': 'ℹ️',
            r'\bidea\b': '💡',
            r'\bfile\b': '📄',
            r'\bfolder\b': '📁',
            r'\bsearch\b': '🔍',
            r'\bemail\b': '📧',
            r'\bmusic\b': '🎵',
            r'\bnews\b': '📰',
            r'\bpassword\b': '🔐'
        }
        
        for pattern, emoji in emoji_map.items():
            if not emoji in response:  # Don't duplicate emojis
                response = re.sub(pattern, f'{emoji} \\g<0>', response, flags=re.IGNORECASE)
        
        return response
    
    def _extract_metadata(self, response: str) -> Dict[str, Any]:
        """Extract metadata from processed response."""
        metadata = {
            "has_actions": bool(re.search(r'\b(open|close|create|delete|save)\b', response.lower())),
            "has_links": bool(re.search(r'https?://[^\s]+', response)),
            "has_code": bool(re.search(r'`[^`]+`', response)),
            "sentiment": self._analyze_sentiment(response),
            "topics": self._extract_topics(response),
            "complexity": self._assess_complexity(response)
        }
        
        return metadata
    
    def _analyze_sentiment(self, response: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'success', 'helpful', 'useful']
        negative_words = ['error', 'failed', 'problem', 'issue', 'wrong', 'bad']
        
        positive_count = sum(1 for word in positive_words if word in response.lower())
        negative_count = sum(1 for word in negative_words if word in response.lower())
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_topics(self, response: str) -> List[str]:
        """Extract main topics from response."""
        # Simple keyword extraction
        topic_keywords = {
            'technology': ['computer', 'software', 'program', 'system', 'code'],
            'file_management': ['file', 'folder', 'directory', 'save', 'open'],
            'communication': ['email', 'message', 'contact', 'send'],
            'security': ['password', 'secure', 'encryption', 'login'],
            'multimedia': ['music', 'video', 'image', 'audio'],
            'web': ['browser', 'website', 'url', 'internet']
        }
        
        topics = []
        response_lower = response.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _assess_complexity(self, response: str) -> str:
        """Assess response complexity."""
        word_count = len(response.split())
        sentence_count = len(response.split('.'))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        if word_count < 50 and avg_sentence_length < 10:
            return "simple"
        elif word_count < 150 and avg_sentence_length < 20:
            return "moderate"
        else:
            return "complex"
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed responses."""
        return {
            "total_responses": len(self.response_cache),
            "formatting_rules": list(self.formatting_rules.keys()),
            "enhancement_settings": {
                "max_length": self.max_response_length,
                "markdown_enabled": self.enable_markdown,
                "emojis_enabled": self.enable_emojis
            }
        }