"""
E2E Test: Bakunin Analytics - Power Concentration Detection

"The only good authority is a dead one." - Mikhail Bakunin

Tests the detection of emergent power structures that can undermine
distributed gift economy:
- Resource concentration (battery warlords)
- Skill gatekeepers (single point of failure)
- Power detection → Steward alerts → Mitigation suggestions
"""

import pytest
import unittest
import tempfile
import os
from datetime import datetime, UTC

from valueflows_node.app.services.bakunin_analytics_service import (
    BakuninAnalyticsService,
    PowerAlert
)


class TestBakuninAnalyticsE2E(unittest.TestCase):
    """E2E tests for Bakunin Analytics power concentration detection"""

    def setUp(self):
        """Create temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Initialize service
        self.service = BakuninAnalyticsService(self.db_path)

        # Create schema
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            agent_type TEXT NOT NULL DEFAULT 'person',
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE resource_specs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            critical BOOLEAN DEFAULT FALSE,
            criticality_reason TEXT,
            criticality_category TEXT,
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE listings (
            id TEXT PRIMARY KEY,
            listing_type TEXT NOT NULL,
            resource_spec_id TEXT NOT NULL,
            agent_id TEXT,
            anonymous INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            community_id TEXT,
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE exchanges (
            id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            resource_spec_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            community_id TEXT,
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_detect_battery_warlord_high_concentration(self):
        """
        E2E Test 1: Detect critical resource concentration

        GIVEN Carol controls 85% of community batteries
        WHEN analytics runs
        THEN "Battery Warlord" alert generated (severity: high)
        AND suggestions include: pool resources, teach repair skills
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create agents
        carol_id = "agent:carol"
        alice_id = "agent:alice"
        bob_id = "agent:bob"

        now = datetime.now(datetime.UTC).isoformat()
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      (carol_id, "Carol", "person", "active", now))
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      (alice_id, "Alice", "person", "active", now))
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      (bob_id, "Bob", "person", "active", now))

        # Create critical resource (battery charging)
        battery_id = "resource:battery-charging"
        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (battery_id, "Battery Charging", "tools", True,
              "Only power source in community", "power", now))

        # Carol offers 17 battery charging sessions (85% of 20 total)
        for i in range(17):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:carol-battery-{i}", "offer", battery_id,
                  carol_id, 0, "active", None, now))

        # Alice offers 2
        for i in range(2):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:alice-battery-{i}", "offer", battery_id,
                  alice_id, 0, "active", None, now))

        # Bob offers 1
        cursor.execute("""
            INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("listing:bob-battery", "offer", battery_id,
              bob_id, 0, "active", None, now))

        # 8 people depend on Carol for power
        for i in range(8):
            cursor.execute("""
                INSERT INTO exchanges VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"exchange:carol-{i}", carol_id, f"agent:person-{i}",
                  battery_id, "completed", None, now))

        conn.commit()
        conn.close()

        # Action: Run analytics
        alerts = self.service.detect_battery_warlords()

        # Verify: Alert generated for Carol
        assert len(alerts) > 0
        carol_alert = next((a for a in alerts if a.agent_name == "Carol"), None)
        assert carol_alert is not None

        # Verify: Concentration percentage correct
        assert carol_alert.concentration_percentage == 85.0

        # Verify: Risk level appropriate
        assert carol_alert.risk_level in ['high', 'critical']

        # Verify: Resource identified
        assert "Battery Charging" in carol_alert.resource_or_skill

        # Verify: Dependency count tracked
        assert carol_alert.dependency_count == 8

        # Verify: Suggestions provided
        assert len(carol_alert.suggestions) > 0
        suggestions_text = ' '.join(carol_alert.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in
                  ['pool', 'workshop', 'teach', 'share', 'repair'])

    def test_detect_skill_gatekeeper_monopoly(self):
        """
        E2E Test 2: Detect skill monopoly

        GIVEN Dan is only person who can fix solar panels
        WHEN analytics runs
        THEN "Skill Gatekeeper" alert generated
        AND suggestions include: skill share, apprenticeship
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create Dan
        dan_id = "agent:dan"
        now = datetime.now(datetime.UTC).isoformat()
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      (dan_id, "Dan", "person", "active", now))

        # Create critical skill (solar panel repair)
        solar_repair_id = "resource:solar-panel-repair"
        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (solar_repair_id, "Solar Panel Repair", "skills", True,
              "Essential for community power", "skills", now))

        # Dan is the ONLY person offering solar panel repair
        cursor.execute("""
            INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("listing:dan-solar", "offer", solar_repair_id,
              dan_id, 0, "active", None, now))

        # 12 people have depended on Dan for solar repair
        for i in range(12):
            cursor.execute("""
                INSERT INTO exchanges VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"exchange:dan-solar-{i}", dan_id, f"agent:person-{i}",
                  solar_repair_id, "completed", None, now))

        conn.commit()
        conn.close()

        # Action: Run analytics
        alerts = self.service.detect_skill_gatekeepers()

        # Verify: Alert generated for Dan
        assert len(alerts) > 0
        dan_alert = alerts[0]
        assert dan_alert.agent_name == "Dan"

        # Verify: 100% monopoly detected
        assert dan_alert.concentration_percentage == 100.0

        # Verify: Critical risk level
        assert dan_alert.risk_level == 'critical'

        # Verify: Skill identified
        assert "Solar Panel Repair" in dan_alert.resource_or_skill

        # Verify: Dependency count
        assert dan_alert.dependency_count == 12

        # Verify: Mitigation suggestions
        assert len(dan_alert.suggestions) > 0
        suggestions_text = ' '.join(dan_alert.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in
                  ['skill', 'teach', 'workshop', 'apprentice', 'share'])

    def test_no_alert_when_resources_distributed(self):
        """
        E2E Test 3: No alert when resources well-distributed

        GIVEN battery charging evenly distributed (30%, 35%, 35%)
        WHEN analytics runs
        THEN no alerts generated
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create 3 agents
        now = datetime.now(datetime.UTC).isoformat()
        for person in ['alice', 'bob', 'carol']:
            cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                          (f"agent:{person}", person.title(), "person", "active", now))

        # Create resource
        battery_id = "resource:battery"
        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (battery_id, "Battery Charging", "tools", True,
              "Power source", "power", now))

        # Distribute offers evenly: 3, 4, 3 (30%, 40%, 30%)
        for i in range(3):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:alice-{i}", "offer", battery_id,
                  "agent:alice", 0, "active", None, now))

        for i in range(4):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:bob-{i}", "offer", battery_id,
                  "agent:bob", 0, "active", None, now))

        for i in range(3):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:carol-{i}", "offer", battery_id,
                  "agent:carol", 0, "active", None, now))

        conn.commit()
        conn.close()

        # Action: Run analytics
        alerts = self.service.detect_battery_warlords()

        # Verify: No alerts (40% is below 60% threshold)
        assert len(alerts) == 0

    def test_alert_risk_levels_scale_with_concentration(self):
        """
        E2E Test 4: Risk levels scale appropriately

        GIVEN concentration at 60%, 75%, 90%
        THEN risk levels: moderate, high, critical
        """
        # Test 90% concentration = critical
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(datetime.UTC).isoformat()
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      ("agent:warlord", "Warlord", "person", "active", now))
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      ("agent:other", "Other", "person", "active", now))

        resource_id = "resource:water"
        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (resource_id, "Water Access", "tools", True,
              "Life critical", "survival", now))

        # Warlord: 9 offers, Other: 1 offer (90% concentration)
        for i in range(9):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:warlord-{i}", "offer", resource_id,
                  "agent:warlord", 0, "active", None, now))

        cursor.execute("""
            INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("listing:other", "offer", resource_id,
              "agent:other", 0, "active", None, now))

        conn.commit()
        conn.close()

        # Action: Run analytics
        alerts = self.service.detect_battery_warlords()

        # Verify: Critical risk level at 90%
        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.concentration_percentage == 90.0
        assert alert.risk_level == 'critical'

    def test_multiple_power_concentrations_detected(self):
        """
        E2E Test 5: Detect multiple warlords simultaneously

        GIVEN Alice monopolizes water AND Bob monopolizes food
        WHEN analytics runs
        THEN both alerts generated
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(datetime.UTC).isoformat()

        # Create agents
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      ("agent:alice", "Alice", "person", "active", now))
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      ("agent:bob", "Bob", "person", "active", now))
        cursor.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                      ("agent:other", "Other", "person", "active", now))

        # Create two critical resources
        water_id = "resource:water"
        food_id = "resource:food"

        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (water_id, "Water Access", "tools", True,
              "Survival critical", "survival", now))
        cursor.execute("""
            INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (food_id, "Food Storage", "tools", True,
              "Survival critical", "survival", now))

        # Alice: 80% of water
        for i in range(8):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:alice-water-{i}", "offer", water_id,
                  "agent:alice", 0, "active", None, now))
        for i in range(2):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:other-water-{i}", "offer", water_id,
                  "agent:other", 0, "active", None, now))

        # Bob: 75% of food
        for i in range(9):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:bob-food-{i}", "offer", food_id,
                  "agent:bob", 0, "active", None, now))
        for i in range(3):
            cursor.execute("""
                INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"listing:other-food-{i}", "offer", food_id,
                  "agent:other", 0, "active", None, now))

        conn.commit()
        conn.close()

        # Action: Run analytics
        alerts = self.service.detect_battery_warlords()

        # Verify: Both warlords detected
        assert len(alerts) >= 2

        alice_alert = next((a for a in alerts if a.agent_name == "Alice"), None)
        bob_alert = next((a for a in alerts if a.agent_name == "Bob"), None)

        assert alice_alert is not None
        assert bob_alert is not None

        assert alice_alert.concentration_percentage == 80.0
        assert bob_alert.concentration_percentage == 75.0

    def test_alert_to_dict_serialization(self):
        """
        E2E Test 6: Alert serialization for API response

        WHEN alert generated
        THEN to_dict() returns complete, serializable structure
        """
        alert = PowerAlert(
            alert_type='resource_concentration',
            agent_id='agent:carol',
            agent_name='Carol',
            resource_or_skill='Battery Charging',
            concentration_percentage=85.0,
            dependency_count=8,
            risk_level='high',
            analysis='Carol provides 85% of Battery Charging in this community...',
            suggestions=['Organize battery repair workshop', 'Pool community battery resources'],
            criticality_category='power'
        )

        # Action: Serialize
        result = alert.to_dict()

        # Verify: All fields present
        assert result['alert_type'] == 'resource_concentration'
        assert result['agent_id'] == 'agent:carol'
        assert result['agent_name'] == 'Carol'
        assert result['resource_or_skill'] == 'Battery Charging'
        assert result['concentration_percentage'] == 85.0
        assert result['dependency_count'] == 8
        assert result['risk_level'] == 'high'
        assert 'detected_at' in result
        assert len(result['suggestions']) == 2
        assert result['criticality_category'] == 'power'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
