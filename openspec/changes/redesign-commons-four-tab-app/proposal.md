# Redesign: Commons four-tab mobile app

**Status:** Draft
**Priority:** High
**Component:** Frontend (`frontend/src`)
**Date:** 2026-11-24
**Prototype:** `frontend/prototypes/commons-app.html` (earlier comparison: `frontend/prototypes/ui-directions.html`)
**Related:** lizTheDeveloper/solarpunk_utopia PR 5 (Living World, familiar runtime); supersedes `usability-mobile-navigation`

## Problem Statement

The current UI has 5 nav sections and 12 top-level destinations. On a phone the header holds three different "+" buttons and the tab row is cut off. The Offers screen opens with a 4-field filter form before any content. The app never tells people whether their post has left their phone, even though delivery runs over a delay-tolerant mesh. Agent proposals show Approve / Deny with no amount, recipients, expiry or undo.

## Proposed Change

Replace the top navigation with a bottom tab bar of four tabs and one Give / ask action:

| Tab | Purpose | Replaces |
|-----|---------|----------|
| Nearby | Shared queue of needs and gifts | Home, Offers, Needs, Search |
| Site | Illustrated map of the land with live readings and jobs per place | Community shelf (plus PR 5 Living World map) |
| Inbox | Decisions (familiar approvals), Replies, Messages | AI Helpers, proposal modal, notifications, Messages, Exchanges |
| You | Profile, activity, community tools, phone settings, safety | Groups, Communities, Knowledge, Network, Profile, Steward, Rapid response, Panic |

## Requirements

### Navigation (MUST)

1. WHEN the viewport is phone width THEN the app SHALL show a bottom tab bar with exactly Nearby, Site, Give / ask, Inbox, You.
2. The Inbox tab badge MUST equal open decisions the user may approve plus unread replies plus unread messages.
3. Every existing route SHALL remain reachable within two taps from a tab (see table above).
4. Existing deep links (`/offers`, `/needs`, `/messages/:id`, etc.) MUST keep working, redirecting into the new tab where the content now lives.

### Sync honesty (MUST)

5. Every tab header SHALL show a sync status pill with online/offline state, the last mesh contact, and the number of queued outbound items.
6. WHEN a user replies, posts or approves while offline THEN the confirmation MUST say the action is queued and will leave with the next phone in range. It MUST NOT say "sent".

### Nearby (MUST)

7. Needs and offers SHALL appear in one feed, filterable by chips (Everything / Needs / Gifts & loans) without a form.
8. Each card SHALL have a single primary action ("I can help", "I'd use this", "Borrow it") and show the poster's vouch count.
9. Familiar match suggestions MAY appear inline but SHALL only introduce people; any spending, outreach or physical action MUST go to Inbox → Decisions.

### Give / ask (MUST)

10. The composer SHALL open as a sheet from any tab with an I have / I need switch, one free-text field, optional category chips, and a visibility choice (this commune / trusted neighbours / whole mesh).

### Site (SHOULD, gated on sensor data)

11. The map SHALL render places from site configuration, not hard-coded art per site.
12. Every reading MUST show its age; readings older than the place's freshness threshold MUST be visibly flagged.
13. Jobs created from a Nearby post or awaiting a decision SHALL link to that post or decision.

### Inbox → Decisions (MUST)

14. Each decision SHALL show type (spending, outreach, physical action), the exact payload, expiry, reversibility, and which role may approve.
15. WHEN the user edits a payload THEN the original approval MUST be invalidated and a new request created (matches `familiar_runtime.py` behaviour in PR 5).
16. WHEN the user lacks the approving role THEN the card MUST name who can approve instead of showing a disabled button.
17. Approved and declined decisions SHALL offer Undo while the action's cancellation window is open.

### Accessibility (MUST)

18. Body text SHALL use a high-legibility face (Atkinson Hyperlegible) at ≥15px; touch targets ≥44px; all state conveyed by text as well as colour; light and dark themes.

## Scenarios

- WHEN I am offline and tap "I can help" on Amara's ride request THEN the card says Amara will see it when our phones next meet AND the sync pill's queued count goes up by one.
- WHEN I change the seed order amount from $38.50 to $45 THEN the card states that it needs a fresh approval from another steward AND the Approve button is gone.
- WHEN I open Site and tap the compost heap whose core reading is 2 h old THEN the reading is flagged as stale.
- WHEN I open `/agents` from an old bookmark THEN I land on Inbox → Decisions.

## Out of Scope

- Backend sensor ingestion for Site (depends on PR 5 follow-up work); Site ships behind a flag with sample data until then.
- Desktop/tablet layout beyond a centred phone column (follow-up proposal).

## Risks

- Moving Steward, Rapid response and Panic under You makes them one tap deeper. Mitigation: Rapid response also gets a long-press on the You tab.
- Existing Playwright E2E tests target the old nav and will need updating.
