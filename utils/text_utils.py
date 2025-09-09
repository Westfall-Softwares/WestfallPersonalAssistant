"""
Text utility functions for the Westfall Personal Assistant.

This module provides common text processing and manipulation functions
used throughout the application.
"""

import re
import unicodedata
from typing import List, Optional, Union
import html


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and normalizing unicode.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding a suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the result
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text by removing common stop words.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum length of keywords
        
    Returns:
        List of keywords
    """
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'over', 'under', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'can', 'may', 'might', 'must', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    keywords = [
        word for word in words
        if word not in stop_words and len(word) >= min_length
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords


def highlight_text(text: str, search_term: str, tag: str = "mark") -> str:
    """
    Highlight occurrences of a search term in text with HTML tags.
    
    Args:
        text: Text to search in
        search_term: Term to highlight
        tag: HTML tag to use for highlighting
        
    Returns:
        Text with highlighted search terms
    """
    if not search_term:
        return text
    
    # Escape HTML in the text and search term
    text = html.escape(text)
    search_term = html.escape(search_term)
    
    # Create pattern that matches case-insensitively
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    
    def replace_func(match):
        return f"<{tag}>{match.group()}</{tag}>"
    
    return pattern.sub(replace_func, text)


def camel_to_snake(text: str) -> str:
    """
    Convert camelCase text to snake_case.
    
    Args:
        text: Text in camelCase
        
    Returns:
        Text in snake_case
    """
    # Insert underscore before uppercase letters (except at start)
    # Handle sequences of uppercase letters properly
    text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)
    text = re.sub('([A-Z])([A-Z][a-z])', r'\1_\2', text)
    return text.lower()


def snake_to_camel(text: str) -> str:
    """
    Convert snake_case text to camelCase.
    
    Args:
        text: Text in snake_case
        
    Returns:
        Text in camelCase
    """
    components = text.split('_')
    if not components:
        return text
    
    # Keep first component lowercase, capitalize the rest
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to extract URLs from
        
    Returns:
        List of found URLs
    """
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to extract emails from
        
    Returns:
        List of found email addresses
    """
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    return email_pattern.findall(text)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def pluralize(word: str, count: int) -> str:
    """
    Simple pluralization of English words.
    
    Args:
        word: Word to pluralize
        count: Count to determine if plural is needed
        
    Returns:
        Singular or plural form of the word
    """
    if count == 1:
        return word
    
    # Simple rules for common cases
    if word.endswith('y'):
        return word[:-1] + 'ies'
    elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word + 'es'
    else:
        return word + 's'


def mask_sensitive_data(text: str, mask_char: str = "*") -> str:
    """
    Mask sensitive data like credit card numbers, SSNs, etc.
    
    Args:
        text: Text that might contain sensitive data
        mask_char: Character to use for masking
        
    Returns:
        Text with sensitive data masked
    """
    # Mask credit card numbers (basic pattern)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                  lambda m: mask_char * len(m.group()), text)
    
    # Mask SSNs (US format)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 
                  lambda m: mask_char * len(m.group()), text)
    
    # Mask phone numbers
    text = re.sub(r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b', 
                  lambda m: mask_char * len(m.group()), text)
    
    return text