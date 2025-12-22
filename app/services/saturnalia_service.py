"""Saturnalia Protocol Service

'All authority is a mask, not a face.' - Paulo Freire

The Saturnalia Protocol creates temporary inversions to prevent roles from
hardening into identities. This is praxis - experiencing role fluidity to
understand that power is constructed, not natural.
"""
import uuid
import random
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from app.models.saturnalia import (
    SaturnaliaConfig,
    SaturnaliaEvent,
    SaturnaliaRoleSwap,
    SaturnaliaOptOut,
    SaturnaliaAnonymousPost,
    SaturnaliaReflection,
    SaturnaliaMode,
    EventStatus,
    TriggerType,
    SwapStatus,
)
from app.database.saturnalia_repository import SaturnaliaRepository


class SaturnaliaService:
    """Service for Saturnalia Protocol operations."""

    def __init__(self, db_path: str):
        self.repo = SaturnaliaRepository(db_path)

    # ===== Configuration =====

    def create_config(
        self,
        created_by: str,
        enabled_modes: List[SaturnaliaMode],
        frequency: str,
        duration_hours: int,
        cell_id: Optional[str] = None,
        community_id: Optional[str] = None,
        exclude_safety_critical: bool = True,
        allow_individual_opt_out: bool = True,
    ) -> SaturnaliaConfig:
        """Create a new Saturnalia configuration."""
        # Calculate next scheduled start based on frequency
        next_start = self._calculate_next_start(frequency)

        config = SaturnaliaConfig(
            id=f"saturnalia-config-{uuid.uuid4()}",
            cell_id=cell_id,
            community_id=community_id,
            enabled=True,
            enabled_modes=enabled_modes,
            frequency=frequency,
            duration_hours=duration_hours,
            exclude_safety_critical=exclude_safety_critical,
            allow_individual_opt_out=allow_individual_opt_out,
            next_scheduled_start=next_start,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=created_by,
        )

        return self.repo.create_config(config)

    def update_config(
        self,
        config_id: str,
        enabled_modes: Optional[List[SaturnaliaMode]] = None,
        frequency: Optional[str] = None,
        duration_hours: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[SaturnaliaConfig]:
        """Update a configuration."""
        config = self.repo.get_config(config_id)
        if not config:
            return None

        # Update fields
        if enabled_modes is not None:
            config.enabled_modes = enabled_modes
        if frequency is not None:
            config.frequency = frequency
            config.next_scheduled_start = self._calculate_next_start(frequency)
        if duration_hours is not None:
            config.duration_hours = duration_hours
        if enabled is not None:
            config.enabled = enabled

        config.updated_at = datetime.now(UTC)

        return self.repo.update_config(config)

    def get_config(self, config_id: str) -> Optional[SaturnaliaConfig]:
        """Get a configuration by ID."""
        return self.repo.get_config(config_id)

    def get_config_for_cell(self, cell_id: str) -> Optional[SaturnaliaConfig]:
        """Get configuration for a specific cell."""
        return self.repo.get_config_for_cell(cell_id)

    # ===== Event Management =====

    def trigger_event(
        self,
        config_id: str,
        triggered_by: Optional[str] = None,
        manual: bool = False,
    ) -> SaturnaliaEvent:
        """Trigger a new Saturnalia event."""
        config = self.repo.get_config(config_id)
        if not config or not config.enabled:
            raise ValueError("Config not found or disabled")

        now = datetime.now(UTC)
        end_time = now + timedelta(hours=config.duration_hours)

        event = SaturnaliaEvent(
            id=f"saturnalia-event-{uuid.uuid4()}",
            config_id=config_id,
            start_time=now,
            end_time=end_time,
            active_modes=config.enabled_modes,
            status=EventStatus.ACTIVE,
            trigger_type=TriggerType.MANUAL if manual else TriggerType.SCHEDULED,
            triggered_by=triggered_by,
            created_at=now,
            activated_at=now,
        )

        event = self.repo.create_event(event)

        # Activate modes
        self._activate_modes(event)

        # Schedule next event
        config.next_scheduled_start = self._calculate_next_start(config.frequency)
        self.repo.update_config(config)

        return event

    def complete_event(self, event_id: str) -> Optional[SaturnaliaEvent]:
        """Complete a Saturnalia event and restore normal state."""
        event = self.repo.get_event(event_id)
        if not event:
            return None

        # Deactivate modes
        self._deactivate_modes(event)

        # Update event status
        event.status = EventStatus.COMPLETED
        event.completed_at = datetime.now(UTC)

        return self.repo.update_event(event)

    def cancel_event(self, event_id: str, reason: str) -> Optional[SaturnaliaEvent]:
        """Cancel an active event."""
        event = self.repo.get_event(event_id)
        if not event:
            return None

        # Deactivate modes
        self._deactivate_modes(event)

        # Update event status
        event.status = EventStatus.CANCELLED
        event.cancelled_at = datetime.now(UTC)
        event.cancellation_reason = reason

        return self.repo.update_event(event)

    def get_active_events(self) -> List[SaturnaliaEvent]:
        """Get all currently active events."""
        return self.repo.get_active_events()

    def get_active_event_for_cell(self, cell_id: str) -> Optional[SaturnaliaEvent]:
        """Get active event for a specific cell."""
        return self.repo.get_active_event_for_cell(cell_id)

    def check_event_expiry(self) -> List[SaturnaliaEvent]:
        """Check for expired events and complete them."""
        active_events = self.repo.get_active_events()
        now = datetime.now(UTC)

        completed_events = []
        for event in active_events:
            if event.end_time <= now:
                completed = self.complete_event(event.id)
                if completed:
                    completed_events.append(completed)

        return completed_events

    # ===== Role Swaps =====

    def create_role_swap(
        self,
        event_id: str,
        original_user_id: str,
        original_role: str,
        temporary_user_id: str,
        scope_type: str,
        scope_id: Optional[str] = None,
    ) -> SaturnaliaRoleSwap:
        """Create a new role swap."""
        swap = SaturnaliaRoleSwap(
            id=f"saturnalia-swap-{uuid.uuid4()}",
            event_id=event_id,
            original_user_id=original_user_id,
            original_role=original_role,
            temporary_user_id=temporary_user_id,
            scope_type=scope_type,
            scope_id=scope_id,
            status=SwapStatus.ACTIVE,
            swapped_at=datetime.now(UTC),
        )

        return self.repo.create_role_swap(swap)

    def get_active_swaps_for_event(self, event_id: str) -> List[SaturnaliaRoleSwap]:
        """Get all active role swaps for an event."""
        return self.repo.get_active_swaps_for_event(event_id)

    def restore_role_swaps(self, event_id: str) -> None:
        """Restore all role swaps for an event."""
        swaps = self.repo.get_active_swaps_for_event(event_id)
        for swap in swaps:
            self.repo.restore_role_swap(swap.id)

    # ===== Opt-Outs =====

    def create_opt_out(
        self,
        user_id: str,
        mode: SaturnaliaMode,
        scope_type: str,
        scope_id: Optional[str] = None,
        reason: Optional[str] = None,
        is_permanent: bool = False,
        duration_days: Optional[int] = None,
    ) -> SaturnaliaOptOut:
        """Create a new opt-out."""
        expires_at = None
        if not is_permanent and duration_days:
            expires_at = datetime.now(UTC) + timedelta(days=duration_days)

        opt_out = SaturnaliaOptOut(
            id=f"saturnalia-optout-{uuid.uuid4()}",
            user_id=user_id,
            mode=mode,
            scope_type=scope_type,
            scope_id=scope_id,
            reason=reason,
            is_permanent=is_permanent,
            expires_at=expires_at,
            opted_out_at=datetime.now(UTC),
        )

        return self.repo.create_opt_out(opt_out)

    def is_user_opted_out(
        self,
        user_id: str,
        mode: SaturnaliaMode,
        scope_id: Optional[str] = None
    ) -> bool:
        """Check if user has opted out of a mode."""
        return self.repo.is_user_opted_out(user_id, mode, scope_id)

    # ===== Anonymous Posts =====

    def create_anonymous_post(
        self,
        event_id: str,
        post_type: str,
        post_id: str,
        actual_author_id: str,
    ) -> SaturnaliaAnonymousPost:
        """Record an anonymous post."""
        post = SaturnaliaAnonymousPost(
            id=f"saturnalia-anon-{uuid.uuid4()}",
            event_id=event_id,
            post_type=post_type,
            post_id=post_id,
            actual_author_id=actual_author_id,
            created_at=datetime.now(UTC),
        )

        return self.repo.create_anonymous_post(post)

    def reveal_anonymous_posts(self, event_id: str) -> None:
        """Reveal all anonymous posts for an event."""
        self.repo.reveal_anonymous_posts_for_event(event_id)

    def get_actual_author(self, post_id: str) -> Optional[str]:
        """Get the actual author of an anonymous post."""
        return self.repo.get_actual_author(post_id)

    # ===== Reflections =====

    def create_reflection(
        self,
        event_id: str,
        user_id: str,
        what_learned: str,
        what_surprised: Optional[str] = None,
        what_changed: Optional[str] = None,
        suggestions: Optional[str] = None,
        overall_rating: Optional[int] = None,
        would_do_again: bool = True,
    ) -> SaturnaliaReflection:
        """Create a post-event reflection."""
        reflection = SaturnaliaReflection(
            id=f"saturnalia-reflection-{uuid.uuid4()}",
            event_id=event_id,
            user_id=user_id,
            what_learned=what_learned,
            what_surprised=what_surprised,
            what_changed=what_changed,
            suggestions=suggestions,
            overall_rating=overall_rating,
            would_do_again=would_do_again,
            submitted_at=datetime.now(UTC),
        )

        return self.repo.create_reflection(reflection)

    def get_reflections_for_event(self, event_id: str) -> List[SaturnaliaReflection]:
        """Get all reflections for an event."""
        return self.repo.get_reflections_for_event(event_id)

    # ===== Mode Activation/Deactivation =====

    def _activate_modes(self, event: SaturnaliaEvent) -> None:
        """Activate all modes for an event."""
        for mode in event.active_modes:
            if mode == SaturnaliaMode.ROLE_SWAP:
                self._activate_role_swap_mode(event)
            elif mode == SaturnaliaMode.ANONYMOUS_PERIOD:
                self._activate_anonymous_mode(event)
            # Other modes are UI-level flags, don't require backend activation

    def _deactivate_modes(self, event: SaturnaliaEvent) -> None:
        """Deactivate all modes for an event."""
        # Restore role swaps
        self.restore_role_swaps(event.id)

        # Reveal anonymous posts
        self.reveal_anonymous_posts(event.id)

    def _activate_role_swap_mode(self, event: SaturnaliaEvent) -> None:
        """Activate role swap mode (placeholder - needs integration with actual roles system)."""
        # TODO: This would need to:
        # 1. Query current stewards
        # 2. Select random new stewards from trusted members
        # 3. Create role swaps
        # 4. Update permissions
        # For now, this is a placeholder
        pass

    def _activate_anonymous_mode(self, event: SaturnaliaEvent) -> None:
        """Activate anonymous posting mode."""
        # This is primarily a UI flag
        # Posts created during this time will be recorded as anonymous
        pass

    # ===== Scheduling Helpers =====

    def _calculate_next_start(self, frequency: str) -> datetime:
        """Calculate next event start time based on frequency."""
        now = datetime.now(UTC)

        if frequency == 'annually':
            # Random day in next year, same month
            return now + timedelta(days=365) + timedelta(days=random.randint(-15, 15))
        elif frequency == 'biannually':
            # Random day in 6 months
            return now + timedelta(days=180) + timedelta(days=random.randint(-7, 7))
        elif frequency == 'quarterly':
            # Random day in 3 months
            return now + timedelta(days=90) + timedelta(days=random.randint(-7, 7))
        else:  # manual
            # No automatic scheduling
            return None

    def check_scheduled_events(self) -> List[SaturnaliaEvent]:
        """Check for configs that should trigger scheduled events."""
        # This would be called periodically (e.g., daily cron)
        # For now, return empty list
        # TODO: Implement scheduled event triggering
        return []
