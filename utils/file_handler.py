"""
File Handling Utilities for Westfall Personal Assistant

Provides safe file operations, path management, and file type detection.
"""

import os
import json
import shutil
import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def ensure_directory(directory: Union[str, Path]) -> bool:
    """Ensure directory exists, create if necessary"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False


def safe_read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Safely read a text file"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None


def safe_write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8', backup: bool = True) -> bool:
    """Safely write content to a file with optional backup"""
    try:
        file_path = Path(file_path)
        
        # Create backup if file exists and backup is requested
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            shutil.copy2(file_path, backup_path)
        
        # Ensure parent directory exists
        ensure_directory(file_path.parent)
        
        # Write to temporary file first, then rename for atomic operation
        temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        with open(temp_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Atomic rename
        temp_path.rename(file_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False


def safe_read_json(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Safely read and parse JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        return None


def safe_write_json(file_path: Union[str, Path], data: Any, indent: int = 2, backup: bool = True) -> bool:
    """Safely write data to JSON file"""
    try:
        json_content = json.dumps(data, indent=indent, default=str, ensure_ascii=False)
        return safe_write_file(file_path, json_content, backup=backup)
    except Exception as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
    """Calculate file hash"""
    try:
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
        
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return None


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get comprehensive file information"""
    path = Path(file_path)
    
    try:
        stat = path.stat()
        
        return {
            'path': str(path.absolute()),
            'name': path.name,
            'extension': path.suffix,
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'is_file': path.is_file(),
            'is_directory': path.is_dir(),
            'mime_type': mimetypes.guess_type(str(path))[0],
            'hash_sha256': get_file_hash(path) if path.is_file() else None
        }
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {'path': str(path), 'error': str(e)}


def cleanup_directory(directory: Union[str, Path], max_age_days: int = 30, pattern: str = "*") -> int:
    """Clean up old files in directory"""
    try:
        directory = Path(directory)
        if not directory.exists():
            return 0
        
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} files from {directory}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup directory {directory}: {e}")
        return 0


def copy_file_safely(source: Union[str, Path], destination: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely copy a file with verification"""
    try:
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            logger.error(f"Source file does not exist: {source}")
            return False
        
        if destination.exists() and not overwrite:
            logger.error(f"Destination exists and overwrite=False: {destination}")
            return False
        
        # Ensure destination directory exists
        ensure_directory(destination.parent)
        
        # Copy file
        shutil.copy2(source, destination)
        
        # Verify copy by comparing sizes
        if source.stat().st_size != destination.stat().st_size:
            logger.error(f"Copy verification failed: size mismatch")
            destination.unlink()  # Remove incomplete copy
            return False
        
        logger.info(f"Successfully copied {source} to {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy file {source} to {destination}: {e}")
        return False


def find_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = True, max_size_mb: int = None) -> List[Path]:
    """Find files matching criteria"""
    try:
        directory = Path(directory)
        if not directory.exists():
            return []
        
        files = []
        glob_pattern = f"**/{pattern}" if recursive else pattern
        
        for file_path in directory.glob(glob_pattern):
            if file_path.is_file():
                # Check size limit if specified
                if max_size_mb:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > max_size_mb:
                        continue
                
                files.append(file_path)
        
        return files
        
    except Exception as e:
        logger.error(f"Failed to find files in {directory}: {e}")
        return []


def get_directory_size(directory: Union[str, Path]) -> int:
    """Calculate total size of directory in bytes"""
    try:
        directory = Path(directory)
        total_size = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
        
    except Exception as e:
        logger.error(f"Failed to calculate directory size for {directory}: {e}")
        return 0


def create_backup(file_path: Union[str, Path], backup_dir: Union[str, Path] = None) -> Optional[Path]:
    """Create a timestamped backup of a file"""
    try:
        source = Path(file_path)
        if not source.exists():
            return None
        
        if backup_dir:
            backup_directory = Path(backup_dir)
        else:
            backup_directory = source.parent / "backups"
        
        ensure_directory(backup_directory)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"
        backup_path = backup_directory / backup_name
        
        if copy_file_safely(source, backup_path):
            return backup_path
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return None


class FileManager:
    """Class-based file manager with built-in safety features"""
    
    def __init__(self, base_directory: Union[str, Path] = None):
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.max_file_size_mb = 100  # Default limit
        self.allowed_extensions = None  # None = allow all
        
    def set_constraints(self, max_file_size_mb: int = None, allowed_extensions: List[str] = None):
        """Set file operation constraints"""
        if max_file_size_mb is not None:
            self.max_file_size_mb = max_file_size_mb
        if allowed_extensions is not None:
            self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
    
    def is_allowed_file(self, file_path: Union[str, Path]) -> bool:
        """Check if file meets constraints"""
        path = Path(file_path)
        
        # Check extension
        if self.allowed_extensions and path.suffix.lower() not in self.allowed_extensions:
            return False
        
        # Check size
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                return False
        
        return True
    
    def safe_path(self, relative_path: str) -> Path:
        """Resolve path safely within base directory"""
        path = self.base_directory / relative_path
        resolved = path.resolve()
        
        # Ensure path is within base directory
        if not str(resolved).startswith(str(self.base_directory.resolve())):
            raise ValueError("Path outside base directory")
        
        return resolved