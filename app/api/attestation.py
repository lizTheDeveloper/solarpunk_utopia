"""Network Import API - Attestation Endpoints

Enables importing existing communities WITHOUT external platforms:
- Steward bulk vouching
- Threshold-signed attestations (3 of 5 stewards)
- Challenge-response verification
- In-person verification
- Mesh vouch verification

All methods work fully offline (no internet required).
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from datetime import datetime
import os

from app.models.attestation import (
    Attestation,
    AttestationClaim,
    ChallengeQuestion,
    BulkVouchRequest,
    StewardVouchRecord,
)
from app.database.attestation_repository import AttestationRepository
from app.database.vouch_repository import VouchRepository
from app.services.attestation_service import AttestationService
from app.services.crypto_service import CryptoService
from app.services.web_of_trust_service import WebOfTrustService
from app.auth.middleware import get_current_user


router = APIRouter(prefix="/attestation", tags=["network-import"])


# Dependency injection
def get_attestation_repo():
    """Get AttestationRepository instance."""
    db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
    return AttestationRepository(db_path)


def get_vouch_repo():
    """Get VouchRepository instance."""
    db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
    return VouchRepository(db_path)


def get_crypto_service():
    """Get CryptoService instance."""
    return CryptoService()


def get_attestation_service(
    attestation_repo: AttestationRepository = Depends(get_attestation_repo),
    vouch_repo: VouchRepository = Depends(get_vouch_repo),
    crypto_service: CryptoService = Depends(get_crypto_service),
) -> AttestationService:
    """Get AttestationService instance."""
    trust_service = WebOfTrustService(vouch_repo)
    return AttestationService(
        attestation_repo=attestation_repo,
        vouch_repo=vouch_repo,
        crypto_service=crypto_service,
        trust_service=trust_service,
    )


# ===== Attestation Creation (Threshold Signatures) =====

@router.post("/create", response_model=Dict, summary="Create threshold-signed attestation")
async def create_attestation(
    type: str,
    subject_identifier: str,
    claims: Dict[str, str],
    issuer_pubkeys: List[str],
    signatures: List[str],
    threshold_required: int = 3,
    expires_at: Optional[str] = None,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Create a threshold-signed attestation for cohort/group membership.

    Requires:
    - Multiple stewards sign (threshold: 3 of 5)
    - NO email/phone in subject_identifier (names/pseudonyms only)
    - All verification happens offline

    Args:
        type: 'cohort', 'membership', 'graduation', 'organization'
        subject_identifier: Name or pseudonym (NO email/phone)
        claims: Key-value claims like {'cohort': '2019-fall', 'role': 'graduate'}
        issuer_pubkeys: Public keys of all signers
        signatures: Signatures from each signer
        threshold_required: Minimum signatures needed (default 3)
        expires_at: Optional expiration ISO timestamp

    Returns:
        Created attestation or error
    """
    expires = datetime.fromisoformat(expires_at) if expires_at else None

    attestation, success, message = service.create_attestation(
        type=type,
        subject_identifier=subject_identifier,
        claims=claims,
        issuer_pubkeys=issuer_pubkeys,
        signatures=signatures,
        threshold_required=threshold_required,
        expires_at=expires,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "attestation": attestation,
        "message": message
    }


@router.get("/{attestation_id}", response_model=Attestation, summary="Get attestation by ID")
async def get_attestation(
    attestation_id: str,
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
):
    """Get an attestation by ID."""
    attestation = repo.get_attestation(attestation_id)
    if not attestation:
        raise HTTPException(status_code=404, detail="Attestation not found")

    return attestation


@router.get("/type/{type}", response_model=List[Attestation], summary="Get attestations by type")
async def get_attestations_by_type(
    type: str,
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
):
    """Get all attestations of a specific type."""
    attestations = repo.get_attestations_by_type(type)
    return attestations


@router.get("/verify/{attestation_id}", summary="Verify attestation signatures")
async def verify_attestation(
    attestation_id: str,
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
    service: AttestationService = Depends(get_attestation_service),
):
    """Verify an attestation's threshold signatures."""
    attestation = repo.get_attestation(attestation_id)
    if not attestation:
        raise HTTPException(status_code=404, detail="Attestation not found")

    is_valid, valid_count = service.verify_attestation_signatures(attestation)

    return {
        "attestation_id": attestation_id,
        "is_valid": is_valid,
        "valid_signatures": valid_count,
        "threshold_required": attestation.threshold_required,
        "message": f"Valid: {is_valid} ({valid_count}/{attestation.threshold_required} signatures)"
    }


# ===== Attestation Claims (Verification Methods) =====

