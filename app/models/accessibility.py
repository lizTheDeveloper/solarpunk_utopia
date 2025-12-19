"""
Accessibility First Models

"Disability justice means designing for the most marginalized first." - Mia Mingus

ONE version that works for all, not a separate "accessible version".
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class FontSize(str, Enum):
    """Font size preference"""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class ReadingLevel(str, Enum):
    """Reading level preference"""

    SIMPLE = "simple"  # Plain language
    STANDARD = "standard"  # Normal
    TECHNICAL = "technical"  # Expert terms OK


class FeatureName(str, Enum):
    """Accessibility feature names"""

    SCREEN_READER = "screen_reader"
    VOICE_CONTROL = "voice_control"
    HIGH_CONTRAST = "high_contrast"
    LARGE_FONT = "large_font"
    SIMPLE_LANGUAGE = "simple_language"


class AuditType(str, Enum):
    """Type of accessibility audit"""

    SCREEN_READER = "screen_reader"
    KEYBOARD = "keyboard"
    CONTRAST = "contrast"
    TOUCH_TARGET = "touch_target"
    LANGUAGE = "language"


class IssueType(str, Enum):
    """Type of accessibility issue"""

    SCREEN_READER_ISSUE = "screen_reader_issue"
    TOUCH_TARGET_TOO_SMALL = "touch_target_too_small"
    LANGUAGE_TOO_COMPLEX = "language_too_complex"
    CONTRAST_TOO_LOW = "contrast_too_low"
    VOICE_CONTROL_BROKEN = "voice_control_broken"


class Severity(str, Enum):
    """Issue severity"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    """Status of accessibility issue"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


@dataclass
class AccessibilityPreferences:
    """User accessibility preferences"""

    uses_screen_reader: bool
    uses_voice_control: bool
    uses_high_contrast: bool
    preferred_font_size: FontSize
    reading_level_preference: ReadingLevel
    accessibility_mode_enabled: bool
    custom_preferences: Optional[Dict[str, Any]]  # JSON


@dataclass
class AccessibilityFeatureUsage:
    """Tracks usage of accessibility features"""

    id: str
    user_id: str
    feature_name: FeatureName
    first_used_at: datetime
    last_used_at: datetime
    usage_count: int
    platform: Optional[str]  # 'android', 'web', 'ios'
    device_info: Optional[Dict[str, Any]]  # JSON
    created_at: datetime


@dataclass
class AccessibilityAuditLog:
    """Log of accessibility audits"""

    id: str
    component_name: str
    component_type: str  # 'page', 'component', 'flow', 'api'
    audit_type: AuditType
    passed: bool
    issues_found: Optional[List[Dict[str, Any]]]  # JSON
    audited_by: Optional[str]  # User ID or 'automated'
    audit_tool: str  # 'manual', 'axe', 'lighthouse', 'nvda', 'talkback'
    resolved: bool
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    audited_at: datetime


@dataclass
class AccessibilityFeedback:
    """User-reported accessibility issues"""

    id: str
    user_id: str
    issue_type: IssueType
    component_affected: str
    description: str
    severity: Severity
    blocks_usage: bool  # Does this prevent them from using the feature?
    accessibility_features_used: Optional[List[str]]  # JSON
    device_info: Optional[Dict[str, Any]]  # JSON
    status: IssueStatus
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    reported_at: datetime


@dataclass
class UIComponentMetadata:
    """Metadata about UI component accessibility compliance"""

    id: str
    component_name: str
    component_path: str
    component_type: str  # 'page', 'button', 'form', 'list', 'modal'
    meets_touch_target_size: bool  # 48x48px minimum
    has_aria_labels: bool
    has_keyboard_navigation: bool
    has_high_contrast_support: bool
    reading_level: Optional[str]
    last_tested_at: Optional[datetime]
    last_tested_by: Optional[str]
    test_results: Optional[Dict[str, Any]]  # JSON
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class AccessibilityMetrics:
    """Metrics for accessibility success tracking"""

    id: str
    period_start: datetime
    period_end: datetime

    # User metrics
    total_active_users: int
    users_with_accessibility_features: int

    # Feature usage breakdown
    screen_reader_users: int
    voice_control_users: int
    high_contrast_users: int
    large_font_users: int

    # Compliance metrics
    components_audited: int
    components_passing: int
    open_accessibility_issues: int
    critical_issues: int

    # Success metric: >10% using accessibility features
    accessibility_feature_usage_percentage: float

    # Metadata
    calculated_at: datetime


@dataclass
class SimplifiedLanguageAlternative:
    """Plain language alternative for complex text"""

    id: str
    original_text: str
    original_text_hash: str
    context: Optional[str]
    simplified_text: str
    reading_level: str
    verified_by: Optional[str]
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class VoiceCommandMapping:
    """Mapping of voice commands to actions"""

    id: str
    voice_command: str
    alternative_phrases: Optional[List[str]]  # JSON
    action_type: str  # 'navigate', 'create', 'search', 'update'
    action_target: str
    requires_confirmation: bool
    feedback_text: Optional[str]
    usage_count: int
    success_rate: float
    created_at: datetime
    enabled: bool


@dataclass
class TouchTargetViolation:
    """UI element that doesn't meet touch target size requirements"""

    id: str
    component_name: str
    component_path: str
    current_size_px: str  # e.g., "32x32"
    required_size_px: str  # "48x48"
    detected_by: str  # 'automated_scan', 'user_report', 'manual_audit'
    detected_at: datetime
    status: str  # 'open', 'fixed', 'wont_fix', 'design_exception'
    fixed_at: Optional[datetime]
    fix_notes: Optional[str]
