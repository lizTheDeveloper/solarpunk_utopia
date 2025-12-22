"""
Tests for Algorithmic Transparency

Tests:
- Match explanation generation
- Adjustable weights
- Bias detection
- Audit trail
- User preferences
"""

import pytest
from datetime import datetime, timedelta, UTC
import uuid

from app.models.algorithmic_transparency import (
    MatchExplanation,
    MatchingWeights,
    MatchingAuditLog,
    BiasDetectionReport,
    TransparencyPreferences,
    DetailLevel,
    CategoryMatchType,
)
from app.services.transparency_service import TransparencyService


# ==================== Match Explanation Tests ====================

def test_match_explanation_creation():
    """Test creating a match explanation"""
    explanation = MatchExplanation(
        id="exp:1",
        match_id="match:1",
        category_score=0.8,
        location_score=0.9,
        time_score=0.7,
        quantity_score=1.0,
        total_score=0.85,
        category_weight=0.4,
        location_weight=0.3,
        time_weight=0.2,
        quantity_weight=0.1,
        explanation_text="Good match: nearby, exact category, plenty of time",
        distance_km=2.5,
        distance_description="Nearby (2.5 km)",
        category_match_type=CategoryMatchType.EXACT,
        time_buffer_hours=48.0,
        quantity_ratio=1.2,
    )

    assert explanation.total_score == 0.85
    assert explanation.category_match_type == CategoryMatchType.EXACT
    assert explanation.distance_km == 2.5


def test_explanation_formatting_minimal():
    """Test minimal explanation formatting"""
    service = TransparencyService()

    explanation = MatchExplanation(
        id="exp:1",
        match_id="match:1",
        category_score=0.8,
        location_score=0.9,
        time_score=0.7,
        quantity_score=1.0,
        total_score=0.85,
        category_weight=0.4,
        location_weight=0.3,
        time_weight=0.2,
        quantity_weight=0.1,
        explanation_text="Good match: nearby, exact category, plenty of time",
    )

    prefs = TransparencyPreferences(
        user_id="user:1",
        detail_level=DetailLevel.MINIMAL,
    )

    formatted = service.format_match_explanation(explanation, prefs)

    assert formatted == "Good match: nearby, exact category, plenty of time"


def test_explanation_formatting_detailed():
    """Test detailed explanation formatting"""
    service = TransparencyService()

    explanation = MatchExplanation(
        id="exp:1",
        match_id="match:1",
        category_score=0.8,
        location_score=0.9,
        time_score=0.7,
        quantity_score=1.0,
        total_score=0.85,
        category_weight=0.4,
        location_weight=0.3,
        time_weight=0.2,
        quantity_weight=0.1,
        explanation_text="Good match",
        distance_km=2.5,
        category_match_type=CategoryMatchType.EXACT,
        time_buffer_hours=48.0,
        quantity_ratio=1.2,
    )

    prefs = TransparencyPreferences(
        user_id="user:1",
        detail_level=DetailLevel.DETAILED,
        show_score_breakdown=True,
        show_weights=True,
    )

    formatted = service.format_match_explanation(explanation, prefs)

    assert "Score Breakdown" in formatted
    assert "Category: 80%" in formatted
    assert "Location: 90%" in formatted
    assert "Distance: 2.5 km" in formatted


# ==================== Matching Weights Tests ====================

def test_weights_validation():
    """Test that weights must sum to 1.0"""
    # Valid weights
    weights = MatchingWeights(
        id="weights:1",
        community_id=None,
        category_weight=0.4,
        location_weight=0.3,
        time_weight=0.2,
        quantity_weight=0.1,
        name="Valid",
    )

    assert weights.validate_weights() is True

    # Invalid weights (sum > 1.0)
    invalid_weights = MatchingWeights(
        id="weights:2",
        community_id=None,
        category_weight=0.5,
        location_weight=0.4,
        time_weight=0.3,
        quantity_weight=0.2,
        name="Invalid",
    )

    assert invalid_weights.validate_weights() is False


def test_custom_weights():
    """Test creating custom weight configuration"""
    # Community that prioritizes proximity over category
    proximity_focused = MatchingWeights(
        id="weights:proximity",
        community_id="community:1",
        category_weight=0.2,  # Lower
        location_weight=0.5,  # Higher
        time_weight=0.2,
        quantity_weight=0.1,
        name="Proximity Focused",
        description="For dense urban communities where distance matters most",
    )

    assert proximity_focused.validate_weights() is True
    assert proximity_focused.location_weight == 0.5
    assert proximity_focused.category_weight == 0.2


# ==================== Bias Detection Tests ====================

def test_geographic_bias_detection():
    """Test detection of geographic bias in matching"""
    service = TransparencyService()

    # Create audit logs with geographic bias (zone A gets matched more)
    logs = []

    # Zone A: 80% match rate
    for i in range(10):
        logs.append(MatchingAuditLog(
            id=f"audit:{uuid.uuid4()}",
            offer_id=f"offer:{i}",
            need_id=f"need:{i}",
            match_score=0.7,
            threshold_score=0.6,
            matched=i < 8,  # 8 out of 10 matched
            weights_config_id="weights:default",
            provider_zone="zone_a",
            receiver_zone="zone_a",
            offer_category="food",
            need_category="food",
        ))

    # Zone B: 30% match rate
    for i in range(10, 20):
        logs.append(MatchingAuditLog(
            id=f"audit:{uuid.uuid4()}",
            offer_id=f"offer:{i}",
            need_id=f"need:{i}",
            match_score=0.7,
            threshold_score=0.6,
            matched=i < 13,  # 3 out of 10 matched
            weights_config_id="weights:default",
            provider_zone="zone_b",
            receiver_zone="zone_b",
            offer_category="food",
            need_category="food",
        ))

    # Detect bias
    bias_score, details = service._detect_geographic_bias(logs)

    # Should detect bias
    assert bias_score > 0.3
    assert "zone_a" in details["zone_match_rates"]
    assert "zone_b" in details["zone_match_rates"]
    assert details["zone_match_rates"]["zone_a"]["rate"] > details["zone_match_rates"]["zone_b"]["rate"]


