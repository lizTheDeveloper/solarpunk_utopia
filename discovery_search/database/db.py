"""
Database initialization for Discovery and Search System

Creates tables for:
- Cached indexes from peer nodes
- Query history
- Response tracking
"""

import aiosqlite
from pathlib import Path
from typing import Optional

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "discovery_search.db"

# Global connection pool
_db_connection: Optional[aiosqlite.Connection] = None


async def init_discovery_db() -> None:
    """Initialize the discovery database and create tables"""
    global _db_connection

    # Ensure data directory exists
    DB_DIR.mkdir(exist_ok=True)

    # Create connection
    _db_connection = await aiosqlite.connect(str(DB_PATH))
    _db_connection.row_factory = aiosqlite.Row

    # Create cached_indexes table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS cached_indexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_type TEXT NOT NULL,
            node_id TEXT NOT NULL,
            node_public_key TEXT NOT NULL,
            bundle_id TEXT NOT NULL,

            -- Index content (JSON)
            index_data TEXT NOT NULL,

            -- Timestamps
            generated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            cached_at TEXT NOT NULL,

            -- Statistics
            entry_count INTEGER NOT NULL,
            size_bytes INTEGER NOT NULL,

            -- Version
            version INTEGER DEFAULT 1,

            UNIQUE(node_id, index_type)
        )
    """)

    # Create indexes for efficient queries
    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_cached_indexes_node_type
        ON cached_indexes(node_id, index_type)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_cached_indexes_expires
        ON cached_indexes(expires_at)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_cached_indexes_type
        ON cached_indexes(index_type)
    """)

    # Create query_history table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id TEXT UNIQUE NOT NULL,
            query_string TEXT NOT NULL,
            query_data TEXT NOT NULL,

            -- Requester
            requester_node_id TEXT NOT NULL,
            requester_agent_id TEXT,

            -- Timestamps
            created_at TEXT NOT NULL,
            response_deadline TEXT NOT NULL,

            -- Status
            status TEXT NOT NULL DEFAULT 'pending',
            responses_received INTEGER DEFAULT 0,

            -- Results
            total_results INTEGER DEFAULT 0
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_history_query_id
        ON query_history(query_id)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_history_status
        ON query_history(status)
    """)

    # Create response_tracking table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS response_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id TEXT UNIQUE NOT NULL,
            query_id TEXT NOT NULL,

            -- Responder
            responder_node_id TEXT NOT NULL,

            -- Response data (JSON)
            response_data TEXT NOT NULL,

            -- Timestamps
            created_at TEXT NOT NULL,
            received_at TEXT NOT NULL,

            -- Results
            result_count INTEGER NOT NULL,
            local_results INTEGER DEFAULT 0,
            cached_results INTEGER DEFAULT 0,

            FOREIGN KEY (query_id) REFERENCES query_history(query_id)
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_response_tracking_query_id
        ON response_tracking(query_id)
    """)

    # Create index_publish_schedule table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS index_publish_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_type TEXT UNIQUE NOT NULL,

            -- Schedule
            interval_minutes INTEGER NOT NULL,
            last_published_at TEXT,
            next_publish_at TEXT,

            -- Status
            enabled INTEGER DEFAULT 1,

            -- Statistics
            total_publishes INTEGER DEFAULT 0,
            last_entry_count INTEGER DEFAULT 0,
            last_bundle_id TEXT
        )
    """)

    # Insert default schedules
    await _db_connection.execute("""
        INSERT OR IGNORE INTO index_publish_schedule (index_type, interval_minutes)
        VALUES
            ('inventory', 10),
            ('service', 30),
            ('knowledge', 60)
    """)

    await _db_connection.commit()


async def get_discovery_db() -> aiosqlite.Connection:
    """Get database connection"""
    global _db_connection
    if _db_connection is None:
        await init_discovery_db()
    return _db_connection


async def close_discovery_db() -> None:
    """Close database connection"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
