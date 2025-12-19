# Tasks: GAP-64 Battery Warlord Detection (Mikhail Bakunin)

## Overview

Detect and alert community to emergent power concentrations - resource monopolies, skill gatekeeping, and coordination bottlenecks that create invisible authority.

## Phase 1: Criticality Tagging (2-3 hours)

### Task 1.1: Add criticality fields to resource specs
**File**: Database migration
**Estimated**: 30 minutes

```sql
ALTER TABLE resource_specs ADD COLUMN critical BOOLEAN DEFAULT FALSE;
ALTER TABLE resource_specs ADD COLUMN criticality_reason TEXT;
ALTER TABLE resource_specs ADD COLUMN criticality_category TEXT;
-- Categories: 'power', 'water', 'medical', 'communication', 'food', 'shelter'

CREATE INDEX idx_resource_specs_critical ON resource_specs(critical) WHERE critical = TRUE;
```

**Acceptance criteria**:
- Criticality tracked per resource type
- Reason documented
- Queryable efficiently

### Task 1.2: Seed critical resources
**File**: Database seed script
**Estimated**: 1 hour

```sql
-- Power
UPDATE resource_specs SET
  critical = TRUE,
  criticality_reason = 'Only power source for phones/devices',
  criticality_category = 'power'
WHERE name IN ('Solar Battery Charging', 'Generator Access', 'Power Bank Lending');

-- Water
UPDATE resource_specs SET
  critical = TRUE,
  criticality_reason = 'Essential for survival',
  criticality_category = 'water'
WHERE name IN ('Water Filtration', 'Clean Water Access');

-- Medical
UPDATE resource_specs SET
  critical = TRUE,
  criticality_reason = 'Health and safety',
  criticality_category = 'medical'
WHERE name IN ('First Aid', 'Medicine', 'Medical Supplies');

-- Communication
UPDATE resource_specs SET
  critical = TRUE,
  criticality_reason = 'Information gatekeeping',
  criticality_category = 'communication'
WHERE name IN ('Internet Access', 'Communications Equipment', 'Radio');

-- Skills (critical knowledge)
UPDATE resource_specs SET
  critical = TRUE,
  criticality_reason = 'Essential maintenance skills',
  criticality_category = 'skills'
WHERE name IN ('Bicycle Repair', 'Phone Repair', 'Medical Care');
```

**Acceptance criteria**:
- 15-20 critical resources tagged
- Reasons documented
- Categories assigned

### Task 1.3: Admin UI for managing criticality
**File**: `frontend/src/pages/AdminResourcesPage.tsx`
**Estimated**: 1.5 hours

Allow admins to mark resources as critical and explain why.

**Acceptance criteria**:
- UI to toggle criticality
- Reason field
- Category selector

## Phase 2: Power Concentration Analytics (4-5 hours)

### Task 2.1: Create Bakunin analytics service
**File**: `app/services/bakunin_analytics.py` (new file)
**Estimated**: 3 hours

