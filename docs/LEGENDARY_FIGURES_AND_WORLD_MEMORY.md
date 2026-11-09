# Legendary Figures & World Memory (Phase 16)

> **HISTORY MAY BECOME LEGEND. LEGEND MUST NEVER BECOME HISTORY BY ACCIDENT.**

> History records what happened. Memory records what people carried forward.
> Legend records what survived the telling. **The Chronicle remembers the difference.**

SoulSmith Phase 16 turns preserved canonical history into persistent in-world
cultural memory: legends, monuments, books, festivals, renamed places, inherited
relic stories, memorials, statues, songs, oral traditions, archives, and NPC
knowledge that can survive long after the original participants are gone.

This document is the authoritative description of the World Memory system.

---

## 1. Canon vs cultural memory

| Concept | Authoritative? | May drift? | Mutates canon? |
|---|---|---|---|
| Chronicle / Memory Object / Group Memory / Living Biography / approved visual history | Yes | No | Never by World Memory |
| World Memory (legend, song, monument, rumor, …) | No — derived interpretation | Yes, explicitly | Never |

The pipeline is:

```
CANONICAL HISTORY -> WORLD MEMORY COMPILER -> CULTURAL MEMORY ARTIFACTS -> IN-WORLD PRESENCE
```

It is **never**:

```
LEGEND / RUMOR / MONUMENT / SONG -> RETROACTIVE CANON
```

## 2. World Memory model

A `WorldMemory` is a persistent, derived record (`world_memories` table) with:

- stable `memory_id`,
- subject entity/event (`subject_entity_type`, `subject_entity_id`),
- source links (`world_memory_source_links` — normalized provenance rows),
- culture/faction/community/region perspective,
- era/time context,
- memory form,
- interpretation type (truth distance),
- declared deviations (`world_memory_deviations`),
- visibility/publication state,
- in-world placement (`world_memory_placements`),
- memory state (`world_memory_state_history`),
- version number and created/updated timestamps.

World Memory never mutates its source records.

## 3. Memory forms

Structured forms (extensible without becoming arbitrary free text):

`legend`, `historical_account`, `folk_tale`, `rumor`, `oral_tradition`,
`song_ballad`, `inscription`, `memorial`, `monument_statue`,
`displayed_artwork`, `archival_document`, `festival_tradition`,
`place_name_inheritance`, `relic_legend`, `lineage_tradition`,
`religious_mythic_interpretation`, `forgotten_fragment`.

New forms may be added without changing the model; the compiler validates
against a known set and rejects unknown forms.

## 4. Truth distance / drift

Interpretation types:

`faithful`, `simplified`, `selective`, `symbolic`, `exaggerated`,
`contradictory`, `corrupted`, `fragmented`, `mythologized`, `disputed`,
`unknown`.

There is no single numeric "truth score". Instead, each deviation is an
inspectable `WorldMemoryDeviationSpec`:

- `deviation_kind` — `omission`, `exaggeration`, `reinterpretation`,
  `conflation`, `contradiction`, or `unknown`,
- `canon_supports` — what the Chronicle supports,
- `legend_claims` — what the legend claims,
- `entry_note` — why/where the variation entered the cultural record.

Example:

> Canon: Rowan defeated three giants at the northern gate.
> Legend: Rowan slew twelve giants alone beneath a blood-red moon.

This is valid world memory only if stored as a declared, mythologized deviation.
It must not alter the canonical participant count, event conditions, or Chronicle
record.

## 5. Competing histories

Multiple communities may remember the same canonical event differently. They are
never reconciled. Provenance distinguishes:

- what happened canonically,
- who says what happened,
- what later culture believes happened.

## 6. Legendary Figures

`legendary_figures` + `legendary_figure_links` let past players, Aspects, NPCs,
and groups become Legendary Figures without copying or mutating their canonical
identity. Links reference canonical identity, Biography, portrait timeline,
Chronicle events, StoryMarks, relationships, relics, locations, Group Memories,
and approved artworks.

A canonical title is different from a later cultural title; both are stored
separately (`figure_title` vs `later_cultural_titles`) and the UI/API keep them
visibly distinct.

## 7. Significance and eligibility

No subject becomes legendary automatically. Eligibility derives from canonical
significance signals only: Memory Object importance tier/score, group
significance, and recurring references. There is no popularity counter.

Remembrance scales: `personal`, `local`, `regional`, `world_famous`, `forgotten`.

A forgotten figure may later be rediscovered.

## 8. Forgetting, loss, and rediscovery

Memory states: `widely_remembered`, `locally_remembered`, `archived_obscure`,
`fragmented`, `misattributed`, `suppressed`, `forgotten`, `rediscovered`.

State transitions are recorded in `world_memory_state_history`. Forgetting never
deletes canonical records. Rediscovery restores visibility, not canon.

