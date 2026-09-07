# AGENTS.md — SoulSmith

SoulSmith is a collaborative storytelling RPG built around a **seven-dice grammar**: seven numeric dice faces form the immutable roll record, a versioned grammar derives symbolic meaning, and the Soulkeeper AI (currently a deterministic stub) weaves encounters, persistent canon, relics, and multiplayer convergence into a "living mythology."

The repo is a monorepo with a **FastAPI backend**, a **React/Vite/Three.js frontend**, SQLite persistence, and no build orchestration beyond per-package commands (no Makefile, no Docker).

---

## Repo layout

- `backend/` — FastAPI (Python 3.12) + Pydantic v2 + SQLite (stdlib `sqlite3`). All logic lives here.
  - `backend/app/` — application code (one module per engine subsystem, all routes in `main.py`).
  - `backend/tests/` — pytest suite.
- `frontend/` — React 19 + Vite + TypeScript + Tailwind 4 + Three.js (`@react-three/fiber`/`drei`) + `oxlint`.
  - `frontend/src/lib/api.ts` — single typed API client.
  - `frontend/src/types.ts` — single source of frontend type definitions.
  - `frontend/src/components/` — one component per feature view.
  - `frontend/src/three/` — the 3D dice renderer modules.
- `docs/` — design docs. `ROLL_CONTRACT.md`, `DICE_RENDERING_SYSTEM.md`, `IMPLEMENTATION_AUDIT.md`, and `ROADMAP.md` are the important ones.
- `art/` — STL dice files and source image assets (not served by the app; static assets are duplicated under `frontend/public/art/`).
- `.agent/skills/` and `.gemini/skills/` — **agent skill definitions** (Three.js procedural techniques, etc.). These are context for AI agents, *not* runtime app code. Do not confuse them with app source.
- `soulsmith.md` — a long AI-generated architecture/design brief. Useful background, but the authoritative contract is `docs/ROLL_CONTRACT.md`.

---

## Commands

### Backend (run from `backend/`)

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

```bash
python -m pytest                        # run tests
ruff check .                            # lint
ruff format --check .                   # format check (no auto-format step)
```

### Frontend (run from `frontend/`)

```bash
npm ci
npm run dev                             # http://localhost:5173
```

```bash
npm run lint        # oxlint
npm run typecheck   # tsc -b --noEmit
npm run test        # NOT a real test runner — see "Testing" below
npm run build       # tsc -b && vite build
```

### CI parity

`.github/workflows/` pins these versions: **Python 3.12** (backend) and **Node 22** (frontend). Backend CI runs `ruff check`, `ruff format --check`, then `pytest --cov`. Frontend CI runs `lint`, `typecheck`, `test`, `build` in that order. `security.yml` runs `pip-audit` (severity high) and `npm audit`.

---

## Architecture and data flow

### Backend module map (`backend/app/`)

