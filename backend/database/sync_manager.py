#!/usr/bin/env python3
"""
Sync Manager for Westfall Personal Assistant

Prepares for future cloud sync capabilities with conflict resolution.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SyncManager:
    """Manages data synchronization and prepares for cloud sync."""
    
    def __init__(self, db_path: str, sync_dir: str = None):
        self.db_path = db_path
        self.sync_dir = Path(sync_dir) if sync_dir else Path.home() / ".westfall_assistant" / "sync"
        self.sync_enabled = False
        self.last_sync = None
        self.sync_conflicts = []
        
        # Ensure sync directory exists
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        
        # Load sync configuration
        self._load_sync_config()
    
    def _load_sync_config(self):
        """Load synchronization configuration."""
        config_file = self.sync_dir / "sync_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.sync_enabled = config.get("enabled", False)
                self.last_sync = config.get("last_sync")
                
                logger.info("Sync configuration loaded")
            except Exception as e:
                logger.error(f"Failed to load sync config: {e}")
    
    def _save_sync_config(self):
        """Save synchronization configuration."""
        config_file = self.sync_dir / "sync_config.json"
        
        config = {
            "enabled": self.sync_enabled,
            "last_sync": self.last_sync,
            "db_path": str(self.db_path),
            "sync_dir": str(self.sync_dir)
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Sync configuration saved")
        except Exception as e:
            logger.error(f"Failed to save sync config: {e}")
    
    def enable_sync(self):
        """Enable data synchronization."""
        self.sync_enabled = True
        self._save_sync_config()
        logger.info("Data synchronization enabled")
    
    def disable_sync(self):
        """Disable data synchronization."""
        self.sync_enabled = False
        self._save_sync_config()
        logger.info("Data synchronization disabled")
    
    def create_sync_snapshot(self) -> str:
        """Create a snapshot of current data for sync."""
        timestamp = datetime.now().isoformat()
        snapshot_file = self.sync_dir / f"snapshot_{timestamp.replace(':', '-')}.json"
        
        try:
            # Calculate database hash
            db_hash = self._calculate_file_hash(self.db_path)
            
            # Create snapshot metadata
            snapshot_data = {
                "timestamp": timestamp,
                "db_path": str(self.db_path),
                "db_hash": db_hash,
                "db_size": os.path.getsize(self.db_path),
                "version": "1.0",
                "changes": self._detect_changes()
            }
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
            
            logger.info(f"Sync snapshot created: {snapshot_file}")
            return str(snapshot_file)
            
        except Exception as e:
            logger.error(f"Failed to create sync snapshot: {e}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _detect_changes(self) -> List[Dict]:
        """Detect changes since last sync (placeholder implementation)."""
        # This is a placeholder for future implementation
        # In a real implementation, this would track database changes
        changes = []
        
        # TODO: Implement change detection based on database timestamps
        # For now, just return an empty list
        
        return changes
    
    def compare_snapshots(self, snapshot1_path: str, snapshot2_path: str) -> Dict:
        """Compare two sync snapshots."""
        try:
            with open(snapshot1_path, 'r') as f:
                snapshot1 = json.load(f)
            
            with open(snapshot2_path, 'r') as f:
                snapshot2 = json.load(f)
            
            comparison = {
                "are_identical": snapshot1["db_hash"] == snapshot2["db_hash"],
                "timestamp_diff": snapshot2["timestamp"] > snapshot1["timestamp"],
                "size_diff": snapshot2["db_size"] - snapshot1["db_size"],
                "changes_count": len(snapshot2.get("changes", [])),
                "conflicts": []
            }
            
            # Check for potential conflicts
            if not comparison["are_identical"] and comparison["timestamp_diff"]:
                comparison["conflicts"].append("Database modified on both sides")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return {"error": str(e)}
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve a sync conflict."""
        try:
            # Find the conflict
            conflict = None
            for c in self.sync_conflicts:
                if c.get("id") == conflict_id:
                    conflict = c
                    break
            
            if not conflict:
                logger.error(f"Conflict not found: {conflict_id}")
                return False
            
            # Apply resolution
            if resolution == "local":
                # Keep local version
                conflict["resolved"] = True
                conflict["resolution"] = "local"
            elif resolution == "remote":
                # Use remote version (placeholder)
                conflict["resolved"] = True
                conflict["resolution"] = "remote"
            elif resolution == "merge":
                # Attempt automatic merge (placeholder)
                conflict["resolved"] = True
                conflict["resolution"] = "merge"
            
            logger.info(f"Conflict {conflict_id} resolved with: {resolution}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """Get current synchronization status."""
        snapshots = list(self.sync_dir.glob("snapshot_*.json"))
        
        return {
            "enabled": self.sync_enabled,
            "last_sync": self.last_sync,
            "snapshots_count": len(snapshots),
            "conflicts_count": len(self.sync_conflicts),
            "sync_directory": str(self.sync_dir),
            "database_hash": self._calculate_file_hash(self.db_path) if os.path.exists(self.db_path) else None
        }
    
    def cleanup_old_snapshots(self, keep_count: int = 10):
        """Clean up old sync snapshots."""
        snapshots = list(self.sync_dir.glob("snapshot_*.json"))
        
        if len(snapshots) > keep_count:
            # Sort by modification time
            snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old snapshots
            for snapshot in snapshots[keep_count:]:
                try:
                    snapshot.unlink()
                    logger.info(f"Removed old snapshot: {snapshot.name}")
                except Exception as e:
                    logger.error(f"Failed to remove snapshot {snapshot.name}: {e}")
    
    def export_sync_data(self) -> Dict:
        """Export data in sync-ready format."""
        return {
            "timestamp": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "database_hash": self._calculate_file_hash(self.db_path) if os.path.exists(self.db_path) else None,
            "sync_enabled": self.sync_enabled,
            "last_sync": self.last_sync,
            "conflicts": self.sync_conflicts
        }
    
    def import_sync_data(self, sync_data: Dict) -> bool:
        """Import sync data (placeholder for future cloud sync)."""
        try:
            # This is a placeholder for future cloud sync implementation
            # For now, just validate the data structure
            
            required_fields = ["timestamp", "database_hash"]
            for field in required_fields:
                if field not in sync_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # TODO: Implement actual import logic
            logger.info("Sync data validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import sync data: {e}")
            return False
    
    def prepare_for_sync(self) -> Dict:
        """Prepare local data for synchronization."""
        if not self.sync_enabled:
            return {"error": "Sync not enabled"}
        
        try:
            # Create current snapshot
            snapshot_path = self.create_sync_snapshot()
            
            # Get current status
            status = self.get_sync_status()
            
            return {
                "ready": True,
                "snapshot_path": snapshot_path,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare for sync: {e}")
            return {"error": str(e)}
    
    def validate_sync_integrity(self) -> Dict:
        """Validate sync data integrity."""
        try:
            issues = []
            
            # Check if database exists
            if not os.path.exists(self.db_path):
                issues.append("Database file not found")
            
            # Check sync directory
            if not self.sync_dir.exists():
                issues.append("Sync directory not found")
            
            # Check for corrupted snapshots
            snapshots = list(self.sync_dir.glob("snapshot_*.json"))
            for snapshot in snapshots:
                try:
                    with open(snapshot, 'r') as f:
                        json.load(f)
                except Exception:
                    issues.append(f"Corrupted snapshot: {snapshot.name}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "snapshots_checked": len(snapshots)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate sync integrity: {e}")
            return {"valid": False, "error": str(e)}