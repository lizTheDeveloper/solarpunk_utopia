# GAP-12: Onboarding Flow

**Status**: Draft
**Priority**: P2 - Core Experience
**Estimated Effort**: 1-2 days
**Assigned**: Unclaimed

## Problem Statement

App opens to empty homepage with no guidance. New users don't know what to do. No welcome, no tutorial, no first-run experience.

## Current Reality

Blank slate. Users are lost.

## Required Implementation

1. System MUST detect first-run (localStorage flag or user.first_login)
2. System MUST show welcome sequence (5-7 screens)
3. System MUST guide through:
   - What is this app?
   - How does gift economy work?
   - Create your first offer
   - Browse community offers
   - How agents help you
4. System MUST mark onboarding complete after flow

## Scenarios

### WHEN new user opens app for first time

**THEN**:
1. Show welcome screen
2. Guide through key features
3. Prompt to create first offer
4. Celebration on completion
5. Never show again

### WHEN returning user opens app

**THEN**: Skip directly to homepage

## Files to Create

- `frontend/src/pages/OnboardingPage.tsx`
- `frontend/src/components/onboarding/WelcomeStep.tsx`
- `frontend/src/components/onboarding/CreateOfferStep.tsx`

## Files to Modify

- `frontend/src/App.tsx` - Route to onboarding if first run

## Success Criteria

- [ ] First-run users see onboarding
- [ ] Onboarding explains key concepts
- [ ] Users create first offer during flow
- [ ] Flow completes and doesn't repeat

**Reference**: `VISION_REALITY_DELTA.md:GAP-12`, `ONBOARDING_EXPERIENCE.md`
