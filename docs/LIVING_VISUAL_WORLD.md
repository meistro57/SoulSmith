# Living Visual World & ComfyUI Runtime (Phase 21)

> **SOULSMITH DOES NOT ILLUSTRATE EVERYTHING. IT PAINTS WHAT BECOMES WORTH
> REMEMBERING.**
>
> **MEMORY IS CANON. ART IS INTERPRETATION.**

Phase 21 turns SoulSmith's completed visual architecture — portrait continuity,
Memory Objects, Chronicle Paintings, the Visual Canon Guardian, the Art
Director, the World Gallery, Legendary Figures, World Memory, ComfyUI
integration, and the Campaign Orchestrator — into a living runtime that paints
meaningful moments during actual play.

The pipeline is one-way:

```
CANONICAL STATE
  -> ART DIRECTOR ELIGIBILITY
  -> SCENE / PORTRAIT / OBJECT SPEC
  -> VISUAL PROVIDER
  -> QUARANTINE
  -> VISUAL CANON GUARDIAN
  -> APPROVAL
  -> GALLERY / MEMORY
```

It is never:

```
GENERATED IMAGE -> NEW CANON
```

## Visual authority boundaries

1. **Canon determines what may be depicted.** Generated pixels never become
   canonical facts merely because they appear in an image.
2. **Generation is selective, not automatic.** The Art Director decides
   eligibility from structured state *before* any provider call. Most events
   produce no Art Moment (silence is valid).
3. **Continuity uses locked references.** Historical character continuity
   requires the explicit historical `PortraitVersion`; continuity never
   silently falls back to unrelated text-to-image generation.
4. **The Guardian stays between output and approval.** Raw output is quarantined
   and may only become player-visible after a `pass` verdict.
5. **Provider failure never damages campaign state.** ComfyUI may disappear;
   SoulSmith keeps playing.
6. **Human direction may interpret, never rewrite.** A human curator can guide
   style/composition/mood/motif but cannot alter locked canonical facts.
7. **Approved art is a historical interpretation with provenance, not
   retroactive evidence.**

## Data model

### ArtMoment

`art_moments` records *what the Art Director found worth painting*. It carries:

- a stable `art_moment_id`, campaign/session/soul, and `visual_type`;
- the deterministic `eligibility_rule` and structured `source_evidence`;
- `source_entity_type`/`source_entity_id` and `reference_asset_ids`;
- the inspectable `spec` (a `VisualSceneSpecModel`).

Art Moments are bookkeeping/interpretation, never canonical history.

### VisualJob

`visual_jobs` records the auditable, resumable generation lifecycle:

- `generation_state` (`queued`, `running`, `guardian_review`, `completed`,
  `approved`, `rejected`, `hidden`, `blocked`, `failed`, `cancelled`,
  `deferred`);
- provider/workflow provenance (`provider`, `provider_model`, `workflow_role`,
  `workflow_version`, `provider_request_id`, `generation_seed`);
- `retry_count`, `quarantined_image_url`, `final_image_url`, `guardian_status`,
  `guardian_report`, and `superseded_job_id`.

Retries never create duplicate canonical events or duplicate approved Gallery
entries; each retry is a new `VisualJob` row that supersedes the prior attempt.

## Art Director eligibility

`evaluate_art_moments(state)` deterministically inspects structured state and
emits Art Moment specs. Signals include:

- significant Memory Object (Chronicle importance);
- a major Thread transition / Integration;
- relic state change (Awakened/Transfigured/Overdrawn/Fractured);
- relationship with canonical interaction history;
- promise fulfillment/breach/release/inheritance/transfer;
- significant Group Memory;
- significant World Memory / Legendary Figure;
- a Wandering place accumulating history.

A **Remembered** relic is an awakening *candidate*, not a validated change; it
does not produce a relic visual until the Relic Recognition system validates the
awakening.

## Visual types

| Visual type | Workflow role | Authority/context contract |
|---|---|---|
| `portrait` | `portrait_initial` | Aspect identity (text-to-image). |
| `portrait_continuity` | `portrait_reference` | Locked source reference required. |
| `memory_object` / `chronicle_painting` | `chronicle_painting` | Evidence-backed event scene. |
| `relic` | `object_initial` | Relic state, never abilities. |
| `relationship` / `group_memory` | `environment_initial` | Preserve participant perspectives. |
| `legendary_figure` / `world_memory` | `environment_initial` | Folklore illustration, never history. |
| `place` | `environment_initial` | Story interpretation, never physical claims. |

## ComfyUI runtime

`backend/app/living_visual_provider.py` is a thin runtime over the existing
`app.comfyui` client/workflow stack. It does not introduce a second
image-generation stack; it maps a `VisualJobType` to a workflow role and
delegates submit/poll/download to `ComfyUIClient` + `WorkflowBinder`.

