#!/usr/bin/env python3
"""
Windows Task Automation and Personal Productivity Module
Implements task templates, quick capture, automation recipes, and productivity analytics
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QHotkey
from PyQt5.QtWidgets import QApplication

# Windows-specific imports for hotkeys and automation
if sys.platform == 'win32':
    try:
        import win32api
        import win32con
        import win32gui
        import win32clipboard
        import keyboard
        WINDOWS_AUTOMATION_AVAILABLE = True
    except ImportError:
        WINDOWS_AUTOMATION_AVAILABLE = False
else:
    WINDOWS_AUTOMATION_AVAILABLE = False

logger = logging.getLogger(__name__)


class TaskTemplate:
    """Template for common tasks"""
    
    def __init__(self, name: str, category: str, template_data: Dict[str, Any]):
        self.name = name
        self.category = category
        self.template_data = template_data
        self.created_at = datetime.now()
        self.usage_count = 0
        self.tags = template_data.get('tags', [])
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            'name': self.name,
            'category': self.category,
            'template_data': self.template_data,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskTemplate':
        """Create template from dictionary"""
        template = cls(
            data['name'],
            data['category'],
            data['template_data']
        )
        template.created_at = datetime.fromisoformat(data['created_at'])
        template.usage_count = data.get('usage_count', 0)
        template.tags = data.get('tags', [])
        return template


class PersonalTaskTemplateManager(QObject):
    """Manages personal task templates"""
    
    template_created = pyqtSignal(str, dict)
    template_used = pyqtSignal(str, dict)
    
    def __init__(self, data_dir: str = None):
        super().__init__()
        self.data_dir = Path(data_dir or self._get_default_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.data_dir / "task_templates.json"
        self.templates: Dict[str, TaskTemplate] = {}
        self.load_templates()
        self._create_default_templates()
        
    def _get_default_data_dir(self) -> str:
        """Get default data directory"""
        if sys.platform == 'win32':
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'WestfallPersonalAssistant', 'templates')
        return os.path.join(os.path.expanduser('~'), '.westfall_assistant', 'templates')
    
    def create_template(self, name: str, category: str, template_data: Dict[str, Any]) -> bool:
        """Create a new task template"""
        try:
            template = TaskTemplate(name, category, template_data)
            self.templates[name] = template
            self.save_templates()
            
            self.template_created.emit(name, template.to_dict())
            logger.info(f"Created task template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
    
    def use_template(self, name: str, custom_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Use a task template with optional customization"""
        if name not in self.templates:
            return None
            
        template = self.templates[name]
        template.usage_count += 1
        
        # Apply template with custom data
        result_data = template.template_data.copy()
        if custom_data:
            result_data.update(custom_data)
            
        # Replace placeholders
        result_data = self._replace_placeholders(result_data)
        
        self.save_templates()
        self.template_used.emit(name, result_data)
        
        return result_data
    
    def _replace_placeholders(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace placeholders in template data"""
        placeholders = {
            '{date}': datetime.now().strftime('%Y-%m-%d'),
            '{time}': datetime.now().strftime('%H:%M'),
            '{datetime}': datetime.now().strftime('%Y-%m-%d %H:%M'),
            '{user}': os.getenv('USERNAME', 'User'),
            '{weekday}': datetime.now().strftime('%A'),
            '{month}': datetime.now().strftime('%B'),
            '{year}': str(datetime.now().year)
        }
        
        def replace_in_value(value):
            if isinstance(value, str):
                for placeholder, replacement in placeholders.items():
                    value = value.replace(placeholder, replacement)
                return value
            elif isinstance(value, dict):
                return {k: replace_in_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_in_value(v) for v in value]
            return value
        
        return replace_in_value(data)
    
    def search_templates(self, query: str = "", category: str = "", tags: List[str] = None) -> List[TaskTemplate]:
        """Search templates by query, category, or tags"""
        results = []
        query_lower = query.lower()
        tags = tags or []
        
        for template in self.templates.values():
            # Check query match
            if query and query_lower not in template.name.lower():
                continue
                
            # Check category match
            if category and category != template.category:
                continue
                
            # Check tags match
            if tags and not any(tag in template.tags for tag in tags):
                continue
                
            results.append(template)
        
        # Sort by usage count (most used first)
        results.sort(key=lambda t: t.usage_count, reverse=True)
        return results
    
    def get_template_analytics(self) -> Dict[str, Any]:
        """Get analytics about template usage"""
        total_templates = len(self.templates)
        total_usage = sum(t.usage_count for t in self.templates.values())
        
        # Category distribution
        categories = {}
        for template in self.templates.values():
            categories[template.category] = categories.get(template.category, 0) + 1
        
        # Most used templates
        most_used = sorted(self.templates.values(), key=lambda t: t.usage_count, reverse=True)[:5]
        
        return {
            'total_templates': total_templates,
            'total_usage': total_usage,
            'categories': categories,
            'most_used': [{'name': t.name, 'usage_count': t.usage_count} for t in most_used]
        }
    
    def _create_default_templates(self):
        """Create default task templates"""
        default_templates = [
            {
                'name': 'Daily Standup',
                'category': 'meetings',
                'template_data': {
                    'title': 'Daily Standup - {date}',
                    'agenda': [
                        'What did I accomplish yesterday?',
                        'What will I work on today?',
                        'Any blockers or challenges?'
                    ],
                    'duration': 15,
                    'tags': ['daily', 'standup', 'meeting']
                }
            },
            {
                'name': 'Project Planning',
                'category': 'planning',
                'template_data': {
                    'title': 'Project Plan - {date}',
                    'sections': [
                        'Project Overview',
                        'Goals and Objectives',
                        'Timeline and Milestones',
                        'Resources Required',
                        'Risk Assessment',
                        'Success Metrics'
                    ],
                    'tags': ['project', 'planning']
                }
            },
            {
                'name': 'Code Review',
                'category': 'development',
                'template_data': {
                    'title': 'Code Review - {date}',
                    'checklist': [
                        'Code functionality',
                        'Code style and formatting',
                        'Performance considerations',
                        'Security review',
                        'Documentation updates',
                        'Test coverage'
                    ],
                    'tags': ['code', 'review', 'development']
                }
            },
            {
                'name': 'Weekly Review',
                'category': 'personal',
                'template_data': {
                    'title': 'Weekly Review - Week of {date}',
                    'sections': [
                        'Accomplishments this week',
                        'Challenges faced',
                        'Goals for next week',
                        'Personal development',
                        'Work-life balance check'
                    ],
                    'tags': ['weekly', 'review', 'personal']
                }
            }
        ]
        
        for template_data in default_templates:
            if template_data['name'] not in self.templates:
                self.create_template(
                    template_data['name'],
                    template_data['category'],
                    template_data['template_data']
                )
    
    def load_templates(self):
        """Load templates from disk"""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = {
                        name: TaskTemplate.from_dict(template_data)
                        for name, template_data in data.items()
                    }
                logger.info(f"Loaded {len(self.templates)} task templates")
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self.templates = {}
    
    def save_templates(self):
        """Save templates to disk"""
        try:
            data = {name: template.to_dict() for name, template in self.templates.items()}
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")


class QuickCaptureManager(QObject):
    """System-wide quick capture with hotkeys"""
    
    text_captured = pyqtSignal(str, dict)
    screen_captured = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.capture_history = []
        self.hotkeys_registered = False
        self.capture_data_dir = Path(self._get_capture_dir())
        self.capture_data_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_capture_dir(self) -> str:
        """Get capture data directory"""
        if sys.platform == 'win32':
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'WestfallPersonalAssistant', 'captures')
        return os.path.join(os.path.expanduser('~'), '.westfall_assistant', 'captures')
    
    def register_hotkeys(self) -> bool:
        """Register system-wide hotkeys for quick capture"""
        if not WINDOWS_AUTOMATION_AVAILABLE:
            logger.warning("Windows automation not available - hotkeys disabled")
            return False
            
        try:
            # Register hotkeys
            keyboard.add_hotkey('ctrl+shift+c', self._quick_text_capture)
            keyboard.add_hotkey('ctrl+shift+s', self._quick_screen_capture)
            keyboard.add_hotkey('ctrl+shift+n', self._quick_note_capture)
            
            self.hotkeys_registered = True
            logger.info("Quick capture hotkeys registered")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}")
            return False
    
    def unregister_hotkeys(self):
        """Unregister hotkeys"""
        if WINDOWS_AUTOMATION_AVAILABLE and self.hotkeys_registered:
            try:
                keyboard.clear_all_hotkeys()
                self.hotkeys_registered = False
                logger.info("Quick capture hotkeys unregistered")
            except Exception as e:
                logger.error(f"Failed to unregister hotkeys: {e}")
    
    def _quick_text_capture(self):
        """Capture clipboard text"""
        try:
            if WINDOWS_AUTOMATION_AVAILABLE:
                win32clipboard.OpenClipboard()
                try:
                    text = win32clipboard.GetClipboardData()
                    self._save_text_capture(text, 'clipboard')
                finally:
                    win32clipboard.CloseClipboard()
        except Exception as e:
            logger.error(f"Text capture failed: {e}")
    
    def _quick_screen_capture(self):
        """Capture screen"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screen_capture_{timestamp}.png"
            filepath = self.capture_data_dir / filename
            
            # Use Windows-specific screen capture
            if WINDOWS_AUTOMATION_AVAILABLE:
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(str(filepath))
                
                self._save_screen_capture(str(filepath), 'screen')
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
    
    def _quick_note_capture(self):
        """Quick note capture"""
        try:
            # This would open a quick note dialog
            note_text = self._get_quick_note_input()
            if note_text:
                self._save_text_capture(note_text, 'note')
        except Exception as e:
            logger.error(f"Note capture failed: {e}")
    
    def _save_text_capture(self, text: str, capture_type: str):
        """Save text capture"""
        capture_data = {
            'type': capture_type,
            'content': text,
            'timestamp': datetime.now().isoformat(),
            'source': 'quick_capture'
        }
        
        self.capture_history.append(capture_data)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"text_capture_{timestamp}.json"
        filepath = self.capture_data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(capture_data, f, indent=2, ensure_ascii=False)
        
        self.text_captured.emit(text, capture_data)
        logger.info(f"Text captured: {len(text)} characters")
    
    def _save_screen_capture(self, filepath: str, capture_type: str):
        """Save screen capture metadata"""
        capture_data = {
            'type': capture_type,
            'filepath': filepath,
            'timestamp': datetime.now().isoformat(),
            'source': 'quick_capture'
        }
        
        self.capture_history.append(capture_data)
        self.screen_captured.emit(filepath, capture_data)
        logger.info(f"Screen captured: {filepath}")
    
    def _get_quick_note_input(self) -> Optional[str]:
        """Get quick note input (simplified for now)"""
        # In a real implementation, this would show a quick input dialog
        return f"Quick note captured at {datetime.now().strftime('%H:%M')}"
    
    def get_capture_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent capture history"""
        return self.capture_history[-limit:]


class AutomationRecipeManager(QObject):
    """Manages custom automation recipes"""
    
    recipe_executed = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.recipes: Dict[str, Dict[str, Any]] = {}
        self.execution_history = []
        self._create_default_recipes()
    
    def create_recipe(self, name: str, triggers: List[str], actions: List[Dict[str, Any]]) -> bool:
        """Create a new automation recipe"""
        try:
            recipe = {
                'name': name,
                'triggers': triggers,
                'actions': actions,
                'created_at': datetime.now().isoformat(),
                'execution_count': 0,
                'enabled': True
            }
            
            self.recipes[name] = recipe
            logger.info(f"Created automation recipe: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create recipe: {e}")
            return False
    
    def execute_recipe(self, name: str, context: Dict[str, Any] = None) -> bool:
        """Execute an automation recipe"""
        if name not in self.recipes:
            return False
            
        recipe = self.recipes[name]
        if not recipe.get('enabled', True):
            return False
            
        try:
            context = context or {}
            execution_result = {'actions_completed': [], 'errors': []}
            
            for action in recipe['actions']:
                try:
                    result = self._execute_action(action, context)
                    execution_result['actions_completed'].append({
                        'action': action,
                        'result': result
                    })
                except Exception as e:
                    execution_result['errors'].append({
                        'action': action,
                        'error': str(e)
                    })
            
            # Update execution count
            recipe['execution_count'] += 1
            
            # Record execution
            execution_record = {
                'recipe_name': name,
                'timestamp': datetime.now().isoformat(),
                'result': execution_result,
                'context': context
            }
            self.execution_history.append(execution_record)
            
            self.recipe_executed.emit(name, execution_record)
            logger.info(f"Executed recipe: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Recipe execution failed: {e}")
            return False
    
    def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a single action"""
        action_type = action.get('type')
        
        if action_type == 'send_notification':
            return self._send_notification_action(action, context)
        elif action_type == 'create_file':
            return self._create_file_action(action, context)
        elif action_type == 'run_command':
            return self._run_command_action(action, context)
        elif action_type == 'wait':
            return self._wait_action(action, context)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _send_notification_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Send notification action"""
        try:
            from backend.platform_compatibility import get_platform_manager
            platform_manager = get_platform_manager()
            
            title = action.get('title', 'Automation')
            message = action.get('message', 'Action completed')
            
            # Replace context variables
            title = self._replace_context_variables(title, context)
            message = self._replace_context_variables(message, context)
            
            return platform_manager.notification_manager.show_notification(title, message)
        except Exception as e:
            logger.error(f"Notification action failed: {e}")
            return False
    
    def _create_file_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Create file action"""
        try:
            filepath = action.get('path', '')
            content = action.get('content', '')
            
            # Replace context variables
            filepath = self._replace_context_variables(filepath, context)
            content = self._replace_context_variables(content, context)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Create file action failed: {e}")
            return False
    
    def _run_command_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Run command action"""
        try:
            import subprocess
            command = action.get('command', '')
            
            # Replace context variables
            command = self._replace_context_variables(command, context)
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Run command action failed: {e}")
            return False
    
    def _wait_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Wait action"""
        try:
            seconds = action.get('seconds', 1)
            time.sleep(seconds)
            return True
        except Exception as e:
            logger.error(f"Wait action failed: {e}")
            return False
    
    def _replace_context_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Replace context variables in text"""
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text
    
    def _create_default_recipes(self):
        """Create default automation recipes"""
        default_recipes = [
            {
                'name': 'Daily Backup Reminder',
                'triggers': ['time:17:00'],
                'actions': [
                    {
                        'type': 'send_notification',
                        'title': 'Daily Backup',
                        'message': 'Time to backup your important files!'
                    }
                ]
            },
            {
                'name': 'Focus Mode',
                'triggers': ['hotkey:ctrl+shift+f'],
                'actions': [
                    {
                        'type': 'send_notification',
                        'title': 'Focus Mode',
                        'message': 'Entering focus mode - notifications disabled'
                    }
                ]
            }
        ]
        
        for recipe_data in default_recipes:
            if recipe_data['name'] not in self.recipes:
                self.create_recipe(
                    recipe_data['name'],
                    recipe_data['triggers'],
                    recipe_data['actions']
                )


class PersonalProductivityManager(QObject):
    """Main productivity management coordinator"""
    
    def __init__(self):
        super().__init__()
        self.template_manager = PersonalTaskTemplateManager()
        self.quick_capture = QuickCaptureManager()
        self.automation_manager = AutomationRecipeManager()
        
        # Initialize components
        self._setup_connections()
        
    def _setup_connections(self):
        """Setup signal connections between components"""
        # Connect template events
        self.template_manager.template_used.connect(self._on_template_used)
        
        # Connect capture events
        self.quick_capture.text_captured.connect(self._on_text_captured)
        self.quick_capture.screen_captured.connect(self._on_screen_captured)
        
        # Connect automation events
        self.automation_manager.recipe_executed.connect(self._on_recipe_executed)
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize productivity features"""
        results = {}
        
        # Register hotkeys
        results['hotkeys_registered'] = self.quick_capture.register_hotkeys()
        
        # Load templates
        template_count = len(self.template_manager.templates)
        results['templates_loaded'] = template_count
        
        # Load recipes
        recipe_count = len(self.automation_manager.recipes)
        results['automation_recipes'] = recipe_count
        
        logger.info("Personal productivity manager initialized")
        return results
    
    def shutdown(self):
        """Shutdown productivity features"""
        self.quick_capture.unregister_hotkeys()
        logger.info("Personal productivity manager shut down")
    
    def _on_template_used(self, name: str, data: Dict[str, Any]):
        """Handle template usage"""
        logger.info(f"Template used: {name}")
    
    def _on_text_captured(self, text: str, data: Dict[str, Any]):
        """Handle text capture"""
        logger.info(f"Text captured: {len(text)} characters")
    
    def _on_screen_captured(self, filepath: str, data: Dict[str, Any]):
        """Handle screen capture"""
        logger.info(f"Screen captured: {filepath}")
    
    def _on_recipe_executed(self, name: str, data: Dict[str, Any]):
        """Handle recipe execution"""
        logger.info(f"Recipe executed: {name}")
    
    def get_productivity_summary(self) -> Dict[str, Any]:
        """Get productivity summary"""
        return {
            'templates': self.template_manager.get_template_analytics(),
            'captures': {
                'total_captures': len(self.quick_capture.capture_history),
                'recent_captures': len(self.quick_capture.get_capture_history(10))
            },
            'automation': {
                'total_recipes': len(self.automation_manager.recipes),
                'total_executions': len(self.automation_manager.execution_history)
            }
        }


# Global instance
_productivity_manager = None
_manager_lock = threading.Lock()


def get_productivity_manager() -> PersonalProductivityManager:
    """Get the global productivity manager instance"""
    global _productivity_manager
    
    if _productivity_manager is None:
        with _manager_lock:
            if _productivity_manager is None:
                _productivity_manager = PersonalProductivityManager()
    
    return _productivity_manager


if __name__ == "__main__":
    # Test the productivity features
    print("Personal Productivity Manager Test")
    print("=" * 40)
    
    manager = get_productivity_manager()
    init_results = manager.initialize()
    
    print("Initialization Results:")
    for key, value in init_results.items():
        print(f"  {key}: {value}")
    
    # Test template creation
    template_manager = manager.template_manager
    template_manager.create_template(
        "Test Template",
        "test",
        {
            'title': 'Test Task - {date}',
            'description': 'This is a test template created at {time}',
            'tags': ['test']
        }
    )
    
    # Test template usage
    result = template_manager.use_template("Test Template")
    print(f"\nTemplate result: {result}")
    
    # Get summary
    summary = manager.get_productivity_summary()
    print(f"\nProductivity Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    manager.shutdown()