| Module | Responsibility |
|---|---|
| `main.py` | The FastAPI app. **Every route is defined here.** Also holds `RoomManager` for the WebSocket convergence endpoint. |
| `db.py` | SQLite storage abstraction. All persistence functions live here; returns plain dicts (via `sqlite3.Row`). Schema is created on first connection. |
| `grammar.py` | Canonical numeric roll contract + versioned grammar registry (`CURRENT_GRAMMAR_VERSION = "1.0.0"`). |
| `rules.py` | Deterministic scene outcome engine (4 outcome classes). |
| `encounters.py` | Encounter framing (`POST /api/v1/encounters/frame`). |
| `soulkeeper.py` | Soulkeeper narration + 5-Gate Canon Guardian audit. **Simulated/template prose** (no LLM call). |
| `soulprint.py` | Astrological soulprint generation (simulated). |
| `phenomena.py` | Phenomena codex (Echoes, Knots, Veils, Wells, Awakenings, etc.). |
| `relics.py` | Relic lifecycle: Dormant → Remembered → Awakened → Overdrawn → Fractured → Transfigured. |
| `curiosity.py` | Seeds, open questions, local threads, integration events. |
| `constellation.py` | Multi-Aspect identity, bonds, anchors, awakening stages. |
| `probable_paths.py` | Unchosen-path persistence and "what-if" scene simulation. |
| `convergence.py` | Multiplayer gatherings, community symbols, canon merge/fork. |
| `reflection.py` | Reflection sessions, private notes, player preferences/accessibility. |
| `visual_memory.py` | Avatar identity, story marks, memory objects, portrait models. |
| `portrait_compiler.py` | Deterministic portrait prompt compilation (sectioned into identity / changes / preserve / must-not-invent / framing). |
| `portrait_provider.py` | Image provider abstraction (`mock`, `external` scaffold, `comfyui`). |
| `portrait_reference.py` | Resolves `source_portrait_version_id` → a canonical `PortraitVersion`, enforcing soul ownership and existence. |
| `visual_world.py` | Phase 4 Worldsmith models (`VisualEntityVersionModel`, `WorldVisualCandidateModel`, request schemas). |
| `visual_compilers.py` | Deterministic world visual compilers (`location`/`relic`/`phenomenon`) + `compile_canonical_delta`. |
| `world_visual_provider.py` | Provider abstraction for world-entity generation (mock + ComfyUI environment/object roles). |
| `chronicle_paintings.py` | Phase 12 models: paintings, statuses, scene spec, Guardian reports, provider capabilities. |
| `painting_compiler.py` | Deterministic Chronicle Painting compiler (structured `SceneSpec` + sectioned provider prompt). |
| `composition_selector.py` | Deterministic composition mode selector for Chronicle Paintings. |
| `painting_reference.py` | Historical participant portrait locking + non-identifying degradation. |
| `painting_provider.py` | Chronicle Painting provider abstraction (mock + ComfyUI) with capability reporting. |
| `visual_canon_guardian.py` | Vision-based Guardian abstraction + deterministic mock (PASS/RETRY/BLOCK). |
| `painting_pipeline.py` | Orchestrates generate → quarantine → inspect → pass/retry/block. |
| `group_memories.py` | Phase 13 Group Memories & Tags: models, perspective preservation, consent projections, deterministic exact-event grouping, typed ID-anchored tags/anchors. |
| `biography.py` | Phase 14 Living Biography: models (version/section/provenance), consent-safe projection, chronology, recurring-thread extraction, fact-vs-perspective classification. |
| `biography_compiler.py` | Phase 14 deterministic biography compiler: gathers consent-filtered canonical records into an inspectable `BiographySpec` before prose. |
| `biography_provider.py` | Phase 14 narrative provider abstraction (mock + future LLM scaffold). |
| `biography_guardian.py` | Phase 14 Biography Guardian: deterministic validation of generated narrative against provenance (not the Visual Canon Guardian). |
| `art_director.py` | Phase 15 Art Director: versioned Art Direction Profile models, deterministic style hierarchy/resolution, Art Direction Spec compiler, provider-capability awareness. Controls interpretation, never canon. |
| `style_reviewer.py` | Phase 15 optional Art Direction Reviewer: deterministic mock style-compliance check that can never override a Visual Canon Guardian BLOCK. |
| `world_gallery.py` | Phase 15 World Gallery: consent-safe projection/query service for approved portraits, world visuals, Chronicle Paintings, shared moments, and biography illustrations, plus Collections/Exhibitions and timelines. |
| `world_memory.py` | Phase 16 World Memory: derived cultural-memory models (World Memory, deviations, Legendary Figures, placements, memory states), truth-distance/drift, significance/eligibility, forgetting/rediscovery, and consent-safe NPC knowledge projection. |
| `world_memory_compiler.py` | Phase 16 deterministic World Memory compiler: gathers consent-filtered canonical sources into an inspectable `WorldMemorySpec` before provider generation and Guardian validation. |
| `world_memory_provider.py` | Phase 16 cultural-artifact provider abstraction (mock default) that renders a structured spec into legend/song/inscription/etc. without inventing undeclared canon. |
| `world_memory_guardian.py` | Phase 16 World Memory Guardian (pass/retry/block): verifies deviations are declared and safe, never "corrects" legends into canon. |
| `campaign.py` | Phase 17 Campaign Orchestrator models + deterministic eligibility/pacing helpers (`CampaignSession`, `CampaignOpportunity`, `CampaignTransition`, `build_*_candidates`, `COOLDOWN_WINDOW`) plus Phase 18 `NarrativeContext`/`NarrativeOutput` models and `NARRATIVE_TEMPLATE_VERSION`. |
| `campaign_orchestrator.py` | Phase 17 Campaign Orchestrator service: evaluates eligible opportunities, runs the reaction pipeline after a committed event, resolves opportunities by delegating to owning domain systems, and exposes provenance/aftermath. Phase 18 routes narration through the narrative runtime and exposes provider status/context-preview/regenerate surfaces. |
| `campaign_provider.py` | Narrative provider abstraction (`CampaignNarrativeProvider`), deterministic mock (`soulsmith-mock-campaign-v1`), and a real OpenAI-compatible provider. Providers receive a consent-safe `NarrativeContext` and never invent canon. |
| `narrative_style.py` | Phase 18 fact-free Soulkeeper style layer (`NarrativeStyle`): prose density, dialogue frequency, tone, mystery, sensory richness, plain-language mode. Style never adds information. |
| `narrative_context_compiler.py` | Phase 18 consent-safe `NarrativeContext` compiler: smallest authorized evidence set + structured scene continuity + NPC-scoped contexts + token estimates. |
| `narrative_guardian.py` | Phase 18 deterministic narrative Guardian (pass/retry/block), distinct from the Visual Canon and World Memory Guardians. Rejects invented participants/events/dates/relic-abilities/Thread-truth/Integration/perspective-leaks/psychological-authority. |
| `narrative_runtime.py` | Phase 18 narrative runtime: provider selection, timeout, bounded retry, validation, safe deterministic fallback, and generation metadata (`narrative_generations` rows). |
| `relationship.py` | Phase 19 Relationship & Promise Engine: models (relationships, participants, source events, events/history, participant perspectives; promises, participants, state history, entity links), consent/visibility helpers, promise lifecycle validation, evidence-backed fulfillment/breach/release/inheritance/transfer evaluation, derived scheduling significance (never affection), and NPC knowledge projection. Persistence lives in `db.py`. |
| `multi_aspect.py` | Phase 20 multi-Aspect campaign sessions: `active_soul_id`, campaign-Aspect registration, deterministic idempotent `switch_aspect`, Aspect-scoped `compile_aspect_view`/`knowledge_projection` (with `forbidden_events`), and viewpoint-specific cross-Aspect encounter resolution. Never merges viewpoints. |
| `wandering.py` | Phase 20 WANDERING foundation: persistent place entities, consent-safe location sampling, bounded deterministic nearby discovery, place-history accumulation, and privacy/safety projection (`project_place_for_viewer`). |
| `map_provider.py` | Phase 20 map/geocoding provider abstraction (`MockMapProvider` default); the domain model is never married to one map vendor. |
| `comfyui/` | ComfyUI rendering adapter (`client.py`, `workflow_loader.py`, `workflow_binder.py`, `workflow_roles.py`, `storage.py`, `errors.py`, bundled `workflows/`). |
| `vision.py` | Dice photo recognition. **Simulated** (random tentative reads). |
| `auth.py` | bcrypt password hashing, JWT tokens, `get_current_user`. |

