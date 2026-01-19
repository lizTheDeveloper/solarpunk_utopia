"""
Test Mycelial Health Monitor Service

Tests the hardware health monitoring system.
"""

import pytest
from app.services.mycelial_health_monitor_service import MycelialHealthMonitorService


def test_service_initialization():
    """Test that the service initializes correctly"""
    service = MycelialHealthMonitorService()
    assert service is not None
    assert service.platform is not None


def test_battery_health():
    """Test battery health collection"""
    service = MycelialHealthMonitorService()
    health = service.get_battery_health()

    assert "available" in health
    assert "timestamp" in health or "error" in health

    if health["available"]:
        assert "percent" in health
        assert "is_charging" in health
        assert "health_status" in health


def test_storage_health():
    """Test storage health collection"""
    service = MycelialHealthMonitorService()
    health = service.get_storage_health()

    assert "available" in health

    if health["available"]:
        assert "total_bytes" in health
        assert "free_bytes" in health
        assert "free_percent" in health
        assert "health_status" in health


def test_full_health_report():
    """Test full health report generation"""
    service = MycelialHealthMonitorService()
    report = service.get_full_health_report()

    assert "node_id" in report
    assert "timestamp" in report
    assert "platform" in report
    assert "battery" in report
    assert "storage" in report
    assert "temperature" in report
    assert "network" in report
    assert "overall_status" in report
    assert "recommendations" in report

    # Overall status should be one of the valid statuses
    assert report["overall_status"] in ["healthy", "degraded", "critical"]

    # Recommendations should be a list
    assert isinstance(report["recommendations"], list)


def test_recommendations_structure():
    """Test that recommendations have proper structure"""
    service = MycelialHealthMonitorService()
    report = service.get_full_health_report()

    for rec in report["recommendations"]:
        assert "priority" in rec
        assert "action" in rec
        assert "reason" in rec
        assert rec["priority"] in ["low", "medium", "high", "urgent"]


def test_power_outage_detection():
    """Test power outage cluster detection"""
    service = MycelialHealthMonitorService()

    # Create mock reports of nodes on battery
    from datetime import datetime
    now = datetime.now(datetime.UTC).isoformat()

    node_reports = [
        {
            "node_id": "node_001",
            "timestamp": now,
            "battery": {"available": True, "is_charging": False, "percent": 80}
        },
        {
            "node_id": "node_002",
            "timestamp": now,
            "battery": {"available": True, "is_charging": False, "percent": 75}
        },
        {
            "node_id": "node_003",
            "timestamp": now,
            "battery": {"available": True, "is_charging": False, "percent": 90}
        }
    ]

    # Should detect outage with 3 nodes
    outage = service.detect_power_outage_cluster(node_reports)
    assert outage is not None
    assert outage["detected"] is True
    assert outage["node_count"] == 3
    assert outage["alert_type"] == "power_outage"

    # Should NOT detect with only 1 node
    single_report = [node_reports[0]]
    outage = service.detect_power_outage_cluster(single_report)
    assert outage is None


def test_health_status_assessment():
    """Test health status assessment logic"""
    service = MycelialHealthMonitorService()

    # Test healthy battery
    health_healthy = {
        "charge_cycles": 100,
        "capacity_percent": 95,
        "temperature_celsius": 25.0
    }
    status = service._assess_battery_health(health_healthy)
    assert status == "healthy"

    # Test degraded battery (high cycles)
    health_degraded = {
        "charge_cycles": 600,
        "capacity_percent": 90,
        "temperature_celsius": 30.0
    }
    status = service._assess_battery_health(health_degraded)
    assert status == "degraded"

    # Test critical battery (degraded capacity)
    health_critical = {
        "charge_cycles": 700,
        "capacity_percent": 70,
        "temperature_celsius": 35.0
    }
    status = service._assess_battery_health(health_critical)
    assert status == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
