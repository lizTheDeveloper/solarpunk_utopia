# Proposal: Accessible Security (Anti Crypto-Priesthood)

**Submitted By:** Philosopher Council (Bakunin)
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-20
**Gap Addressed:** GAP-66
**Priority:** P3 - Philosophical (Post-Workshop)

## Problem Statement

**Bakunin:** "I bow before the authority of specialists... but I allow no one to impose it upon me."

Security and encryption are presented as impenetrable jargon. Users must "trust the crypto-priests" (developers).

Current security docs:
```
"DTN uses BP7 with HMAC-SHA256 bundle authentication
and AES-256-GCM encryption for payload confidentiality..."
```

Translation for users: "Magic! Just trust us!"

This creates a **crypto-priesthood** - a class of experts who must be trusted because their knowledge is inaccessible. That's authority, not freedom.

## Proposed Solution

### Demystify Everything

Security explanations that a 15-year-old can understand:

### What We Protect (Plain English)

```markdown
# Security Explained (No Jargon)

## What We're Protecting

- **Your identity**: So only you can post as you
- **Your messages**: So only the recipient can read them
- **Your location**: So stalkers can't find you
- **Your relationships**: Who you exchange with

## How It Works

### 1. Encryption = Locked Boxes
When you send a message, it goes in a locked box.
Only the recipient has the key.
Even we can't read it.

Technical name: X25519 + XSalsa20-Poly1305
But all you need to know: It's the same encryption used by Signal.

### 2. Signatures = Wax Seals
When you post an offer, it has your digital signature.
No one can fake it. No one can change it.
If someone tries to edit your offer, the seal breaks.

Technical name: Ed25519
But all you need to know: Mathematicians have proven it can't be faked.

### 3. Mesh Sync = Passing Notes
Messages hop phone-to-phone until they reach you.
Like kids passing notes in class.
Works even when internet is down.

Technical name: DTN (Delay Tolerant Networking)
But all you need to know: Your message will get there, eventually.

## What This DOESN'T Protect

Be honest about limitations:

- If someone steals your unlocked phone → they have your keys
- If you share your password → anyone can impersonate you
- Metadata (who talks to who, when) → visible to phone carriers
- If you screenshot and share → that's on you

## Trust But Verify

- Code is open source: [github link]
- Security reviewed by: [list auditors]
- If you know cryptography, check our work: [link to specs]
- Found a bug? [responsible disclosure link]
```

### Accessibility Test

Before publishing any security docs, ask:
1. Can a 15-year-old understand this?
2. Does it avoid techno-mysticism?
3. Does it empower or intimidate?
4. Does it admit limitations honestly?

## Requirements

### Requirement: Jargon-Free Security Docs

The system SHALL explain security in plain language.

#### Scenario: New User Onboarding
- GIVEN a new user is onboarding
- WHEN they ask "Is this secure?"
- THEN they see plain-English explanations
- AND technical jargon is hidden behind "want the details?" toggles
- AND metaphors (locked boxes, wax seals) make concepts accessible

### Requirement: Security Status Visibility

The system SHALL show current security status simply.

#### Scenario: Check My Security
- GIVEN a user opens Security Settings
- WHEN they view their status
- THEN they see:
  - ✅ Messages: Encrypted (only recipients can read)
  - ✅ Identity: Verified (signed with your key)
  - ⚠️ Backup: Not backed up (if you lose your phone, you lose access)
- AND each item has a "Learn more" with plain explanation

### Requirement: Honest Limitations

The system SHALL be honest about what isn't protected.

#### Scenario: Metadata Warning
- GIVEN user is sending a message
- WHEN they view security info
- THEN they see: "Message content is encrypted, but your phone carrier can see you're using this app and when."
- AND guidance on protecting metadata if needed (VPN, etc.)

### Requirement: No Trust Required

The system SHALL enable verification, not just trust.

#### Scenario: Verify the Code
- GIVEN a technical user wants to verify
- WHEN they click "Verify Yourself"
- THEN they get:
  - Link to open source code
  - How to audit the crypto
  - Third-party security audits
  - Reproducible build instructions

## Implementation

### Phase 1: Plain English Docs
- Rewrite all security docs
- Test with non-technical users
- Add metaphors and analogies

### Phase 2: In-App Explanations
- Security status screen
- Contextual help ("What does this lock icon mean?")
- Honest limitations disclosure

### Phase 3: Verification Tools
- Links to source code
- Audit reports
- Reproducible builds

### Phase 4: Security Onboarding
- Interactive tutorial: "Here's how your messages are protected"
- Quiz: "Test your understanding"
- Resources: "Want to learn more?"

## Example Explanations

### "What is end-to-end encryption?"

❌ **Crypto-priesthood version:**
"Messages are encrypted using X25519 key exchange with XSalsa20-Poly1305 AEAD, providing IND-CCA2 security..."

✅ **Accessible version:**
"When you send a message, it goes in a locked box. You and the recipient have the only keys. Even the people who built this app can't open it. The message travels locked, and only unlocks when your friend opens it."

### "What is a digital signature?"

❌ **Crypto-priesthood version:**
"Ed25519 signatures provide existential unforgeability under chosen message attack..."

✅ **Accessible version:**
"It's like a wax seal on a letter. If anyone opens the letter, the seal breaks. Your digital signature proves YOU wrote this, and proves no one changed it. Mathematicians have proven: no one can fake your seal."

### "What is mesh networking?"

❌ **Crypto-priesthood version:**
"DTN implements store-and-forward bundle protocol with BP7 compliance..."

✅ **Accessible version:**
"Like kids passing notes in class. Your message hops from phone to phone until it reaches your friend. Works even when the internet is down, as long as phones are nearby."

## Philosophical Foundation

**Bakunin on expertise:**
"Does it follow that I reject all authority? Far from me such a thought. In the matter of boots, I refer to the authority of the bootmaker... But I allow neither the bootmaker nor the architect to impose their authority upon me."

We're not saying "don't trust experts." We're saying:
1. Explain it so people CAN understand
2. Let people verify if they want
3. Don't require blind trust

**Anti-priesthood:** A priest mediates between you and the divine because you can't access it directly. A crypto-priest mediates between you and security because you can't understand it. We reject both. Security should be understandable.

## Success Criteria

- [ ] 15-year-old test: Can a teenager understand security docs?
- [ ] No unexplained jargon in user-facing text
- [ ] Security status visible in simple terms
- [ ] Limitations honestly disclosed
- [ ] Verification possible for those who want it
- [ ] Non-technical users feel empowered, not intimidated

## Dependencies

- Existing security documentation
- In-app help system
- Open source repository

## Notes

This isn't about dumbing down security. It's about respecting users enough to explain what we're doing. The math is real. The protection is real. But so is the user's right to understand it.

Bakunin: Bow to expertise when you choose to. Never when it's imposed.
