#!/usr/bin/env python3
"""
Database Schema Versioning and Migration System for Westfall Personal Assistant

Provides schema versioning, migration paths, data validation during migration,
configuration upgrades, and rollback capabilities.
"""

import os
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import threading
import hashlib
import shutil

logger = logging.getLogger(__name__)


class MigrationType(Enum):
    """Types of database migrations."""
    SCHEMA_CHANGE = "schema_change"
    DATA_TRANSFORM = "data_transform"
    INDEX_UPDATE = "index_update"
    CONSTRAINT_CHANGE = "constraint_change"
    CLEANUP = "cleanup"


@dataclass
class Migration:
    """Represents a database migration."""
    version: str
    name: str
    description: str
    migration_type: MigrationType
    up_sql: str
    down_sql: str
    dependencies: List[str]
    created_at: datetime
    checksum: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'version': self.version,
            'name': self.name,
            'description': self.description,
            'migration_type': self.migration_type.value,
            'up_sql': self.up_sql,
            'down_sql': self.down_sql,
            'dependencies': self.dependencies,
            'created_at': self.created_at.isoformat(),
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Migration':
        """Create migration from dictionary."""
        return cls(
            version=data['version'],
            name=data['name'],
            description=data['description'],
            migration_type=MigrationType(data['migration_type']),
            up_sql=data['up_sql'],
            down_sql=data['down_sql'],
            dependencies=data.get('dependencies', []),
            created_at=datetime.fromisoformat(data['created_at']),
            checksum=data['checksum']
        )


