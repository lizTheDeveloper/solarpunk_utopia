# Proposal: Web of Trust Identity System

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** ✅ IMPLEMENTED
**Complexity:** 2 systems
**Timeline:** WORKSHOP BLOCKER
**Implemented:** 2025-12-19

## Problem Statement

Open networks get infiltrated. Period. With 500k+ people and active adversaries (state actors, bounty hunters, bad faith actors), we cannot allow anonymous joins. But we also cannot have a central authority deciding who's in.

We need a **web of trust**: you get in because someone already trusted vouches for you.

## Proposed Solution

A decentralized vouching system where:
1. Founding members are "genesis nodes" (trust seeds)
2. Each trusted member can vouch for new members
3. Trust is transitive but attenuates with distance
4. Compromised nodes can be revoked, cascading to their vouches

### Trust Model

```
Genesis (Liz, core team)
    └── Vouches for Alice (trust: 1.0)
            └── Vouches for Bob (trust: 0.8)
                    └── Vouches for Carol (trust: 0.64)
                            └── Vouches for Dave (trust: 0.51)
```

**Trust attenuation:** Each hop reduces trust by 20% (configurable per community).

**Trust threshold:** Actions require minimum trust level:
- View public offers: 0.3
- Post offers/needs: 0.5
- Send direct messages: 0.6
- Vouch for others: 0.7
- Steward/admin actions: 0.9

### Revocation

If Alice is compromised:
1. Her vouchers can revoke her
2. All her vouches become suspect (trust drops 50%)
3. Those she vouched can seek re-vouching from others
4. Cascade is limited to prevent weaponized revocation

## Requirements

### Requirement: No Central Authority

The system SHALL NOT have a single point of trust authority.

#### Scenario: Genesis Distribution
- GIVEN the network launch
- WHEN initial trusted members are established
- THEN trust originates from 5+ independent genesis nodes
- AND no single genesis node can unilaterally exclude someone vouched by others

### Requirement: Vouch Chain

The system SHALL track vouching chains.

#### Scenario: New Member Onboarding
- GIVEN Alice is a trusted member (trust > 0.7)
- WHEN Alice vouches for Bob
- THEN Bob receives trust = Alice's trust × 0.8
- AND Bob's profile shows "Vouched by Alice"
- AND Bob can now access features matching their trust level

### Requirement: Revocation Cascade

The system SHALL handle compromised nodes gracefully.

#### Scenario: Burned Node
- GIVEN Alice vouched for Bob, Bob vouched for Carol
- WHEN Alice is marked as compromised by 2+ of her vouchers
- THEN Alice loses all trust
- AND Bob's trust drops 50%
- AND Carol's trust drops 25%
- AND Bob and Carol are notified to seek additional vouches

### Requirement: Trust Recovery

The system SHALL allow recovery from revocation cascade.

#### Scenario: Re-vouching
- GIVEN Bob's trust dropped due to Alice's revocation
- WHEN Dave (unconnected to Alice) vouches for Bob
- THEN Bob's trust is recalculated from remaining vouch chains
- AND Bob can rebuild trust through the new chain

### Requirement: Import Existing Trust

The system SHALL bootstrap from existing trusted networks.

#### Scenario: Hipcamp Import
- GIVEN a user has a verified Hipcamp account since 2019
- WHEN they join the network
- THEN they receive a trust bonus based on account age/reputation
- AND this counts as a "genesis-adjacent" vouch

## Data Model

```python
class Vouch:
    voucher_id: str          # Public key of person giving vouch
    vouchee_id: str          # Public key of person receiving vouch
    created_at: datetime
    context: str             # "Met in person", "Worked together", etc.
    revoked: bool
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]

class TrustScore:
    user_id: str
    computed_trust: float    # 0.0 - 1.0
    vouch_chains: List[List[str]]  # All paths to genesis nodes
    last_computed: datetime
```

## Tasks

1. [ ] Design trust computation algorithm
2. [ ] Implement Vouch model and storage
3. [ ] Create vouch API endpoints
4. [ ] Build trust score computation service
5. [ ] Implement revocation cascade logic
6. [ ] Create trust threshold middleware for API routes
7. [ ] Build "Vouch for someone" UI flow
8. [ ] Build "My trust status" UI
9. [ ] Implement genesis node bootstrap
10. [ ] Build import from external identity (Hipcamp, etc.)
11. [ ] Create "I've been revoked, help" recovery flow

## Dependencies

- Identity/auth system (GAP-02)
- Ed25519 key pairs (already in codebase)

## Risks

- **Sybil attacks:** Someone creates many fake vouches. Mitigation: Trust attenuation + genesis distance limits.
- **Social engineering:** Attacker befriends way in. Mitigation: Context requirements ("how do you know them?"), community vigilance.
- **Weaponized revocation:** Bad actor revokes legitimate members. Mitigation: Require 2+ vouchers to revoke, rate limiting.

## Success Criteria

- [ ] New user cannot access network without vouch
- [ ] Trust scores compute correctly across chains
- [ ] Revocation cascades appropriately
- [ ] Recovery via re-vouching works
- [ ] Import from external identity works
