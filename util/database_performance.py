"""
WestfallPersonalAssistant Database Performance Manager
Provides connection pooling, query optimization, and database performance features
"""

import sqlite3
import threading
import time
import queue
import logging
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from util.resource_manager import get_resource_manager
from util.error_handler import get_error_handler


@dataclass
class QueryStats:
    """Statistics for database queries"""
    query: str
    execution_time: float
    timestamp: float
    rows_affected: int
    error: Optional[str] = None


class ConnectionPool:
    """Thread-safe database connection pool"""
    
    def __init__(self, database_path: str, max_connections: int = 10, 
                 timeout: float = 30.0):
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        
        # Connection management
        self._connections = queue.Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = threading.RLock()
        self._stats = {
            'total_requests': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0
        }
        
        # Initialize pool with minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with initial connections"""
        # Create a few initial connections
        initial_count = min(2, self.max_connections)
        
        for _ in range(initial_count):
            try:
                conn = self._create_connection()
                if conn:
                    self._connections.put(conn, block=False)
            except Exception as e:
                logging.warning(f"Failed to create initial connection: {e}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection"""
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            
            # Enable foreign keys and WAL mode for better performance
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")  # 10MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            
            # Set row factory for better usability
            conn.row_factory = sqlite3.Row
            
            self._created_connections += 1
            return conn
            
        except Exception as e:
            logging.error(f"Failed to create database connection: {e}")
            self._stats['connection_errors'] += 1
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        connection = None
        try:
            with self._lock:
                self._stats['total_requests'] += 1
            
            # Try to get connection from pool
            try:
                connection = self._connections.get(block=True, timeout=5.0)
                with self._lock:
                    self._stats['pool_hits'] += 1
                    self._stats['active_connections'] += 1
                
            except queue.Empty:
                # Pool is empty, create new connection if allowed
                if self._created_connections < self.max_connections:
                    connection = self._create_connection()
                    if connection:
                        with self._lock:
                            self._stats['pool_misses'] += 1
                            self._stats['active_connections'] += 1
                    else:
                        raise Exception("Failed to create new connection")
                else:
                    raise Exception("Connection pool exhausted")
            
            yield connection
            
        finally:
            if connection:
                try:
                    # Return connection to pool if it's still valid
                    if self._is_connection_valid(connection):
                        self._connections.put(connection, block=False)
                    else:
                        # Connection is invalid, close it
                        connection.close()
                        self._created_connections -= 1
                except Exception as e:
                    logging.warning(f"Error returning connection to pool: {e}")
                    try:
                        connection.close()
                    except:
                        pass
                    self._created_connections -= 1
                
                with self._lock:
                    self._stats['active_connections'] -= 1
    
    def _is_connection_valid(self, connection: sqlite3.Connection) -> bool:
        """Check if connection is still valid"""
        try:
            connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self._connections.empty():
            try:
                conn = self._connections.get_nowait()
                conn.close()
            except queue.Empty:
                break
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")
        
        self._created_connections = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            return {
                'max_connections': self.max_connections,
                'created_connections': self._created_connections,
                'available_connections': self._connections.qsize(),
                'stats': self._stats.copy()
            }


class QueryOptimizer:
    """Optimizes database queries and tracks performance"""
    
    def __init__(self):
        self.query_stats = []
        self.max_stats = 1000  # Keep last 1000 queries
        self.slow_query_threshold = 1.0  # 1 second
        self._stats_lock = threading.RLock()
        
        # Common query optimizations
        self.index_suggestions = {}
        self.query_cache = {}
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query for potential optimizations"""
        query_lower = query.lower().strip()
        suggestions = []
        
        # Check for missing indexes
        if 'where' in query_lower and 'select' in query_lower:
            # Simple heuristic: look for WHERE clauses that might benefit from indexes
            if 'email' in query_lower or 'username' in query_lower:
                suggestions.append("Consider adding index on email/username columns")
            
            if 'created_at' in query_lower or 'updated_at' in query_lower:
                suggestions.append("Consider adding index on timestamp columns")
        
        # Check for inefficient patterns
        if 'select *' in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        if query_lower.count('join') > 3:
            suggestions.append("Complex query with multiple JOINs - consider optimization")
        
        return {
            'query': query,
            'suggestions': suggestions,
            'estimated_complexity': self._estimate_complexity(query_lower)
        }
    
    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity"""
        score = 0
        
        # Count operations that increase complexity
        score += query.count('join') * 2
        score += query.count('subquery') * 3
        score += query.count('group by') * 2
        score += query.count('order by') * 1
        score += query.count('having') * 2
        
        if score == 0:
            return "simple"
        elif score <= 3:
            return "moderate"
        elif score <= 6:
            return "complex"
        else:
            return "very_complex"
    
    def record_query(self, query: str, execution_time: float, 
                    rows_affected: int = 0, error: str = None):
        """Record query execution statistics"""
        with self._stats_lock:
            stat = QueryStats(
                query=query,
                execution_time=execution_time,
                timestamp=time.time(),
                rows_affected=rows_affected,
                error=error
            )
            
            self.query_stats.append(stat)
            
            # Keep only recent stats
            if len(self.query_stats) > self.max_stats:
                self.query_stats = self.query_stats[-self.max_stats:]
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logging.warning(f"Slow query ({execution_time:.3f}s): {query[:100]}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get query performance report"""
        with self._stats_lock:
            if not self.query_stats:
                return {"total_queries": 0}
            
            execution_times = [stat.execution_time for stat in self.query_stats]
            error_count = sum(1 for stat in self.query_stats if stat.error)
            
            # Find slowest queries
            slowest_queries = sorted(
                self.query_stats,
                key=lambda x: x.execution_time,
                reverse=True
            )[:10]
            
            return {
                "total_queries": len(self.query_stats),
                "average_time": sum(execution_times) / len(execution_times),
                "min_time": min(execution_times),
                "max_time": max(execution_times),
                "error_count": error_count,
                "error_rate": error_count / len(self.query_stats),
                "slow_queries": len([t for t in execution_times if t > self.slow_query_threshold]),
                "slowest_queries": [
                    {
                        "query": stat.query[:100],
                        "time": stat.execution_time,
                        "timestamp": stat.timestamp
                    } for stat in slowest_queries
                ]
            }


class DatabasePerformanceManager(QObject):
    """Main database performance management class"""
    
    # Signals
    slow_query_detected = pyqtSignal(str, float)  # query, execution_time
    connection_pool_exhausted = pyqtSignal()
    database_error = pyqtSignal(str)  # error_message
    
    def __init__(self, database_path: str, max_connections: int = 10):
        super().__init__()
        
        self.database_path = database_path
        self.connection_pool = ConnectionPool(database_path, max_connections)
        self.query_optimizer = QueryOptimizer()
        self.error_handler = get_error_handler()
        
        # Performance monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_performance)
        self.monitor_timer.start(60000)  # Monitor every minute
        
        # Optimization settings
        self.auto_optimize = True
        self.vacuum_interval_hours = 24
        self.last_vacuum = 0
        
    def execute_query(self, query: str, params: tuple = None, 
                     fetch_all: bool = True) -> Optional[Union[List, sqlite3.Row]]:
        """Execute a query with performance monitoring"""
        start_time = time.time()
        error = None
        rows_affected = 0
        result = None
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows_affected = cursor.rowcount
                
                # Fetch results for SELECT queries
                if query.strip().lower().startswith('select'):
                    if fetch_all:
                        result = cursor.fetchall()
                    else:
                        result = cursor.fetchone()
                else:
                    # For non-SELECT queries, commit the transaction
                    conn.commit()
                    result = rows_affected
                
        except Exception as e:
            error = str(e)
            self.error_handler.handle_database_error(e, f"Query execution failed: {query[:50]}")
            self.database_error.emit(error)
            
        finally:
            # Record performance statistics
            execution_time = time.time() - start_time
            self.query_optimizer.record_query(query, execution_time, rows_affected, error)
            
            # Emit signal for slow queries
            if execution_time > self.query_optimizer.slow_query_threshold:
                self.slow_query_detected.emit(query, execution_time)
        
        return result
    
    def execute_many(self, query: str, param_list: List[tuple]) -> int:
        """Execute a query with many parameter sets"""
        start_time = time.time()
        error = None
        total_affected = 0
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, param_list)
                total_affected = cursor.rowcount
                conn.commit()
                
        except Exception as e:
            error = str(e)
            self.error_handler.handle_database_error(e, f"Batch query execution failed")
            self.database_error.emit(error)
            
        finally:
            execution_time = time.time() - start_time
            batch_query = f"{query} [BATCH: {len(param_list)} items]"
            self.query_optimizer.record_query(batch_query, execution_time, total_affected, error)
        
        return total_affected
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.connection_pool.get_connection() as conn:
            try:
                conn.execute("BEGIN")
                yield conn
                conn.execute("COMMIT")
            except Exception as e:
                conn.execute("ROLLBACK")
                self.error_handler.handle_database_error(e, "Transaction rolled back")
                raise
    
    def optimize_database(self):
        """Perform database optimization"""
        try:
            with self.connection_pool.get_connection() as conn:
                # Update statistics
                conn.execute("ANALYZE")
                
                # Check if vacuum is needed
                current_time = time.time()
                if (current_time - self.last_vacuum) > (self.vacuum_interval_hours * 3600):
                    logging.info("Performing database vacuum...")
                    conn.execute("VACUUM")
                    self.last_vacuum = current_time
                
                # Optimize page cache
                conn.execute("PRAGMA optimize")
                
                logging.info("Database optimization completed")
                
        except Exception as e:
            self.error_handler.handle_database_error(e, "Database optimization failed")
    
    def create_indexes(self, index_definitions: List[str]):
        """Create database indexes for performance"""
        for index_def in index_definitions:
            try:
                with self.connection_pool.get_connection() as conn:
                    conn.execute(index_def)
                    logging.info(f"Created index: {index_def}")
            except Exception as e:
                logging.warning(f"Failed to create index: {index_def} - {e}")
    
    def get_suggested_indexes(self) -> List[str]:
        """Get suggested indexes based on query patterns"""
        # Analyze recent queries to suggest indexes
        suggestions = []
        
        # Common index suggestions based on typical patterns
        common_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id, key)",
        ]
        
        return common_indexes
    
    def monitor_performance(self):
        """Monitor database performance"""
        try:
            # Get connection pool stats
            pool_stats = self.connection_pool.get_stats()
            
            # Check for pool exhaustion
            if pool_stats['available_connections'] == 0:
                self.connection_pool_exhausted.emit()
            
            # Get query performance stats
            query_stats = self.query_optimizer.get_performance_report()
            
            # Log performance summary
            if query_stats.get('total_queries', 0) > 0:
                logging.debug(
                    f"DB Performance: {query_stats['total_queries']} queries, "
                    f"avg: {query_stats['average_time']:.3f}s, "
                    f"slow: {query_stats['slow_queries']}, "
                    f"errors: {query_stats['error_count']}"
                )
            
            # Auto-optimize if enabled
            if self.auto_optimize and query_stats.get('slow_queries', 0) > 10:
                self.optimize_database()
                
        except Exception as e:
            logging.warning(f"Performance monitoring error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'connection_pool': self.connection_pool.get_stats(),
            'query_performance': self.query_optimizer.get_performance_report(),
            'database_file_size': self._get_database_size(),
            'wal_file_size': self._get_wal_size(),
            'last_vacuum': self.last_vacuum,
            'auto_optimize_enabled': self.auto_optimize
        }
    
    def _get_database_size(self) -> int:
        """Get database file size in bytes"""
        try:
            return Path(self.database_path).stat().st_size
        except Exception:
            return 0
    
    def _get_wal_size(self) -> int:
        """Get WAL file size in bytes"""
        try:
            wal_path = Path(self.database_path + '-wal')
            return wal_path.stat().st_size if wal_path.exists() else 0
        except Exception:
            return 0
    
    def cleanup(self):
        """Cleanup database resources"""
        self.monitor_timer.stop()
        self.connection_pool.close_all()


# Decorators for database operations
def with_db_performance_monitoring(func):
    """Decorator to monitor database operation performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Log slow operations
                logging.warning(f"Slow database operation {func.__name__}: {execution_time:.3f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Database operation {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def db_transaction(func):
    """Decorator to wrap function in database transaction"""
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'db_manager') and self.db_manager:
            with self.db_manager.transaction() as conn:
                return func(self, conn, *args, **kwargs)
        else:
            return func(self, *args, **kwargs)
    
    return wrapper


# Connection string optimization
def optimize_connection_string(database_path: str) -> str:
    """Create optimized connection string with performance parameters"""
    params = [
        "journal_mode=WAL",
        "synchronous=NORMAL", 
        "cache_size=10000",
        "temp_store=MEMORY",
        "foreign_keys=ON"
    ]
    
    return f"{database_path}?" + "&".join(params)


# Global database performance manager
_db_performance_manager = None

def get_db_performance_manager(database_path: str = None) -> DatabasePerformanceManager:
    """Get or create global database performance manager"""
    global _db_performance_manager
    
    if _db_performance_manager is None and database_path:
        _db_performance_manager = DatabasePerformanceManager(database_path)
    
    return _db_performance_manager