import aiosqlite
import os
from pathlib import Path
from typing import Optional

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "dtn_bundles.db"

# Global connection pool
_db_connection: Optional[aiosqlite.Connection] = None


async def init_db() -> None:
    """Initialize the database and create tables"""
    global _db_connection

    # Ensure data directory exists
    DB_DIR.mkdir(exist_ok=True)

    # Create connection
    _db_connection = await aiosqlite.connect(str(DB_PATH))
    _db_connection.row_factory = aiosqlite.Row

    # Create bundles table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS bundles (
            bundleId TEXT PRIMARY KEY,
            queue TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            expiresAt TEXT NOT NULL,
            priority TEXT NOT NULL,
            audience TEXT NOT NULL,
            topic TEXT NOT NULL,
            tags TEXT NOT NULL,
            payloadType TEXT NOT NULL,
            payload TEXT NOT NULL,
            hopLimit INTEGER NOT NULL,
            hopCount INTEGER NOT NULL DEFAULT 0,
            receiptPolicy TEXT NOT NULL,
            signature TEXT NOT NULL,
            authorPublicKey TEXT NOT NULL,
            sizeBytes INTEGER NOT NULL,
            addedToQueueAt TEXT NOT NULL
        )
    """)

    # Create indexes for efficient queries
    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_queue ON bundles(queue)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_priority ON bundles(priority)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_expiresAt ON bundles(expiresAt)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_topic ON bundles(topic)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_queue_priority ON bundles(queue, priority)
    """)

    # Create metadata table for tracking cache size
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    await _db_connection.commit()


async def get_db() -> aiosqlite.Connection:
    """Get database connection"""
    global _db_connection
    if _db_connection is None:
        await init_db()
    return _db_connection


async def close_db() -> None:
    """Close database connection"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
