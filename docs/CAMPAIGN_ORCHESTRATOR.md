# Campaign Orchestrator

> **THE ORCHESTRATOR DECIDES WHAT GETS AN OPPORTUNITY TO ACT NEXT. IT DOES NOT DECIDE WHAT THE PLAYER'S STORY MEANS.**

Phase 17 turns SoulSmith's Phase 0-16 subsystems — canonical rolls, Chronicle
provenance, Curiosity, Threads, Soul Constellation, Probable Paths, Relic
Recognition, Convergence, reflection, portraits, Memory Objects, Chronicle
Paintings, Group Memories, Living Biography, Art Director/World Gallery, and
World Memory/Legendary Figures — into one coherent, continuous, playable loop.

This document describes the orchestrator's authority boundaries, opportunity
model, deterministic eligibility, pacing, session lifecycle, reaction pipeline,
callback provenance, cross-Aspect behavior, recognition/rejection semantics,
Integration Events, the relic loop, the NPC/world reaction loop, narrative
provider boundaries, save/resume idempotency, observability, the North-Star
scenario, and known v1 limitations.

---

## Authority boundaries

The orchestrator coordinates. It never duplicates domain logic.

| Concern | Owned by | Orchestrator role |
|---|---|---|
| Numeric roll contract & grammar | `grammar.py` | Hands the existing interpreted roll through unchanged. |
| Scene outcome rules | `rules.py` | Delegates via the existing `/scenes/resolve` path. |
| Chronicle persistence & provenance | `db.py`, `scene_events` | Commits events through the existing roll/resolve path, then reads them. |
| Seeds, Questions, Local Threads, Integration | `curiosity.py`, `db.py` | Surfaces echo/integration *opportunities*; delegates the actual mutation. |
| Relic stages & awakening | `relics.py` | Surfaces relic-memory and awakening *candidates*; never awakens directly. |
| Soul Constellation & cross-Aspect bonds | `constellation.py` | Surfaces passive echoes; never grants omniscient knowledge. |
| Probable Paths | `probable_paths.py` | Surfaces noncanonical echoes; never promotes them to canon. |
| World Memory & NPC knowledge | `world_memory.py` | Projects scoped NPC knowledge; never exposes raw Chronicle state. |
| Group Memories | `group_memories.py` | Surfaces consent-visible callbacks; never rewrites member perspectives. |
| Visual/art eligibility | visual memory, paintings, gallery | Surfaces eligibility cues; never generates or approves art. |
| Narrative prose | provider abstraction | Receives a consent-safe `NarrativeContext`; chooses wording only. |

**Invariants**

1. Existing domain systems remain authoritative for their own rules.
2. Player agency outranks pacing convenience.
3. Canonical changes pass existing provenance/validation rules.
4. Callbacks cite real Chronicle evidence; no invisible model memory.
5. Cross-Aspect knowledge respects what the character can plausibly know.
6. Seeds/mysteries may remain unresolved indefinitely.
7. Refusing an interpretation is always valid and never punished.
8. There is no hidden engagement optimizer.
9. The loop is deterministic and offline (no external AI/GPU required).

---

## Opportunity model

`CampaignOpportunityModel` (`backend/app/campaign.py`) is the structured unit the
orchestrator produces. Each opportunity carries:

- a stable `opportunity_id` and `session_id`;
- `opportunity_type` (bounded, extensible);
- `eligibility_rule` (human-readable, deterministic);
- `source_evidence` (typed provenance links: `source_type` + `source_id`);
- `involved_entities`;
- `visibility_scope` (consent scope);
- `urgency_class` and `participation` (`optional` / `passive` / `player_triggered`);
- `cooldown_key` and `lifecycle_state`;
- `domain_action` + `domain_action_payload` (what the domain system will do when selected);
- `reasoning`, `narration`, `narration_source`, timestamps.

**Opportunity types** (extensible but bounded):

`new_encounter`, `seed_echo`, `recurring_symbol`, `unresolved_question_callback`,
`relationship_callback`, `promise_consequence`, `relic_memory`,
`relic_awakening_candidate`, `probable_path_echo`, `cross_aspect_echo`,
`npc_historical_reaction`, `group_memory_callback`,
`world_memory_legend_encounter`, `integration_candidate`, `recognition`,
`reflection_prompt`, `chronicle_painting_eligibility`.

