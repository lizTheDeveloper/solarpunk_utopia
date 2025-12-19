"""
Index Builder Service

Generates index bundles from local ValueFlows data.
Queries VF database for listings, agents, resources, protocols, and lessons.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional

# Add ValueFlows node to path
vf_path = Path(__file__).parent.parent.parent / "valueflows_node"
sys.path.insert(0, str(vf_path))

from ..models import (
    IndexType,
    InventoryIndex,
    InventoryIndexEntry,
    ServiceIndex,
    ServiceIndexEntry,
    KnowledgeIndex,
    KnowledgeIndexEntry,
)


class IndexBuilder:
    """
    Builds index bundles from local ValueFlows database.

    Queries VF data and generates compact indexes for publishing.
    """

    def __init__(self, node_id: str, node_public_key: str):
        """
        Initialize index builder.

        Args:
            node_id: This node's identifier (public key fingerprint)
            node_public_key: This node's full public key
        """
        self.node_id = node_id
        self.node_public_key = node_public_key

    async def build_inventory_index(
        self,
        ttl_days: int = 3
    ) -> InventoryIndex:
        """
        Build inventory index from local listings.

        Queries VF database for active offers and needs.

        Args:
            ttl_days: Time-to-live for this index in days

        Returns:
            InventoryIndex ready for publishing
        """
        from valueflows_node.app.database import get_database
        from valueflows_node.app.repositories.vf.listing_repo import ListingRepository
        from valueflows_node.app.repositories.vf.resource_spec_repo import ResourceSpecRepository
        from valueflows_node.app.repositories.vf.agent_repo import AgentRepository
        from valueflows_node.app.repositories.vf.location_repo import LocationRepository

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl_days)

        entries: List[InventoryIndexEntry] = []
        categories = set()

        try:
            # Connect to VF database
            db = get_database()
            db.connect()

            listing_repo = ListingRepository(db.conn)
            resource_spec_repo = ResourceSpecRepository(db.conn)
            agent_repo = AgentRepository(db.conn)
            location_repo = LocationRepository(db.conn)

            # Get all active listings
            active_listings = listing_repo.find_by_status("active", limit=1000)

            for listing in active_listings:
                # Get resource spec
                resource_spec = resource_spec_repo.find_by_id(listing.resource_spec_id)
                if not resource_spec:
                    continue

                # Get agent
                agent = agent_repo.find_by_id(listing.agent_id)

                # Get location (if any)
                location = None
                location_name = None
                if listing.location_id:
                    location = location_repo.find_by_id(listing.location_id)
                    if location:
                        location_name = location.name

                # Create index entry
                entry = InventoryIndexEntry(
                    listing_id=listing.id,
                    listing_type=listing.listing_type.value,
                    resource_spec_id=resource_spec.id,
                    resource_name=resource_spec.name,
                    category=resource_spec.category.value,
                    subcategory=resource_spec.subcategory,
                    quantity=listing.quantity,
                    unit=listing.unit,
                    location_id=listing.location_id,
                    location_name=location_name,
                    available_from=listing.available_from,
                    available_until=listing.available_until,
                    title=listing.title,
                    description=listing.description,
                    agent_id=listing.agent_id,
                    agent_name=agent.name if agent else None,
                    bundle_id=None,  # Will be set when listing is published as bundle
                )

                entries.append(entry)
                categories.add(resource_spec.category.value)

            db.close()

        except Exception as e:
            print(f"Error building inventory index: {e}")
            # Continue with empty index rather than failing

        # Count offers and needs
        total_offers = sum(1 for e in entries if e.listing_type == "offer")
        total_needs = sum(1 for e in entries if e.listing_type == "need")

        return InventoryIndex(
            node_id=self.node_id,
            node_public_key=self.node_public_key,
            entries=entries,
            generated_at=now,
            expires_at=expires_at,
            total_offers=total_offers,
            total_needs=total_needs,
            categories=sorted(list(categories)),
        )

    async def build_service_index(
        self,
        ttl_days: int = 7
    ) -> ServiceIndex:
        """
        Build service index from skill/labor listings.

        Args:
            ttl_days: Time-to-live for this index in days

        Returns:
            ServiceIndex ready for publishing
        """
        from valueflows_node.app.database import get_database
        from valueflows_node.app.repositories.vf.listing_repo import ListingRepository
        from valueflows_node.app.repositories.vf.resource_spec_repo import ResourceSpecRepository
        from valueflows_node.app.repositories.vf.agent_repo import AgentRepository
        from valueflows_node.app.repositories.vf.location_repo import LocationRepository
        from valueflows_node.app.models.vf.resource_spec import ResourceCategory

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl_days)

        entries: List[ServiceIndexEntry] = []
        service_types = set()

        try:
            db = get_database()
            db.connect()

            listing_repo = ListingRepository(db.conn)
            resource_spec_repo = ResourceSpecRepository(db.conn)
            agent_repo = AgentRepository(db.conn)
            location_repo = LocationRepository(db.conn)

            # Get skill and labor listings
            skill_listings = listing_repo.find_offers(
                category=ResourceCategory.SKILLS,
                status="active",
                limit=1000
            )
            labor_listings = listing_repo.find_offers(
                category=ResourceCategory.LABOR,
                status="active",
                limit=1000
            )

            all_service_listings = skill_listings + labor_listings

            for listing in all_service_listings:
                resource_spec = resource_spec_repo.find_by_id(listing.resource_spec_id)
                if not resource_spec:
                    continue

                agent = agent_repo.find_by_id(listing.agent_id)

                location_name = None
                if listing.location_id:
                    location = location_repo.find_by_id(listing.location_id)
                    if location:
                        location_name = location.name

                # Create service entry
                entry = ServiceIndexEntry(
                    listing_id=listing.id,
                    service_type=resource_spec.name.lower(),
                    skill_name=resource_spec.name,
                    category=resource_spec.category.value,
                    agent_id=listing.agent_id,
                    agent_name=agent.name if agent else None,
                    available_from=listing.available_from,
                    available_until=listing.available_until,
                    hours_available=listing.quantity,
                    location_id=listing.location_id,
                    location_name=location_name,
                    title=listing.title,
                    description=listing.description,
                    bundle_id=None,
                )

                entries.append(entry)
                service_types.add(resource_spec.name.lower())

            db.close()

        except Exception as e:
            print(f"Error building service index: {e}")

        return ServiceIndex(
            node_id=self.node_id,
            node_public_key=self.node_public_key,
            entries=entries,
            generated_at=now,
            expires_at=expires_at,
            total_services=len(entries),
            service_types=sorted(list(service_types)),
        )

    async def build_knowledge_index(
        self,
        ttl_days: int = 30
    ) -> KnowledgeIndex:
        """
        Build knowledge index from protocols, lessons, and cached files.

        Args:
            ttl_days: Time-to-live for this index in days

        Returns:
            KnowledgeIndex ready for publishing
        """
        from valueflows_node.app.database import get_database
        from valueflows_node.app.repositories.vf.protocol_repo import ProtocolRepository
        from valueflows_node.app.repositories.vf.lesson_repo import LessonRepository

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl_days)

        entries: List[KnowledgeIndexEntry] = []
        categories = set()
        total_protocols = 0
        total_lessons = 0
        total_files = 0

        try:
            db = get_database()
            db.connect()

            protocol_repo = ProtocolRepository(db.conn)
            lesson_repo = LessonRepository(db.conn)

            # Get all protocols
            protocols = protocol_repo.find_all(limit=1000)
            for protocol in protocols:
                entry = KnowledgeIndexEntry(
                    content_id=protocol.id,
                    content_type="protocol",
                    title=protocol.name,
                    category=protocol.category if hasattr(protocol, 'category') else "other",
                    description=protocol.description if hasattr(protocol, 'description') else None,
                    author_id=protocol.author if hasattr(protocol, 'author') else None,
                    tags=[],
                    created_at=protocol.created_at if hasattr(protocol, 'created_at') else None,
                )
                entries.append(entry)
                if hasattr(protocol, 'category'):
                    categories.add(protocol.category)
                total_protocols += 1

            # Get all lessons
            lessons = lesson_repo.find_all(limit=1000)
            for lesson in lessons:
                entry = KnowledgeIndexEntry(
                    content_id=lesson.id,
                    content_type="lesson",
                    title=lesson.title,
                    category=lesson.category if hasattr(lesson, 'category') else "other",
                    description=lesson.content[:200] if hasattr(lesson, 'content') and lesson.content else None,
                    author_id=lesson.author if hasattr(lesson, 'author') else None,
                    tags=[],
                    created_at=lesson.created_at if hasattr(lesson, 'created_at') else None,
                )
                entries.append(entry)
                if hasattr(lesson, 'category'):
                    categories.add(lesson.category)
                total_lessons += 1

            db.close()

        except Exception as e:
            print(f"Error building knowledge index: {e}")

        return KnowledgeIndex(
            node_id=self.node_id,
            node_public_key=self.node_public_key,
            entries=entries,
            generated_at=now,
            expires_at=expires_at,
            total_protocols=total_protocols,
            total_lessons=total_lessons,
            total_files=total_files,
            categories=sorted(list(categories)),
        )
