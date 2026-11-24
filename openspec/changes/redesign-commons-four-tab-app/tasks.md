# Tasks: Commons four-tab mobile app

## Phase 1: Shell and design tokens
- [ ] Add design tokens (colours, fonts, light/dark) to `tailwind.config.js` and `index.css`, ported from the prototype `:root`
- [ ] Load Bricolage Grotesque, Atkinson Hyperlegible, JetBrains Mono with system fallbacks
- [ ] Build `BottomTabBar` (Nearby, Site, Give / ask, Inbox, You) and replace `Navigation` on mobile
- [ ] Build `SyncPill` from `MeshSyncStatus` data (last contact, queued count, expandable explanation)
- [ ] Add route redirects for old paths into the new tabs

## Phase 2: Nearby and Give / ask
- [ ] `NearbyPage`: merged feed from `useOffers` + `useNeeds`, chip filters, search
- [ ] `PostCard` with single primary action, vouch count, queued/sent confirmation and undo
- [ ] Inline familiar match card using `useMatches` / `useAcceptMatch`
- [ ] `GiveAskSheet` composer using `useCreateOffer` / `useCreateNeed` and `VisibilitySelector`

## Phase 3: Inbox
- [ ] `InboxPage` with Decisions / Replies / Messages segments and combined badge count
- [ ] `DecisionCard` from `useProposals('pending')`: type, payload, expiry, reversibility, approver role
- [ ] Edit-invalidates-approval flow and role-gated "who can approve" state
- [ ] Undo within cancellation window via `useReviewProposal`
- [ ] Plan timeline component (familiar plan steps)

## Phase 4: You
- [ ] `YouPage` with grouped links to existing pages (activity, community, phone, safety)

## Phase 5: Site (behind flag)
- [ ] Site config schema (places, shapes, sensor bindings, freshness thresholds)
- [ ] `SiteMap` SVG renderer + `PlacePanel` with readings, people, jobs
- [ ] Sample site data until sensor ingestion lands

## Phase 6: Validation
- [ ] Update Playwright E2E tests for new navigation
- [ ] Screenshot review at 390px and 1280px, light and dark
- [ ] Accessibility pass: focus order, 44px targets, screen-reader labels
- [ ] PM validation against scenarios in `proposal.md`
