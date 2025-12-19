#!/usr/bin/env python3
"""Basic test for panic features - no pytest required"""
import os
import tempfile
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.panic_service import PanicService


def test_basic_panic_features():
    """Test basic panic features functionality."""
    print("Testing Panic Features...")
    print("=" * 60)

    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    try:
        service = PanicService(db_path=db_path)

        # Test 1: Duress PIN
        print("\n1. Testing Duress PIN...")
        user_id = "test-user-1"
        duress_pin = "1234"

        config = service.set_duress_pin(user_id, duress_pin)
        assert config.enabled is True, "Duress PIN should be enabled"
        print("   ✓ Duress PIN set successfully")

        is_duress = service.verify_duress_pin(user_id, duress_pin)
        assert is_duress is True, "Should verify correct duress PIN"
        print("   ✓ Duress PIN verified")

        is_duress = service.verify_duress_pin(user_id, "wrong")
        assert is_duress is False, "Should reject wrong PIN"
        print("   ✓ Wrong PIN rejected")

        # Test 2: Quick Wipe
        print("\n2. Testing Quick Wipe...")
        config = service.configure_quick_wipe(user_id, enabled=True, confirmation_required=False)
        assert config.enabled is True, "Quick wipe should be enabled"
        print("   ✓ Quick wipe configured")

        wipe_log = service.trigger_quick_wipe(user_id, confirmed=True)
        assert wipe_log.trigger == "quick_wipe", "Wipe log should show correct trigger"
        assert len(wipe_log.data_types_wiped) > 0, "Should have wiped some data types"
        print(f"   ✓ Quick wipe triggered, wiped: {', '.join(wipe_log.data_types_wiped)}")

        # Test 3: Dead Man's Switch
        print("\n3. Testing Dead Man's Switch...")
        user_id_2 = "test-user-2"
        config = service.configure_dead_mans_switch(user_id_2, enabled=True, timeout_hours=72)
        assert config.enabled is True, "Dead man's switch should be enabled"
        assert config.timeout_hours == 72, "Timeout should be 72 hours"
        print("   ✓ Dead man's switch configured")

        service.checkin(user_id_2)
        print("   ✓ Check-in successful")

        # Test 4: Decoy Mode
        print("\n4. Testing Decoy Mode...")
        user_id_3 = "test-user-3"
        config = service.configure_decoy_mode(user_id_3, enabled=True, decoy_type="calculator")
        assert config.enabled is True, "Decoy mode should be enabled"
        assert config.decoy_type == "calculator", "Decoy type should be calculator"
        print("   ✓ Decoy mode configured")

        # Test 5: Burn Notice
        print("\n5. Testing Burn Notice...")
        user_id_4 = "test-user-4"
        notice = service.create_burn_notice(user_id_4, "manual_trigger")
        assert notice.user_id == user_id_4, "Burn notice should be for correct user"
        assert notice.reason == "manual_trigger", "Burn notice should have correct reason"
        print(f"   ✓ Burn notice created: {notice.id}")

        success = service.resolve_burn_notice(user_id_4, notice.id)
        assert success is True, "Should resolve burn notice"
        print("   ✓ Burn notice resolved")

        # Test 6: Seed Phrase
        print("\n6. Testing Seed Phrase...")
        seed_phrase = service.generate_seed_phrase()
        words = seed_phrase.split()
        assert len(words) == 12, "Seed phrase should have 12 words"
        print(f"   ✓ Seed phrase generated: {seed_phrase[:30]}...")

        encrypted = service.encrypt_seed_phrase(seed_phrase, "password")
        assert encrypted != seed_phrase, "Seed phrase should be encrypted"
        print("   ✓ Seed phrase encrypted")

        decrypted = service.decrypt_seed_phrase(encrypted, "password")
        assert decrypted == seed_phrase, "Seed phrase should decrypt correctly"
        print("   ✓ Seed phrase decrypted")

        # Test 7: Status Aggregation
        print("\n7. Testing Status Aggregation...")
        user_id_5 = "test-user-5"
        service.set_duress_pin(user_id_5, "5678")
        service.configure_quick_wipe(user_id_5, enabled=True)
        service.configure_dead_mans_switch(user_id_5, enabled=True)
        service.configure_decoy_mode(user_id_5, enabled=True)

        status = service.get_panic_status(user_id_5)
        assert status["duress_pin"]["enabled"] is True, "Duress PIN should be in status"
        assert status["quick_wipe"]["enabled"] is True, "Quick wipe should be in status"
        assert status["dead_mans_switch"]["enabled"] is True, "Dead man's switch should be in status"
        assert status["decoy_mode"]["enabled"] is True, "Decoy mode should be in status"
        print("   ✓ Status aggregation working")

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    try:
        test_basic_panic_features()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
