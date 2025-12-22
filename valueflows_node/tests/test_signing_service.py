"""
Tests for Ed25519 signing service.

Validates cryptographic signing and verification of ValueFlows objects.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timezone
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from valueflows_node.app.services.signing_service import SigningService
from valueflows_node.app.models.vf.listing import Listing, ListingType
from valueflows_node.app.models.vf.agent import Agent, AgentType
from valueflows_node.app.models.vf.location import Location


@pytest.fixture
def temp_keys_dir():
    """Create a temporary directory for test keys"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def signing_service(temp_keys_dir):
    """Create a signing service with temporary keys"""
    return SigningService(keys_dir=temp_keys_dir)


class TestKeypairGeneration:
    """Test Ed25519 keypair generation and loading"""

    def test_generates_keypair_on_first_init(self, temp_keys_dir):
        """Should generate new keypair if none exists"""
        service = SigningService(keys_dir=temp_keys_dir)

        assert (temp_keys_dir / "vf_node_private.pem").exists()
        assert (temp_keys_dir / "vf_node_public.pem").exists()

        # Check permissions
        private_stat = (temp_keys_dir / "vf_node_private.pem").stat()
        assert oct(private_stat.st_mode)[-3:] == '600'  # Owner-only

    def test_loads_existing_keypair(self, temp_keys_dir):
        """Should load existing keypair instead of generating new one"""
        service1 = SigningService(keys_dir=temp_keys_dir)
        public_key1 = service1.get_public_key_pem()

        # Create second service with same keys dir
        service2 = SigningService(keys_dir=temp_keys_dir)
        public_key2 = service2.get_public_key_pem()

        assert public_key1 == public_key2

    def test_public_key_fingerprint(self, signing_service):
        """Should generate consistent fingerprint"""
        fingerprint1 = signing_service.get_public_key_fingerprint()
        fingerprint2 = signing_service.get_public_key_fingerprint()

        assert fingerprint1 == fingerprint2
        assert len(fingerprint1) == 16
        assert fingerprint1.isalnum()

    def test_static_generate_keypair(self):
        """Should generate valid keypair via static method"""
        keypair = SigningService.generate_keypair()

        assert 'private_key' in keypair
        assert 'public_key' in keypair
        assert '-----BEGIN PRIVATE KEY-----' in keypair['private_key']
        assert '-----BEGIN PUBLIC KEY-----' in keypair['public_key']


class TestSigning:
    """Test signing of VF objects"""

    def test_sign_listing(self, signing_service):
        """Should sign a listing with Ed25519"""
        listing = Listing(
            id="listing:test:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Test Offer",
            description="Test description",
            created_at=datetime.now(timezone.utc)
        )

        signature = signing_service.sign_object(listing)

        assert signature
        assert len(signature) > 0
        # Ed25519 signatures are 64 bytes, base64 encoded = 88 chars
        assert len(signature) == 88

    def test_sign_agent(self, signing_service):
        """Should sign an agent object"""
        agent = Agent(
            id="agent:001",
            name="Test Commune",
            agent_type=AgentType.GROUP,
            primary_location_id="loc:garden",
            created_at=datetime.now(timezone.utc)
        )

        signature = signing_service.sign_object(agent)

        assert signature
        assert len(signature) == 88

    def test_different_objects_different_signatures(self, signing_service):
        """Different objects should have different signatures"""
        listing1 = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        listing2 = Listing(
            id="listing:002",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:carrots",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=3.0,
            unit="kg",
            title="Carrots",
            description="Fresh carrots",
            created_at=datetime.now(timezone.utc)
        )

        sig1 = signing_service.sign_object(listing1)
        sig2 = signing_service.sign_object(listing2)

        assert sig1 != sig2

    def test_same_object_same_signature(self, signing_service):
        """Same object should produce same signature (deterministic)"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )

        sig1 = signing_service.sign_object(listing)
        sig2 = signing_service.sign_object(listing)

        assert sig1 == sig2


class TestVerification:
    """Test signature verification"""

    def test_verify_valid_signature(self, signing_service):
        """Should verify valid signature"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        # Sign the listing
        listing.signature = signing_service.sign_object(listing)
        public_key = signing_service.get_public_key_pem()

        # Verify signature
        is_valid = SigningService.verify_signature(listing, public_key)

        assert is_valid is True

    def test_verify_invalid_signature(self, signing_service):
        """Should reject invalid signature"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        # Set invalid signature
        listing.signature = "invalid_signature_data"
        public_key = signing_service.get_public_key_pem()

        # Verify signature
        is_valid = SigningService.verify_signature(listing, public_key)

        assert is_valid is False

    def test_verify_tampered_content(self, signing_service):
        """Should reject signature if content is tampered"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        # Sign the listing
        listing.signature = signing_service.sign_object(listing)
        public_key = signing_service.get_public_key_pem()

        # Tamper with content
        listing.quantity = 100.0  # Changed from 5.0

        # Verify signature (should fail)
        is_valid = SigningService.verify_signature(listing, public_key)

        assert is_valid is False

    def test_verify_wrong_public_key(self, temp_keys_dir):
        """Should reject signature when verified with wrong public key"""
        # Create first service and sign
        service1 = SigningService(keys_dir=temp_keys_dir)
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )
        listing.signature = service1.sign_object(listing)

        # Create second service with different keys
        temp_dir2 = Path(tempfile.mkdtemp())
        service2 = SigningService(keys_dir=temp_dir2)
        wrong_public_key = service2.get_public_key_pem()

        # Verify with wrong key (should fail)
        is_valid = SigningService.verify_signature(listing, wrong_public_key)

        shutil.rmtree(temp_dir2)
        assert is_valid is False

    def test_verify_missing_signature(self, signing_service):
        """Should reject object without signature"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        # No signature set
        public_key = signing_service.get_public_key_pem()

        is_valid = SigningService.verify_signature(listing, public_key)

        assert is_valid is False


class TestSignAndUpdate:
    """Test sign_and_update helper method"""

    def test_sign_and_update_with_author_id(self, signing_service):
        """Should sign and update author/signature fields with provided author_id"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        updated = signing_service.sign_and_update(listing, author_id="custom:author")

        assert updated.author == "custom:author"
        assert updated.signature
        assert len(updated.signature) == 88

    def test_sign_and_update_with_default_author(self, signing_service):
        """Should use node fingerprint as author_id when not provided"""
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )

        updated = signing_service.sign_and_update(listing)

        expected_fingerprint = signing_service.get_public_key_fingerprint()
        assert updated.author == expected_fingerprint
        assert updated.signature

        # Verify signature is valid
        is_valid = SigningService.verify_signature(updated, signing_service.get_public_key_pem())
        assert is_valid is True


class TestCrossServiceVerification:
    """Test verification across different service instances"""

    def test_verify_across_services_same_keys(self, temp_keys_dir):
        """Should verify signature from one service with another service using same keys"""
        # Service 1 signs
        service1 = SigningService(keys_dir=temp_keys_dir)
        listing = Listing(
            id="listing:001",
            listing_type=ListingType.OFFER,
            resource_spec_id="spec:tomatoes",
            agent_id="agent:001",
            location_id="loc:garden",
            quantity=5.0,
            unit="kg",
            title="Tomatoes",
            description="Fresh tomatoes",
            created_at=datetime.now(timezone.utc)
        )
        listing.signature = service1.sign_object(listing)
        public_key = service1.get_public_key_pem()

        # Service 2 verifies (same keys dir)
        service2 = SigningService(keys_dir=temp_keys_dir)
        is_valid = SigningService.verify_signature(listing, public_key)

        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