```python
from typing import List, Dict
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PowerAlert(BaseModel):
    alert_type: str  # 'resource_concentration', 'skill_gatekeeper', 'coordination_monopoly'
    agent_id: str
    agent_name: str
    resource: str
    percentage: float
    dependency_count: int
    risk_level: RiskLevel
    analysis: str
    suggestions: List[str]

class BakuninAnalytics:
    def __init__(self, db):
        self.db = db

    async def detect_battery_warlords(self, commune_id: str) -> List[PowerAlert]:
        """Detect critical resource concentration"""
        query = """
        WITH total_offers AS (
            SELECT resource_spec_id, COUNT(*) as total
            FROM listings
            WHERE commune_id = ? AND critical_resource = TRUE
            GROUP BY resource_spec_id
        )
        SELECT
            l.agent_id,
            l.resource_spec_id,
            rs.name,
            COUNT(*) as agent_offers,
            (COUNT(*) * 100.0 / t.total) as percentage
        FROM listings l
        JOIN resource_specs rs ON l.resource_spec_id = rs.id
        JOIN total_offers t ON l.resource_spec_id = t.resource_spec_id
        WHERE l.commune_id = ? AND rs.critical = TRUE
        GROUP BY l.agent_id, l.resource_spec_id
        HAVING percentage > 50
        ORDER BY percentage DESC
        """

        results = await self.db.execute(query, (commune_id, commune_id))
        alerts = []

        for row in results:
            alerts.append(PowerAlert(
                alert_type='resource_concentration',
                agent_id=row.agent_id,
                agent_name=await self.get_agent_name(row.agent_id),
                resource=row.name,
                percentage=row.percentage,
                dependency_count=await self.count_dependencies(row.agent_id, row.resource_spec_id),
                risk_level=self.assess_risk(row.percentage),
                analysis=self.generate_analysis(row),
                suggestions=self.generate_suggestions(row)
            ))

        return alerts

    async def detect_gatekeepers(self, commune_id: str) -> List[PowerAlert]:
        """Detect skill/service monopolies"""
        # Find resources where only one person offers
        query = """
        SELECT
            l.agent_id,
            l.resource_spec_id,
            rs.name,
            COUNT(DISTINCT l.agent_id) as provider_count
        FROM listings l
        JOIN resource_specs rs ON l.resource_spec_id = rs.id
        WHERE l.commune_id = ? AND rs.critical = TRUE
        GROUP BY l.resource_spec_id
        HAVING provider_count = 1
        """

        results = await self.db.execute(query, (commune_id,))
        alerts = []

        for row in results:
            dependency_count = await self.count_dependencies(row.agent_id, row.resource_spec_id)

            alerts.append(PowerAlert(
                alert_type='skill_gatekeeper',
                agent_id=row.agent_id,
                agent_name=await self.get_agent_name(row.agent_id),
                resource=row.name,
                percentage=100.0,  # Only provider
                dependency_count=dependency_count,
                risk_level=self.assess_gatekeeper_risk(dependency_count),
                analysis=f"Only {row.agent_name} can provide {row.name}. This creates dependency.",
                suggestions=[
                    f"Organize a {row.name} workshop",
                    f"Pool resources for training",
                    f"Document {row.agent_name}'s process"
                ]
            ))

        return alerts

    async def detect_coordination_monopolies(self, commune_id: str) -> List[PowerAlert]:
        """Detect people who coordinate too much"""
        # Count who creates/coordinates most proposals, work parties, etc.
        query = """
        SELECT
            coordinator_id,
            COUNT(*) as coordination_count,
            (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM work_parties WHERE commune_id = ?)) as percentage
        FROM work_parties
        WHERE commune_id = ?
        GROUP BY coordinator_id
        HAVING percentage > 60
        """

        results = await self.db.execute(query, (commune_id, commune_id))
        alerts = []

        for row in results:
            alerts.append(PowerAlert(
                alert_type='coordination_monopoly',
                agent_id=row.coordinator_id,
                agent_name=await self.get_agent_name(row.coordinator_id),
                resource='Coordination',
                percentage=row.percentage,
                dependency_count=row.coordination_count,
                risk_level=self.assess_risk(row.percentage),
                analysis=f"{row.agent_name} coordinates {row.percentage:.0f}% of activities",
                suggestions=[
                    "Rotate coordination role",
                    f"Document {row.agent_name}'s process",
                    "Create coordination collective (3+ people)",
                    "Discuss: Is this hierarchy OK with everyone?"
                ]
            ))

        return alerts

    def assess_risk(self, percentage: float) -> RiskLevel:
        if percentage >= 80:
            return RiskLevel.CRITICAL
        elif percentage >= 60:
            return RiskLevel.HIGH
        elif percentage >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def assess_gatekeeper_risk(self, dependency_count: int) -> RiskLevel:
        if dependency_count >= 20:
            return RiskLevel.CRITICAL
        elif dependency_count >= 10:
            return RiskLevel.HIGH
        elif dependency_count >= 5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
```

**Acceptance criteria**:
- Detects resource concentration
- Detects gatekeepers
- Detects coordination monopolies
- Risk assessment accurate
- Suggestions helpful

### Task 2.2: Create API endpoints
**File**: `app/api/power_dynamics.py` (new file)
**Estimated**: 1 hour

```python
@router.get("/power-dynamics/alerts")
async def get_power_alerts(commune_id: str):
    """Get all power concentration alerts for commune"""
    analytics = BakuninAnalytics(db)

    warlords = await analytics.detect_battery_warlords(commune_id)
    gatekeepers = await analytics.detect_gatekeepers(commune_id)
    coordinators = await analytics.detect_coordination_monopolies(commune_id)

    return {
        "resource_concentration": warlords,
        "skill_gatekeepers": gatekeepers,
        "coordination_monopolies": coordinators,
        "total_alerts": len(warlords) + len(gatekeepers) + len(coordinators)
    }
```