### Core game loop

```
Roll (digital /dice/roll, manual /dice/interpret, camera /dice/photo-ingest)
  → numeric faces (validated by Pydantic)
  → versioned grammar → symbolic interpretation
  → encounter frame (/encounters/frame)
  → player intent + approach + Resonance/Strain spend
  → /scenes/resolve → deterministic outcome + narration
  → Chronicle event logged (scene_events)
     + auto-plants a Curiosity seed + auto-logs a Probable Path
```

All REST endpoints are under `/api/v1/`. The one WebSocket endpoint is `/ws/v1/convergence/{room_id}`.

### Persistence

SQLite only, via stdlib `sqlite3`. DB file defaults to `backend/soulsmith_canonical.db`, overridable with the `SOULSMITH_DB_FILE` env var. `db.py` runs `CREATE TABLE IF NOT EXISTS` plus an `_add_column_if_missing` helper — **new columns are appended via this helper, there is no migration framework**. The README and `soulsmith.md` describe Postgres/Qdrant/OpenRouter as the production plan; none of that is wired in (no DB driver in `requirements.txt`).

---

## The canonical roll contract (critical)

This is the single most important rule in the codebase:

- **Numeric dice faces are immutable source of truth.** Symbolic meaning is *derived* through a named grammar version.
- The seven dice are `d20`, `d12`, `d10`, `percentile`, `d8`, `d6`, `d4`. Validation is in `NumericDiceRoll` (`grammar.py`).
- Never let frontend, narration, or any downstream code overwrite the raw numeric values.
- The `VersionedGrammar` model validates that every die face (1..N) is covered by exactly one mapping — adding a grammar must cover all faces or model validation fails.
- The d4 `Thread` vocabulary is intentionally exactly four faces: **Bond, Memory, Mark, Prophecy**. `Portal` and `Debt` are reserved for future Chronicle consequences, not primary d4 faces.
- Full schema/lifecycle is documented in `docs/ROLL_CONTRACT.md`.

