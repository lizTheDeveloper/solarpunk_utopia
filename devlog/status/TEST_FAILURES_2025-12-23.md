# Test Failure Report - 2025-12-23

**Autonomous Session Discovery**

## Summary

- **Total Tests:** 295
- **Passed:** 216 (73%)
- **Failed:** 61 (21%)
- **Errors:** 18 (6%)
- **Warnings:** 135

**Overall Test Health:** 27% failure rate - NEEDS IMMEDIATE ATTENTION

## Critical Findings

This is NOT a small number of broken tests. With 79 total failures/errors, approximately 1 in 4 tests is failing. This indicates:

1. Recent changes broke existing functionality
2. Tests were written but implementation incomplete
3. Integration between components is broken
4. CI/CD may not be running tests on commits

## Failures by Category

### P0 - Safety-Critical Features (19 failures/errors)

These protect lives. MUST be fixed before workshop.

#### Rapid Response (6 failures)
- `test_full_rapid_response_flow` - Complete emergency flow broken
- `test_critical_alert_requires_high_trust` - Trust gating not working
- `test_critical_alert_auto_downgrade_if_unconfirmed` - Auto-downgrade broken
- `test_alert_propagation_priority` - Emergency priority not working
- `test_alert_purge_after_24_hours` - Auto-purge not working
- `test_responder_coordination_flow` - Responder workflow broken

#### Sanctuary Network (6 errors)
- `test_full_sanctuary_flow` - ERROR: Complete flow broken
- `test_high_sensitivity_requires_high_trust` - ERROR: Trust requirements broken
- `test_steward_cannot_verify_twice` - ERROR: Duplicate verification check broken
- `test_verification_expires_after_90_days` - ERROR: Expiration not working
- `test_high_trust_resources_for_critical_needs` - ERROR
- `test_needs_second_verification_flag` - ERROR

#### Panic Features (2 failures)
- `test_quick_wipe_destroys_data` - Assertion error: data NOT wiped!
- `test_seed_phrase_encryption_decryption` - Encryption broken

#### Network Import (4 failures)
- `test_in_person_attestation_claim_offline` - Offline verification broken
- `test_challenge_response_verification_offline` - Challenge/response broken
- `test_mesh_vouch_verification_offline` - Mesh vouch broken
- `test_steward_accountability_offline` - Steward accountability broken

### P1 - Core DTN Infrastructure (18 failures)

#### Bundle Service Unit Tests (13 failures)
- `test_create_simple_bundle` - Basic bundle creation broken
- `test_create_bundle_with_ttl_hours` - TTL handling broken
- `test_create_bundle_auto_ttl` - Auto TTL broken
- `test_create_bundle_with_tags` - Tagging broken
- `test_bundle_id_is_content_addressed` - Content addressing broken
- `test_validate_valid_bundle` - Validation broken
- `test_reject_tampered_payload` - Tamper detection broken
- `test_reject_expired_bundle` - Expiration check broken
- `test_reject_invalid_signature` - Signature validation broken
- `test_receive_valid_bundle` - Bundle receiving broken
- `test_reject_duplicate_bundle` - Duplicate detection broken
- `test_quarantine_invalid_bundle` - Quarantine broken
- `test_bundle_snake_case_aliases` - Model serialization broken

#### DTN Mesh Sync (5 failures)
- `test_partial_overlap_sync` - Partial sync broken
- `test_emergency_priority_first` - Priority ordering broken
- `test_audience_enforcement_high_trust` - Trust enforcement broken
- `test_bidirectional_sync` - Two-way sync broken
- `test_no_duplicate_transfers` - Duplicate prevention broken

### P2 - Discovery & Coordination (14 failures)

#### Cross-Community Discovery (3 failures)
- `test_blocking_overrides_visibility` - Blocking check failing
- `test_public_vs_regional_audience` - Audience levels broken
- `test_visibility_respects_individual_choice` - Individual choice broken

**Root Cause:** Tests create vouches but don't establish trust chains properly. Alice vouches for Bob, but Alice isn't a genesis node, so Bob has computed_trust = 0.0. The `can_see_resource` method checks if viewer has trust >= 0.1 for NETWORK_WIDE visibility, which fails.

#### Care Outreach (11 errors)
- `test_register_volunteer` - ERROR
- `test_find_available_volunteer` - ERROR
- `test_flag_for_outreach` - ERROR
- `test_add_outreach_note` - ERROR
- `test_mark_converted` - ERROR
- `test_assess_and_provide` - ERROR
- `test_access_level_receiving_care` - ERROR
- `test_access_permissions_minimal_but_human` - ERROR
- `test_handle_suspected_infiltrator` - ERROR
- `test_get_metrics` - ERROR
- `test_suggest_experience_for_new_outreach` - ERROR
- `test_get_all_experiences` - ERROR

**Likely Cause:** Service not instantiated correctly or missing dependencies

### P3 - Economic Features (9 failures)

#### Economic Withdrawal (6 failures)
- `test_create_campaign` - AttributeError
- `test_pledge_to_campaign` - AttributeError
- `test_campaign_activation` - AttributeError
- `test_mark_avoided_target` - AttributeError
- `test_bulk_buy_creation` - AttributeError
- `test_bulk_buy_commitment` - AttributeError

**Likely Cause:** Service method renamed or signature changed

#### Gift Economy Integration (3 failures)
- `test_complete_offer_need_exchange_flow` - Core flow broken
- `test_bundle_propagation_across_services` - DTN propagation broken
- `test_agent_proposals_require_approval` - Agent approval broken

