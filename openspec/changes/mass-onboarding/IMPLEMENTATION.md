# Mass Onboarding Implementation

**Status:** Implemented
**Date:** 2025-12-19

## What Was Implemented

### ✅ Event Onboarding System (Completed)

**Backend API:**
- `POST /onboarding/event/create` - Stewards create event invites
- `GET /onboarding/event/{event_id}` - Get event details
- `GET /onboarding/event/code/{invite_code}` - Get event by code (for QR scanning)
- `POST /onboarding/event/join` - Join via event invite code
- `GET /onboarding/event/my` - Get your created events

**Database:**
- `event_invites` table - Stores event metadata and invite codes
- `event_attendees` table - Tracks who joined via which event
- Auto-generated unique invite codes for QR generation

**Features:**
- Stewards (trust >= 0.9) can create event invites
- Each event gets unique invite code for QR generation
- Configurable max attendees and temporary trust level
- Event-scoped trust grants (default 0.3)
- Automatic vouch creation from event creator
- Expiration handling (expires 1 day after event ends)

### ✅ Batch Invite System (Completed)

**Backend API:**
- `POST /onboarding/batch/create` - Create batch invite links
- `POST /onboarding/batch/join` - Join via batch invite

**Database:**
- `batch_invites` table - Stores batch invite metadata
- `batch_invite_uses` table - Tracks usage per invite

**Features:**
- Established members (trust >= 0.7) can create batch invites
- Configurable max uses (1-100)
- Configurable validity period (1-30 days)
- Unique invite links/codes
- Automatic vouch from creator when used
- Usage tracking and limits

### ✅ Trust Ladder & Analytics (Completed)

**Backend API:**
- `GET /onboarding/analytics` - Onboarding statistics (stewards only)

**Features:**
- Track total event/batch invites created
- Track total attendees/members onboarded
- Calculate upgrade rates (event → full member)
- Count active events
- Track recent joins (24h)
- Trust level distribution (placeholder for future)

**Trust Levels Defined:**
- `EVENT` (0.3) - Can participate in event only
- `MEMBER` (0.5) - Cell access, can post offers/needs
- `ESTABLISHED` (0.7) - Can vouch others, batch invites
- `STEWARD` (0.9) - Create event invites, analytics
- `GENESIS` (1.0) - Genesis node

## Files Created

### Models
- `app/models/event_onboarding.py` - All onboarding data models
  - `EventInvite` - Event invite details
  - `BatchInvite` - Batch invite details
  - `EventAttendee` - Attendee records
  - `OnboardingAnalytics` - Statistics
  - `TrustLevel` enum
  - Request/response models

### Repository
- `app/database/event_onboarding_repository.py` - Database operations
  - SQLite schema creation
  - CRUD operations for events and batch invites
  - Invite code generation
  - Usage tracking
  - Analytics computation

### API
- `app/api/event_onboarding.py` - FastAPI endpoints
  - Event creation and joining
  - Batch invite creation and joining
  - Analytics endpoint
  - Permission checks (trust level validation)

### Integration
- `app/main.py` - Registered onboarding router

## API Examples

### Create Event Invite (Steward)

```bash
POST /onboarding/event/create
Authorization: Bearer <token>

{
  "event_name": "Portland Solarpunk Workshop",
  "event_type": "workshop",
  "event_start": "2025-12-20T10:00:00Z",
  "event_end": "2025-12-20T18:00:00Z",
  "event_location": "Portland Community Center",
  "max_attendees": 200,
  "temporary_trust_level": 0.3
}

Response:
{
  "id": "event-abc123",
  "invite_code": "WS2025ABC",  # Use for QR generation
  "event_name": "Portland Solarpunk Workshop",
  ...
}
```

### Join Event (Attendee)

```bash
POST /onboarding/event/join
Authorization: Bearer <token>

{
  "invite_code": "WS2025ABC",
  "user_name": "Maria",
  "location": "Portland, OR"
}

Response:
{
  "success": true,
  "event_name": "Portland Solarpunk Workshop",
  "temporary_trust_level": 0.3,
  "your_trust_score": 0.64,
  "message": "Welcome to Portland Solarpunk Workshop! You have temporary access during the event."
}
```

### Create Batch Invite (Established Member)

```bash
POST /onboarding/batch/create
Authorization: Bearer <token>

{
  "max_uses": 20,
  "days_valid": 7,
  "context": "Bringing my community organizing group"
}

Response:
{
  "id": "batch-xyz789",
  "invite_link": "BATCH-XYZ789ABC",
  "max_uses": 20,
  "used_count": 0,
  "expires_at": "2025-12-26T00:00:00Z",
  ...
}
```

### Get Analytics (Steward)

