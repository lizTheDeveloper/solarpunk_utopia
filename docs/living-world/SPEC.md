# Solarpunk Living World — Product and Game Design Specification
**Status:** Draft v0.1 — November 2, 2026
**Scope:** An explorable, federated, real-world community RPG built as a layer on Solarpunk Utopia.
**Initial pilot:** Wild Seeds Ranch (proposed), with Castle Quest and MangoLoop as prospective ecosystem collaborators. Specific organizational roles remain unconfirmed.

## 1. Vision
An inhabited, whimsical pixel-art world where real people appear as characters by consent, actual locations become explorable maps, real projects become quests, learning yields portable skill records, and groups can form persistent parties to improve their communities. The player should be able to answer, joyfully and rapidly: Who's here? What do they know? What are they learning? What's happening soon? What needs doing? Who could we do it with?

**Core fantasy:** We are collaboratively building the world we want to inhabit, and the world visibly changes when we act.

**Product thesis:** The playful frontend makes community life legible and inviting. Solarpunk Utopia's ValueFlows, scheduling, resource coordination, and human-approved agent systems provide real-world infrastructure beneath the game.

## 2. Design pillars
1. **Explorable presence:** Walking a stylized top-down map should be enjoyable even without a task. Landmarks, secret gardens, animals, seasonal decoration, easter eggs and player expression are important gameplay, not optional polish.
2. **Reality is the game engine:** Gardens actually need tending; equipment actually wears; real seasons and events create meaningful change. Never invent food shortages, emergencies or countdowns to force engagement.
3. **Competence is progression:** Reward learning, teaching, teamwork, repair, care work and demonstrable outcomes, not simply hours, spending or popularity.
4. **Whimsy-maxing:** Gentle surprises, environmental storytelling, expressive avatars, playful titles, discovery and gifts enrich the world without coercive hooks.
5. **Portable belonging:** A person can join many communities, retain consented skills and accomplishments, and participate in cross-site parties.
6. **Local sovereignty:** Each site controls membership, visibility, verification rules, data disclosure and its playable map.
7. **Human agency:** AI agents propose useful matches and schedules; consequential real-world changes always require appropriate human approval.

## 3. Who it serves
- Resident: see daily activity and neighbors; propose work; contribute without a bureaucratic dashboard.
- Volunteer/visitor: discover events, beginner quests, onboarding and people willing to mentor.
- Teacher/mentor: offer workshops, review evidence and award skill endorsements.
- Steward/organizer: publish needs and events, manage permissions, approve quests and observe maintenance backlogs.
- Remote ally: make contributions, join learning and planning parties without pretending to be physically onsite.
- New community organizer: create an independent site and connect it to other communities.

## 4. Main play experience
### 4.1 First arrival
Player enters an explorable outdoor arrival plaza at a fictionalized/stylized Wild Seeds map. There is an optional onboarding guide (NPC or community-authored sign), an events board, a community needs board, an animated skills garden, and a gathering spot. No real person's presence is revealed without their explicit opt-in.

### 4.2 The daily loop
EXPLORE -> DISCOVER (people/events/needs) -> CONNECT (talk, join a party, ask for mentoring) -> DO (offline or online contribution) -> VERIFY (peer/mentor/steward as appropriate) -> CELEBRATE (world visibly improves, participant receives evidence of learning/contribution) -> RETURN BY CHOICE.
No punitive daily streaks, artificial hunger meters, or XP debt.

### 4.3 The community floor
A legible, fast-updating public area offering:
- Who is available **now**, shown only by explicitly enabled presence; distinguish onsite, online, and available-to-help.
- What people can **teach** versus what they want to **learn**, self-declared and separately endorsed.
- Today's tasks: urgency based on authentic deadlines, urgency explanations, skill/safety prerequisites, approximate effort, accessibility and needed roles.
- Upcoming events with timezone, location, capacity, RSVP and accessibility notes.
- Active parties and open role slots, with clear join/request semantics.
- Real-world changes since last visit: planted beds, completed repairs, workshops, shared meals and community-created artworks.
If no live information is available, display last-updated timestamps instead of manufacturing activity.