The orchestrator only emits a type when a deterministic eligibility rule exists
for it.

---

## Deterministic eligibility before narration

Eligibility is computed from structured state *before* any prose is generated.
Each eligibility builder (`build_*_candidates` in `campaign.py`) takes only
structured records and returns a candidate spec or `[]`. For example:

- `Seed exists + not retired + cooldown satisfied -> seed_echo`
- `Remembered relic + required Thread recognized -> relic_awakening_candidate`
- `Public remembered World Memory about another subject -> npc_historical_reaction`
- `Local Thread reached pattern_recognized -> integration_candidate` / `recognition`

A model/LLM may never decide that a canonical promise, relationship, relic
history, Thread, or cross-Aspect connection exists merely because it makes a
better scene.

---

## Pacing

Pacing is lightweight, inspectable, and count-based (not wall-clock), so it is
deterministic and offline-testable.

- Each opportunity type has a `cooldown_window` in `COOLDOWN_WINDOW`.
- After an opportunity is resolved/rejected/postponed/hidden, its `cooldown_key`
  becomes "hot" for that window and is not re-offered.
- `new_encounter` has window 0 and is always available.
- Silence is a valid outcome: if nothing is eligible, the evaluator returns
  `silence: true`.

The system can say, effectively: *"Nothing needs to echo right now. Let the
current scene breathe."* It never infers hidden player psychology to tune pacing.

---

## Session lifecycle

`POST /api/v1/campaign/session` starts or resumes a `CampaignSession` (idempotent
per `campaign_id` + `soul_id`). A session can then:

1. load campaign/Aspect/Constellation context;
2. evaluate eligible opportunities (`POST /api/v1/campaign/opportunities/evaluate`);
3. present/resolve an encounter through the existing canonical dice path;
4. interpret the roll through its versioned grammar;
5. resolve player choice through the existing `/scenes/resolve`;
6. commit the event through the orchestrator (`POST /api/v1/campaign/commit`);
7. let each subsystem react;
8. evaluate new Seeds/Threads/relic/callback eligibility;
9. produce derived artifacts when appropriate (via existing domain endpoints);
10. read a concise aftermath (`GET /api/v1/campaign/session/{id}/aftermath`).

Not every encounter requires every stage.

---

## Reaction pipeline

After a canonical event is committed, `commit_canonical_event` runs an explicit
reaction pipeline. Each subsystem returns a structured result:

- `no_action`
- `candidate_created`
- `state_updated`
- `player_review_required`
- `future_opportunity_scheduled`

Results are collected into an auditable `CampaignTransition` (and per-subsystem
`CampaignReaction` rows). A failure in a derived/noncanonical subsystem yields a
`no_action` result with an error detail and never rolls back valid canonical
history. The Chronicle itself always records `state_updated` for the committed
event.

---

## Callback provenance

Every callback retains provenance. For an NPC reacting to another Aspect's
promise, the system can show:

1. the original promise/event (source Memory Object / Chronicle event);
2. the originating Aspect;
3. how the current NPC/world gained access (World Memory subject + visibility +
   NPC knowledge projection);
4. intermediate World Memory/relic/relationship/Constellation evidence;
5. the current callback event.

`GET /api/v1/campaign/transitions/{id}/provenance` and
`GET /api/v1/campaign/opportunities/{id}/inspect` expose this. No callback relies
on invisible model memory.

---

## Cross-Aspect behavior

The orchestrator surfaces recurring symbols, relic familiarity, displaced
consequences, inherited promises, legends of another Aspect, and shared
Deep-Thread evidence through the existing Soul Constellation and World Memory
architecture. The current Aspect never receives omniscient knowledge
automatically; cross-Aspect echoes carry only the evidence a bond/anchor/world
memory authorizes. The player may recognize a connection before the character
does, and that distinction is preserved.

---

## Player recognition and rejection

When enough evidence exists for a Local Thread or cross-Aspect pattern, the
orchestrator surfaces a `recognition` opportunity. The player may:

- `recognize`
- `reject`
- `rename`
- `reinterpret`
- `postpone`
- `hide`

Rejection/postponement/hiding never mutates canonical Thread state, never
punishes the player, and never secretly re-injects the interpretation as fact.

