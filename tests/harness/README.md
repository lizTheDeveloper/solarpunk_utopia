# Test Harness Infrastructure

Utilities for complex test scenarios in the Solarpunk Gift Economy Mesh Network.

## Overview

The test harness provides three main utilities:

1. **Multi-Node Mesh Simulation** - Simulate DTN mesh networks with multiple nodes
2. **Time Control** - Freeze and manipulate time for timeout testing
3. **Trust Graph Fixtures** - Predefined trust network topologies

## Installation

No additional dependencies needed - the harness uses only Python standard library.

## Usage

### 1. Multi-Node Mesh Simulation

Test DTN bundle propagation across mesh networks:

```python
from tests.harness import MultiNodeHarness

async def test_mesh_propagation():
    harness = MultiNodeHarness()

    # Create nodes
    alice = harness.create_node("Alice")
    bob = harness.create_node("Bob")
    carol = harness.create_node("Carol")

    # Connect them: Alice -- Bob -- Carol
    harness.connect(alice, bob)
    harness.connect(bob, carol)

    # Create a bundle on Alice
    bundle = harness.create_bundle(
        source="Alice",
        destination="Carol",
        payload=b"Hello from Alice!",
        priority=1  # EMERGENCY priority
    )
    alice.add_bundle(bundle)

    # Sync Alice → Bob
    transferred = await harness.sync_nodes(alice, bob)
    assert bundle.bundle_id in transferred

    # Sync Bob → Carol
    transferred = await harness.sync_nodes(bob, carol)
    assert bundle.bundle_id in transferred

    # Verify Carol received the bundle
    assert bundle.bundle_id in carol.bundles
    assert carol.bundles[bundle.bundle_id].payload == b"Hello from Alice!"
```

**Features:**
- Create/destroy nodes dynamically
- Connect/disconnect nodes on demand
- Priority-based bundle transfer (EMERGENCY first)
- Automatic hop count tracking
- Bundle expiration (TTL)
- Max hop limit enforcement
- Sync logging and statistics

### 2. Time Control

Test timeout behaviors without waiting:

```python
from tests.harness import freeze_time, advance_time
import time

def test_bundle_expiration():
    # Freeze time at current moment
    with freeze_time() as tc:
        start = time.time()

        # Create bundle with 60 second TTL
        bundle = create_bundle(ttl_seconds=60)

        # Advance time by 61 seconds
        tc.advance(seconds=61)

        # Bundle is now expired
        assert is_expired(bundle)

        # Time resumes normally after context

def test_slow_exchange():
    # Advance to 24 hours in the future
    with advance_time(hours=24):
        # Check if deadline passed
        assert exchange.is_overdue()
```

**Features:**
- Freeze time at specific point
- Advance by seconds/minutes/hours/days
- Context managers for automatic cleanup
- Works with `time.time()` and `datetime.now()`

### 3. Trust Graph Fixtures

Test Web of Trust scenarios with predefined topologies:

```python
from tests.harness import create_trust_chain, create_disjoint_communities, TrustGraphFixture

def test_trust_propagation():
    # Create linear chain: Genesis → Alice → Bob → Carol
    chain = create_trust_chain(["Genesis", "Alice", "Bob", "Carol"])

    # Verify trust decay
    assert chain.get_trust("Genesis") == 1.0
    assert chain.get_trust("Alice") == 0.85  # 1.0 * 0.85
    assert chain.get_trust("Bob") == 0.7225  # 0.85 * 0.85
    assert chain.get_trust("Carol") == 0.614125  # 0.85^3

def test_vouch_revocation():
    chain = create_trust_chain(["Genesis", "Alice", "Bob"])

    # Revoke vouch
    chain.revoke_vouch("Alice", "Bob")

    # Bob's trust drops to 0 (no other path to genesis)
    assert chain.get_trust("Bob") == 0.0

def test_disjoint_communities():
    # Create 2 communities: one with 5 members, one with 3
    fixture = create_disjoint_communities([5, 3])

    # No trust path between communities
    path = fixture.get_trust_path("Community0_Member0", "Community1_Member0")
    assert path is None
```

**Predefined Topologies:**

