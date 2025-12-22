"""
GAP-64: Battery Warlord Detection (Bakunin Analytics Service)
Philosophical foundation: Mikhail Bakunin

"Where there is authority, there is no freedom."

This service detects emergent power structures and resource concentration that could
create de facto authority, even in a supposedly non-hierarchical gift economy.

Alerts the community to:
- Critical resource concentration (battery warlords)
- Skill gatekeepers (only person who can fix X)
- Coordination monopolies (one person coordinates everything)
"""

from typing import List, Dict, Optional, Tuple
import sqlite3
from datetime import datetime, timedelta, UTC


class PowerAlert:
    """Represents a detected power concentration that needs community attention"""

    def __init__(
        self,
        alert_type: str,  # 'resource_concentration', 'skill_gatekeeper', 'coordination_monopoly'
        agent_id: str,
        agent_name: str,
        resource_or_skill: str,
        concentration_percentage: float,
        dependency_count: int,
        risk_level: str,  # 'low', 'medium', 'high', 'critical'
        analysis: str,
        suggestions: List[str],
        criticality_category: Optional[str] = None
    ):
        self.alert_type = alert_type
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.resource_or_skill = resource_or_skill
        self.concentration_percentage = concentration_percentage
        self.dependency_count = dependency_count
        self.risk_level = risk_level
        self.analysis = analysis
        self.suggestions = suggestions
        self.criticality_category = criticality_category
        self.detected_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        return {
            "alert_type": self.alert_type,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "resource_or_skill": self.resource_or_skill,
            "concentration_percentage": round(self.concentration_percentage, 1),
            "dependency_count": self.dependency_count,
            "risk_level": self.risk_level,
            "analysis": self.analysis,
            "suggestions": self.suggestions,
            "criticality_category": self.criticality_category,
            "detected_at": self.detected_at,
        }


