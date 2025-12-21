# Proposal: Conscientization Agent

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** FULLY IMPLEMENTED
**Completed:** 2025-12-21
**Note:** Backend agent implementation complete. Now queries real ValueFlows database: infers learners from skill NEED listings, finds mentors from skill OFFER listings, detects culture circles from grouped needs. Works with existing database schema.
**Complexity:** 2 systems

## Problem Statement

Users often consume content passively (e.g., late at night) when they lack the energy to act immediately. They might be inspired but blocked by not knowing *what resources they need* or *who can show them how*. We need to bridge the gap between "watching a video" and "putting hands on the thing" without demanding immediate high-energy effort.

## Proposed Solution

A **Conscientization Agent** that lowers the barrier to entry by identifying **Practical Next Steps**.

1.  **"What Does It Take?" (Resource Parsing)**: The agent analyzes the content and generates a **Resource Request** list (e.g., "To do this, you need a soldering iron and 3 LEDs"). The user can click "Request" to ask the network for these items.
2.  **Co-Investigator Match**: "Who can explore this with me?" The agent finds nearby nodes who are masters of this topic and effectively "Co-Investigators" (Teachers who learn).
3.  **Event Surface**: Highlights upcoming "Hands-On" workshops or "Let's Get Started" classes relevant to the content.

## Requirements

### Requirement: Resource Gap Identification

The system SHALL parse content to identify necessary tools/materials and check if the user has them.

#### Scenario: The Late Night Project
- WHEN User watches "Hydroponics 101" at 11 PM
- THEN Agent shows sidebar: "You have the pump, but need nutrients. Click to Request nutrients from the Heap."

### Requirement: Mentor Connection

The system SHALL identify local experts willing to teach the subject.

#### Scenario: Finding a Teacher
- WHEN User reads "Welding Basics"
- THEN show: "Auntie Maria (0.5km away) teaches Welding on Tuesdays. Ping her?"

#### Scenario: Study Group Auto-Match
- WHEN 3 users read "Marx in the Data Center" within 24h
- THEN Agent proposes: "A Culture Circle on Data Sovereignty could form. Interest?"

### Requirement: Praxis Linking

The system SHALL link information to potential physical actions.

#### Scenario: From Theory to Action
- WHEN User reads "Water Filtration Guide"
- THEN show sidebar: "Open Tasks: 3 neighbors need help fixing filters." (Contextual matching).

### Requirement: Culture Circle Formation

The system SHALL suggest connections between users learning the same topics.

#### Scenario: Study Group Auto-Match
- WHEN 3 users read "Marx in the Data Center" within 24h
- THEN Agent proposes: "A Culture Circle on Data Sovereignty could form. Interest?"

## Dependencies

- **File Chunking System**: To attach prompts to file metadata.
- **Briar/Manyverse**: To host the Culture Circles.

## Risks

- **Annoyance**: Users might just want the file. Mitigation: "Emergency Mode" bypasses all prompts.
- **Bias**: Who writes the questions? Mitigation: Questions are open-source and community-curated.

## Alternatives Considered

- **Wiki**: Passive consumption. Rejected.
- **Quiz**: Banking model (testing retention). Rejected.
