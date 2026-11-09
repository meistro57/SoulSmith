# Multi-Aspect Campaign Sessions & Wandering Mode Foundation

> **THE PLAYER MAY KNOW THE WHOLE STORY. EACH ASPECT KNOWS ONLY THE LIFE THEY HAVE LIVED.**
>
> **THE WORLD MAY SUGGEST WHERE TO LOOK. IT MUST NEVER REQUIRE THE PLAYER TO SURRENDER THEIR PRIVACY OR SAFETY.**

SoulSmith already distinguishes Chronicle truth, personal memory, World Memory, NPC knowledge, and cross-Aspect echoes. Phase 20 makes those distinctions operational during active play, and lays the domain foundation for real-world **WANDERING** play without marrying the model to one map vendor or requiring continuous tracking.

---

## Knowledge layers

Five layers are explicit and enforceable, and none may collapse into another:

| Layer | Meaning | Who sees it |
|---|---|---|
| **Canonical truth** | What the Chronicle records actually happened | The controlling player at campaign scope; never the provider |
| **Player knowledge** | The whole campaign-level view the player is permitted to see | The player (UI/overview) |
| **Aspect knowledge** | What the active playable Aspect has legitimately experienced | The active Aspect only |
| **NPC knowledge** | A consent-safe projection derived from World Memory | The in-world NPC, scoped to their access |
| **World Memory** | Derived cultural belief (legends, songs, inscriptions) | Anyone the visibility rules permit |

An Aspect may feel familiarity only when an existing system legitimately supplies it: Soul Constellation bonds/anchors, Relic Recognition, Probable Paths, World Memory, Relationships/Promises. Raw provider/model memory is never knowledge provenance.

The enforcements:

- `_gather_state` (in `campaign_orchestrator.py`) resolves the **active** Aspect via `active_soul_id(session)` and scopes Seeds, open questions, Threads, Probable Paths, Relics, relationships, promises, World Memories, Memory Objects, and Chronicle events to that Aspect.
- `get_canonical_events_for_soul`, `get_seeds_for_soul`, and `get_open_questions_for_soul` (in `db.py`) are the Aspect-scoped Chronicle/Curiosity queries.
- `compile_aspect_view` / `knowledge_projection` (in `multi_aspect.py`) expose a bounded, inspectable projection including `forbidden_events` — the canonical truth the Aspect is *not* shown.

---

## Multi-Aspect campaign model

A campaign (`campaign_id`) may contain many **playable Aspects**, each registered idempotently in `campaign_aspects`. Each Aspect has independent structured state keyed by its `soul_id` (which is the Aspect name string used across the existing domain tables):

- identity (linked to its Constellation Aspect when one exists)
- viewpoint/location (`viewpoint_location`)
- Chronicle visibility (Aspect-scoped events)
- knowledge (Seeds, questions, Threads, Probable Paths)
- relationships and promises (consent-filtered)
- relic possession/history (`get_or_create_relics_records(soul_id=...)`)
- World Memory exposure and Memory Objects
- current opportunities (evaluated per active Aspect)

A `campaign_sessions` row is campaign-level: `soul_id` records the default/owner Aspect while `active_soul_id` tracks the currently active playable Aspect.

---

## Aspect switching

`switch_campaign_aspect` (`campaign_orchestrator.py`) delegates to `multi_aspect.switch_aspect`:

1. persist the departing Aspect's structured state (it already lives in soul_id-keyed domain tables; switching only persists the viewpoint),
2. load the destination Aspect's state,
3. rebuild `NarrativeContext` from the destination viewpoint on the next `evaluate_opportunities`,
4. recalculate eligible Campaign Opportunities and NPC/world knowledge projection,
5. preserve campaign-level history (transitions/opportunities are never deleted),
6. never leak private/unknown information into the new viewpoint.

Switching is **idempotent**: switching to the already-active Aspect returns `idempotent: true` and records no new `aspect_switches` row. Save/resume is deterministic: `start_or_resume_session` returns the same campaign session and re-asserts the requested active Aspect.

