# Workshop Verification Checklist

**Purpose:** Verify that all workshop requirements are met before deployment
**Status:** Ready for final verification
**Last Updated:** 2025-12-22

---

## Pre-Workshop Verification (Do This Before Workshop Day)

### 1. APK Installation Test

- [ ] **Download APK from build directory**
  ```bash
  # APK location
  frontend/android/app/build/outputs/apk/debug/app-debug.apk
  ```

- [ ] **Install on physical Android device**
  - Transfer APK to phone (USB, ADB, or QR code)
  - Enable "Install from Unknown Sources" in Settings
  - Install APK
  - Verify app opens without crashes

- [ ] **Test on minimum spec device**
  - Android 8.0 or higher
  - 2GB RAM minimum
  - Verify acceptable performance

### 2. Onboarding Flow Test

- [ ] **First-time user experience**
  - Open app for first time
  - See 6-step onboarding (Welcome → Gift Economy → Create Offer → Browse Offers → Agents Help → Completion)
  - Complete all steps without errors
  - Land on main app screen

- [ ] **Event QR code scanning**
  - Generate event QR code (test workshop event)
  - Scan QR from another phone
  - Verify user is added to event community
  - See other event participants

### 3. Core Gift Economy Flow Test

- [ ] **Create an offer**
  - Navigate to Offers page
  - Click "Create Offer"
  - Fill in: title, description, quantity, tags
  - Submit successfully
  - See offer in offer list

- [ ] **Create a need**
  - Navigate to Needs page
  - Click "Create Need"
  - Fill in: title, description, urgency, tags
  - Submit successfully
  - See need in needs list

- [ ] **Get matched**
  - Wait for AI matchmaker to run
  - Check Matches page
  - Verify compatible offer/need matches appear
  - Match quality score displayed

- [ ] **Accept a match**
  - Click on a match
  - Review match details
  - Click "Accept Match"
  - Verify exchange is created

- [ ] **Complete an exchange**
  - Navigate to Exchanges page
  - Select an exchange
  - Mark as "In Progress"
  - Complete the exchange
  - Both parties confirm completion

### 4. Mesh Messaging Test

- [ ] **Two-phone mesh test**
  - Have two phones with app installed
  - Ensure both have Bluetooth/WiFi enabled
  - User A sends message to User B
  - Verify message appears on User B's phone
  - Verify end-to-end encryption indicator

- [ ] **Offline message delivery**
  - Phone A composes message while offline
  - Message queued locally
  - Phone A comes in range of Phone B
  - Verify message syncs via mesh
  - Verify delivery confirmation

### 5. Web of Trust Test

- [ ] **Genesis node vouching**
  - Identify genesis node (trust = 1.0)
  - Genesis vouches for User A
  - Verify User A trust score ~0.85

- [ ] **Multi-hop trust propagation**
  - User A (trust 0.85) vouches for User B
  - Verify User B trust score (trust × decay)
  - User B attempts high-trust action
  - Verify access granted/denied based on threshold

- [ ] **Vouch revocation**
  - User A revokes vouch for User B
  - Verify User B's trust recalculated
  - If no other vouch chains, verify User B loses high-trust access

### 6. OPSEC Features Test

- [ ] **Duress PIN**
  - Set up normal PIN (e.g., 1234)
  - Set up duress PIN (e.g., 4321)
  - Login with duress PIN
  - Verify login appears successful (no visible difference)
  - Verify burn notice created
  - Verify local sensitive data wiped OR decoy mode activated

- [ ] **Quick wipe**
  - Navigate to panic features
  - Trigger quick wipe
  - Verify confirmation dialog
  - Confirm wipe
  - Verify all local data deleted
  - Verify keys securely overwritten (not just deleted)

- [ ] **Dead man's switch**
  - Set dead man's switch timer (e.g., 72 hours)
  - Don't check in for duration
  - Verify burn notice sent after timer expires
  - Verify vouch chain notified

### 7. Steward Dashboard Test

- [ ] **Metrics display**
  - Login as steward
  - Navigate to steward dashboard
  - Verify metrics displayed:
    - Member count
    - Active offers/needs
    - Exchanges this week
    - Cell health indicators

- [ ] **Attention items**
  - Verify attention queue shows:
    - Pending join requests
    - Proposals awaiting approval
    - Trust issues requiring review
  - Click on item
  - Verify details displayed