```bash
GET /onboarding/analytics
Authorization: Bearer <token>

Response:
{
  "total_event_invites": 5,
  "total_batch_invites": 12,
  "total_event_attendees": 250,
  "total_batch_members": 80,
  "upgrade_rate": 0.72,
  "active_events": 3,
  "recent_joins_24h": 45,
  "trust_level_distribution": {}
}
```

## Frontend Integration Needed

The backend is complete. Frontend needs to implement:

### For Stewards
1. **Event Creation Form**
   - Input: Event name, type, dates, location, max attendees
   - Output: Display QR code from invite_code
   - Generate QR using library like `qrcode.react` or `react-qr-code`

2. **Event Management Dashboard**
   - List created events
   - Show attendee count vs max
   - Display event status (active/expired)
   - Option to deactivate event early

3. **Analytics Dashboard**
   - Display onboarding metrics
   - Charts for growth over time
   - Upgrade funnel visualization

### For Members
4. **Event Join Flow**
   - QR scanner (use phone camera)
   - Extract invite code from QR
   - POST to /onboarding/event/join
   - Show welcome message and trust level

5. **Batch Invite Creation**
   - Simple form for established members
   - Generate shareable link/QR
   - Show usage stats

## QR Code Generation

**Server-side (optional):**
```python
import qrcode
import io

def generate_event_qr(invite_code: str) -> bytes:
    """Generate QR code image for event invite"""
    # Create QR code with event join URL
    qr_data = f"https://solarpunk.app/join/event/{invite_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
```

**Client-side (React):**
```tsx
import QRCode from 'react-qr-code';

function EventInviteDisplay({ inviteCode }) {
  const joinUrl = `https://solarpunk.app/join/event/${inviteCode}`;

  return (
    <div>
      <h2>Event QR Code</h2>
      <QRCode value={joinUrl} size={256} />
      <p>Invite Code: {inviteCode}</p>
      <p>Share this QR code with attendees!</p>
    </div>
  );
}
```

## What Remains

### Priority 1 (Before Workshop)
- [ ] Frontend QR code generation and display
- [ ] Frontend QR scanner for joining
- [ ] Event management UI for stewards
- [ ] Post-event upgrade prompt workflow

### Priority 2 (Post-Workshop)
- [ ] OAuth integration for network import (Hipcamp, GitHub, etc.)
- [ ] Open application review flow for stewards
- [ ] Automated expiration of event trust after event ends
- [ ] Email/SMS notifications for event attendees

### Priority 3 (Future)
- [ ] Invite capacity limits per steward (rate limiting)
- [ ] Abuse detection (too many invites, suspicious patterns)
- [ ] Batch invite analytics (conversion rates per creator)
- [ ] Trust ladder progression automation

## Success Criteria

- [x] Backend API for event invites ✅
- [x] Backend API for batch invites ✅
- [x] Trust-based permission checks ✅
- [x] Automatic vouch creation ✅
- [x] Analytics endpoint ✅
- [ ] Frontend QR generation (PENDING)
- [ ] Frontend QR scanning (PENDING)
- [ ] Event management UI (PENDING)
- [ ] 200 people can onboard in 15 minutes (NEEDS TESTING)

## Testing

To test the implementation:

1. **Create a steward user:**
   ```bash
   # Add genesis node
   POST /vouch/genesis/add/steward-alice
   ```

2. **Create an event:**
   ```bash
   POST /onboarding/event/create
   # Returns invite_code
   ```

3. **Join as attendee:**
   ```bash
   POST /onboarding/event/join
   {
     "invite_code": "...",
     "user_name": "Bob"
   }
   ```

4. **Check analytics:**
   ```bash
   GET /onboarding/analytics
   ```

## Architecture Notes

### Database Schema

**event_invites:**
- Stores event metadata
- Auto-generates unique invite codes
- Tracks attendee count
- Enforces max attendees
- Handles expiration

**batch_invites:**
- Stores batch invite metadata
- Tracks usage count vs max uses
- Enforces expiration
- Records context (why created)

**Integration with Web of Trust:**
- Event join creates automatic vouch from event creator
- Batch join creates automatic vouch from batch creator
- Trust scores recomputed after vouching
- Permissions enforced via trust thresholds

## Known Limitations

1. **No geographic constraints:** Events don't enforce location-based access
2. **No event capacity overflow handling:** Need queue system for >max_attendees
3. **No vouch expiration:** Event vouches don't auto-expire (manual revocation only)
4. **No OAuth yet:** Network import not implemented
5. **Frontend not implemented:** Backend complete, UI needed

## Next Steps

1. Implement frontend QR generation
2. Test at small event (20-50 people)
3. Optimize for workshop (200+ people)
4. Add event capacity queue system
5. Implement OAuth for network import
