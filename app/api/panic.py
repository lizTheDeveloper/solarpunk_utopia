"""Panic Features API - Duress & Safety Protocols

OPSEC-critical endpoints:
- Configure duress PIN, quick wipe, dead man's switch, decoy mode
- Trigger panic features
- Check burn notice status
- Recover from seed phrase
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.services.panic_service import PanicService
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/api/panic", tags=["panic"])


# ===== Request/Response Models =====

class SetDuressPINRequest(BaseModel):
    """Request to set duress PIN."""
    duress_pin: str = Field(..., description="Duress PIN (4-6 digits)")


class ConfigureQuickWipeRequest(BaseModel):
    """Request to configure quick wipe."""
    enabled: bool = Field(default=True)
    gesture_type: str = Field(default="five_tap_logo", description="Gesture: five_tap_logo, shake_pattern")
    confirmation_required: bool = Field(default=True, description="Require confirmation?")


class TriggerQuickWipeRequest(BaseModel):
    """Request to trigger quick wipe."""
    confirmed: bool = Field(default=False, description="User confirmed?")


class ConfigureDeadMansSwitchRequest(BaseModel):
    """Request to configure dead man's switch."""
    enabled: bool = Field(default=True)
    timeout_hours: int = Field(default=72, description="Hours of inactivity before wipe")


class ConfigureDecoyModeRequest(BaseModel):
    """Request to configure decoy mode."""
    enabled: bool = Field(default=True)
    decoy_type: str = Field(default="calculator", description="Decoy type: calculator, notes, weather")
    secret_gesture: str = Field(default="31337=", description="Secret gesture to reveal real app")


class CreateBurnNoticeRequest(BaseModel):
    """Request to create burn notice."""
    reason: str = Field(..., description="Reason: manual_trigger, suspected_compromise, etc.")


class ResolveBurnNoticeRequest(BaseModel):
    """Request to resolve burn notice."""
    notice_id: str = Field(..., description="Burn notice ID to resolve")


class RecoverFromSeedPhraseRequest(BaseModel):
    """Request to recover from seed phrase."""
    seed_phrase: str = Field(..., description="12-word BIP39 seed phrase")
    password: str = Field(..., description="Password for decrypting local data")


# ===== Dependency Injection =====

def get_panic_service() -> PanicService:
    """Get panic service instance."""
    # TODO: Get from dependency injection container
    return PanicService(db_path="data/solarpunk.db")


# ===== Duress PIN Endpoints =====

