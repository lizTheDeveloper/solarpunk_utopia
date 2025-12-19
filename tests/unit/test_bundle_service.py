"""
Unit Tests for DTN Bundle Service

Tests bundle creation, validation, signing, and content-addressing.
"""

import pytest
from datetime import datetime, timedelta, timezone
import asyncio

from app.models.bundle import Bundle, BundleCreate
from app.models.priority import Priority, Audience, Topic, ReceiptPolicy
from app.services.bundle_service import BundleService
from app.services.crypto_service import CryptoService


@pytest.fixture
def crypto_service():
    """Create a crypto service with temporary keys"""
    import tempfile
    from pathlib import Path
    temp_dir = Path(tempfile.mkdtemp())
    service = CryptoService(keys_dir=temp_dir)
    yield service
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def bundle_service(crypto_service):
    """Create a bundle service"""
    return BundleService(crypto_service)


class TestBundleCreation:
    """Test bundle creation and signing"""

    @pytest.mark.asyncio
    async def test_create_simple_bundle(self, bundle_service):
        """Should create and sign a simple bundle"""
        bundle_create = BundleCreate(
            payload={"message": "Hello, world!"},
            payloadType="text/plain",
            topic=Topic.COORDINATION,
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC
        )

        bundle = await bundle_service.create_bundle(bundle_create)

        assert bundle.bundleId.startswith("b:sha256:")
        assert bundle.payload == {"message": "Hello, world!"}
        assert bundle.payloadType == "text/plain"
        assert bundle.signature
        assert len(bundle.signature) == 88  # Base64 encoded Ed25519 signature
        assert bundle.authorPublicKey
        assert bundle.hopCount == 0
        assert bundle.priority == Priority.NORMAL

    @pytest.mark.asyncio
    async def test_create_bundle_with_ttl_hours(self, bundle_service):
        """Should create bundle with ttl_hours parameter"""
        bundle_create = BundleCreate(
            payload={"data": "test"},
            payload_type="application/json",  # Snake_case variant
            topic=Topic.MUTUAL_AID,
            ttl_hours=48
        )

        bundle = await bundle_service.create_bundle(bundle_create)

        assert bundle.bundleId.startswith("b:sha256:")
        assert bundle.payloadType == "application/json"
        # Should expire in approximately 48 hours
        hours_until_expiry = (bundle.expiresAt - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 47.9 < hours_until_expiry < 48.1

    @pytest.mark.asyncio
    async def test_create_bundle_auto_ttl(self, bundle_service):
        """Should auto-calculate TTL based on priority and topic"""
        bundle_create = BundleCreate(
            payload={"emergency": "help needed"},
            payloadType="emergency/alert",
            topic=Topic.COORDINATION,
            priority=Priority.EMERGENCY
        )

        bundle = await bundle_service.create_bundle(bundle_create)

        # Emergency priority should have 12 hour TTL
        hours_until_expiry = (bundle.expiresAt - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 11.9 < hours_until_expiry < 12.1

    @pytest.mark.asyncio
    async def test_create_bundle_with_tags(self, bundle_service):
        """Should create bundle with tags"""
        bundle_create = BundleCreate(
            payload={"resource": "tomatoes"},
            payloadType="vf:Listing",
            topic=Topic.MUTUAL_AID,
            tags=["food", "perishable", "organic"]
        )

        bundle = await bundle_service.create_bundle(bundle_create)

        assert bundle.tags == ["food", "perishable", "organic"]

    @pytest.mark.asyncio
    async def test_bundle_id_is_content_addressed(self, bundle_service):
        """Same content should produce same bundleId"""
        payload = {"message": "Deterministic test"}

        bundle1_create = BundleCreate(
            payload=payload,
            payloadType="text/plain",
            topic=Topic.COORDINATION
        )
        bundle1 = await bundle_service.create_bundle(bundle1_create)

        # Note: bundleId includes signature, which includes timestamp,
        # so two bundles created at different times will have different IDs
        # But the calculation itself should be deterministic
        calculated_id = bundle1.calculate_bundle_id()
        assert bundle1.bundleId == calculated_id


class TestBundleValidation:
    """Test bundle validation logic"""

    @pytest.mark.asyncio
    async def test_validate_valid_bundle(self, bundle_service):
        """Should validate a correctly signed bundle"""
        bundle_create = BundleCreate(
            payload={"test": "data"},
            payloadType="test/type",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        is_valid, error = await bundle_service.validate_bundle(bundle)

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_reject_tampered_payload(self, bundle_service):
        """Should reject bundle with tampered payload"""
        bundle_create = BundleCreate(
            payload={"original": "data"},
            payloadType="test/type",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Tamper with payload
        bundle.payload = {"tampered": "data"}

        is_valid, error = await bundle_service.validate_bundle(bundle)

        assert is_valid is False
        assert "signature" in error.lower() or "mismatch" in error.lower()

    @pytest.mark.asyncio
    async def test_reject_expired_bundle(self, bundle_service):
        """Should reject expired bundle"""
        # Create bundle that expires in the past
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        bundle_create = BundleCreate(
            payload={"test": "expired"},
            payloadType="test/type",
            topic=Topic.COORDINATION,
            expiresAt=past_time
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        is_valid, error = await bundle_service.validate_bundle(bundle)

        assert is_valid is False
        assert "expired" in error.lower()

    @pytest.mark.asyncio
    async def test_reject_invalid_signature(self, bundle_service):
        """Should reject bundle with invalid signature"""
        bundle_create = BundleCreate(
            payload={"test": "data"},
            payloadType="test/type",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Corrupt the signature
        bundle.signature = "invalid_signature_data"

        is_valid, error = await bundle_service.validate_bundle(bundle)

        assert is_valid is False
        assert "signature" in error.lower()

    @pytest.mark.asyncio
    async def test_reject_hop_limit_exceeded(self, bundle_service):
        """Should reject bundle that exceeded hop limit"""
        # Create a bundle with hopLimit=5, then manually set hopCount=10
        # We need to create it manually to avoid signature issues
        from datetime import datetime, timezone, timedelta
        from app.models.bundle import Bundle

        bundle = Bundle(
            bundleId="b:sha256:test_hop_exceeded",
            createdAt=datetime.now(timezone.utc),
            expiresAt=datetime.now(timezone.utc) + timedelta(hours=1),
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=[],
            payloadType="test/type",
            payload={"test": "data"},
            hopLimit=5,
            hopCount=10,  # Exceeds limit
            receiptPolicy=ReceiptPolicy.NONE,
            signature="test_signature",
            authorPublicKey=bundle_service.crypto_service.get_public_key_pem()
        )

        # Sign the bundle with correct hopCount=10
        canonical = bundle.to_canonical_json()
        bundle.signature = bundle_service.crypto_service.sign(canonical)
        bundle.bundleId = bundle.calculate_bundle_id()

        is_valid, error = await bundle_service.validate_bundle(bundle)

        assert is_valid is False
        assert "hop" in error.lower()


class TestBundleReceiving:
    """Test bundle receiving and routing to queues"""

    @pytest.mark.asyncio
    async def test_receive_valid_bundle(self, bundle_service):
        """Should accept and route valid bundle to inbox"""
        bundle_create = BundleCreate(
            payload={"message": "incoming"},
            payloadType="text/plain",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Simulate receiving from another node
        success, message = await bundle_service.receive_bundle(bundle)

        assert success is True
        assert "success" in message.lower()

    @pytest.mark.asyncio
    async def test_reject_duplicate_bundle(self, bundle_service):
        """Should reject duplicate bundles"""
        bundle_create = BundleCreate(
            payload={"message": "duplicate test"},
            payloadType="text/plain",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Receive first time
        success1, _ = await bundle_service.receive_bundle(bundle)
        assert success1 is True

        # Try to receive again
        success2, message2 = await bundle_service.receive_bundle(bundle)
        assert success2 is False
        assert "exists" in message2.lower() or "duplicate" in message2.lower()

    @pytest.mark.asyncio
    async def test_quarantine_invalid_bundle(self, bundle_service):
        """Should quarantine invalid bundles"""
        bundle_create = BundleCreate(
            payload={"test": "data"},
            payloadType="test/type",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Tamper with bundle
        bundle.payload = {"tampered": "content"}

        success, message = await bundle_service.receive_bundle(bundle)

        assert success is False
        assert "invalid" in message.lower()
        # Bundle should be in quarantine (implementation detail - not tested here)


class TestBundleProperties:
    """Test bundle utility methods and properties"""

    @pytest.mark.asyncio
    async def test_bundle_snake_case_aliases(self, bundle_service):
        """Should provide snake_case aliases for camelCase fields"""
        bundle_create = BundleCreate(
            payload={"test": "aliases"},
            payloadType="test/type",
            topic=Topic.COORDINATION
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Test all snake_case aliases
        assert bundle.bundle_id == bundle.bundleId
        assert bundle.created_at == bundle.createdAt
        assert bundle.expires_at == bundle.expiresAt
        assert bundle.payload_type == bundle.payloadType
        assert bundle.hop_limit == bundle.hopLimit
        assert bundle.hop_count == bundle.hopCount
        assert bundle.receipt_policy == bundle.receiptPolicy
        assert bundle.author_public_key == bundle.authorPublicKey

    def test_is_expired(self):
        """Should correctly detect expired bundles"""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        expired_bundle = Bundle(
            bundleId="b:sha256:test1",
            createdAt=datetime.now(timezone.utc),
            expiresAt=past,
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=[],
            payloadType="test",
            payload={},
            hopLimit=20,
            receiptPolicy=ReceiptPolicy.NONE,
            signature="test_sig",
            authorPublicKey="test_key"
        )

        valid_bundle = Bundle(
            bundleId="b:sha256:test2",
            createdAt=datetime.now(timezone.utc),
            expiresAt=future,
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=[],
            payloadType="test",
            payload={},
            hopLimit=20,
            receiptPolicy=ReceiptPolicy.NONE,
            signature="test_sig",
            authorPublicKey="test_key"
        )

        assert expired_bundle.is_expired() is True
        assert valid_bundle.is_expired() is False

    def test_is_hop_limit_exceeded(self):
        """Should correctly detect hop limit exceeded"""
        bundle_within_limit = Bundle(
            bundleId="b:sha256:test1",
            createdAt=datetime.now(timezone.utc),
            expiresAt=datetime.now(timezone.utc) + timedelta(hours=1),
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=[],
            payloadType="test",
            payload={},
            hopLimit=5,
            hopCount=3,
            receiptPolicy=ReceiptPolicy.NONE,
            signature="test_sig",
            authorPublicKey="test_key"
        )

        bundle_exceeded = Bundle(
            bundleId="b:sha256:test2",
            createdAt=datetime.now(timezone.utc),
            expiresAt=datetime.now(timezone.utc) + timedelta(hours=1),
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=[],
            payloadType="test",
            payload={},
            hopLimit=5,
            hopCount=10,
            receiptPolicy=ReceiptPolicy.NONE,
            signature="test_sig",
            authorPublicKey="test_key"
        )

        assert bundle_within_limit.is_hop_limit_exceeded() is False
        assert bundle_exceeded.is_hop_limit_exceeded() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
