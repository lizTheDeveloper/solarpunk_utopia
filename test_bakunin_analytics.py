"""
Test GAP-64: Battery Warlord Detection (Bakunin Analytics)

Tests the detection of emergent power structures:
- Resource concentration (battery warlords)
- Skill gatekeepers
- Coordination monopolies
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
import uuid

from valueflows_node.app.services.bakunin_analytics_service import BakuninAnalyticsService


@pytest.fixture
def test_db():
    """Create in-memory test database with schema"""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create minimal schema
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
    return conn


def test_detect_battery_warlord(test_db):
    """Test detection of critical resource concentration"""
    cursor = test_db.cursor()

    # Create agents
    dave_id = "agent:dave"
    alice_id = "agent:alice"
    bob_id = "agent:bob"

    cursor.execute("INSERT INTO agents (id, name, agent_type, created_at) VALUES (?, ?, ?, ?)",
                   (dave_id, "Dave", "person", datetime.utcnow().isoformat()))
    cursor.execute("INSERT INTO agents (id, name, agent_type, created_at) VALUES (?, ?, ?, ?)",
                   (alice_id, "Alice", "person", datetime.utcnow().isoformat()))
    cursor.execute("INSERT INTO agents (id, name, agent_type, created_at) VALUES (?, ?, ?, ?)",
                   (bob_id, "Bob", "person", datetime.utcnow().isoformat()))

    # Create critical resource (battery charging)
    battery_id = "resource:battery-charging"
    cursor.execute("""
        INSERT INTO resource_specs (id, name, category, critical, criticality_reason, criticality_category, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (battery_id, "Battery Charging", "tools", True, "Only power source", "power", datetime.utcnow().isoformat()))

    # Dave offers 8 battery charging sessions (80% of total 10)
    for i in range(8):
        cursor.execute("""
            INSERT INTO listings (id, listing_type, resource_spec_id, agent_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"listing:dave-battery-{i}", "offer", battery_id, dave_id, "active", datetime.utcnow().isoformat()))

    # Alice offers 1
    cursor.execute("""
        INSERT INTO listings (id, listing_type, resource_spec_id, agent_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("listing:alice-battery", "offer", battery_id, alice_id, "active", datetime.utcnow().isoformat()))

    # Bob offers 1
    cursor.execute("""
        INSERT INTO listings (id, listing_type, resource_spec_id, agent_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("listing:bob-battery", "offer", battery_id, bob_id, "active", datetime.utcnow().isoformat()))

    # Create exchanges showing 5 people depend on Dave
    for i in range(5):
        cursor.execute("""
            INSERT INTO exchanges (id, provider_id, receiver_id, resource_spec_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"exchange:dave-{i}", dave_id, f"agent:person-{i}", battery_id, "completed", datetime.utcnow().isoformat()))

    test_db.commit()

    # Save database to file for service
    test_db.close()

    # Create service and detect
    service = BakuninAnalyticsService(":memory:")

    # Re-open connection
    import sqlite3
    service.db_path = ":memory:"
    conn2 = sqlite3.connect(":memory:")
    conn2.row_factory = sqlite3.Row

    # Restore data
    cursor2 = conn2.cursor()
    cursor2.execute("""
    CREATE TABLE agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        agent_type TEXT NOT NULL DEFAULT 'person',
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL
    )
    """)
    cursor2.execute("""
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
    cursor2.execute("""
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
    cursor2.execute("""
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

    # Re-insert data
    cursor2.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                    (dave_id, "Dave", "person", "active", datetime.utcnow().isoformat()))
    cursor2.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                    (alice_id, "Alice", "person", "active", datetime.utcnow().isoformat()))
    cursor2.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?)",
                    (bob_id, "Bob", "person", "active", datetime.utcnow().isoformat()))

    cursor2.execute("INSERT INTO resource_specs VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (battery_id, "Battery Charging", "tools", True, "Only power source", "power", datetime.utcnow().isoformat()))

    for i in range(8):
        cursor2.execute("INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (f"listing:dave-battery-{i}", "offer", battery_id, dave_id, 0, "active", None, datetime.utcnow().isoformat()))

    cursor2.execute("INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("listing:alice-battery", "offer", battery_id, alice_id, 0, "active", None, datetime.utcnow().isoformat()))
    cursor2.execute("INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("listing:bob-battery", "offer", battery_id, bob_id, 0, "active", None, datetime.utcnow().isoformat()))

    for i in range(5):
        cursor2.execute("INSERT INTO exchanges VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (f"exchange:dave-{i}", dave_id, f"agent:person-{i}", battery_id, "completed", None, datetime.utcnow().isoformat()))

    conn2.commit()

    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.db') as f:
        for line in conn2.iterdump():
            f.write(f"{line}\n".encode('utf-8'))
        temp_path = f.name

    conn2.close()

    # Test with actual file
    service = BakuninAnalyticsService(temp_path)
    alerts = service.detect_battery_warlords()

    # Should detect Dave as battery warlord
    assert len(alerts) > 0
    dave_alert = next((a for a in alerts if a.agent_name == "Dave"), None)
    assert dave_alert is not None
    assert dave_alert.concentration_percentage == 80.0
    assert dave_alert.risk_level in ['high', 'critical']
    assert "Battery Charging" in dave_alert.resource_or_skill
    assert dave_alert.dependency_count == 5

    # Cleanup
    import os
    os.unlink(temp_path)

    print("✓ Battery warlord detection working!")


def test_detect_skill_gatekeeper(test_db):
    """Test detection of skill monopolies"""
    cursor = test_db.cursor()

    # Create agents
    alice_id = "agent:alice"
    cursor.execute("INSERT INTO agents (id, name, agent_type, created_at) VALUES (?, ?, ?, ?)",
                   (alice_id, "Alice", "person", datetime.utcnow().isoformat()))

    # Create critical skill (bike repair)
    bike_repair_id = "resource:bike-repair"
    cursor.execute("""
        INSERT INTO resource_specs (id, name, category, critical, criticality_reason, criticality_category, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (bike_repair_id, "Bike Repair", "skills", True, "Only mechanic", "skills", datetime.utcnow().isoformat()))

    # Alice is the ONLY person offering bike repair
    cursor.execute("""
        INSERT INTO listings (id, listing_type, resource_spec_id, agent_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("listing:alice-bike", "offer", bike_repair_id, alice_id, "active", datetime.utcnow().isoformat()))

    # 10 people have depended on Alice for bike repair
    for i in range(10):
        cursor.execute("""
            INSERT INTO exchanges (id, provider_id, receiver_id, resource_spec_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"exchange:alice-bike-{i}", alice_id, f"agent:person-{i}", bike_repair_id, "completed", datetime.utcnow().isoformat()))

    test_db.commit()

    # Save to file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.db') as f:
        for line in test_db.iterdump():
            f.write(f"{line}\n".encode('utf-8'))
        temp_path = f.name

    # Test
    service = BakuninAnalyticsService(temp_path)
    alerts = service.detect_skill_gatekeepers()

    # Should detect Alice as skill gatekeeper
    assert len(alerts) > 0
    alice_alert = alerts[0]
    assert alice_alert.agent_name == "Alice"
    assert alice_alert.concentration_percentage == 100.0
    assert alice_alert.risk_level == 'critical'
    assert "Bike Repair" in alice_alert.resource_or_skill
    assert alice_alert.dependency_count == 10

    # Cleanup
    import os
    os.unlink(temp_path)

    print("✓ Skill gatekeeper detection working!")


def test_api_response_format():
    """Test that PowerAlert.to_dict() returns correct format"""
    from valueflows_node.app.services.bakunin_analytics_service import PowerAlert

    alert = PowerAlert(
        alert_type='resource_concentration',
        agent_id='agent:dave',
        agent_name='Dave',
        resource_or_skill='Battery Charging',
        concentration_percentage=80.5,
        dependency_count=12,
        risk_level='high',
        analysis='Dave provides 80.5% of Battery Charging...',
        suggestions=['Organize workshop', 'Pool resources'],
        criticality_category='power'
    )

    result = alert.to_dict()

    assert result['alert_type'] == 'resource_concentration'
    assert result['agent_id'] == 'agent:dave'
    assert result['agent_name'] == 'Dave'
    assert result['concentration_percentage'] == 80.5
    assert result['dependency_count'] == 12
    assert result['risk_level'] == 'high'
    assert len(result['suggestions']) == 2
    assert 'detected_at' in result

    print("✓ API response format correct!")


if __name__ == "__main__":
    # Run individual tests
    test_db = test_db()
    test_detect_battery_warlord(test_db)

    test_db2 = test_db()
    test_detect_skill_gatekeeper(test_db2)

    test_api_response_format()

    print("\n✓ All Bakunin Analytics tests passed!")
    print("\"Where there is authority, there is no freedom.\" - Mikhail Bakunin")