Rediscovery may occur through relics, ruins, inscriptions, paintings, archives,
descendants, old biographies, recurring symbols, or cross-Aspect recognition.

## 9. In-world cultural consequences

Cultural artifacts are derived world state with their own provenance and
lifecycle. Examples: an annual festival, a renamed street/gate/bridge, a statue
erected or later removed, a ceremonial relic, a phrase entering local folklore,
a distorted bedtime story, a battlefield becoming sacred/taboo, a portrait
hanging in a hall, a Chronicle Painting moving from private collection to
public museum.

## 10. NPC historical knowledge

`project_npc_knowledge` is consent-safe and provenance-aware. An NPC's knowledge
is scoped by culture/faction, location, era, social role, archive access,
education, local tradition, direct relationship, and publication state.

- A peasant may know only the folk tale.
- A royal archivist may know a near-contemporary account.
- A descendant may know private family history.

An NPC never automatically receives the canonical database truth. Each projected
entry carries a `fidelity` and a `canonical_truth_visible` flag.

## 11. Relic inheritance

A relic may carry canonical ownership history and cultural legends about prior
bearers, false attributions, inherited names/titles, forgotten functions, and
remembered promises. Relic legend never collapses into relic canon.

## 12. Soul Constellation integration

World Memory supports cross-Aspect historical echoes (a statue of an earlier
Aspect, a song with a recurring symbol, a relic tied to an earlier life) without
forcing a metaphysical interpretation. The game may present the connection as
fantasy, psychology, spirituality, coincidence, or metaphor; mechanics never
require one reading.

## 13. World Gallery integration

Phase 15's Gallery is the canonical player-facing archive for approved visual
history. Phase 16 may place selected artifacts inside world memory (a historical
portrait in a memorial exhibition, an approved Chronicle Painting as a public
cultural artifact). Gallery visibility and in-world availability remain
independent.

## 14. Generation / provider boundaries

Legends, songs, inscriptions, and historical accounts are generated from a
structured, consent-filtered `WorldMemorySpec`. The provider may embellish style
within declared interpretation/drift constraints and must not introduce
undeclared canonical facts.

Providers follow the existing abstraction pattern (`world_memory_provider.py`).
The deterministic `mock` provider is the default and requires no external AI.

## 15. World Memory Guardian

`world_memory_guardian.py` validates generated cultural-memory artifacts. It does
not correct legends into canon. It verifies that deviations are intentional,
declared, and safe.

It detects (at minimum):

- source IDs that do not exist,
- factual claims with no canonical backing and no declared deviation,
- private participant information leaking into public legend,
- undeclared participant invention,
- a scoped perspective claiming omniscient truth,
- drift without a declared deviation,
- unapproved visual references (a rejected/quarantined painting cannot become a
  public monument),
- accidental promotion of legend into canonical records.

A declared exaggeration may pass. An undeclared hallucination must fail. The
structured result is `pass` / `retry` / `block` with diagnostics, consistent
with the existing Visual Canon Guardian and Biography Guardian patterns.

## 16. Consent / publication

All reads go through consent/publication projection. Public-canon World Memory is
visible to all viewers; private World Memory is visible only to its owner.
Private participants never leak through narrative, provenance, counts, or alt
text.

## 17. Known v1 limitations

- Only the deterministic mock provider and Guardian are wired; a real LLM
  provider and semantic claim review would be added behind the same interfaces.
- Participant-invention detection is structural (explicit soul-id tokens), not
  semantic.
- Forgetting/rediscovery is a stored state transition; there is no automatic
  time-based degradation of memory.
- World Memory placement records reference locations/relics/gallery collections
  by ID; in-world placement is not yet surfaced inside those feature views.
- NPC knowledge projection is computed on demand and not yet persisted.

## 18. API surface

Under `/api/v1/`:

- `POST /world-memory/compile` — compile World Memory from canonical sources.
- `GET /world-memory` — list (consent-filtered, filterable).
- `GET /world-memory/{memory_id}` — get one.
- `GET /world-memory/{memory_id}/versions` — version history.
- `GET /world-memory/{memory_id}/deviations` — declared drift + provenance.
- `GET /world-memory/query` — query memories about an event/person/place/relic.
- `POST /world-memory/{memory_id}/approve` / `reject`.
- `POST /world-memory/{memory_id}/mark-state` — forget/rediscover.
- `GET /world-memory/{memory_id}/state-history`.
- `POST /world-memory/{memory_id}/placements` / `GET .../placements`.
- `POST /world-memory/npc-knowledge` — NPC knowledge projection.
- `POST /legendary-figures/promote` — promote an eligible subject.
- `GET /legendary-figures` / `GET /legendary-figures/{figure_id}`.
