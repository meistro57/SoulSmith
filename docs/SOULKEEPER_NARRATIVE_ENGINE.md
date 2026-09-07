# Soulkeeper Narrative Engine & Provider Runtime

> **DOMAIN SYSTEMS DECIDE WHAT IS TRUE. THE SOULKEEPER DECIDES HOW IT IS TOLD.**

Phase 18 replaces the Phase 17 campaign narrative mock with a real provider
runtime that turns approved, provenance-backed campaign state into vivid scenes,
NPC dialogue, atmosphere, connective prose, and player-facing narration — while
preserving every existing canon, consent, provenance, Guardian, and
domain-authority boundary.

```
CANON + OPPORTUNITY + KNOWLEDGE PROJECTION + CONSENT FILTER
  -> NARRATIVE CONTEXT -> PROVIDER -> NARRATIVE GUARDIAN -> PLAYER-FACING STORY
```

Never:

```
MODEL PROSE -> NEW CANON
```

---

## Authority boundaries

The Soulkeeper may generate:

- scene description
- environmental detail
- dialogue
- sensory framing
- emotional atmosphere tied to explicit scene state
- transitions between structured beats
- evocative questions
- descriptions of uncertainty
- summaries of already-committed consequences
- alternate phrasings of the same authorized opportunity

The Soulkeeper may **not** invent:

- prior Chronicle events
- canonical relationships or promises
- StoryMarks
- relic ownership/history/abilities/awakening
- Thread truth
- Integration Events
- cross-Aspect relationships
- participant presence
- locations
- dates/ages/durations not supplied by canon
- private facts
- NPC omniscient knowledge
- World Memory claims outside the projected perspective
- visual facts that conflict with locked historical references

If narration needs a fact not present in `NarrativeContext`, it should omit or
phrase around the gap rather than guess.

---

## NarrativeContext

`NarrativeContext` (`backend/app/campaign.py`) is the single, inspectable,
consent-safe input to every provider. It carries only the fields needed by
narration:

- campaign/session ids
- active Aspect / current viewpoint
- authorized scene facts (`allowed_claims`)
- current opportunity type
- relevant source evidence (provenance links)
- visible participants and their knowledge boundaries
- already-canonical, visible relationships/promises
- current relic state and permitted relic knowledge
- Seeds/Questions/Symbols that may be echoed
- Thread evidence only when the current opportunity allows it
- World Memory / NPC knowledge projection where applicable
- player-visible consequences and allowed uncertainty
- tone/style hints
- art-direction references (visual continuity)
- forbidden/private facts (never exposed)
- provenance ids for every meaningful claim
- explicit structured scene continuity (never raw chat history)
- correction instructions appended by the runtime during retry

The provider never receives the entire database simply because it exists.

### Scene continuity

Continuity is compiled from SoulSmith-owned structured state (current location,
current participants, prior transition summary, recent visible actions), never
from provider chat history. Save/resume remains reconstructible from structured
state alone.

---

## Provider abstraction/runtime

The runtime lives behind the existing `CampaignNarrativeProvider` abstraction
(`backend/app/campaign_provider.py`). Two providers are wired:

- `MockCampaignNarrativeProvider` — deterministic, offline, first-class for
  tests and local development.
- `OpenAICompatibleCampaignProvider` — a real, configurable provider backed by
  any OpenAI-compatible chat-completions endpoint (local or remote). No vendor
  SDK is hard-wired.

`NarrativeRuntime` (`backend/app/narrative_runtime.py`) wraps a provider into one
validated result, managing selection, timeout, bounded retry, validation, safe
deterministic fallback, and generation metadata.

Configuration (backend env vars):

| Variable | Default | Meaning |
|---|---|---|
| `SOULSMITH_CAMPAIGN_PROVIDER` | `mock` | `mock` or `openai_compatible` |
| `SOULSMITH_NARRATIVE_BASE_URL` | empty | OpenAI-compatible base URL |
| `SOULSMITH_NARRATIVE_API_KEY` | empty | optional bearer key |
| `SOULSMITH_NARRATIVE_MODEL` | `local-model` | model name |
| `SOULSMITH_NARRATIVE_TIMEOUT_SECONDS` | `30` | per-call timeout |

Provider selection respects deployment policy; the API selection endpoint is
advisory and never exposes secrets.

---

## Structured output

Provider output is structured enough for UI control and validation, not a
screenplay DSL. `NarrativeOutput` (`backend/app/campaign.py`) includes:

