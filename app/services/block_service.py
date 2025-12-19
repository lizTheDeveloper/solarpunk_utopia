"""
Block Service - Business logic for blocking (GAP-107)

Provides helper functions for checking blocks across the application.
"""

import sqlite3
from typing import Optional
from app.database.block_repository import BlockRepository


class BlockService:
    """Service for checking and managing blocks"""

    def __init__(self, repo: Optional[BlockRepository] = None):
        if repo:
            self.repo = repo
        else:
            # Create default repository
            # TODO: Use proper DI for database connection
            conn = sqlite3.connect("data/solarpunk.db", check_same_thread=False)
            self.repo = BlockRepository(conn)

    def can_match(self, user_a: str, user_b: str) -> bool:
        """
        Check if two users can be matched.

        Returns False if either user has blocked the other.
        Silent failure - doesn't reveal who blocked whom.

        Args:
            user_a: First user ID
            user_b: Second user ID

        Returns:
            bool: True if match is allowed, False if blocked
        """
        return not self.repo.is_blocked(user_a, user_b)

    def can_message(self, sender_id: str, recipient_id: str) -> bool:
        """
        Check if sender can message recipient.

        Returns False if either has blocked the other.

        Args:
            sender_id: User attempting to send message
            recipient_id: Intended recipient

        Returns:
            bool: True if messaging is allowed, False if blocked
        """
        return not self.repo.is_blocked(sender_id, recipient_id)

    def filter_matches(self, user_id: str, potential_match_ids: list[str]) -> list[str]:
        """
        Filter out users who have blocked or been blocked by user_id.

        Args:
            user_id: User ID to check
            potential_match_ids: List of potential match user IDs

        Returns:
            list[str]: Filtered list excluding blocked users
        """
        blocked = set(self.repo.get_blocked_by_user(user_id))
        blocked_by = set(self.repo.get_blocks_against_user(user_id))
        excluded = blocked | blocked_by

        return [uid for uid in potential_match_ids if uid not in excluded]


# Global instance for easy access
# TODO: Replace with proper dependency injection
_block_service: Optional[BlockService] = None


def get_block_service() -> BlockService:
    """Get global block service instance"""
    global _block_service
    if _block_service is None:
        _block_service = BlockService()
    return _block_service


# Integration helper functions

async def verify_match_allowed(provider_id: str, receiver_id: str) -> bool:
    """
    Verify match is allowed (not blocked).

    Use this in match creation endpoints and agent proposals.

    Args:
        provider_id: User offering
        receiver_id: User requesting

    Returns:
        bool: True if match allowed

    Example:
        ```python
        # In mutual_aid_matchmaker.py:
        if not await verify_match_allowed(match.provider_id, match.receiver_id):
            logger.info(f"Match blocked by user preference")
            return None  # Silent failure
        ```
    """
    service = get_block_service()
    return service.can_match(provider_id, receiver_id)


async def verify_message_allowed(sender_id: str, recipient_id: str) -> bool:
    """
    Verify message is allowed (not blocked).

    Use this in message sending endpoints.

    Args:
        sender_id: User sending message
        recipient_id: Intended recipient

    Returns:
        bool: True if message allowed

    Example:
        ```python
        # In messages API:
        if not await verify_message_allowed(sender_id, recipient_id):
            raise HTTPException(403, "Cannot send message to this user")
        ```
    """
    service = get_block_service()
    return service.can_message(sender_id, recipient_id)
