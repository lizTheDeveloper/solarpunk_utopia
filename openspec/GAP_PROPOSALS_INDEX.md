# Gap Proposals Index

This document tracks all openspec change requests created from VISION_REALITY_DELTA.md gaps.

**Created**: December 18, 2025
**Source**: `VISION_REALITY_DELTA.md`

## Priority 1: Critical Path (Demo Blockers)

✅ **Completed**: 7 proposals created

| Gap ID | Title | Status | Location | Effort |
|--------|-------|--------|----------|--------|
| GAP-01 | Proposal Approval → VF Bridge | Draft | `openspec/changes/gap-01-proposal-approval-bridge/` | 2-3 hours |
| GAP-02 | User Identity System | Draft | `openspec/changes/gap-02-user-identity-system/` | 1-2 days |
| GAP-03 | Community/Commune Entity | Draft | `openspec/changes/gap-03-community-entity/` | 1 day |
| GAP-04 | Seed Demo Data | Draft | `openspec/changes/gap-04-seed-demo-data/` | 3-4 hours |
| GAP-05 | Proposal Persistence | ✅ COMPLETE | N/A - Already implemented | N/A |
| GAP-06 | Frontend/Backend API Routes | ✅ COMPLETE | `openspec/archive/2025-12-18/gap-06-api-route-fixes/` | 1.5 hours |
| GAP-06B | DELETE Endpoint for Listings | ✅ COMPLETE | `openspec/archive/2025-12-18/gap-06b-delete-endpoint/` | 30 min |
| GAP-07 | Approval Payload Format | ✅ COMPLETE | N/A - Already fixed | N/A |
| GAP-08 | VF Bundle Publisher | ✅ COMPLETE | `openspec/archive/2025-12-18/gap-08-vf-bundle-publisher/` | 1 hour |

**Total P1 Proposals**: 7 created (5 complete: 2 pre-existing + 3 newly implemented)

## Priority 2: Core Experience Gaps

✅ **Completed**: 4 proposals created

| Gap ID | Title | Status | Location | Effort |
|--------|-------|--------|----------|--------|
| GAP-09 | Notification/Awareness System | Draft | `openspec/changes/gap-09-notification-system/` | MVP: 2-3 hours, Full: 1-2 days |
| GAP-10 | Exchange Completion Flow | Draft | `openspec/changes/gap-10-exchange-completion/` | 3-4 hours |
| GAP-11 | Replace Remaining Agent Mock Data | Draft | `openspec/changes/gap-11-agent-mock-data/` | 4-6 hours |
| GAP-12 | Onboarding Flow | Draft | `openspec/changes/gap-12-onboarding-flow/` | 1-2 days |

## Priority 3: Polish & Depth

📝 **To be created**: 4 proposals

| Gap ID | Title | Effort |
|--------|-------|--------|
| GAP-13 | Urgency Indicators | 2-3 hours |
| GAP-14 | Calendar Integration | 2-3 hours |
| GAP-15 | Statistics/Impact Tracking | 4-6 hours |
| GAP-16 | DTN Sync Automation | Demo: 2-3 hours, Real: requires native |

## Priority 4: UX Polish Gaps

📝 **To be created**: 14 proposals

| Gap ID | Title | Effort |
|--------|-------|--------|
| GAP-17 | "My Stuff" View | 3-4 hours |
| GAP-18 | Edit/Delete for Offers & Needs | 2-3 hours |
| GAP-19 | Messaging Between Matched Parties | MVP: 1 hour, Full: 1-2 days |
| GAP-20 | Photos on Offers | 4-6 hours |
| GAP-21 | Filter/Sort on Offers & Needs | 3-4 hours |
| GAP-22 | Locations Configurable | 2-3 hours quick, 1 day proper |
| GAP-23 | Custom Items Beyond Predefined | 2-3 hours |
| GAP-24 | Recurring Offers | 4-6 hours |
| GAP-25 | "Accept Offer" Button Functionality | 3-4 hours |
| GAP-26 | Navigation Badge Display | 30 minutes |
| GAP-27 | Offline/Sync Status Indicator | 2-3 hours |
| GAP-28 | Success/Error Feedback (Toasts) | 2-3 hours |
| GAP-29 | Mobile Bottom Navigation | 2-3 hours |
| GAP-30 | Proximity/Distance Display | 4-6 hours |

