"""
Task Manager Module for Westfall Personal Assistant

This module provides task management functionality including task creation,
tracking, and completion management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task with metadata."""
    id: str
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'priority': self.priority,
            'tags': self.tags
        }


class TaskManager:
    """Manages tasks for the personal assistant."""

    def __init__(self):
        """Initialize the task manager."""
        self.tasks: List[Task] = []
        self._task_counter = 0

    def add_task(self, task: Dict[str, Any]) -> str:
        """
        Add a new task.

        Args:
            task: Dictionary containing task information

        Returns:
            Task ID of the created task
        """
        try:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(datetime.now().timestamp())}"

            # Create task object
            new_task = Task(
                id=task_id,
                title=task.get('title', 'Untitled Task'),
                description=task.get('description', ''),
                due_date=task.get('due_date'),
                priority=task.get('priority', 'medium'),
                tags=task.get('tags', [])
            )

            self.tasks.append(new_task)
            logger.info("Added task: %s", task_id)

            return task_id

        except Exception as e:
            logger.error("Error adding task: %s", e)
            raise

    def get_tasks(self, completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get tasks, optionally filtered by completion status.

        Args:
            completed: If True, return only completed tasks; if False, only incomplete;
                      if None, return all tasks

        Returns:
            List of task dictionaries
        """
        try:
            filtered_tasks = self.tasks

            if completed is not None:
                filtered_tasks = [task for task in self.tasks if task.completed == completed]

            return [task.to_dict() for task in filtered_tasks]

        except Exception as e:
            logger.error("Error getting tasks: %s", e)
            return []

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            Task dictionary if found, None otherwise
        """
        try:
            for task in self.tasks:
                if task.id == task_id:
                    return task.to_dict()
            return None

        except Exception as e:
            logger.error("Error getting task %s: %s", task_id, e)
            return None

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a task with new information.

        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update

        Returns:
            True if task was updated successfully, False otherwise
        """
        try:
            for task in self.tasks:
                if task.id == task_id:
                    if 'title' in updates:
                        task.title = updates['title']
                    if 'description' in updates:
                        task.description = updates['description']
                    if 'due_date' in updates:
                        task.due_date = updates['due_date']
                    if 'priority' in updates:
                        task.priority = updates['priority']
                    if 'tags' in updates:
                        task.tags = updates['tags']
                    if 'completed' in updates:
                        task.completed = updates['completed']
                        if updates['completed'] and not task.completed_at:
                            task.completed_at = datetime.now()
                        elif not updates['completed']:
                            task.completed_at = None

                    logger.info("Updated task: %s", task_id)
                    return True

            logger.warning("Task not found for update: %s", task_id)
            return False

        except Exception as e:
            logger.error("Error updating task %s: %s", task_id, e)
            return False

    def remove_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Remove a task by ID.

        Args:
            task_id: ID of the task to remove

        Returns:
            Removed task dictionary if found, None otherwise
        """
        try:
            for i, task in enumerate(self.tasks):
                if task.id == task_id:
                    removed_task = self.tasks.pop(i)
                    logger.info("Removed task: %s", task_id)
                    return removed_task.to_dict()

            logger.warning("Task not found for removal: %s", task_id)
            return None

        except Exception as e:
            logger.error("Error removing task %s: %s", task_id, e)
            return None

    def complete_task(self, task_id: str) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: ID of the task to complete

        Returns:
            True if task was completed successfully, False otherwise
        """
        return self.update_task(task_id, {'completed': True})

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search tasks by title, description, or tags.

        Args:
            query: Search query string

        Returns:
            List of matching task dictionaries
        """
        try:
            query_lower = query.lower()
            matching_tasks = []

            for task in self.tasks:
                # Search in title, description, and tags
                if (query_lower in task.title.lower() or
                    query_lower in task.description.lower() or
                    any(query_lower in tag.lower() for tag in task.tags)):
                    matching_tasks.append(task)

            return [task.to_dict() for task in matching_tasks]

        except Exception as e:
            logger.error("Error searching tasks: %s", e)
            return []

    def get_status(self) -> Dict[str, Any]:
        """
        Get task manager status and statistics.

        Returns:
            Dictionary with task statistics
        """
        try:
            total_tasks = len(self.tasks)
            completed_tasks = len([task for task in self.tasks if task.completed])
            pending_tasks = total_tasks - completed_tasks

            # Get tasks by priority
            priority_counts = {}
            for priority in ['low', 'medium', 'high']:
                priority_counts[priority] = len([
                    task for task in self.tasks
                    if task.priority == priority and not task.completed
                ])

            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'priority_breakdown': priority_counts
            }

        except Exception as e:
            logger.error("Error getting task manager status: %s", e)
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'priority_breakdown': {'low': 0, 'medium': 0, 'high': 0}
            }


# Singleton instance
_task_manager_instance = None

def get_task_manager() -> TaskManager:
    """Get singleton task manager instance."""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