@router.post("/duress-pin")
async def set_duress_pin(
    request: SetDuressPINRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Set duress PIN for current user.

    When this PIN is entered, the app will:
    1. Open in decoy mode (showing innocuous content)
    2. Send a burn notice to the network
    3. Not reveal that duress mode is active
    """
    config = service.set_duress_pin(user_id, request.duress_pin)
    return {
        "success": True,
        "message": "Duress PIN set successfully",
        "config": {
            "enabled": config.enabled,
            "created_at": config.created_at.isoformat()
        }
    }


@router.post("/duress-pin/verify")
async def verify_duress_pin(
    pin: str,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Check if a PIN is the duress PIN.

    CRITICAL: This endpoint should be called during authentication.
    If it returns true, activate decoy mode and send burn notice.
    """
    is_duress = service.verify_duress_pin(user_id, pin)
    return {
        "is_duress": is_duress,
        "action": "activate_decoy_mode" if is_duress else None
    }


# ===== Quick Wipe Endpoints =====

@router.post("/quick-wipe/configure")
async def configure_quick_wipe(
    request: ConfigureQuickWipeRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Configure quick wipe settings."""
    config = service.configure_quick_wipe(
        user_id,
        request.enabled,
        request.gesture_type,
        request.confirmation_required
    )
    return {
        "success": True,
        "config": {
            "enabled": config.enabled,
            "gesture_type": config.gesture_type,
            "confirmation_required": config.confirmation_required
        }
    }


@router.post("/quick-wipe/trigger")
async def trigger_quick_wipe(
    request: TriggerQuickWipeRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Trigger quick wipe.

    CRITICAL: This destroys all sensitive data in <3 seconds.
    Cannot be undone (except via seed phrase recovery).
    """
    try:
        wipe_log = service.trigger_quick_wipe(user_id, request.confirmed)
        return {
            "success": True,
            "message": "Data wiped successfully",
            "wiped": wipe_log.data_types_wiped,
            "recovery_possible": wipe_log.recovery_possible
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Dead Man's Switch Endpoints =====

@router.post("/dead-mans-switch/configure")
async def configure_dead_mans_switch(
    request: ConfigureDeadMansSwitchRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Configure dead man's switch.

    If user doesn't check in within timeout_hours, data is auto-wiped.
    """
    config = service.configure_dead_mans_switch(
        user_id,
        request.enabled,
        request.timeout_hours
    )
    return {
        "success": True,
        "config": {
            "enabled": config.enabled,
            "timeout_hours": config.timeout_hours,
            "trigger_time": config.calculate_trigger_time().isoformat()
        }
    }


@router.post("/dead-mans-switch/checkin")
async def checkin(
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """User checks in, resetting dead man's switch timer.

    This should be called every time the app is opened.
    """
    service.checkin(user_id)
    return {
        "success": True,
        "message": "Checked in successfully"
    }


# ===== Decoy Mode Endpoints =====

@router.post("/decoy-mode/configure")
async def configure_decoy_mode(
    request: ConfigureDecoyModeRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Configure decoy mode.

    When active, app appears as calculator/notes/weather app.
    Secret gesture reveals real app.
    """
    config = service.configure_decoy_mode(
        user_id,
        request.enabled,
        request.decoy_type,
        request.secret_gesture
    )
    return {
        "success": True,
        "config": {
            "enabled": config.enabled,
            "decoy_type": config.decoy_type,
            "secret_gesture": config.secret_gesture
        }
    }


@router.get("/decoy-mode/config")
async def get_decoy_config(
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Get decoy mode configuration."""
    config = service.get_decoy_config(user_id)
    if not config:
        return {"enabled": False}

    return {
        "enabled": config.enabled,
        "decoy_type": config.decoy_type,
        "secret_gesture": config.secret_gesture,
        "currently_in_decoy": config.currently_in_decoy
    }


# ===== Burn Notice Endpoints =====

@router.post("/burn-notice")
async def create_burn_notice(
    request: CreateBurnNoticeRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Create a burn notice - signal that you may be compromised.

    This will:
    - Suspend your trust score
    - Hold pending messages
    - Flag your recent vouches
    - Notify your vouch chain
    """
    notice = service.create_burn_notice(user_id, request.reason)
    return {
        "success": True,
        "notice": {
            "id": notice.id,
            "status": notice.status.value,
            "created_at": notice.created_at.isoformat()
        }
    }


@router.post("/burn-notice/resolve")
async def resolve_burn_notice(
    request: ResolveBurnNoticeRequest,
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Resolve a burn notice - confirm you're safe.

    This restores your trust score and clears the burn notice.
    Sends "all clear" message to network.
    Requires re-authentication.
    """
    success = await service.resolve_burn_notice(user_id, request.notice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Burn notice not found")

    return {
        "success": True,
        "message": "Burn notice resolved, trust restored, all clear sent to network"
    }


# ===== Recovery Endpoints =====

@router.post("/seed-phrase/generate")
async def generate_seed_phrase(
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Generate a new seed phrase for identity recovery.

    CRITICAL: User must write this down and store securely.
    This is the ONLY way to recover after a wipe.
    """
    seed_phrase = service.generate_seed_phrase()
    return {
        "seed_phrase": seed_phrase,
        "warning": "Write this down and store securely. This is the ONLY way to recover after a wipe."
    }


@router.post("/seed-phrase/recover")
async def recover_from_seed_phrase(
    request: RecoverFromSeedPhraseRequest,
    service: PanicService = Depends(get_panic_service)
):
    """Recover identity from seed phrase after wipe.

    This regenerates Ed25519 keys and restores identity.
    User still needs to re-authenticate with vouch chain.
    """
    keys = service.recover_from_seed_phrase(request.seed_phrase)
    return {
        "success": True,
        "public_key": keys["public_key"],
        "message": "Identity recovered. Re-authenticate with vouch chain to restore trust."
    }


# ===== Status Endpoints =====

@router.get("/status")
async def get_panic_status(
    user_id: str = Depends(get_current_user),
    service: PanicService = Depends(get_panic_service)
):
    """Get status of all panic features for current user."""
    status = service.get_panic_status(user_id)

    # Convert configs to serializable format
    def serialize_config(config):
        if config is None:
            return None
        return {
            "user_id": config.user_id,
            "enabled": getattr(config, 'enabled', False),
            "created_at": config.created_at.isoformat() if hasattr(config, 'created_at') else None
        }

    return {
        "duress_pin": {
            "enabled": status["duress_pin"]["enabled"],
            "config": serialize_config(status["duress_pin"]["config"])
        },
        "quick_wipe": {
            "enabled": status["quick_wipe"]["enabled"],
            "config": serialize_config(status["quick_wipe"]["config"])
        },
        "dead_mans_switch": {
            "enabled": status["dead_mans_switch"]["enabled"],
            "config": serialize_config(status["dead_mans_switch"]["config"]),
            "time_remaining": str(status["dead_mans_switch"]["time_remaining"]) if status["dead_mans_switch"]["time_remaining"] else None
        },
        "decoy_mode": {
            "enabled": status["decoy_mode"]["enabled"],
            "config": serialize_config(status["decoy_mode"]["config"])
        },
        "burn_notices": {
            "active_count": len(status["burn_notices"]["active"]),
            "notices": [
                {
                    "id": n.id,
                    "reason": n.reason,
                    "status": n.status.value,
                    "created_at": n.created_at.isoformat()
                }
                for n in status["burn_notices"]["active"]
            ]
        },
        "wipe_history": [
            {
                "id": log.id,
                "trigger": log.trigger,
                "wiped_at": log.wiped_at.isoformat(),
                "data_types_wiped": log.data_types_wiped,
                "recovery_possible": log.recovery_possible
            }
            for log in status["wipe_history"]
        ]
    }
