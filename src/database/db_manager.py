"""
Database Manager - SQLite Connection and Initialization
Handles database setup, connections, and migrations
"""
import aiosqlite
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and initialization"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file (defaults to settings.database_path)
        """
        self.db_path = db_path or settings.database_path
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Initialize database and create tables from schema"""
        logger.info(f"Initializing database at {self.db_path}")
        
        # Ensure database directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection and execute schema
        async with aiosqlite.connect(self.db_path) as db:
            # Read schema file
            schema_path = Path(__file__).parent / "schema.sql"
            
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema (split by semicolon for multiple statements)
                await db.executescript(schema_sql)
                await db.commit()
                logger.info("Database schema initialized successfully")
            else:
                logger.warning(f"Schema file not found at {schema_path}")
        
        logger.info("Database initialization complete")
    
    async def connect(self) -> aiosqlite.Connection:
        """
        Get database connection
        
        Returns:
            Active database connection
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager for database connections
        
        Usage:
            async with db_manager.get_connection() as db:
                await db.execute(...)
        """
        db = await aiosqlite.connect(self.db_path)
        db.row_factory = aiosqlite.Row
        try:
            yield db
        finally:
            await db.close()
    
    async def execute_query(self, query: str, parameters: tuple = ()):
        """
        Execute a query and return results
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            List of rows
        """
        async with self.get_connection() as db:
            async with db.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def execute_insert(self, query: str, parameters: tuple = ()):
        """
        Execute an insert query and return last row id
        
        Args:
            query: SQL insert query
            parameters: Query parameters
            
        Returns:
            Last inserted row id
        """
        async with self.get_connection() as db:
            cursor = await db.execute(query, parameters)
            await db.commit()
            return cursor.lastrowid
    
    async def execute_update(self, query: str, parameters: tuple = ()):
        """
        Execute an update/delete query
        
        Args:
            query: SQL update/delete query
            parameters: Query parameters
            
        Returns:
            Number of affected rows
        """
        async with self.get_connection() as db:
            cursor = await db.execute(query, parameters)
            await db.commit()
            return cursor.rowcount


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager
