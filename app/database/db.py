import aiosqlite
import os
from pathlib import Path
from typing import Optional

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "dtn_bundles.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Global connection pool
_db_connection: Optional[aiosqlite.Connection] = None


async def _run_migrations(conn: aiosqlite.Connection) -> None:
    """Run database migrations"""
    # Create migrations tracking table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)

    # Get list of already applied migrations
    cursor = await conn.execute("SELECT filename FROM migrations")
    applied = {row[0] for row in await cursor.fetchall()}

    # Get all migration files
    if not MIGRATIONS_DIR.exists():
        return

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for migration_file in migration_files:
        if migration_file.name in applied:
            continue

        print(f"Applying migration: {migration_file.name}")

        # Read and execute migration
        sql = migration_file.read_text()
        await conn.executescript(sql)

        # Record migration
        await conn.execute(
            "INSERT INTO migrations (filename, applied_at) VALUES (?, datetime('now'))",
            (migration_file.name,)
        )
        await conn.commit()

        print(f"Applied migration: {migration_file.name}")


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

    # Create proposals table for agent proposal persistence
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            proposal_id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            proposal_type TEXT NOT NULL,
            title TEXT NOT NULL,
            explanation TEXT NOT NULL,
            inputs_used TEXT NOT NULL,
            constraints TEXT NOT NULL,
            data TEXT NOT NULL,
            requires_approval TEXT NOT NULL,
            approvals TEXT NOT NULL,
            approval_reasons TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            executed_at TEXT,
            bundle_id TEXT
        )
    """)

    # Create indexes for proposals
    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_proposal_status ON proposals(status)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_proposal_agent ON proposals(agent_name)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_proposal_type ON proposals(proposal_type)
    """)

    # Add community_id to proposals table (migration - will fail silently if column exists)
    try:
        await _db_connection.execute("""
            ALTER TABLE proposals ADD COLUMN community_id TEXT
        """)
    except:
        pass  # Column already exists

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_proposal_community ON proposals(community_id)
    """)

    # Create users table for authentication
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TEXT NOT NULL,
            last_login TEXT,
            settings TEXT DEFAULT '{}'
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
    """)

    # Create sessions table for authentication
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)
    """)

    # Create communities table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS communities (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            settings TEXT DEFAULT '{}',
            is_public INTEGER DEFAULT 1
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_communities_name ON communities(name)
    """)

    # Create community memberships table
    await _db_connection.execute("""
        CREATE TABLE IF NOT EXISTS community_memberships (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            community_id TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
            UNIQUE(user_id, community_id)
        )
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_memberships_user ON community_memberships(user_id)
    """)

    await _db_connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_memberships_community ON community_memberships(community_id)
    """)

    # Run migrations
    await _run_migrations(_db_connection)

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
