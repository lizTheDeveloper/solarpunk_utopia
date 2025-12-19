# GAP-09: Notification/Awareness System

**Status**: Draft
**Priority**: P2 - Core Experience
**Estimated Effort**: MVP 2-3 hours, Full 1-2 days
**Assigned**: Unclaimed

## Problem Statement

Alice has no way to know when proposals need her approval. She must manually navigate to /agents page and hope something's there. No notifications, no awareness, no badges.

## Current Reality

No notification system exists. Users miss important proposals.

## Required Implementation

### MVP: Polling-based Awareness (2-3 hours)

1. Backend MUST provide `/agents/proposals/pending-count` endpoint
2. Frontend MUST poll endpoint every 30 seconds
3. Frontend MUST display badge on navigation: "Agents (3)"
4. Frontend MUST show card on homepage: "3 proposals need your review"

### Full: Real-time System (1-2 days)

1. Backend MUST publish proposal events to NATS
2. Backend MUST expose WebSocket for real-time updates
3. Frontend MUST subscribe to WebSocket
4. Frontend MUST update UI immediately on new proposals

## Files to Modify

MVP:
- `app/api/agents.py` - Add pending count endpoint
- `frontend/src/components/Navigation.tsx` - Display badge
- `frontend/src/pages/HomePage.tsx` - Add proposal count card

Full:
- `app/events/proposal_publisher.py` - NATS integration
- `frontend/src/hooks/useWebSocket.ts` - WebSocket client

## Success Criteria

- [ ] Users see pending proposal count
- [ ] Badge updates when proposals arrive
- [ ] No need to manually check agents page

**Reference**: `VISION_REALITY_DELTA.md:GAP-09`