@router.post("/claim/in-person", response_model=Dict, summary="Claim attestation with in-person verification")
async def claim_in_person(
    attestation_id: str,
    verifier_steward_id: str,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Claim an attestation with in-person verification by steward.

    This is the gold standard: steward confirms identity face-to-face.

    Requires:
    - Verifier must be steward (trust >= 0.9)
    - In-person confirmation

    Works fully offline.
    """
    claim, success, message = service.claim_attestation_in_person(
        attestation_id=attestation_id,
        claimer_user_id=current_user.id,
        verifier_steward_id=verifier_steward_id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "claim": claim,
        "message": message
    }


@router.post("/claim/challenge", response_model=Dict, summary="Claim attestation via challenge-response")
async def claim_challenge(
    attestation_id: str,
    challenge_id: str,
    answer: str,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Claim an attestation by answering a challenge question.

    Only real cohort members would know the answer.

    Works fully offline.
    """
    claim, success, message = service.claim_attestation_challenge(
        attestation_id=attestation_id,
        claimer_user_id=current_user.id,
        challenge_id=challenge_id,
        answer=answer,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "claim": claim,
        "message": message
    }


@router.post("/claim/mesh-vouch", response_model=Dict, summary="Claim attestation via mesh vouch")
async def claim_mesh_vouch(
    attestation_id: str,
    voucher_cohort_member_id: str,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Claim an attestation via vouch from existing verified cohort member.

    Requires:
    - Voucher has verified the same attestation
    - Voucher has trust >= 0.7

    Works fully offline via mesh.
    """
    claim, success, message = service.claim_attestation_mesh_vouch(
        attestation_id=attestation_id,
        claimer_user_id=current_user.id,
        voucher_cohort_member_id=voucher_cohort_member_id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "claim": claim,
        "message": message
    }


@router.get("/claims/my", response_model=List[AttestationClaim], summary="Get my attestation claims")
async def get_my_claims(
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
):
    """Get all attestation claims for current user."""
    claims = repo.get_claims_for_user(current_user.id)
    return claims


@router.get("/claims/verified", response_model=List[AttestationClaim], summary="Get my verified claims")
async def get_my_verified_claims(
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
):
    """Get only verified attestation claims for current user."""
    claims = repo.get_verified_claims_for_user(current_user.id)
    return claims


# ===== Challenge Questions =====

@router.post("/challenge/create", response_model=Dict, summary="Create challenge question (steward only)")
async def create_challenge(
    attestation_id: str,
    question: str,
    answer: str,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Create a challenge question for an attestation.

    Only stewards can create challenges.
    Only real cohort members would know the answer.

    Example: "What city was the 2019 bootcamp in?"
    """
    challenge, success, message = service.create_challenge_question(
        attestation_id=attestation_id,
        question=question,
        answer=answer,
        created_by=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=403, detail=message)

    return {
        "challenge_id": challenge.id,
        "message": message
    }


@router.get("/challenge/{attestation_id}", response_model=List[ChallengeQuestion], summary="Get active challenges")
async def get_challenges(
    attestation_id: str,
    current_user=Depends(get_current_user),
    repo: AttestationRepository = Depends(get_attestation_repo),
):
    """Get active challenge questions for an attestation."""
    challenges = repo.get_active_challenges(attestation_id)

    # Don't expose answer hashes to non-stewards
    for challenge in challenges:
        challenge.answer_hash = "***REDACTED***"

    return challenges


# ===== Steward Bulk Vouching =====

@router.post("/bulk-vouch", summary="Bulk vouch for multiple people (steward only)")
async def bulk_vouch(
    request: BulkVouchRequest,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Steward vouches for multiple people they know personally.

    This is for importing existing communities WITHOUT external platforms.

    Requires:
    - Caller is steward (trust >= 0.9)
    - Steward attests "I have met these people in person"

    Works fully offline.
    """
    vouches, failed, message = service.bulk_vouch(
        steward_id=current_user.id,
        request=request,
    )

    return {
        "vouches_created": len(vouches),
        "failed_identifiers": failed,
        "message": message,
        "vouches": vouches
    }


# ===== Steward Accountability =====

@router.get("/steward/accountability/{steward_id}", response_model=StewardVouchRecord, summary="Get steward accountability")
async def get_steward_accountability(
    steward_id: str,
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Get steward's vouching accountability record.

    Shows:
    - Total vouches given
    - Vouches revoked (infiltrators)
    - Revocation rate
    - Status (active/warning/suspended)

    Used to track steward patterns and catch bad imports.
    """
    record = service.get_steward_accountability(steward_id)
    return record


@router.get("/steward/my-accountability", response_model=StewardVouchRecord, summary="Get my accountability")
async def get_my_accountability(
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """Get your own steward accountability record."""
    record = service.get_steward_accountability(current_user.id)
    return record


# ===== Trust Calculation with Attestations =====

@router.get("/trust-bonus", summary="Get trust bonus from attestations")
async def get_trust_bonus(
    current_user=Depends(get_current_user),
    service: AttestationService = Depends(get_attestation_service),
):
    """
    Get trust bonus from verified attestations.

    This bonus is added to base trust from vouch chain.

    Returns:
        Total trust bonus (0.0 - 0.3)
    """
    bonus = service.get_user_attestation_trust_bonus(current_user.id)

    return {
        "user_id": current_user.id,
        "attestation_trust_bonus": bonus,
        "max_possible": 0.3,
        "message": f"Attestations grant +{bonus:.2f} trust bonus"
    }
