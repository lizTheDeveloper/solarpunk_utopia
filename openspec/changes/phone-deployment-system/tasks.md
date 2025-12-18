# Implementation Tasks: Phone Deployment System

**Proposal:** phone-deployment-system
**Complexity:** 3 systems

---

## Task Breakdown

### System 1: Software Manifest and Installation (1.2 systems)

**Task 1.1: Build DTN Bundle Service APK**
- Android foreground service
- Queue management, TTL enforcement, forwarding
- Background sync on AP connection
- **Complexity:** 0.5 systems (depends on dtn-bundle-system being complete)

**Task 1.2: Build ValueFlows Node APK**
- Android app with UI
- VF database, CRUD operations
- Offer/need creation, browsing, search
- Agent integration
- **Complexity:** 0.5 systems (depends on valueflows-node-full being complete)

**Task 1.3: Create F-Droid installation script**
- Download F-Droid APK
- Install via `adb install`
- Configure F-Droid repositories
- **Complexity:** 0.1 systems

**Task 1.4: Create base app installation script**
- Install Briar, Manyverse, Syncthing, Kiwix, Organic Maps, Termux
- Either via F-Droid or direct APK
- Verify installation success
- **Complexity:** 0.1 systems

---

### System 2: Deployment Presets (0.8 systems)

**Task 2.1: Define Citizen preset configuration**
- JSON file with: cache budget, TTL enforcement, forwarding rules, battery profile
- **Complexity:** 0.1 systems

**Task 2.2: Define Bridge preset configuration**
- Larger cache, aggressive forwarding, speculative caching enabled
- **Complexity:** 0.1 systems

**Task 2.3: Define AP preset configuration**
- Hotspot settings, index publishing frequency, portal hosting
- **Complexity:** 0.2 systems

**Task 2.4: Define Library preset configuration**
- Large cache, file serving, Kiwix full content, index response
- **Complexity:** 0.2 systems

**Task 2.5: Implement preset application**
- Read preset JSON
- Configure DTN Bundle Service
- Configure ValueFlows Node
- Set Android system settings (if applicable)
- **Complexity:** 0.2 systems

---

### System 3: Provisioning Automation (1.0 systems)

**Task 3.1: Create provisioning script**
- `scripts/provision_phone.sh --role=citizen`
- Steps: install F-Droid → install apps → install custom APKs → apply preset → load content → verify
- Progress reporting
- **Complexity:** 0.4 systems

**Task 3.2: Implement batch provisioning**
- `scripts/provision_batch.sh --count=10 --role=citizen`
- Parallel execution via `adb -s SERIAL`
- Progress dashboard (which phones complete, which fail)
- **Complexity:** 0.3 systems

**Task 3.3: Create content loading automation**
- Kiwix content packs (permaculture, regeneration, gift economy)
- Organic Maps offline data (local area)
- Distribute via Syncthing from master phone
- **Complexity:** 0.2 systems

**Task 3.4: Create testing and validation script**
- `scripts/test_phone.sh`
- Check: all apps installed, DTN service running, VF node database created, preset applied
- Report: pass/fail per phone
- **Complexity:** 0.1 systems

---

## Documentation Tasks (included in complexity)

**Task D1: Create participant quick-start guide**
- 1-page PDF: "Your Solarpunk Phone"
- Sections: Apps overview, Creating offers/needs, Discovering others, Battery tips
- **Complexity:** included

**Task D2: Create facilitator troubleshooting guide**
- Common issues and fixes
- How to reset phone to provisioned state
- Emergency contacts and procedures
- **Complexity:** included

---

## Workshop Preparation Tasks (included in complexity)

**Task W1: Provision 20+ phones**
- Run batch provisioning
- Handle failures (retry or replace)
- Label phones (SP-01 through SP-25)
- **Complexity:** included (execution, not development)

**Task W2: Charge all phones**
- Charge to >80%
- Verify battery health
- **Complexity:** included (logistics)

**Task W3: Print guides**
- Print 30x quick-start guides
- Print 5x facilitator troubleshooting guides
- **Complexity:** included (logistics)

**Task W4: Dry-run workshop flow**
- Simulate participant onboarding
- Test: receive phone → create offer → browse offers → accept match
- Time each step
- **Complexity:** included (validation)

---

## Validation Checklist

- [ ] DTN Bundle Service APK built and tested
- [ ] ValueFlows Node APK built and tested
- [ ] F-Droid installation script works
- [ ] Base app installation script works
- [ ] 4 deployment presets defined (Citizen, Bridge, AP, Library)
- [ ] Preset application works correctly
- [ ] Provisioning script provisions phone in <15 min
- [ ] Batch provisioning supports parallel execution
- [ ] Content loading works (Kiwix, maps)
- [ ] Testing script validates provisioned phones
- [ ] 20+ phones provisioned successfully
- [ ] All phones charged >80%
- [ ] Quick-start guide created and printed
- [ ] Troubleshooting guide created
- [ ] Dry-run completed successfully
- [ ] Phones ready for workshop participants

---

## Total Complexity: 3 Systems

- Software manifest and installation: 1.2 systems
- Deployment presets: 0.8 systems
- Provisioning automation: 1.0 systems
