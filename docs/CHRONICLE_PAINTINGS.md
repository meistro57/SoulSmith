# Chronicle Paintings + Visual Canon Guardian

Phase 12 turns canonical Memory Objects into visual history while preserving
SoulSmith's central rule:

> **MEMORY IS CANON. ART IS INTERPRETATION.**

A Chronicle Painting is a generated visual interpretation of a canonical Memory
Object. Artwork may be regenerated, rejected, superseded, or stylistically
reinterpreted without altering the event it depicts.

## Canon rule

The pipeline is always:

```
CANON -> SCENE SPEC -> IMAGE GENERATION -> VISUAL CANON GUARDIAN -> PLAYER-VISIBLE CANDIDATE
```

Never `ART -> CANON`. Generated imagery must never mutate Memory Objects,
Chronicle events, StoryMarks, PortraitVersions, participant identity, relic
history, scene outcomes, dice rolls, or grammar interpretation.

## Three gates

1. **Canon Guardian** — protects what enters the Chronicle.
2. **Visual Canon Guardian** — protects what comes out of image generation.
3. **Human approval** — chooses which valid artistic interpretation becomes preferred.

These responsibilities are kept distinct and are not collapsed into one mechanism.

## Architecture

| Module | Responsibility |
|---|---|
| `app/chronicle_paintings.py` | Painting/candidate models, statuses, Guardian report/violation models, provider capability model. |
| `app/painting_compiler.py` | Dedicated scene compiler: canonical extraction (structured `SceneSpec`) separated from artistic phrasing. |
| `app/composition_selector.py` | Deterministic composition mode selector. |
| `app/painting_reference.py` | Historical participant portrait locking and non-identifying degradation. |
| `app/painting_provider.py` | Provider abstraction (`mock`, `comfyui`) with honest capability reporting. |
| `app/visual_canon_guardian.py` | Vision-based Guardian abstraction + deterministic mock (PASS/RETRY/BLOCK). |
| `app/painting_pipeline.py` | Orchestrates generate → quarantine → inspect → retry/block/pass. |
| `app/comfyui/storage.py` | `ChronicleImageStore` (quarantine vs promoted player-visible storage). |
| `app/comfyui/workflow_roles.py` | `chronicle_painting` workflow role. |

## Lifecycle

Statuses: `candidate`, `approved`, `rejected`, `superseded`, `failed`.

Generation intents: `initial`, `retry`, `composition_change`, `style_change`,
`reference_upgrade`, `manual_regeneration`.

A generated painting is never automatically canon. Approval only makes it the
preferred artistic representation of the Memory Object. Approving a replacement
supersedes the previous approved painting without deleting historical candidates.

## Historical participant locking

- If the Memory Object references a historical `PortraitVersion`, that exact
  version is used. The newest portrait is never silently substituted.
- When canonical appearance is unavailable, identity-specific details are not
  invented. A non-identifying strategy (`silhouette`, `rear_view`, `distant`,
  `environmental`, `omitted`) is selected and recorded in generation metadata.
- StoryMarks, scars, tattoos, age, hair, clothing, equipment, ethnicity, and
  facial features are never fabricated.

## Scene compiler

`compile_chronicle_painting_scene` produces an inspectable `SceneSpec`:

- location/time/environment/event
- participants with exact historical portrait versions
- canonical appearance
- StoryMarks
- equipment and relic state
- pose/action
- phenomena
- emotional tone
- composition
- must-preserve facts
- must-not-invent constraints

`compile_painting_prompt` renders this into provider instructions with explicit
sections: Scene, Participants, Historical Appearance, Action, Relics/Equipment,
StoryMarks, Phenomena, Atmosphere, Composition, Preserve, Do Not Invent, Visual
Style.

## Composition

`select_composition` is a deterministic selector supporting `intimate`,
`environmental`, `confrontation`, `discovery`, `aftermath`, `journey`, `ritual`,
`relic_focus`, `phenomenon_focus`, and `group_memory`. It uses participant count,
significance, phenomena, relic involvement, event type, and emotional tone.
Significance influences scale without producing a superhero poster.

Default visual direction: cinematic painterly realism, grounded fantasy,
atmospheric storytelling, tactile environments, natural dramatic lighting,
expressive but believable characters, strong depth, environmental detail,
restrained magical phenomena. No tarot borders, captions, UI, HUD, labels, text,
logos, or MMO-poster composition.

## Provider capabilities

Providers report honest capability levels:

- `text_to_image`
- `single_reference`
- `multiple_references`
- `identity_conditioning`
- `regional_conditioning`
- `deterministic_seed`
- `aspect_ratio_control`

