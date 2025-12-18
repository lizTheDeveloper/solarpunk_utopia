# Tasks: Governance Circle Agent

## Phase 1: Proposals

- [ ] Define `GovernanceProposal` schema (title, description, votingMethod, deadline) <!-- id: 0 -->
- [ ] Implement voting logic (Consent, Consensus, Majority, Lazy Consensus) <!-- id: 1 -->
- [ ] Create UI for browsing and voting on proposals <!-- id: 2 -->

## Phase 2: Conflict Resolution

- [ ] Define `ConflictCase` schema <!-- id: 3 -->
- [ ] Implement "Circle Scheduler" (finds time for mediators + parties) <!-- id: 4 -->
- [ ] Create "Circle Script" templates (agent guides participants through steps) <!-- id: 5 -->

## Validation

- [ ] Verify separate voting methods work as intended <!-- id: 6 -->
- [ ] Verify blocked user triggers mediation prompt <!-- id: 7 -->
- [ ] Simulate a "Lazy Consensus" passing after timeout <!-- id: 8 -->
