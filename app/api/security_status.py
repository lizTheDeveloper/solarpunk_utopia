"""Security Status API - GAP-66

Plain-language security information for users.
Anti crypto-priesthood: explain, don't mystify.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.models.security_status import (
    SecurityStatus,
    SecurityExplanation,
    SecuritySetting,
    SecurityLevel,
    SECURITY_LEVELS,
    SECURITY_EXPLANATIONS
)

router = APIRouter(prefix="/api/security", tags=["security"])


# ===== Request/Response Models =====

class SetSecurityLevelRequest(BaseModel):
    """Request to set security level."""
    level: str  # "basic", "high", or "maximum"


# ===== Endpoints =====

@router.get("/status")
async def get_security_status(
    user_id: str  # TODO: Get from auth middleware
):
    """Get your current security status in plain English.

    Shows what's protected and what isn't.
    No jargon. No techno-mysticism.
    """
    try:
        # TODO: Get actual user settings from database
        # For now, return example status

        warnings = []

        # Check if user has backup
        has_backup = False  # TODO: Check actual backup status
        if not has_backup:
            warnings.append("No backup: If you lose your phone, you lose access")

        status = SecurityStatus(
            user_id=user_id,
            messages_encrypted=True,
            encryption_algorithm="X25519 + XSalsa20-Poly1305",
            identity_verified=True,
            signature_algorithm="Ed25519",
            has_backup=has_backup,
            backup_method=None,
            security_level="basic",
            warnings=warnings
        )

        return {
            "status": "success",
            "security_status": status.dict(),
            "plain_english": {
                "messages": "✅ Encrypted - only recipients can read",
                "identity": "✅ Verified - signed with your key",
                "backup": "⚠️ Not backed up - save your seed phrase!"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/explain/{feature}")
async def explain_feature(feature: str):
    """Get plain-English explanation of a security feature.

    Available features:
    - encryption
    - signatures
    - mesh_sync
    - web_of_trust

    Returns simple explanation + metaphor + technical details (optional).
    """
    if feature not in SECURITY_EXPLANATIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown feature: {feature}. Try: encryption, signatures, mesh_sync, web_of_trust"
        )

    explanation = SECURITY_EXPLANATIONS[feature]

    return {
        "status": "success",
        "feature": feature,
        "simple": explanation.simple_explanation,
        "metaphor": explanation.metaphor,
        "limitations": explanation.limitations,
        "technical_details": {
            "want_details": "Click to see technical explanation",
            "details": explanation.technical_details
        }
    }


@router.get("/levels")
async def get_security_levels():
    """Get available security levels.

    Basic → High → Maximum

    Each level adds more protection (and more friction).
    Choose what fits your threat model.
    """
    return {
        "status": "success",
        "levels": {
            level: data.dict()
            for level, data in SECURITY_LEVELS.items()
        },
        "current": "basic",  # TODO: Get from user settings
        "note": "Higher levels = more security, more friction. Choose what you need."
    }


@router.post("/set-level")
async def set_security_level(
    request: SetSecurityLevelRequest,
    user_id: str  # TODO: Get from auth middleware
):
    """Set your security level.

    basic: Messages encrypted, identity signed
    high: + PIN lock, auto-lock
    maximum: + Duress PIN, panic wipe, auto-delete
    """
    if request.level not in SECURITY_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level: {request.level}. Choose: basic, high, maximum"
        )

    # TODO: Actually update user settings in database

    level_info = SECURITY_LEVELS[request.level]

    return {
        "status": "success",
        "message": f"Security level set to {request.level}",
        "enabled_features": level_info.features,
        "good_for": level_info.good_for
    }


@router.get("/limitations")
async def get_security_limitations():
    """Get honest list of what we DON'T protect.

    Bakunin: Don't impose authority. Explain honestly.

    We tell you what we can't do.
    """
    return {
        "status": "success",
        "limitations": {
            "stolen_unlocked_phone": {
                "risk": "If someone steals your unlocked phone, they have your keys",
                "mitigation": [
                    "Always lock your phone",
                    "Use duress PIN (opens decoy app)",
                    "Use panic wipe (5 taps on logo)"
                ]
            },
            "shared_password": {
                "risk": "If you share your password, anyone can impersonate you",
                "mitigation": [
                    "Don't share your password",
                    "Don't reuse passwords",
                    "Use seed phrase backup"
                ]
            },
            "metadata": {
                "risk": "Phone carriers can see you're using the app and when",
                "what_we_hide": [
                    "Message content (encrypted)",
                    "Who you're messaging (encrypted)"
                ],
                "what_we_cant_hide": [
                    "That you're using the app",
                    "Approximate message sizes",
                    "Timing"
                ],
                "mitigation": [
                    "Use VPN to hide from carrier",
                    "Use Tor to hide IP",
                    "Meet in person for sensitive talks"
                ]
            },
            "screenshots": {
                "risk": "If you screenshot and share, that's on you",
                "mitigation": [
                    "Don't screenshot sensitive messages",
                    "Don't share sanctuary locations",
                    "Trust who you message"
                ]
            }
        },
        "philosophy": "Security is not magic. It's math. We're honest about limits."
    }


@router.get("/verify")
async def get_verification_info():
    """How to verify our security claims.

    Trust but verify.
    """
    return {
        "status": "success",
        "for_everyone": {
            "open_source": "https://github.com/yourorg/solarpunk-mesh",
            "security_audits": "https://audits.example.com",
            "report_bugs": "security@example.com"
        },
        "for_technical_users": {
            "crypto_specs": "https://docs.example.com/crypto",
            "audit_code": "https://github.com/yourorg/solarpunk-mesh/SECURITY.md",
            "reproducible_builds": "https://docs.example.com/builds",
            "verify_signatures": "https://docs.example.com/verify"
        },
        "for_cryptographers": {
            "threat_model": "https://docs.example.com/threat-model",
            "primitives": [
                "Ed25519 (signatures)",
                "X25519 (key exchange)",
                "XSalsa20-Poly1305 (AEAD)",
                "Argon2id (key derivation)"
            ],
            "key_management": "https://docs.example.com/keys",
            "attack_surface": "https://docs.example.com/security-architecture"
        },
        "bakunin_principle": "Bow to expertise when you choose to. Never when imposed. We explain. You verify if you want."
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "feature": "security-status",
        "gap": "GAP-66",
        "philosophy": "Security explained, not imposed - Bakunin"
    }
