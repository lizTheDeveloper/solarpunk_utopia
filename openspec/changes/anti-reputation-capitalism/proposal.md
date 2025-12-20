# Proposal: Anti-Reputation Capitalism

**Submitted By:** Philosopher Council
**Date:** 2025-12-20
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-20
**Priority:** P1 - Philosophical Core

## Problem Statement

We're building a gift economy but importing capitalist metrics:

- **Dollar values on gifts**: "That meal was worth $15"
- **Personal contribution tracking**: "You've kept $340 in community"
- **Achievement gamification**: "Carol hit 10 exchanges this month!"
- **Value leaderboards** (even implicit): Who gave most?

This creates **reputation capitalism** - you give to build status, not from generosity. The gift becomes a transaction with social ROI.

**The exchange IS the value.** Carol doesn't need to be celebrated for sharing - she already got the joy of sharing. Adding metrics on top corrupts the gift.

## What We're Removing

### 1. Dollar Values on Exchanges

**Before:**
```python
class ExchangeValue:
    exchange_id: str
    estimated_value: float  # $50 for drill share
```

**After:**
```python
class Exchange:
    # No value field. It happened. That's enough.
```

### 2. Personal Contribution Tracking

**Before:**
```
┌─────────────────────────────┐
│ Your Impact This Month      │
│ $340 kept in community      │
│ 12 exchanges completed      │
└─────────────────────────────┘
```

**After:**
Nothing. You know what you did. You were there.

### 3. Individual Celebration

**Before:**
```
🎉 Carol hit 10 exchanges this month!
```

**After:**
Nothing. Carol got the value from the exchanges themselves.

### 4. Steward Dashboard Value Tracking

**Before:**
```
│ $2,340  │
│ Kept    │
│ Local   │
```

**After:**
```
│ 47      │
│ Exchanges│
│ This Week│
```

(If even that - do stewards need to count?)

## What We Keep (Optional, Buried)

### Stats for Nerds

For people who genuinely want numbers, an opt-in buried setting:

```
Settings > Advanced > Stats for Nerds

☐ Show me network statistics
  (Aggregate counts, no individual tracking)

If enabled:
- "~2,400 exchanges network-wide this month"
- "Estimated value equivalent: ~$X" (rough multiplier, not per-exchange tracking)
```

This is:
- Opt-in (off by default)
- Aggregate only (no individual data)
- Rough estimates (category × count, not tracked per exchange)
- Buried (not on home screen)

### Community Aliveness

Stewards might want to know "is the network alive?" without dollar values:

```
Cell Health (not value):
- Exchanges happening: Yes (12 this week)
- Active members: 34 of 47
- Needs being met: Most
- Vibe: Good
```

No dollars. No individual attribution. Just "is this working?"

## Philosophical Foundation

### Gift vs. Transaction

**Transaction:** I give you X, I get Y (money, status, reputation points)
**Gift:** I give you X because I want to. Full stop.

The moment we track "value given," we convert gifts to transactions. The recipient becomes a means to my reputation. The gift economy becomes reputation capitalism with extra steps.

### Goldman on Recognition

Emma Goldman didn't want medals for her activism. The work was the point. Recognition corrupts motivation.

Same principle: Carol doesn't need "10 exchanges!" celebration. The exchanges were the point.

### Loafer's Rights (GAP-62)

If we track contribution, we create pressure to contribute. Those who receive more than they give become visible as "takers." This contradicts loafer's rights - the right to exist without justifying your existence through productivity.

### Anonymous Gifts (GAP-61)

If we track value, anonymous gifts become second-class. They can't be "counted" toward your contribution. This creates incentive against anonymity.

## Implementation

### Phase 1: Remove Value Tracking

1. Remove `ExchangeValue` model
2. Remove value estimation service
3. Remove personal impact dashboard
4. Remove "Carol hit X exchanges" celebrations
5. Remove dollar amounts from steward dashboard

### Phase 2: Simplify to Counts (If Needed)

1. Steward sees "exchanges happened: 47" not "$12,000 circulated"
2. Network health is "alive/quiet" not "value metrics"
3. No individual attribution

### Phase 3: Stats for Nerds (Optional)

1. Buried opt-in setting
2. Aggregate only
3. Rough estimates at display time
4. Never stored per-exchange

## Files to Modify

### Remove:
- `valueflows_node/app/models/leakage_metrics.py`
- `valueflows_node/app/services/value_estimation_service.py`
- `valueflows_node/app/services/metrics_aggregation_service.py`
- `frontend/src/components/PersonalImpactWidget.tsx`
- Remove value tracking from exchange completion flow

### Modify:
- `openspec/changes/leakage-metrics/proposal.md` - Mark as superseded
- `openspec/changes/steward-dashboard/proposal.md` - Remove $ amounts
- `frontend/src/components/CommunityImpactWidget.tsx` - Remove $ amounts

### Keep (Simplified):
- Network "aliveness" indicator
- Exchange counts (if stewards want them)
- Stats for nerds (opt-in, buried)

## Privacy Guarantees

**What we track:**
- That exchanges happened (the exchange record itself)
- Aggregate counts (for network health)

**What we DON'T track:**
- Dollar value of exchanges
- Individual contribution amounts
- "Impact" metrics per person
- Achievement milestones

## Success Criteria

- [ ] No dollar values attached to exchanges
- [ ] No personal contribution dashboards
- [ ] No individual achievement celebrations
- [ ] Steward dashboard shows counts, not dollars
- [ ] Stats for nerds is opt-in and buried
- [ ] GAP-62 (loafer's rights) is not undermined
- [ ] GAP-61 (anonymous gifts) is not disadvantaged

## What This Means for "Economic Warfare" Narrative

The original leakage-metrics proposal said we need to prove "$X diverted from Amazon."

Counter-argument:
- Do we need to prove it with dashboards? Or is the lived experience enough?
- If we need aggregate numbers for fundraising/press, compute rough estimates at display time (category × count) without storing per-exchange values
- The proof is in the community, not the metrics

## Notes

This is about keeping the gift economy a gift economy.

The exchange is the celebration.
The gift is the point.
Carol already got her reward - she was there.

We don't need to count.
