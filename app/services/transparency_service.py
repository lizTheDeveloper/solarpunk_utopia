"""
Transparency Service

Business logic for algorithmic transparency features:
- Explanation formatting
- Bias detection
- Audit trail management
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, UTC
from collections import defaultdict
import uuid

from app.models.algorithmic_transparency import (
    MatchExplanation,
    MatchingWeights,
    MatchingAuditLog,
    BiasDetectionReport,
    TransparencyPreferences,
    CategoryMatchType,
    DetailLevel,
    BiasReportStatus,
)
from app.repositories.transparency_repository import TransparencyRepository


logger = logging.getLogger(__name__)


class TransparencyService:
    """Service for algorithmic transparency"""

    def __init__(self, repository: Optional[TransparencyRepository] = None):
        self.repository = repository or TransparencyRepository()

    # ==================== Explanation Formatting ====================

    def format_match_explanation(
        self,
        explanation: MatchExplanation,
        preferences: TransparencyPreferences,
    ) -> str:
        """
        Format match explanation based on user preferences.

        Returns human-readable explanation of why match was made.
        """
        if preferences.detail_level == DetailLevel.MINIMAL:
            return self._format_minimal_explanation(explanation)
        elif preferences.detail_level == DetailLevel.MEDIUM:
            return self._format_medium_explanation(explanation, preferences)
        else:  # DETAILED
            return self._format_detailed_explanation(explanation, preferences)

    def _format_minimal_explanation(self, explanation: MatchExplanation) -> str:
        """Minimal explanation - just the basics"""
        return explanation.explanation_text

    def _format_medium_explanation(
        self, explanation: MatchExplanation, preferences: TransparencyPreferences
    ) -> str:
        """Medium explanation - text + key scores"""
        parts = [explanation.explanation_text]

        if preferences.show_score_breakdown:
            parts.append("\n\nMatch Quality:")
            parts.append(f"• Overall: {explanation.total_score:.0%}")

            # Show top contributing factors
            scores = [
                ("Category match", explanation.category_score * explanation.category_weight),
                ("Proximity", explanation.location_score * explanation.location_weight),
                ("Timing", explanation.time_score * explanation.time_weight),
                ("Quantity", explanation.quantity_score * explanation.quantity_weight),
            ]
            scores.sort(key=lambda x: x[1], reverse=True)

            for factor, weighted_score in scores[:2]:  # Top 2 factors
                parts.append(f"• {factor}: {weighted_score:.0%}")

        if explanation.distance_description:
            parts.append(f"\n{explanation.distance_description}")

        return "\n".join(parts)

    def _format_detailed_explanation(
        self, explanation: MatchExplanation, preferences: TransparencyPreferences
    ) -> str:
        """Detailed explanation - full breakdown"""
        parts = [explanation.explanation_text, "\n"]

        if preferences.show_score_breakdown:
            parts.append("Score Breakdown:")
            parts.append(f"• Category: {explanation.category_score:.0%} (weight: {explanation.category_weight:.0%})")
            parts.append(f"• Location: {explanation.location_score:.0%} (weight: {explanation.location_weight:.0%})")
            parts.append(f"• Timing: {explanation.time_score:.0%} (weight: {explanation.time_weight:.0%})")
            parts.append(f"• Quantity: {explanation.quantity_score:.0%} (weight: {explanation.quantity_weight:.0%})")
            parts.append(f"\nTotal Score: {explanation.total_score:.0%}")

        if preferences.show_weights:
            parts.append("\nMatching Priorities:")
            weights = [
                ("Category match", explanation.category_weight),
                ("Proximity", explanation.location_weight),
                ("Timing", explanation.time_weight),
                ("Quantity fit", explanation.quantity_weight),
            ]
            weights.sort(key=lambda x: x[1], reverse=True)
            for factor, weight in weights:
                parts.append(f"• {factor}: {weight:.0%}")

        # Additional details
        details = []
        if explanation.distance_km is not None:
            details.append(f"Distance: {explanation.distance_km:.1f} km")
        if explanation.category_match_type:
            match_types = {
                CategoryMatchType.EXACT: "Exact category match",
                CategoryMatchType.PARENT: "Same category family",
                CategoryMatchType.SEMANTIC: "Related categories",
                CategoryMatchType.NONE: "Different categories",
            }
            details.append(f"Category: {match_types[explanation.category_match_type]}")
        if explanation.time_buffer_hours is not None:
            details.append(f"Time buffer: {explanation.time_buffer_hours:.1f} hours")
        if explanation.quantity_ratio is not None:
            details.append(f"Quantity ratio: {explanation.quantity_ratio:.1f}x")

        if details:
            parts.append("\nDetails:")
            for detail in details:
                parts.append(f"• {detail}")

        return "\n".join(parts)

    def format_rejection_reason(
        self,
        offer_id: str,
        need_id: str,
        score: float,
        threshold: float,
        score_breakdown: Dict[str, float],
    ) -> str:
        """
        Format explanation for why offers and needs were NOT matched.

        Only shown to users who have enabled show_rejection_reasons.
        """
        parts = [f"Score {score:.0%} below threshold ({threshold:.0%})"]

        # Find weakest factors
        factors = [
            ("Category mismatch", score_breakdown.get("category_score", 0)),
            ("Too far apart", score_breakdown.get("location_score", 0)),
            ("Timing conflict", score_breakdown.get("time_score", 0)),
            ("Quantity mismatch", score_breakdown.get("quantity_score", 0)),
        ]
        factors.sort(key=lambda x: x[1])

        weak_factors = [f for f, s in factors if s < 0.5]
        if weak_factors:
            parts.append("\nReasons:")
            for factor in weak_factors:
                parts.append(f"• {factor}")

        return "\n".join(parts)

    # ==================== Bias Detection ====================

    async def detect_bias(
        self,
        community_id: Optional[str] = None,
        days_back: int = 30,
    ) -> BiasDetectionReport:
        """
        Analyze matching patterns for systematic bias.

        Checks for:
        - Geographic bias (certain areas favored/ignored)
        - Category bias (certain categories matched less)
        - Demographic bias (if anonymized data available)
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=days_back)

        # Get audit logs
        logs = await self.repository.get_audit_logs(
            start_time=start_time,
            end_time=end_time,
            community_id=community_id,
        )

        if len(logs) < 10:
            # Not enough data
            return BiasDetectionReport(
                id=f"bias:{uuid.uuid4()}",
                analysis_start=start_time,
                analysis_end=end_time,
                community_id=community_id,
                total_matches_analyzed=len(logs),
                bias_detected=False,
                recommendations=json.dumps({"message": "Insufficient data for bias detection"}),
                created_by="system",
                status=BiasReportStatus.DRAFT,
            )

        # Analyze geographic bias
        geo_bias_score, geo_details = self._detect_geographic_bias(logs)

        # Analyze category bias
        cat_bias_score, cat_details = self._detect_category_bias(logs)

        # Calculate overall bias
        overall_bias = max(geo_bias_score, cat_bias_score)
        bias_detected = overall_bias > 0.3  # Threshold for concern

        # Generate recommendations
        recommendations = self._generate_bias_recommendations(
            geo_bias_score, geo_details, cat_bias_score, cat_details
        )

        report = BiasDetectionReport(
            id=f"bias:{uuid.uuid4()}",
            analysis_start=start_time,
            analysis_end=end_time,
            community_id=community_id,
            total_matches_analyzed=len(logs),
            geographic_bias_score=geo_bias_score,
            geographic_bias_details=json.dumps(geo_details),
            category_bias_score=cat_bias_score,
            category_bias_details=json.dumps(cat_details),
            overall_bias_score=overall_bias,
            bias_detected=bias_detected,
            recommendations=json.dumps(recommendations),
            created_by="system",
            status=BiasReportStatus.DRAFT,
        )

        # Store report
        await self.repository.create_bias_report(report)

        return report

    def _detect_geographic_bias(
        self, logs: List[MatchingAuditLog]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect geographic bias in matching.

        Returns:
            (bias_score 0-1, details dict)
        """
        zone_match_rates: Dict[str, Dict[str, int]] = defaultdict(lambda: {"matched": 0, "total": 0})

        for log in logs:
            if log.provider_zone:
                zone_match_rates[log.provider_zone]["total"] += 1
                if log.matched:
                    zone_match_rates[log.provider_zone]["matched"] += 1

            if log.receiver_zone and log.receiver_zone != log.provider_zone:
                zone_match_rates[log.receiver_zone]["total"] += 1
                if log.matched:
                    zone_match_rates[log.receiver_zone]["matched"] += 1

        if not zone_match_rates:
            return 0.0, {"message": "No geographic data available"}

        # Calculate match rates per zone
        zone_rates = {}
        for zone, counts in zone_match_rates.items():
            if counts["total"] > 0:
                zone_rates[zone] = counts["matched"] / counts["total"]

        if len(zone_rates) < 2:
            return 0.0, {"message": "Insufficient zones for comparison"}

        # Calculate variance in match rates
        rates = list(zone_rates.values())
        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        std_dev = variance ** 0.5

        # Bias score based on coefficient of variation
        cv = std_dev / mean_rate if mean_rate > 0 else 0
        bias_score = min(cv, 1.0)  # Cap at 1.0

        details = {
            "zone_match_rates": {
                zone: {
                    "rate": zone_rates[zone],
                    "count": zone_match_rates[zone]["total"],
                }
                for zone in zone_rates
            },
            "mean_rate": mean_rate,
            "std_dev": std_dev,
            "coefficient_variation": cv,
        }

        return bias_score, details

    def _detect_category_bias(
        self, logs: List[MatchingAuditLog]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect category bias in matching.

        Returns:
            (bias_score 0-1, details dict)
        """
        category_match_rates: Dict[str, Dict[str, int]] = defaultdict(lambda: {"matched": 0, "total": 0})

        for log in logs:
            if log.offer_category:
                category_match_rates[log.offer_category]["total"] += 1
                if log.matched:
                    category_match_rates[log.offer_category]["matched"] += 1

            if log.need_category and log.need_category != log.offer_category:
                category_match_rates[log.need_category]["total"] += 1
                if log.matched:
                    category_match_rates[log.need_category]["matched"] += 1

        if not category_match_rates:
            return 0.0, {"message": "No category data available"}

        # Calculate match rates per category
        category_rates = {}
        for category, counts in category_match_rates.items():
            if counts["total"] >= 3:  # Minimum sample size
                category_rates[category] = counts["matched"] / counts["total"]

        if len(category_rates) < 2:
            return 0.0, {"message": "Insufficient categories for comparison"}

        # Calculate variance
        rates = list(category_rates.values())
        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        std_dev = variance ** 0.5

        cv = std_dev / mean_rate if mean_rate > 0 else 0
        bias_score = min(cv, 1.0)

        details = {
            "category_match_rates": {
                cat: {
                    "rate": category_rates[cat],
                    "count": category_match_rates[cat]["total"],
                }
                for cat in category_rates
            },
            "mean_rate": mean_rate,
            "std_dev": std_dev,
            "coefficient_variation": cv,
        }

        return bias_score, details

    def _generate_bias_recommendations(
        self,
        geo_bias_score: float,
        geo_details: Dict[str, Any],
        cat_bias_score: float,
        cat_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate recommendations for addressing detected bias"""
        recommendations = []

        # Geographic bias recommendations
        if geo_bias_score > 0.3:
            zone_rates = geo_details.get("zone_match_rates", {})
            if zone_rates:
                worst_zones = sorted(
                    zone_rates.items(),
                    key=lambda x: x[1]["rate"]
                )[:3]

                recommendations.append({
                    "issue": "Geographic matching disparity detected",
                    "severity": "high" if geo_bias_score > 0.5 else "medium",
                    "details": f"Some geographic zones have significantly lower match rates",
                    "suggestion": f"Consider increasing location_weight or investigating barriers in: {', '.join([z[0] for z in worst_zones])}",
                    "affected_zones": [z[0] for z in worst_zones],
                })

        # Category bias recommendations
        if cat_bias_score > 0.3:
            cat_rates = cat_details.get("category_match_rates", {})
            if cat_rates:
                worst_cats = sorted(
                    cat_rates.items(),
                    key=lambda x: x[1]["rate"]
                )[:3]

                recommendations.append({
                    "issue": "Category matching disparity detected",
                    "severity": "high" if cat_bias_score > 0.5 else "medium",
                    "details": f"Some categories have significantly lower match rates",
                    "suggestion": f"Consider adjusting category_weight or improving category granularity for: {', '.join([c[0] for c in worst_cats])}",
                    "affected_categories": [c[0] for c in worst_cats],
                })

        if not recommendations:
            recommendations.append({
                "issue": "No significant bias detected",
                "severity": "low",
                "details": "Matching appears relatively fair across analyzed dimensions",
                "suggestion": "Continue monitoring, especially as network grows",
            })

        return {
            "recommendations": recommendations,
            "overall_assessment": "Bias detected - action recommended" if (geo_bias_score > 0.3 or cat_bias_score > 0.3) else "No significant bias detected",
        }

    # ==================== Utility ====================

    def hash_demographic_data(self, user_data: Dict[str, Any]) -> str:
        """
        Create privacy-preserving hash of demographic data.

        Used for bias detection without revealing individual data.
        """
        # Extract relevant demographic fields (if provided)
        demographic_fields = {
            "age_range": user_data.get("age_range"),
            "location_zone": user_data.get("location_zone"),
            "language": user_data.get("language"),
        }

        # Sort and hash
        canonical = json.dumps(demographic_fields, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
