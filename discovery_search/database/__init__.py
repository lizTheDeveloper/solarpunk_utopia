"""
Database layer for Discovery and Search System
"""

from .db import init_discovery_db, get_discovery_db, close_discovery_db
from .cache_db import IndexCacheDB

__all__ = [
    "init_discovery_db",
    "get_discovery_db",
    "close_discovery_db",
    "IndexCacheDB",
]
