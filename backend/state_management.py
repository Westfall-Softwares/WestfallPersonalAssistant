#!/usr/bin/env python3
"""
Centralized State Management System for Westfall Personal Assistant

Provides unified state management with observer pattern, persistence, 
and undo/redo functionality for the application.
"""

import json
import logging
import threading
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import copy
import weakref

logger = logging.getLogger(__name__)


class StateChangeType(Enum):
    """Types of state changes."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_UPDATE = "bulk_update"


@dataclass
class StateChange:
    """Represents a state change for undo/redo functionality."""
    change_id: str
    change_type: StateChangeType
    path: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'change_id': self.change_id,
            'change_type': self.change_type.value,
            'path': self.path,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StateChange':
        """Create from dictionary for deserialization."""
        return cls(
            change_id=data['change_id'],
            change_type=StateChangeType(data['change_type']),
            path=data['path'],
            old_value=data['old_value'],
            new_value=data['new_value'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class StateObserver:
    """Base class for state observers."""
    
    def on_state_change(self, path: str, old_value: Any, new_value: Any, 
                       change_type: StateChangeType, metadata: Dict = None):
        """Called when state changes."""
        pass
    
    def on_state_batch_change(self, changes: List[StateChange]):
        """Called when multiple state changes occur in a batch."""
        pass


class StateManager:
    """Centralized state management with observer pattern and persistence."""
    
    def __init__(self, persistence_path: Optional[str] = None):
        self._state: Dict = {}
        self._observers: List[weakref.ref] = []
        self._change_history: List[StateChange] = []
        self._undo_stack: List[StateChange] = []
        self._redo_stack: List[StateChange] = []
        self._lock = threading.RLock()
        self._batch_mode = False
        self._batch_changes: List[StateChange] = []
        self._change_counter = 0
        self._max_history = 1000
        self._persistence_path = Path(persistence_path) if persistence_path else None
        
        # Load state from persistence if available
        if self._persistence_path and self._persistence_path.exists():
            self._load_state()
    
    def _generate_change_id(self) -> str:
        """Generate unique change ID."""
        self._change_counter += 1
        return f"change_{self._change_counter}_{int(datetime.now().timestamp() * 1000)}"
    
    def _get_nested_value(self, path: str) -> Any:
        """Get value from nested dictionary path."""
        keys = path.split('.')
        value = self._state
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, path: str, value: Any) -> Any:
        """Set value in nested dictionary path, return old value."""
        keys = path.split('.')
        current = self._state
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Get old value and set new value
        final_key = keys[-1]
        old_value = current.get(final_key)
        current[final_key] = value
        
        return old_value
    
    def _delete_nested_value(self, path: str) -> Any:
        """Delete value from nested dictionary path, return old value."""
        keys = path.split('.')
        current = self._state
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                return None
            current = current[key]
        
        # Delete final key
        final_key = keys[-1]
        return current.pop(final_key, None)
    
    def _notify_observers(self, path: str, old_value: Any, new_value: Any, 
                         change_type: StateChangeType, metadata: Dict = None):
        """Notify all observers of state change."""
        # Clean up dead references
        self._observers = [ref for ref in self._observers if ref() is not None]
        
        for observer_ref in self._observers:
            observer = observer_ref()
            if observer:
                try:
                    observer.on_state_change(path, old_value, new_value, change_type, metadata)
                except Exception as e:
                    logger.error(f"Error notifying observer: {e}")
    
    def _notify_batch_observers(self, changes: List[StateChange]):
        """Notify observers of batch changes."""
        self._observers = [ref for ref in self._observers if ref() is not None]
        
        for observer_ref in self._observers:
            observer = observer_ref()
            if observer:
                try:
                    observer.on_state_batch_change(changes)
                except Exception as e:
                    logger.error(f"Error notifying observer for batch: {e}")
    
    def _record_change(self, change: StateChange):
        """Record a state change for undo/redo."""
        self._change_history.append(change)
        
        # Limit history size
        if len(self._change_history) > self._max_history:
            self._change_history = self._change_history[-self._max_history:]
        
        # Add to undo stack
        self._undo_stack.append(change)
        
        # Clear redo stack when new change is made
        self._redo_stack.clear()
        
        # Limit undo stack size
        if len(self._undo_stack) > 100:
            self._undo_stack = self._undo_stack[-100:]
    
    def add_observer(self, observer: StateObserver):
        """Add a state observer."""
        with self._lock:
            self._observers.append(weakref.ref(observer))
    
    def remove_observer(self, observer: StateObserver):
        """Remove a state observer."""
        with self._lock:
            self._observers = [ref for ref in self._observers 
                             if ref() is not None and ref() != observer]
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get state value by path."""
        with self._lock:
            value = self._get_nested_value(path)
            return copy.deepcopy(value) if value is not None else default
    
    def set(self, path: str, value: Any, metadata: Dict = None) -> bool:
        """Set state value by path."""
        with self._lock:
            try:
                old_value = self._get_nested_value(path)
                
                # Determine change type
                if old_value is None:
                    change_type = StateChangeType.CREATE
                else:
                    change_type = StateChangeType.UPDATE
                
                # Set new value
                self._set_nested_value(path, copy.deepcopy(value))
                
                # Create change record
                change = StateChange(
                    change_id=self._generate_change_id(),
                    change_type=change_type,
                    path=path,
                    old_value=copy.deepcopy(old_value),
                    new_value=copy.deepcopy(value),
                    timestamp=datetime.now(),
                    metadata=metadata
                )
                
                if self._batch_mode:
                    self._batch_changes.append(change)
                else:
                    self._record_change(change)
                    self._notify_observers(path, old_value, value, change_type, metadata)
                    self._auto_persist()
                
                return True
                
            except Exception as e:
                logger.error(f"Error setting state {path}: {e}")
                return False
    
    def update(self, path: str, updates: Dict, metadata: Dict = None) -> bool:
        """Update multiple values in a nested object."""
        with self._lock:
            try:
                current_value = self._get_nested_value(path)
                if not isinstance(current_value, dict):
                    logger.error(f"Cannot update non-dict value at path {path}")
                    return False
                
                old_value = copy.deepcopy(current_value)
                current_value.update(updates)
                
                change = StateChange(
                    change_id=self._generate_change_id(),
                    change_type=StateChangeType.UPDATE,
                    path=path,
                    old_value=old_value,
                    new_value=copy.deepcopy(current_value),
                    timestamp=datetime.now(),
                    metadata=metadata
                )
                
                if self._batch_mode:
                    self._batch_changes.append(change)
                else:
                    self._record_change(change)
                    self._notify_observers(path, old_value, current_value, 
                                         StateChangeType.UPDATE, metadata)
                    self._auto_persist()
                
                return True
                
            except Exception as e:
                logger.error(f"Error updating state {path}: {e}")
                return False
    
    def delete(self, path: str, metadata: Dict = None) -> bool:
        """Delete state value by path."""
        with self._lock:
            try:
                old_value = self._delete_nested_value(path)
                
                if old_value is None:
                    return False  # Nothing to delete
                
                change = StateChange(
                    change_id=self._generate_change_id(),
                    change_type=StateChangeType.DELETE,
                    path=path,
                    old_value=copy.deepcopy(old_value),
                    new_value=None,
                    timestamp=datetime.now(),
                    metadata=metadata
                )
                
                if self._batch_mode:
                    self._batch_changes.append(change)
                else:
                    self._record_change(change)
                    self._notify_observers(path, old_value, None, 
                                         StateChangeType.DELETE, metadata)
                    self._auto_persist()
                
                return True
                
            except Exception as e:
                logger.error(f"Error deleting state {path}: {e}")
                return False
    
    def batch_update(self, updates: List[Dict], metadata: Dict = None):
        """Perform multiple state updates in a batch."""
        with self._lock:
            self._batch_mode = True
            self._batch_changes.clear()
            
            try:
                for update in updates:
                    path = update.get('path')
                    action = update.get('action', 'set')
                    value = update.get('value')
                    
                    if action == 'set':
                        self.set(path, value)
                    elif action == 'update':
                        self.update(path, value)
                    elif action == 'delete':
                        self.delete(path)
                
                # Process batch
                if self._batch_changes:
                    for change in self._batch_changes:
                        self._record_change(change)
                    
                    self._notify_batch_observers(self._batch_changes)
                    self._auto_persist()
                
            finally:
                self._batch_mode = False
                self._batch_changes.clear()
    
    def undo(self) -> bool:
        """Undo the last state change."""
        with self._lock:
            if not self._undo_stack:
                return False
            
            change = self._undo_stack.pop()
            
            try:
                # Reverse the change
                if change.change_type == StateChangeType.CREATE:
                    self._delete_nested_value(change.path)
                elif change.change_type == StateChangeType.UPDATE:
                    self._set_nested_value(change.path, change.old_value)
                elif change.change_type == StateChangeType.DELETE:
                    self._set_nested_value(change.path, change.old_value)
                
                # Add to redo stack
                self._redo_stack.append(change)
                
                # Notify observers
                self._notify_observers(change.path, change.new_value, change.old_value, 
                                     change.change_type, {"action": "undo"})
                self._auto_persist()
                
                return True
                
            except Exception as e:
                logger.error(f"Error during undo: {e}")
                # Put change back on undo stack
                self._undo_stack.append(change)
                return False
    
    def redo(self) -> bool:
        """Redo the last undone state change."""
        with self._lock:
            if not self._redo_stack:
                return False
            
            change = self._redo_stack.pop()
            
            try:
                # Reapply the change
                if change.change_type == StateChangeType.CREATE:
                    self._set_nested_value(change.path, change.new_value)
                elif change.change_type == StateChangeType.UPDATE:
                    self._set_nested_value(change.path, change.new_value)
                elif change.change_type == StateChangeType.DELETE:
                    self._delete_nested_value(change.path)
                
                # Add back to undo stack
                self._undo_stack.append(change)
                
                # Notify observers
                self._notify_observers(change.path, change.old_value, change.new_value, 
                                     change.change_type, {"action": "redo"})
                self._auto_persist()
                
                return True
                
            except Exception as e:
                logger.error(f"Error during redo: {e}")
                # Put change back on redo stack
                self._redo_stack.append(change)
                return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return bool(self._undo_stack)
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return bool(self._redo_stack)
    
    def get_state_snapshot(self) -> Dict:
        """Get a complete snapshot of the current state."""
        with self._lock:
            return copy.deepcopy(self._state)
    
    def restore_state_snapshot(self, snapshot: Dict, metadata: Dict = None):
        """Restore state from a snapshot."""
        with self._lock:
            old_state = copy.deepcopy(self._state)
            self._state = copy.deepcopy(snapshot)
            
            change = StateChange(
                change_id=self._generate_change_id(),
                change_type=StateChangeType.BULK_UPDATE,
                path="",
                old_value=old_state,
                new_value=snapshot,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self._record_change(change)
            self._notify_observers("", old_state, snapshot, 
                                 StateChangeType.BULK_UPDATE, metadata)
            self._auto_persist()
    
    def get_change_history(self, limit: int = 100) -> List[Dict]:
        """Get recent change history."""
        with self._lock:
            recent_changes = self._change_history[-limit:] if limit else self._change_history
            return [change.to_dict() for change in recent_changes]
    
    def clear_history(self):
        """Clear change history and undo/redo stacks."""
        with self._lock:
            self._change_history.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()
    
    def _auto_persist(self):
        """Automatically persist state if persistence is enabled."""
        if self._persistence_path:
            try:
                self.persist()
            except Exception as e:
                logger.error(f"Auto-persist failed: {e}")
    
    def persist(self, path: Optional[str] = None):
        """Persist current state to file."""
        persist_path = Path(path) if path else self._persistence_path
        if not persist_path:
            return
        
        try:
            persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            state_data = {
                "state": self._state,
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "change_count": len(self._change_history)
                }
            }
            
            with open(persist_path, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            
            logger.debug(f"State persisted to {persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")
    
    def _load_state(self, path: Optional[str] = None):
        """Load state from file."""
        load_path = Path(path) if path else self._persistence_path
        if not load_path or not load_path.exists():
            return
        
        try:
            with open(load_path, 'r') as f:
                state_data = json.load(f)
            
            self._state = state_data.get("state", {})
            logger.info(f"State loaded from {load_path}")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    
    def get_status(self) -> Dict:
        """Get state manager status information."""
        with self._lock:
            return {
                "state_size": len(str(self._state)),
                "change_history_count": len(self._change_history),
                "undo_stack_count": len(self._undo_stack),
                "redo_stack_count": len(self._redo_stack),
                "observer_count": len([ref for ref in self._observers if ref() is not None]),
                "persistence_enabled": self._persistence_path is not None,
                "batch_mode": self._batch_mode
            }


# Global state manager instance
state_manager = StateManager()


def initialize_state_manager(persistence_path: str = None):
    """Initialize global state manager with persistence."""
    global state_manager
    state_manager = StateManager(persistence_path)
    return state_manager