### P4 - API & Validation (7 failures)

#### API Endpoint Fixes (3 failures)
- `test_accept_match_updates_status` - Match acceptance broken
- `test_reject_match_updates_status` - Match rejection broken
- `test_reject_proposal_uses_current_user_id` - Proposal rejection auth broken

#### Fraud/Abuse Protections (4 failures)
- `test_verification_requires_min_stewards` - Steward verification broken
- `test_verification_valid_with_min_stewards` - Min stewards check broken
- `test_verification_expires_after_90_days` - Expiration broken
- `test_high_trust_requires_successful_uses` - Success tracking broken

### P5 - Test Infrastructure (8 failures)

#### Harness/Time Control (6 failures)
- `test_freeze_time` - TypeError
- `test_advance_time` - TypeError
- `test_advance_with_units` - TypeError
- `test_freeze_time_context_manager` - Error
- `test_advance_time_context_manager` - Error
- `test_revoke_vouch` - AssertionError

**Likely Cause:** Test harness API changed or broken

#### Sanctuary Verification (2 failures)
- `test_pending_verification_list` - Query broken
- `test_pending_excludes_steward_who_verified` - Filtering broken

### P6 - Miscellaneous (4 failures)

- `test_library_node_caching` - Knowledge distribution caching broken
- `test_complete_file_distribution_flow` - File distribution broken
- `test_local_first_export` - sqlite3.OperationalError: Fork rights export broken
- `test_time_based_alert_expiration` - Mycelial strike alert expiration broken

## Warnings

135 warnings detected, primarily:

1. **Pydantic Deprecation (39 warnings):** Class-based config deprecated, should use ConfigDict
2. **datetime.utcnow() Deprecation:** Should use timezone-aware datetime.now(datetime.UTC)
3. **Pydantic json_encoders Deprecation:** Should use custom serializers

## Recommendations

### Immediate Actions (Before Workshop)

1. **Fix P0 failures first** - Rapid response and sanctuary network are safety-critical
2. **Fix Bundle Service** - DTN is foundational infrastructure
3. **Fix Discovery** - Communities need to find each other's resources

### Short-Term (Post-Workshop Week 1)

1. **Fix Economic Features** - Gift economy and withdrawal campaigns
2. **Fix API Endpoints** - Match accept/reject, proposal rejection
3. **Fix Care Outreach** - Community support system

### Medium-Term (Month 1)

1. **Fix Test Infrastructure** - Time control harness
2. **Address Deprecation Warnings** - Pydantic and datetime updates
3. **Improve CI/CD** - Ensure tests run on every commit

## Root Cause Analysis

### Pattern 1: Incomplete Trust Chain Setup

Many E2E tests create vouches but don't establish genesis nodes, causing trust score computations to fail.

**Example:** `test_blocking_overrides_visibility` creates `alice_id -> bob_id` vouch, but alice_id is not a genesis node, so bob_id has computed_trust = 0.0.

**Fix:** Test helper should either:
- Create genesis node first
- Or use a trust graph fixture that includes genesis

### Pattern 2: AttributeError in Services

Economic withdrawal and care outreach tests fail with AttributeErrors, suggesting:
- Service methods were renamed
- Service dependencies changed
- Service not properly instantiated

**Fix:** Review service interfaces and update tests

### Pattern 3: TypeError in Test Harness

Time control tests fail with TypeErrors, suggesting:
- API signature changed
- Dependencies missing

**Fix:** Review harness implementation vs usage

## Test Coverage Analysis

```
Total: 295 tests
Passing: 216 (73%)
Failing: 79 (27%)
```

**Good Coverage Areas:**
- Web of Trust E2E (10/10 passing)
- Saturnalia E2E (14/14 passing)
- Governance E2E (10/10 passing)
- Ancestor Voting E2E (11/11 passing)
- Blocking Silent Failure (10/10 passing)
- Mycelial Strike E2E (9/10 passing - 90%)
- Algorithmic Transparency (13/13 passing)

**Problem Areas:**
- Rapid Response E2E (0/6 passing - 0%)
- Sanctuary Network E2E (0/6 passing - 0%)
- Care Outreach (0/12 passing - 0%)
- Bundle Service (0/13 passing - 0%)
- Economic Withdrawal (0/6 passing - 0%)

## Next Steps

### Create Remediation Proposal

File: `openspec/changes/fix-test-suite-failures/proposal.md`

**Requirements:**
- SHALL fix all P0 safety-critical failures
- SHALL fix all bundle service failures (foundational)
- SHALL fix discovery failures (workshop blocker)
- SHOULD fix remaining failures by priority
- SHALL add CI/CD test gates to prevent regression

### Estimated Effort

- P0 Safety-Critical: 20-30 hours
- P1 DTN Infrastructure: 15-20 hours
- P2-P6 Remaining: 30-40 hours
- **Total: 65-90 hours**

This is 2-3 weeks of focused work for one developer, or 1 week for 3 developers working in parallel.

## Conclusion

The test suite reveals significant technical debt. While 73% of tests pass, the 27% failure rate concentrates in mission-critical areas:

- Emergency response systems (rapid response, sanctuary)
- Core infrastructure (DTN bundles, mesh sync)
- Community features (discovery, care outreach)

**The workshop is at risk.** If rapid response and sanctuary networks don't work, we're shipping vaporware, not resistance infrastructure.

**Recommendation:** Pause feature work. Fix the foundations. Then ship.
