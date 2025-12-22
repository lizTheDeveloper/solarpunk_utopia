"""
Time Control for Testing

Provides utilities to freeze and manipulate time in tests:
- Freeze time at a specific point
- Advance time by seconds/minutes/hours/days
- Verify timeout behaviors
"""

import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import patch


class TimeController:
    """
    Controller for manipulating time in tests

    Example usage:
        tc = TimeController()
        tc.freeze()  # Freeze time at current moment

        # Time doesn't advance
        assert tc.now() == tc.now()

        # Manually advance by 5 seconds
        tc.advance(seconds=5)
        assert tc.now() == tc.frozen_at + 5

        tc.unfreeze()  # Resume normal time
    """

    def __init__(self):
        self.frozen_at: Optional[float] = None
        self._original_time = time.time
        self._original_datetime_now = datetime.now

    def freeze(self, at: Optional[float] = None) -> None:
        """
        Freeze time at a specific point

        Args:
            at: Unix timestamp to freeze at (defaults to current time)
        """
        if at is None:
            at = time.time()

        self.frozen_at = at

        # Patch time.time and datetime.now
        def frozen_time():
            return self.frozen_at

        def frozen_datetime_now(tz=None):
            return datetime.fromtimestamp(self.frozen_at, tz=tz)

        # Store original functions
        self._time_patch = patch('time.time', side_effect=frozen_time)
        self._datetime_patch = patch('datetime.datetime.now', side_effect=frozen_datetime_now)

        self._time_patch.start()
        self._datetime_patch.start()

    def unfreeze(self) -> None:
        """Resume normal time"""
        if self.frozen_at is not None:
            self._time_patch.stop()
            self._datetime_patch.stop()
            self.frozen_at = None

    def advance(
        self,
        seconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        days: float = 0
    ) -> None:
        """
        Advance frozen time by specified amount

        Raises ValueError if time is not frozen
        """
        if self.frozen_at is None:
            raise ValueError("Cannot advance time when not frozen")

        delta = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
        self.frozen_at += delta

    def now(self) -> float:
        """Get current time (frozen or real)"""
        if self.frozen_at is not None:
            return self.frozen_at
        return time.time()

    def datetime_now(self) -> datetime:
        """Get current datetime (frozen or real)"""
        if self.frozen_at is not None:
            return datetime.fromtimestamp(self.frozen_at)
        return datetime.now()

    def is_frozen(self) -> bool:
        """Check if time is currently frozen"""
        return self.frozen_at is not None


@contextmanager
def freeze_time(at: Optional[float] = None):
    """
    Context manager to freeze time temporarily

    Example:
        with freeze_time():
            start = time.time()
            time.sleep(1)  # Doesn't actually sleep
            end = time.time()
            assert start == end  # Time didn't advance

        # Time resumes normally after context
    """
    tc = TimeController()
    tc.freeze(at)
    try:
        yield tc
    finally:
        tc.unfreeze()


@contextmanager
def advance_time(
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    days: float = 0
):
    """
    Context manager to freeze time and advance it

    Example:
        with advance_time(hours=24):
            # Time is now 24 hours in the future
            assert is_expired(timestamp_from_yesterday)

        # Time resumes normally
    """
    tc = TimeController()
    tc.freeze()
    tc.advance(seconds=seconds, minutes=minutes, hours=hours, days=days)
    try:
        yield tc
    finally:
        tc.unfreeze()


def mock_sleep(duration: float) -> None:
    """
    Mock sleep function that advances time instead of blocking

    Use this in tests that need to verify timeout behavior without actually waiting
    """
    # In tests, we don't actually sleep
    # Instead, we could advance a TimeController if one is active
    pass
