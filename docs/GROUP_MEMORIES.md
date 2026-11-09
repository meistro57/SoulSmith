# Group Memories & Tags

Phase 13 lets SoulSmith recognize that multiple souls can participate in the
same canonical event while remembering it differently.

> **SHARED EVENT DOES NOT MEAN SHARED MEMORY.**

A Group Memory is a relational structure linking participant-specific canonical
Memory Objects to the same shared event, shared anchors, and each other. It never
rewrites, reconciles, or flattens those memories into one authoritative
narrative.

## The distinction

```text
Shared Event -> Group Memory -> participant-specific Memory Objects
```

Each participant keeps their own Memory Object with their own perspective,
emotional tone, significance, consequences, StoryMarks, remembered details, and
visibility/consent state. The Group Memory links them. It does not rewrite them.

Soul A may remember fear. Soul B may remember triumph. Soul C may remember the
sound of a door closing. All can be valid participant memories of the same
event. Disagreement is presented as perspective, never as corruption.

## Data model

### `group_memories`

| Field | Purpose |
|---|---|
| `group_id` | Stable group-memory ID. |
| `event_id` | Exact shared event ID (the deterministic grouping key). |
| `title` / `summary` | Derived only from safe shared facts. |
| `visibility` | Publication state (`public_canon` / `private_canon`). |
| `group_significance` | Group-level signal (`personal`, `relationship`, `community`, `world`, `legendary`). |
| `group_significance_score` | Derived score (1..10), never overwrites individual significance. |

### `group_memory_members` (junction)

Links a Group Memory to participant Memory Objects:

- `memory_object_id` — the participant's canonical Memory Object.
- `soul_id` — the participant whose memory this is.
- `role_in_event` — participant role in the event.
- `portrait_version_id` — the historical `PortraitVersion` locked at event time.

### `group_memory_tags` (typed, ID-anchored)

| Field | Purpose |
|---|---|
| `tag_type` | Typed vocabulary: `person`, `location`, `relic`, `phenomenon`, `faction`, `relationship`, `emotional_theme`, `event_type`, `recurring_motif`, `consequence`, `thread`. |
| `value` | Safe display label. |
| `anchor_kind` / `anchor_id` | Optional canonical entity anchor (see below). |
| `is_descriptor` | Free-form descriptive secondary metadata, never canonical. |

### `group_memory_anchors`

Shared canonical anchors referencing historical, immutable versions:

- `portrait` — historical participant `PortraitVersion`.
- `location` / `relic` / `phenomenon` — historical `VisualEntityVersion`.
- `chronicle_painting` — approved Chronicle Painting ID.

Historical references remain locked to the versions that existed at event time;
they are never silently substituted with current/latest versions.

## Perspective preservation

`GET /api/v1/group-memories/{group_id}/perspectives` returns a
`PerspectiveComparison` that keeps each participant's recollection distinct:

- `perspectives` — consent-filtered participant perspectives.
- `shared_facts` — the deterministic intersection of safe canonical fields.
- `disagreements` — fields where recollections differ, listed side by side.

Shared facts are derived, never written back into any Memory Object. Conflicting
recollections remain distinct; an LLM or projection never converts disagreement
into fabricated consensus.

## Typed tags and anchors

Prefer stable IDs and typed anchors over free-form strings. A `person` tag with
an `anchor_id` referencing a `PortraitVersion` is a canonical entity anchor. A
tag with `is_descriptor=true` is free-form secondary metadata and is explicitly
non-canonical.

Tags and anchors query related memories without modifying the memories
themselves:

- `GET /api/v1/group-memories/related?tag_type=&tag_value=`
- `GET /api/v1/group-memories/related?anchor_type=&anchor_ref=`

## Automatic vs suggested grouping

- **Automatic grouping** (`POST /api/v1/group-memories/auto-group?event_id=`) is
  deterministic and keyed only by exact shared `event_id`.
- **Semantic similarity never asserts canonical equivalence.**
  `GET /api/v1/group-memories/suggestions/{memory_object_id}` returns
  *suggestions* flagged `canonical: false`; they are never written as members.
- Manual grouping (`POST /api/v1/group-memories/{id}/members`) is available when
  appropriate.

An AI may say "these memories may describe the same event." It may not silently
declare "these memories are the same event."

## Historical visual references

A Group Memory may reference historical participant PortraitVersions, location
/ relic / phenomenon VisualEntityVersions, and Chronicle Painting IDs. Anchors
are validated against real, matching versions at add time and locked thereafter.

## Consent and privacy

Consent is participant-specific. One participant allowing their memory to be
shared does not grant permission to expose another participant's private memory
or identity.

`project_group_for_viewer` filters every response:

- Private, non-viewer participants are omitted entirely (not even counted).
- The viewer always sees their own member link.
- Title/summary are re-derived from public facts only.
- Person tags and portrait anchors referencing hidden participants are stripped.

Private participant names, portrait references, StoryMarks, emotional
interpretation, and Memory Object contents do not leak through tags, counts,
metadata, summaries, or API responses.

## Group Memory UI

A player viewing a Memory Object sees, where permitted: that others remember
this event, participant roles, shared anchors/tags, their own perspective, other
visible perspectives, points of agreement, and explicitly different
recollections. The presentation is narrative and human-readable:

> **Everyone remembers the same moment differently.**

## Chronicle Painting relationship

A Chronicle Painting remains art, not canon. Group Memories prepare future
artwork for shared-event paintings, participant-specific interpretations, and
alternate compositions, but the Visual Canon Guardian still validates every
generated image before it becomes player-visible. Advanced multi-reference
identity conditioning is not solved in this phase; capability reporting degrades
honestly.

## AI boundaries

- Canonical grouping by exact shared event ID is deterministic.
- Tag extraction from structured canonical fields is deterministic.
- Semantic suggestions remain suggestions until confirmed by deterministic
  evidence or an explicit authorized action.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/group-memories` | Create a Group Memory for a shared event. |
| POST | `/api/v1/group-memories/auto-group?event_id=` | Deterministic exact-event grouping. |
| GET | `/api/v1/group-memories` | List Group Memories (consent-filtered). |
| GET | `/api/v1/group-memories/by-event/{event_id}` | Get by event. |
| GET | `/api/v1/group-memories/{group_id}` | Get one (consent-filtered). |
| POST | `/api/v1/group-memories/{group_id}/members` | Attach a Memory Object. |
| DELETE | `/api/v1/group-memories/{group_id}/members/{memory_object_id}` | Detach (never deletes the Memory Object). |
| POST | `/api/v1/group-memories/{group_id}/tags` | Add a typed tag. |
| DELETE | `/api/v1/group-memories/{group_id}/tags/{tag_id}` | Remove a tag. |
| POST | `/api/v1/group-memories/{group_id}/anchors` | Add a validated anchor. |
| GET | `/api/v1/group-memories/{group_id}/anchors` | Get shared anchors. |
| GET | `/api/v1/group-memories/{group_id}/perspectives` | Get perspective comparison. |
| GET | `/api/v1/group-memories/related` | Find related memories by anchor/tag. |
| GET | `/api/v1/group-memories/suggestions/{memory_object_id}` | Non-canonical similarity suggestions. |

## Known v1 limitations

- Multi-reference identity conditioning for shared-event paintings is not
  solved; the painting provider remains text-to-image for Chronicle scenes.
- Semantic suggestions are keyword/title/participant heuristics, not an
  embedding index. They never assert canonical equivalence.
- No migration framework; schema additions use the existing
  `CREATE TABLE IF NOT EXISTS` convention.
