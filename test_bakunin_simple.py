"""
Simple test for GAP-64: Battery Warlord Detection
Tests the API response format without needing full database setup
"""

from valueflows_node.app.services.bakunin_analytics_service import PowerAlert


def test_power_alert_format():
    """Test that PowerAlert creates correct dict format"""
    alert = PowerAlert(
        alert_type='resource_concentration',
        agent_id='agent:dave',
        agent_name='Dave',
        resource_or_skill='Battery Charging',
        concentration_percentage=80.5,
        dependency_count=12,
        risk_level='high',
        analysis='Dave provides 80.5% of Battery Charging in the community.',
        suggestions=['Organize workshop on battery maintenance', 'Pool resources to buy more chargers'],
        criticality_category='power'
    )

    result = alert.to_dict()

    assert result['alert_type'] == 'resource_concentration'
    assert result['agent_id'] == 'agent:dave'
    assert result['agent_name'] == 'Dave'
    assert result['resource_or_skill'] == 'Battery Charging'
    assert result['concentration_percentage'] == 80.5
    assert result['dependency_count'] == 12
    assert result['risk_level'] == 'high'
    assert 'Dave provides 80.5%' in result['analysis']
    assert len(result['suggestions']) == 2
    assert 'workshop' in result['suggestions'][0].lower()
    assert result['criticality_category'] == 'power'
    assert 'detected_at' in result
    assert result['detected_at'] is not None

    print("✓ PowerAlert.to_dict() format correct")
    print(f"  Alert type: {result['alert_type']}")
    print(f"  Agent: {result['agent_name']}")
    print(f"  Resource: {result['resource_or_skill']}")
    print(f"  Concentration: {result['concentration_percentage']}%")
    print(f"  Risk level: {result['risk_level']}")
    print(f"  Dependencies: {result['dependency_count']} people")
    print(f"  Suggestions: {len(result['suggestions'])}")


def test_analysis_generators():
    """Test that analysis text generators work"""
    from valueflows_node.app.services.bakunin_analytics_service import BakuninAnalyticsService

    service = BakuninAnalyticsService(":memory:")

    # Test warlord analysis
    analysis = service._generate_warlord_analysis(
        agent_name="Dave",
        resource_name="Battery Charging",
        percentage=80.0,
        dep_count=15,
        reason="Only power source"
    )

    assert "Dave provides 80.0%" in analysis
    assert "Battery Charging" in analysis
    assert "15 people depend" in analysis
    assert "dependency" in analysis.lower()
    assert "Only power source" in analysis

    print("✓ Warlord analysis generator working")
    print(f"  Generated: {analysis[:100]}...")

    # Test gatekeeper analysis
    analysis2 = service._generate_gatekeeper_analysis(
        agent_name="Alice",
        skill_name="Bike Repair",
        total_providers=1,
        dep_count=10
    )

    assert "Only Alice" in analysis2
    assert "Bike Repair" in analysis2
    assert "10 people" in analysis2
    assert "incredible work" in analysis2  # Celebrates while critiquing structure

    print("✓ Gatekeeper analysis generator working")
    print(f"  Generated: {analysis2[:100]}...")

    # Test coordination analysis
    analysis3 = service._generate_coordination_analysis(
        agent_name="Carol",
        count=85,
        percentage=75.5,
        partners=23,
        days=90
    )

    assert "Carol has coordinated 85" in analysis3
    assert "75.5%" in analysis3
    assert "23 different people" in analysis3
    assert "amazing" in analysis3.lower()  # Celebrates
    assert "dependency" in analysis3.lower()  # But critiques structure

    print("✓ Coordination analysis generator working")
    print(f"  Generated: {analysis3[:100]}...")


def test_suggestion_generators():
    """Test that suggestions are helpful"""
    from valueflows_node.app.services.bakunin_analytics_service import BakuninAnalyticsService

    service = BakuninAnalyticsService(":memory:")

    # Test decentralization suggestions for power
    suggestions = service._generate_decentralization_suggestions(
        resource_name="Solar Battery",
        category="power"
    )

    assert len(suggestions) >= 3
    assert any("workshop" in s.lower() for s in suggestions)
    assert any("distributed" in s.lower() or "solar" in s.lower() for s in suggestions)

    print("✓ Decentralization suggestions working")
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. {sug}")

    # Test skill sharing suggestions
    suggestions2 = service._generate_skill_sharing_suggestions(
        skill_name="Bike Repair",
        agent_name="Alice"
    )

    assert len(suggestions2) >= 3
    assert any("Alice" in s and "teach" in s.lower() for s in suggestions2)
    assert any("workshop" in s.lower() for s in suggestions2)
    assert any("document" in s.lower() for s in suggestions2)

    print("✓ Skill sharing suggestions working")
    for i, sug in enumerate(suggestions2, 1):
        print(f"  {i}. {sug}")

    # Test coordination suggestions
    suggestions3 = service._generate_coordination_suggestions("Carol")

    assert len(suggestions3) >= 3
    assert any("rotate" in s.lower() for s in suggestions3)
    assert any("Carol" in s for s in suggestions3)

    print("✓ Coordination suggestions working")
    for i, sug in enumerate(suggestions3, 1):
        print(f"  {i}. {sug}")


if __name__ == "__main__":
    print("=" * 60)
    print("GAP-64: Battery Warlord Detection - Simple Tests")
    print("Philosophical Foundation: Mikhail Bakunin")
    print("\"Where there is authority, there is no freedom.\"")
    print("=" * 60)
    print()

    test_power_alert_format()
    print()

    test_analysis_generators()
    print()

    test_suggestion_generators()
    print()

    print("=" * 60)
    print("✓ All tests passed!")
    print()
    print("The Bakunin Analytics Service can now detect:")
    print("  1. Critical resource concentration (battery warlords)")
    print("  2. Skill monopolies (gatekeepers)")
    print("  3. Coordination bottlenecks (monopolies)")
    print()
    print("This helps communities see invisible power structures")
    print("before they solidify into hierarchy.")
    print("=" * 60)