**Acceptance criteria**:
- Returns all alert types
- Filtered by commune
- Performant queries

### Task 2.3: Schedule periodic analysis
**File**: Background job
**Estimated**: 1 hour

```python
# Run daily
@scheduler.scheduled_job('cron', hour=2)  # 2 AM
async def daily_power_analysis():
    for commune in await get_all_communes():
        alerts = await get_power_alerts(commune.id)

        if alerts['total_alerts'] > 0:
            # Post to community channel
            await post_power_dynamics_report(commune.id, alerts)
```

**Acceptance criteria**:
- Runs daily
- Posts to community if alerts found
- Non-intrusive timing

## Phase 3: Power Dynamics Dashboard (4-5 hours)

### Task 3.1: Create PowerDynamicsPage
**File**: `frontend/src/pages/PowerDynamicsPage.tsx` (new file)
**Estimated**: 3 hours

```tsx
export function PowerDynamicsPage() {
  const { data: alerts } = useQuery(['power-dynamics'], () =>
    api.get('/power-dynamics/alerts')
  );

  return (
    <Page title="Power Dynamics (Bakunin Monitor)">
      <Alert severity="info">
        <Typography variant="h6">
          "Where there is authority, there is no freedom." - Mikhail Bakunin
        </Typography>
        <Typography variant="body2">
          This page helps us see invisible power structures before they solidify.
        </Typography>
      </Alert>

      {alerts?.total_alerts === 0 ? (
        <Card>
          <CardContent>
            <CheckCircle color="success" sx={{ fontSize: 60 }} />
            <Typography variant="h6">
              No significant power concentrations detected
            </Typography>
            <Typography color="text.secondary">
              Resources and coordination are distributed across the community.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          <Section title="Critical Resource Concentration">
            {alerts?.resource_concentration.map(alert => (
              <Alert
                key={alert.agent_id + alert.resource}
                severity={alert.risk_level}
              >
                <AlertTitle>
                  {alert.agent_name} provides {alert.percentage.toFixed(0)}% of {alert.resource}
                </AlertTitle>
                <Typography variant="body2">{alert.analysis}</Typography>

                <Typography variant="subtitle2" sx={{ mt: 2 }}>Suggestions:</Typography>
                <Stack spacing={1}>
                  {alert.suggestions.map(s => (
                    <Button key={s} variant="outlined" size="small">
                      {s}
                    </Button>
                  ))}
                </Stack>
              </Alert>
            ))}
          </Section>

          <Section title="Skill Gatekeepers">
            {alerts?.skill_gatekeepers.map(alert => (
              <Alert severity={alert.risk_level}>
                <AlertTitle>
                  Only {alert.agent_name} provides {alert.resource}
                </AlertTitle>
                <Typography>
                  {alert.dependency_count} people depend on this skill.
                </Typography>
                {/* ... suggestions ... */}
              </Alert>
            ))}
          </Section>

          <Section title="Coordination Concentration">
            {alerts?.coordination_monopolies.map(alert => (
              <Alert severity={alert.risk_level}>
                <AlertTitle>
                  {alert.agent_name} coordinates {alert.percentage.toFixed(0)}% of activities
                </AlertTitle>
                <Typography variant="body2">{alert.analysis}</Typography>
                {/* ... suggestions ... */}
              </Alert>
            ))}
          </Section>
        </>
      )}

      <Section title="Decentralization Progress">
        <DecentralizationChart />
      </Section>
    </Page>
  );
}
```

**Acceptance criteria**:
- Lists all alert types
- Severity colors correct
- Suggestions actionable
- Bakunin quote prominent
- Mobile-friendly

### Task 3.2: Create decentralization chart
**File**: Same as above
**Estimated**: 1.5 hours

```tsx
function DecentralizationChart() {
  const { data: history } = useQuery(['power-dynamics-history']);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6">Decentralization Over Time</Typography>
        <LineChart
          data={history}
          xAxis={{ dataKey: 'date' }}
          series={[
            { dataKey: 'critical_monopolies', label: 'Critical Monopolies' },
            { dataKey: 'high_risk_alerts', label: 'High Risk Alerts' },
          ]}
        />

        {history?.trend === 'improving' ? (
          <Alert severity="success">
            Trend: ✅ Decentralizing!
          </Alert>
        ) : (
          <Alert severity="warning">
            Trend: ⚠️ Concentration increasing
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
```

