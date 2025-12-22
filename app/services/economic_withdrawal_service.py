"""Economic Withdrawal Service

Every transaction in the gift economy is a transaction that DIDN'T go to Bezos.

Coordinated campaigns to redirect spending from extractive corporations to
regenerative community systems. This is economic strike as praxis.
"""
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from app.models.economic_withdrawal import (
    Campaign,
    CampaignPledge,
    CorporateAlternative,
    ExitProgress,
    BulkBuyOrder,
    BulkBuyCommitment,
    CampaignType,
    CampaignStatus,
    PledgeStatus,
)
from app.database.economic_withdrawal_repository import EconomicWithdrawalRepository
from app.services.bundle_service import BundleService
from app.models.bundle import BundleCreate
from app.models.priority import Priority, Audience, Topic


class EconomicWithdrawalService:
    """Service for economic withdrawal coordination."""

    def __init__(self, db_path: str):
        self.repo = EconomicWithdrawalRepository(db_path)
        self.bundle_service = BundleService(db_path)

    # ===== Campaign Management =====

    def create_campaign(
        self,
        created_by: str,
        campaign_type: CampaignType,
        name: str,
        description: str,
        target_corporation: str,
        target_category: Optional[str],
        cell_id: Optional[str],
        network_wide: bool,
        threshold_participants: int,
        pledge_deadline: datetime,
        campaign_start: datetime,
        campaign_end: datetime
    ) -> Campaign:
        """Create a new economic withdrawal campaign."""
        # Create campaign
        campaign = Campaign(
            id=f"campaign-{uuid.uuid4()}",
            campaign_type=campaign_type,
            name=name,
            description=description,
            target_corporation=target_corporation,
            target_category=target_category,
            cell_id=cell_id,
            network_wide=network_wide,
            created_by=created_by,
            threshold_participants=threshold_participants,
            current_participants=0,
            status=CampaignStatus.GATHERING,
            pledge_deadline=pledge_deadline,
            campaign_start=campaign_start,
            campaign_end=campaign_end,
            created_at=datetime.now(datetime.UTC),
            updated_at=datetime.now(datetime.UTC),
        )

        # Save to database
        campaign = self.repo.create_campaign(campaign)

        # Propagate via DTN
        self._propagate_campaign(campaign)

        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        return self.repo.get_campaign(campaign_id)

    def get_active_campaigns(self, cell_id: Optional[str] = None) -> List[Campaign]:
        """Get active campaigns (GATHERING or ACTIVE status)."""
        return self.repo.get_active_campaigns(cell_id)

    def get_campaigns_by_cell(self, cell_id: str) -> List[Campaign]:
        """Get all campaigns for a cell."""
        return self.repo.get_campaigns_by_cell(cell_id)

    def get_network_wide_campaigns(self) -> List[Campaign]:
        """Get all network-wide campaigns."""
        return self.repo.get_network_wide_campaigns()

    def check_and_activate_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Check if campaign can activate and activate if ready."""
        campaign = self.repo.get_campaign(campaign_id)
        if not campaign:
            return None

        if campaign.can_activate():
            campaign.activate()
            campaign = self.repo.update_campaign(campaign)

            # Propagate activation announcement
            self._propagate_campaign_activation(campaign)

        return campaign

    def complete_campaign(self, campaign_id: str) -> Campaign:
        """Complete a campaign and calculate final impact."""
        campaign = self.repo.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Only ACTIVE campaigns can be completed")

        # Calculate final impact from all pledges
        pledges = self.repo.get_campaign_pledges(campaign_id)
        total_impact = sum(p.estimated_spending_redirected or 0 for p in pledges)
        total_alternatives = sum(p.alternatives_used for p in pledges)

        campaign.estimated_economic_impact = total_impact
        campaign.local_transactions_facilitated = total_alternatives
        campaign.complete()

        campaign = self.repo.update_campaign(campaign)

        # Propagate completion announcement
        self._propagate_campaign_completion(campaign)

        # Update exit progress for all participants
        for pledge in pledges:
            self._update_user_exit_progress(pledge.user_id, campaign, pledge)

        return campaign

    def _propagate_campaign(self, campaign: Campaign):
        """Propagate new campaign via DTN."""
        bundle = BundleCreate(
            source_node=campaign.created_by,
            destination_audience=Audience.CELL if campaign.cell_id else Audience.NETWORK,
            topic=Topic.ECONOMIC_CAMPAIGN,
            priority=Priority.MEDIUM,
            payload={
                "action": "campaign_created",
                "campaign_id": campaign.id,
                "name": campaign.name,
                "description": campaign.description,
                "target_corporation": campaign.target_corporation,
                "campaign_type": campaign.campaign_type.value,
                "threshold_participants": campaign.threshold_participants,
                "pledge_deadline": campaign.pledge_deadline.isoformat(),
                "campaign_start": campaign.campaign_start.isoformat(),
                "campaign_end": campaign.campaign_end.isoformat(),
            },
            ttl_seconds=86400 * 7  # 7 days
        )
        self.bundle_service.store_bundle(bundle)

    def _propagate_campaign_activation(self, campaign: Campaign):
        """Propagate campaign activation announcement."""
        bundle = BundleCreate(
            source_node=campaign.created_by,
            destination_audience=Audience.CELL if campaign.cell_id else Audience.NETWORK,
            topic=Topic.ECONOMIC_CAMPAIGN,
            priority=Priority.MEDIUM,
            payload={
                "action": "campaign_activated",
                "campaign_id": campaign.id,
                "name": campaign.name,
                "participants": campaign.current_participants,
                "message": f"{campaign.name} has activated! {campaign.current_participants} members committed.",
            },
            ttl_seconds=86400 * 7
        )
        self.bundle_service.store_bundle(bundle)

    def _propagate_campaign_completion(self, campaign: Campaign):
        """Propagate campaign completion with results."""
        bundle = BundleCreate(
            source_node=campaign.created_by,
            destination_audience=Audience.CELL if campaign.cell_id else Audience.NETWORK,
            topic=Topic.ECONOMIC_CAMPAIGN,
            priority=Priority.MEDIUM,
            payload={
                "action": "campaign_completed",
                "campaign_id": campaign.id,
                "name": campaign.name,
                "participants": campaign.current_participants,
                "estimated_impact": campaign.estimated_economic_impact,
                "local_transactions": campaign.local_transactions_facilitated,
                "network_value": campaign.network_value_circulated,
                "message": f"{campaign.name} complete! ${campaign.estimated_economic_impact:.2f} redirected from {campaign.target_corporation}.",
            },
            ttl_seconds=86400 * 30  # 30 days
        )
        self.bundle_service.store_bundle(bundle)

    # ===== Pledge Management =====

    def create_pledge(
        self,
        user_id: str,
        campaign_id: str,
        commitment_level: str = "full",
        commitment_notes: Optional[str] = None,
        buddy_id: Optional[str] = None
    ) -> CampaignPledge:
        """Create a pledge to participate in a campaign."""
        # Check if user already pledged
        existing = self.repo.get_user_pledge_for_campaign(user_id, campaign_id)
        if existing:
            raise ValueError("User has already pledged to this campaign")

        # Get campaign
        campaign = self.repo.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status not in [CampaignStatus.GATHERING]:
            raise ValueError("Campaign is not accepting new pledges")

        if datetime.now(datetime.UTC) > campaign.pledge_deadline:
            raise ValueError("Pledge deadline has passed")

        # Create pledge
        pledge = CampaignPledge(
            id=f"pledge-{uuid.uuid4()}",
            campaign_id=campaign_id,
            user_id=user_id,
            commitment_level=commitment_level,
            commitment_notes=commitment_notes,
            status=PledgeStatus.COMMITTED,
            buddy_id=buddy_id,
            pledged_at=datetime.now(datetime.UTC),
            updated_at=datetime.now(datetime.UTC),
        )

        pledge = self.repo.create_pledge(pledge)

        # Update campaign participant count
        campaign.current_participants += 1
        campaign.updated_at = datetime.now(datetime.UTC)
        self.repo.update_campaign(campaign)

        # Check if campaign can activate
        self.check_and_activate_campaign(campaign_id)

        # Propagate pledge
        self._propagate_pledge(campaign, pledge)

        return pledge

    def get_pledge(self, pledge_id: str) -> Optional[CampaignPledge]:
        """Get a pledge by ID."""
        return self.repo.get_pledge(pledge_id)

    def get_user_pledges(self, user_id: str) -> List[CampaignPledge]:
        """Get all pledges by a user."""
        return self.repo.get_user_pledges(user_id)

    def get_campaign_pledges(self, campaign_id: str) -> List[CampaignPledge]:
        """Get all pledges for a campaign."""
        return self.repo.get_campaign_pledges(campaign_id)

    def mark_avoided(
        self,
        pledge_id: str,
        estimated_value: Optional[float] = None
    ) -> CampaignPledge:
        """Mark that user avoided target corporation."""
        pledge = self.repo.get_pledge(pledge_id)
        if not pledge:
            raise ValueError("Pledge not found")

        pledge.mark_avoided(estimated_value)
        return self.repo.update_pledge(pledge)

    def mark_alternative_used(
        self,
        pledge_id: str,
        alternative_id: Optional[str] = None
    ) -> CampaignPledge:
        """Mark that user used an alternative."""
        pledge = self.repo.get_pledge(pledge_id)
        if not pledge:
            raise ValueError("Pledge not found")

        pledge.mark_alternative_used()
        pledge = self.repo.update_pledge(pledge)

        # Increment alternative usage count if provided
        if alternative_id:
            self.repo.increment_alternative_usage(alternative_id)

        return pledge

    def activate_pledges_for_campaign(self, campaign_id: str):
        """Activate all pledges when campaign starts (GATHERING -> ACTIVE)."""
        pledges = self.repo.get_campaign_pledges(campaign_id)
        for pledge in pledges:
            if pledge.status == PledgeStatus.COMMITTED:
                pledge.status = PledgeStatus.ACTIVE
                pledge.updated_at = datetime.now(datetime.UTC)
                self.repo.update_pledge(pledge)

    def _propagate_pledge(self, campaign: Campaign, pledge: CampaignPledge):
        """Propagate new pledge (for participant count updates)."""
        bundle = BundleCreate(
            source_node=pledge.user_id,
            destination_audience=Audience.CELL if campaign.cell_id else Audience.NETWORK,
            topic=Topic.ECONOMIC_CAMPAIGN,
            priority=Priority.LOW,
            payload={
                "action": "pledge_created",
                "campaign_id": campaign.id,
                "current_participants": campaign.current_participants,
                "threshold_participants": campaign.threshold_participants,
            },
            ttl_seconds=86400 * 7
        )
        self.bundle_service.store_bundle(bundle)

    # ===== Corporate Alternatives =====

    def create_alternative(
        self,
        created_by: str,
        campaign_type: CampaignType,
        replaces_corporation: str,
        replaces_service: str,
        alternative_type: str,
        name: str,
        description: str,
        cell_id: Optional[str] = None,
        network_wide: bool = False,
        contact_user_id: Optional[str] = None,
        access_instructions: Optional[str] = None
    ) -> CorporateAlternative:
        """Create a corporate alternative."""
        alternative = CorporateAlternative(
            id=f"alt-{uuid.uuid4()}",
            campaign_type=campaign_type,
            replaces_corporation=replaces_corporation,
            replaces_service=replaces_service,
            alternative_type=alternative_type,
            name=name,
            description=description,
            cell_id=cell_id,
            network_wide=network_wide,
            contact_user_id=contact_user_id,
            access_instructions=access_instructions,
            times_used=0,
            created_at=datetime.now(datetime.UTC),
            created_by=created_by,
        )

        return self.repo.create_alternative(alternative)

    def get_alternatives_for_campaign(
        self,
        campaign_id: str
    ) -> List[CorporateAlternative]:
        """Get alternatives for a campaign's type."""
        campaign = self.repo.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        return self.repo.get_alternatives_for_campaign_type(
            campaign.campaign_type,
            campaign.cell_id
        )

    def get_alternatives_for_type(
        self,
        campaign_type: CampaignType,
        cell_id: Optional[str] = None
    ) -> List[CorporateAlternative]:
        """Get alternatives for a campaign type."""
        return self.repo.get_alternatives_for_campaign_type(campaign_type, cell_id)

    # ===== Exit Progress =====

    def get_or_create_exit_progress(self, user_id: str) -> ExitProgress:
        """Get or create exit progress for a user."""
        progress = self.repo.get_exit_progress(user_id)
        if not progress:
            progress = ExitProgress(
                id=f"progress-{uuid.uuid4()}",
                user_id=user_id,
                categories={},
                total_estimated_redirected=0.0,
                campaigns_participated=0,
                campaigns_completed=0,
                created_at=datetime.now(datetime.UTC),
                updated_at=datetime.now(datetime.UTC),
            )
            progress = self.repo.create_exit_progress(progress)
        return progress

    def _update_user_exit_progress(
        self,
        user_id: str,
        campaign: Campaign,
        pledge: CampaignPledge
    ):
        """Update user's exit progress after campaign completion."""
        progress = self.get_or_create_exit_progress(user_id)

        # Update total redirected
        if pledge.estimated_spending_redirected:
            progress.total_estimated_redirected += pledge.estimated_spending_redirected

        # Update campaign counts
        progress.campaigns_participated += 1
        if pledge.status == PledgeStatus.COMPLETED:
            progress.campaigns_completed += 1

        # Update category-specific progress
        category = campaign.target_category or campaign.campaign_type.value
        if category not in progress.categories:
            progress.categories[category] = {
                "baseline_monthly_spending": 0.0,
                "current_monthly_spending": 0.0,
                "reduction_percent": 0.0,
                "campaigns_completed": 0,
            }

        progress.categories[category]["campaigns_completed"] += 1
        progress.updated_at = datetime.now(datetime.UTC)

        self.repo.update_exit_progress(progress)

    # ===== Bulk Buys =====

    def create_bulk_buy(
        self,
        coordinator_id: str,
        cell_id: str,
        item_name: str,
        item_description: str,
        unit: str,
        retail_price_per_unit: float,
        wholesale_price_per_unit: float,
        minimum_units: int,
        commitment_deadline: datetime,
        delivery_date: datetime,
        distribution_location: Optional[str] = None,
        supplier: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> BulkBuyOrder:
        """Create a bulk buy order."""
        savings_percent = ((retail_price_per_unit - wholesale_price_per_unit) / retail_price_per_unit) * 100

        bulk_buy = BulkBuyOrder(
            id=f"bulk-{uuid.uuid4()}",
            campaign_id=campaign_id,
            item_name=item_name,
            item_description=item_description,
            unit=unit,
            retail_price_per_unit=retail_price_per_unit,
            wholesale_price_per_unit=wholesale_price_per_unit,
            savings_percent=savings_percent,
            minimum_units=minimum_units,
            current_committed_units=0,
            cell_id=cell_id,
            coordinator_id=coordinator_id,
            supplier=supplier,
            commitment_deadline=commitment_deadline,
            delivery_date=delivery_date,
            distribution_location=distribution_location,
            status="gathering",
            created_at=datetime.now(datetime.UTC),
            updated_at=datetime.now(datetime.UTC),
        )

        bulk_buy = self.repo.create_bulk_buy(bulk_buy)

        # Propagate bulk buy announcement
        self._propagate_bulk_buy(bulk_buy)

        return bulk_buy

    def commit_to_bulk_buy(
        self,
        user_id: str,
        bulk_buy_id: str,
        units: int
    ) -> BulkBuyCommitment:
        """Commit to a bulk buy."""
        bulk_buy = self.repo.get_bulk_buy(bulk_buy_id)
        if not bulk_buy:
            raise ValueError("Bulk buy not found")

        if bulk_buy.status != "gathering":
            raise ValueError("Bulk buy is not accepting commitments")

        if datetime.now(datetime.UTC) > bulk_buy.commitment_deadline:
            raise ValueError("Commitment deadline has passed")

        # Calculate total cost
        total_cost = units * bulk_buy.wholesale_price_per_unit

        # Create commitment
        commitment = BulkBuyCommitment(
            id=f"commitment-{uuid.uuid4()}",
            bulk_buy_id=bulk_buy_id,
            user_id=user_id,
            units=units,
            total_cost=total_cost,
            paid=False,
            picked_up=False,
            committed_at=datetime.now(datetime.UTC),
        )

        commitment = self.repo.create_bulk_buy_commitment(commitment)

        # Update bulk buy
        bulk_buy.current_committed_units += units
        bulk_buy.updated_at = datetime.now(datetime.UTC)

        # Check if threshold met
        if bulk_buy.can_order() and bulk_buy.status == "gathering":
            bulk_buy.status = "confirmed"

        self.repo.update_bulk_buy(bulk_buy)

        return commitment

    def get_bulk_buy(self, bulk_buy_id: str) -> Optional[BulkBuyOrder]:
        """Get a bulk buy order."""
        return self.repo.get_bulk_buy(bulk_buy_id)

    def get_bulk_buys_by_cell(self, cell_id: str) -> List[BulkBuyOrder]:
        """Get all bulk buys for a cell."""
        return self.repo.get_bulk_buys_by_cell(cell_id)

    def get_bulk_buy_commitments(self, bulk_buy_id: str) -> List[BulkBuyCommitment]:
        """Get all commitments for a bulk buy."""
        return self.repo.get_bulk_buy_commitments(bulk_buy_id)

    def _propagate_bulk_buy(self, bulk_buy: BulkBuyOrder):
        """Propagate bulk buy announcement."""
        bundle = BundleCreate(
            source_node=bulk_buy.coordinator_id,
            destination_audience=Audience.CELL,
            topic=Topic.ECONOMIC_CAMPAIGN,
            priority=Priority.MEDIUM,
            payload={
                "action": "bulk_buy_created",
                "bulk_buy_id": bulk_buy.id,
                "item_name": bulk_buy.item_name,
                "item_description": bulk_buy.item_description,
                "wholesale_price_per_unit": bulk_buy.wholesale_price_per_unit,
                "savings_percent": bulk_buy.savings_percent,
                "minimum_units": bulk_buy.minimum_units,
                "commitment_deadline": bulk_buy.commitment_deadline.isoformat(),
            },
            ttl_seconds=86400 * 7
        )
        self.bundle_service.store_bundle(bundle)
