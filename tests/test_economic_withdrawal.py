"""Tests for Economic Withdrawal System

Every transaction in the gift economy is a transaction that DIDN'T go to Bezos.

This tests the coordinated campaign system for redirecting spending from
extractive corporations to regenerative community systems.
"""
import pytest
import uuid
from datetime import datetime, timedelta, UTC
from pathlib import Path

from app.services.economic_withdrawal_service import EconomicWithdrawalService
from app.models.economic_withdrawal import (
    CampaignType,
    CampaignStatus,
    PledgeStatus,
)
from tests.conftest import init_test_db


# Test database path
TEST_DB_PATH = "data/test_economic_withdrawal.db"


@pytest.fixture
def service():
    """Create a test service with a clean database."""
    # Initialize database with migrations
    init_test_db(TEST_DB_PATH)

    # Create service
    service = EconomicWithdrawalService(db_path=TEST_DB_PATH)

    yield service

    # Cleanup: remove test database
    db_file = Path(TEST_DB_PATH)
    if db_file.exists():
        db_file.unlink()


def test_create_campaign(service):
    """Test creating an economic withdrawal campaign."""
    # Create campaign
    campaign = service.create_campaign(
        created_by="user-steward-001",
        campaign_type=CampaignType.AMAZON_EXIT,
        name="No Amazon November",
        description="Collective commitment to buy nothing from Amazon for 30 days",
        target_corporation="Amazon",
        target_category="online_retail",
        cell_id="cell-001",
        network_wide=False,
        threshold_participants=100,
        pledge_deadline=datetime.now(UTC) + timedelta(days=30),
        campaign_start=datetime.now(UTC) + timedelta(days=31),
        campaign_end=datetime.now(UTC) + timedelta(days=61),
    )

    assert campaign.id is not None
    assert campaign.name == "No Amazon November"
    assert campaign.status == CampaignStatus.GATHERING
    assert campaign.current_participants == 0
    assert campaign.threshold_participants == 100


def test_pledge_to_campaign(service):
    """Test pledging to participate in a campaign."""
    # Create campaign
    campaign = service.create_campaign(
        created_by="user-steward-001",
        campaign_type=CampaignType.AMAZON_EXIT,
        name="No Amazon November",
        description="Collective commitment to buy nothing from Amazon",
        target_corporation="Amazon",
        target_category="online_retail",
        cell_id="cell-001",
        network_wide=False,
        threshold_participants=2,
        pledge_deadline=datetime.now(UTC) + timedelta(days=30),
        campaign_start=datetime.now(UTC) + timedelta(days=31),
        campaign_end=datetime.now(UTC) + timedelta(days=61),
    )

    # Create pledge
    pledge = service.create_pledge(
        user_id="user-001",
        campaign_id=campaign.id,
        commitment_level="full",
        commitment_notes="Time to break my Amazon addiction!"
    )

    assert pledge.id is not None
    assert pledge.campaign_id == campaign.id
    assert pledge.user_id == "user-001"
    assert pledge.status == PledgeStatus.COMMITTED
    assert pledge.commitment_level == "full"

    # Check campaign updated
    updated_campaign = service.get_campaign(campaign.id)
    assert updated_campaign.current_participants == 1


def test_campaign_activation(service):
    """Test that campaign activates when threshold is met."""
    # Create campaign with low threshold
    campaign = service.create_campaign(
        created_by="user-steward-001",
        campaign_type=CampaignType.AMAZON_EXIT,
        name="Test Campaign",
        description="Test campaign",
        target_corporation="Amazon",
        target_category="online_retail",
        cell_id="cell-001",
        network_wide=False,
        threshold_participants=2,
        pledge_deadline=datetime.now(UTC) + timedelta(days=30),
        campaign_start=datetime.now(UTC) + timedelta(days=31),
        campaign_end=datetime.now(UTC) + timedelta(days=61),
    )

    # Add first pledge
    service.create_pledge(
        user_id="user-001",
        campaign_id=campaign.id,
        commitment_level="full"
    )

    # Campaign should still be GATHERING
    campaign = service.get_campaign(campaign.id)
    assert campaign.status == CampaignStatus.GATHERING

    # Add second pledge - should activate campaign
    service.create_pledge(
        user_id="user-002",
        campaign_id=campaign.id,
        commitment_level="full"
    )

    # Campaign should now be ACTIVE
    campaign = service.get_campaign(campaign.id)
    assert campaign.status == CampaignStatus.ACTIVE
    assert campaign.activated_at is not None