- [ ] **Approve join request**
  - Select pending join request
  - Review applicant details
  - Click "Approve"
  - Verify member added to cell
  - Verify applicant receives notification

### 8. Local Cells Test

- [ ] **Cell creation**
  - Navigate to Cells page
  - Create new cell (5-50 members)
  - Set cell name, description, visibility
  - Invite members
  - Verify cell appears in cell list

- [ ] **Cell discovery**
  - As new user, browse available cells
  - See cells with PUBLIC visibility
  - Request to join cell
  - Verify request sent to stewards

- [ ] **Cell-specific resources**
  - As cell member, create offer with audience=CELL
  - Verify offer visible to cell members
  - Verify offer NOT visible to non-members

### 9. Offline-First Verification

- [ ] **Airplane mode test**
  - Enable airplane mode on phone
  - Open app
  - Verify local data still accessible:
    - View offers/needs
    - View exchanges
    - View messages (already received)
  - Create new offer
  - Verify offer saved locally
  - Disable airplane mode
  - Verify offer syncs to network

- [ ] **Sync conflict resolution**
  - Create offer on Phone A (offline)
  - Create different offer with same ID on Phone B (offline)
  - Bring both phones online
  - Verify conflict detected
  - Verify conflict resolution (last-write-wins or merge)

### 10. Sanctuary Network Test (High-Trust Only)

⚠️ **Warning:** Only test with trusted participants. Real sanctuary resources must never be compromised.

- [ ] **Safe space offer**
  - Steward offers safe_space resource
  - Mark sensitivity: HIGH
  - Verify resource NOT visible until verified

- [ ] **Multi-steward verification**
  - 3 of 5 stewards verify safe space:
    - Escape routes confirmed
    - Capacity confirmed
    - Buddy protocol confirmed
  - After verification, resource becomes visible
  - Only high-trust users (>0.8) can see resource

- [ ] **Auto-purge timer**
  - Create sanctuary coordination message
  - Set auto-purge: 24 hours
  - Wait 24 hours
  - Verify message deleted from all devices
  - Verify no permanent records retained

### 11. Rapid Response Test (Simulation Only)

⚠️ **Warning:** Only test with simulation data. Never trigger real alerts during testing.

- [ ] **Emergency alert creation**
  - User taps emergency button twice
  - Enters alert type: "ice_raid" (simulation)
  - Enters location hint: "test location"
  - Verify alert created with EMERGENCY priority

- [ ] **Alert propagation**
  - Verify alert propagates to responders within 30 seconds
  - Check multiple phones
  - Verify all responders receive alert

- [ ] **Responder coordination**
  - Responder marks "available"
  - Responder marks "en_route"
  - Coordinator escalates/de-escalates
  - Verify status updates visible to all

- [ ] **After-action review**
  - Alert resolved
  - Coordinator creates after-action review
  - Captures lessons learned
  - No permanent location data retained

### 12. Performance Test

- [ ] **Load test with 50 users**
  - Create 50 test accounts
  - Each creates 2 offers, 2 needs
  - Run matchmaker
  - Verify acceptable response time (<5 seconds)

- [ ] **Mesh sync performance**
  - 10 phones in mesh range
  - Each has 20 bundles to sync
  - Measure sync time
  - Verify EMERGENCY bundles prioritized

- [ ] **Database performance**
  - 1000+ offers in database
  - Search for specific tag
  - Verify results return <2 seconds
  - Verify pagination works

### 13. Battery/Storage Test

- [ ] **Battery consumption**
  - Full charge phone
  - Run app in background for 8 hours
  - Measure battery drain
  - Target: <10% drain per 8 hours

- [ ] **Storage consumption**
  - Fresh install: measure storage
  - Use app normally for 1 week
  - 50 offers, 50 needs, 100 messages
  - Measure storage
  - Target: <500MB total

---

## Workshop Day Verification (Do This Morning Of)

### Setup Phase (2 hours before workshop)

- [ ] **Test device staging**
  - 10 phones with APK pre-installed
  - All charged >80%
  - All connected to test mesh network
  - All running latest APK version

- [ ] **Event QR code generation**
  - Generate workshop event QR code
  - Test scan from 3 different phones
  - Print QR code poster (large format)
  - Prepare digital QR for projection

- [ ] **Steward accounts ready**
  - 3 steward accounts created
  - All logged in on separate devices
  - Dashboard tested and working
  - Approval permissions verified

- [ ] **Demo data seeded**
  - 10 sample offers
  - 10 sample needs
  - 5 sample matches
  - 2 completed exchanges (for demonstration)

