"""
GAP-64: Battery Warlord Detection API
Bakunin Analytics Endpoints

Provides visibility into emergent power structures and resource concentration.

"Where there is authority, there is no freedom." - Mikhail Bakunin

GET /vf/power-dynamics - Get all power concentration alerts
GET /vf/power-dynamics/resource-concentration - Get battery warlord alerts
GET /vf/power-dynamics/skill-gatekeepers - Get skill monopoly alerts
GET /vf/power-dynamics/coordination-monopolies - Get coordination bottleneck alerts
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, List

from ...database import get_database
from ...services.bakunin_analytics_service import BakuninAnalyticsService

router = APIRouter(prefix="/vf/power-dynamics", tags=["power-dynamics", "bakunin"])


@router.get("", response_model=Dict)
async def get_all_power_dynamics(
    community_id: Optional[str] = Query(None, description="Filter by community ID")
):
    """
    Get comprehensive power dynamics analysis for the community.

    Returns all three types of alerts:
    - Resource concentration (battery warlords)
    - Skill gatekeepers (monopolies on critical skills)
    - Coordination monopolies (bottleneck coordinators)

    This helps communities see invisible power structures before they solidify.

    **Philosophical Foundation**: Mikhail Bakunin's warning that authority often
    emerges not from malice but from competence, generosity, and resource control.
    """
    db_path = await get_database()
    service = BakuninAnalyticsService(db_path)

    result = service.get_all_power_alerts(community_id)

    # Add metadata
    result["summary"] = {
        "total_alerts": sum(len(alerts) for alerts in result.values()),
        "critical_alerts": sum(
            1 for category in result.values()
            for alert in category
            if alert.get("risk_level") == "critical"
        ),
        "high_alerts": sum(
            1 for category in result.values()
            for alert in category
            if alert.get("risk_level") == "high"
        ),
        "philosophy": "Where there is authority, there is no freedom. - Mikhail Bakunin"
    }

    return result


@router.get("/resource-concentration", response_model=List[Dict])
async def get_resource_concentration(
    community_id: Optional[str] = Query(None, description="Filter by community ID")
):
    """
    Detect critical resource concentration ("battery warlords").

    Identifies when one person controls a high percentage of critical resources
    like batteries, solar panels, water filters, medical supplies, etc.

    **Why This Matters**:
    - Creates dependency on one person
    - Gives unintentional power to resource holder
    - Fragile if that person leaves or becomes unavailable
    - Can become de facto authority

    **Example Alert**: "Dave provides 80% of battery charging. This creates
    dependency. Suggestions: Teach battery maintenance, pool resources for
    more chargers, discuss as community."
    """
    db_path = await get_database()
    service = BakuninAnalyticsService(db_path)

    alerts = service.detect_battery_warlords(community_id)

    return [alert.to_dict() for alert in alerts]


@router.get("/skill-gatekeepers", response_model=List[Dict])
async def get_skill_gatekeepers(
    community_id: Optional[str] = Query(None, description="Filter by community ID")
):
    """
    Detect skill monopolies (gatekeeping).

    Identifies when only one (or very few) people can provide a critical skill:
    - Only one person who can repair bikes
    - Only one medic
    - Only one person who knows solar panel maintenance
    - Only one person fluent in sign language

    **Why This Matters**:
    - Creates dependency bottleneck
    - Knowledge not shared = fragile system
    - Person becomes de facto authority in that domain
    - If they're unavailable, the skill is lost

    **Bakunin's Insight**: Authority often emerges from competence. The person
    who's "really good at X" becomes the gatekeeper, even without intending to.

    **Example Alert**: "Only Alice can repair bikes. 15 people depend on this.
    Suggestions: Alice teaches workshop, document her process, send someone
    else to training."
    """
    db_path = await get_database()
    service = BakuninAnalyticsService(db_path)

    alerts = service.detect_skill_gatekeepers(community_id)

    return [alert.to_dict() for alert in alerts]


@router.get("/coordination-monopolies", response_model=List[Dict])
async def get_coordination_monopolies(
    community_id: Optional[str] = Query(None, description="Filter by community ID"),
    days: int = Query(90, ge=7, le=365, description="Analysis period in days")
):
    """
    Detect coordination monopolies (one person coordinates everything).

    Identifies when one person becomes a bottleneck coordinator:
    - Coordinates most work parties
    - Matches most offers/needs
    - Schedules most activities
    - Becomes "the" go-to person

    **Why This Matters**:
    - If they burn out, coordination stops
    - Others may defer instead of self-organizing
    - Creates de facto authority over priorities/scheduling
    - Prevents distributed decision-making

    **Example Alert**: "Carol has coordinated 85% of work parties this quarter.
    Carol is doing amazing work! BUT: Creates dependency. Suggestions: Rotate
    coordination, document Carol's process, create coordination collective."

    **Note**: This alert celebrates the person's contribution while addressing
    the structural issue. We're not blaming people - we're making power visible
    so the community can decide if it's acceptable.
    """
    db_path = await get_database()
    service = BakuninAnalyticsService(db_path)

    alerts = service.detect_coordination_monopolies(community_id, days)

    return [alert.to_dict() for alert in alerts]