### 4.4 Explorable physical map
- Top-down / isometric-friendly tile system, avatars, navigation, interactable landmarks, accessible keyboard/touch controls.
- Zones: welcome plaza, commons, garden, workshop, kitchen, learning hall, water and energy systems, event spaces; only actual and permitted spaces are made visible in site deployments.
- Interactive objects open structured real-world information: garden plot -> planting plan and care tasks; solar rig -> educational guide and maintenance; noticeboard -> quests; stage -> events.
- World edits and user-generated decoration may be proposed by players; moderator approval and rollback for shared spaces.
- Representation must not imply unrestricted physical access. Sensitive rooms and living quarters are hidden by default.
- Prefer stylized maps, not accurate security-sensitive layouts or exact locations of valuable equipment.

## 5. Core game systems
### 5.1 Profiles, skills and consent
Character = public nickname, avatar, optional bio and pronouns, interests, skills (learning, practiced, endorsed), teaching availability, project history, affiliated communities and privacy settings. Identity and presence controls are independent. A profile is never created for another person without consent.

### 5.2 Quests grounded in real work
Quest fields: sponsor community, objective, real-world beneficiary, location/remote eligibility, roles and capacity, prerequisites, equipment, estimated effort, due date if genuinely needed, risk tier, evidence/verification process, accessibility, state and audit trail.
States: proposed -> approved -> open -> in progress -> awaiting verification -> completed / canceled.
Example: 'Build the Solar Commons' includes site-assessed requirements, qualified electrical oversight and educational documentation; it is NOT an authorization for an unqualified player to do electrical work.
Work may also be recognized without formal quests; keep friction low.

### 5.3 Parties
An organizer opens a party for a quest or event. Members can join/request, take roles, coordinate through opt-in messaging and resolve availability. Parties can span communities. Members need not earn identical XP; contributions may be documented in varied ways.

### 5.4 Progression
Three distinct tracks: **learning evidence** (what one has demonstrated), **contributions** (what one helped accomplish), **community progress** (what the place now sustains). XP is an optional celebratory representation, not a labor market, credit score, safety certification, entitlement, or governance vote.
Avoid global leaderboards. Offer cooperative milestones and context-rich achievements. Contributions such as mentoring, cleaning, accessibility work, facilitation and emotional labor must be recognized without surveillance.

### 5.5 Living ecology and maintenance
Genuine seasonal constraints, plant health, resource lifespan, weather and maintenance generate naturally recurring work. Actual ecological observations take precedence over simulation. Missing data remains unknown, never simulated as fact. The world can optionally display an explicitly labeled illustrative ecological layer when data is unavailable.
Failure becomes learning, recovery and community resilience, not punishment.

### 5.6 Events and workshops
Calendar events appear in-world as visual objects (signs, stages, gathering circles). Registration and RSVP integrate with existing scheduling where supported. Learning outcomes and endorsements require explicit assessment rather than automatic attendance XP.

### 5.7 Federation
Community identity and authorization remain local. Users may carry selectively disclosed achievements across communities. Federation supports discovery of public quests/events, invitations to cross-community parties, and resource/knowledge exchange, subject to local approval and privacy policy.
Offline-first sync is eventual; display stale states and reconcile conflicts safely.

## 6. Ethical Octalysis design
Use the eight drives as a design checklist, **not** as a mandate for dark patterns:
1. **Epic meaning:** visible contribution to ecological regeneration and community flourishing.
2. **Development/accomplishment:** demonstrated skills, progress stories, collaborative achievements.
3. **Creative empowerment/feedback:** site decoration, experimental garden plans, collaboratively authored quests, useful feedback.
4. **Ownership/possession:** care and stewardship of projects, persistent personal creations; avoid enclosing commons as virtual property.
5. **Social influence/relatedness:** parties, mentoring, hospitality, shared rituals, peer celebration; no compulsory social exposure.
6. **Scarcity/impatience:** ONLY real-world limited capacity, seasonal windows, material constraints, and genuine event seats; no manufactured FOMO.
7. **Unpredictability/curiosity:** harmless secrets, wildlife, seasonal changes, discovery and player-generated surprises; not variable-ratio rewards designed to encourage compulsion.
8. **Loss/avoidance:** accurate warnings for genuine spoilage, plant care and maintenance; no streak loss, shame, exaggerated crises, or threats to belonging.
**Acceptance rule:** Every potentially dark-drive mechanic must correspond to a real, explainable constraint or be removed.

