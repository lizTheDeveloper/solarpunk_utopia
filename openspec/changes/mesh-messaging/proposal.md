# Proposal: Mesh Messaging

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED - Full stack complete: backend API + frontend UI (E2E crypto uses placeholder, DTN integration pending)
**Complexity:** 3 systems
**Timeline:** WORKSHOP BLOCKER
**Implemented:** 2025-12-19

## Problem Statement

The platform handles offers, needs, and matching. But after a match, people need to TALK. "Where should we meet?" "Can you bring it by 5pm?" "I'm running late."

Currently there's no messaging. People would have to exchange phone numbers and use SMS (surveilled) or Signal (requires internet). We need mesh-native messaging that works without infrastructure.

## Proposed Solution

End-to-end encrypted messaging that routes over the DTN mesh.

### Architecture

```
Alice's Phone                              Bob's Phone
┌─────────────────┐                    ┌─────────────────┐
│ Compose Message │                    │ Receive Message │
│       ↓         │                    │       ↑         │
│ Encrypt w/      │                    │ Decrypt w/      │
│ Bob's Public Key│                    │ Bob's Private   │
│       ↓         │                    │       ↑         │
│ Create DTN      │    WiFi/BT Mesh    │ Receive DTN     │
│ Bundle          │ ──────────────────→│ Bundle          │
│       ↓         │    (Store & Fwd)   │       ↑         │
│ Queue for Send  │                    │ Inbox           │
└─────────────────┘                    └─────────────────┘
```

### Message Types

1. **Direct Message:** Alice → Bob (E2E encrypted)
2. **Exchange Thread:** Conversation attached to a specific exchange
3. **Cell Broadcast:** Message to all cell members
4. **Steward Alert:** Priority message from steward to cell

### Encryption

- Uses existing Ed25519 keys for identity
- Messages encrypted with recipient's public key
- Forward secrecy via ephemeral key exchange (like Signal's Double Ratchet)
- Metadata-minimal: only recipient key visible, not sender

## Requirements

### Requirement: End-to-End Encryption

The system SHALL encrypt all messages such that only the recipient can read them.

#### Scenario: Private Message
- GIVEN Alice wants to message Bob
- WHEN Alice composes and sends the message
- THEN the message is encrypted with Bob's public key
- AND stored as a DTN bundle
- AND only Bob's private key can decrypt it
- AND neither relay nodes nor servers can read the content

### Requirement: Mesh Delivery

The system SHALL deliver messages via DTN mesh.

#### Scenario: Offline Delivery
- GIVEN Alice sends a message to Bob
- AND Bob is currently offline
- WHEN the message bundle reaches other mesh nodes
- THEN it is stored and forwarded
- AND when Bob's phone comes in range of any node with the message
- THEN Bob receives the message

### Requirement: Exchange Threads

The system SHALL attach conversations to exchanges.

#### Scenario: Coordination
- GIVEN Alice and Bob matched for a tomato exchange
- WHEN Alice opens the exchange details
- THEN she sees a conversation thread for this exchange
- AND can send messages about logistics
- AND the thread is visible to both parties only

### Requirement: Cell Broadcast

The system SHALL allow messaging to entire cells.

#### Scenario: Community Announcement
- GIVEN Maria is a steward of Downtown Collective
- WHEN Maria sends a cell broadcast
- THEN all cell members receive the message
- AND it's marked as a broadcast (not direct)
- AND replies go to Maria only (not reply-all chaos)

### Requirement: Delivery Receipts

The system SHALL confirm message delivery.

#### Scenario: Confirmation
- GIVEN Alice sends a message to Bob
- WHEN Bob's phone receives and decrypts the message
- THEN a delivery receipt bundle is sent back
- AND Alice sees "Delivered" status
- AND optionally "Read" when Bob opens it

### Requirement: Message Expiration

The system SHALL support ephemeral messages.

#### Scenario: Burn After Reading
- GIVEN Alice sends a sensitive message with 1-hour expiry
- WHEN the message is delivered
- THEN it auto-deletes from Bob's device after 1 hour
- AND it cannot be recovered

## Data Model

```python
class Message:
    id: str
    sender_pubkey: str         # Encrypted sender identity
    recipient_pubkey: str      # Who can decrypt
    encrypted_content: bytes   # E2E encrypted
    timestamp: datetime
    expires_at: Optional[datetime]
    thread_id: Optional[str]   # Links to exchange or conversation
    message_type: str          # "direct", "exchange", "broadcast", "alert"

class MessageBundle(Bundle):
    # Extends DTN Bundle
    payload_type: "message/encrypted"
    audience: "direct"         # Single recipient
    priority: "normal" | "emergency"
```

## Tasks

1. [ ] Design E2E encryption protocol (adapt Signal's Double Ratchet)
2. [ ] Implement key exchange handshake
3. [ ] Create message bundle type in DTN system
4. [ ] Build message composition UI
5. [ ] Build inbox/conversation view
6. [ ] Implement delivery receipt bundles
7. [ ] Create exchange thread UI (attach to exchanges)
8. [ ] Build cell broadcast function
9. [ ] Implement message expiration (ephemeral)
10. [ ] Add steward alert priority messaging
11. [ ] Test mesh delivery under various network conditions

## Dependencies

- DTN Bundle System (already exists)
- Ed25519 keys (already exists)
- Web of Trust (for trust-gated messaging)

## Risks

- **Spam:** Bad actor floods with messages. Mitigation: Trust-gated (can only message people in your trust network), rate limiting.
- **Message bombs:** Large messages clog mesh. Mitigation: Message size limits, priority queuing.
- **Key compromise:** Lost private key means lost messages. Mitigation: Cannot help - that's the security model. Users must secure keys.

## Security Notes

- **No metadata logging:** Server (if any) cannot see who messages whom
- **Forward secrecy:** Compromising current keys doesn't reveal past messages
- **Plausible deniability:** Sender identity is encrypted; only recipient knows who sent

## Success Criteria

- [ ] Alice can message Bob with E2E encryption
- [ ] Messages deliver over mesh without internet
- [ ] Exchange threads work
- [ ] Cell broadcasts work
- [ ] Delivery receipts show status
- [ ] Ephemeral messages auto-delete
