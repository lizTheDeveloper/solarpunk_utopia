# GAP-04: Seed Demo Data

**Status**: Draft
**Priority**: P1 - Critical (Demo Blocker)
**Estimated Effort**: 3-4 hours
**Assigned**: Unclaimed

## Problem Statement

The system starts with an empty database. Workshop attendees see nothing but empty pages. No demo content, no example flows, no "living commune" to explore.

First impressions matter. An empty app looks broken, not promising.

## Current Reality

**Location**: No seed data script exists

Running the app fresh shows:
- Zero offers
- Zero needs
- Zero agents (people)
- Zero locations
- Zero pending proposals
- No way to demo the agent features

## Required Implementation

The system SHALL provide a seed data script that creates realistic demo content.

### MUST Requirements

1. The system MUST create a script `scripts/seed_demo_data.py`
2. The script MUST create 1 default community: "Sunrise Collective"
3. The script MUST create 10 demo agents (people) with realistic names
4. The script MUST create 5 locations within the commune
5. The script MUST create 15 resource specifications
6. The script MUST create 20 offers (mix of food, tools, skills, space)
7. The script MUST create 10 needs (realistic requests)
8. The script MUST create 3 pending agent proposals ready for approval
9. The script MUST be idempotent (safe to run multiple times)
10. The script MUST clear existing demo data before creating new

### SHOULD Requirements

1. The script SHOULD create 2 upcoming exchanges (to show the flow)
2. The script SHOULD include diverse resource types
3. The script SHOULD use realistic quantities and TTLs
4. The script SHOULD create proposals from different agent types

## Scenarios

### WHEN running seed script on empty database

**GIVEN**: Fresh database with no data

**WHEN**: `python scripts/seed_demo_data.py` is run

**THEN**:
1. Console MUST show progress: "Creating community...", "Creating agents...", etc.
2. Script MUST complete without errors
3. Database MUST contain all specified entities
4. Frontend MUST show populated pages

### WHEN running seed script on existing data

**GIVEN**: Database already has seed data

**WHEN**: Script is run again

**THEN**:
1. Script MUST delete previous seed data
2. Script MUST create fresh seed data
3. No duplicate entries MUST exist
4. Non-seed data MUST be preserved

## Data to Create

### Community
- Name: "Sunrise Collective"
- Description: "A resilient gift economy community"

### Demo Agents (People)
1. Alice - experienced gardener
2. Bob - carpenter and builder
3. Carol - preserving and canning expert
4. Dave - permaculture designer
5. Eve - herbalist and healer
6. Frank - mechanic and tool repair
7. Grace - community organizer
8. Hank - forager and wildcrafting
9. Iris - textile arts and mending
10. Jack - renewable energy tech

### Locations
1. North Garden
2. South Garden
3. Tool Shed
4. Community Kitchen
5. Workshop

### Resource Specs (Sample)
- Tomatoes (kg)
- Eggs (dozen)
- Hand tools (various)
- Carpentry skills (hours)
- Preserve jars (units)
- Herbal remedies (units)
- Workshop space (hours)
- Bicycle repair (service)
- Sewing/mending (hours)
- Solar panel maintenance (service)

### Sample Offers
- Alice: 5kg tomatoes, expires 3 days, North Garden
- Bob: 4 hours carpentry, available next week
- Carol: 12 preserve jars, available now
- Dave: Permaculture consultation, 2 hours
- Eve: Chamomile tea (200g)
- Frank: Bicycle tune-up service
- Grace: Workshop space, 4 hours, Saturday
- Hank: Wild mushrooms (1kg), expires 2 days
- Iris: Clothing mending, 3 hours available
- Jack: Solar panel inspection

### Sample Needs
- Bob needs: Tomatoes for family dinner
- Alice needs: Carpentry help for raised bed
- Grace needs: Facilitation tools
- Hank needs: Bicycle repair
- Eve needs: Preserve jars for herbal tinctures

### Sample Proposals
1. Mutual aid match: Alice offers tomatoes → Bob needs tomatoes
2. Work party: Garden cleanup, 5 participants needed
3. Perishable alert: Hank's mushrooms expiring in 24h

## Files to Create

- `scripts/seed_demo_data.py`

## Files to Modify

None (self-contained script)

## Testing Requirements

1. Run on empty database - verify all entities created
2. Run twice - verify idempotency
3. Check frontend - verify data displays correctly
4. Verify agent proposals are actionable

## Success Criteria

- [ ] Script runs without errors
- [ ] All specified entities created
- [ ] Frontend shows populated pages
- [ ] Agents page shows 3 pending proposals
- [ ] Offers page shows 20 offers
- [ ] Needs page shows 10 needs
- [ ] Data is realistic and diverse

## Dependencies

- Database schema must be complete
- VF API endpoints must work
- Agent API endpoints must work

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-04`
