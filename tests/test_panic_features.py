"""Tests for Panic Features - Duress & Safety Protocols

Tests:
- Duress PIN detection and burn notice creation
- Quick wipe data destruction
- Dead man's switch timeout and auto-wipe
- Decoy mode configuration
- Seed phrase generation and recovery
"""
import os
import tempfile
import pytest
from datetime import datetime, timedelta

from app.models.panic import BurnNoticeStatus
from app.services.panic_service import PanicService


@pytest.fixture
def panic_service():
    """Create panic service with temporary database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    service = PanicService(db_path=db_path)
    yield service

    # Cleanup
    os.unlink(db_path)


def test_duress_pin_set_and_verify(panic_service):
    """Test setting and verifying duress PIN."""
    user_id = "test-user-123"
    duress_pin = "1234"

    # Set duress PIN
    config = panic_service.set_duress_pin(user_id, duress_pin)
    assert config.enabled is True
    assert config.user_id == user_id

    # Verify correct PIN
    is_duress = panic_service.verify_duress_pin(user_id, duress_pin)
    assert is_duress is True

    # Verify incorrect PIN
    is_duress = panic_service.verify_duress_pin(user_id, "5678")
    assert is_duress is False


def test_duress_pin_creates_burn_notice(panic_service):
    """Test that duress PIN triggers burn notice."""
    user_id = "test-user-456"
    duress_pin = "9999"

    # Set duress PIN
    panic_service.set_duress_pin(user_id, duress_pin)

    # Verify duress PIN (should create burn notice)
    panic_service.verify_duress_pin(user_id, duress_pin)

    # Check that burn notice was created
    notices = panic_service.repo.get_burn_notices_for_user(user_id)
    assert len(notices) == 1
    assert notices[0].reason == "duress_pin_entered"
    assert notices[0].status == BurnNoticeStatus.PENDING


def test_quick_wipe_configuration(panic_service):
    """Test quick wipe configuration."""
    user_id = "test-user-789"

    # Configure quick wipe
    config = panic_service.configure_quick_wipe(
        user_id,
        enabled=True,
        gesture_type="shake_pattern",
        confirmation_required=False
    )

    assert config.enabled is True
    assert config.gesture_type == "shake_pattern"
    assert config.confirmation_required is False


def test_quick_wipe_requires_confirmation(panic_service):
    """Test that quick wipe respects confirmation requirement."""
    user_id = "test-user-101"

    # Configure quick wipe with confirmation required
    panic_service.configure_quick_wipe(
        user_id,
        enabled=True,
        confirmation_required=True
    )

    # Try to trigger without confirmation - should fail
    with pytest.raises(ValueError, match="confirmation required"):
        panic_service.trigger_quick_wipe(user_id, confirmed=False)


def test_quick_wipe_destroys_data(panic_service):
    """Test that quick wipe actually destroys data."""
    user_id = "test-user-102"

    # Configure quick wipe without confirmation
    panic_service.configure_quick_wipe(
        user_id,
        enabled=True,
        confirmation_required=False
    )

    # Trigger quick wipe
    wipe_log = panic_service.trigger_quick_wipe(user_id, confirmed=True)

    assert wipe_log.trigger == "quick_wipe"
    assert wipe_log.user_id == user_id
    assert wipe_log.recovery_possible is True
    assert len(wipe_log.data_types_wiped) > 0


def test_dead_mans_switch_configuration(panic_service):
    """Test dead man's switch configuration."""
    user_id = "test-user-103"

    # Configure dead man's switch
    config = panic_service.configure_dead_mans_switch(
        user_id,
        enabled=True,
        timeout_hours=48
    )

    assert config.enabled is True
    assert config.timeout_hours == 48
    assert config.triggered is False

    # Check trigger time is calculated correctly
    expected_trigger = datetime.utcnow() + timedelta(hours=48)
    trigger_time = config.calculate_trigger_time()
    # Allow 1 second difference
    assert abs((trigger_time - expected_trigger).total_seconds()) < 1


def test_dead_mans_switch_checkin(panic_service):
    """Test dead man's switch check-in resets timer."""
    user_id = "test-user-104"

    # Configure with short timeout for testing
    config = panic_service.configure_dead_mans_switch(
        user_id,
        enabled=True,
        timeout_hours=1
    )

    original_trigger = config.calculate_trigger_time()

    # Wait a moment
    import time
    time.sleep(0.1)

    # Check in
    panic_service.checkin(user_id)

    # Get updated config
    updated_config = panic_service.repo.get_dead_mans_switch(user_id)
    new_trigger = updated_config.calculate_trigger_time()

    # New trigger time should be later than original
    assert new_trigger > original_trigger


