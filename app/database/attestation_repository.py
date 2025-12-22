"""Repository for Attestation data access

Handles:
- Cryptographic attestations (threshold signatures)
- Attestation claims (verification via in-person, challenge, mesh)
- Challenge questions
- Steward accountability tracking
"""
import sqlite3
import json
import hashlib
from typing import List, Optional, Dict
from datetime import datetime, UTC
import uuid

from app.models.attestation import (
    Attestation,
    AttestationClaim,
    ChallengeQuestion,
    StewardVouchRecord,
)


class AttestationRepository:
    """Database access for attestations and network import."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Create attestation tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Attestations table (threshold-signed cohort/group membership)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attestations (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                subject_identifier TEXT NOT NULL,
                claims_json TEXT NOT NULL,
                issuer_pubkeys_json TEXT NOT NULL,
                signatures_json TEXT NOT NULL,
                threshold_required INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
        """)

        # Attestation claims table (users claiming attestations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attestation_claims (
                id TEXT PRIMARY KEY,
                attestation_id TEXT NOT NULL,
                claimer_user_id TEXT NOT NULL,
                verification_method TEXT NOT NULL,
                verifier_id TEXT,
                challenge_response TEXT,
                verified_at TEXT NOT NULL,
                trust_granted REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (attestation_id) REFERENCES attestations(id),
                UNIQUE(attestation_id, claimer_user_id)
            )
        """)

        # Challenge questions table (for challenge-response verification)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenge_questions (
                id TEXT PRIMARY KEY,
                attestation_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer_hash TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (attestation_id) REFERENCES attestations(id)
            )
        """)

        # Steward vouching accountability table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS steward_vouch_records (
                steward_id TEXT PRIMARY KEY,
                total_vouches INTEGER DEFAULT 0,
                vouches_revoked INTEGER DEFAULT 0,
                vouches_flagged INTEGER DEFAULT 0,
                revocation_rate REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                last_review TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attestations_type ON attestations(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attestations_subject ON attestations(subject_identifier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_claimer ON attestation_claims(claimer_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_attestation ON attestation_claims(attestation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_challenges_attestation ON challenge_questions(attestation_id)")

        conn.commit()
        conn.close()

    # ===== Attestation Methods =====

    def create_attestation(
        self,
        type: str,
        subject_identifier: str,
        claims: Dict[str, str],
        issuer_pubkeys: List[str],
        signatures: List[str],
        threshold_required: int = 3,
        expires_at: Optional[datetime] = None,
    ) -> Attestation:
        """Create a new attestation with threshold signatures."""
        attestation_id = f"attestation-{uuid.uuid4()}"
        created_at = datetime.now(UTC)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO attestations
                (id, type, subject_identifier, claims_json, issuer_pubkeys_json,
                 signatures_json, threshold_required, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attestation_id,
                type,
                subject_identifier,
                json.dumps(claims),
                json.dumps(issuer_pubkeys),
                json.dumps(signatures),
                threshold_required,
                created_at.isoformat(),
                expires_at.isoformat() if expires_at else None
            ))
            conn.commit()
        finally:
            conn.close()

        return Attestation(
            id=attestation_id,
            type=type,
            subject_identifier=subject_identifier,
            claims=claims,
            issuer_pubkeys=issuer_pubkeys,
            signatures=signatures,
            threshold_required=threshold_required,
            created_at=created_at,
            expires_at=expires_at,
        )

    def get_attestation(self, attestation_id: str) -> Optional[Attestation]:
        """Get an attestation by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, type, subject_identifier, claims_json, issuer_pubkeys_json,
                   signatures_json, threshold_required, created_at, expires_at
            FROM attestations WHERE id = ?
        """, (attestation_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_attestation(row)

    def get_attestations_by_type(self, type: str) -> List[Attestation]:
        """Get all attestations of a specific type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, type, subject_identifier, claims_json, issuer_pubkeys_json,
                   signatures_json, threshold_required, created_at, expires_at
            FROM attestations WHERE type = ?
        """, (type,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_attestation(row) for row in rows]

    def get_attestations_by_subject(self, subject_identifier: str) -> List[Attestation]:
        """Get all attestations for a subject (name/pseudonym)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, type, subject_identifier, claims_json, issuer_pubkeys_json,
                   signatures_json, threshold_required, created_at, expires_at
            FROM attestations WHERE subject_identifier = ?
        """, (subject_identifier,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_attestation(row) for row in rows]

    # ===== Attestation Claim Methods =====

    def create_claim(
        self,
        attestation_id: str,
        claimer_user_id: str,
        verification_method: str,
        trust_granted: float,
        verifier_id: Optional[str] = None,
        challenge_response: Optional[str] = None,
    ) -> AttestationClaim:
        """Create a new attestation claim."""
        claim_id = f"claim-{uuid.uuid4()}"
        verified_at = datetime.now(UTC)
        status = "pending"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO attestation_claims
                (id, attestation_id, claimer_user_id, verification_method,
                 verifier_id, challenge_response, verified_at, trust_granted, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id,
                attestation_id,
                claimer_user_id,
                verification_method,
                verifier_id,
                challenge_response,
                verified_at.isoformat(),
                trust_granted,
                status,
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Claim already exists
            conn.close()
            return self.get_claim_by_user_and_attestation(claimer_user_id, attestation_id)
        finally:
            if conn:
                conn.close()

        return AttestationClaim(
            id=claim_id,
            attestation_id=attestation_id,
            claimer_user_id=claimer_user_id,
            verification_method=verification_method,
            verifier_id=verifier_id,
            challenge_response=challenge_response,
            verified_at=verified_at,
            trust_granted=trust_granted,
            status=status,
        )

    def update_claim_status(self, claim_id: str, status: str) -> bool:
        """Update claim status (pending -> verified/rejected)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE attestation_claims SET status = ? WHERE id = ?
        """, (status, claim_id))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return updated

    def get_claim(self, claim_id: str) -> Optional[AttestationClaim]:
        """Get a claim by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, attestation_id, claimer_user_id, verification_method,
                   verifier_id, challenge_response, verified_at, trust_granted, status
            FROM attestation_claims WHERE id = ?
        """, (claim_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_claim(row)

    def get_claim_by_user_and_attestation(
        self,
        user_id: str,
        attestation_id: str
    ) -> Optional[AttestationClaim]:
        """Get a user's claim for a specific attestation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, attestation_id, claimer_user_id, verification_method,
                   verifier_id, challenge_response, verified_at, trust_granted, status
            FROM attestation_claims
            WHERE claimer_user_id = ? AND attestation_id = ?
        """, (user_id, attestation_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_claim(row)

    def get_claims_for_user(self, user_id: str) -> List[AttestationClaim]:
        """Get all claims by a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, attestation_id, claimer_user_id, verification_method,
                   verifier_id, challenge_response, verified_at, trust_granted, status
            FROM attestation_claims WHERE claimer_user_id = ?
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_claim(row) for row in rows]

    def get_verified_claims_for_user(self, user_id: str) -> List[AttestationClaim]:
        """Get only verified claims for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, attestation_id, claimer_user_id, verification_method,
                   verifier_id, challenge_response, verified_at, trust_granted, status
            FROM attestation_claims
            WHERE claimer_user_id = ? AND status = 'verified'
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_claim(row) for row in rows]

    # ===== Challenge Question Methods =====

    def create_challenge(
        self,
        attestation_id: str,
        question: str,
        answer: str,
        created_by: str,
    ) -> ChallengeQuestion:
        """Create a challenge question for an attestation."""
        challenge_id = f"challenge-{uuid.uuid4()}"
        created_at = datetime.now(UTC)

        # Hash the answer (lowercase, trimmed)
        answer_normalized = answer.lower().strip()
        answer_hash = hashlib.sha256(answer_normalized.encode('utf-8')).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO challenge_questions
            (id, attestation_id, question, answer_hash, created_by, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            challenge_id,
            attestation_id,
            question,
            answer_hash,
            created_by,
            created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return ChallengeQuestion(
            id=challenge_id,
            attestation_id=attestation_id,
            question=question,
            answer_hash=answer_hash,
            created_by=created_by,
            created_at=created_at,
            active=True,
        )

    def get_active_challenges(self, attestation_id: str) -> List[ChallengeQuestion]:
        """Get active challenge questions for an attestation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, attestation_id, question, answer_hash, created_by, created_at, active
            FROM challenge_questions
            WHERE attestation_id = ? AND active = 1
        """, (attestation_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_challenge(row) for row in rows]

    def verify_challenge_answer(self, challenge_id: str, answer: str) -> bool:
        """Verify if an answer to a challenge is correct."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT answer_hash FROM challenge_questions WHERE id = ?
        """, (challenge_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        stored_hash = row[0]
        answer_normalized = answer.lower().strip()
        answer_hash = hashlib.sha256(answer_normalized.encode('utf-8')).hexdigest()

        return answer_hash == stored_hash

    # ===== Steward Accountability Methods =====

    def get_or_create_steward_record(self, steward_id: str) -> StewardVouchRecord:
        """Get steward vouch record or create if doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT steward_id, total_vouches, vouches_revoked, vouches_flagged,
                   revocation_rate, status, last_review, notes
            FROM steward_vouch_records WHERE steward_id = ?
        """, (steward_id,))

        row = cursor.fetchone()

        if row:
            conn.close()
            return self._row_to_steward_record(row)

        # Create new record
        last_review = datetime.now(UTC)
        cursor.execute("""
            INSERT INTO steward_vouch_records
            (steward_id, total_vouches, vouches_revoked, vouches_flagged,
             revocation_rate, status, last_review)
            VALUES (?, 0, 0, 0, 0.0, 'active', ?)
        """, (steward_id, last_review.isoformat()))

        conn.commit()
        conn.close()

        return StewardVouchRecord(
            steward_id=steward_id,
            total_vouches=0,
            vouches_revoked=0,
            vouches_flagged=0,
            revocation_rate=0.0,
            status="active",
            last_review=last_review,
        )

    def update_steward_vouch_stats(
        self,
        steward_id: str,
        total_vouches: int,
        vouches_revoked: int,
        vouches_flagged: int,
    ) -> StewardVouchRecord:
        """Update steward vouching statistics."""
        revocation_rate = vouches_revoked / total_vouches if total_vouches > 0 else 0.0

        # Determine status based on revocation rate
        status = "active"
        if revocation_rate >= 0.20:
            status = "suspended"
        elif revocation_rate >= 0.10:
            status = "warning"

        last_review = datetime.now(UTC)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE steward_vouch_records
            SET total_vouches = ?,
                vouches_revoked = ?,
                vouches_flagged = ?,
                revocation_rate = ?,
                status = ?,
                last_review = ?
            WHERE steward_id = ?
        """, (
            total_vouches,
            vouches_revoked,
            vouches_flagged,
            revocation_rate,
            status,
            last_review.isoformat(),
            steward_id,
        ))

        conn.commit()
        conn.close()

        return StewardVouchRecord(
            steward_id=steward_id,
            total_vouches=total_vouches,
            vouches_revoked=vouches_revoked,
            vouches_flagged=vouches_flagged,
            revocation_rate=revocation_rate,
            status=status,
            last_review=last_review,
        )

    # ===== Helper Methods =====

    def _row_to_attestation(self, row) -> Attestation:
        """Convert database row to Attestation model."""
        return Attestation(
            id=row[0],
            type=row[1],
            subject_identifier=row[2],
            claims=json.loads(row[3]),
            issuer_pubkeys=json.loads(row[4]),
            signatures=json.loads(row[5]),
            threshold_required=row[6],
            created_at=datetime.fromisoformat(row[7]),
            expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
        )

    def _row_to_claim(self, row) -> AttestationClaim:
        """Convert database row to AttestationClaim model."""
        return AttestationClaim(
            id=row[0],
            attestation_id=row[1],
            claimer_user_id=row[2],
            verification_method=row[3],
            verifier_id=row[4],
            challenge_response=row[5],
            verified_at=datetime.fromisoformat(row[6]),
            trust_granted=row[7],
            status=row[8],
        )

    def _row_to_challenge(self, row) -> ChallengeQuestion:
        """Convert database row to ChallengeQuestion model."""
        return ChallengeQuestion(
            id=row[0],
            attestation_id=row[1],
            question=row[2],
            answer_hash=row[3],
            created_by=row[4],
            created_at=datetime.fromisoformat(row[5]),
            active=bool(row[6]),
        )

    def _row_to_steward_record(self, row) -> StewardVouchRecord:
        """Convert database row to StewardVouchRecord model."""
        return StewardVouchRecord(
            steward_id=row[0],
            total_vouches=row[1],
            vouches_revoked=row[2],
            vouches_flagged=row[3],
            revocation_rate=row[4],
            status=row[5],
            last_review=datetime.fromisoformat(row[6]),
            notes=row[7],
        )
