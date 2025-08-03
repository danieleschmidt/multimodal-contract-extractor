"""Database connection management for contract processing system."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and provides connection pooling."""
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize database connection manager.
        
        Args:
            database_path: Path to SQLite database file. If None, uses in-memory database.
        """
        self.database_path = database_path or ":memory:"
        self._connection: Optional[sqlite3.Connection] = None
        self.is_initialized = False
        
        # Configure SQLite connection settings
        self.connection_settings = {
            'timeout': 30.0,
            'check_same_thread': False,
            'isolation_level': None,  # Autocommit mode
        }
    
    def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        if self.is_initialized:
            return
        
        logger.info(f"Initializing database at {self.database_path}")
        
        with self.get_connection() as conn:
            self._create_tables(conn)
            self._create_indexes(conn)
            conn.commit()
        
        self.is_initialized = True
        logger.info("Database initialization completed")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection as a context manager.
        
        Yields:
            SQLite connection object
        """
        conn = None
        try:
            conn = sqlite3.connect(self.database_path, **self.connection_settings)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            
            # Set SQLite pragmas for better performance and reliability
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.exception(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables for contract processing."""
        
        # Contracts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id TEXT PRIMARY KEY,
                title TEXT,
                contract_type TEXT NOT NULL,
                filename TEXT,
                pages INTEGER DEFAULT 0,
                file_size_bytes INTEGER,
                created_date TEXT,
                effective_date TEXT,
                expiration_date TEXT,
                processed_at TEXT NOT NULL,
                processing_time_seconds REAL DEFAULT 0.0,
                overall_confidence REAL DEFAULT 0.0,
                language TEXT DEFAULT 'en',
                jurisdiction TEXT,
                governing_law TEXT,
                key_terms TEXT,  -- JSON blob
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Contract parties table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contract_parties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                address TEXT,
                email TEXT,
                phone TEXT,
                entity_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contracts (id) ON DELETE CASCADE
            )
        """)
        
        # Legal clauses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS legal_clauses (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT,
                text TEXT NOT NULL,
                page INTEGER DEFAULT 1,
                coordinates TEXT,  -- JSON array [x1, y1, x2, y2]
                confidence REAL DEFAULT 0.0,
                key_terms TEXT,  -- JSON array
                entities TEXT,  -- JSON blob
                obligations TEXT,  -- JSON array
                conditions TEXT,  -- JSON array
                dates TEXT,  -- JSON array of ISO dates
                amounts TEXT,  -- JSON array
                section_number TEXT,
                parent_section TEXT,
                is_mandatory BOOLEAN DEFAULT 1,
                risk_level TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contracts (id) ON DELETE CASCADE
            )
        """)
        
        # Processing results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processing_results (
                id TEXT PRIMARY KEY,
                document_path TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                current_stage TEXT NOT NULL,
                validation_result TEXT,  -- JSON blob
                metrics TEXT,  -- JSON blob
                extracted_data TEXT,  -- JSON blob
                errors TEXT,  -- JSON array
                processing_config TEXT,  -- JSON blob
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # OCR cache table for performance optimization
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ocr_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                ocr_text TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                processing_time_seconds REAL DEFAULT 0.0,
                ocr_settings TEXT,  -- JSON blob of OCR settings used
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Metrics and analytics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processing_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_labels TEXT,  -- JSON blob for metric labels
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                contract_id TEXT,
                processing_result_id TEXT,
                FOREIGN KEY (contract_id) REFERENCES contracts (id),
                FOREIGN KEY (processing_result_id) REFERENCES processing_results (id)
            )
        """)
        
        # Configuration table for system settings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.debug("Database tables created successfully")
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for better query performance."""
        
        # Contracts indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_type ON contracts (contract_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_filename ON contracts (filename)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_processed_at ON contracts (processed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON contracts (created_at)")
        
        # Contract parties indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_parties_contract_id ON contract_parties (contract_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_parties_name ON contract_parties (name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_parties_role ON contract_parties (role)")
        
        # Legal clauses indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clauses_contract_id ON legal_clauses (contract_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clauses_type ON legal_clauses (type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clauses_page ON legal_clauses (page)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clauses_risk_level ON legal_clauses (risk_level)")
        
        # Processing results indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_status ON processing_results (status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_started_at ON processing_results (started_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_document_path ON processing_results (document_path)")
        
        # OCR cache indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_cache_hash ON ocr_cache (file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_cache_path ON ocr_cache (file_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_cache_accessed ON ocr_cache (last_accessed)")
        
        # Metrics indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON processing_metrics (metric_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON processing_metrics (timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_contract_id ON processing_metrics (contract_id)")
        
        logger.debug("Database indexes created successfully")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> list:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of query results as dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params or {})
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params or {})
            conn.commit()
            return cursor.rowcount
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health information."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Table row counts
                tables = ['contracts', 'contract_parties', 'legal_clauses', 
                         'processing_results', 'ocr_cache', 'processing_metrics']
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database size
                cursor = conn.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor = conn.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                stats['database_size_bytes'] = page_count * page_size
                
                # Performance stats
                cursor = conn.execute("PRAGMA cache_size")
                stats['cache_size'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.exception(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old records to maintain database performance.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            with self.get_connection() as conn:
                # Clean up old OCR cache entries
                cursor = conn.execute("""
                    DELETE FROM ocr_cache 
                    WHERE last_accessed < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                
                # Clean up old metrics (keep more detailed retention policy)
                cursor = conn.execute("""
                    DELETE FROM processing_metrics 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep * 2))  # Keep metrics longer
                
                deleted_count += cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old database records")
                return deleted_count
                
        except Exception as e:
            logger.exception(f"Error during database cleanup: {str(e)}")
            return 0
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where to save the backup
            
        Returns:
            True if backup was successful, False otherwise
        """
        try:
            if self.database_path == ":memory:":
                logger.warning("Cannot backup in-memory database")
                return False
            
            backup_path_obj = Path(backup_path)
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source_conn:
                backup_conn = sqlite3.connect(str(backup_path_obj))
                source_conn.backup(backup_conn)
                backup_conn.close()
            
            logger.info(f"Database backup created at {backup_path}")
            return True
            
        except Exception as e:
            logger.exception(f"Error creating database backup: {str(e)}")
            return False


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection(database_path: Optional[str] = None) -> DatabaseConnection:
    """
    Get the global database connection instance.
    
    Args:
        database_path: Path to database file (only used on first call)
        
    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection(database_path)
        _db_connection.initialize()
    
    return _db_connection