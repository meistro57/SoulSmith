# Living Biography

Phase 14 turns the Chronicle from a collection of canonical memories into a
living, evolving biography of a soul.

> **THE BIOGRAPHY IS DERIVED FROM THE CHRONICLE. IT DOES NOT REWRITE IT.**

```text
CANONICAL CHRONICLE -> BIOGRAPHY COMPILER -> PROVENANCE-AWARE NARRATIVE
    -> PLAYER REVIEW / PRESENTATION
```

Never:

```text
GENERATED BIOGRAPHY -> RETROACTIVE CANON
```

The biography is an interpretation and organization of canonical records. The
source records remain authoritative.

## Biography vs canon

- The **Chronicle** is what happened and what was remembered.
- The **biography** is the story those memories can support.

A biography passage is not canon because it sounds convincing. Every factual or
interpretive passage retains machine-readable provenance back to the canonical
records that support it. Narrative bridges are connective tissue and never
assert new canon.

## Data model

Normalized relational tables (no opaque JSON graph):

### `biography_versions`

Immutable, auditable versions. Regenerating never erases a previous version.

| Field | Purpose |
|---|---|
| `biography_id` | Stable version ID (`bio_<version>_<uuid>`). |
| `soul_id` | Subject soul. |
| `version_number` | Monotonic per-soul version. |
| `status` | `draft` / `current` / `superseded` / `rejected` / `failed`. |
| `title` / `current_chapter` | Derived from canonical records. |
| `scope_type` / `scope_ref` | Full-life or scoped (relationship/location/thread). |
| `visibility` | `public_canon` / `private_canon`. |
| `source_snapshot_json` | Source Chronicle range/count snapshot. |
| `provider` / `provider_model` / `compiler_version` | Compiler/provider metadata. |
| `guardian_status` / `guardian_report_json` | Biography Guardian outcome. |

### `biography_sections`

One row per compiled section with `section_type`, `title`, `narrative`,
`claim_kind`, `perspective_of`, and optional `visual_reference`.

### `biography_provenance`

Per-section, per-source provenance links:

- `source_type` — `memory_object`, `group_memory`, `portrait_version`,
  `visual_entity_version`, `chronicle_painting`, `story_mark`, `relic`,
  `probable_path`.
- `source_id` — the canonical record ID.
- `claim_kind` — fact vs perspective classification for this link.

## Structured biography compiler

`app/biography_compiler.py` gathers consent-filtered canonical records and
produces an inspectable `BiographySpec` *before* any prose is generated:

- chronological canonical records,
- significance,
- Group Memory membership,
- typed tags/anchors,
- participants/relationships,
- StoryMarks,
- relic/location/phenomenon continuity,
- recurring threads,
- unresolved consequences,
- approved visual references,
- consent-safe projection.

The narrative provider receives only this structured, consent-filtered input and
must return structured output with provenance references.

## Chronology / eras

`compile_chronology` orders memories by exact `created_at` when available and
otherwise uses safe relative labels ("earliest remembered moment", "later in the
Chronicle", "latest remembered moment"). It never invents calendar dates, ages,
durations, or ordering to smooth prose.

## Provenance model

Every section carries `claim_kind` and a list of provenance references. The UI
answers "Why does my biography say this?" by expanding "From the Chronicle" and
listing the supporting Memory Object(s), Group Memory context, portrait/world
visual version, Chronicle Painting, StoryMark, relic, or probable path.

## Fact vs perspective vs interpretation

Claim kinds are explicit and machine-readable:

| `claim_kind` | Meaning |
|---|---|
| `canonical_fact` | A fact present in a canonical record. |
| `participant_perspective` | One participant's recollection. |
| `shared_perspective` | Multiple participants' recollections side by side. |
| `inferred_theme` | A derived pattern, never a new fact. |
| `narrative_connective` | Stylistic bridge; asserts no canon. |
| `unresolved` | Uncertain or open. |

An LLM may not convert themes, interpretations, symbolism, or participant
recollections into objective canonical fact.

## Recurring threads

`extract_recurring_threads` derives threads deterministically from repetition
(recurring person/place/relic) and typed tags/anchors (`recurring_motif`,
`thread`). Each thread links back to its source records. AI-assisted thematic
labels remain separate from canonical tags.

## Group Memory integration

> Shared event does not mean shared memory.

A biography may describe a shared event from the subject's perspective and, when
consent permits, note that another participant remembers it differently:

> You remember the crossing as a victory. Another surviving account remembers it
> primarily as a loss.

Disagreements are never flattened into one narrative truth. Only
visibility-permitted perspectives are exposed.

## Approved visual usage

Approved `PortraitVersion`s, approved location/relic/phenomenon
`VisualEntityVersion`s, and approved Chronicle Paintings are used as
illustration, never evidence. Rejected, quarantined, blocked, superseded-as-
current, or unreviewed artwork is never used. The Visual Canon Guardian remains
mandatory for new Chronicle artwork; Phase 14 does not bypass it.

## Narrative provider abstraction

`app/biography_provider.py` defines `BiographyNarrativeProvider`. The
deterministic mock (`soulsmith-mock-biography-v1`) requires no internet or
external AI and produces stable output. Provider failure never damages Chronicle
data or replaces the current biography.

## Biography Guardian

`app/biography_guardian.py` validates generated output before it becomes
current/player-visible. It is not the Visual Canon Guardian; it validates
narrative claims against the structured source/provenance set:

- unknown/out-of-scope source IDs,
- unsupported factual claims (factual passage with no provenance),
- invented dates/ages/durations,
- perspective presented as objective fact,
- references to unapproved visual artifacts.

Deterministic structural validation is mandatory. A failed draft never replaces
the current biography.

## Consent and publication

Compilation is consent-filtered for its audience. A private biography and a
public biography are not necessarily the same document. Public output does not
leak private participants or hidden information through prose, titles, tags,
captions, source counts, provenance metadata, or thread summaries.

## Review and regeneration workflow

- `POST /api/v1/biographies/compile` — compile a draft.
- `POST /api/v1/biographies/{id}/approve` — make current (supersedes prior).
- `POST /api/v1/biographies/{id}/reject` — reject a draft.
- Regeneration compiles a new immutable version.

Corrections operate through the right layer: poor wording is regenerated;
incorrect canonical memory is routed to the existing Chronicle correction
mechanism, never silently edited from the biography screen.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/biographies/compile` | Compile a biography draft. |
| GET | `/api/v1/biographies/current?soul_id=` | Get the current biography. |
| GET | `/api/v1/biographies/history?soul_id=` | List version history. |
| GET | `/api/v1/biographies/{id}` | Get one version. |
| POST | `/api/v1/biographies/{id}/approve` | Make a draft current. |
| POST | `/api/v1/biographies/{id}/reject` | Reject a draft. |
| GET | `/api/v1/biographies/{id}/sections/{section_id}/provenance` | Inspect section provenance. |

All responses are consent-aware.

## Known v1 limitations

- Only the deterministic mock narrative provider is wired; a real LLM provider
  would be added behind the same abstraction.
- Semantic claim verification is not implemented; deterministic structural
  validation is mandatory and mock tests cover pass/fail behavior.
- Thread scoping filters at the memory-object layer but relies on typed tags for
  motif-level scoping; no embedding index.
- No migration framework; schema additions use the existing
  `CREATE TABLE IF NOT EXISTS` convention.
