"""
Algorithmic Transparency API Endpoints

Provides transparency into AI matching decisions:
- Match explanations
- Weight configuration
- Bias detection reports
- User preferences
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta, UTC

from app.models.algorithmic_transparency import (
    MatchExplanation,
    MatchingWeights,
    BiasDetectionReport,
    TransparencyPreferences,
    DetailLevel,
    BiasReportStatus,
)
from app.repositories.transparency_repository import TransparencyRepository
from app.services.transparency_service import TransparencyService


router = APIRouter(prefix="/transparency", tags=["transparency"])


# ==================== Pydantic Models ====================

class MatchExplanationResponse(BaseModel):
    """Response model for match explanations"""
    id: str
    match_id: str
    total_score: float
    explanation_text: str
    category_score: Optional[float] = None
    location_score: Optional[float] = None
    time_score: Optional[float] = None
    quantity_score: Optional[float] = None
    category_weight: Optional[float] = None
    location_weight: Optional[float] = None
    time_weight: Optional[float] = None
    quantity_weight: Optional[float] = None
    distance_km: Optional[float] = None
    distance_description: Optional[str] = None
    category_match_type: Optional[str] = None
    time_buffer_hours: Optional[float] = None
    quantity_ratio: Optional[float] = None

    class Config:
        from_attributes = True


class WeightsRequest(BaseModel):
    """Request to create/update matching weights"""
    community_id: Optional[str] = None
    category_weight: float
    location_weight: float
    time_weight: float
    quantity_weight: float
    name: str
    description: Optional[str] = None
    is_active: bool = True


class BiasReportRequest(BaseModel):
    """Request to run bias detection"""
    community_id: Optional[str] = None
    days_back: int = 30


class PreferencesRequest(BaseModel):
    """Request to update transparency preferences"""
    detail_level: str = "medium"
    show_score_breakdown: bool = True
    show_weights: bool = True
    show_rejection_reasons: bool = False
    receive_bias_reports: bool = True


# ==================== Dependency Injection ====================

def get_transparency_repo() -> TransparencyRepository:
    """Get transparency repository instance"""
    return TransparencyRepository()


def get_transparency_service() -> TransparencyService:
    """Get transparency service instance"""
    return TransparencyService()


# ==================== Match Explanations ====================

@router.get("/matches/{match_id}/explanation", response_model=MatchExplanationResponse)
async def get_match_explanation(
    match_id: str,
    user_id: str,
    repo: TransparencyRepository = Depends(get_transparency_repo),
    service: TransparencyService = Depends(get_transparency_service),
):
    """
    Get detailed explanation for a match.

    Returns explanation formatted according to user preferences.
    """
    # Get user preferences
    preferences = await repo.get_transparency_preferences(user_id)

    # Get explanation
    explanation = await repo.get_match_explanation(match_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Match explanation not found")

    # Format according to preferences
    formatted_text = service.format_match_explanation(explanation, preferences)

    # Return appropriate level of detail
    response_data = {
        "id": explanation.id,
        "match_id": explanation.match_id,
        "total_score": explanation.total_score,
        "explanation_text": formatted_text,
    }

    if preferences.show_score_breakdown:
        response_data.update({
            "category_score": explanation.category_score,
            "location_score": explanation.location_score,
            "time_score": explanation.time_score,
            "quantity_score": explanation.quantity_score,
        })

    if preferences.show_weights:
        response_data.update({
            "category_weight": explanation.category_weight,
            "location_weight": explanation.location_weight,
            "time_weight": explanation.time_weight,
            "quantity_weight": explanation.quantity_weight,
        })

    if preferences.detail_level == "detailed":
        response_data.update({
            "distance_km": explanation.distance_km,
            "distance_description": explanation.distance_description,
            "category_match_type": explanation.category_match_type.value if explanation.category_match_type else None,
            "time_buffer_hours": explanation.time_buffer_hours,
            "quantity_ratio": explanation.quantity_ratio,
        })

    return MatchExplanationResponse(**response_data)


# ==================== Matching Weights ====================

@router.get("/weights", response_model=List[dict])
async def list_matching_weights(
    community_id: Optional[str] = None,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """
    List all weight configurations for a community.

    Returns both active and historical configurations.
    """
    weights = await repo.list_weights(community_id)
    return [w.to_dict() for w in weights]


@router.get("/weights/active", response_model=dict)
async def get_active_weights(
    community_id: Optional[str] = None,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """Get currently active matching weights for community"""
    weights = await repo.get_active_weights(community_id)
    return weights.to_dict()


@router.post("/weights", response_model=dict)
async def create_matching_weights(
    request: WeightsRequest,
    user_id: str,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """
    Create new matching weights configuration.

    Allows communities to tune matching priorities.
    Weights must sum to 1.0.
    """
    import uuid

    # Validate weights sum to 1.0
    total = (
        request.category_weight +
        request.location_weight +
        request.time_weight +
        request.quantity_weight
    )
    if abs(total - 1.0) > 0.001:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0 (got {total})"
        )

    weights = MatchingWeights(
        id=f"weights:{uuid.uuid4()}",
        community_id=request.community_id,
        category_weight=request.category_weight,
        location_weight=request.location_weight,
        time_weight=request.time_weight,
        quantity_weight=request.quantity_weight,
        name=request.name,
        description=request.description,
        is_active=request.is_active,
        created_by=user_id,
    )

    created = await repo.create_matching_weights(weights)
    return created.to_dict()


@router.put("/weights/{weights_id}", response_model=dict)
async def update_matching_weights(
    weights_id: str,
    request: WeightsRequest,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """Update existing matching weights configuration"""
    # Validate weights sum to 1.0
    total = (
        request.category_weight +
        request.location_weight +
        request.time_weight +
        request.quantity_weight
    )
    if abs(total - 1.0) > 0.001:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0 (got {total})"
        )

    weights = MatchingWeights(
        id=weights_id,
        community_id=request.community_id,
        category_weight=request.category_weight,
        location_weight=request.location_weight,
        time_weight=request.time_weight,
        quantity_weight=request.quantity_weight,
        name=request.name,
        description=request.description,
        is_active=request.is_active,
    )

    updated = await repo.update_matching_weights(weights)
    return updated.to_dict()


# ==================== Bias Detection ====================

@router.post("/bias-detection/run", response_model=dict)
async def run_bias_detection(
    request: BiasReportRequest,
    service: TransparencyService = Depends(get_transparency_service),
):
    """
    Run bias detection analysis on matching patterns.

    Analyzes recent matches for systematic bias in:
    - Geographic distribution
    - Category distribution
    - Demographic patterns (if data available)

    Returns report with findings and recommendations.
    """
    report = await service.detect_bias(
        community_id=request.community_id,
        days_back=request.days_back,
    )

    return report.to_dict()


@router.get("/bias-detection/reports", response_model=List[dict])
async def list_bias_reports(
    community_id: Optional[str] = None,
    status: Optional[str] = None,
    bias_detected_only: bool = False,
    limit: int = 20,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """List bias detection reports"""
    status_enum = BiasReportStatus(status) if status else None

    reports = await repo.list_bias_reports(
        community_id=community_id,
        status=status_enum,
        bias_detected_only=bias_detected_only,
        limit=limit,
    )

    return [r.to_dict() for r in reports]


@router.get("/bias-detection/reports/{report_id}", response_model=dict)
async def get_bias_report(
    report_id: str,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """Get specific bias detection report"""
    report = await repo.get_bias_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report.to_dict()


# ==================== User Preferences ====================

@router.get("/preferences/{user_id}", response_model=dict)
async def get_transparency_preferences(
    user_id: str,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """Get user transparency preferences"""
    prefs = await repo.get_transparency_preferences(user_id)
    return prefs.to_dict()


@router.put("/preferences/{user_id}", response_model=dict)
async def update_transparency_preferences(
    user_id: str,
    request: PreferencesRequest,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """Update user transparency preferences"""
    prefs = TransparencyPreferences(
        user_id=user_id,
        detail_level=DetailLevel(request.detail_level),
        show_score_breakdown=request.show_score_breakdown,
        show_weights=request.show_weights,
        show_rejection_reasons=request.show_rejection_reasons,
        receive_bias_reports=request.receive_bias_reports,
    )

    updated = await repo.update_transparency_preferences(prefs)
    return updated.to_dict()


# ==================== Statistics ====================

@router.get("/stats/overview")
async def get_transparency_stats(
    community_id: Optional[str] = None,
    days_back: int = 30,
    repo: TransparencyRepository = Depends(get_transparency_repo),
):
    """
    Get overview statistics about matching transparency.

    Returns:
    - Total matches analyzed
    - Average match scores
    - Most recent bias detection results
    """
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=days_back)

    # Get audit logs
    logs = await repo.get_audit_logs(
        start_time=start_time,
        end_time=end_time,
        community_id=community_id,
        limit=1000,
    )

    matched_logs = [log for log in logs if log.matched]

    stats = {
        "period_days": days_back,
        "total_analyzed": len(logs),
        "total_matched": len(matched_logs),
        "match_rate": len(matched_logs) / len(logs) if logs else 0,
        "average_score": sum(log.match_score for log in matched_logs) / len(matched_logs) if matched_logs else 0,
    }

    # Get most recent bias report
    reports = await repo.list_bias_reports(
        community_id=community_id,
        limit=1,
    )

    if reports:
        stats["latest_bias_report"] = {
            "id": reports[0].id,
            "bias_detected": reports[0].bias_detected,
            "overall_bias_score": reports[0].overall_bias_score,
            "created_at": reports[0].created_at.isoformat() if reports[0].created_at else None,
        }

    return stats