### During Workshop Checks

- [ ] **First 30 minutes: Onboarding**
  - 20+ people successfully scan QR
  - All complete onboarding
  - No crashes or errors
  - Network performance acceptable

- [ ] **Hour 1: First Offers/Needs**
  - 50+ offers created
  - 50+ needs created
  - Matchmaker running every 5 minutes
  - First matches appearing

- [ ] **Hour 2: Exchanges Begin**
  - 20+ matches accepted
  - 10+ exchanges in progress
  - Mesh messaging working
  - No sync issues

- [ ] **Hour 3: Community Formation**
  - Cells forming organically
  - Stewards approving join requests
  - High engagement observed
  - No major bugs reported

- [ ] **End of Day: Impact Metrics**
  - 200+ attendees onboarded ✅
  - 50+ offers posted ✅
  - 20+ matches made ✅
  - 10+ exchanges completed ✅
  - Mesh messaging works phone-to-phone ✅

---

## Post-Workshop Verification

### Immediate (Within 24 hours)

- [ ] **Collect user feedback**
  - Survey sent to all participants
  - Bug reports collected
  - Feature requests noted
  - Pain points documented

- [ ] **Analyze logs**
  - Review error logs
  - Identify crash patterns
  - Check performance metrics
  - Note any security issues

- [ ] **Data integrity check**
  - Verify all offers/needs persisted
  - Check for data loss during mesh sync
  - Verify exchange completion records
  - Check trust score calculations

### Week 1 Follow-up

- [ ] **Active user retention**
  - How many users still active?
  - How many new offers/needs created?
  - How many exchanges completed?
  - What's the engagement rate?

- [ ] **Bug fix prioritization**
  - Critical bugs (data loss, crashes): Fix immediately
  - High bugs (broken features): Fix within 48 hours
  - Medium bugs (UX issues): Fix within 1 week
  - Low bugs (cosmetic): Backlog

- [ ] **Scale preparation**
  - If successful, prepare for 10,000+ users
  - Infrastructure scaling plan
  - Mesh network optimization
  - Database optimization

---

## Success Criteria Summary

### Must Have (Workshop Blocker)
- ✅ APK installs on Android 8+ devices
- ✅ Onboarding completes without errors
- ✅ Offer/need creation works
- ✅ Matchmaker finds compatible matches
- ✅ Exchanges can be completed
- ✅ Mesh messaging delivers messages

### Should Have (Quality)
- ✅ Web of trust prevents infiltration
- ✅ OPSEC features work (duress, wipe)
- ✅ Steward dashboard shows metrics
- ✅ Local cells can be created
- ✅ Offline mode works

### Nice to Have (Polish)
- ✅ Performance is acceptable on old phones
- ✅ Battery consumption is reasonable
- ✅ UI is responsive and clear
- ✅ Error messages are helpful

---

## Known Issues to Monitor

### Test Fixture Naming
- Some E2E tests reference migration files with different names
- This affects test suite, not production code
- Low priority fix (doesn't block workshop)

### Database Locking (Fixed)
- Previous sessions had SQLite locking issues
- Fixed in commit 4b28878
- Monitor for any recurrence during workshop

### First-Time Setup
- First app launch may be slow (database initialization)
- Users should expect 10-30 second initial load
- Subsequent launches much faster

---

## Emergency Contacts

If critical issues discovered during verification:

1. **Check logs first**
   - `adb logcat` for Android logs
   - Backend logs in `valueflows_node/logs/`
   - Frontend console errors

2. **Review recent commits**
   - Check git log for recent changes
   - Verify no regressions introduced

3. **Rollback if necessary**
   - Keep previous working APK
   - Can rollback to previous commit if needed

---

## Final Checklist Before Workshop

- [ ] All verification tests above completed
- [ ] No critical bugs identified
- [ ] APK copied to multiple USB drives (redundancy)
- [ ] Event QR code tested and printed
- [ ] Steward devices staged and ready
- [ ] Demo data seeded
- [ ] Backup plan prepared (if network fails, what's Plan B?)

---

**If all boxes checked: READY FOR WORKSHOP** ✅

**If any critical issues: DELAY WORKSHOP, FIX FIRST** ⚠️

Remember: This isn't a demo. This is infrastructure people will depend on. Better to delay than to fail when it matters.

---

*Last Updated: 2025-12-22*
*Status: Ready for verification*
