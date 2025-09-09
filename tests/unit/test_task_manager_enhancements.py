"""
Tests for enhanced task manager functionality.
"""

import unittest
import sys
import os

# Add project root to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from core.task_manager import TaskManager, get_task_manager


class TestTaskManagerEnhancements(unittest.TestCase):
    """Test cases for enhanced task manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task_manager = TaskManager()
        
    def test_schedule_recurring_task(self):
        """Test scheduling a recurring task."""
        task_data = {
            'title': 'Daily Backup',
            'description': 'Run daily backup routine',
            'priority': 'high'
        }
        
        task_id = self.task_manager.schedule_recurring(task_data, 'daily')
        
        self.assertIsNotNone(task_id)
        self.assertTrue(task_id.startswith('task_'))
        
        # Verify the task was added with recurring metadata
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task['title'], 'Daily Backup')
        
    def test_get_task_by_id_method(self):
        """Test the get_task_by_id method."""
        # Add a task first
        task_data = {'title': 'Test Task', 'description': 'Test Description'}
        task_id = self.task_manager.add_task(task_data)
        
        # Test get_task_by_id method
        task = self.task_manager.get_task_by_id(task_id)
        
        self.assertIsNotNone(task)
        self.assertEqual(task['title'], 'Test Task')
        self.assertEqual(task['description'], 'Test Description')
        
    def test_get_task_by_id_nonexistent(self):
        """Test get_task_by_id with non-existent task."""
        task = self.task_manager.get_task_by_id('nonexistent_id')
        self.assertIsNone(task)
        
    def test_existing_update_task_method(self):
        """Test that the existing update_task method still works."""
        # Add a task first
        task_data = {'title': 'Original Title', 'priority': 'low'}
        task_id = self.task_manager.add_task(task_data)
        
        # Update the task
        updates = {'title': 'Updated Title', 'priority': 'high'}
        result = self.task_manager.update_task(task_id, updates)
        
        self.assertTrue(result)
        
        # Verify the update
        updated_task = self.task_manager.get_task(task_id)
        self.assertEqual(updated_task['title'], 'Updated Title')
        self.assertEqual(updated_task['priority'], 'high')


class TestTaskManagerSingleton(unittest.TestCase):
    """Test the task manager singleton functionality."""
    
    def test_singleton_pattern(self):
        """Test that get_task_manager returns the same instance."""
        tm1 = get_task_manager()
        tm2 = get_task_manager()
        self.assertIs(tm1, tm2)


if __name__ == '__main__':
    unittest.main()