"""Network Import - Attestation Models

Enables importing existing communities via:
- Steward bulk vouching
- Cryptographic cohort attestations (threshold signatures)
- Challenge-response verification
- In-person verification

All methods work WITHOUT external platforms or internet dependency.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class Attestation(BaseModel):
    """A cryptographic attestation for cohort/group membership.

    Signed by multiple stewards (threshold signatures) to prevent single point of compromise.
    NO email/phone stored - verification is in-person or via mesh challenge.
    """
    id: str = Field(description="Unique attestation ID (UUID)")
    type: str = Field(description="Type: 'cohort', 'membership', 'graduation', 'organization'")
    subject_identifier: str = Field(
        description="Name or pseudonym (NO email/phone - privacy by design)"
    )
    claims: Dict[str, str] = Field(
        description="Key-value claims: {'cohort': '2019-fall', 'role': 'graduate'}",
        default_factory=dict
    )
    issuer_pubkeys: List[str] = Field(
        description="Public keys of all issuers (threshold: 3 of 5 required)"
    )
    signatures: List[str] = Field(
        description="Threshold signatures (3 of 5 stewards must sign)"
    )
    threshold_required: int = Field(
        default=3,
        description="Minimum signatures required (e.g., 3 of 5)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Optional expiration (e.g., event attestations expire after event)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "attestation-001",
                "type": "cohort",
                "subject_identifier": "Alex K.",
                "claims": {
                    "cohort": "2019-fall-bootcamp",
                    "role": "graduate",
                    "organization": "Rethink Institute"
                },
                "issuer_pubkeys": ["steward1-pk", "steward2-pk", "steward3-pk"],
                "signatures": ["sig1", "sig2", "sig3"],
                "threshold_required": 3,
                "created_at": "2025-12-19T00:00:00Z",
                "expires_at": None
            }
        }


class AttestationClaim(BaseModel):
    """A user claiming an attestation and being verified.

    Verification happens via:
    - In-person: steward confirms identity face-to-face
    - Challenge: answer cohort-specific question only real members know
    - Mesh vouch: existing verified cohort member vouches
    """
    id: str = Field(description="Unique claim ID (UUID)")
    attestation_id: str = Field(description="Attestation being claimed")
    claimer_user_id: str = Field(description="User claiming this attestation")
    verification_method: str = Field(
        description="How verified: 'in_person', 'challenge', 'mesh_vouch'"
    )
    verifier_id: Optional[str] = Field(
        default=None,
        description="Who verified (steward ID for in-person, cohort member for mesh_vouch)"
    )
    challenge_response: Optional[str] = Field(
        default=None,
        description="Response to challenge question (hashed)"
    )
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    trust_granted: float = Field(
        ge=0.0,
        le=1.0,
        description="Trust bonus granted (0.0 - 1.0)"
    )
    status: str = Field(
        default="pending",
        description="Status: 'pending', 'verified', 'rejected'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "claim-001",
                "attestation_id": "attestation-001",
                "claimer_user_id": "user-pk-123",
                "verification_method": "in_person",
                "verifier_id": "steward1-pk",
                "verified_at": "2025-12-19T00:00:00Z",
                "trust_granted": 0.15,
                "status": "verified"
            }
        }


class ChallengeQuestion(BaseModel):
    """A challenge question for verifying cohort membership.

    Only real members of the cohort would know the answer.
    Examples: "What city was the 2019 bootcamp in?", "Who taught week 3?"
    """
    id: str = Field(description="Unique challenge ID (UUID)")
    attestation_id: str = Field(description="Attestation this challenge verifies")
    question: str = Field(description="The challenge question")
    answer_hash: str = Field(description="SHA256 hash of correct answer (lowercase, trimmed)")
    created_by: str = Field(description="Steward who created this challenge")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True, description="Whether this challenge is still active")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "challenge-001",
                "attestation_id": "attestation-001",
                "question": "What city was the 2019 fall bootcamp held in?",
                "answer_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "portland"
                "created_by": "steward1-pk",
                "created_at": "2025-12-19T00:00:00Z",
                "active": True
            }
        }


class BulkVouchRequest(BaseModel):
    """Request to vouch for multiple people (steward bulk import).

    Steward attests "I have met these people in person" and provides contact info.
    """
    vouchees: List[Dict[str, str]] = Field(
        description="List of people to vouch for: [{'name': 'Alex', 'identifier': 'alex@email.com'}]"
    )
    context: str = Field(
        description="How steward knows them: 'co_op_members', 'bootcamp_cohort', 'workshop_attendees'"
    )
    attestation: str = Field(
        default="met_in_person",
        description="Attestation type: 'met_in_person', 'worked_together', 'family'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vouchees": [
                    {"name": "Alex K.", "identifier": "alex@example.com"},
                    {"name": "Jamie L.", "identifier": "jamie@example.com"}
                ],
                "context": "food_co_op_members",
                "attestation": "met_in_person"
            }
        }


class StewardVouchRecord(BaseModel):
    """Track steward vouching patterns for accountability.

    If a steward vouches for infiltrators, pattern is flagged.
    """
    steward_id: str = Field(description="Steward who gave vouches")
    total_vouches: int = Field(default=0, description="Total people vouched for")
    vouches_revoked: int = Field(default=0, description="How many were later revoked")
    vouches_flagged: int = Field(default=0, description="How many were flagged as suspicious")
    revocation_rate: float = Field(
        default=0.0,
        description="Percentage of vouches that were revoked (0.0 - 1.0)"
    )
    status: str = Field(
        default="active",
        description="Status: 'active', 'warning', 'suspended'"
    )
    last_review: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, description="Admin notes about this steward")

    class Config:
        json_schema_extra = {
            "example": {
                "steward_id": "steward1-pk",
                "total_vouches": 50,
                "vouches_revoked": 2,
                "vouches_flagged": 1,
                "revocation_rate": 0.04,
                "status": "active",
                "last_review": "2025-12-19T00:00:00Z"
            }
        }


# Trust bonuses for different verification methods
ATTESTATION_TRUST_BONUSES = {
    "bootcamp_graduate": 0.15,
    "co_op_member": 0.10,
    "challenge_verified": 0.05,
    "in_person_verified": 0.10,
    "mesh_vouch_verified": 0.05,
}

# Revocation rate thresholds for steward status
STEWARD_REVOCATION_THRESHOLDS = {
    "warning": 0.10,   # 10% revocation rate triggers warning
    "suspended": 0.20,  # 20% revocation rate suspends vouching
}
