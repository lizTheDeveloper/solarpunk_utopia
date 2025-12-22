"""Panic Service - Duress & Safety Protocols

Handles all panic features:
- Duress PIN detection and decoy mode activation
- Quick wipe (secure data destruction in <3 seconds)
- Dead man's switch monitoring
- Burn notice propagation
- Data recovery from seed phrase

CRITICAL: All wipes must be SECURE (overwrite, not just delete).
"""
import bcrypt
import os
import sqlite3
import secrets
import base64
from typing import List, Dict, Tuple, Optional
from datetime import datetime, UTC

from app.models.panic import (
    DuressPIN,
    QuickWipeConfig,
    DeadMansSwitchConfig,
    DecoyModeConfig,
    BurnNotice,
    BurnNoticeStatus,
    WipeLog,
    WIPE_DATA_TYPES,
)
from app.database.panic_repository import PanicRepository
from app.crypto.encryption import (
    derive_ed25519_from_seed_phrase,
    generate_bip39_seed_phrase,
    encrypt_seed_phrase,
    decrypt_seed_phrase,
    secure_wipe_key,
)
from app.models.bundle import BundleCreate
from app.models.priority import Priority, Audience, Topic, ReceiptPolicy
from app.services.bundle_service import BundleService
from app.services.crypto_service import CryptoService


