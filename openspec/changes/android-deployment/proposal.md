# Proposal: Android Deployment Package

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED - APK with local storage and DTN mesh sync ready
**Complexity:** 3 systems
**Timeline:** WORKSHOP BLOCKER
**Implemented:** 2025-12-19

## Problem Statement

The platform currently runs as Docker containers on servers. For a resilient mesh network that can survive infrastructure seizure, surveillance, and internet shutdowns, the system MUST run on commodity Android phones. Old phones. Cheap phones. Phones that can be distributed, hidden, and replaced.

## Proposed Solution

Package the DTN Bundle System, ValueFlows Node, and mesh networking as an Android APK that runs locally on each phone.

### Architecture

```
┌─────────────────────────────────────┐
│           Android Phone             │
├─────────────────────────────────────┤
│  React Native / WebView Frontend    │
│  ─────────────────────────────────  │
│  Local SQLite Database              │
│  ─────────────────────────────────  │
│  Python Runtime (Chaquopy/Kivy)     │
│  - DTN Bundle Service               │
│  - VF Node (local)                  │
│  - Mesh Sync Service                │
│  ─────────────────────────────────  │
│  WiFi Direct / Bluetooth Mesh       │
└─────────────────────────────────────┘
```

### Deployment Options

1. **Option A: WebView + Python Backend (Chaquopy)**
   - Existing React frontend in WebView
   - Python services via Chaquopy
   - Fastest path from current codebase

2. **Option B: React Native Rewrite**
   - Native performance
   - Better offline/background support
   - More work but more robust

3. **Option C: Progressive Web App**
   - Works today in browser
   - Limited background/mesh capabilities
   - Good for initial onboarding, upgrade later

**Recommendation:** Option C for workshop (works now), Option A for v1.0

## Requirements

### Requirement: Runs Without Server

The application SHALL operate fully without any internet connection or central server.

#### Scenario: Island Mode
- GIVEN a phone with the app installed
- WHEN the phone has no cellular or WiFi internet
- THEN the user can still view local data, create offers/needs, and queue messages
- AND when another mesh node comes in range, data syncs automatically

### Requirement: Installs via Sideload

The application SHALL be installable without Google Play Store.

#### Scenario: APK Distribution
- GIVEN a user with an Android phone
- WHEN they receive the APK via direct transfer, QR code, or mesh share
- THEN they can install and run the app
- WITHOUT needing a Google account or Play Store access

### Requirement: Runs on Old Hardware

The application SHALL run on Android 8+ devices with 2GB RAM.

#### Scenario: Burner Phone Compatibility
- GIVEN a $30 prepaid Android phone from 2018
- WHEN the app is installed
- THEN all core features work acceptably

## Tasks

1. [ ] Set up React Native or Capacitor project wrapping existing frontend
2. [ ] Port SQLite schema to run locally on device
3. [ ] Implement local HTTP server for frontend-backend communication
4. [ ] Package Python runtime (Chaquopy) or rewrite critical services in JS/Kotlin
5. [ ] Implement WiFi Direct mesh discovery
6. [ ] Implement Bluetooth Low Energy fallback
7. [ ] Create APK build pipeline
8. [ ] Test on minimum spec devices
9. [ ] Create sideload distribution mechanism (QR code APK share)

## Dependencies

- Current frontend (React/TypeScript)
- Current backend services (Python/FastAPI)
- DTN Bundle System
- Mesh networking specs

## Risks

- **Python on Android is janky.** Mitigation: Core sync logic may need Kotlin rewrite.
- **Background execution limits.** Mitigation: Foreground service with notification.
- **Battery drain.** Mitigation: Configurable sync intervals.

## Success Criteria

- [ ] APK installs on Android 8+ device
- [ ] App works with airplane mode ON
- [ ] Two phones in proximity sync data via WiFi Direct
- [ ] Core loop (offer/need/match) works entirely offline
