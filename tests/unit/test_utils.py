"""
Unit tests for utility functions.
"""

import unittest
from datetime import datetime, timezone, timedelta
import sys
import os

# Add project root to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from utils.date_utils import (
    get_current_timestamp, parse_date_string, format_relative_time,
    is_business_day, format_duration
)
from utils.text_utils import (
    clean_text, truncate_text, extract_keywords, 
    camel_to_snake, snake_to_camel, format_file_size
)


class TestDateUtils(unittest.TestCase):
    """Test cases for date utility functions."""
    
    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        timestamp = get_current_timestamp()
        self.assertIsInstance(timestamp, str)
        self.assertIn('T', timestamp)  # ISO format includes T
    
    def test_parse_date_string(self):
        """Test date string parsing."""
        test_cases = [
            "2023-12-25",
            "2023-12-25 15:30:00",
            "12/25/2023",
            "25/12/2023"
        ]
        
        for date_str in test_cases:
            result = parse_date_string(date_str)
            self.assertIsInstance(result, datetime)
    
    def test_parse_invalid_date_string(self):
        """Test parsing invalid date string."""
        result = parse_date_string("invalid date")
        self.assertIsNone(result)
    
    def test_format_relative_time(self):
        """Test relative time formatting."""
        now = datetime.now(timezone.utc)
        
        # Test "just now"
        result = format_relative_time(now)
        self.assertEqual(result, "Just now")
        
        # Test "1 hour ago"
        hour_ago = now - timedelta(hours=1)
        result = format_relative_time(hour_ago)
        self.assertEqual(result, "1 hour ago")
        
        # Test "1 day ago"
        day_ago = now - timedelta(days=1)
        result = format_relative_time(day_ago)
        self.assertEqual(result, "1 day ago")
    
    def test_is_business_day(self):
        """Test business day detection."""
        # Monday (weekday 0)
        monday = datetime(2023, 12, 25)  # This is a Monday
        self.assertTrue(is_business_day(monday))
        
        # Saturday (weekday 5)
        saturday = datetime(2023, 12, 30)  # This is a Saturday
        self.assertFalse(is_business_day(saturday))
    
    def test_format_duration(self):
        """Test duration formatting."""
        self.assertEqual(format_duration(30), "30 seconds")
        self.assertEqual(format_duration(90), "1 minutes 30 seconds")
        self.assertEqual(format_duration(3600), "1 hours")
        self.assertEqual(format_duration(86400), "1 days")


class TestTextUtils(unittest.TestCase):
    """Test cases for text utility functions."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Hello   world  \n\t  "
        cleaned = clean_text(dirty_text)
        self.assertEqual(cleaned, "Hello world")
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "This is a long text that needs to be truncated"
        result = truncate_text(text, 20)
        self.assertEqual(result, "This is a long te...")
        self.assertEqual(len(result), 20)
    
    def test_truncate_text_no_truncation(self):
        """Test text truncation when text is shorter than limit."""
        text = "Short text"
        result = truncate_text(text, 20)
        self.assertEqual(result, text)
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extract_keywords(text)
        
        # Should exclude stop words like "the", "over"
        self.assertNotIn("the", keywords)
        self.assertNotIn("over", keywords)
        
        # Should include meaningful words
        self.assertIn("quick", keywords)
        self.assertIn("brown", keywords)
        self.assertIn("fox", keywords)
    
    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion."""
        self.assertEqual(camel_to_snake("camelCase"), "camel_case")
        self.assertEqual(camel_to_snake("XMLHttpRequest"), "xml_http_request")
        self.assertEqual(camel_to_snake("simple"), "simple")
    
    def test_snake_to_camel(self):
        """Test snake_case to camelCase conversion."""
        self.assertEqual(snake_to_camel("snake_case"), "snakeCase")
        self.assertEqual(snake_to_camel("xml_http_request"), "xmlHttpRequest")
        self.assertEqual(snake_to_camel("simple"), "simple")
    
    def test_format_file_size(self):
        """Test file size formatting."""
        self.assertEqual(format_file_size(0), "0 B")
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024), "1.0 GB")


if __name__ == '__main__':
    unittest.main()