---

## Simultaneously living Aspects

Where campaign/world rules permit, multiple Aspects may exist during overlapping periods. This enables two player-controlled Aspects meeting, one Aspect hearing about another, relationships/promises between Aspects, relic transfer, shared Group Memories, competing perspectives on one event, and one Aspect becoming World Memory during another's lifetime.

Soul Constellation interpretation remains player-controlled; Aspects are not assumed to be reincarnations or sequential lives.

---

## Cross-Aspect encounters and consequences

When two Aspects meet, `resolve_cross_aspect_encounter` (`multi_aspect.py`) returns a **viewpoint-specific projection**. The shared canonical event is one event with participant perspectives, never duplicated contradictory canon. Each Aspect's view is compiled from its own structured state, never from the other Aspect or the player's omniscient view.

Consequences are wired through the existing engines:

- **Relationships/Promises** (`relationship.py`): a promise may be `inherited`/`transferred` to another Aspect only with explicit target provenance; ambiguity stays disputed.
- **Relics**: a promise/relationship entity link with `link_type: "relic"` preserves the relic's provenance chain.
- **Places** (`wandering.py`): an action by Aspect A can leave `place_history` that Aspect B later encounters as a `recurring_location` callback, without B automatically understanding it.

---

## Campaign Orchestrator integration

Phase 17 orchestration now evaluates opportunities at both **campaign** and **Aspect** scope. New candidate builders (`campaign.py`):

- `build_aspect_switch_candidates` — another playable Aspect is a switch target,
- `build_cross_aspect_meeting_candidates` — two Aspects sharing a canonical relationship/bond may meet,
- `build_recurring_location_candidates` — a place with accumulated, visible history may be revisited,
- `build_location_bound_seed_candidates` — a Seed the Aspect holds may be rooted at a remembered place.

New opportunity types: `aspect_switch`, `cross_aspect_meeting`, `recurring_location`, `location_bound_seed`. The orchestrator coordinates eligibility; it never decides metaphysical meaning or merges viewpoints.

---

## WANDERING: real-world play foundation

The discovery loop is:

`MOVE THROUGH WORLD -> DISCOVER PLACE / PRESENCE / PURPOSE -> ENCOUNTER -> CHOICE -> CHRONICLE -> LOCATION REMEMBERS`

A real-world location is context. It does not become narrative canon until an authorized event is committed through the existing systems.

### Place/location model

`places` (in `db.py`, modeled in `wandering.py`) represents persistent SoulSmith places: real-world reference, fictional place, hybrid/interpretive place, region, discovery zone, or event site.

Precise coordinates are stored separately from the player-facing/public representation. `project_place_for_viewer` strips coordinates unless the viewer is the owner in authorized debug mode; private places are reduced to a public label/region.

A place may accumulate Chronicle events, World Memories, relic history, symbols, Seeds, relationships, legendary figures, Gallery/world art, Group Memories, and discoveries by multiple Aspects via `place_history` — this is how **places themselves acquire history**.

### Nearby discovery

`nearby_eligible_places` (`wandering.py`) is a deterministic, bounded contract:

- requires explicit location consent (opt-in),
- discovery radius and approximate proximity (haversine),
- count-based cooldowns and a max result cap,
- previously discovered vs unknown,
- public vs private discoveries,
- campaign-specific vs world/shared discoveries (via `consent_scope`).

A user-requested/current location check is sufficient; continuous background tracking is not required.

### Map/provider abstraction

`map_provider.py` defines a provider interface. Phase 20 ships only the deterministic `MockMapProvider`; a real geocoder can be added behind the same interface without touching the domain model.

### Exploration without grind

Walking/exploration may reveal opportunities, but SoulSmith does not copy walking-distance grind, streak pressure, or urgency. No encounter requires trespassing, dangerous access, distracted driving, or an inaccessible coordinate. Administrators/content systems may mark a place `restricted`/`retired`, which stops new discovery **without deleting** Chronicle history already recorded there.

