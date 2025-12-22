"""
Test Harness Infrastructure

Provides utilities for complex test scenarios:
- Multi-node mesh network simulation
- Time manipulation for timeout testing
- Trust graph fixtures for Web of Trust testing
"""

from .multi_node import MultiNodeHarness, MockNode
from .time_control import TimeController, freeze_time, advance_time
from .trust_fixtures import TrustGraphFixture, create_trust_chain, create_disjoint_communities

__all__ = [
    'MultiNodeHarness',
    'MockNode',
    'TimeController',
    'freeze_time',
    'advance_time',
    'TrustGraphFixture',
    'create_trust_chain',
    'create_disjoint_communities',
]