class SchemaVersionManager:
    """Manages database schema versions and migrations."""
    
    def __init__(self, db_path: str, migrations_dir: str = None):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir) if migrations_dir else Path("migrations")
        self.migrations_dir.mkdir(exist_ok=True)
        
        self.migrations = {}
        self.applied_migrations = set()
        self.lock = threading.RLock()
        
        self._ensure_migration_table()
        self._load_migrations()
        self._load_applied_migrations()
    
    def _ensure_migration_table(self):
        """Ensure the migrations tracking table exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        migration_type TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checksum TEXT NOT NULL,
                        rollback_data TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def _load_migrations(self):
        """Load migration files from the migrations directory."""
        with self.lock:
            self.migrations.clear()
            
            for migration_file in self.migrations_dir.glob("*.json"):
                try:
                    with open(migration_file, 'r') as f:
                        migration_data = json.load(f)
                    
                    migration = Migration.from_dict(migration_data)
                    self.migrations[migration.version] = migration
                    
                except Exception as e:
                    logger.error(f"Failed to load migration {migration_file}: {e}")
    
    def _load_applied_migrations(self):
        """Load list of applied migrations from database."""
        with self.lock:
            self.applied_migrations.clear()
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
                    
                    for row in cursor.fetchall():
                        self.applied_migrations.add(row[0])
                        
            except Exception as e:
                logger.error(f"Failed to load applied migrations: {e}")
    
    def create_migration(self, name: str, description: str, migration_type: MigrationType,
                        up_sql: str, down_sql: str, dependencies: List[str] = None) -> str:
        """Create a new migration."""
        # Generate version based on timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate checksum
        content = f"{name}{description}{up_sql}{down_sql}"
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        migration = Migration(
            version=version,
            name=name,
            description=description,
            migration_type=migration_type,
            up_sql=up_sql,
            down_sql=down_sql,
            dependencies=dependencies or [],
            created_at=datetime.now(),
            checksum=checksum
        )
        
        # Save migration to file
        migration_file = self.migrations_dir / f"{version}_{name.replace(' ', '_').lower()}.json"
        try:
            with open(migration_file, 'w') as f:
                json.dump(migration.to_dict(), f, indent=2)
            
            # Add to loaded migrations
            with self.lock:
                self.migrations[version] = migration
            
            logger.info(f"Created migration {version}: {name}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise
    
    def apply_migration(self, version: str, validate_data: bool = True) -> bool:
        """Apply a specific migration."""
        with self.lock:
            if version in self.applied_migrations:
                logger.warning(f"Migration {version} already applied")
                return True
            
            if version not in self.migrations:
                logger.error(f"Migration {version} not found")
                return False
            
            migration = self.migrations[version]
            
            # Check dependencies
            for dep_version in migration.dependencies:
                if dep_version not in self.applied_migrations:
                    logger.error(f"Dependency {dep_version} not applied for migration {version}")
                    return False
            
            try:
                # Create backup before migration
                backup_data = self._create_rollback_data(migration)
                
                with sqlite3.connect(self.db_path) as conn:
                    # Execute migration SQL
                    for statement in migration.up_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(statement)
                    
                    # Validate data if requested
                    if validate_data and not self._validate_migration_data(conn, migration):
                        conn.rollback()
                        logger.error(f"Data validation failed for migration {version}")
                        return False
                    
                    # Record migration as applied
                    conn.execute('''
                        INSERT INTO schema_migrations 
                        (version, name, description, migration_type, checksum, rollback_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        migration.version,
                        migration.name,
                        migration.description,
                        migration.migration_type.value,
                        migration.checksum,
                        json.dumps(backup_data)
                    ))
                    
                    conn.commit()
                
                self.applied_migrations.add(version)
                logger.info(f"Successfully applied migration {version}: {migration.name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration."""
        with self.lock:
            if version not in self.applied_migrations:
                logger.warning(f"Migration {version} not applied, cannot rollback")
                return True
            
            if version not in self.migrations:
                logger.error(f"Migration {version} definition not found")
                return False
            
            migration = self.migrations[version]
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Get rollback data
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT rollback_data FROM schema_migrations WHERE version = ?",
                        (version,)
                    )
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        rollback_data = json.loads(result[0])
                        self._restore_rollback_data(conn, rollback_data)
                    
                    # Execute rollback SQL
                    for statement in migration.down_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(statement)
                    
                    # Remove migration record
                    conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                    conn.commit()
                
                self.applied_migrations.discard(version)
                logger.info(f"Successfully rolled back migration {version}: {migration.name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to rollback migration {version}: {e}")
                return False
    
    def migrate_to_version(self, target_version: str) -> bool:
        """Migrate database to a specific version."""
        with self.lock:
            # Get migrations that need to be applied
            pending_migrations = []
            
            for version in sorted(self.migrations.keys()):
                if version <= target_version and version not in self.applied_migrations:
                    pending_migrations.append(version)
            
            # Apply migrations in order
            for version in pending_migrations:
                if not self.apply_migration(version):
                    logger.error(f"Migration to version {target_version} failed at {version}")
                    return False
            
            logger.info(f"Successfully migrated to version {target_version}")
            return True
    
    def migrate_to_latest(self) -> bool:
        """Migrate database to the latest version."""
        with self.lock:
            if not self.migrations:
                logger.info("No migrations found")
                return True
            
            latest_version = max(self.migrations.keys())
            return self.migrate_to_version(latest_version)
    
    def get_current_version(self) -> Optional[str]:
        """Get the current schema version."""
        with self.lock:
            if not self.applied_migrations:
                return None
            return max(self.applied_migrations)
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations."""
        with self.lock:
            return [v for v in sorted(self.migrations.keys()) if v not in self.applied_migrations]
    
    def _create_rollback_data(self, migration: Migration) -> Dict:
        """Create rollback data before applying migration."""
        # For now, just store basic info
        # In a real implementation, this would capture data that might be lost
        return {
            'migration_version': migration.version,
            'timestamp': datetime.now().isoformat(),
            'type': 'basic_rollback'
        }
    
    def _restore_rollback_data(self, conn: sqlite3.Connection, rollback_data: Dict):
        """Restore data from rollback information."""
        # Implementation would depend on what data was captured
        logger.info(f"Restoring rollback data: {rollback_data.get('type', 'unknown')}")
    
    def _validate_migration_data(self, conn: sqlite3.Connection, migration: Migration) -> bool:
        """Validate data after migration."""
        try:
            # Basic validation - check that all tables still exist and are accessible
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if not table_name.startswith('sqlite_'):
                    # Try to count rows to ensure table is accessible
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    cursor.fetchone()
            
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    def export_migration_history(self) -> Dict:
        """Export migration history for backup/audit purposes."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT version, name, description, migration_type, applied_at, checksum
                        FROM schema_migrations ORDER BY applied_at
                    ''')
                    
                    history = []
                    for row in cursor.fetchall():
                        history.append({
                            'version': row[0],
                            'name': row[1],
                            'description': row[2],
                            'migration_type': row[3],
                            'applied_at': row[4],
                            'checksum': row[5]
                        })
                    
                    return {
                        'exported_at': datetime.now().isoformat(),
                        'current_version': self.get_current_version(),
                        'total_migrations': len(history),
                        'migrations': history
                    }
                    
            except Exception as e:
                logger.error(f"Failed to export migration history: {e}")
                return {}


class ConfigurationUpgrader:
    """Handles configuration file upgrades between versions."""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.upgrade_handlers = {}
        self.config_versions = {}
    
    def register_upgrade_handler(self, from_version: str, to_version: str, 
                                handler: Callable[[Dict], Dict]):
        """Register an upgrade handler for configuration files."""
        self.upgrade_handlers[(from_version, to_version)] = handler
    
    def upgrade_config_file(self, config_file: Path, target_version: str) -> bool:
        """Upgrade a configuration file to target version."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            current_version = config_data.get('version', '1.0.0')
            
            if current_version == target_version:
                logger.info(f"Config {config_file.name} already at target version {target_version}")
                return True
            
            # Create backup
            backup_path = config_file.with_suffix(f'.backup_{current_version}')
            shutil.copy2(config_file, backup_path)
            
            # Apply upgrades
            upgraded_config = self._apply_config_upgrades(config_data, current_version, target_version)
            
            if upgraded_config is None:
                logger.error(f"No upgrade path from {current_version} to {target_version}")
                return False
            
            # Set new version
            upgraded_config['version'] = target_version
            upgraded_config['upgraded_at'] = datetime.now().isoformat()
            
            # Save upgraded config
            with open(config_file, 'w') as f:
                json.dump(upgraded_config, f, indent=2)
            
            logger.info(f"Upgraded {config_file.name} from {current_version} to {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upgrade config {config_file}: {e}")
            return False
    
    def _apply_config_upgrades(self, config_data: Dict, from_version: str, 
                              to_version: str) -> Optional[Dict]:
        """Apply a series of upgrades to reach target version."""
        current_data = config_data.copy()
        current_version = from_version
        
        # Simple approach: try direct upgrade first
        if (from_version, to_version) in self.upgrade_handlers:
            handler = self.upgrade_handlers[(from_version, to_version)]
            return handler(current_data)
        
        # TODO: Implement multi-step upgrade path finding
        # For now, only support direct upgrades
        
        return None
    
    def upgrade_all_configs(self, target_version: str) -> bool:
        """Upgrade all configuration files to target version."""
        success = True
        
        for config_file in self.config_dir.glob("*.json"):
            if not self.upgrade_config_file(config_file, target_version):
                success = False
                logger.error(f"Failed to upgrade {config_file}")
        
        return success


# Example migration creation helpers
def create_add_column_migration(table_name: str, column_name: str, column_type: str, 
                               default_value: str = None) -> Tuple[str, str]:
    """Create SQL for adding a column."""
    up_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    if default_value:
        up_sql += f" DEFAULT {default_value}"
    
    # SQLite doesn't support DROP COLUMN easily, so we create a complex rollback
    down_sql = f"-- Cannot easily drop column {column_name} from {table_name} in SQLite"
    
    return up_sql, down_sql


def create_add_table_migration(table_name: str, schema: str) -> Tuple[str, str]:
    """Create SQL for adding a table."""
    up_sql = f"CREATE TABLE {table_name} ({schema})"
    down_sql = f"DROP TABLE IF EXISTS {table_name}"
    
    return up_sql, down_sql


def create_add_index_migration(index_name: str, table_name: str, columns: List[str]) -> Tuple[str, str]:
    """Create SQL for adding an index."""
    columns_str = ", ".join(columns)
    up_sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
    down_sql = f"DROP INDEX IF EXISTS {index_name}"
    
    return up_sql, down_sql