- `prose` / `scene_prose` — primary scene narration
- `soulkeeper_narration` — explicit Soulkeeper voice
- `dialogue` — attributable lines (`speaker`, `line`, `kind`)
- `question` — player-facing prompt
- `flavor_lines` — optional atmosphere/connective lines
- `presentation_cues` — optional presentation hints
- `referenced_provenance_ids` — provenance backing the claims
- `declared_uncertainty` — explicit uncertainty

Malformed structured output is rejected gracefully (provider failure, no canon
mutation).

---

## Narrative validation (Guardian)

`narrative_guardian.py` runs a deterministic validation stage for real provider
output before it reaches the player. It is distinct from the Visual Canon
Guardian and the World Memory Guardian, but follows the same philosophy.

Checks include:

- referenced source ids exist and are allowed
- no unknown participant/entity asserted
- no invented prior event
- no undeclared canonical fact
- no private/forbidden fact leak
- no invented date/age/duration
- no invented relic ability
- no Thread truth promotion
- no invented Integration Event
- cross-Aspect / perspective boundaries preserved
- no authoritative psychological/spiritual conclusions about the player

Outcomes: `pass`, `retry` (with correction instructions), or `block` (fallback).

---

## Retries and fallbacks

- Validation `retry` re-runs the same authorized context with explicit
  correction instructions appended to `context.corrections`. Context is never
  widened; rules are never weakened.
- Retries are bounded (`DEFAULT_MAX_RETRIES = 2`).
- On exhaustion or `block`, the runtime falls back to the deterministic mock.
  The fallback never fabricates new canon.
- Provider exceptions (timeout, network, malformed output) return a graceful
  generation failure while the already-valid campaign transition is preserved.
  Canon is never corrupted.

---

## Soulkeeper style layer

`narrative_style.py` holds a fact-free presentation style (`NarrativeStyle`):
prose density, dialogue frequency, tone, mystery level, humor allowance, sensory
richness, scene length, Soulkeeper presence, and plain-language mode. Style
settings never add information unavailable in the structured context.

Direction remains: curiosity before explanation, evidence before
interpretation, agency without doctrine.

---

## NPC knowledge and dialogue

NPC dialogue is compiled from the NPC's own Phase 16 knowledge projection
(`project_npc_knowledge`), never from the player's omniscient context. NPCs can
be confidently wrong when World Memory supports it — as folklore, not canon.

---

## Multi-perspective narration

Where Group Memories, competing World Memories, or cross-Aspect material is
present, narration preserves perspective boundaries: "Mira remembers...",
"The village says...", "The relic's inscription suggests...". Different
viewpoints may coexist without reconciliation.

---

## Player-choice phrasing

The narrative engine may phrase choices but never changes the structured choices
supplied by the orchestrator. Choice/action ids, eligibility, and known
consequences are preserved; hidden outcomes are never revealed; no tempting
fourth option is added.

---

## Prompt/template versioning

System instructions/templates are versioned with
`NARRATIVE_TEMPLATE_VERSION`. Every generation records provider, model, template
version, generation timestamp, transition/session id, retry count, and
validation outcome in the `narrative_generations` table. Changing a template
never rewrites prior canonical events or historical generated prose records.

---

## Context and cost discipline

The context compiler gathers the smallest evidence set needed for the current
opportunity. Diagnostics expose source count and an approximate token estimate
(`context_stats`), never private narrative content or secrets.

---

## API

- `GET /api/v1/campaign/narrative/status` — provider status/capabilities
- `POST /api/v1/campaign/narrative/select` — advisory provider selection
- `POST /api/v1/campaign/narrative/preview-context` — authorized-debug preview
  of a compiled `NarrativeContext`
- `GET /api/v1/campaign/opportunities/{id}/narrative` — generation metadata and
  validation report
- `POST /api/v1/campaign/opportunities/{id}/regenerate` — re-voice phrasing
  without changing campaign/domain state

---

## Offline/local operation

The deterministic mock remains available and is the default. The runtime is
designed so a local OpenAI-compatible (or other) backend can be configured
without changing campaign logic. Internet connectivity is never a requirement
for the deterministic tests.

---

## Known v1 limitations

- `relationship_callback` and `promise_consequence` opportunities still lack a
  dedicated relationship/promise data model (roadmap priority #2).
- The real provider is validated structurally and via the narrative Guardian,
  but prose-quality heuristics (not truth boundaries) remain coarse.
- Context token estimation is a rough heuristic, not a tokenizer.