---

## Key patterns and conventions

- **Pydantic v2 everywhere.** Use `model_dump()` (never `.dict()`). Request/response models are defined in the domain modules and imported into `main.py`.
- **Adding an endpoint** means touching three places: the route in `main.py`, the model/function in the relevant domain module, and the persistence function in `db.py`.
- **Python files** start with `from __future__ import annotations`. Docstrings at the top of each module.
- **DB functions return dicts** (via `sqlite3.Row`), and are rehydrated into Pydantic models with `Model(**record)` at the route layer.
- **Frontend types** (`src/types.ts`) are a hand-maintained mirror of the backend Pydantic models. When you change a backend model, update `types.ts` and the matching `apiClient` method in `src/lib/api.ts`.
- **`apiClient`** in `src/lib/api.ts` is the only place HTTP calls are made. It attaches the Bearer token from `localStorage` and normalizes the base URL.
- **3D renderer** (`DiceRoller3D.tsx` + `src/three/*`) rebuilds the scene when material/quality settings change and **must dispose all WebGL resources** via `disposeSceneResources.ts` on teardown. See `docs/DICE_RENDERING_SYSTEM.md` for the full renderer contract.

---

## Gotchas (non-obvious, save yourself the trial-and-error)

1. **`npm run test` is not a unit test runner.** It executes `node scripts/run-tests.mjs`, which regex-asserts against the *source text* of `types.ts`, `api.ts`, `diceQualityProfiles.ts`, `resonanceEffects.ts`, `diceMotion.ts`, and `prepareDiceGeometry.ts`. Renaming a symbol or rewording a string can break "tests" with no real coverage. If you change those files, update the assertions in `run-tests.mjs`.

2. **The "AI" is stubbed, except portrait rendering.** `soulkeeper.py` narration is deterministic template prose; `vision.py` dice recognition returns random simulated reads. Portrait generation has a real integration: `SOULSMITH_IMAGE_PROVIDER=comfyui` routes through `backend/app/comfyui/` to a local ComfyUI instance; the `mock` provider is the default and the `external` provider is an unconfigured scaffold. Don't assume the text/vision modules reach a network.

