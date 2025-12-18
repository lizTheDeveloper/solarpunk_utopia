"""
Example Integration: Multi-AP Mesh Network + DTN

This example demonstrates how bridge node services integrate with the DTN
Bundle System to enable store-and-forward communication across AP islands.

Run this as a standalone example or integrate into existing DTN application.
"""

import asyncio
import logging
from datetime import datetime

from bridge_node import (
    NetworkMonitor,
    SyncOrchestrator,
    BridgeMetrics,
    ModeDetector,
    NetworkInfo,
    MeshMode
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_bridge_node():
    """
    Example: Complete bridge node setup and operation.

    This demonstrates:
    1. Initializing all bridge services
    2. Wiring up callbacks for AP transitions
    3. Automatic sync on island changes
    4. Metrics tracking
    5. Mode detection and fallback
    """

    logger.info("=== Bridge Node Example ===")

    # Initialize services
    network_monitor = NetworkMonitor(poll_interval=5.0)
    sync_orchestrator = SyncOrchestrator(
        dtn_base_url="http://localhost:8000",
        sync_timeout=300,
        max_bundles_per_sync=100
    )
    bridge_metrics = BridgeMetrics(node_id="example_bridge")
    mode_detector = ModeDetector(check_interval=30.0)

    # Wire up callbacks
    async def on_ap_transition(old_network: NetworkInfo, new_network: NetworkInfo):
        """
        Called when bridge node moves between islands.

        This is the core integration point:
        1. Detect island change
        2. Trigger DTN sync
        3. Record metrics
        """
        logger.info(
            f"🚶 Island transition detected: "
            f"{old_network.island_id} → {new_network.island_id}"
        )

        # Record arrival at new island
        if new_network.island_id:
            bridge_metrics.record_island_arrival(new_network.island_id)

        # Trigger sync with new island
        logger.info(f"🔄 Starting sync with {new_network.island_id}...")
        sync_op = await sync_orchestrator.sync_on_ap_transition(
            old_network,
            new_network
        )

        # Record metrics
        if new_network.island_id:
            bridge_metrics.record_sync(
                island_id=new_network.island_id,
                bundles_received=sync_op.bundles_received,
                bundles_sent=sync_op.bundles_sent,
                from_island=old_network.island_id
            )

        logger.info(
            f"✅ Sync complete: "
            f"received={sync_op.bundles_received}, "
            f"sent={sync_op.bundles_sent}"
        )

    async def on_mode_change(old_mode: MeshMode, new_mode: MeshMode):
        """
        Called when mesh mode changes (Mode A ↔ Mode C).

        This enables graceful degradation and recovery.
        """
        if new_mode == MeshMode.MODE_A:
            logger.info("🚀 Switched to Mode A (BATMAN-adv multi-hop routing)")
        elif new_mode == MeshMode.MODE_C:
            logger.warning(
                f"⚠️  Fell back to Mode C (DTN-only) from {old_mode.value}"
            )

    # Set callbacks
    network_monitor.on_ap_transition = on_ap_transition
    mode_detector.on_mode_change = on_mode_change

    # Start services
    logger.info("Starting bridge services...")
    await network_monitor.start()
    await mode_detector.start()

    # Start metrics session
    session_id = bridge_metrics.start_session()
    logger.info(f"Bridge session started: {session_id}")

    # Run for a while (in production, this would run indefinitely)
    logger.info("Bridge node running... (Ctrl+C to stop)")
    try:
        # Print status every 30 seconds
        while True:
            await asyncio.sleep(30)

            # Get current status
            current_network = network_monitor.get_current_network()
            current_mode = mode_detector.get_current_mode()
            effectiveness = bridge_metrics.get_effectiveness_score()

            logger.info(
                f"📊 Status: island={current_network.island_id if current_network else 'none'}, "
                f"mode={current_mode.value}, "
                f"effectiveness={effectiveness:.2f}"
            )

            # Get recent metrics
            summary = bridge_metrics.get_summary()
            logger.info(
                f"📈 Totals: syncs={summary['totals']['syncs']}, "
                f"bundles_rx={summary['totals']['bundles_received']}, "
                f"bundles_tx={summary['totals']['bundles_sent']}, "
                f"islands={summary['totals']['islands_visited']}"
            )

    except KeyboardInterrupt:
        logger.info("Shutting down...")

    finally:
        # Cleanup
        await network_monitor.stop()
        await mode_detector.stop()
        bridge_metrics.end_session()

        # Export final metrics
        metrics_file = f"/tmp/bridge_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bridge_metrics.export_metrics(metrics_file)
        logger.info(f"Metrics exported to {metrics_file}")


async def example_ap_island():
    """
    Example: Access Point island with DTN node.

    This shows how an AP island runs a DTN node that:
    1. Serves bundles to local clients
    2. Syncs with bridge nodes when they visit
    3. Forwards bundles to other islands via bridges
    """

    logger.info("=== AP Island Example ===")
    logger.info("This example shows DTN node running on an AP island")
    logger.info("")
    logger.info("In production:")
    logger.info("1. Deploy AP with deploy_ap_raspberry_pi.sh")
    logger.info("2. Run DTN node on AP gateway (10.44.X.1:8000)")
    logger.info("3. DTN node serves sync endpoints:")
    logger.info("   - GET /sync/pull - Bridge nodes pull bundles")
    logger.info("   - POST /sync/push - Bridge nodes push bundles")
    logger.info("4. Bridge nodes visit and sync automatically")
    logger.info("")
    logger.info("See app/api/sync.py for DTN sync implementation")


async def example_mode_c_operation():
    """
    Example: Mode C (DTN-only) operation.

    This demonstrates the foundation layer that always works:
    1. Islands operate independently
    2. Bridge nodes carry bundles
    3. Bundles propagate via store-and-forward
    """

    logger.info("=== Mode C (DTN-Only) Example ===")
    logger.info("")
    logger.info("Scenario: Garden and Kitchen islands (no routing)")
    logger.info("")

    # Simulate island states
    garden_bundles = ["offer_123", "need_456", "file_chunk_789"]
    kitchen_bundles = ["offer_abc", "response_xyz"]

    logger.info(f"Garden island has {len(garden_bundles)} bundles")
    logger.info(f"Kitchen island has {len(kitchen_bundles)} bundles")
    logger.info("")

    # Simulate bridge node visit to Garden
    logger.info("Bridge node arrives at Garden...")
    logger.info(f"  Pulling {len(garden_bundles)} bundles from Garden")
    bridge_cache = garden_bundles.copy()
    logger.info(f"  Bridge cache: {bridge_cache}")
    logger.info("")

    # Simulate bridge node travel (5 minutes)
    logger.info("Bridge node walking to Kitchen... (5 min)")
    await asyncio.sleep(1)  # Simulated travel time
    logger.info("")

    # Simulate bridge node visit to Kitchen
    logger.info("Bridge node arrives at Kitchen...")
    logger.info(f"  Pushing {len(bridge_cache)} bundles to Kitchen")
    kitchen_bundles.extend(bridge_cache)
    logger.info(f"  Pulling {len(kitchen_bundles)} bundles from Kitchen")
    logger.info("")

    logger.info(f"✅ Garden bundles now on Kitchen: {garden_bundles}")
    logger.info(f"Total propagation time: ~5 minutes")
    logger.info("")
    logger.info("This is Mode C: Reliable store-and-forward via bridge walks")


async def example_mode_a_operation():
    """
    Example: Mode A (BATMAN-adv) operation.

    This demonstrates the optimum layer when available:
    1. Multi-hop routing over bat0
    2. Near-instant sync
    3. Graceful fallback to Mode C
    """

    logger.info("=== Mode A (BATMAN-adv) Example ===")
    logger.info("")
    logger.info("Scenario: Devices with batman-adv kernel support")
    logger.info("")

    # Check if Mode A available
    mode_detector = ModeDetector()
    mode_a_status = await mode_detector.check_mode_a()

    if mode_a_status.available:
        logger.info("✅ Mode A available!")
        logger.info(f"   Interface: {mode_a_status.batman_interface}")
        logger.info(f"   Version: {mode_a_status.batman_version}")
        logger.info(f"   Peers: {mode_a_status.mesh_peers}")
        logger.info("")
        logger.info("DTN sync now works over multi-hop routing:")
        logger.info("  Garden (10.44.0.10) → Kitchen (10.44.0.11)")
        logger.info("  Latency: <100ms (vs 5 min in Mode C)")
    else:
        logger.info("❌ Mode A not available")
        logger.info(f"   Reason: {mode_a_status.details}")
        logger.info("")
        logger.info("Falling back to Mode C (DTN-only)")
        logger.info("This is normal for stock Android devices")

    logger.info("")
    logger.info("Mode A provides speedup when available,")
    logger.info("but Mode C ensures everything always works.")


async def main():
    """Run all examples"""

    print("\n" + "="*60)
    print("Multi-AP Mesh Network Integration Examples")
    print("="*60 + "\n")

    # Example 1: Mode C operation (foundation)
    await example_mode_c_operation()
    await asyncio.sleep(2)

    # Example 2: Mode A operation (optimum)
    await example_mode_a_operation()
    await asyncio.sleep(2)

    # Example 3: AP island
    await example_ap_island()
    await asyncio.sleep(2)

    # Example 4: Full bridge node (commented out as it runs indefinitely)
    logger.info("\n" + "="*60)
    logger.info("To run full bridge node example:")
    logger.info("  python example_integration.py --bridge")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    import sys

    if "--bridge" in sys.argv:
        # Run full bridge node example
        asyncio.run(example_bridge_node())
    else:
        # Run quick examples
        asyncio.run(main())
