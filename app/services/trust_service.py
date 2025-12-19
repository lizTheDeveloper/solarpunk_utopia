"""
Trust and Access Control Service

Implements audience-based access control for DTN bundles.
Enforces trust thresholds and keyring management.
"""

import logging
from typing import Set, Optional, Dict, Any
from pathlib import Path
import json

from ..models import Bundle
from ..models.priority import Audience


logger = logging.getLogger(__name__)


class TrustLevel:
    """Trust level constants"""
    UNKNOWN = 0
    KNOWN = 1
    TRUSTED = 2
    VERIFIED = 3


class TrustService:
    """
    Service for managing trust relationships and access control.

    Implements:
    - Keyring management (public keys of trusted nodes)
    - Audience-based access control
    - Trust threshold enforcement
    """

    def __init__(self, trust_store_path: Optional[Path] = None):
        """
        Initialize trust service.

        Args:
            trust_store_path: Path to trust store file (JSON)
        """
        if trust_store_path is None:
            trust_store_path = Path(__file__).parent.parent.parent / "data" / "trust_store.json"

        self.trust_store_path = trust_store_path
        self.trust_store_path.parent.mkdir(parents=True, exist_ok=True)

        # Load trust store
        self.keyrings: Dict[str, Set[str]] = {
            "public": set(),  # All known public keys
            "local": set(),  # Local commune members
            "trusted": set(),  # Explicitly trusted entities
            "verified": set()  # Cryptographically verified identities
        }
        self.trust_levels: Dict[str, int] = {}  # public_key -> trust_level

        self._load_trust_store()

    def _load_trust_store(self):
        """Load trust store from disk"""
        if not self.trust_store_path.exists():
            logger.info("No trust store found, starting fresh")
            return

        try:
            with open(self.trust_store_path, 'r') as f:
                data = json.load(f)

            # Load keyrings
            for ring_name, keys in data.get("keyrings", {}).items():
                self.keyrings[ring_name] = set(keys)

            # Load trust levels
            self.trust_levels = data.get("trust_levels", {})

            logger.info(f"Loaded trust store: {len(self.trust_levels)} entries")

        except Exception as e:
            logger.error(f"Failed to load trust store: {e}")

    def _save_trust_store(self):
        """Save trust store to disk"""
        try:
            data = {
                "keyrings": {
                    name: list(keys) for name, keys in self.keyrings.items()
                },
                "trust_levels": self.trust_levels
            }

            with open(self.trust_store_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Trust store saved")

        except Exception as e:
            logger.error(f"Failed to save trust store: {e}")

    def add_to_keyring(self, public_key: str, keyring: str = "public", trust_level: int = TrustLevel.KNOWN):
        """
        Add a public key to a keyring.

        Args:
            public_key: Public key to add (PEM format or fingerprint)
            keyring: Which keyring to add to (public, local, trusted, verified)
            trust_level: Trust level to assign
        """
        if keyring not in self.keyrings:
            logger.warning(f"Unknown keyring: {keyring}, using 'public'")
            keyring = "public"

        self.keyrings[keyring].add(public_key)
        self.trust_levels[public_key] = trust_level

        self._save_trust_store()
        logger.info(f"Added {public_key[:20]}... to {keyring} keyring with trust level {trust_level}")

    def remove_from_keyring(self, public_key: str, keyring: str):
        """
        Remove a public key from a keyring.

        Args:
            public_key: Public key to remove
            keyring: Which keyring to remove from
        """
        if keyring in self.keyrings:
            self.keyrings[keyring].discard(public_key)
            self._save_trust_store()
            logger.info(f"Removed {public_key[:20]}... from {keyring} keyring")

    def get_trust_level(self, public_key: str) -> int:
        """
        Get trust level for a public key.

        Args:
            public_key: Public key to check

        Returns:
            Trust level (0-3)
        """
        return self.trust_levels.get(public_key, TrustLevel.UNKNOWN)

    def is_in_keyring(self, public_key: str, keyring: str) -> bool:
        """
        Check if a public key is in a specific keyring.

        Args:
            public_key: Public key to check
            keyring: Keyring name

        Returns:
            True if key is in keyring
        """
        return public_key in self.keyrings.get(keyring, set())

    def can_access_bundle(self, bundle: Bundle, requester_public_key: str) -> tuple[bool, Optional[str]]:
        """
        Check if a requester can access a bundle based on audience and trust.

        Args:
            bundle: Bundle to check access for
            requester_public_key: Public key of requesting entity

        Returns:
            (can_access, reason) tuple
        """
        audience = bundle.audience
        author_key = bundle.authorPublicKey
        trust_level = self.get_trust_level(requester_public_key)

        # PUBLIC: Anyone can access
        if audience == Audience.PUBLIC:
            return True, "Public audience"

        # Author can always access their own bundles
        if requester_public_key == author_key:
            return True, "Bundle author"

        # LOCAL: Must be in local keyring
        if audience == Audience.LOCAL:
            if self.is_in_keyring(requester_public_key, "local"):
                return True, "Local commune member"
            return False, "Not a local commune member"

        # TRUSTED: Must be in trusted keyring or higher
        if audience == Audience.TRUSTED:
            if self.is_in_keyring(requester_public_key, "trusted"):
                return True, "Trusted keyring member"
            if self.is_in_keyring(requester_public_key, "verified"):
                return True, "Verified keyring member"
            if trust_level >= TrustLevel.TRUSTED:
                return True, f"Trust level {trust_level}"
            return False, "Not trusted"

        # PRIVATE: Must be in verified keyring or explicitly trusted
        if audience == Audience.PRIVATE:
            if self.is_in_keyring(requester_public_key, "verified"):
                return True, "Verified keyring member"
            if trust_level >= TrustLevel.VERIFIED:
                return True, f"Trust level {trust_level}"
            return False, "Insufficient trust for private bundle"

        # Default deny
        return False, f"Unknown audience: {audience}"

    def filter_bundles_by_access(self, bundles: list[Bundle], requester_public_key: str) -> list[Bundle]:
        """
        Filter a list of bundles to only those the requester can access.

        Args:
            bundles: List of bundles to filter
            requester_public_key: Public key of requesting entity

        Returns:
            Filtered list of accessible bundles
        """
        accessible = []
        denied_count = 0

        for bundle in bundles:
            can_access, reason = self.can_access_bundle(bundle, requester_public_key)
            if can_access:
                accessible.append(bundle)
            else:
                denied_count += 1
                logger.debug(f"Access denied to bundle {bundle.bundleId}: {reason}")

        if denied_count > 0:
            logger.info(f"Filtered {denied_count} bundles due to access control")

        return accessible

    def enforce_bundle_creation_policy(self, audience: Audience, creator_public_key: str) -> tuple[bool, Optional[str]]:
        """
        Enforce policy on who can create bundles with specific audiences.

        Args:
            audience: Audience level being requested
            creator_public_key: Public key of bundle creator

        Returns:
            (allowed, reason) tuple
        """
        trust_level = self.get_trust_level(creator_public_key)

        # PUBLIC and LOCAL: Anyone can create
        if audience in [Audience.PUBLIC, Audience.LOCAL]:
            return True, "Allowed"

        # TRUSTED: Must be in local or trusted keyring
        if audience == Audience.TRUSTED:
            if self.is_in_keyring(creator_public_key, "local"):
                return True, "Local member"
            if self.is_in_keyring(creator_public_key, "trusted"):
                return True, "Trusted member"
            if trust_level >= TrustLevel.TRUSTED:
                return True, f"Trust level {trust_level}"
            return False, "Insufficient trust to create TRUSTED bundles"

        # PRIVATE: Must be verified
        if audience == Audience.PRIVATE:
            if self.is_in_keyring(creator_public_key, "verified"):
                return True, "Verified member"
            if trust_level >= TrustLevel.VERIFIED:
                return True, f"Trust level {trust_level}"
            return False, "Must be verified to create PRIVATE bundles"

        return True, "Default allow"

    def get_trust_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the trust store.

        Returns:
            Statistics dictionary
        """
        return {
            "keyrings": {
                name: len(keys) for name, keys in self.keyrings.items()
            },
            "total_known_keys": len(self.trust_levels),
            "trust_distribution": {
                "unknown": sum(1 for lvl in self.trust_levels.values() if lvl == TrustLevel.UNKNOWN),
                "known": sum(1 for lvl in self.trust_levels.values() if lvl == TrustLevel.KNOWN),
                "trusted": sum(1 for lvl in self.trust_levels.values() if lvl == TrustLevel.TRUSTED),
                "verified": sum(1 for lvl in self.trust_levels.values() if lvl == TrustLevel.VERIFIED)
            }
        }

    def import_commune_keyring(self, keyring_data: Dict[str, Any]):
        """
        Import a keyring from another commune.

        Args:
            keyring_data: Keyring data to import
        """
        imported_count = 0

        for public_key in keyring_data.get("members", []):
            if public_key not in self.trust_levels:
                self.add_to_keyring(
                    public_key,
                    keyring="public",
                    trust_level=TrustLevel.KNOWN
                )
                imported_count += 1

        logger.info(f"Imported {imported_count} keys from commune keyring")

    def export_commune_keyring(self, keyring: str = "local") -> Dict[str, Any]:
        """
        Export a keyring for sharing with other communes.

        Args:
            keyring: Which keyring to export

        Returns:
            Exportable keyring data
        """
        return {
            "keyring": keyring,
            "members": list(self.keyrings.get(keyring, set())),
            "exported_at": __import__("datetime").datetime.now(timezone.utc).isoformat()
        }
