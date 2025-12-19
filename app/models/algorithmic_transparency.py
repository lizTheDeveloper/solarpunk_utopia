"""
Algorithmic Transparency Models

Enables users to understand AI matching decisions through:
- Detailed score breakdowns
- Adjustable weights
- Bias detection
- Audit trails
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class DetailLevel(str, Enum):
    """How much explanation detail user wants"""
    MINIMAL = "minimal"
    MEDIUM = "medium"
    DETAILED = "detailed"


class CategoryMatchType(str, Enum):
    """Type of category match"""
    EXACT = "exact"  # Exact category match
    PARENT = "parent"  # Same top-level category
    SEMANTIC = "semantic"  # Keyword overlap
    NONE = "none"  # No match


class BiasReportStatus(str, Enum):
    """Status of bias detection report"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class MatchExplanation:
    """
    Detailed explanation of why a match was made.
    Provides transparency into AI decision-making.
    """

    id: str
    match_id: str

    # Score breakdown
    category_score: float
    location_score: float
    time_score: float
    quantity_score: float
    total_score: float

    # Applied weights
    category_weight: float
    location_weight: float
    time_weight: float
    quantity_weight: float

    # Human-readable explanation
    explanation_text: str

    # Details
    distance_km: Optional[float] = None
    distance_description: Optional[str] = None
    category_match_type: Optional[CategoryMatchType] = None
    time_buffer_hours: Optional[float] = None
    quantity_ratio: Optional[float] = None

    # Metadata
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "category_score": self.category_score,
            "location_score": self.location_score,
            "time_score": self.time_score,
            "quantity_score": self.quantity_score,
            "total_score": self.total_score,
            "category_weight": self.category_weight,
            "location_weight": self.location_weight,
            "time_weight": self.time_weight,
            "quantity_weight": self.quantity_weight,
            "explanation_text": self.explanation_text,
            "distance_km": self.distance_km,
            "distance_description": self.distance_description,
            "category_match_type": self.category_match_type.value if self.category_match_type else None,
            "time_buffer_hours": self.time_buffer_hours,
            "quantity_ratio": self.quantity_ratio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchExplanation":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            match_id=data["match_id"],
            category_score=data["category_score"],
            location_score=data["location_score"],
            time_score=data["time_score"],
            quantity_score=data["quantity_score"],
            total_score=data["total_score"],
            category_weight=data["category_weight"],
            location_weight=data["location_weight"],
            time_weight=data["time_weight"],
            quantity_weight=data["quantity_weight"],
            explanation_text=data["explanation_text"],
            distance_km=data.get("distance_km"),
            distance_description=data.get("distance_description"),
            category_match_type=CategoryMatchType(data["category_match_type"]) if data.get("category_match_type") else None,
            time_buffer_hours=data.get("time_buffer_hours"),
            quantity_ratio=data.get("quantity_ratio"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


@dataclass
class MatchingWeights:
    """
    Configurable weights for matching algorithm.
    Allows communities to tune matching priorities.
    """

    id: str
    community_id: Optional[str]

    # Weights (must sum to 1.0)
    category_weight: float = 0.4
    location_weight: float = 0.3
    time_weight: float = 0.2
    quantity_weight: float = 0.1

    # Description
    name: str = "Default"
    description: Optional[str] = None

    # Activation
    is_active: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0 (within floating point tolerance)"""
        total = self.category_weight + self.location_weight + self.time_weight + self.quantity_weight
        return abs(total - 1.0) < 0.001

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "community_id": self.community_id,
            "category_weight": self.category_weight,
            "location_weight": self.location_weight,
            "time_weight": self.time_weight,
            "quantity_weight": self.quantity_weight,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchingWeights":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            community_id=data.get("community_id"),
            category_weight=data.get("category_weight", 0.4),
            location_weight=data.get("location_weight", 0.3),
            time_weight=data.get("time_weight", 0.2),
            quantity_weight=data.get("quantity_weight", 0.1),
            name=data.get("name", "Default"),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            created_by=data.get("created_by"),
        )


@dataclass
class MatchingAuditLog:
    """
    Audit trail for all matching decisions.
    Enables bias detection and algorithmic accountability.
    """

    id: str

    # What was considered (required fields first)
    offer_id: str
    need_id: str

    # Score
    match_score: float
    threshold_score: float
    matched: bool  # TRUE if match created, FALSE if score too low

    # Weights used
    weights_config_id: str

    # Optional fields
    match_id: Optional[str] = None  # NULL if no match created

    # Anonymized demographic data (for bias detection)
    provider_demographic_hash: Optional[str] = None
    receiver_demographic_hash: Optional[str] = None

    # Location zones
    provider_zone: Optional[str] = None
    receiver_zone: Optional[str] = None

    # Categories
    offer_category: Optional[str] = None
    need_category: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    agent_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "offer_id": self.offer_id,
            "need_id": self.need_id,
            "match_score": self.match_score,
            "threshold_score": self.threshold_score,
            "matched": self.matched,
            "weights_config_id": self.weights_config_id,
            "provider_demographic_hash": self.provider_demographic_hash,
            "receiver_demographic_hash": self.receiver_demographic_hash,
            "provider_zone": self.provider_zone,
            "receiver_zone": self.receiver_zone,
            "offer_category": self.offer_category,
            "need_category": self.need_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "agent_version": self.agent_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchingAuditLog":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            match_id=data.get("match_id"),
            offer_id=data["offer_id"],
            need_id=data["need_id"],
            match_score=data["match_score"],
            threshold_score=data["threshold_score"],
            matched=data["matched"],
            weights_config_id=data["weights_config_id"],
            provider_demographic_hash=data.get("provider_demographic_hash"),
            receiver_demographic_hash=data.get("receiver_demographic_hash"),
            provider_zone=data.get("provider_zone"),
            receiver_zone=data.get("receiver_zone"),
            offer_category=data.get("offer_category"),
            need_category=data.get("need_category"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            agent_version=data.get("agent_version"),
        )


@dataclass
class BiasDetectionReport:
    """
    Analysis of matching patterns to detect systematic bias.
    Helps communities identify and correct unfair matching.
    """

    id: str

    # Time window
    analysis_start: datetime
    analysis_end: datetime

    # Scope
    community_id: Optional[str] = None
    category: Optional[str] = None  # NULL = all categories

    # Findings
    total_matches_analyzed: int = 0

    # Bias scores (0-1, higher = more bias)
    geographic_bias_score: Optional[float] = None
    geographic_bias_details: Optional[str] = None  # JSON

    category_bias_score: Optional[float] = None
    category_bias_details: Optional[str] = None  # JSON

    demographic_bias_score: Optional[float] = None
    demographic_bias_details: Optional[str] = None  # JSON

    # Overall
    overall_bias_score: Optional[float] = None
    bias_detected: bool = False
    recommendations: Optional[str] = None  # JSON

    # Metadata
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Status
    status: BiasReportStatus = BiasReportStatus.DRAFT

    # Community review
    community_reviewed: bool = False
    community_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "analysis_start": self.analysis_start.isoformat(),
            "analysis_end": self.analysis_end.isoformat(),
            "community_id": self.community_id,
            "category": self.category,
            "total_matches_analyzed": self.total_matches_analyzed,
            "geographic_bias_score": self.geographic_bias_score,
            "geographic_bias_details": self.geographic_bias_details,
            "category_bias_score": self.category_bias_score,
            "category_bias_details": self.category_bias_details,
            "demographic_bias_score": self.demographic_bias_score,
            "demographic_bias_details": self.demographic_bias_details,
            "overall_bias_score": self.overall_bias_score,
            "bias_detected": self.bias_detected,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "status": self.status.value,
            "community_reviewed": self.community_reviewed,
            "community_response": self.community_response,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BiasDetectionReport":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            analysis_start=datetime.fromisoformat(data["analysis_start"]),
            analysis_end=datetime.fromisoformat(data["analysis_end"]),
            community_id=data.get("community_id"),
            category=data.get("category"),
            total_matches_analyzed=data.get("total_matches_analyzed", 0),
            geographic_bias_score=data.get("geographic_bias_score"),
            geographic_bias_details=data.get("geographic_bias_details"),
            category_bias_score=data.get("category_bias_score"),
            category_bias_details=data.get("category_bias_details"),
            demographic_bias_score=data.get("demographic_bias_score"),
            demographic_bias_details=data.get("demographic_bias_details"),
            overall_bias_score=data.get("overall_bias_score"),
            bias_detected=data.get("bias_detected", False),
            recommendations=data.get("recommendations"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            created_by=data.get("created_by"),
            status=BiasReportStatus(data.get("status", "draft")),
            community_reviewed=data.get("community_reviewed", False),
            community_response=data.get("community_response"),
        )


@dataclass
class TransparencyPreferences:
    """
    User preferences for explanation detail.
    Allows users to control information density.
    """

    user_id: str

    # Detail level
    detail_level: DetailLevel = DetailLevel.MEDIUM

    # Show specific components
    show_score_breakdown: bool = True
    show_weights: bool = True
    show_rejection_reasons: bool = False
    receive_bias_reports: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "detail_level": self.detail_level.value,
            "show_score_breakdown": self.show_score_breakdown,
            "show_weights": self.show_weights,
            "show_rejection_reasons": self.show_rejection_reasons,
            "receive_bias_reports": self.receive_bias_reports,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransparencyPreferences":
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            detail_level=DetailLevel(data.get("detail_level", "medium")),
            show_score_breakdown=data.get("show_score_breakdown", True),
            show_weights=data.get("show_weights", True),
            show_rejection_reasons=data.get("show_rejection_reasons", False),
            receive_bias_reports=data.get("receive_bias_reports", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
