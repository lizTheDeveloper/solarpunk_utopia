"""
Test Group Formation Protocol

Tests fractal group formation with physical key exchange.
"""

import pytest
from nacl.public import PrivateKey
from nacl.encoding import Base64Encoder
from app.services.group_formation_service import GroupFormationService


@pytest.fixture
def service():
    """Create service instance"""
    return GroupFormationService()


@pytest.fixture
def founder_keys():
    """Generate test founder keys (3 members for minimum)"""
    keys = []
    for i in range(3):
        private_key = PrivateKey.generate()
        keys.append({
            "user_id": f"user_{i}",
            "public_key": private_key.public_key.encode(),
            "private_key": private_key.encode()
        })
    return keys


def test_service_initialization(service):
    """Test service initializes correctly"""
    assert service is not None
    assert service.min_group_size == 3


def test_generate_group_key(service):
    """Test group key generation"""
    key = service.generate_group_key()
    assert len(key) == 32  # 256 bits
    assert isinstance(key, bytes)


def test_create_initial_group_success(service, founder_keys):
    """Test successful group creation with minimum members"""
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Test Commune"
    )

    assert group["id"] is not None
    assert group["name"] == "Test Commune"
    assert group["member_count"] == 3
    assert group["formation_method"] == "physical_key_exchange"
    assert "shared_key" in group
    assert group["nesting_level"] == 0
    assert "resources" in group
    assert "inventory_id" in group["resources"]
    assert "chat_channel_id" in group["resources"]
    assert "governance_scope_id" in group["resources"]


def test_create_initial_group_too_few_members(service):
    """Test group creation fails with fewer than minimum members"""
    insufficient_keys = [
        {"user_id": "user_1", "public_key": b"key1"},
        {"user_id": "user_2", "public_key": b"key2"}
    ]

    with pytest.raises(ValueError) as exc_info:
        service.create_initial_group(
            founder_keys=insufficient_keys,
            group_name="Invalid Commune"
        )

    assert "at least 3 founding members" in str(exc_info.value).lower()


def test_create_invitation(service, founder_keys):
    """Test encrypted invitation creation"""
    # Create a group first
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Test Group"
    )

    # Create invitation
    inviter = founder_keys[0]
    invitee_private_key = PrivateKey.generate()
    invitee_public_key = invitee_private_key.public_key.encode()

    group_key_bytes = Base64Encoder.decode(group["shared_key"].encode('utf-8'))

    invitation = service.create_formation_invitation(
        group_id=group["id"],
        inviter_user_id=inviter["user_id"],
        inviter_private_key=inviter["private_key"],
        invitee_public_key=invitee_public_key,
        group_shared_key=group_key_bytes
    )

    assert invitation["group_id"] == group["id"]
    assert invitation["inviter_user_id"] == inviter["user_id"]
    assert "encrypted_group_key" in invitation
    assert invitation["invitation_type"] == "group_formation"


def test_accept_invitation(service, founder_keys):
    """Test accepting invitation and decrypting group key"""
    # Create group
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Test Group"
    )

    # Create invitation
    inviter = founder_keys[0]
    invitee_private_key = PrivateKey.generate()
    invitee_public_key = invitee_private_key.public_key.encode()

    group_key_bytes = Base64Encoder.decode(group["shared_key"].encode('utf-8'))

    invitation = service.create_formation_invitation(
        group_id=group["id"],
        inviter_user_id=inviter["user_id"],
        inviter_private_key=inviter["private_key"],
        invitee_public_key=invitee_public_key,
        group_shared_key=group_key_bytes
    )

    # Accept invitation
    inviter_public_key = PrivateKey(inviter["private_key"]).public_key.encode()

    decrypted_key = service.accept_invitation(
        invitation=invitation,
        invitee_user_id="new_user",
        invitee_private_key=invitee_private_key.encode(),
        inviter_public_key=inviter_public_key
    )

    # Decrypted key should match original
    assert decrypted_key == group_key_bytes


def test_qr_formation_flow(service, founder_keys):
    """Test QR code formation and joining"""
    # Create group
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="QR Test Group"
    )

    group_key_bytes = Base64Encoder.decode(group["shared_key"].encode('utf-8'))

    # Generate QR token
    qr_token, otp = service.generate_qr_formation_token(
        group_id=group["id"],
        inviter_user_id=founder_keys[0]["user_id"],
        group_shared_key=group_key_bytes,
        expiry_minutes=30
    )

    assert qr_token is not None
    assert len(otp) == 6  # 6-digit OTP
    assert otp.isdigit()

    # Join via QR
    decrypted_key = service.scan_qr_and_join(
        qr_token=qr_token,
        otp=otp,
        joiner_user_id="qr_joiner"
    )

    # Should decrypt to same key
    assert decrypted_key == group_key_bytes