3. **Most game endpoints are not authenticated.** Only `/api/v1/auth/*` and `/api/v1/auth/me` enforce JWT auth. The rest accept `soul_id`/`soul_name` as a query or body param, with hard-coded demo defaults like `"Kaelen the Star-Watcher"` and `"Unbound Soul"`. This is demo-state; do not assume JWT identity propagates into game state.

4. **Backend test isolation is via monkeypatch, not a test DB config.** `tests/conftest.py` has an autouse fixture that sets `SOULSMITH_DB_FILE` to a temp path and clears `app.db._initialized_files`. When you add DB-backed tests, rely on this fixture; don't point at the real DB.

5. **No migration framework.** Schema changes go in `db.py` `_run_init_schema` / `_add_column_if_missing`. Historical columns are appended lazily (e.g. `scene_events.raw_roll_json`, `grammar_version`, `player_intent`, `chosen_approach`, etc.).

6. **Environment variables** (backend): `SOULSMITH_DB_FILE`, `SOULSMITH_JWT_SECRET` (default is a hardcoded dev value — override in production), `SOULSMITH_IMAGE_PROVIDER` (`mock`/`external`/`comfyui`), `SOULSMITH_IMAGE_PROVIDER_API_KEY`, plus the ComfyUI set — `COMFYUI_SERVER_URL`, `COMFYUI_PORTRAIT_INITIAL_WORKFLOW` (text-to-image), `COMFYUI_PORTRAIT_REFERENCE_WORKFLOW` (img2img continuity), `COMFYUI_PORTRAIT_REFERENCE_STRENGTH` (0..1, maps to `denoise = 1 - strength`), `COMFYUI_CHRONICLE_PAINTING_WORKFLOW` (text-to-image Chronicle scenes), `COMFYUI_TIMEOUT_SECONDS`, `COMFYUI_POLL_INTERVAL_SECONDS`, `SOULSMITH_ASSET_ROOT`. Chronicle Paintings also use `SOULSMITH_MOCK_GUARDIAN_VERDICT` (`pass`/`retry`/`block`) and `SOULSMITH_CHRONICLE_MAX_RETRIES` (default 2). Frontend: `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

7. **CORS is wide open** (`allow_origins=["*"]` in `main.py`). This is intentional for local dev but relevant if you touch deployment.

8. **`requirements.txt` has trailing blank lines** and deliberately contains only runtime deps (no DB driver, no AI SDK). Dev/test tooling lives in `requirements-dev.txt` (which includes `-r requirements.txt`).

9. **Do not invent die semantics.** The grammar is fixed in `grammar.py`. The LLM/narration layer must receive the structured interpretation, not improvise its own meaning (this is called out explicitly in `soulsmith.md` and `docs/ROADMAP.md`).

10. **Generated images are SoulSmith-owned.** `main.py` mounts `StaticFiles` at `/assets` (serving `SOULSMITH_ASSET_ROOT`, default `backend/assets/`). The ComfyUI provider copies PNGs into `backend/assets/portraits/candidates/` and stores `/assets/...` URLs, never ComfyUI `/view` URLs. The frontend resolves those relative paths against `API_BASE_URL` via `resolveAssetUrl` in `src/lib/api.ts`. The `mock`/`external` providers return `/assets/...` paths without writing files (pre-existing).

11. **Workflow roles decide initial vs reference.** `comfyui/workflow_roles.py` maps generation types to roles: `initial` → `portrait_initial`; `story_mark_update`/`equipment_update`/`age_update`/`manual_regeneration` → `portrait_reference`. Continuity types *require* a source portrait and fail cleanly (they never silently fall back to text-to-image, which could change the character's identity). The `provider_model` field encodes the role (`soulsmith-comfyui-portrait-initial-v1` vs `...-reference-v1`) so you can tell which workflow produced a candidate.

12. **Continuity is source-portrait-locked.** `portrait_reference.resolve_source_portrait` enforces that a `source_portrait_version_id` is a real, soul-owned, imaged `PortraitVersion`; it never substitutes a newer portrait for the one requested. Approving a candidate creates a *new* `PortraitVersion` and never mutates the referenced one, so historical versions and events referencing them stay intact. The reference-image technique is dependency-free img2img (`LoadImage` + `VAEEncode` + `KSampler` denoise); IPAdapter/FaceID are documented as an optional upgrade, not assumed to exist.

13. **ComfyUI diagnostics** live at `GET /api/v1/visual-memory/providers/comfyui/status` (reachability, initial/reference workflow availability, output-storage writability).

14. **World entities have visual history too.** Phase 4 (`visual_world.py`, `visual_compilers.py`, `world_visual_provider.py`) gives locations, relics, and phenomena immutable `VisualEntityVersion`s and a candidate/review flow mirroring portraits, under `/api/v1/visual-world/*`. Workflow roles come from `comfyui/workflow_roles.py`: locations/phenomena → `environment_{initial,reference}`, relics → `object_{initial,reference}`. Approving a world candidate creates a *new* immutable version (`approve_world_visual_candidate_transaction` is idempotent) and never mutates older ones, so Chronicle scenes can reference the version that actually existed at event time. NPCs reuse the portrait pipeline; `world_event`/Chronicle painting visuals are deferred to a later phase.

15. **Chronicle Paintings are art, not canon.** Phase 12 (`chronicle_paintings.py`, `painting_compiler.py`, `painting_pipeline.py`, `visual_canon_guardian.py`) enforces `CANON -> SCENE SPEC -> IMAGE GENERATION -> VISUAL CANON GUARDIAN -> PLAYER-VISIBLE CANDIDATE`. Raw generated output lands in `backend/assets/chronicle/quarantine/` and is copied into `chronicle/paintings/` only after the Guardian passes. The deterministic mock Guardian can be forced with `SOULSMITH_MOCK_GUARDIAN_VERDICT=pass|retry|block`; retry budget is `SOULSMITH_CHRONICLE_MAX_RETRIES` (default 2). Approving a replacement painting supersedes (never deletes) the prior approved one, and the gallery query returns only approved `public_canon` paintings.

16. **Group Memories link memories without rewriting them.** Phase 13 (`group_memories.py`) enforces `SHARED EVENT != SHARED MEMORY`: canonical grouping is keyed by exact `event_id` only (never semantic similarity — that yields `suggestions`, not members), and every response goes through `project_group_for_viewer` for participant-specific consent filtering. Private participants are omitted (not counted) from public projections; title/summary are re-derived from public facts only. See `docs/GROUP_MEMORIES.md`.

17. **The Biography is derived, never canonical.** Phase 14 (`biography*.py`) enforces `CANON -> SPEC -> NARRATIVE -> REVIEW`, never `BIOGRAPHY -> CANON`. Provenance is stored as normalized `biography_provenance` rows, not an opaque JSON graph; every read goes through `project_biography_for_viewer` for consent filtering. Regeneration always creates a new immutable `biography_versions` row (status `draft`/`current`/`superseded`/`rejected`/`failed`), and only Guardian-passed drafts may become `current`. See `docs/LIVING_BIOGRAPHY.md`.

18. **The Art Director controls interpretation, not canon.** Phase 15 (`art_director.py`, `style_reviewer.py`, `world_gallery.py`) keeps style and canon separate: Art Direction Profiles store only stylistic treatment, updating a profile appends an immutable `art_direction_profile_versions` row, and profile selection on candidate/painting creation is optional (tracked via `art_direction_profile_id`/`art_direction_profile_version_id` columns). The World Gallery (`world_gallery.py`) is a publication surface that returns only approved, consent-safe artifacts; private participants must never leak through images, captions, provenance, counts, or alt text. The optional style reviewer can never override a Visual Canon Guardian BLOCK. See `docs/ART_DIRECTOR_AND_WORLD_GALLERY.md`.

19. **World Memory is derived, never canonical.** Phase 16 (`world_memory.py`, `world_memory_compiler.py`, `world_memory_provider.py`, `world_memory_guardian.py`) turns preserved history into cultural memory (legends, monuments, songs, festivals, relic legends, NPC knowledge) under the invariant **history may become legend, legend must never become history by accident**. World Memory rows (`world_memories`) carry normalized source links, declared deviations, memory-state history, and Legendary Figure links; they never mutate Memory Objects, Group Memories, Biographies, relics, or approved visual history. The World Memory Guardian (pass/retry/block) rejects undeclared drift, undeclared hallucinated facts, private leaks, scoped-perspective omniscience, and unapproved visual references — a declared exaggeration passes, an undeclared one fails. NPC knowledge projection is consent-safe and scoped; an NPC never automatically receives canonical database truth. See `docs/LEGENDARY_FIGURES_AND_WORLD_MEMORY.md`.

20. **The Campaign Orchestrator coordinates, never owns meaning.** Phase 17 (`campaign.py`, `campaign_orchestrator.py`, `campaign_provider.py`) decides *what gets an opportunity to act next*, not *what the player's story means*. It evaluates deterministic, provenance-carrying `CampaignOpportunity`s from structured state before narration; runs an auditable `CampaignTransition` reaction pipeline after each committed event; enforces count-based cooldowns (not wall-clock) so callbacks never become spam; preserves player recognition/rejection (recognize/reject/rename/reinterpret/postpone/hide) without mutating canonical Thread state; surfaces relic-memory/awakening candidates without ever awakening a relic; projects scoped NPC knowledge through Phase 16 rather than raw Chronicle omniscience; and delegates every canonical mutation to the domain system that owns it. Orchestrator rows (`campaign_sessions`, `campaign_opportunities`, `campaign_transitions`, `campaign_reactions`) are bookkeeping, never canonical history. See `docs/CAMPAIGN_ORCHESTRATOR.md`.

21. **The Soulkeeper narrates, never decides what is true.** Phase 18 (`narrative_style.py`, `narrative_context_compiler.py`, `narrative_guardian.py`, `narrative_runtime.py`, plus the Phase 18 pieces of `campaign.py`/`campaign_provider.py`) turns approved structured state into player-facing prose under the invariant **domain systems decide what is true, the Soulkeeper decides how it is told**. Providers receive a bounded `NarrativeContext`, never the whole database; a deterministic narrative Guardian (pass/retry/block) rejects invented participants/events/dates/durations/relic-abilities/Thread-truth/Integration-events/perspective-violations/private-leaks/psychological-authority; retries reuse the same authoritative facts with correction instructions and never widen context; provider failure and malformed output degrade gracefully without corrupting canon. `narrative_generations` rows are bookkeeping/audit (provider, model, `NARRATIVE_TEMPLATE_VERSION`, retry count, validation outcome), never canonical history, and changing a template never rewrites historical prose. See `docs/SOULKEEPER_NARRATIVE_ENGINE.md`.

22. **A relationship is history, a promise is a claim on the future, and neither may be invented by the narrator.** Phase 19 (`relationship.py`, plus the relationship/promise tables and helpers in `db.py`) gives relationships and promises first-class provenance-backed persistence. Relationships derive from canonical interactions and explicit state, never narrative vibes; participant perspectives may differ without becoming objective truth; there is no numeric affection meter that silently becomes canonical. Promises must have a canonical source event or explicit player-authorized creation; their original wording/source is immutable and every state change (kept/broken/fulfilled/released/inherited/transferred/disputed/forgotten/rediscovered) is appended to history. Fulfillment/breach/release/inheritance/transfer are evidence-backed. Relics, Soul Constellation, World Memory, NPC knowledge, and the Campaign Orchestrator (`relationship_callback`/`promise_consequence` candidates) integrate with the engine but never mutate its canon. The Phase 18 narrative Guardian also rejects `invented_promise`/`invented_relationship`/`promise_state_authority`. See `docs/RELATIONSHIPS_AND_PROMISES.md`.

23. **The player may know the whole story; each Aspect knows only the life it has lived.** Phase 20 (`multi_aspect.py`, `wandering.py`, `map_provider.py`, plus the `campaign_aspects`/`aspect_switches`/`places`/`place_history`/`location_consent`/`location_samples`/`wandering_discoveries` tables and `active_soul_id` column in `db.py`) makes the knowledge layers operational during play: `CANONICAL TRUTH != PLAYER KNOWLEDGE != ASPECT KNOWLEDGE != NPC KNOWLEDGE != WORLD MEMORY`. `campaign_sessions` is campaign-level with a mutable `active_soul_id`; `_gather_state` resolves the active Aspect and scopes Seeds/questions/Threads/Chronicle/relationships/promises/relics/World Memory to it via `get_canonical_events_for_soul`/`get_seeds_for_soul`/`get_open_questions_for_soul`. Aspect switching is deterministic and idempotent; it never merges viewpoints or leaks private state. WANDERING is a consent-safe, provider-independent foundation: place entities accumulate `place_history`, location samples require explicit opt-in (`location_consent`), nearby discovery is bounded/deterministic, and precise coordinates are stripped from every public projection unless the viewer is the owner in authorized debug mode. Retiring a place stops new discovery without deleting old history. See `docs/MULTI_ASPECT_AND_WANDERING.md`.

---

## Testing approach

- **Backend:** pytest. Tests import app modules directly and hit route functions (not necessarily via HTTP). One test file per engine subsystem. Use `Model(**record)` rehydration patterns in assertions. Run with `python -m pytest` from `backend/`.
- **Frontend:** no real test framework. `npm run test` is the regex source-assertion script described above. Manual visual QA for the renderer is documented at the bottom of `docs/DICE_RENDERING_SYSTEM.md`.

---

## Where to look first

- Canonical roll / grammar rules → `backend/app/grammar.py`, `docs/ROLL_CONTRACT.md`
- Scene resolution rules → `backend/app/rules.py`
- All API routes → `backend/app/main.py`
- Persistence schema → `backend/app/db.py`
- Frontend API surface → `frontend/src/lib/api.ts`, `frontend/src/types.ts`
- 3D dice renderer → `frontend/src/three/`, `docs/DICE_RENDERING_SYSTEM.md`
- Art direction & gallery → `backend/app/art_director.py`, `backend/app/world_gallery.py`, `docs/ART_DIRECTOR_AND_WORLD_GALLERY.md`
- Legendary Figures & World Memory → `backend/app/world_memory.py`, `backend/app/world_memory_compiler.py`, `backend/app/world_memory_guardian.py`, `docs/LEGENDARY_FIGURES_AND_WORLD_MEMORY.md`
- Campaign Orchestrator & North-Star loop → `backend/app/campaign.py`, `backend/app/campaign_orchestrator.py`, `backend/app/campaign_provider.py`, `docs/CAMPAIGN_ORCHESTRATOR.md`
- Soulkeeper Narrative Engine & Provider Runtime → `backend/app/narrative_style.py`, `backend/app/narrative_context_compiler.py`, `backend/app/narrative_guardian.py`, `backend/app/narrative_runtime.py`, `docs/SOULKEEPER_NARRATIVE_ENGINE.md`
- Relationships & Promises → `backend/app/relationship.py`, `docs/RELATIONSHIPS_AND_PROMISES.md`
- Multi-Aspect sessions & Wandering → `backend/app/multi_aspect.py`, `backend/app/wandering.py`, `backend/app/map_provider.py`, `docs/MULTI_ASPECT_AND_WANDERING.md`
- Current design intent and roadmap → `docs/ROADMAP.md`