def test_category_bias_detection():
    """Test detection of category bias in matching"""
    service = TransparencyService()

    logs = []

    # Food category: 70% match rate
    for i in range(10):
        logs.append(MatchingAuditLog(
            id=f"audit:{uuid.uuid4()}",
            offer_id=f"offer:{i}",
            need_id=f"need:{i}",
            match_score=0.7,
            threshold_score=0.6,
            matched=i < 7,
            weights_config_id="weights:default",
            provider_zone="zone_a",
            receiver_zone="zone_a",
            offer_category="food",
            need_category="food",
        ))

    # Tools category: 20% match rate
    for i in range(10, 20):
        logs.append(MatchingAuditLog(
            id=f"audit:{uuid.uuid4()}",
            offer_id=f"offer:{i}",
            need_id=f"need:{i}",
            match_score=0.7,
            threshold_score=0.6,
            matched=i < 12,
            weights_config_id="weights:default",
            provider_zone="zone_a",
            receiver_zone="zone_a",
            offer_category="tools",
            need_category="tools",
        ))

    bias_score, details = service._detect_category_bias(logs)

    assert bias_score > 0.2
    assert "food" in details["category_match_rates"]
    assert "tools" in details["category_match_rates"]


# ==================== Audit Trail Tests ====================

def test_audit_log_creation():
    """Test creating audit log entry"""
    log = MatchingAuditLog(
        id="audit:1",
        match_id="match:1",
        offer_id="offer:1",
        need_id="need:1",
        match_score=0.75,
        threshold_score=0.6,
        matched=True,
        weights_config_id="weights:default",
        provider_zone="downtown",
        receiver_zone="downtown",
        offer_category="food:produce",
        need_category="food:produce",
        agent_version="1.0.0",
    )

    assert log.matched is True
    assert log.match_score > log.threshold_score


def test_rejection_logging():
    """Test that rejected matches are logged"""
    log = MatchingAuditLog(
        id="audit:2",
        match_id=None,  # No match created
        offer_id="offer:2",
        need_id="need:2",
        match_score=0.45,
        threshold_score=0.6,
        matched=False,  # Below threshold
        weights_config_id="weights:default",
        offer_category="housing",
        need_category="food",
    )

    assert log.matched is False
    assert log.match_id is None
    assert log.match_score < log.threshold_score


# ==================== User Preferences Tests ====================

def test_transparency_preferences():
    """Test user transparency preferences"""
    prefs = TransparencyPreferences(
        user_id="user:1",
        detail_level=DetailLevel.MEDIUM,
        show_score_breakdown=True,
        show_weights=True,
        show_rejection_reasons=False,
        receive_bias_reports=True,
    )

    assert prefs.detail_level == DetailLevel.MEDIUM
    assert prefs.show_score_breakdown is True
    assert prefs.show_rejection_reasons is False


def test_preference_defaults():
    """Test that preferences have sensible defaults"""
    prefs = TransparencyPreferences(user_id="user:2")

    assert prefs.detail_level == DetailLevel.MEDIUM
    assert prefs.show_score_breakdown is True
    assert prefs.show_weights is True
    assert prefs.show_rejection_reasons is False
    assert prefs.receive_bias_reports is True


# ==================== Integration Tests ====================

def test_end_to_end_transparency():
    """Test complete transparency flow"""
    # 1. Create weights
    weights = MatchingWeights(
        id="weights:test",
        community_id="community:test",
        category_weight=0.4,
        location_weight=0.3,
        time_weight=0.2,
        quantity_weight=0.1,
        name="Test Weights",
    )

    assert weights.validate_weights()

    # 2. Create match explanation
    explanation = MatchExplanation(
        id="exp:test",
        match_id="match:test",
        category_score=0.9,
        location_score=0.8,
        time_score=0.7,
        quantity_score=1.0,
        total_score=0.85,
        category_weight=weights.category_weight,
        location_weight=weights.location_weight,
        time_weight=weights.time_weight,
        quantity_weight=weights.quantity_weight,
        explanation_text="Excellent match",
        category_match_type=CategoryMatchType.EXACT,
    )

    # 3. Format for user
    service = TransparencyService()
    prefs = TransparencyPreferences(
        user_id="user:test",
        detail_level=DetailLevel.DETAILED,
    )

    formatted = service.format_match_explanation(explanation, prefs)

    assert "Excellent match" in formatted
    assert "90%" in formatted  # Category score


def test_bias_report_generation():
    """Test generating bias detection report"""
    report = BiasDetectionReport(
        id="bias:1",
        analysis_start=datetime.now(UTC) - timedelta(days=30),
        analysis_end=datetime.now(UTC),
        community_id="community:1",
        total_matches_analyzed=100,
        geographic_bias_score=0.35,
        geographic_bias_details='{"message": "Some geographic disparity detected"}',
        category_bias_score=0.15,
        category_bias_details='{"message": "Categories relatively balanced"}',
        overall_bias_score=0.35,
        bias_detected=True,
        recommendations='{"suggestions": ["Investigate zone_b barriers"]}',
        created_by="system",
    )

    assert report.bias_detected is True
    assert report.overall_bias_score == 0.35
    assert report.geographic_bias_score > report.category_bias_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