## Priority 5: Agent & Backend Gaps

📝 **To be created**: 10 proposals

| Gap ID | Title | Effort |
|--------|-------|--------|
| GAP-31 | Agent Settings Persistence | 2-3 hours |
| GAP-32 | Agent Stats Real Data | 3-4 hours |
| GAP-33 | Commons Router Cache State | 2-3 hours |
| GAP-34 | Work Party Scheduler Availability | 3-4 hours |
| GAP-35 | Education Pathfinder Skills/Commitments | 4-6 hours |
| GAP-36 | Permaculture Planner LLM Integration | 4-6 hours |
| GAP-37 | Weather API Integration | 2-3 hours |
| GAP-38 | Proposal Executor Service Integration | 3-4 hours |
| GAP-39 | Files API Routing Verification | 1-2 hours |
| GAP-40 | LLM Backend Setup Documentation | Configuration only |

---

## Summary Statistics

| Priority | Total Gaps | Proposals Created | Already Complete | Remaining |
|----------|-----------|-------------------|------------------|-----------|
| P1 (Critical) | 8 | 7 | 2 | 0 |
| P2 (Core UX) | 4 | 4 | 0 | 0 |
| P3 (Polish) | 4 | 0 | 0 | 4 |
| P4 (UX) | 14 | 0 | 1 | 13 |
| P5 (Backend) | 10 | 0 | 0 | 10 |
| P6 (Production/Security) | 18 | 0 | 0 | 18 ⚠️ CRITICAL |
| P7 (Philosophical) | 11 | 0 | 0 | 11 |
| **Total** | **69** | **11** | **3** | **56** |

---

## Implementation Order (Recommended)

Based on VISION_REALITY_DELTA.md recommendations:

### Week 1: Make the Demo Work
1. ✅ GAP-05: Proposal persistence (DONE)
2. ✅ GAP-06: API route fixes (DONE - 2025-12-18)
3. ✅ GAP-06B: DELETE endpoint (DONE - 2025-12-18)
4. ✅ GAP-07: Approval payload (DONE)
5. 📋 GAP-04: Seed data
6. 📋 GAP-01: Proposal→VF bridge
7. 📋 GAP-09: Notification badges (MVP)
8. 📋 GAP-10: Exchange completion

### Week 2: Add Identity & Onboarding
8. 📋 GAP-02: User identity
9. 📋 GAP-03: Community entity
10. 📋 GAP-12: Onboarding flow

### Week 3: Polish & Depth
11. 📋 GAP-11: Replace mock data
12. 📋 GAP-13: Urgency indicators
13. 📋 GAP-14: Calendar integration
14. 📋 GAP-15: Statistics

### Quick Wins (Anytime)
- 📋 GAP-26: Nav badge display (30 min)
- 📋 GAP-28: Toast notifications (2-3 hours)
- 📋 GAP-18: Edit/delete buttons (2-3 hours)
- 📋 GAP-06B: DELETE endpoint (30 min)

---

## Next Steps

To complete the remaining gaps as openspec proposals:

```bash
# Create Priority 2 proposals
./scripts/create_gap_proposals.sh 09 10 11 12

# Create Priority 3 proposals
./scripts/create_gap_proposals.sh 13 14 15 16

# Create Priority 4 proposals (batch)
./scripts/create_gap_proposals.sh 17-30

# Create Priority 5 proposals (batch)
./scripts/create_gap_proposals.sh 31-40
```

Or create manually following the same structure as Priority 1 proposals:
1. Create directory: `openspec/changes/gap-{id}-{short-name}/`
2. Create `proposal.md` with SHALL/MUST requirements and scenarios
3. Create `tasks.md` with implementation breakdown

---

## Proposal Template Reference

See any Priority 1 proposal for template structure:
- **proposal.md**: Problem statement, requirements (MUST/SHOULD/MAY), scenarios (WHEN/THEN), files to modify
- **tasks.md**: Phased implementation with time estimates, verification checklists

---

**Document Status**: Living document, updated as proposals are created and implemented.
