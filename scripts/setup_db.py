"""
Database Setup Script - Initialize database and create tables
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Initialize database"""
    logger.info("Starting database setup...")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    try:
        # Initialize database (creates tables from schema.sql)
        await db_manager.initialize()
        
        logger.info("✓ Database initialized successfully")
        logger.info(f"✓ Database location: {db_manager.db_path}")
        
        # Verify tables were created
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = await cursor.fetchall()
            
            logger.info(f"✓ Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        logger.info("\n✅ Database setup complete!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