class BakuninAnalyticsService:
    """Detects and analyzes emergent power structures in the gift economy"""

    def __init__(self, db_path: str):
        self.db_path = db_path

        # Thresholds for alerts
        self.CRITICAL_RESOURCE_THRESHOLD = 50  # % - If one person provides >50% of critical resource
        self.GATEKEEPER_THRESHOLD = 80  # % - If one person provides >80% of a skill
        self.COORDINATION_THRESHOLD = 60  # % - If one person coordinates >60% of activities

        # Minimum sample size to avoid false positives
        self.MIN_OFFERS_FOR_ANALYSIS = 5
        self.MIN_EXCHANGES_FOR_ANALYSIS = 10

    def detect_battery_warlords(self, community_id: Optional[str] = None) -> List[PowerAlert]:
        """
        Detect critical resource concentration

        Returns alerts for agents who control a high percentage of critical resources
        like batteries, solar panels, water filters, medical supplies, etc.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        alerts = []

        try:
            # Find critical resources with their categories
            critical_resources_query = """
            SELECT id, name, criticality_reason, criticality_category
            FROM resource_specs
            WHERE critical = 1
            """

            critical_resources = cursor.execute(critical_resources_query).fetchall()

            for resource in critical_resources:
                # Count total active offers for this critical resource
                total_offers_query = """
                SELECT COUNT(*) as total
                FROM listings
                WHERE resource_spec_id = ?
                AND listing_type = 'offer'
                AND status = 'active'
                AND anonymous = 0
                """ + (" AND community_id = ?" if community_id else "")

                params = [resource['id']]
                if community_id:
                    params.append(community_id)

                total = cursor.execute(total_offers_query, params).fetchone()['total']

                if total < self.MIN_OFFERS_FOR_ANALYSIS:
                    continue  # Not enough data for meaningful analysis

                # Find agents with high concentration of this resource
                concentration_query = """
                SELECT
                    l.agent_id,
                    a.name as agent_name,
                    COUNT(*) as offer_count,
                    (COUNT(*) * 100.0 / ?) as percentage
                FROM listings l
                JOIN agents a ON l.agent_id = a.id
                WHERE l.resource_spec_id = ?
                AND l.listing_type = 'offer'
                AND l.status = 'active'
                AND l.anonymous = 0
                """ + (" AND l.community_id = ?" if community_id else "") + """
                GROUP BY l.agent_id
                HAVING percentage >= ?
                ORDER BY percentage DESC
                """

                params = [total, resource['id']]
                if community_id:
                    params.append(community_id)
                params.append(self.CRITICAL_RESOURCE_THRESHOLD)

                concentrations = cursor.execute(concentration_query, params).fetchall()

                for conc in concentrations:
                    # Count how many people depend on this
                    dependency_query = """
                    SELECT COUNT(DISTINCT receiver_id) as dep_count
                    FROM exchanges
                    WHERE provider_id = ?
                    AND resource_spec_id = ?
                    AND status IN ('completed', 'in_progress')
                    """

                    dep_count = cursor.execute(
                        dependency_query,
                        [conc['agent_id'], resource['id']]
                    ).fetchone()['dep_count']

                    # Determine risk level
                    if conc['percentage'] >= 90:
                        risk_level = 'critical'
                    elif conc['percentage'] >= 70:
                        risk_level = 'high'
                    elif conc['percentage'] >= 50:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'

                    # Generate analysis and suggestions
                    analysis = self._generate_warlord_analysis(
                        conc['agent_name'],
                        resource['name'],
                        conc['percentage'],
                        dep_count,
                        resource['criticality_reason']
                    )

                    suggestions = self._generate_decentralization_suggestions(
                        resource['name'],
                        resource['criticality_category']
                    )

                    alert = PowerAlert(
                        alert_type='resource_concentration',
                        agent_id=conc['agent_id'],
                        agent_name=conc['agent_name'],
                        resource_or_skill=resource['name'],
                        concentration_percentage=conc['percentage'],
                        dependency_count=dep_count,
                        risk_level=risk_level,
                        analysis=analysis,
                        suggestions=suggestions,
                        criticality_category=resource['criticality_category']
                    )

                    alerts.append(alert)

        finally:
            conn.close()

        return alerts

    def detect_skill_gatekeepers(self, community_id: Optional[str] = None) -> List[PowerAlert]:
        """
        Detect skill monopolies - when only one person can provide a critical skill

        Examples: Only one person who can repair bikes, only one medic, only one
        person who knows how to maintain the solar panels, etc.
        """
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        alerts = []

        try:
            # Find skill-based resources (category = 'skills' or 'labor')
            skill_resources_query = """
            SELECT DISTINCT rs.id, rs.name, rs.category, rs.critical, rs.criticality_category
            FROM resource_specs rs
            JOIN listings l ON rs.id = l.resource_spec_id
            WHERE rs.category IN ('skills', 'labor')
            AND l.listing_type = 'offer'
            AND l.status = 'active'
            """ + (" AND l.community_id = ?" if community_id else "")

            params = [community_id] if community_id else []
            skill_resources = cursor.execute(skill_resources_query, params).fetchall()

            for skill in skill_resources:
                # Count unique providers of this skill
                providers_query = """
                SELECT
                    agent_id,
                    COUNT(*) as offer_count
                FROM listings
                WHERE resource_spec_id = ?
                AND listing_type = 'offer'
                AND status = 'active'
                AND anonymous = 0
                """ + (" AND community_id = ?" if community_id else "") + """
                GROUP BY agent_id
                """

                params = [skill['id']]
                if community_id:
                    params.append(community_id)

                providers = cursor.execute(providers_query, params).fetchall()

                if len(providers) == 0:
                    continue

                total_providers = len(providers)

                # If only 1-2 people provide this skill, check if it's critical
                if total_providers <= 2:
                    for provider in providers:
                        percentage = (1 / total_providers) * 100

                        # Get provider name
                        agent_query = "SELECT name FROM agents WHERE id = ?"
                        agent_name = cursor.execute(agent_query, [provider['agent_id']]).fetchone()['name']

                        # Count dependencies
                        dep_query = """
                        SELECT COUNT(DISTINCT receiver_id) as dep_count
                        FROM exchanges
                        WHERE provider_id = ?
                        AND resource_spec_id = ?
                        AND status IN ('completed', 'in_progress')
                        """

                        dep_count = cursor.execute(
                            dep_query,
                            [provider['agent_id'], skill['id']]
                        ).fetchone()['dep_count']

                        # Determine risk level
                        if total_providers == 1 and (skill['critical'] or dep_count > 5):
                            risk_level = 'critical'
                        elif total_providers == 1:
                            risk_level = 'high'
                        elif total_providers == 2 and skill['critical']:
                            risk_level = 'medium'
                        else:
                            risk_level = 'low'

                        if risk_level in ['critical', 'high']:
                            analysis = self._generate_gatekeeper_analysis(
                                agent_name,
                                skill['name'],
                                total_providers,
                                dep_count
                            )

                            suggestions = self._generate_skill_sharing_suggestions(
                                skill['name'],
                                agent_name
                            )

                            alert = PowerAlert(
                                alert_type='skill_gatekeeper',
                                agent_id=provider['agent_id'],
                                agent_name=agent_name,
                                resource_or_skill=skill['name'],
                                concentration_percentage=percentage,
                                dependency_count=dep_count,
                                risk_level=risk_level,
                                analysis=analysis,
                                suggestions=suggestions,
                                criticality_category=skill['criticality_category'] if 'criticality_category' in skill.keys() else None
                            )

                            alerts.append(alert)

        finally:
            conn.close()

        return alerts

    def detect_coordination_monopolies(self, community_id: Optional[str] = None, days: int = 90) -> List[PowerAlert]:
        """
        Detect when one person coordinates too many activities

        Looks at processes, exchanges, and commitments to see if one person is
        becoming a bottleneck or de facto coordinator.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        alerts = []

        try:
            cutoff_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

            # Count exchanges coordinated (where someone is the provider in many exchanges)
            coordination_query = """
            SELECT
                provider_id as agent_id,
                COUNT(*) as coordination_count,
                COUNT(DISTINCT receiver_id) as unique_partners
            FROM exchanges
            WHERE created_at >= ?
            """ + (" AND community_id = ?" if community_id else "") + """
            GROUP BY provider_id
            HAVING coordination_count >= ?
            """

            params = [cutoff_date]
            if community_id:
                params.append(community_id)
            params.append(self.MIN_EXCHANGES_FOR_ANALYSIS)

            coordinators = cursor.execute(coordination_query, params).fetchall()

            # Get total exchanges in period for percentage calculation
            total_query = """
            SELECT COUNT(*) as total
            FROM exchanges
            WHERE created_at >= ?
            """ + (" AND community_id = ?" if community_id else "")

            params = [cutoff_date]
            if community_id:
                params.append(community_id)

            total_exchanges = cursor.execute(total_query, params).fetchone()['total']

            if total_exchanges < self.MIN_EXCHANGES_FOR_ANALYSIS:
                return alerts  # Not enough data

            for coord in coordinators:
                percentage = (coord['coordination_count'] / total_exchanges) * 100

                if percentage >= self.COORDINATION_THRESHOLD:
                    # Get agent name
                    agent_query = "SELECT name FROM agents WHERE id = ?"
                    agent_name = cursor.execute(agent_query, [coord['agent_id']]).fetchone()['name']

                    # Determine risk level
                    if percentage >= 80:
                        risk_level = 'critical'
                    elif percentage >= 70:
                        risk_level = 'high'
                    elif percentage >= 60:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'

                    analysis = self._generate_coordination_analysis(
                        agent_name,
                        coord['coordination_count'],
                        percentage,
                        coord['unique_partners'],
                        days
                    )

                    suggestions = self._generate_coordination_suggestions(agent_name)

                    alert = PowerAlert(
                        alert_type='coordination_monopoly',
                        agent_id=coord['agent_id'],
                        agent_name=agent_name,
                        resource_or_skill='Exchange Coordination',
                        concentration_percentage=percentage,
                        dependency_count=coord['unique_partners'],
                        risk_level=risk_level,
                        analysis=analysis,
                        suggestions=suggestions
                    )

                    alerts.append(alert)

        finally:
            conn.close()

        return alerts

    def get_all_power_alerts(self, community_id: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Get all types of power concentration alerts"""
        return {
            "resource_concentration": [a.to_dict() for a in self.detect_battery_warlords(community_id)],
            "skill_gatekeepers": [a.to_dict() for a in self.detect_skill_gatekeepers(community_id)],
            "coordination_monopolies": [a.to_dict() for a in self.detect_coordination_monopolies(community_id)],
        }

    # Analysis and suggestion generators

    def _generate_warlord_analysis(
        self,
        agent_name: str,
        resource_name: str,
        percentage: float,
        dep_count: int,
        reason: Optional[str]
    ) -> str:
        analysis = f"{agent_name} provides {percentage:.1f}% of {resource_name} in the community."

        if dep_count > 0:
            analysis += f" {dep_count} people depend on this resource."

        analysis += "\n\nWhy this matters:\n"
        analysis += "- Creates dependency on one person\n"
        analysis += f"- Gives {agent_name} unintentional power\n"
        analysis += "- Fragile if " + agent_name.split()[0] + " leaves or gets sick"

        if reason:
            analysis += f"\n- Critical because: {reason}"

        return analysis

    def _generate_decentralization_suggestions(
        self,
        resource_name: str,
        category: Optional[str]
    ) -> List[str]:
        suggestions = [
            f"Organize a workshop on {resource_name} maintenance/creation",
            f"Pool resources to acquire more {resource_name}",
            "Discuss as community: Is this concentration acceptable?",
        ]

        if category == 'power':
            suggestions.append("Consider distributed solar/battery system")
        elif category == 'skills':
            suggestions.append("Create mentorship/apprenticeship program")
        elif category == 'communication':
            suggestions.append("Document processes for others to learn")

        return suggestions

    def _generate_gatekeeper_analysis(
        self,
        agent_name: str,
        skill_name: str,
        total_providers: int,
        dep_count: int
    ) -> str:
        if total_providers == 1:
            analysis = f"Only {agent_name} can provide {skill_name}."
        else:
            analysis = f"Only {total_providers} people can provide {skill_name}, and {agent_name} is one of them."

        if dep_count > 0:
            analysis += f" {dep_count} people have relied on this skill."

        analysis += "\n\nObservations:\n"
        analysis += f"- {agent_name} is doing incredible work! ✓\n"
        analysis += "- BUT: Creates dependency on one person ⚠\n"
        analysis += f"- If {agent_name.split()[0]} is unavailable, this skill is lost\n"
        analysis += f"- {agent_name} may have de facto authority in this domain"

        return analysis

    def _generate_skill_sharing_suggestions(
        self,
        skill_name: str,
        agent_name: str
    ) -> List[str]:
        return [
            f"Ask {agent_name} to teach {skill_name} workshop",
            f"Document {agent_name}'s process step-by-step",
            f"Pool resources to send someone else for {skill_name} training",
            "Create apprenticeship/shadowing opportunity",
            "Celebrate mentorship and succession planning",
        ]

    def _generate_coordination_analysis(
        self,
        agent_name: str,
        count: int,
        percentage: float,
        partners: int,
        days: int
    ) -> str:
        analysis = f"{agent_name} has coordinated {count} exchanges over the last {days} days "
        analysis += f"({percentage:.1f}% of all community exchanges), "
        analysis += f"working with {partners} different people.\n\n"

        analysis += "Observations:\n"
        analysis += f"- {agent_name} is doing amazing coordination work! ✓\n"
        analysis += "- BUT: Creates dependency on one person ⚠\n"
        analysis += f"- If {agent_name.split()[0]} burns out, coordination stops\n"
        analysis += f"- {agent_name} has de facto authority over scheduling/priorities\n"
        analysis += "- Others may defer to " + agent_name.split()[0] + " instead of self-organizing"

        return analysis

    def _generate_coordination_suggestions(self, agent_name: str) -> List[str]:
        return [
            "Rotate coordination role among multiple people",
            f"Document {agent_name}'s coordination process",
            "Create coordination collective (3+ people)",
            "Discuss as community: Is this concentration healthy?",
            "Celebrate mentorship - teach others to coordinate",
        ]