It supports:

- configurable `COMFYUI_SERVER_URL`;
- workflow selection by visual type (role → bundled workflow file);
- prompt/workflow parameter injection through bounded `WorkflowBinder`
  contracts (never raw ComfyUI node IDs leaking into domain code);
- queue submission, progress polling, completion retrieval;
- timeout (`COMFYUI_TIMEOUT_SECONDS`) and poll interval;
- reference-image upload for continuity;
- health/capability status via `GET /api/v1/living-visuals/providers/status`;
- deterministic mock fallback (`SOULSMITH_IMAGE_PROVIDER=mock`, the default).

## Scene specifications

`VisualSceneSpecModel` (in `living_visual_compiler.py`) separates:

- **locked canonical facts** (`permitted_participants`, `canonical_objects`,
  `relic_state`, `location`, `action_facts`, `outcome_facts`);
- **prohibited additions** (`prohibited_additions`);
- **unknown fields** (`unknown_fields`) which remain unknown instead of being
  filled with accidental specificity;
- **interpretation fields** (`emotional_tone`, `composition`, `style_guidance`,
  `mood`, `motif`, `symbolism`);
- **source evidence** (`source_evidence`) backing every locked fact.

## Portrait continuity

The existing portrait continuity architecture is preserved. Continuity updates
require a locked historical `PortraitVersion`, use the reference workflow, and
never silently fall back to text-to-image. Approval creates a new interpretation
rather than mutating the source.

## Chronicle Paintings and relic imagery

The existing `CANON -> SCENE SPEC -> GENERATION -> VISUAL CANON GUARDIAN ->
PLAYER-VISIBLE CANDIDATE` pipeline remains authoritative. A painting depicts an
evidence-backed event while allowing artistic interpretation of atmosphere,
composition, lighting, emotion, and style. The visual system cannot awaken a
relic or invent abilities; earlier visual versions are preserved when a relic
changes canonically.

## Relationship, promise, and Group Memory imagery

Relationship/promise evidence may make a visual moment eligible, but participant
perspectives are preserved and consent is respected before depicting
identifiable characters together or publishing shared imagery.

## Wandering and place memory

A place may accumulate Chronicle Paintings, World Memory illustrations, relic
imagery, legendary interpretations, and environmental art. Generated art
interprets the SoulSmith story associated with a place; it never claims that
fictional visual elements physically exist at the real-world location.

## Soulkeeper coordination

Phase 18 narration and Phase 21 visual generation share structured evidence,
not freeform prompts between models. The visual scene spec retains explicit
source evidence and locked facts. Narrative regeneration does not silently
trigger duplicate visual jobs, and visual generation never changes
narrative/domain outcomes.

## Human creative direction (Mythmaker extension point)

`POST /api/v1/living-visuals/art-moments/{id}/curate` records contributor
attribution/provenance and applies interpretation-only guidance
(style/composition/mood/motif/symbolism). It lays groundwork for a future
Mythmaker Workshop and never gains authority over canon.

## Quarantine and approval

Raw generated assets land under `/assets/living-visuals/quarantine/` and are
copied into `/assets/living-visuals/approved/` only after the Guardian passes.
Rejected/blocked images remain non-canonical and never leak into normal player
surfaces.

## Async queue and recovery

Generation may be slower than gameplay. The flow is:

```
Art Moment eligible -> VisualJob queued -> gameplay continues
  -> render completes -> Guardian -> candidate becomes available
```

`VisualJob`s persist in SQLite, so a queued/in-flight job recovers safely after
backend restart. `POST /api/v1/living-visuals/jobs/{job_id}/process` is
idempotent for already-approved/rejected/hidden jobs.

## Provider outage and graceful degradation

If ComfyUI is offline, canonical gameplay continues, Art Moments remain queued,
no fake successful asset is created, status is visible in authorized
diagnostics, and retries do not duplicate jobs.

## Resource discipline

Controls in v1:

- bounded retry count (`SOULSMITH_VISUAL_MAX_RETRIES`, default 2);
- count-based eligibility (no engagement-optimization heuristics);
- deterministic mock mode for local/no-GPU operation.

## Known v1 limitations

- Generation is synchronous within a FastAPI threadpool (the queue is a
  persisted state machine, not a multi-worker job server).
- `identity_conditioning` / `multiple_references` are not supported; the
  chronicle/relationship/group scene types degrade to textual historical
  appearance or non-identifying framing rather than pretending img2img
  preserves many faces.
- The Guardian is a deterministic spec validator plus human approval; it does
  not pretend computer vision can perfectly prove every visual detail.
