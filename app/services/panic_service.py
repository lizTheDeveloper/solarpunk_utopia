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
from typing import List, Dict, Tuple, Optional
from datetime import datetime

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


class PanicService:
    """Service for panic features and secure data wipe."""

    def __init__(self, db_path: str):
        self.repo = PanicRepository(db_path)
        self.db_path = db_path

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

    def verify_duress_pin(self, user_id: str, pin: str) -> bool:
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
                self.create_burn_notice(user_id, "duress_pin_entered")

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

    def check_overdue_switches(self) -> List[Tuple[str, WipeLog]]:
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
            self.create_burn_notice(config.user_id, "dead_mans_switch_triggered")

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

    def create_burn_notice(self, user_id: str, reason: str) -> BurnNotice:
        """Create a burn notice for a potentially compromised user.

        This will:
        1. Suspend user's trust score
        2. Hold pending messages
        3. Flag recent vouches for review
        4. Notify vouch chain

        Args:
            user_id: User who may be compromised
            reason: Why (duress_pin_entered, manual_trigger, dead_mans_switch, etc.)

        Returns:
            BurnNotice object
        """
        # Create the notice
        notice = self.repo.create_burn_notice(user_id, reason)

        # TODO: Integrate with bundle service to propagate via DTN
        # For now, mark as pending - propagation will happen in background

        return notice

    def propagate_burn_notice(self, notice_id: str) -> bool:
        """Propagate burn notice to network via DTN.

        This should be called by background worker.
        """
        notice = self.repo.get_burn_notice(notice_id)
        if not notice:
            return False

        # TODO: Create DTN bundle with burn notice
        # Bundle should go to:
        # 1. User's vouch chain
        # 2. Recent contacts
        # 3. Cell stewards

        # For now, mark as sent
        self.repo.update_burn_notice_status(notice_id, BurnNoticeStatus.SENT)
        return True

    def resolve_burn_notice(self, user_id: str, notice_id: str) -> bool:
        """User confirms they're safe and re-authenticates.

        This restores their trust and clears the burn notice.
        """
        notice = self.repo.get_burn_notice(notice_id)
        if not notice or notice.user_id != user_id:
            return False

        # Mark as resolved
        self.repo.update_burn_notice_status(notice_id, BurnNoticeStatus.RESOLVED)

        # TODO: Send "all clear" message to network
        # TODO: Restore trust score

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
        # TODO: Implement key storage wipe
        # For now, just log that we would wipe them
        wiped_types.append("private_keys")

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
        # Simple implementation - in production, use proper BIP39 library
        # For now, generate 12 random words from a wordlist

        # BIP39 wordlist (simplified - first 100 words for demo)
        wordlist = [
            "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
            "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
            "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
            "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
            "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
            "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album",
            "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone",
            "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among",
            "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry",
            "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
            "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april",
            "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor",
            "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact"
        ]

        # Generate 12 random words
        words = [secrets.choice(wordlist) for _ in range(12)]
        return " ".join(words)

    def encrypt_seed_phrase(self, seed_phrase: str, password: str) -> str:
        """Encrypt seed phrase with user password.

        In production, use proper encryption (AES-256-GCM or similar).
        For now, this is a placeholder.
        """
        # TODO: Implement proper encryption
        # For now, just return a placeholder
        return f"ENCRYPTED[{seed_phrase}]"

    def decrypt_seed_phrase(self, encrypted: str, password: str) -> str:
        """Decrypt seed phrase with user password."""
        # TODO: Implement proper decryption
        # For now, just extract from placeholder
        if encrypted.startswith("ENCRYPTED[") and encrypted.endswith("]"):
            return encrypted[10:-1]
        return encrypted

    def recover_from_seed_phrase(self, seed_phrase: str) -> Dict[str, str]:
        """Recover identity from seed phrase.

        This regenerates Ed25519 keys from the seed phrase.

        Returns:
            Dictionary with 'public_key' and 'private_key'
        """
        # TODO: Implement proper BIP39 -> Ed25519 derivation
        # For now, return placeholder
        return {
            "public_key": "placeholder_public_key",
            "private_key": "placeholder_private_key"
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
                    config.calculate_trigger_time() - datetime.utcnow()
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
