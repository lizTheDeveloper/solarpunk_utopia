# Implementation Tasks: Multi-AP Mesh Network

**Proposal:** multi-ap-mesh-network
**Complexity:** 4 systems

---

## Task Breakdown

### System 1: AP Infrastructure Setup (1.0 systems)

**Task 1.1: Configure AP devices (Raspberry Pi)**
- Install Raspberry Pi OS Lite
- Install and configure hostapd
- Configure SSIDs (SolarpunkGarden, SolarpunkKitchen, etc.)
- Assign subnets (10.44.1.0/24, 10.44.2.0/24, etc.)
- Configure DHCP (dnsmasq)
- **Complexity:** 0.5 systems

**Task 1.2: Configure AP devices (Android phones)**
- Alternative: Use old Android phones as APs
- Configure AP mode via settings or Termux
- Assign SSIDs and subnets
- **Complexity:** 0.3 systems

**Task 1.3: Deploy APs in physical locations**
- Mount/place APs in garden, kitchen, workshop, library
- Provide power (solar + battery, wall power, or battery banks)
- Test coverage area
- **Complexity:** 0.2 systems

---

### System 2: Bridge Node Configuration (1.0 systems)

**Task 2.1: Configure bridge node role**
- Set node deployment preset to "bridge"
- Increase cache budget (2-8GB)
- Enable aggressive forwarding for emergency/perishables
- **Complexity:** 0.3 systems

**Task 2.2: Implement island transition behavior**
- Detect AP change (network SSID change)
- Trigger sync on new AP connection
- Prioritize pending bundles for forwarding
- **Complexity:** 0.4 systems

**Task 2.3: Implement bridge metrics**
- Track bundles carried between islands
- Log sync times and volumes
- Display bridge effectiveness in UI
- **Complexity:** 0.3 systems

---

### System 3: Mode C (DTN-Only) Fallback (0.8 systems)

**Task 3.1: Ensure DTN works without IP routing**
- Bundles sync within same island
- Bundles carried by bridge nodes
- No dependency on cross-island connectivity
- **Complexity:** 0.3 systems

**Task 3.2: Implement graceful degradation**
- Detect when IP routing unavailable
- Fall back to DTN-only mode
- Continue functioning without errors
- **Complexity:** 0.3 systems

**Task 3.3: Test Mode C reliability**
- Disable all routing between islands
- Verify all apps work
- Measure propagation time via bridge nodes
- **Complexity:** 0.2 systems

---

### System 4: Mode A (BATMAN-adv) Implementation (1.2 systems)

**Task 4.1: Document Mode A requirements**
- LineageOS or rooted Android
- Kernel with batman-adv support (built-in or module)
- Ability to create mesh interface (bat0)
- **Complexity:** 0.1 systems

**Task 4.2: Implement Mode A setup scripts**
- Load batman-adv kernel module
- Create bat0 interface
- Assign address from 10.44.0.0/16
- Join BATMAN mesh
- **Complexity:** 0.5 systems

**Task 4.3: Implement Mode A routing**
- Route DTN sync traffic over bat0
- Multi-hop forwarding between islands
- Monitor mesh topology
- **Complexity:** 0.4 systems

**Task 4.4: Implement Mode A → Mode C fallback**
- Detect routing failures
- Fallback to store-and-forward
- Recover when routing restored
- **Complexity:** 0.2 systems

---

## Mode B Research Tasks (not included in complexity, research only)

**Task R1: Evaluate Wi-Fi Direct support**
- Test concurrent Wi-Fi Direct groups on target devices
- Measure battery impact
- Document device compatibility

**Task R2: Prototype Meshrabiya-style bridging**
- Implement app-level virtual mesh
- Test reliability
- Compare to Mode C performance

**Task R3: Decide on Mode B viability**
- If viable, create implementation proposal
- If not viable, document reasons and stick with Mode A/C

---

## Validation Checklist

- [ ] 3+ APs operating (Garden, Kitchen, Workshop minimum)
- [ ] APs assign addresses from correct subnets
- [ ] Local DTN sync works within each island
- [ ] Bridge nodes carry bundles between islands
- [ ] Mode C works reliably (all apps functional)
- [ ] Bundle propagation measured (<10 min between islands)
- [ ] Mode A setup scripts work on supported devices
- [ ] Mode A provides multi-hop routing
- [ ] Mode A degrades to Mode C gracefully
- [ ] Mode B research completed (viability determined)
- [ ] Network handles 20+ concurrent users
- [ ] Battery impact measured and acceptable

---

## Total Complexity: 4 Systems

- AP infrastructure: 1.0 systems
- Bridge node configuration: 1.0 systems
- Mode C fallback: 0.8 systems
- Mode A implementation: 1.2 systems
