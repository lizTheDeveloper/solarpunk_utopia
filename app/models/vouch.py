"""Web of Trust - Vouch and Trust Score Models"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Vouch(BaseModel):
    """A vouch from one trusted member to another.

    Trust propagates through vouch chains, attenuating with distance from genesis nodes.
    """
    id: str = Field(description="Unique vouch ID (UUID)")
    voucher_id: str = Field(description="User ID of person giving the vouch (public key)")
    vouchee_id: str = Field(description="User ID of person receiving the vouch (public key)")
    context: str = Field(description="How they know each other: 'met_in_person', 'worked_together', 'family', etc.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = Field(default=False, description="Whether this vouch has been revoked")
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "vouch-001",
                "voucher_id": "alice-pk",
                "vouchee_id": "bob-pk",
                "context": "met_in_person",
                "created_at": "2025-12-19T00:00:00Z",
                "revoked": False,
            }
        }


class VouchRequest(BaseModel):
    """Request to vouch for a new member."""
    vouchee_id: str = Field(description="User ID to vouch for")
    context: str = Field(description="How you know them")


class RevocationRequest(BaseModel):
    """Request to revoke a vouch (compromise detected)."""
    vouch_id: str = Field(description="ID of vouch to revoke")
    reason: str = Field(description="Why this vouch is being revoked")


class TrustScore(BaseModel):
    """Computed trust score for a user.

    Trust computation:
    - Genesis nodes start with 1.0 trust
    - Each vouch hop attenuates trust by 20% (multiplies by 0.8)
    - Multiple vouch chains use the highest scoring path
    - Revocation reduces trust in cascade
    """
    user_id: str = Field(description="User being scored")
    computed_trust: float = Field(ge=0.0, le=1.0, description="Trust score from 0.0 to 1.0")
    vouch_chains: List[List[str]] = Field(
        description="All paths from this user to genesis nodes",
        default_factory=list
    )
    best_chain_distance: int = Field(
        description="Hops to nearest genesis node via highest-scoring chain",
        default=999
    )
    is_genesis: bool = Field(default=False, description="Whether this user is a genesis node")
    last_computed: datetime = Field(default_factory=datetime.utcnow)
    vouch_count: int = Field(default=0, description="Number of active vouches received")
    revocation_count: int = Field(default=0, description="Number of vouches revoked")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "bob-pk",
                "computed_trust": 0.8,
                "vouch_chains": [["genesis-alice", "alice-pk", "bob-pk"]],
                "best_chain_distance": 2,
                "is_genesis": False,
                "last_computed": "2025-12-19T00:00:00Z",
                "vouch_count": 1,
                "revocation_count": 0,
            }
        }


# Trust thresholds for actions (from proposal)
TRUST_THRESHOLDS = {
    "view_public_offers": 0.3,
    "post_offers_needs": 0.5,
    "send_messages": 0.6,
    "vouch_others": 0.7,
    "steward_actions": 0.9,
}

# Trust attenuation per hop (0.8 = 20% reduction per hop)
TRUST_ATTENUATION = 0.8

# Maximum vouch chain distance to consider (prevents long weak chains)
MAX_VOUCH_DISTANCE = 10

# Fraud/Abuse Prevention Constants (GAP-103, GAP-104, GAP-105)
MAX_VOUCHES_PER_MONTH = 5  # GAP-103: Monthly vouch limit
MIN_KNOWN_HOURS = 24  # GAP-104: Must know person for 24 hours before vouching
VOUCH_COOLOFF_HOURS = 48  # GAP-105: 48h grace period for no-consequence revocation

# Genesis node IDs (bootstrapped on initial deployment)
GENESIS_NODES = [
    # These will be configured via environment or initial setup
    # For now, placeholder that will be populated from database
]