def test_qr_invalid_otp(service, founder_keys):
    """Test QR join fails with invalid OTP"""
    # Create group and QR token
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="QR Test Group"
    )

    group_key_bytes = Base64Encoder.decode(group["shared_key"].encode('utf-8'))

    qr_token, otp = service.generate_qr_formation_token(
        group_id=group["id"],
        inviter_user_id=founder_keys[0]["user_id"],
        group_shared_key=group_key_bytes,
        expiry_minutes=30
    )

    # Try to join with wrong OTP
    with pytest.raises(ValueError):
        service.scan_qr_and_join(
            qr_token=qr_token,
            otp="999999",  # Wrong OTP
            joiner_user_id="qr_joiner"
        )


def test_create_nested_group(service, founder_keys):
    """Test creating nested subgroup"""
    # Create parent group
    parent_group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Parent Commune"
    )

    # Create nested subgroup
    subgroup_founders = founder_keys[:3]
    parent_key_bytes = Base64Encoder.decode(parent_group["shared_key"].encode('utf-8'))

    subgroup = service.create_nested_group(
        parent_group_id=parent_group["id"],
        parent_group_key=parent_key_bytes,
        founder_keys=subgroup_founders,
        subgroup_name="Garden Squad"
    )

    assert subgroup["parent_group_id"] == parent_group["id"]
    assert subgroup["name"] == "Garden Squad"
    assert subgroup["nesting_level"] == 1  # One level deep
    assert subgroup["metadata"]["subsidiarity_enforced"] is True


def test_merge_groups(service, founder_keys):
    """Test merging two groups (fusion)"""
    # Create two groups
    group_a = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Group A"
    )

    group_b_founders = [
        {"user_id": f"user_b_{i}", "public_key": PrivateKey.generate().public_key.encode()}
        for i in range(3)
    ]
    group_b = service.create_initial_group(
        founder_keys=group_b_founders,
        group_name="Group B"
    )

    # Merge them
    group_a_key = Base64Encoder.decode(group_a["shared_key"].encode('utf-8'))
    group_b_key = Base64Encoder.decode(group_b["shared_key"].encode('utf-8'))

    merged = service.merge_groups(
        group_a_id=group_a["id"],
        group_a_key=group_a_key,
        group_b_id=group_b["id"],
        group_b_key=group_b_key,
        merged_name="Merged Federation"
    )

    assert merged["name"] == "Merged Federation"
    assert merged["formation_method"] == "group_fusion"
    assert group_a["id"] in merged["parent_groups"]
    assert group_b["id"] in merged["parent_groups"]
    assert merged["status"] == "pending_consensus"


def test_split_group(service, founder_keys):
    """Test splitting a group (fission)"""
    # Create group with 6 members
    six_members = [
        {"user_id": f"user_{i}", "public_key": PrivateKey.generate().public_key.encode()}
        for i in range(6)
    ]

    original_group = service.create_initial_group(
        founder_keys=six_members,
        group_name="Original Commune"
    )

    # Split: 3 members leave
    departing_ids = [m["user_id"] for m in six_members[:3]]
    group_key_bytes = Base64Encoder.decode(original_group["shared_key"].encode('utf-8'))

    split_result = service.split_group(
        original_group_id=original_group["id"],
        original_group_key=group_key_bytes,
        departing_member_ids=departing_ids,
        new_group_name="Breakaway Commune",
        secession_reason="Philosophical differences"
    )

    assert "new_group" in split_result
    assert split_result["new_group"]["name"] == "Breakaway Commune"
    assert split_result["new_group"]["formation_method"] == "group_fission"
    assert len(split_result["new_group"]["founding_members"]) == 3
    assert "original_group_new_key" in split_result  # Key rotated for security


def test_split_group_too_few_departing(service, founder_keys):
    """Test split fails if departing members < minimum"""
    group = service.create_initial_group(
        founder_keys=founder_keys,
        group_name="Test Group"
    )

    group_key_bytes = Base64Encoder.decode(group["shared_key"].encode('utf-8'))

    # Try to split with only 2 departing members (< minimum 3)
    with pytest.raises(ValueError) as exc_info:
        service.split_group(
            original_group_id=group["id"],
            original_group_key=group_key_bytes,
            departing_member_ids=["user_1", "user_2"],
            new_group_name="Invalid Split"
        )

    assert "min 3 members" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