---

## Integration Events

An Integration Event requires actual Chronicle-backed evidence that the player
responded differently to a recurring pattern (a Local Thread with status
`pattern_recognized`). The orchestrator surfaces the `integration_candidate`;
the existing Integration system (`execute_integration_event`) decides validity.
Successful integration may trigger Thread state change, relic awakening,
relationship change, or new Chronicle evidence — never a generic XP layer.

---

## Relic loop

The orchestrator supports the full chain without claiming authority over
awakening:

`relic encountered -> recognition candidate -> remembered promise/history ->
repeated contextual echo -> player choice -> Integration evidence ->
awakening candidate -> Relic Recognition validation -> canonical relic change`

`relic_awakening_candidate` is surfaced when a `Remembered` relic's required
Thread is recognized. The orchestrator never awakens the relic; the existing
`POST /api/v1/relics/attune-narrative` endpoint performs the canonical change.

---

## NPC/world reaction loop

NPC reactions use World Memory and Phase 16 NPC-knowledge projection. The
orchestrator builds an `NPCKnowledgeRequest` from the World Memory's own
culture/era and projects only the knowledge the NPC could plausibly hold. A
non-matching culture/era/access yields `no_action` (no reaction); a legitimate
match yields deterministic narration that cites the World Memory source.

---

## Narrative provider boundaries

Model-generated narration (when used) sits behind `CampaignNarrativeProvider`
(`campaign_provider.py`), mirroring the Biography/World Memory provider pattern.
The provider receives a consent-safe `NarrativeContext` containing only facts
already authorized by deterministic systems. It may choose wording, tone,
sensory detail, and connective prose. It may not:

- create new canonical relationships;
- invent prior events;
- declare Threads true;
- create unearned relic abilities;
- invent cross-Aspect connections;
- reveal private/unknown world information;
- override a player's rejection.

The deterministic mock (`soulsmith-mock-campaign-v1`) is the default; provider
failure never invents fallback canon.

---

## Save/resume and idempotency

- Sessions, opportunities, and transitions are persisted in SQLite.
- Replaying `commit` for the same event returns the existing transition
  (`idempotent: true`) and never duplicates a canonical event.
- Replaying `resolve` for the same opportunity returns the prior transition and
  never re-applies a domain mutation (a seed echoes exactly once).
- Resume reconstructs state from persisted structured rows, never from model
  conversation memory.

---

## Observability

Each transition records a stable `transition_id`, `systems_invoked`, `outcomes`,
`canonical_change`, `provider_failure`, and `rejected_invalid_transition`.
Opportunity inspection exposes the eligibility rule, source evidence, consulted
systems, cooldown, consent scope, and narration source. Private narrative/
reflection content is never logged.

---

## North-Star scenario

`backend/tests/test_campaign_orchestrator.py::test_north_star_end_to_end` runs the
roadmap's target sequence deterministically and offline:

1. create a fresh campaign and first Aspect;
2. encounter a symbol and record it canonically;
3. echo the symbol later through the Curiosity system;
4. introduce a relic with historical significance;
5. surface a relic memory the current Aspect did not personally create;
6. create/load another Aspect with a canonical promise;
7. make that promise available to the world through legitimate provenance;
8. project appropriate knowledge to an NPC and have the NPC react;
9. accumulate Chronicle evidence for a recurring Thread;
10. surface a recognition opportunity and let the player recognize;
11. validate an Integration Event through the existing Integration system;
12. trigger a relic-awakening candidate and validate it through Relic Recognition;
13. persist the resulting Chronicle/Thread/relic consequences;
14. prove every callback is traceable to its source evidence.

---

## Known v1 limitations

- Only the deterministic mock narrative provider is wired; a real LLM provider
  would be added behind the same `CampaignNarrativeProvider` interface.
- `relationship_callback` and `promise_consequence` opportunity types are
  recognized but not auto-generated (they await a dedicated relationship/promise
  data model); the NPC promise-reaction path is covered via World Memory.
- Cooldowns are count-based, not wall-clock-based.
- Campaign sessions are keyed by `campaign_id` + `soul_id`; multi-Aspect
  simultaneous sessions within one campaign are deferred.
- Orchestrator state is separate from canonical history and never migrates it.
