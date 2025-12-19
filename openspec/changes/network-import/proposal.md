# Proposal: Network Import - Bring Existing Communities (No Big Tech)

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-19
**Complexity:** 2 systems
**Timeline:** WORKSHOP BLOCKER

## Problem Statement

You have 500,000 people in existing networks. They already trust each other. They already have relationships.

Starting from zero would be insane. We need to import existing trust graphs.

**BUT:** We cannot create dependencies on big tech platforms. OAuth to Hipcamp/Google/GitHub means:
- Those platforms can cut us off
- Those platforms can be pressured to share data
- Those platforms become attack surfaces
- We're not building independence if we depend on them

## Proposed Solution

**Zero OAuth. Zero big tech dependencies.**

Import trust through:
1. **Steward vouching** - Community leaders vouch for their communities
2. **Cryptographic proof of membership** - Signed attestations
3. **In-person verification** - The original web of trust
4. **Existing out-of-band trust** - You already know these people

### Import Methods

| Method | How It Works | Trust Level |
|--------|--------------|-------------|
| **Steward Import** | Trusted steward vouches for list of people they personally know | Steward's trust × 0.8 |
| **Cohort Attestation** | Admin signs "these people graduated bootcamp" - cryptographic proof | 0.6 baseline |
| **Event Verification** | You were at the workshop, steward saw you | Event trust (limited) |
| **Personal Vouch** | Friend vouches for friend | Standard chain |
| **Challenge-Response** | "Only real members would know X" - shared secret verification | 0.5 after verification |

### NO OAuth. NO APIs. NO Platform Dependencies.

The network must function if:
- All tech platforms cut us off tomorrow
- The internet goes down
- Every corporation becomes hostile

## Requirements

### Requirement: Steward Bulk Vouch

The system SHALL allow stewards to vouch for multiple people they personally know.

#### Scenario: Co-op Leader Import
- GIVEN Carlos runs a food co-op and knows all 50 members personally
- WHEN Carlos becomes a network steward
- THEN he can create vouches for members he's met in person
- AND each vouch includes "I have met this person" attestation
- AND those members receive invites
- AND when they join, they get Carlos's vouch automatically

### Requirement: Cryptographic Cohort Attestation

The system SHALL support signed attestations for cohorts.

#### Scenario: Bootcamp Alumni
- GIVEN Liz has the graduation records for bootcamp cohorts
- WHEN Liz (or designated admin) signs an attestation "email X graduated cohort Y"
- THEN that attestation is stored in the network
- AND when someone with that email joins, they can claim the attestation
- AND their email is verified (they must control it)
- AND they receive the trust level associated with that attestation

### Requirement: Challenge-Response Verification

The system SHALL support shared-secret verification.

#### Scenario: "Real Members Know"
- GIVEN a community has shared knowledge only real members would know
- WHEN the community sets up a challenge question
- THEN new members claiming that community must answer correctly
- AND correct answer grants partial trust
- AND this is used alongside other verification, not alone

### Requirement: No External Platform Dependency

The system SHALL NOT require any external platform for trust verification.

#### Scenario: Platform Cutoff
- GIVEN all major tech platforms refuse to work with us
- WHEN new members need to join
- THEN all import methods still work
- AND no functionality is degraded
- AND the network continues operating

### Requirement: Steward Accountability

The system SHALL track who vouched for whom.

#### Scenario: Bad Import
- GIVEN Carlos vouched for 50 people
- WHEN 3 of them turn out to be infiltrators
- THEN Carlos's pattern is flagged for review
- AND his vouching privileges may be suspended
- AND legitimate members he vouched can be re-verified through other channels

## Import Flows

### Steward Import Flow
```
1. Steward has list of people they personally know
2. For each person:
   a. Steward attests "I have met this person in person"
   b. Steward provides contact method (email, phone, or mesh ID)
3. System generates invitations
4. When person joins, steward vouch is applied
5. Person immediately has trust from steward chain
```

### Cohort Attestation Flow (No Internet Required)
```
1. Multiple stewards (threshold: 3 of 5) sign attestation together
2. Attestation: "Person with name X from CohortY" (no email needed)
3. Attestation distributed via mesh to all nodes
4. Person joins network, claims attestation
5. Verification via:
   a. In-person: steward confirms identity face-to-face, OR
   b. Challenge: answer cohort-specific question only members know, OR
   c. Mesh vouch: another verified cohort member vouches
6. Claim is recorded, trust applied
```

### Event Flow (already designed)
```
1. Steward creates event with QR
2. Attendees scan, get event-scoped trust
3. During event, steward can upgrade to full vouch for people met
4. Post-event, non-vouched members prompted to get vouches or lose access
```

## Data Model

```python
class Attestation:
    id: str
    type: str                  # "cohort", "membership", "graduation"
    subject_identifier: str     # name or pseudonym (NO email/phone)
    claims: Dict[str, str]     # "cohort": "2019-fall", "role": "graduate"
    issuer_pubkeys: List[str]  # Multiple signers required (threshold)
    signatures: List[str]      # Threshold signatures (3 of 5)
    created_at: datetime
    expires_at: Optional[datetime]

class AttestationClaim:
    attestation_id: str
    claimer_user_id: str
    verification_method: str   # "in_person", "challenge", "mesh_vouch"
    verifier_id: str           # Who verified (steward or cohort member)
    verified_at: datetime
    trust_granted: float
```

## Trust Calculation (No Platforms)

```
Base trust from vouch chain (standard)
  +
Attestation bonus (if verified):
  - Bootcamp graduate: +0.15
  - Known co-op member: +0.10
  - Challenge-response verified: +0.05
  =
Final trust score (capped at 0.95)
```

## Tasks

1. [ ] Design attestation data model
2. [ ] Implement threshold signing (multiple stewards required)
3. [ ] Build attestation claim flow
4. [ ] Create steward bulk vouch UI
5. [ ] Build in-person verification flow (steward confirms face-to-face)
6. [ ] Build challenge-response system (cohort-specific questions)
7. [ ] Build mesh vouch verification (existing cohort member vouches)
8. [ ] Implement attestation expiration
9. [ ] Build steward accountability tracking
10. [ ] Test all flows work fully offline (no internet at any step)
11. [ ] Ensure works on old phones (Android 8+, 2GB RAM)

## Dependencies

- Web of Trust (trust scoring)
- Local Cells (cell assignment)
- Identity system (key pairs)

## Security Considerations

- Attestations require threshold signatures (3 of 5 stewards) - no single point of compromise
- No email/phone - verification is in-person or via mesh challenge
- All verification works fully offline
- No external services at any step
- Steward accountability - bad vouches have consequences

## What We're NOT Doing

- ❌ OAuth to any platform
- ❌ API calls to external services
- ❌ Dependency on platform goodwill
- ❌ Data sharing with any corporation
- ❌ Trust that can be revoked by outsiders

## Success Criteria

- [ ] Steward can import known community without external services
- [ ] Cohort attestations work with threshold signatures (no single admin)
- [ ] All verification is in-person or mesh-based (no email/phone)
- [ ] All import methods work with no internet
- [ ] Works on old phones (Android 8+, 2GB RAM)
- [ ] Platform cutoff has zero impact on functionality
- [ ] No data leaves the mesh to any external service
