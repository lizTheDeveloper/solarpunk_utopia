"""
Discovery and Search System for Solarpunk Mesh Network

Implements TIER 1 discovery and search functionality:
- Index bundle publishing (InventoryIndex, ServiceIndex, KnowledgeIndex)
- Query/response protocol for distributed search
- Speculative index caching for offline discovery

This system enables users to find offers, needs, services, and knowledge
across a delay-tolerant mesh network without full data replication.
"""

from .models import *
from .services import *

__version__ = "1.0.0"
