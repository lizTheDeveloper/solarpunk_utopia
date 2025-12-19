"""Attestation Service - Network Import Business Logic

Handles:
- Creating threshold-signed attestations (multiple stewards sign)
- Verifying threshold signatures (3 of 5 required)
- Processing attestation claims (in-person, challenge, mesh vouch)
- Steward bulk vouching
- Accountability tracking

All methods work WITHOUT external platforms or internet.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

from app.models.attestation import (
    Attestation,
    AttestationClaim,
    ChallengeQuestion,
    BulkVouchRequest,
    StewardVouchRecord,
    ATTESTATION_TRUST_BONUSES,
    STEWARD_REVOCATION_THRESHOLDS,
)
from app.models.vouch import Vouch
from app.database.attestation_repository import AttestationRepository
from app.database.vouch_repository import VouchRepository
from app.services.crypto_service import CryptoService
from app.services.web_of_trust_service import WebOfTrustService


class AttestationService:
    """Service for creating and verifying attestations (network import)."""

    def __init__(
        self,
        attestation_repo: AttestationRepository,
        vouch_repo: VouchRepository,
        crypto_service: CryptoService,
        trust_service: WebOfTrustService,
    ):
        self.attestation_repo = attestation_repo
        self.vouch_repo = vouch_repo
        self.crypto_service = crypto_service
        self.trust_service = trust_service

    # ===== Threshold Signature Attestations =====

    def create_attestation(
        self,
        type: str,
        subject_identifier: str,
        claims: Dict[str, str],
        issuer_pubkeys: List[str],
        signatures: List[str],
        threshold_required: int = 3,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[Attestation, bool, str]:
        """Create a threshold-signed attestation.

        Args:
            type: Attestation type (cohort, membership, etc.)
            subject_identifier: Name/pseudonym (NO email/phone)
            claims: Key-value claims
            issuer_pubkeys: Public keys of all signers
            signatures: Signatures from each issuer
            threshold_required: Minimum signatures needed (default 3)
            expires_at: Optional expiration

        Returns:
            (attestation, is_valid, message)
        """
        # Verify threshold signatures
        if len(signatures) < threshold_required:
            return (
                None,
                False,
                f"Insufficient signatures: need {threshold_required}, got {len(signatures)}"
            )

        if len(signatures) != len(issuer_pubkeys):
            return (
                None,
                False,
                "Signature count must match issuer count"
            )

        # Create canonical data to verify
        canonical_data = json.dumps({
            "type": type,
            "subject_identifier": subject_identifier,
            "claims": claims,
            "threshold_required": threshold_required,
        }, sort_keys=True)

        # Verify each signature
        valid_signatures = 0
        for i, (pubkey, signature) in enumerate(zip(issuer_pubkeys, signatures)):
            try:
                # Convert pubkey string to PEM format if needed
                if not pubkey.startswith("-----BEGIN"):
                    # Assume it's a raw pubkey, wrap it
                    pubkey_pem = f"-----BEGIN PUBLIC KEY-----\n{pubkey}\n-----END PUBLIC KEY-----"
                else:
                    pubkey_pem = pubkey

                if self.crypto_service.verify(canonical_data, signature, pubkey_pem):
                    valid_signatures += 1
            except Exception as e:
                # Invalid signature or pubkey format
                continue

        if valid_signatures < threshold_required:
            return (
                None,
                False,
                f"Threshold not met: need {threshold_required} valid signatures, got {valid_signatures}"
            )

        # Create the attestation
        attestation = self.attestation_repo.create_attestation(
            type=type,
            subject_identifier=subject_identifier,
            claims=claims,
            issuer_pubkeys=issuer_pubkeys,
            signatures=signatures,
            threshold_required=threshold_required,
            expires_at=expires_at,
        )

        return (attestation, True, f"Attestation created with {valid_signatures} valid signatures")

    def verify_attestation_signatures(self, attestation: Attestation) -> Tuple[bool, int]:
        """Verify an attestation's threshold signatures.

        Returns:
            (is_valid, valid_signature_count)
        """
        canonical_data = json.dumps({
            "type": attestation.type,
            "subject_identifier": attestation.subject_identifier,
            "claims": attestation.claims,
            "threshold_required": attestation.threshold_required,
        }, sort_keys=True)

        valid_signatures = 0
        for pubkey, signature in zip(attestation.issuer_pubkeys, attestation.signatures):
            try:
                if not pubkey.startswith("-----BEGIN"):
                    pubkey_pem = f"-----BEGIN PUBLIC KEY-----\n{pubkey}\n-----END PUBLIC KEY-----"
                else:
                    pubkey_pem = pubkey

                if self.crypto_service.verify(canonical_data, signature, pubkey_pem):
                    valid_signatures += 1
            except:
                continue

        is_valid = valid_signatures >= attestation.threshold_required
        return (is_valid, valid_signatures)

    # ===== Attestation Claims and Verification =====

    def claim_attestation_in_person(
        self,
        attestation_id: str,
        claimer_user_id: str,
        verifier_steward_id: str,
    ) -> Tuple[AttestationClaim, bool, str]:
        """Claim an attestation with in-person verification by steward.

        This is the gold standard: steward confirms identity face-to-face.

        Args:
            attestation_id: Attestation being claimed
            claimer_user_id: User claiming it
            verifier_steward_id: Steward who verified in person

        Returns:
            (claim, success, message)
        """
        # Verify steward has sufficient trust
        steward_trust = self.trust_service.compute_trust_score(verifier_steward_id)
        if steward_trust.computed_trust < 0.9:  # Steward threshold
            return (
                None,
                False,
                f"Verifier must be steward (trust >= 0.9), has {steward_trust.computed_trust:.2f}"
            )

        # Get attestation
        attestation = self.attestation_repo.get_attestation(attestation_id)
        if not attestation:
            return (None, False, "Attestation not found")

        # Check if already claimed
        existing_claim = self.attestation_repo.get_claim_by_user_and_attestation(
            claimer_user_id,
            attestation_id
        )
        if existing_claim:
            return (existing_claim, False, "Already claimed this attestation")

        # Determine trust bonus based on attestation type
        trust_bonus = ATTESTATION_TRUST_BONUSES.get("in_person_verified", 0.10)
        if "cohort" in attestation.claims:
            trust_bonus += ATTESTATION_TRUST_BONUSES.get("bootcamp_graduate", 0.15)
        elif "organization" in attestation.claims:
            trust_bonus += ATTESTATION_TRUST_BONUSES.get("co_op_member", 0.10)

        # Create claim
        claim = self.attestation_repo.create_claim(
            attestation_id=attestation_id,
            claimer_user_id=claimer_user_id,
            verification_method="in_person",
            trust_granted=min(trust_bonus, 0.25),  # Cap at 0.25
            verifier_id=verifier_steward_id,
        )

        # Update to verified status
        self.attestation_repo.update_claim_status(claim.id, "verified")

        # Recompute claimer's trust (they now have attestation bonus)
        self.trust_service.compute_trust_score(claimer_user_id, force_recompute=True)

        return (claim, True, "Attestation claimed and verified in-person")

    def claim_attestation_challenge(
        self,
        attestation_id: str,
        claimer_user_id: str,
        challenge_id: str,
        answer: str,
    ) -> Tuple[AttestationClaim, bool, str]:
        """Claim an attestation by answering challenge question.

        Only real members would know the answer.

        Args:
            attestation_id: Attestation being claimed
            claimer_user_id: User claiming it
            challenge_id: Challenge question ID
            answer: User's answer

        Returns:
            (claim, success, message)
        """
        # Verify answer
        is_correct = self.attestation_repo.verify_challenge_answer(challenge_id, answer)
        if not is_correct:
            return (None, False, "Incorrect answer")

        # Get attestation
        attestation = self.attestation_repo.get_attestation(attestation_id)
        if not attestation:
            return (None, False, "Attestation not found")

        # Check if already claimed
        existing_claim = self.attestation_repo.get_claim_by_user_and_attestation(
            claimer_user_id,
            attestation_id
        )
        if existing_claim:
            return (existing_claim, False, "Already claimed this attestation")

        # Challenge verification grants lower trust than in-person
        trust_bonus = ATTESTATION_TRUST_BONUSES.get("challenge_verified", 0.05)

        # Create claim
        import hashlib
        answer_hash = hashlib.sha256(answer.lower().strip().encode('utf-8')).hexdigest()

        claim = self.attestation_repo.create_claim(
            attestation_id=attestation_id,
            claimer_user_id=claimer_user_id,
            verification_method="challenge",
            trust_granted=trust_bonus,
            challenge_response=answer_hash,
        )

        # Update to verified status
        self.attestation_repo.update_claim_status(claim.id, "verified")

        # Recompute claimer's trust
        self.trust_service.compute_trust_score(claimer_user_id, force_recompute=True)

        return (claim, True, "Attestation claimed via challenge-response")

    def claim_attestation_mesh_vouch(
        self,
        attestation_id: str,
        claimer_user_id: str,
        voucher_cohort_member_id: str,
    ) -> Tuple[AttestationClaim, bool, str]:
        """Claim an attestation via vouch from existing verified cohort member.

        The voucher must have already verified the same attestation.

        Args:
            attestation_id: Attestation being claimed
            claimer_user_id: User claiming it
            voucher_cohort_member_id: Existing verified member who vouches

        Returns:
            (claim, success, message)
        """
        # Verify voucher has verified this attestation
        voucher_claim = self.attestation_repo.get_claim_by_user_and_attestation(
            voucher_cohort_member_id,
            attestation_id
        )
        if not voucher_claim or voucher_claim.status != "verified":
            return (
                None,
                False,
                "Voucher must have verified this attestation first"
            )

        # Verify voucher has sufficient trust to vouch
        can_vouch = self.trust_service.can_vouch_for_others(voucher_cohort_member_id)
        if not can_vouch:
            return (
                None,
                False,
                "Voucher does not have sufficient trust to vouch (need 0.7)"
            )

        # Get attestation
        attestation = self.attestation_repo.get_attestation(attestation_id)
        if not attestation:
            return (None, False, "Attestation not found")

        # Check if already claimed
        existing_claim = self.attestation_repo.get_claim_by_user_and_attestation(
            claimer_user_id,
            attestation_id
        )
        if existing_claim:
            return (existing_claim, False, "Already claimed this attestation")

        # Mesh vouch grants minimal trust
        trust_bonus = ATTESTATION_TRUST_BONUSES.get("mesh_vouch_verified", 0.05)

        # Create claim
        claim = self.attestation_repo.create_claim(
            attestation_id=attestation_id,
            claimer_user_id=claimer_user_id,
            verification_method="mesh_vouch",
            trust_granted=trust_bonus,
            verifier_id=voucher_cohort_member_id,
        )

        # Update to verified status
        self.attestation_repo.update_claim_status(claim.id, "verified")

        # Recompute claimer's trust
        self.trust_service.compute_trust_score(claimer_user_id, force_recompute=True)

        return (claim, True, "Attestation claimed via mesh vouch")

    # ===== Steward Bulk Vouching =====

    def bulk_vouch(
        self,
        steward_id: str,
        request: BulkVouchRequest,
    ) -> Tuple[List[Vouch], List[str], str]:
        """Steward vouches for multiple people they know personally.

        This is for importing existing communities without external platforms.

        Args:
            steward_id: Steward doing the vouching
            request: Bulk vouch request with list of people

        Returns:
            (vouches_created, failed_identifiers, message)
        """
        # Verify steward has sufficient trust
        steward_trust = self.trust_service.compute_trust_score(steward_id)
        if steward_trust.computed_trust < 0.9:
            return (
                [],
                [v["identifier"] for v in request.vouchees],
                f"Must be steward (trust >= 0.9), have {steward_trust.computed_trust:.2f}"
            )

        vouches_created = []
        failed = []

        for vouchee_data in request.vouchees:
            identifier = vouchee_data.get("identifier")
            name = vouchee_data.get("name", "Unknown")

            # In a real system, we'd look up user by identifier
            # For now, assume identifier IS the user_id (public key)
            vouchee_id = identifier

            # Check if vouch already exists
            existing = self.vouch_repo.get_vouches_for_user(vouchee_id, include_revoked=False)
            already_vouched = any(v.voucher_id == steward_id for v in existing)

            if already_vouched:
                failed.append(identifier)
                continue

            # Create vouch
            try:
                vouch = self.vouch_repo.create_vouch(
                    voucher_id=steward_id,
                    vouchee_id=vouchee_id,
                    context=request.context,
                )
                vouches_created.append(vouch)

                # Recompute vouchee trust
                self.trust_service.compute_trust_score(vouchee_id, force_recompute=True)
            except Exception as e:
                failed.append(identifier)

        # Update steward accountability record
        steward_record = self.attestation_repo.get_or_create_steward_record(steward_id)
        new_total = steward_record.total_vouches + len(vouches_created)
        self.attestation_repo.update_steward_vouch_stats(
            steward_id=steward_id,
            total_vouches=new_total,
            vouches_revoked=steward_record.vouches_revoked,
            vouches_flagged=steward_record.vouches_flagged,
        )

        message = f"Created {len(vouches_created)} vouches"
        if failed:
            message += f", {len(failed)} failed (already vouched or error)"

        return (vouches_created, failed, message)

    # ===== Challenge Questions =====

    def create_challenge_question(
        self,
        attestation_id: str,
        question: str,
        answer: str,
        created_by: str,
    ) -> Tuple[ChallengeQuestion, bool, str]:
        """Create a challenge question for an attestation.

        Only stewards can create challenges.

        Args:
            attestation_id: Attestation this challenge verifies
            question: The question
            answer: Correct answer
            created_by: Steward creating this

        Returns:
            (challenge, success, message)
        """
        # Verify creator is steward
        creator_trust = self.trust_service.compute_trust_score(created_by)
        if creator_trust.computed_trust < 0.9:
            return (
                None,
                False,
                f"Must be steward (trust >= 0.9), have {creator_trust.computed_trust:.2f}"
            )

        # Create challenge
        challenge = self.attestation_repo.create_challenge(
            attestation_id=attestation_id,
            question=question,
            answer=answer,
            created_by=created_by,
        )

        return (challenge, True, "Challenge question created")

    # ===== Steward Accountability =====

    def update_steward_accountability_on_revocation(
        self,
        vouch_id: str,
    ) -> StewardVouchRecord:
        """Update steward accountability when one of their vouches is revoked.

        Called automatically when a vouch is revoked.

        Args:
            vouch_id: Vouch that was revoked

        Returns:
            Updated steward record
        """
        # Get the vouch
        vouch = self.vouch_repo.get_vouch(vouch_id)
        if not vouch:
            return None

        steward_id = vouch.voucher_id

        # Get all vouches by this steward
        all_vouches = self.vouch_repo.get_vouches_by_user(steward_id)
        total_vouches = len(all_vouches)
        vouches_revoked = len([v for v in all_vouches if v.revoked])

        # Get steward record
        steward_record = self.attestation_repo.get_or_create_steward_record(steward_id)

        # Update stats
        updated_record = self.attestation_repo.update_steward_vouch_stats(
            steward_id=steward_id,
            total_vouches=total_vouches,
            vouches_revoked=vouches_revoked,
            vouches_flagged=steward_record.vouches_flagged,
        )

        return updated_record

    def get_steward_accountability(self, steward_id: str) -> StewardVouchRecord:
        """Get steward's vouching accountability record."""
        return self.attestation_repo.get_or_create_steward_record(steward_id)

    # ===== Trust Calculation with Attestation Bonuses =====

    def get_user_attestation_trust_bonus(self, user_id: str) -> float:
        """Calculate total trust bonus from verified attestations.

        This bonus is added to base trust from vouch chain.

        Args:
            user_id: User to calculate bonus for

        Returns:
            Total trust bonus (0.0 - 0.3)
        """
        verified_claims = self.attestation_repo.get_verified_claims_for_user(user_id)

        total_bonus = sum(claim.trust_granted for claim in verified_claims)

        # Cap at 0.3 to prevent attestation farming
        return min(total_bonus, 0.3)
