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
        Add a new task with input validation.

        Args:
            task: Dictionary containing task information

        Returns:
            Task ID of the created task
            
        Raises:
            ValueError: If task data is invalid
        """
        # Input validation
        if not isinstance(task, dict):
            raise ValueError("Task must be a dictionary")
        
        # Validate required fields
        title = task.get('title', '').strip()
        if not title:
            raise ValueError("Task title is required")
        
        if len(title) > 200:
            raise ValueError("Task title too long (max 200 characters)")
        
        # Validate description
        description = task.get('description', '').strip()
        if len(description) > 1000:
            raise ValueError("Task description too long (max 1000 characters)")
        
        # Validate priority
        priority = task.get('priority', 'medium').lower()
        if priority not in ['low', 'medium', 'high', 'urgent']:
            priority = 'medium'
        
        # Validate tags
        tags = task.get('tags', [])
        if not isinstance(tags, list):
            tags = []
        else:
            # Filter and validate tags
            validated_tags = []
            for tag in tags[:10]:  # Limit to 10 tags
                if isinstance(tag, str) and len(tag.strip()) > 0 and len(tag.strip()) <= 50:
                    validated_tags.append(tag.strip())
            tags = validated_tags
        
        # Validate due_date if provided
        due_date = task.get('due_date')
        if due_date is not None:
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning("Invalid due_date format, ignoring")
                    due_date = None
            elif not isinstance(due_date, datetime):
                due_date = None
        
        # Additional security validation
        try:
            from backend.security.input_validation import input_validator, ValidationError
            
            # Sanitize title and description
            try:
                title = input_validator.sanitize_string(title, max_length=200)
                description = input_validator.sanitize_string(description, max_length=1000)
                
                # Check for suspicious content
                if input_validator.contains_suspicious_patterns(title) or \
                   input_validator.contains_suspicious_patterns(description):
                    raise ValueError("Task contains potentially unsafe content")
                    
            except ValidationError as ve:
                raise ValueError(f"Invalid task data: {str(ve)}")
                
        except ImportError:
            # Fallback validation if security module not available
            import html
            title = html.escape(title)
            description = html.escape(description)
        
        try:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(datetime.now().timestamp())}"

            # Create task object with validated data
            new_task = Task(
                id=task_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                tags=tags
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

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by its ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            Task dictionary if found, None otherwise
        """
        return self.get_task(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a task with new information and input validation.

        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update

        Returns:
            True if task was updated successfully, False otherwise
            
        Raises:
            ValueError: If update data is invalid
        """
        # Input validation
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Task ID must be a non-empty string")
        
        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary")
        
        if len(updates) == 0:
            return True  # No updates to apply
        
        # Validate update fields
        validated_updates = {}
        
        # Validate title
        if 'title' in updates:
            title = str(updates['title']).strip()
            if not title:
                raise ValueError("Task title cannot be empty")
            if len(title) > 200:
                raise ValueError("Task title too long (max 200 characters)")
            validated_updates['title'] = title
        
        # Validate description
        if 'description' in updates:
            description = str(updates['description']).strip()
            if len(description) > 1000:
                raise ValueError("Task description too long (max 1000 characters)")
            validated_updates['description'] = description
        
        # Validate priority
        if 'priority' in updates:
            priority = str(updates['priority']).lower()
            if priority not in ['low', 'medium', 'high', 'urgent']:
                raise ValueError("Priority must be: low, medium, high, or urgent")
            validated_updates['priority'] = priority
        
        # Validate tags
        if 'tags' in updates:
            tags = updates['tags']
            if not isinstance(tags, list):
                raise ValueError("Tags must be a list")
            
            validated_tags = []
            for tag in tags[:10]:  # Limit to 10 tags
                if isinstance(tag, str) and len(tag.strip()) > 0 and len(tag.strip()) <= 50:
                    validated_tags.append(tag.strip())
            validated_updates['tags'] = validated_tags
        
        # Validate completed status
        if 'completed' in updates:
            if not isinstance(updates['completed'], bool):
                raise ValueError("Completed status must be a boolean")
            validated_updates['completed'] = updates['completed']
        
        # Validate due_date
        if 'due_date' in updates:
            due_date = updates['due_date']
            if due_date is not None:
                if isinstance(due_date, str):
                    try:
                        due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValueError("Invalid due_date format")
                elif not isinstance(due_date, datetime):
                    raise ValueError("due_date must be a datetime object or ISO string")
            validated_updates['due_date'] = due_date
        
        # Additional security validation
        try:
            from backend.security.input_validation import input_validator, ValidationError
            
            # Sanitize text fields
            if 'title' in validated_updates:
                try:
                    title = input_validator.sanitize_string(validated_updates['title'], max_length=200)
                    if input_validator.contains_suspicious_patterns(title):
                        raise ValueError("Task title contains potentially unsafe content")
                    validated_updates['title'] = title
                except ValidationError as ve:
                    raise ValueError(f"Invalid title: {str(ve)}")
            
            if 'description' in validated_updates:
                try:
                    description = input_validator.sanitize_string(validated_updates['description'], max_length=1000)
                    if input_validator.contains_suspicious_patterns(description):
                        raise ValueError("Task description contains potentially unsafe content")
                    validated_updates['description'] = description
                except ValidationError as ve:
                    raise ValueError(f"Invalid description: {str(ve)}")
                    
        except ImportError:
            # Fallback validation if security module not available
            import html
            if 'title' in validated_updates:
                validated_updates['title'] = html.escape(validated_updates['title'])
            if 'description' in validated_updates:
                validated_updates['description'] = html.escape(validated_updates['description'])
        
        try:
            for task in self.tasks:
                if task.id == task_id:
                    # Apply validated updates
                    for field, value in validated_updates.items():
                        if field == 'completed':
                            task.completed = value
                            if value and not task.completed_at:
                                task.completed_at = datetime.now()
                            elif not value:
                                task.completed_at = None
                        else:
                            setattr(task, field, value)

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

    def schedule_recurring(self, task: Dict[str, Any], interval: str) -> str:
        """
        Schedule a recurring task.

        Args:
            task: Dictionary containing task information
            interval: Recurrence interval (e.g., 'daily', 'weekly', 'monthly')

        Returns:
            Task ID of the created recurring task
        """
        try:
            # Add recurring metadata to the task
            task['recurring'] = True
            task['interval'] = interval
            
            # Add the task
            task_id = self.add_task(task)
            
            logger.info("Scheduled recurring task: %s with interval: %s", task_id, interval)
            return task_id
            
        except Exception as e:
            logger.error("Error scheduling recurring task: %s", e)
            raise

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search tasks by title, description, or tags with input validation.

        Args:
            query: Search query string

        Returns:
            List of matching task dictionaries
            
        Raises:
            ValueError: If query is invalid
        """
        # Input validation
        if not isinstance(query, str):
            raise ValueError("Search query must be a string")
        
        query = query.strip()
        if not query:
            raise ValueError("Search query cannot be empty")
        
        if len(query) > 200:
            raise ValueError("Search query too long (max 200 characters)")
        
        # Security validation
        try:
            from backend.security.input_validation import input_validator, ValidationError
            
            try:
                # Sanitize search query
                query = input_validator.sanitize_string(query, max_length=200)
                
                # Check for suspicious patterns (but allow search to continue)
                if input_validator.contains_suspicious_patterns(query):
                    logger.warning(f"Suspicious search query detected: {query[:50]}...")
                    # For search, we'll allow it but log the warning
                    
            except ValidationError as ve:
                raise ValueError(f"Invalid search query: {str(ve)}")
                
        except ImportError:
            # Fallback validation if security module not available
            import html
            query = html.escape(query)
        
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
