#!/usr/bin/env python3
"""
Backup Manager for Westfall Personal Assistant

Handles automated database backups with encryption and scheduling.
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages automated database backups with encryption."""
    
    def __init__(self, db_path: str, backup_dir: str, encryption_manager):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.encryption_manager = encryption_manager
        self.backup_interval = 24 * 3600  # 24 hours in seconds
        self.max_backups = 7  # Keep 7 daily backups
        self.backup_thread = None
        self.stop_backup = False
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create a single backup of the database."""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / f"{backup_name}.db"
        encrypted_backup_path = self.backup_dir / f"{backup_name}.db.encrypted"
        
        try:
            # Create database backup using SQLite backup API for consistency
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Perform the backup
            source_conn.backup(backup_conn)
            
            # Close connections
            source_conn.close()
            backup_conn.close()
            
            # Encrypt the backup
            self.encryption_manager.encrypt_file(str(backup_path), str(encrypted_backup_path))
            
            # Remove unencrypted backup
            backup_path.unlink()
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "original_size": Path(self.db_path).stat().st_size,
                "backup_size": encrypted_backup_path.stat().st_size,
                "encrypted": True
            }
            
            metadata_path = self.backup_dir / f"{backup_name}.meta"
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {encrypted_backup_path}")
            return str(encrypted_backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            # Cleanup partial backup files
            if backup_path.exists():
                backup_path.unlink()
            if encrypted_backup_path.exists():
                encrypted_backup_path.unlink()
            raise
    
    def restore_backup(self, backup_path: str, target_path: str = None) -> bool:
        """Restore database from backup."""
        if target_path is None:
            target_path = self.db_path
        
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create temporary decrypted file
            temp_db_path = backup_file.parent / f"temp_restore_{datetime.now().timestamp()}.db"
            
            # Decrypt the backup
            self.encryption_manager.decrypt_file(str(backup_file), str(temp_db_path))
            
            # Backup current database if it exists
            if Path(target_path).exists():
                current_backup = f"{target_path}.before_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_path, current_backup)
                logger.info(f"Current database backed up to: {current_backup}")
            
            # Replace current database with restored one
            shutil.copy2(str(temp_db_path), target_path)
            
            # Cleanup temporary file
            temp_db_path.unlink()
            
            logger.info(f"Database restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups with metadata."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db.encrypted"):
            backup_name = backup_file.stem.replace(".db", "")
            metadata_file = self.backup_dir / f"{backup_name}.meta"
            
            backup_info = {
                "name": backup_name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            }
            
            # Load metadata if available
            if metadata_file.exists():
                try:
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    backup_info.update(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {backup_name}: {e}")
            
            backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Remove old backups beyond the retention limit."""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            backups_to_remove = backups[self.max_backups:]
            
            for backup in backups_to_remove:
                try:
                    # Remove backup file
                    backup_path = Path(backup["path"])
                    backup_path.unlink()
                    
                    # Remove metadata file
                    backup_name = backup["name"]
                    metadata_path = self.backup_dir / f"{backup_name}.meta"
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    logger.info(f"Removed old backup: {backup_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to remove old backup {backup['name']}: {e}")
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a specific backup."""
        try:
            backup_path = self.backup_dir / f"{backup_name}.db.encrypted"
            metadata_path = self.backup_dir / f"{backup_name}.meta"
            
            if backup_path.exists():
                backup_path.unlink()
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Backup deleted: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {e}")
            return False
    
    def start_automatic_backups(self):
        """Start automatic backup schedule."""
        if self.backup_thread and self.backup_thread.is_alive():
            logger.info("Automatic backups already running")
            return
        
        self.stop_backup = False
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        logger.info("Automatic backup schedule started")
    
    def stop_automatic_backups(self):
        """Stop automatic backup schedule."""
        self.stop_backup = True
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        logger.info("Automatic backup schedule stopped")
    
    def _backup_loop(self):
        """Background thread for automatic backups."""
        while not self.stop_backup:
            try:
                # Wait for the next backup time
                time.sleep(self.backup_interval)
                
                if not self.stop_backup:
                    # Create automatic backup
                    self.create_backup()
                    
                    # Cleanup old backups
                    self.cleanup_old_backups()
                    
            except Exception as e:
                logger.error(f"Error in automatic backup: {e}")
                # Continue the loop despite errors
                time.sleep(60)  # Wait a minute before retrying
    
    def set_backup_interval(self, hours: int):
        """Set backup interval in hours."""
        self.backup_interval = hours * 3600
        logger.info(f"Backup interval set to {hours} hours")
    
    def set_backup_retention(self, max_backups: int):
        """Set maximum number of backups to retain."""
        self.max_backups = max_backups
        logger.info(f"Backup retention set to {max_backups} backups")
    
    def get_backup_status(self) -> Dict:
        """Get current backup status and configuration."""
        backups = self.list_backups()
        
        return {
            "automatic_backups_running": self.backup_thread and self.backup_thread.is_alive(),
            "backup_interval_hours": self.backup_interval / 3600,
            "max_backups": self.max_backups,
            "total_backups": len(backups),
            "last_backup": backups[0] if backups else None,
            "backup_directory": str(self.backup_dir),
            "next_backup_in_seconds": self.backup_interval if not self.stop_backup else None
        }
    
    def verify_backup(self, backup_path: str) -> Dict:
        """Verify backup integrity."""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return {"valid": False, "error": "Backup file not found"}
            
            # Try to decrypt and open the backup
            temp_db_path = backup_file.parent / f"temp_verify_{datetime.now().timestamp()}.db"
            
            # Decrypt the backup
            self.encryption_manager.decrypt_file(str(backup_file), str(temp_db_path))
            
            # Try to open as SQLite database
            conn = sqlite3.connect(str(temp_db_path))
            cursor = conn.cursor()
            
            # Check if it's a valid database by running a simple query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            conn.close()
            temp_db_path.unlink()  # Cleanup temp file
            
            return {
                "valid": True,
                "tables_count": len(tables),
                "tables": [table[0] for table in tables]
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def schedule_automatic_backup(self, hour: int = 2, minute: int = 0):
        """Schedule automatic daily backup."""
        try:
            import schedule
            
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._scheduled_backup)
            logger.info(f"Scheduled automatic backup for {hour:02d}:{minute:02d}")
            
        except ImportError:
            logger.warning("schedule library not available - using simple timer")
            # Fallback to simple timer
            import threading
            import time
            
            def backup_timer():
                while not self.stop_backup:
                    # Calculate time until next backup
                    now = datetime.now()
                    next_backup = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_backup <= now:
                        next_backup += timedelta(days=1)
                    
                    sleep_seconds = (next_backup - now).total_seconds()
                    time.sleep(min(sleep_seconds, 3600))  # Check every hour max
                    
                    if not self.stop_backup:
                        self._scheduled_backup()
            
            backup_thread = threading.Thread(target=backup_timer, daemon=True)
            backup_thread.start()
    
    def _scheduled_backup(self):
        """Perform scheduled backup."""
        try:
            backup_name = f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(backup_name)
            self.cleanup_old_backups()
            logger.info("Scheduled backup completed successfully")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def create_cloud_backup(self, backup_name: str = None, cloud_provider: str = "local") -> str:
        """Create an encrypted backup for cloud storage."""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"cloud_backup_{timestamp}"
        
        try:
            # Create local encrypted backup first
            local_backup_path = self.create_backup(backup_name)
            
            if cloud_provider == "local":
                return local_backup_path
            
            # TODO: Implement actual cloud providers (AWS S3, Google Cloud, etc.)
            # For now, just return the local path
            logger.info(f"Cloud backup created locally: {local_backup_path}")
            return local_backup_path
            
        except Exception as e:
            logger.error(f"Failed to create cloud backup: {e}")
            raise
    
    def export_backup_manifest(self) -> Dict:
        """Export a manifest of all backups for external tracking."""
        backups = self.list_backups()
        
        manifest = {
            "manifest_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "backup_directory": str(self.backup_dir),
            "total_backups": len(backups),
            "backups": []
        }
        
        for backup in backups:
            manifest["backups"].append({
                "name": backup["name"],
                "created_at": backup["created_at"],
                "size_bytes": backup["size"],
                "encrypted": backup.get("encrypted", True),
                "path": backup["path"]
            })
        
        manifest_path = self.backup_dir / "backup_manifest.json"
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup manifest exported to {manifest_path}")
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to export backup manifest: {e}")
            raise
    
    def import_backup_manifest(self, manifest_path: Union[str, Path]) -> bool:
        """Import and validate backup manifest."""
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Validate manifest structure
            required_fields = ["manifest_version", "created_at", "backups"]
            for field in required_fields:
                if field not in manifest:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate each backup entry exists
            missing_backups = []
            for backup_entry in manifest["backups"]:
                backup_path = Path(backup_entry["path"])
                if not backup_path.exists():
                    missing_backups.append(backup_entry["name"])
            
            if missing_backups:
                logger.warning(f"Missing backup files: {missing_backups}")
                return False
            
            logger.info(f"Backup manifest validated successfully: {len(manifest['backups'])} backups")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import backup manifest: {e}")
            return False