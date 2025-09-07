"""
WestfallPersonalAssistant Error Handler
Provides consistent error handling across the application
"""

import sys
import traceback
import logging
import os
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt
import sqlite3
import requests

class ErrorHandler:
    """Global error handler with consistent error management"""
    
    _instance = None
    
    def __new__(cls, log_dir='logs', parent=None):
        """Singleton pattern to ensure only one error handler instance"""
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir='logs', parent=None):
        """Initialize error handler with logging"""
        if self._initialized:
            return
            
        self.log_dir = log_dir
        self.parent = parent
        self.enable_logging()
        
        # Store original excepthook
        self.original_excepthook = sys.excepthook
        
        # Set global exception handler
        sys.excepthook = self.handle_exception
        
        # Initialize counters for error tracking
        self.error_counts = {
            'network': 0,
            'database': 0,
            'file': 0,
            'ui': 0,
            'general': 0
        }
        
        self._initialized = True
    
    def enable_logging(self):
        """Set up logging configuration"""
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create a log file for this session
        log_file = os.path.join(self.log_dir, f'error_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Configure logging
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        # Don't log keyboard interrupts
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the error
        logging.error("Uncaught exception", 
                     exc_info=(exc_type, exc_value, exc_traceback))
        
        # Format traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Show error dialog if in GUI mode
        try:
            app = QApplication.instance()
            if app:
                self.error_counts['general'] += 1
                QMessageBox.critical(self.parent, "Unhandled Error", 
                                   f"An unexpected error occurred:\n\n{str(exc_value)}\n\n"
                                   f"This error has been logged to:\n{self.log_dir}")
        except Exception:
            pass
        
        # Call original handler
        self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def handle_network_error(self, error, message=None, parent=None, retry_func=None):
        """Handle network errors consistently"""
        if message is None:
            message = "A network error occurred"
        
        # Get actual parent window
        parent = parent or self.parent
        
        # Log the error
        logging.error(f"Network error: {error}")
        self.error_counts['network'] += 1
        
        # Show error dialog with retry option if provided
        if retry_func:
            retry = QMessageBox.warning(parent, "Network Error", 
                                      f"{message}:\n{str(error)}\n\nWould you like to retry?",
                                      QMessageBox.Retry | QMessageBox.Cancel)
            if retry == QMessageBox.Retry:
                return retry_func()
        else:
            QMessageBox.warning(parent, "Network Error", 
                              f"{message}:\n{str(error)}")
        
        return None
    
    def handle_database_error(self, error, message=None, parent=None, critical=False):
        """Handle database errors consistently"""
        if message is None:
            message = "A database error occurred"
        
        # Get actual parent window
        parent = parent or self.parent
        
        # Log the error
        logging.error(f"Database error: {error}")
        self.error_counts['database'] += 1
        
        # Show appropriate message box
        if critical:
            return QMessageBox.critical(parent, "Database Error", 
                                     f"{message}:\n{str(error)}")
        else:
            return QMessageBox.warning(parent, "Database Error", 
                                    f"{message}:\n{str(error)}")
    
    def handle_file_error(self, error, message=None, parent=None, file_path=None):
        """Handle file operation errors consistently"""
        if message is None:
            message = "A file operation error occurred"
        
        # Add file path to message if provided
        if file_path:
            message = f"{message}\nFile: {file_path}"
        
        # Get actual parent window
        parent = parent or self.parent
        
        # Log the error
        logging.error(f"File error: {error}")
        self.error_counts['file'] += 1
        
        # Show error dialog
        return QMessageBox.warning(parent, "File Error", 
                                f"{message}:\n{str(error)}")
    
    def handle_ui_error(self, error, message=None, parent=None):
        """Handle UI-related errors consistently"""
        if message is None:
            message = "A user interface error occurred"
        
        # Get actual parent window
        parent = parent or self.parent
        
        # Log the error
        logging.error(f"UI error: {error}")
        self.error_counts['ui'] += 1
        
        # Show error dialog
        return QMessageBox.information(parent, "Interface Error", 
                                     f"{message}:\n{str(error)}")
    
    def show_error_message(self, message, title="Error", parent=None):
        """Show a generic error message"""
        # Get actual parent window
        parent = parent or self.parent
        
        # Show error dialog
        return QMessageBox.warning(parent, title, message)
    
    def show_success_message(self, message, title="Success", parent=None):
        """Show a success message"""
        # Get actual parent window
        parent = parent or self.parent
        
        # Show success dialog
        return QMessageBox.information(parent, title, message)
    
    def show_warning_message(self, message, title="Warning", parent=None):
        """Show a warning message"""
        # Get actual parent window
        parent = parent or self.parent
        
        # Show warning dialog
        return QMessageBox.warning(parent, title, message)
    
    def get_error_statistics(self):
        """Get statistics about errors that occurred"""
        return {
            'counts': self.error_counts,
            'total': sum(self.error_counts.values())
        }
    
    def reset_error_counts(self):
        """Reset error counters"""
        for key in self.error_counts:
            self.error_counts[key] = 0
    
    @staticmethod
    def is_network_error(exception):
        """Check if an exception is a network error"""
        return (isinstance(exception, requests.exceptions.RequestException) or
                (isinstance(exception, OSError) and exception.errno in (104, 110, 111)))
    
    @staticmethod
    def is_database_error(exception):
        """Check if an exception is a database error"""
        return isinstance(exception, sqlite3.Error)
    
    @staticmethod
    def is_file_error(exception):
        """Check if an exception is a file error"""
        return (isinstance(exception, (IOError, FileNotFoundError, PermissionError)) or
                (isinstance(exception, OSError) and exception.errno in (2, 13, 22)))

# Global function to get the error handler instance
def get_error_handler(parent=None):
    """Get or create the global error handler instance"""
    return ErrorHandler(parent=parent)