The v1 ComfyUI chronicle workflow is text-to-image only
(`multiple_references=False`, `identity_conditioning=False`,
`regional_conditioning=False`). Multi-participant identity preservation is not
pretended; it degrades honestly to textual historical-appearance descriptions
while future IPAdapter/FaceID/regional conditioning remains a clean extension
point.

## ComfyUI workflow role

`COMFYUI_CHRONICLE_PAINTING_WORKFLOW` points at the bundled
`chronicle_painting_v1_api.json` (API-format, wide 1344x768 text-to-image). The
workflow JSON lives outside Python source and follows the existing
`workflow_loader`/`workflow_binder` pattern.

## Storage and quarantine

- Quarantine: `backend/assets/chronicle/quarantine/` (unreviewed/failed output).
- Player-visible: `backend/assets/chronicle/paintings/` (promoted only after PASS).

Raw generated output is written to quarantine first and copied into the
player-visible area only after the Guardian passes. Quarantined images are never
served as normal Chronicle assets. Temporary ComfyUI `/view` URLs are never
persisted as canonical asset URLs.

## Visual Canon Guardian

No generated Chronicle Painting may be shown to a player before it passes visual
review. The Guardian inspects the actual generated image (not merely prompt or
metadata) and returns a structured verdict:

```json
{
  "status": "pass | retry | block",
  "confidence": 0.0,
  "violations": [
    {
      "type": "...",
      "severity": "low | medium | high | critical",
      "description": "...",
      "canonical_expected": "...",
      "observed": "..."
    }
  ],
  "correction_instructions": []
}
```

Inspection covers participant count, duplicate participants, unknown foreground
people, historical identity continuity, age/appearance, StoryMarks,
clothing/equipment, relic presence/state, scene fidelity, phenomena, invented
details, anatomy integrity, corruption, unwanted text/logos, and consent.

- **PASS** — persist report, permit player-visible candidate.
- **RETRY** — quarantine, feed correction instructions into regeneration, retry
  up to a configurable maximum (`SOULSMITH_CHRONICLE_MAX_RETRIES`, default 2).
- **BLOCK** — quarantine, preserve diagnostics, graceful failure.

Guardian reports are stored per attempt for auditability. The Guardian judges art
against canon; it never modifies canon to match art.

### Deterministic mock

`MockVisualCanonGuardian` requires no GPU/ComfyUI/external AI/internet. Without a
forced verdict it PASSes valid canonical inputs; `SOULSMITH_MOCK_GUARDIAN_VERDICT`
(`pass`/`retry`/`block`) forces a deterministic verdict so every branch is
testable.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/chronicle-paintings` | Create a painting attempt from a Memory Object. |
| POST | `/api/v1/chronicle-paintings/{id}/generate` | Run generate → quarantine → Guardian loop. |
| POST | `/api/v1/chronicle-paintings/{id}/approve` | Approve (supersedes prior approved). |
| POST | `/api/v1/chronicle-paintings/{id}/reject` | Reject (auditable). |
| GET | `/api/v1/chronicle-paintings/{id}` | Get one painting. |
| GET | `/api/v1/chronicle-paintings?memory_object_id=` | Painting history for a memory. |
| GET | `/api/v1/chronicle-paintings/gallery` | Approved public paintings with memory metadata. |
| GET | `/api/v1/chronicle-paintings/providers/capabilities` | Provider capability report. |

## Privacy and consent

Existing consent behavior is preserved. Generation and publication are separate;
a painting may exist privately while prohibited from public canon. The gallery
query returns only approved paintings whose Memory Object is `public_canon`. The
Visual Canon Guardian is an additional defense, not a replacement for
deterministic consent checks.

## Failure behavior

ComfyUI downtime, missing workflows/references, provider timeout, Guardian
failure, generation failure, or storage failure never damage the Memory Object or
an existing approved painting. Diagnostics are preserved and errors surfaced.
An approved painting is never superseded until a new candidate passes the
Guardian and is explicitly approved.

## Known v1 limitations

- The ComfyUI chronicle workflow is text-to-image only; it does not conditionally
  preserve multiple participant identities. Multi-identity scenes rely on textual
  historical-appearance descriptions and the Guardian's canonical checks.
- The Guardian's only implementation is the deterministic mock; a real
  vision model remains a future provider.
- World Gallery UI is intentionally deferred; the backend gallery query is ready.

## Future multi-reference identity options

IPAdapter/FaceID or regional conditioning could preserve participant-to-reference
mapping. The provider capability model already reserves `multiple_references`,
`identity_conditioning`, and `regional_conditioning` flags for this upgrade.
