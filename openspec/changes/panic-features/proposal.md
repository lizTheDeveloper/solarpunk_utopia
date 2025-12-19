# Proposal: Panic Features - Duress & Safety Protocols

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** ✅ IMPLEMENTED
**Complexity:** 2 systems
**Timeline:** WORKSHOP BLOCKER
**Implemented:** 2025-12-19

## Problem Statement

Activists get detained. Phones get seized. People get coerced into unlocking devices. In an environment of state violence and bounty hunters, the app must protect users even under duress.

This is not paranoia. This is operational security for a resistance network.

## Proposed Solution

A suite of panic features that protect the user and the network when things go wrong.

### Feature Set

1. **Duress PIN:** Alternate PIN that opens a decoy interface
2. **Quick Wipe:** Panic gesture that destroys sensitive data
3. **Dead Man's Switch:** Auto-wipe if app not opened for N days
4. **Decoy Mode:** Fake "normal" app content for inspection
5. **Burn Notice:** Signal to network that you're compromised
6. **Steganography Mode:** Hide app as calculator/notes app

## Requirements

### Requirement: Duress PIN

The system SHALL provide an alternate unlock that shows a decoy interface.

#### Scenario: Border Crossing
- GIVEN Maria has set up a duress PIN (1234) and real PIN (5678)
- WHEN an ICE agent forces Maria to unlock her phone
- AND Maria enters the duress PIN (1234)
- THEN the app opens showing only public, innocuous content
- AND the real data is not accessible
- AND no indication is given that duress mode is active
- AND a silent "burn notice" is queued to the network

### Requirement: Quick Wipe

The system SHALL allow instant destruction of sensitive data.

#### Scenario: Panic Gesture
- GIVEN the user has enabled panic gesture (5 taps on logo)
- WHEN the user performs the panic gesture
- THEN all private keys are destroyed
- AND all local messages are destroyed
- AND all vouch data is destroyed
- AND the app resets to "fresh install" state
- AND this happens in under 3 seconds

### Requirement: Dead Man's Switch

The system SHALL auto-protect if user goes dark.

#### Scenario: Detention
- GIVEN Alice has set a 72-hour dead man's switch
- WHEN Alice doesn't open the app for 72 hours
- THEN local sensitive data is automatically wiped
- AND a "gone dark" notice is sent to her vouch chain
- AND her ability to vouch is suspended until she checks in

### Requirement: Decoy Mode

The system SHALL provide plausible deniability.

#### Scenario: Phone Inspection
- GIVEN the phone is inspected by authorities
- WHEN the app is opened (without duress or with decoy active)
- THEN it appears to be a simple notes app or calculator
- AND there is no visible indication of mesh/resistance functionality
- AND the icon and name are innocuous ("Notes" or "Calculator Plus")

### Requirement: Burn Notice

The system SHALL allow signaling compromise to the network.

#### Scenario: Compromised Member
- GIVEN Alice's phone was seized
- WHEN Alice (or the duress system) sends a burn notice
- THEN Alice's trust score is immediately suspended
- AND all pending messages to Alice are held
- AND her recent vouches are flagged for review
- AND her vouch chain is notified: "Alice may be compromised"

### Requirement: Steganography Mode

The system SHALL hide its true nature.

#### Scenario: Hidden Installation
- GIVEN user wants maximum deniability
- WHEN they enable steganography mode
- THEN app icon becomes "Calculator" or "Notes"
- AND app name in settings shows generic name
- AND opening the app shows a functional calculator/notepad
- AND secret gesture (e.g., type "31337=" in calculator) reveals real app

## Security Considerations

### Data That Gets Wiped
- Private keys (Ed25519)
- Message history
- Vouch chains
- Local trust data
- Offer/need history
- Exchange records

### Data That Survives (On Network)
- Public key (identity can be recovered with seed phrase)
- Published offers (already on mesh)
- Completed exchanges (already propagated)

### Recovery Path
1. User escapes/is released
2. Uses seed phrase to regenerate keys
3. Re-authenticates with trusted contact
4. Trust chain is restored from network
5. Resumes participation

## Tasks

1. [ ] Implement dual-PIN system with decoy data store
2. [ ] Build quick-wipe with secure deletion (overwrite, not just delete)
3. [ ] Create dead man's switch background service
4. [ ] Develop decoy UI (calculator or notes that actually works)
5. [ ] Implement burn notice protocol over DTN
6. [ ] Create steganography mode with hidden gesture
7. [ ] Build recovery flow from seed phrase
8. [ ] Add "I'm back" re-authentication flow
9. [ ] Test all features under stress (can you wipe in 3 seconds while shaking?)
10. [ ] Document OPSEC best practices for users

## Dependencies

- Identity system (Ed25519 keys)
- Web of Trust (for burn notice propagation)
- DTN messaging (for network notifications)

## Risks

- **Accidental wipe:** User panics unnecessarily. Mitigation: Confirmation gesture, recovery from seed phrase.
- **Duress detection:** Sophisticated adversary notices duress mode. Mitigation: Decoy must be completely convincing.
- **False burn notice:** Attacker triggers burn notice to disrupt network. Mitigation: Burn notice suspends but doesn't permanently revoke; requires confirmation.

## Success Criteria

- [ ] Duress PIN opens convincing decoy
- [ ] Quick wipe destroys all sensitive data in <3 seconds
- [ ] Dead man's switch triggers correctly
- [ ] Decoy mode is indistinguishable from normal app
- [ ] Burn notice propagates to vouch chain
- [ ] User can recover from seed phrase after wipe
