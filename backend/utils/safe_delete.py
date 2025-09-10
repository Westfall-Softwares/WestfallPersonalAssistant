#!/usr/bin/env python3
"""
Safe Deletion and Recovery Utilities for Westfall Assistant - Entrepreneur Edition

Provides soft delete functionality with recovery options for critical data.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SafeDeleteManager:
    """Manages soft deletion and recovery of critical data."""
    
    def __init__(self, config_dir: str = None, retention_days: int = 30):
        self.config_dir = config_dir or os.path.expanduser("~/.westfall_assistant")
        self.trash_dir = os.path.join(self.config_dir, "trash")
        self.retention_days = retention_days
        
        # Ensure trash directory exists
        os.makedirs(self.trash_dir, exist_ok=True)
        
        # Periodically clean old trash entries
        self._cleanup_old_entries()
    
    def soft_delete(self, item_type: str, item_id: str, data: Any, metadata: Dict[str, Any] = None) -> str:
        """
        Soft delete an item by moving it to trash with recovery information.
        
        Args:
            item_type: Type of item being deleted (e.g., 'api_key', 'setting', 'conversation')
            item_id: Unique identifier for the item
            data: The data being deleted
            metadata: Additional metadata about the deletion
        
        Returns:
            trash_id: Unique identifier for recovery
        """
        timestamp = datetime.now().isoformat()
        trash_id = f"{item_type}_{item_id}_{int(time.time())}"
        
        trash_entry = {
            "trash_id": trash_id,
            "item_type": item_type,
            "item_id": item_id,
            "data": data,
            "metadata": metadata or {},
            "deleted_at": timestamp,
            "expires_at": (datetime.now() + timedelta(days=self.retention_days)).isoformat()
        }
        
        trash_file = os.path.join(self.trash_dir, f"{trash_id}.json")
        
        try:
            with open(trash_file, 'w') as f:
                json.dump(trash_entry, f, indent=2, default=str)
            
            logger.info(f"Item soft deleted: {item_type}/{item_id} -> {trash_id}")
            return trash_id
            
        except Exception as e:
            logger.error(f"Failed to soft delete item: {e}")
            raise
    
    def recover_item(self, trash_id: str) -> Optional[Dict[str, Any]]:
        """
        Recover a soft-deleted item.
        
        Args:
            trash_id: The trash ID returned from soft_delete
        
        Returns:
            The recovered item data or None if not found
        """
        trash_file = os.path.join(self.trash_dir, f"{trash_id}.json")
        
        if not os.path.exists(trash_file):
            return None
        
        try:
            with open(trash_file, 'r') as f:
                trash_entry = json.load(f)
            
            # Check if item has expired
            expires_at = datetime.fromisoformat(trash_entry["expires_at"])
            if datetime.now() > expires_at:
                os.remove(trash_file)
                logger.warning(f"Trash item expired and removed: {trash_id}")
                return None
            
            logger.info(f"Item recovered from trash: {trash_id}")
            return trash_entry
            
        except Exception as e:
            logger.error(f"Failed to recover item {trash_id}: {e}")
            return None
    
    def restore_item(self, trash_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore an item and remove it from trash.
        
        Args:
            trash_id: The trash ID to restore
        
        Returns:
            The restored item data or None if not found
        """
        trash_entry = self.recover_item(trash_id)
        if not trash_entry:
            return None
        
        # Remove from trash after successful recovery
        trash_file = os.path.join(self.trash_dir, f"{trash_id}.json")
        try:
            os.remove(trash_file)
            logger.info(f"Item restored and removed from trash: {trash_id}")
        except Exception as e:
            logger.warning(f"Failed to remove trash file after restore: {e}")
        
        return trash_entry
    
    def list_trash_items(self, item_type: str = None) -> List[Dict[str, Any]]:
        """
        List items in trash, optionally filtered by type.
        
        Args:
            item_type: Optional filter by item type
        
        Returns:
            List of trash entries
        """
        trash_items = []
        
        if not os.path.exists(self.trash_dir):
            return trash_items
        
        for filename in os.listdir(self.trash_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.trash_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    trash_entry = json.load(f)
                
                # Check if expired
                expires_at = datetime.fromisoformat(trash_entry["expires_at"])
                if datetime.now() > expires_at:
                    os.remove(filepath)
                    continue
                
                # Filter by type if specified
                if item_type and trash_entry.get("item_type") != item_type:
                    continue
                
                # Add summary info for listing
                trash_entry["summary"] = {
                    "trash_id": trash_entry["trash_id"],
                    "item_type": trash_entry["item_type"],
                    "item_id": trash_entry["item_id"],
                    "deleted_at": trash_entry["deleted_at"],
                    "expires_at": trash_entry["expires_at"],
                    "days_until_expiry": (expires_at - datetime.now()).days
                }
                
                trash_items.append(trash_entry)
                
            except Exception as e:
                logger.error(f"Failed to read trash file {filename}: {e}")
        
        return sorted(trash_items, key=lambda x: x["deleted_at"], reverse=True)
    
    def permanently_delete(self, trash_id: str) -> bool:
        """
        Permanently delete an item from trash.
        
        Args:
            trash_id: The trash ID to permanently delete
        
        Returns:
            True if successfully deleted, False otherwise
        """
        trash_file = os.path.join(self.trash_dir, f"{trash_id}.json")
        
        if not os.path.exists(trash_file):
            return False
        
        try:
            os.remove(trash_file)
            logger.info(f"Item permanently deleted from trash: {trash_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to permanently delete item {trash_id}: {e}")
            return False
    
    def _cleanup_old_entries(self):
        """Remove expired entries from trash."""
        if not os.path.exists(self.trash_dir):
            return
        
        current_time = datetime.now()
        cleaned_count = 0
        
        for filename in os.listdir(self.trash_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.trash_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    trash_entry = json.load(f)
                
                expires_at = datetime.fromisoformat(trash_entry["expires_at"])
                if current_time > expires_at:
                    os.remove(filepath)
                    cleaned_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process trash file {filename}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} expired items from trash")
    
    def empty_trash(self, item_type: str = None) -> int:
        """
        Empty the trash, optionally for a specific item type.
        
        Args:
            item_type: Optional filter by item type
        
        Returns:
            Number of items deleted
        """
        if not os.path.exists(self.trash_dir):
            return 0
        
        deleted_count = 0
        
        for filename in os.listdir(self.trash_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.trash_dir, filename)
            
            try:
                # If filtering by type, check the content
                if item_type:
                    with open(filepath, 'r') as f:
                        trash_entry = json.load(f)
                    
                    if trash_entry.get("item_type") != item_type:
                        continue
                
                os.remove(filepath)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to delete trash file {filename}: {e}")
        
        logger.info(f"Emptied trash: {deleted_count} items deleted")
        return deleted_count
    
    def get_trash_stats(self) -> Dict[str, Any]:
        """Get statistics about trash contents."""
        if not os.path.exists(self.trash_dir):
            return {"total_items": 0, "by_type": {}, "total_size_mb": 0}
        
        stats = {
            "total_items": 0,
            "by_type": {},
            "total_size_mb": 0,
            "oldest_item": None,
            "newest_item": None
        }
        
        oldest_time = None
        newest_time = None
        
        for filename in os.listdir(self.trash_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.trash_dir, filename)
            
            try:
                # Get file size
                file_size = os.path.getsize(filepath)
                stats["total_size_mb"] += file_size / (1024 * 1024)
                
                # Read content for type stats
                with open(filepath, 'r') as f:
                    trash_entry = json.load(f)
                
                item_type = trash_entry.get("item_type", "unknown")
                stats["by_type"][item_type] = stats["by_type"].get(item_type, 0) + 1
                stats["total_items"] += 1
                
                # Track oldest and newest
                deleted_at = datetime.fromisoformat(trash_entry["deleted_at"])
                if oldest_time is None or deleted_at < oldest_time:
                    oldest_time = deleted_at
                    stats["oldest_item"] = trash_entry["deleted_at"]
                
                if newest_time is None or deleted_at > newest_time:
                    newest_time = deleted_at
                    stats["newest_item"] = trash_entry["deleted_at"]
                
            except Exception as e:
                logger.error(f"Failed to process trash file for stats {filename}: {e}")
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats


# Global safe delete manager instance
_global_safe_delete_manager: Optional[SafeDeleteManager] = None


def get_safe_delete_manager(config_dir: str = None) -> SafeDeleteManager:
    """Get or create the global safe delete manager."""
    global _global_safe_delete_manager
    
    if _global_safe_delete_manager is None:
        _global_safe_delete_manager = SafeDeleteManager(config_dir)
    
    return _global_safe_delete_manager


def safe_delete(item_type: str, item_id: str, data: Any, metadata: Dict[str, Any] = None) -> str:
    """Convenience function for safe deletion."""
    manager = get_safe_delete_manager()
    return manager.soft_delete(item_type, item_id, data, metadata)


def recover_item(trash_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function for recovery."""
    manager = get_safe_delete_manager()
    return manager.recover_item(trash_id)