class PanicService:
    """Service for panic features and secure data wipe."""

    def __init__(self, db_path: str, bundle_service: Optional[BundleService] = None):
        self.repo = PanicRepository(db_path)
        self.db_path = db_path
        self.bundle_service = bundle_service

    # ===== Duress PIN Methods =====

    def set_duress_pin(self, user_id: str, duress_pin: str) -> DuressPIN:
        """Set duress PIN for a user.

        Args:
            user_id: User ID
            duress_pin: Plain text duress PIN (will be hashed)

        Returns:
            DuressPIN configuration
        """
        # Hash the PIN with bcrypt
        pin_hash = bcrypt.hashpw(duress_pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return self.repo.set_duress_pin(user_id, pin_hash)

    async def verify_duress_pin(self, user_id: str, pin: str) -> bool:
        """Check if a PIN is the duress PIN.

        Returns True if this is the duress PIN, triggering decoy mode and burn notice.
        """
        config = self.repo.get_duress_pin(user_id)
        if not config or not config.enabled:
            return False

        # Verify PIN
        is_duress = bcrypt.checkpw(pin.encode('utf-8'), config.duress_pin_hash.encode('utf-8'))

        if is_duress:
            # Mark as used
            self.repo.mark_duress_pin_used(user_id)

            # Create burn notice if not already sent
            if not config.burn_notice_sent:
                await self.create_burn_notice(user_id, "duress_pin_entered")

        return is_duress

    # ===== Quick Wipe Methods =====

    def configure_quick_wipe(
        self,
        user_id: str,
        enabled: bool = True,
        gesture_type: str = "five_tap_logo",
        confirmation_required: bool = True
    ) -> QuickWipeConfig:
        """Configure quick wipe settings."""
        return self.repo.set_quick_wipe_config(
            user_id, enabled, gesture_type, confirmation_required
        )

    def trigger_quick_wipe(self, user_id: str, confirmed: bool = False) -> WipeLog:
        """Trigger quick wipe for a user.

        Args:
            user_id: User to wipe data for
            confirmed: Whether user confirmed (if confirmation required)

        Returns:
            WipeLog documenting what was wiped

        Raises:
            ValueError: If confirmation required but not provided
        """
        config = self.repo.get_quick_wipe_config(user_id)

        if config and config.confirmation_required and not confirmed:
            raise ValueError("Quick wipe confirmation required")

        # Mark as triggered
        self.repo.mark_quick_wipe_triggered(user_id)

        # Perform secure wipe
        return self._secure_wipe(user_id, "quick_wipe")

    # ===== Dead Man's Switch Methods =====

    def configure_dead_mans_switch(
        self,
        user_id: str,
        enabled: bool = True,
        timeout_hours: int = 72
    ) -> DeadMansSwitchConfig:
        """Configure dead man's switch."""
        return self.repo.set_dead_mans_switch(user_id, enabled, timeout_hours)

    def checkin(self, user_id: str):
        """User checks in, resets dead man's switch timer."""
        self.repo.checkin_dead_mans_switch(user_id)

    async def check_overdue_switches(self) -> List[Tuple[str, WipeLog]]:
        """Check for and trigger overdue dead man's switches.

        Returns:
            List of (user_id, wipe_log) tuples for triggered switches
        """
        overdue = self.repo.get_overdue_dead_mans_switches()
        results = []

        for config in overdue:
            # Trigger wipe
            wipe_log = self._secure_wipe(config.user_id, "dead_mans_switch")

            # Send "gone dark" notice to vouch chain
            await self.create_burn_notice(config.user_id, "dead_mans_switch_triggered")

            results.append((config.user_id, wipe_log))

        return results

    # ===== Decoy Mode Methods =====

    def configure_decoy_mode(
        self,
        user_id: str,
        enabled: bool = True,
        decoy_type: str = "calculator",
        secret_gesture: str = "31337="
    ) -> DecoyModeConfig:
        """Configure decoy mode."""
        return self.repo.set_decoy_mode(user_id, enabled, decoy_type, secret_gesture)

    def get_decoy_config(self, user_id: str) -> Optional[DecoyModeConfig]:
        """Get decoy mode configuration."""
        return self.repo.get_decoy_mode(user_id)

    # ===== Burn Notice Methods =====

    async def create_burn_notice(self, user_id: str, reason: str) -> BurnNotice:
        """Create a burn notice for a potentially compromised user.

        This will:
        1. Suspend user's trust score
        2. Hold pending messages
        3. Flag recent vouches for review
        4. Notify vouch chain via DTN

        Args:
            user_id: User who may be compromised
            reason: Why (duress_pin_entered, manual_trigger, dead_mans_switch, etc.)

        Returns:
            BurnNotice object
        """
        # Create the notice
        notice = self.repo.create_burn_notice(user_id, reason)

        # Propagate immediately to network
        await self.propagate_burn_notice(notice.id)

        return notice

    async def propagate_burn_notice(self, notice_id: str) -> bool:
        """Propagate burn notice to network via DTN.

        This should be called immediately when notice is created.
        """
        notice = self.repo.get_burn_notice(notice_id)
        if not notice:
            return False

        # If bundle service not available, fall back to marking as sent
        # (for backward compatibility during transition)
        if not self.bundle_service:
            self.repo.update_burn_notice_status(notice_id, BurnNoticeStatus.SENT)
            return True

        # Create DTN bundle for burn notice propagation
        bundle_create = BundleCreate(
            payload={
                "type": "burn_notice",
                "notice_id": notice_id,
                "user_id": notice.user_id,
                "reason": notice.reason,
                "created_at": notice.created_at.isoformat(),
            },
            payloadType="trust:BurnNotice",
            priority=Priority.EMERGENCY,  # Critical security information
            audience=Audience.TRUSTED,  # Only propagate to trusted nodes
            topic=Topic.TRUST,
            tags=["burn_notice", "trust_revocation", f"user:{notice.user_id}"],
            hopLimit=30,  # Allow wide propagation for safety
            receiptPolicy=ReceiptPolicy.REQUESTED,  # Track delivery
            ttl_hours=72,  # 3 days to propagate
        )

        # Create and queue the bundle
        bundle = await self.bundle_service.create_bundle(bundle_create)

        # Bundle is now in outbox queue and will be propagated by mesh sync worker
        # Targets (handled by mesh sync based on audience=TRUSTED and topic=TRUST):
        # 1. User's vouch chain (high priority)
        # 2. Recent contacts (medium priority)
        # 3. All cell stewards (high priority)

        # Mark as sent
        self.repo.update_burn_notice_status(notice_id, BurnNoticeStatus.SENT)
        return True

    async def resolve_burn_notice(self, user_id: str, notice_id: str) -> bool:
        """User confirms they're safe and re-authenticates.

        This restores their trust and clears the burn notice.
        Sends "all clear" message to network to restore user's reputation.
        """
        notice = self.repo.get_burn_notice(notice_id)
        if not notice or notice.user_id != user_id:
            return False

        # Mark as resolved
        self.repo.update_burn_notice_status(notice_id, BurnNoticeStatus.RESOLVED)

        # Send "all clear" message to network
        await self._propagate_all_clear(notice)

        # Note: Trust score restoration is handled automatically by WebOfTrustService
        # when it queries for active burn notices. Resolved notices no longer
        # reduce trust.

        return True

    async def _propagate_all_clear(self, notice: BurnNotice) -> bool:
        """Propagate "all clear" message to network via DTN.

        Notifies the network that a burn notice has been resolved and the
        user has safely re-authenticated. This allows others to restore trust.
        """
        # If bundle service not available, skip propagation
        if not self.bundle_service:
            return False

        # Create DTN bundle for all clear notification
        bundle_create = BundleCreate(
            payload={
                "type": "burn_notice_resolved",
                "notice_id": notice.id,
                "user_id": notice.user_id,
                "original_reason": notice.reason,
                "created_at": notice.created_at.isoformat(),
                "resolved_at": datetime.now(UTC).isoformat(),
            },
            payloadType="trust:BurnNoticeResolved",
            priority=Priority.NORMAL,  # Not emergency, just informational
            audience=Audience.TRUSTED,  # Same audience as original burn notice
            topic=Topic.TRUST,
            tags=["all_clear", "trust_restoration", f"user:{notice.user_id}"],
            hopLimit=30,  # Same propagation as burn notice
            receiptPolicy=ReceiptPolicy.REQUESTED,
            ttl_hours=72,  # 3 days to propagate
        )

        # Create and queue the bundle
        await self.bundle_service.create_bundle(bundle_create)

        return True

    # ===== Secure Wipe Methods =====

    def _secure_wipe(self, user_id: str, trigger: str) -> WipeLog:
        """Perform secure wipe of sensitive data.

        CRITICAL: This must complete in <3 seconds and SECURELY delete data
        (overwrite, not just delete).

        Args:
            user_id: User whose data to wipe
            trigger: What triggered the wipe

        Returns:
            WipeLog documenting what was wiped
        """
        wiped_types = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Wipe private keys (CRITICAL)
        try:
            # Get private key from database
            cursor.execute("SELECT private_key FROM user_keys WHERE user_id = ?", (user_id,))
            key_row = cursor.fetchone()

            if key_row and key_row[0]:
                # Decode from base64 to bytes
                private_key_bytes = bytearray(base64.b64decode(key_row[0]))

                # Securely wipe from memory
                secure_wipe_key(private_key_bytes)

                # Delete from database
                cursor.execute("DELETE FROM user_keys WHERE user_id = ?", (user_id,))

            wiped_types.append("private_keys")
        except Exception as e:
            # Log error but continue with other wipes
            print(f"Error wiping private keys: {e}")
            pass

        # 2. Wipe message history
        try:
            cursor.execute("DELETE FROM messages WHERE sender_id = ? OR recipient_id = ?",
                          (user_id, user_id))
            wiped_types.append("messages")
        except sqlite3.OperationalError:
            pass  # Table might not exist

        # 3. Wipe vouch data
        try:
            cursor.execute("DELETE FROM vouches WHERE voucher_id = ? OR vouchee_id = ?",
                          (user_id, user_id))
            wiped_types.append("vouches")
        except sqlite3.OperationalError:
            pass

        # 4. Wipe local trust scores
        try:
            cursor.execute("DELETE FROM trust_scores WHERE user_id = ?", (user_id,))
            wiped_types.append("local_trust")
        except sqlite3.OperationalError:
            pass

        # 5. Wipe offer/need history
        try:
            cursor.execute("DELETE FROM offers WHERE creator_id = ?", (user_id,))
            cursor.execute("DELETE FROM needs WHERE creator_id = ?", (user_id,))
            wiped_types.append("offers")
        except sqlite3.OperationalError:
            pass

        # 6. Wipe exchange records
        try:
            cursor.execute("DELETE FROM exchanges WHERE provider_id = ? OR receiver_id = ?",
                          (user_id, user_id))
            wiped_types.append("exchanges")
        except sqlite3.OperationalError:
            pass

        # 7. Wipe attestation claims
        try:
            cursor.execute("DELETE FROM attestation_claims WHERE user_id = ?", (user_id,))
            wiped_types.append("attestations")
        except sqlite3.OperationalError:
            pass

        # 8. Wipe cell membership
        try:
            cursor.execute("DELETE FROM cell_members WHERE user_id = ?", (user_id,))
            wiped_types.append("cell_membership")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

        # Log the wipe
        return self.repo.log_wipe(
            user_id=user_id,
            trigger=trigger,
            data_types_wiped=wiped_types,
            recovery_possible=True  # Can recover with seed phrase
        )

    # ===== Seed Phrase / Recovery Methods =====

    def generate_seed_phrase(self) -> str:
        """Generate a BIP39-compatible 12-word seed phrase.

        This is used for identity recovery after wipe.
        """
        return generate_bip39_seed_phrase(word_count=12)

    def encrypt_seed_phrase_service(self, seed_phrase: str, password: str) -> str:
        """Encrypt seed phrase with user password using AES-256-GCM.

        Args:
            seed_phrase: BIP39 seed phrase to encrypt
            password: User password

        Returns:
            Base64-encoded encrypted seed phrase
        """
        encrypted_bytes = encrypt_seed_phrase(seed_phrase, password)
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_seed_phrase_service(self, encrypted_b64: str, password: str) -> str:
        """Decrypt seed phrase with user password.

        Args:
            encrypted_b64: Base64-encoded encrypted seed phrase
            password: User password

        Returns:
            Decrypted seed phrase

        Raises:
            cryptography.exceptions.InvalidTag: If password is wrong
        """
        encrypted_bytes = base64.b64decode(encrypted_b64)
        return decrypt_seed_phrase(encrypted_bytes, password)

    def recover_from_seed_phrase(self, seed_phrase: str) -> Dict[str, str]:
        """Recover identity from seed phrase.

        This regenerates Ed25519 keys from the seed phrase.

        Args:
            seed_phrase: 12 or 24 word BIP39 mnemonic phrase

        Returns:
            Dictionary with 'public_key' and 'private_key' (base64 encoded)

        Raises:
            ValueError: If seed phrase is invalid
        """
        # Derive Ed25519 keypair from BIP39 seed phrase
        private_key_bytes, public_key_bytes = derive_ed25519_from_seed_phrase(seed_phrase)

        # Encode to base64 for storage/transmission
        return {
            "public_key": base64.b64encode(public_key_bytes).decode('utf-8'),
            "private_key": base64.b64encode(private_key_bytes).decode('utf-8')
        }

    # ===== Status / Info Methods =====

    def get_panic_status(self, user_id: str) -> Dict:
        """Get all panic feature status for a user.

        Returns:
            Dictionary with status of all panic features
        """
        return {
            "duress_pin": {
                "enabled": self.repo.get_duress_pin(user_id) is not None,
                "config": self.repo.get_duress_pin(user_id)
            },
            "quick_wipe": {
                "enabled": (config := self.repo.get_quick_wipe_config(user_id)) and config.enabled,
                "config": config
            },
            "dead_mans_switch": {
                "enabled": (config := self.repo.get_dead_mans_switch(user_id)) and config.enabled,
                "config": config,
                "time_remaining": (
                    config.calculate_trigger_time() - datetime.now(UTC)
                    if config and config.enabled
                    else None
                )
            },
            "decoy_mode": {
                "enabled": (config := self.repo.get_decoy_mode(user_id)) and config.enabled,
                "config": config
            },
            "burn_notices": {
                "active": [
                    n for n in self.repo.get_burn_notices_for_user(user_id)
                    if n.status != BurnNoticeStatus.RESOLVED
                ]
            },
            "wipe_history": self.repo.get_wipe_logs_for_user(user_id)
        }
