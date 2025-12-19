# Proposal: Algorithmic Transparency

**Status:** IMPLEMENTED
**Philosopher:** Joy Buolamwini (Algorithmic Justice)

## Problem
AI agents match offers to needs. But users don't know WHY they got matched. Is it fair? Is it biased? Black box matching erodes trust.

## Solution
Every AI match includes an **explanation**:
- "Matched because: proximity (2 miles), skill match (woodworking), trust score (7.2/10)"
- "Not matched because: too far (15 miles), no mutual availability"
- Users can see the weights: distance 30%, skill 40%, trust 20%, availability 10%

## Key Features
- ✅ Explainable AI - every match includes reasoning
- ✅ Adjustable weights - communities can tune matching priorities
- ✅ Bias detection - flag matches that seem systematically unfair
- ✅ Audit trail - researchers can analyze matching patterns

## Implementation

### Database Schema
- `match_explanations` - Detailed score breakdowns for each match
- `matching_weights` - Community-configurable weight settings
- `matching_audit_log` - Complete audit trail of all matching decisions
- `bias_detection_reports` - Automated bias analysis reports
- `transparency_preferences` - User preferences for explanation detail

### Code Changes
- Enhanced `MutualAidMatchmaker` agent with transparency features (app/agents/mutual_aid_matchmaker.py:30)
- Added transparency models (app/models/algorithmic_transparency.py)
- Created transparency repository (app/repositories/transparency_repository.py)
- Implemented bias detection service (app/services/transparency_service.py)
- Added API endpoints (app/api/algorithmic_transparency.py)
- Comprehensive test coverage (tests/test_algorithmic_transparency.py) - 13 tests passing

### API Endpoints
- `GET /transparency/matches/{match_id}/explanation` - Get match explanation
- `GET /transparency/weights` - List weight configurations
- `POST /transparency/weights` - Create custom weights
- `POST /transparency/bias-detection/run` - Run bias analysis
- `GET /transparency/bias-detection/reports` - List bias reports
- `GET /transparency/preferences/{user_id}` - Get user preferences
- `PUT /transparency/preferences/{user_id}` - Update preferences

### Features
- **Three detail levels**: minimal, medium, detailed
- **Configurable weights**: Communities can tune matching priorities (category, location, time, quantity)
- **Bias detection**: Automated analysis for geographic and category bias
- **Audit trail**: All matching decisions logged (including rejections)
- **Privacy-preserving**: Demographic hashes for bias detection without exposing individual data

## Success Metric
>80% of users understand why they were or weren't matched.

## Testing
All 13 tests passing:
- Match explanation creation and formatting
- Weight validation and customization
- Geographic bias detection
- Category bias detection
- Audit logging
- User preferences
