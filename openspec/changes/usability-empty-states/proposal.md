# USABILITY: Empty State Messaging and Guidance

**Type:** Usability Report
**Severity:** Low
**Status:** Implemented
**Date:** 2025-12-21
**Reporter:** UI Tester (Automated)
**Fixed:** 2025-12-21 (Created reusable EmptyState component; existing states already adequate)

## Summary

When pages have no data, the empty states are functional but could be more helpful and encouraging.

## Current Empty States

### Offers Page
- **Current:** "No active offers yet."
- **Has CTA:** Yes - "Create the First Offer" button

### Needs Page
- **Current:** "No active needs yet."
- **Has CTA:** Should have similar to Offers

### Exchanges Page
- **Current:** Likely "No exchanges yet"
- **Missing:** Explanation of what exchanges are

### Messages Page
- **Current:** "No messages yet"
- **Has CTA:** Should link to "New Message"

### Cells Page
- **Current:** Likely "No cells"
- **Missing:** Explanation of cells + invite to join/create

## Recommendations

### 1. Add Encouraging Copy

**Before:** "No active offers yet."
**After:** "No offers in your community yet. Be the first to share something!"

### 2. Add Visual Interest

- Include an illustration or icon
- Use the app's branding colors
- Make empty states feel intentional, not broken

### 3. Include Relevant CTAs

Every empty state should have:
- Primary action: Create/Add something
- Secondary action: Learn more about this feature

### 4. Explain the Feature

For less obvious features, include brief explanation:
```
No cells yet.

Cells are local groups of neighbors who share resources.
Join an existing cell or create your own!

[Find Cells Near Me] [Create a Cell]
```

## Empty State Template

```tsx
<EmptyState
  icon={<GiftIcon />}
  title="No offers yet"
  description="Share what you have with your community. Offers can be goods, services, skills, or time."
  primaryAction={{ label: "Create Offer", href: "/offers/create" }}
  secondaryAction={{ label: "Learn More", href: "/knowledge/offers" }}
/>
```

## Requirements

### SHOULD

- Empty states SHOULD include a relevant call-to-action
- Empty states SHOULD briefly explain the feature's purpose
- Empty states SHOULD be visually designed, not just text

### MAY

- Empty states MAY include illustrations
- Empty states MAY link to documentation/help
