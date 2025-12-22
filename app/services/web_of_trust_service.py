"""Trust Score Computation Service

Implements the Web of Trust algorithm:
1. Genesis nodes have 1.0 trust
2. Trust attenuates by 20% per hop (multiply by 0.8)
3. Multiple vouch chains -> use highest scoring path
4. Revocation causes cascade with reduced impact
"""
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta, UTC
from app.models.vouch import (
    TrustScore,
    Vouch,
    TRUST_ATTENUATION,
    MAX_VOUCH_DISTANCE,
    TRUST_THRESHOLDS,
)
from app.database.vouch_repository import VouchRepository


class WebOfTrustService:
    """Service for computing and managing trust scores."""

    def __init__(self, vouch_repo: VouchRepository):
        self.vouch_repo = vouch_repo

    def compute_trust_score(self, user_id: str, force_recompute: bool = False) -> TrustScore:
        """Compute trust score for a user.

        Args:
            user_id: User to compute trust for
            force_recompute: If False, return cached score if recent enough

        Returns:
            TrustScore with computed trust value and vouch chains
        """
        # Check for cached score (within last hour)
        if not force_recompute:
            cached = self.vouch_repo.get_trust_score(user_id)
            if cached and (datetime.now(UTC) - cached.last_computed) < timedelta(hours=1):
                return cached

        # Check if genesis node
        if self.vouch_repo.is_genesis_node(user_id):
            trust_score = TrustScore(
                user_id=user_id,
                computed_trust=1.0,
                vouch_chains=[[user_id]],
                best_chain_distance=0,
                is_genesis=True,
                last_computed=datetime.now(UTC),
                vouch_count=0,
                revocation_count=0,
            )
            self.vouch_repo.save_trust_score(trust_score)
            return trust_score

        # Build vouch graph
        all_chains = self._find_vouch_chains_to_genesis(user_id)

        if not all_chains:
            # No path to any genesis node
            vouches_received = self.vouch_repo.get_vouches_for_user(user_id, include_revoked=False)
            vouches_revoked = self.vouch_repo.get_vouches_for_user(user_id, include_revoked=True)
            revocation_count = len([v for v in vouches_revoked if v.revoked])

            trust_score = TrustScore(
                user_id=user_id,
                computed_trust=0.0,
                vouch_chains=[],
                best_chain_distance=999,
                is_genesis=False,
                last_computed=datetime.now(UTC),
                vouch_count=len(vouches_received),
                revocation_count=revocation_count,
            )
            self.vouch_repo.save_trust_score(trust_score)
            return trust_score

        # Compute trust from best chain
        best_trust = 0.0
        best_distance = 999

        for chain in all_chains:
            # Distance is number of hops (excluding genesis node at start)
            distance = len(chain) - 1
            # Trust = TRUST_ATTENUATION ^ distance
            chain_trust = TRUST_ATTENUATION ** distance

            if chain_trust > best_trust:
                best_trust = chain_trust
                best_distance = distance

        # Get vouch stats
        vouches_received = self.vouch_repo.get_vouches_for_user(user_id, include_revoked=False)
        vouches_revoked = self.vouch_repo.get_vouches_for_user(user_id, include_revoked=True)
        revocation_count = len([v for v in vouches_revoked if v.revoked])

        trust_score = TrustScore(
            user_id=user_id,
            computed_trust=best_trust,
            vouch_chains=all_chains,
            best_chain_distance=best_distance,
            is_genesis=False,
            last_computed=datetime.now(UTC),
            vouch_count=len(vouches_received),
            revocation_count=revocation_count,
        )

        self.vouch_repo.save_trust_score(trust_score)
        return trust_score

    def _find_vouch_chains_to_genesis(self, user_id: str) -> List[List[str]]:
        """Find all vouch chains from user to genesis nodes using BFS.

        Returns:
            List of chains, where each chain is [genesis_node, ..., user_id]
        """
        genesis_nodes = self.vouch_repo.get_genesis_nodes()
        all_chains = []

        # BFS from each genesis node to find paths to user
        for genesis_id in genesis_nodes:
            chains = self._bfs_vouch_chains(genesis_id, user_id)
            all_chains.extend(chains)

        return all_chains

    def _bfs_vouch_chains(self, start_node: str, target_node: str) -> List[List[str]]:
        """Find all paths from start_node to target_node via vouches using BFS.

        Args:
            start_node: Usually a genesis node
            target_node: User we're computing trust for

        Returns:
            List of chains from start to target
        """
        if start_node == target_node:
            return [[start_node]]

        # Queue: (current_node, path_so_far)
        queue: List[Tuple[str, List[str]]] = [(start_node, [start_node])]
        visited: Set[str] = {start_node}
        found_chains = []

        while queue:
            current, path = queue.pop(0)

            # Don't exceed max distance
            if len(path) > MAX_VOUCH_DISTANCE:
                continue

            # Get all vouches made by current user (non-revoked)
            vouches = self.vouch_repo.get_vouches_by_user(current)
            vouches = [v for v in vouches if not v.revoked]

            for vouch in vouches:
                vouchee = vouch.vouchee_id

                # Found target
                if vouchee == target_node:
                    found_chains.append(path + [vouchee])
                    continue

                # Continue exploring
                if vouchee not in visited:
                    visited.add(vouchee)
                    queue.append((vouchee, path + [vouchee]))

        return found_chains

    def revoke_vouch_with_cascade(self, vouch_id: str, reason: str) -> Dict[str, any]:
        """Revoke a vouch and trigger cascade recomputation.

        When a vouch is revoked:
        1. Mark the vouch as revoked
        2. Recompute trust for the vouchee (their trust drops)
        3. Recursively recompute trust for anyone vouched by vouchee

        Returns:
            Dict with revocation stats: affected_users, trust_changes
        """
        # Get the vouch
        vouch = self.vouch_repo.get_vouch(vouch_id)
        if not vouch:
            return {"error": "Vouch not found", "affected_users": []}

        if vouch.revoked:
            return {"error": "Vouch already revoked", "affected_users": []}

        # Revoke it
        self.vouch_repo.revoke_vouch(vouch_id, reason)

        # Cascade: recompute trust for affected users
        affected_users = self._cascade_trust_recomputation(vouch.vouchee_id)

        return {
            "vouch_id": vouch_id,
            "vouchee_id": vouch.vouchee_id,
            "affected_users": affected_users,
            "revoked_at": datetime.now(UTC).isoformat(),
        }

    def _cascade_trust_recomputation(self, start_user_id: str) -> List[str]:
        """Recursively recompute trust for user and everyone they vouched.

        Args:
            start_user_id: User whose vouch was revoked

        Returns:
            List of user IDs whose trust was recomputed
        """
        affected = []
        visited = set()
        queue = [start_user_id]

        while queue:
            user_id = queue.pop(0)

            if user_id in visited:
                continue

            visited.add(user_id)

            # Recompute this user's trust
            self.compute_trust_score(user_id, force_recompute=True)
            affected.append(user_id)

            # Add all users they vouched for (need recomputation too)
            vouches = self.vouch_repo.get_vouches_by_user(user_id)
            for vouch in vouches:
                if not vouch.revoked and vouch.vouchee_id not in visited:
                    queue.append(vouch.vouchee_id)

        return affected

    def check_trust_threshold(self, user_id: str, action: str) -> Tuple[bool, float]:
        """Check if user meets trust threshold for an action.

        Args:
            user_id: User attempting the action
            action: One of TRUST_THRESHOLDS keys

        Returns:
            (meets_threshold, actual_trust)
        """
        if action not in TRUST_THRESHOLDS:
            raise ValueError(f"Unknown action: {action}. Must be one of {list(TRUST_THRESHOLDS.keys())}")

        trust_score = self.compute_trust_score(user_id)
        threshold = TRUST_THRESHOLDS[action]

        return (trust_score.computed_trust >= threshold, trust_score.computed_trust)

    def can_vouch_for_others(self, user_id: str) -> bool:
        """Check if user has sufficient trust to vouch for others."""
        meets_threshold, _ = self.check_trust_threshold(user_id, "vouch_others")
        return meets_threshold

    def get_vouch_eligibility(self, voucher_id: str, vouchee_id: str) -> Dict[str, any]:
        """Check if a user can vouch for another user.

        Implements fraud/abuse protections (GAP-103, GAP-104):
        - Monthly vouch limit: max 5 vouches per 30 days
        - Cooling period: must know person for 24 hours before vouching

        Returns:
            Dict with eligibility info: can_vouch, reason, voucher_trust
        """
        from app.models.vouch import MAX_VOUCHES_PER_MONTH, MIN_KNOWN_HOURS

        # Check if voucher has sufficient trust
        voucher_trust = self.compute_trust_score(voucher_id)

        if voucher_trust.computed_trust < TRUST_THRESHOLDS["vouch_others"]:
            return {
                "can_vouch": False,
                "reason": f"Insufficient trust (need {TRUST_THRESHOLDS['vouch_others']}, have {voucher_trust.computed_trust:.2f})",
                "voucher_trust": voucher_trust.computed_trust,
            }

        # GAP-103: Check monthly vouch limit
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        recent_vouches = self.vouch_repo.get_vouches_since(voucher_id, thirty_days_ago)
        if len(recent_vouches) >= MAX_VOUCHES_PER_MONTH:
            days_until_reset = 30 - (datetime.now(UTC) - recent_vouches[0].created_at).days
            return {
                "can_vouch": False,
                "reason": f"Monthly vouch limit reached ({MAX_VOUCHES_PER_MONTH}). Resets in {days_until_reset} days.",
                "voucher_trust": voucher_trust.computed_trust,
            }

        # Check if vouch already exists
        existing_vouches = self.vouch_repo.get_vouches_for_user(vouchee_id, include_revoked=False)
        for vouch in existing_vouches:
            if vouch.voucher_id == voucher_id:
                return {
                    "can_vouch": False,
                    "reason": "You have already vouched for this user",
                    "voucher_trust": voucher_trust.computed_trust,
                }

        # GAP-104: Check cooling period (24 hours known)
        # For now, we approximate "first interaction" as the earlier of:
        # 1. First message exchanged with this user (TODO: implement message interaction tracking)
        # 2. For simplicity in this implementation, we'll require a separate "interaction" timestamp
        #    This would be tracked in a separate table in production
        # Since we don't have interaction tracking yet, we'll skip this check for now
        # but leave the framework in place
        # TODO: Implement interaction tracking table and check here

        return {
            "can_vouch": True,
            "reason": "Eligible to vouch",
            "voucher_trust": voucher_trust.computed_trust,
        }