### Location privacy

Location is personal data:

- explicit opt-in before access (`location_consent`),
- clear purpose per request,
- no continuous tracking,
- minimized stored precision (`precision_level`: fine/medium/coarse),
- configurable retention,
- deletion/revocation support consistent with the existing privacy architecture,
- precise home/private locations are never published by default,
- no player can infer another's private location through API metadata,
- consent before contributing a real-world location to shared/public World Memory.

`submit_location_sample` rejects any sample without the consent grant (HTTP 403), so core play is never blocked by declining location.

### Camera and physical-world interaction

SoulSmith's existing camera/dice capture path remains compatible with Wandering encounters. A future AR layer would render an already-authorized SoulSmith encounter into the camera view rather than use AR output as canonical evidence. Phase 20 does not require AR and does not pretend generic image recognition proves a fictional phenomenon exists.

### Offline behavior

Wandering degrades gracefully: the deterministic/mock gameplay remains fully usable without location services, cached already-authorized opportunities are returned deterministically, and a map/provider failure never corrupts campaign state. Offline play never fabricates a server-authoritative discovery.

### GATHERING and WORLD PULSE compatibility

The place model carries no campaign-authority fields, so a place discovered in Wandering can later host a Gathering or contribute consent-safe public mythology to World Pulse without redesign.

---

## API surfaces

- `GET /api/v1/campaign/{campaign_id}/aspects` — list campaign Aspects,
- `POST /api/v1/campaign/aspects/register` — register a playable Aspect,
- `POST /api/v1/campaign/aspects/switch` — switch active Aspect (idempotent),
- `GET /api/v1/campaign/session/{session_id}/aspect-view` — inspect the active Aspect's knowledge projection,
- `POST /api/v1/campaign/encounters/cross-aspect` — resolve a cross-Aspect meeting,
- `POST /api/v1/wandering/places` / `GET /api/v1/wandering/places` — create/list places,
- `POST /api/v1/wandering/places/retire` — retire an unsafe place,
- `POST /api/v1/wandering/location-consent` / `GET .../location-consent/{soul_id}` — location consent,
- `POST /api/v1/wandering/location-sample` — submit an authorized location sample,
- `GET /api/v1/wandering/nearby` — query nearby eligible Wandering opportunities,
- `POST /api/v1/wandering/discoveries/record` — record a place discovery,
- `POST /api/v1/wandering/place-history` / `GET .../places/{place_id}/history` — place history.

---

## Frontend

The playable Campaign UI (`CampaignView.tsx`) now includes:

- an Aspect selector/switcher with a clear active-viewpoint indicator,
- a Wandering entry point with permission/privacy explanation,
- a mobile-friendly discovery/map shell (nearby opportunities and remembered places),
- graceful no-location mode.

The game remains fully usable when the player declines location permission.

---

## Known v1 limitations

- Map/geocoding is a deterministic mock; no real vendor is wired in.
- No continuous background tracking, real AR overlay, or QR/visual-marker recognition yet.
- Wall-clock cooldowns remain optional; the orchestrator uses deterministic count-based pacing.
- Precise coordinate storage is supported but minimized; retention/auto-deletion policy is represented in the consent record, not enforced by a scheduled job.
- The discovery surface shows only authorized public/remembered content; richer map rendering is deferred.

---

## Tests

`backend/tests/test_multi_aspect_wandering.py` covers the 26 Phase 20 behaviors, including Aspect switching persistence, viewpoint rebuild, knowledge-layer isolation, private Chronicle isolation, cross-Aspect meeting boundaries, promise/relic provenance, NPC knowledge scoping, World Memory distinctness, orchestrator Aspect-scoped opportunities, idempotent switching, save/resume, location consent denial, bounded deterministic nearby discovery, hidden/precise-coordinate non-leakage, place history accumulation, later-Aspect callbacks, location-bound Seed provenance, retired-location safety without deletion, offline non-fabrication, map-failure resilience, camera/dice compatibility, and no campaign-authority leak.
