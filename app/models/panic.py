"""Panic Features - Duress & Safety Protocols

Protects users and the network when phones are seized, users are detained,
or devices are inspected by authorities.

Features:
- Duress PIN: Alternate unlock showing decoy interface
- Quick Wipe: Panic gesture destroys sensitive data in <3 seconds
- Dead Man's Switch: Auto-wipe if app not opened for N days
- Decoy Mode: App appears as calculator/notes
- Burn Notice: Signal to network that user is compromised
- Seed Phrase Recovery: Restore identity after wipe
"""
from datetime import datetime, timedelta, UTC
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class DuressPIN(BaseModel):
    """Duress PIN configuration for a user.

    When duress PIN is entered, app opens in decoy mode and sends burn notice.
    """
    user_id: str = Field(description="User this duress PIN belongs to")
    duress_pin_hash: str = Field(description="Bcrypt hash of duress PIN")
    enabled: bool = Field(default=True, description="Whether duress PIN is active")
    last_used: Optional[datetime] = Field(
        default=None,
        description="Last time duress PIN was entered (indicates compromise)"
    )
    burn_notice_sent: bool = Field(
        default=False,
        description="Whether burn notice was sent after duress entry"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-pk-123",
                "duress_pin_hash": "$2b$12$...",
                "enabled": True,
                "last_used": None,
                "burn_notice_sent": False,
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class QuickWipeConfig(BaseModel):
    """Quick wipe configuration.

    User can trigger instant data destruction via panic gesture.
    """
    user_id: str = Field(description="User this config belongs to")
    enabled: bool = Field(default=False, description="Whether quick wipe is enabled")
    gesture_type: str = Field(
        default="five_tap_logo",
        description="Gesture to trigger wipe: 'five_tap_logo', 'shake_pattern', etc."
    )
    confirmation_required: bool = Field(
        default=True,
        description="Whether gesture needs confirmation (prevents accidents)"
    )
    last_triggered: Optional[datetime] = Field(
        default=None,
        description="Last time quick wipe was triggered"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-pk-123",
                "enabled": True,
                "gesture_type": "five_tap_logo",
                "confirmation_required": True,
                "last_triggered": None,
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class DeadMansSwitchConfig(BaseModel):
    """Dead man's switch configuration.

    Auto-wipes sensitive data if user doesn't check in within timeframe.
    """
    user_id: str = Field(description="User this config belongs to")
    enabled: bool = Field(default=False, description="Whether dead man's switch is active")
    timeout_hours: int = Field(
        default=72,
        description="Hours of inactivity before auto-wipe triggers"
    )
    last_checkin: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last time user checked in (opened app)"
    )
    trigger_time: Optional[datetime] = Field(
        default=None,
        description="When the switch will trigger (calculated)"
    )
    triggered: bool = Field(
        default=False,
        description="Whether switch has triggered"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_trigger_time(self) -> datetime:
        """Calculate when dead man's switch will trigger."""
        return self.last_checkin + timedelta(hours=self.timeout_hours)

    def is_overdue(self) -> bool:
        """Check if dead man's switch is overdue to trigger."""
        return datetime.now(UTC) >= self.calculate_trigger_time()

    def checkin(self):
        """User checks in, resets the timer."""
        self.last_checkin = datetime.now(UTC)
        self.trigger_time = self.calculate_trigger_time()
        self.triggered = False

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-pk-123",
                "enabled": True,
                "timeout_hours": 72,
                "last_checkin": "2025-12-19T00:00:00Z",
                "trigger_time": "2025-12-22T00:00:00Z",
                "triggered": False,
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class DecoyModeConfig(BaseModel):
    """Decoy mode configuration.

    Makes app appear as innocuous calculator or notes app.
    """
    user_id: str = Field(description="User this config belongs to")
    enabled: bool = Field(default=False, description="Whether decoy mode is active")
    decoy_type: str = Field(
        default="calculator",
        description="Type of decoy: 'calculator', 'notes', 'weather'"
    )
    secret_gesture: str = Field(
        default="31337=",
        description="Secret gesture to reveal real app (e.g., type '31337=' in calculator)"
    )
    currently_in_decoy: bool = Field(
        default=False,
        description="Whether app is currently showing decoy interface"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-pk-123",
                "enabled": True,
                "decoy_type": "calculator",
                "secret_gesture": "31337=",
                "currently_in_decoy": False,
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class BurnNoticeStatus(str, Enum):
    """Status of burn notice."""
    PENDING = "pending"
    SENT = "sent"
    PROPAGATED = "propagated"
    RESOLVED = "resolved"


class BurnNotice(BaseModel):
    """Burn notice - signal that a user may be compromised.

    Propagates through DTN to vouch chain, suspending trust.
    """
    id: str = Field(description="Unique burn notice ID")
    user_id: str = Field(description="User who is compromised (or suspected)")
    reason: str = Field(
        description="Reason: 'duress_pin_entered', 'manual_trigger', 'third_party_report'"
    )
    status: BurnNoticeStatus = Field(
        default=BurnNoticeStatus.PENDING,
        description="Status of burn notice propagation"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    propagated_at: Optional[datetime] = Field(
        default=None,
        description="When notice was sent to network"
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When user confirmed they're safe and re-authenticated"
    )
    vouch_chain_notified: bool = Field(
        default=False,
        description="Whether vouch chain has been notified"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "burn-notice-001",
                "user_id": "user-pk-123",
                "reason": "duress_pin_entered",
                "status": "sent",
                "created_at": "2025-12-19T00:00:00Z",
                "propagated_at": "2025-12-19T00:00:10Z",
                "resolved_at": None,
                "vouch_chain_notified": True
            }
        }


class SeedPhraseRecovery(BaseModel):
    """Seed phrase for identity recovery after wipe.

    BIP39-compatible 12-word mnemonic for regenerating Ed25519 keys.
    """
    user_id: str = Field(description="User this seed phrase belongs to")
    seed_phrase_encrypted: str = Field(
        description="Encrypted seed phrase (encrypted with user password)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = Field(
        default=None,
        description="Last time seed phrase was used for recovery"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-pk-123",
                "seed_phrase_encrypted": "encrypted_mnemonic_here",
                "created_at": "2025-12-19T00:00:00Z",
                "last_used": None
            }
        }


class WipeLog(BaseModel):
    """Log of data wipe events for audit/recovery."""
    id: str = Field(description="Unique wipe log ID")
    user_id: str = Field(description="User whose data was wiped")
    trigger: str = Field(
        description="What triggered wipe: 'quick_wipe', 'dead_mans_switch', 'duress_pin', 'manual'"
    )
    wiped_at: datetime = Field(default_factory=datetime.utcnow)
    data_types_wiped: list[str] = Field(
        description="What was wiped: ['private_keys', 'messages', 'vouches', etc.]"
    )
    recovery_possible: bool = Field(
        default=True,
        description="Whether recovery is possible (seed phrase still valid)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wipe-log-001",
                "user_id": "user-pk-123",
                "trigger": "quick_wipe",
                "wiped_at": "2025-12-19T00:00:00Z",
                "data_types_wiped": ["private_keys", "messages", "vouches", "local_trust"],
                "recovery_possible": True
            }
        }


# Data types that get wiped during panic
WIPE_DATA_TYPES = [
    "private_keys",       # Ed25519 keys
    "messages",           # Message history
    "vouches",            # Vouch chains
    "local_trust",        # Trust scores
    "offers",             # Offer/need history
    "exchanges",          # Exchange records
    "attestations",       # Attestation claims
    "cell_membership",    # Local cell data
]

# Data that survives (on network, can be recovered)
SURVIVING_DATA = [
    "public_key",         # Identity (can be regenerated from seed)
    "published_offers",   # Already on mesh
    "completed_exchanges",# Already propagated
    "network_attestations", # Already on network
]
