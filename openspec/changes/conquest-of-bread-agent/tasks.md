# Tasks: Conquest of Bread Agent

## Phase 1: The Common Heap

- [ ] Implement `AbundanceThreshold` calculator (Supply vs Demand velocity) <!-- id: 0 -->
- [ ] Create `HeapMode` flag in ResourceSpec (bypassing Exchange logic) <!-- id: 1 -->
- [ ] Build "Heap View" UI (showing what is currently free/abundant) <!-- id: 2 -->

## Phase 2: Rationing

- [ ] Implement `NeedPriority` classifier (Survival vs Comfort) <!-- id: 3 -->
- [ ] Create `RationingProtocol` (enforcing limits per person when scarce) <!-- id: 4 -->

## Validation

- [ ] Verify "Heap Mode" activates when inventory is high <!-- id: 5 -->
- [ ] Verify "Offer" requirement disappears for Heap items <!-- id: 6 -->
- [ ] Simulate rapid depletion and verify "Heap Mode" shuts off <!-- id: 7 -->