**Acceptance criteria**:
- Shows trend over time
- Visual feedback on progress
- Celebrates improvement

### Task 3.3: Add navigation link
**File**: Main navigation
**Estimated**: 30 minutes

Add link to Power Dynamics page in main nav or settings.

**Acceptance criteria**:
- Easily discoverable
- Icon appropriate

## Phase 4: Community Notifications (2 hours)

### Task 4.1: Create alert notification system
**File**: `app/services/power_dynamics_notifier.py` (new)
**Estimated**: 1.5 hours

```python
async def notify_community_of_alerts(commune_id: str, alerts: Dict):
    """Post power dynamics report to community"""
    if alerts['total_alerts'] == 0:
        return  # No alerts, no notification

    message = format_power_dynamics_report(alerts)

    # Post to community channel
    await post_to_community_channel(commune_id, message)

    # Optional: Email community stewards
    await email_stewards(commune_id, alerts)

def format_power_dynamics_report(alerts: Dict) -> str:
    """Format as friendly community message"""
    message = "**Power Dynamics Report**\n\n"
    message += '"Where there is authority, there is no freedom." - Bakunin\n\n'

    if alerts['resource_concentration']:
        message += "**Resource Concentration Detected:**\n"
        for alert in alerts['resource_concentration']:
            message += f"- {alert.agent_name} provides {alert.percentage:.0f}% of {alert.resource}\n"

    # ... other sections ...

    message += "\n**This is not about blame!** These patterns emerge naturally."
    message += " Let's discuss as a community how to decentralize."

    return message
```

**Acceptance criteria**:
- Non-accusatory tone
- Actionable suggestions
- Posted to appropriate channel

### Task 4.2: Add opt-in for notifications
**File**: Settings
**Estimated**: 30 minutes

Let users control power dynamics notifications.

**Acceptance criteria**:
- Optional notifications
- Clear explanations

## Phase 5: Testing (2-3 hours)

### Task 5.1: Unit tests
**Estimated**: 1.5 hours

```python
def test_detect_battery_warlord():
    # Create scenario: Dave offers 80% of battery charging
    alerts = await analytics.detect_battery_warlords(commune_id)

    assert len(alerts) == 1
    assert alerts[0].agent_name == "Dave"
    assert alerts[0].percentage >= 80
    assert alerts[0].risk_level == RiskLevel.CRITICAL

def test_detect_gatekeeper():
    # Only Alice offers bicycle repair
    alerts = await analytics.detect_gatekeepers(commune_id)

    assert any(a.resource == "Bicycle Repair" for a in alerts)

def test_no_false_positives_low_concentration():
    # Resources distributed evenly - no alerts
    alerts = await analytics.detect_battery_warlords(commune_id)
    assert len(alerts) == 0
```

**Acceptance criteria**:
- All detection logic tested
- No false positives
- Risk assessment accurate

### Task 5.2: E2E tests
**Estimated**: 1.5 hours

Test full flow:
1. Create resource concentration scenario
2. Run daily analysis
3. Verify alerts generated
4. Check dashboard displays correctly
5. Verify notifications sent

**Acceptance criteria**:
- End-to-end flow works
- UI displays correctly
- Notifications appropriate

## Verification Checklist

- [ ] Critical resources tagged
- [ ] Power concentration detected
- [ ] Skill gatekeeping detected
- [ ] Coordination monopolies detected
- [ ] Risk assessment accurate
- [ ] Dashboard displays alerts
- [ ] Suggestions actionable
- [ ] Tone non-accusatory
- [ ] Community notifications work
- [ ] Decentralization progress tracked
- [ ] Tests pass
- [ ] Documentation complete

## Estimated Total Time

- Phase 1: 3 hours (criticality tagging)
- Phase 2: 5 hours (analytics)
- Phase 3: 5 hours (dashboard)
- Phase 4: 2 hours (notifications)
- Phase 5: 3 hours (testing)

**Total: 4-6 days (18 hours)**

## Dependencies

- Database with listings, exchanges, work parties
- Community notification system
- Charting library
- Background job scheduler

## Philosophical Principles

- Authority often emerges from competence/generosity
- Visibility enables freedom
- Structure, not blame
- Decentralization is ongoing work
- Celebrate mentorship and succession

## Success Metrics

- Detects all monopolies above threshold
- Community discusses alerts constructively
- Decentralization improves over time
- No one feels attacked by alerts
- Skill-sharing increases
