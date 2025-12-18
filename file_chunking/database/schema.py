"""
Database Schema

SQLite schema for chunk metadata, file manifests, and download tracking.
"""

import aiosqlite
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Database file path (relative to file_chunking directory)
DB_PATH = Path(__file__).parent.parent / "data" / "file_chunking.db"

# Global database connection
_db: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get database connection (singleton)"""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def init_db() -> None:
    """
    Initialize database and create tables.

    Creates:
    - file_manifests: File metadata and chunk references
    - chunks: Individual chunk metadata and storage paths
    - downloads: Download progress tracking
    - library_cache: Library node cache tracking
    """
    global _db

    # Create data directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    _db = await aiosqlite.connect(str(DB_PATH))
    _db.row_factory = aiosqlite.Row

    # Enable foreign keys
    await _db.execute("PRAGMA foreign_keys = ON")

    # Create file_manifests table
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS file_manifests (
            file_hash TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            chunk_size INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL,
            chunk_hashes TEXT NOT NULL,  -- JSON array
            merkle_root TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT,
            tags TEXT,  -- JSON array
            description TEXT,
            is_complete INTEGER DEFAULT 0,  -- 1 if all chunks stored locally
            last_accessed TEXT
        )
    """)

    # Create chunks table
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_hash TEXT PRIMARY KEY,
            chunk_index INTEGER NOT NULL,
            chunk_size INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            status TEXT NOT NULL,  -- stored, requested, pending, verified
            storage_path TEXT,
            created_at TEXT NOT NULL,
            verified_at TEXT,
            FOREIGN KEY (file_hash) REFERENCES file_manifests(file_hash) ON DELETE CASCADE
        )
    """)

    # Create index on file_hash for faster queries
    await _db.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_file_hash
        ON chunks(file_hash)
    """)

    # Create index on status for faster queries
    await _db.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_status
        ON chunks(status)
    """)

    # Create downloads table
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            request_id TEXT PRIMARY KEY,
            file_hash TEXT NOT NULL,
            file_name TEXT,
            file_size INTEGER,
            status TEXT NOT NULL,  -- pending, requesting_manifest, downloading, etc.
            manifest_received INTEGER DEFAULT 0,
            total_chunks INTEGER DEFAULT 0,
            received_chunks INTEGER DEFAULT 0,
            bytes_received INTEGER DEFAULT 0,
            percent_complete REAL DEFAULT 0.0,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            error_message TEXT,
            output_path TEXT,
            FOREIGN KEY (file_hash) REFERENCES file_manifests(file_hash) ON DELETE CASCADE
        )
    """)

    # Create library_cache table (for library nodes)
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS library_cache (
            file_hash TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            access_count INTEGER DEFAULT 0,
            last_accessed TEXT,
            cached_at TEXT NOT NULL,
            tags TEXT,  -- JSON array
            priority_score REAL DEFAULT 0.0,  -- For cache eviction
            FOREIGN KEY (file_hash) REFERENCES file_manifests(file_hash) ON DELETE CASCADE
        )
    """)

    # Create index on priority_score for cache eviction
    await _db.execute("""
        CREATE INDEX IF NOT EXISTS idx_library_cache_priority
        ON library_cache(priority_score)
    """)

    await _db.commit()

    logger.info(f"Database initialized at {DB_PATH}")


async def close_db() -> None:
    """Close database connection"""
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


async def reset_db() -> None:
    """
    Reset database (drop all tables and recreate).

    WARNING: This deletes all data!
    """
    global _db

    if _db:
        await _db.execute("DROP TABLE IF EXISTS library_cache")
        await _db.execute("DROP TABLE IF EXISTS downloads")
        await _db.execute("DROP TABLE IF EXISTS chunks")
        await _db.execute("DROP TABLE IF EXISTS file_manifests")
        await _db.commit()

        logger.warning("Database tables dropped")

    # Recreate tables
    await init_db()