def test_mark_avoided_target(service):
    """Test marking that user avoided target corporation."""
    # Create campaign and pledge
    campaign = service.create_campaign(
        created_by="user-steward-001",
        campaign_type=CampaignType.AMAZON_EXIT,
        name="No Amazon November",
        description="Test",
        target_corporation="Amazon",
        target_category="online_retail",
        cell_id="cell-001",
        network_wide=False,
        threshold_participants=100,
        pledge_deadline=datetime.now(UTC) + timedelta(days=30),
        campaign_start=datetime.now(UTC) + timedelta(days=31),
        campaign_end=datetime.now(UTC) + timedelta(days=61),
    )

    pledge = service.create_pledge(
        user_id="user-001",
        campaign_id=campaign.id,
        commitment_level="full"
    )

    # Mark avoided
    updated_pledge = service.mark_avoided(
        pledge_id=pledge.id,
        estimated_value=50.0
    )

    assert updated_pledge.times_avoided_target == 1
    assert updated_pledge.estimated_spending_redirected == 50.0


def test_create_corporate_alternative(service):
    """Test creating a corporate alternative."""
    alternative = service.create_alternative(
        created_by="user-steward-001",
        campaign_type=CampaignType.TOOL_LIBRARY,
        replaces_corporation="Home Depot",
        replaces_service="tool rental/purchase",
        alternative_type="network_sharing",
        name="Downtown Tool Library",
        description="Shared power tools, hand tools, garden equipment",
        cell_id="cell-001",
        network_wide=False,
        contact_user_id="user-maria",
        access_instructions="DM Maria for access code"
    )

    assert alternative.id is not None
    assert alternative.name == "Downtown Tool Library"
    assert alternative.campaign_type == CampaignType.TOOL_LIBRARY
    assert alternative.times_used == 0


def test_exit_progress_tracking(service):
    """Test user's exit progress tracking."""
    # Get or create exit progress
    progress = service.get_or_create_exit_progress("user-001")

    assert progress.user_id == "user-001"
    assert progress.total_estimated_redirected == 0.0
    assert progress.campaigns_participated == 0
    assert progress.campaigns_completed == 0
    assert len(progress.categories) == 0


def test_bulk_buy_creation(service):
    """Test creating a bulk buy order."""
    bulk_buy = service.create_bulk_buy(
        coordinator_id="user-steward-001",
        cell_id="cell-001",
        item_name="Organic Brown Rice",
        item_description="25lb bags, local organic farm",
        unit="lb",
        retail_price_per_unit=3.50,
        wholesale_price_per_unit=2.00,
        minimum_units=500,
        commitment_deadline=datetime.now(UTC) + timedelta(days=14),
        delivery_date=datetime.now(UTC) + timedelta(days=21),
        distribution_location="Community Center",
        supplier="Valley View Organic Farm"
    )

    assert bulk_buy.id is not None
    assert bulk_buy.item_name == "Organic Brown Rice"
    assert bulk_buy.savings_percent > 40  # Should be ~43%
    assert bulk_buy.current_committed_units == 0
    assert bulk_buy.status == "gathering"


def test_bulk_buy_commitment(service):
    """Test committing to a bulk buy."""
    # Create bulk buy
    bulk_buy = service.create_bulk_buy(
        coordinator_id="user-steward-001",
        cell_id="cell-001",
        item_name="Organic Rice",
        item_description="Test",
        unit="lb",
        retail_price_per_unit=3.50,
        wholesale_price_per_unit=2.00,
        minimum_units=100,
        commitment_deadline=datetime.now(UTC) + timedelta(days=14),
        delivery_date=datetime.now(UTC) + timedelta(days=21),
    )

    # Commit to buy
    commitment = service.commit_to_bulk_buy(
        user_id="user-001",
        bulk_buy_id=bulk_buy.id,
        units=25
    )

    assert commitment.id is not None
    assert commitment.units == 25
    assert commitment.total_cost == 25 * 2.00  # 25 units * $2/unit
    assert not commitment.paid
    assert not commitment.picked_up

    # Check bulk buy updated
    updated_bulk_buy = service.get_bulk_buy(bulk_buy.id)
    assert updated_bulk_buy.current_committed_units == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