## 7. Relationship to Solarpunk Utopia architecture
Do **not** rewrite the underlying commons platform or assume all existing endpoints match game needs.
Proposed layers:
- Game client: map renderer, avatar interactions, cards, events, accessibility and responsive mobile UX.
- Game application service: characters, maps, zones, quests, parties, skill records, achievements, presence, consent and permissions.
- Integration adapters: ValueFlows offers/needs and economic events; Work Party Scheduler; Education Pathfinder; Permaculture Planner; agent proposal and approval workflows; distributed/offline sync.
- Community gateway: site-specific membership, publication settings and federation permissions.
All real-world state-changing actions must be mediated by existing permission/approval policies.

## 8. Suggested domain entities
Community(id, owner, federation_policy, timezone); Zone(id, community_id, visibility, approximate_geometry); Landmark(id, zone_id, kind, external_ref); Character(id, pseudonym, privacy); Membership(character_id, community_id, role, visibility); Presence(character_id, community_id, state, expires_at, consent); Skill(id, taxonomy, safety_class); SkillClaim(character_id, skill_id, level, evidence, verifier, disclosure); Quest(id, community_id, objective, real_world_ref, risk, approvals, status); QuestRole(quest_id, skill, capacity); Party(id, quest_id, visibility); PartyMember(party_id, character_id, role); Event(id, community_id, start, timezone, capacity); Contribution(id, source_event, actor, evidence, verification); Decoration(id, zone_id, moderation_state); FederationGrant(source, target, scope, expiry).
Use opaque IDs, audit trails and revocation; never infer exact physical presence from game position.

## 9. Initial acceptance scenarios
- **Presence:** Given no presence consent, when a stranger opens the map, the person is not identified as onsite.
- **Skills:** Given a visitor lists interest in solar, when they browse people, self-declared interest is distinguishable from endorsed competence.
- **Quest:** Given an approved garden maintenance need, when a player joins a party and completes the task, an authorized verifier can mark completion and the related real-world resource record updates once.
- **Safety:** Given electrical installation prerequisites, when an unqualified player attempts to claim a hazardous role, the system blocks unsupported independent work and offers an educational role.
- **Events:** Given an event tomorrow, when a visitor enters the commons, they see correct timezone, capacity and RSVP state.
- **Ecology:** Given a plant has no sensor/inspection data, when the player inspects it, its health is shown as unknown, not fabricated.
- **Federation:** Given consent to share a skill endorsement, when joining a different community, the endorsement appears with issuer and evidence; revoking consent removes its visibility.
- **Offline:** Given a disconnected community, when reconnecting, recorded contributions deduplicate and conflicting real-world approvals require human reconciliation.
- **Delight:** Given a first-time visitor with no quest, they can explore, discover at least one playful interaction and understand how to participate within five minutes.

## 10. Paid residency as a bounded prototype
Proposed pilot outcome: a playable Wild Seeds common area with 3-5 interactive landmarks, a consent-based people/skills board, events board, live project quests, party joining, and at least one real workshop-to-verified-achievement flow (e.g., a supervised solar education quest). Provide onboarding for organizers, instrumentation with privacy protections, and handoff documentation.
**Not included without separately agreed scope:** full property digital twin, real-time tracking, property access control, comprehensive electrical infrastructure management, automatic legal certification, production multiplayer scaling, all communities federated at once, hardware installation, continuing operations.
Milestones: discovery and permissions -> design approval -> integration spike -> playable vertical slice -> supervised residency playtest -> findings and roadmap.
Success measures: voluntary onboarding, users finding a useful quest, successful party formation, completed/verified real contributions, participant understanding of who can help, event discovery, accessibility and trust.

## 11. Open decisions and risks
- Name and brand; relationship to Reclaim City, Octalysis and original art/IP.
- Exact hosting, data controller, privacy notices, retention and consent for resident profiles.
- Licensing of newly funded development and ownership of game art, content, datasets and platform improvements; existing repo is MIT.
- Residency fee, travel, lodging, curriculum scope, deliverables and acceptance sign-off.
- Multiplayer engine/asset pipeline selection, accessibility budget and moderation staffing.
- How site leaders validate contributions fairly without turning reputation into social hierarchy.
- How real and illustrative world data are differentiated in UI.
- Specific roles of Wild Seeds Ranch, Castle Quest, MangoLoop and their founders.

## 12. Next design increment
Produce detailed wireflows for the arrival plaza, people-and-skills pavilion, daily needs board, quest/party screen and event stage; then an API contract and proof-of-integration against actual existing service endpoints.
