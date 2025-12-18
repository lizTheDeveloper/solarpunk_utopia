# Tasks: Mycelial Health Monitor Agent

## Phase 1: Telemetry

- [ ] Implement `HardwareStats` collector (BatteryManager, StorageManager) <!-- id: 0 -->
- [ ] Create `HealthReport` bundle format <!-- id: 1 -->
- [ ] Build "Network Health Dashboard" UI <!-- id: 2 -->

## Phase 2: Intelligence

- [ ] Implement "Outage Detector" (correlation of power events) <!-- id: 3 -->
- [ ] Create "Healing Request" generator (auto-post to VF) <!-- id: 4 -->

## Validation

- [ ] Verify battery stats are accurate on target devices <!-- id: 5 -->
- [ ] Simulate multi-node power loss and verify alert trigger <!-- id: 6 -->
- [ ] Verify "Healing Request" appears in local Needs list <!-- id: 7 -->