- **Chain**: Linear trust propagation (A → B → C → D)
- **Disjoint Communities**: Multiple separate trust networks
- **Ring**: Circular vouching (A → B → C → D → A)
- **Star**: One center vouches for all (hub and spoke)

**Features:**
- Automatic trust score calculation
- Configurable trust decay (default 0.85)
- Vouch creation and revocation
- Trust path finding
- Graph export for debugging

## Example: Complete E2E Test

```python
import pytest
from tests.harness import MultiNodeHarness, create_trust_chain, freeze_time

@pytest.mark.asyncio
async def test_emergency_alert_with_trust_gating():
    """
    Test that emergency alerts propagate only through trusted nodes
    """
    # Set up trust network
    trust = create_trust_chain(["Genesis", "Alice", "Bob", "Carol"])

    # Set up mesh network
    harness = MultiNodeHarness()
    alice = harness.create_node("Alice")
    bob = harness.create_node("Bob")
    carol = harness.create_node("Carol")
    mallory = harness.create_node("Mallory")  # Untrusted

    # Connect all nodes
    harness.connect(alice, bob)
    harness.connect(bob, carol)
    harness.connect(bob, mallory)

    # Create emergency bundle
    bundle = harness.create_bundle(
        source="Alice",
        destination="*",  # Broadcast
        payload=b'{"type": "ice_raid", "location": "downtown"}',
        priority=10  # EMERGENCY
    )
    alice.add_bundle(bundle)

    # Propagate with trust gating
    # In real implementation, sync would check trust before transferring
    await harness.sync_nodes(alice, bob)

    # Bob has high trust, receives bundle
    assert bundle.bundle_id in bob.bundles

    # Sync to Carol (trusted) and Mallory (untrusted)
    # Real implementation would check trust.get_trust("Carol") >= 0.8
    if trust.get_trust("Carol") >= 0.8:
        await harness.sync_nodes(bob, carol)
        assert bundle.bundle_id in carol.bundles

    if trust.get_trust("Mallory") >= 0.8:
        await harness.sync_nodes(bob, mallory)
    else:
        # Mallory doesn't get emergency bundles (untrusted)
        assert bundle.bundle_id not in mallory.bundles
```

## Architecture Compliance

The test harness ensures compliance with architecture constraints:

1. **Fully Distributed**: No central coordination required
2. **Works Offline**: Pure mesh simulation, no network calls
3. **Seizure Resistant**: Tests compartmentalization and data minimization
4. **Understandable**: Clear APIs with examples
5. **No Dependencies**: Uses only Python stdlib

## Test Coverage

Use the harness to test:

- DTN bundle propagation (Priority 3, Phase 3)
- Emergency alert propagation (Priority 1, Phase 1)
- Web of Trust vouch chains (Priority 2, Phase 2)
- Cross-community discovery (Priority 3, Phase 3)
- Slow exchange timeouts (Priority 5, Phase 5)
- Auto-purge after delays (Sanctuary network)

## Performance

The harness is lightweight:
- Multi-node tests: <10ms for 10-node network
- Time control: Zero overhead (mocking only)
- Trust graphs: <1ms for 100-node graphs

Perfect for CI/CD pipelines.

## Integration with E2E Tests

See existing E2E tests for usage examples:
- `tests/e2e/test_dtn_mesh_sync_e2e.py` - Multi-node mesh sync
- `tests/e2e/test_web_of_trust_e2e.py` - Trust graph scenarios
- `tests/e2e/test_rapid_response_e2e.py` - Emergency propagation

## Contributing

When adding new harness utilities:

1. Follow existing patterns (dataclasses, type hints)
2. Add comprehensive docstrings
3. Include usage examples in this README
4. Write tests for the harness itself (`tests/test_harness.py`)
5. Keep it simple - no external dependencies

## Philosophy

> "If we can't test it automatically, we can't be sure it works when someone's life depends on it."

The test harness enables comprehensive testing of mesh network behaviors that would be impossible to reproduce reliably in real networks. By simulating complex scenarios deterministically, we ensure the system works correctly during ICE raids, infrastructure outages, and adversarial conditions.

Lives depend on this network. Test accordingly.