def test_decoy_mode_configuration(panic_service):
    """Test decoy mode configuration."""
    user_id = "test-user-105"

    # Configure decoy mode
    config = panic_service.configure_decoy_mode(
        user_id,
        enabled=True,
        decoy_type="notes",
        secret_gesture="secret123"
    )

    assert config.enabled is True
    assert config.decoy_type == "notes"
    assert config.secret_gesture == "secret123"


def test_burn_notice_creation(panic_service):
    """Test burn notice creation and propagation."""
    user_id = "test-user-106"

    # Create burn notice
    notice = panic_service.create_burn_notice(user_id, "manual_trigger")

    assert notice.user_id == user_id
    assert notice.reason == "manual_trigger"
    assert notice.status == BurnNoticeStatus.PENDING
    assert notice.vouch_chain_notified is False


def test_burn_notice_resolution(panic_service):
    """Test burn notice resolution."""
    user_id = "test-user-107"

    # Create burn notice
    notice = panic_service.create_burn_notice(user_id, "manual_trigger")

    # Resolve it
    success = panic_service.resolve_burn_notice(user_id, notice.id)
    assert success is True

    # Check status
    resolved_notice = panic_service.repo.get_burn_notice(notice.id)
    assert resolved_notice.status == BurnNoticeStatus.RESOLVED
    assert resolved_notice.resolved_at is not None


def test_seed_phrase_generation(panic_service):
    """Test seed phrase generation."""
    seed_phrase = panic_service.generate_seed_phrase()

    # Should be 12 words
    words = seed_phrase.split()
    assert len(words) == 12

    # All words should be strings
    for word in words:
        assert isinstance(word, str)
        assert len(word) > 0


def test_seed_phrase_encryption_decryption(panic_service):
    """Test seed phrase encryption and decryption."""
    seed_phrase = "test seed phrase with twelve words here now okay good fine"
    password = "secure_password_123"

    # Encrypt
    encrypted = panic_service.encrypt_seed_phrase(seed_phrase, password)
    assert encrypted != seed_phrase

    # Decrypt
    decrypted = panic_service.decrypt_seed_phrase(encrypted, password)
    assert decrypted == seed_phrase


def test_panic_status_aggregation(panic_service):
    """Test getting all panic status for a user."""
    user_id = "test-user-108"

    # Configure all features
    panic_service.set_duress_pin(user_id, "1234")
    panic_service.configure_quick_wipe(user_id, enabled=True)
    panic_service.configure_dead_mans_switch(user_id, enabled=True)
    panic_service.configure_decoy_mode(user_id, enabled=True)

    # Get status
    status = panic_service.get_panic_status(user_id)

    assert status["duress_pin"]["enabled"] is True
    assert status["quick_wipe"]["enabled"] is True
    assert status["dead_mans_switch"]["enabled"] is True
    assert status["decoy_mode"]["enabled"] is True
    assert isinstance(status["burn_notices"]["active"], list)
    assert isinstance(status["wipe_history"], list)


def test_overdue_dead_mans_switches(panic_service):
    """Test detection and triggering of overdue dead man's switches."""
    user_id = "test-user-109"

    # Configure with very short timeout
    config = panic_service.configure_dead_mans_switch(
        user_id,
        enabled=True,
        timeout_hours=1
    )

    # Manually set last_checkin to past to simulate timeout
    import sqlite3
    conn = sqlite3.connect(panic_service.db_path)
    cursor = conn.cursor()

    past_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    trigger_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    cursor.execute("""
        UPDATE dead_mans_switch_configs
        SET last_checkin = ?, trigger_time = ?
        WHERE user_id = ?
    """, (past_time, trigger_time, user_id))

    conn.commit()
    conn.close()

    # Check for overdue switches
    overdue = panic_service.repo.get_overdue_dead_mans_switches()
    assert len(overdue) == 1
    assert overdue[0].user_id == user_id

    # Trigger overdue switches
    results = panic_service.check_overdue_switches()
    assert len(results) == 1
    assert results[0][0] == user_id  # user_id
    assert results[0][1].trigger == "dead_mans_switch"  # wipe_log


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
