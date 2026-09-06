<div align="center">

# ✦ SOULSMITH ✦

### Roll the spark. Write the legend.

**A living mythology engine where seven dice, shared imagination, and AI forge stories that remember.**

[![Project Status](https://img.shields.io/badge/status-playable%203D%20STL%20engine-46cbff?style=for-the-badge)](#project-status)
[![Game Type](https://img.shields.io/badge/game-collaborative%20storytelling-d7aa55?style=for-the-badge)](#what-is-soulsmith)
[![AI](https://img.shields.io/badge/AI-Soulkeeper-837cff?style=for-the-badge)](#the-soulkeeper)

[Website](https://quantummindsunited.com/soulsmith/) · [Vision](#the-vision) · [How It Works](#how-it-works) · [Roadmap](#roadmap)

</div>

---
<img width="1037" height="1287" alt="image" src="https://github.com/user-attachments/assets/37a9cdd3-0222-4379-9ad0-a94cda6e3b24" />


## The Vision

Most role-playing games invite players into a world that has already been written.

**SoulSmith begins with an empty table, seven dice, and a question:**

> What kind of mythology will emerge when chance provides the fragments, people provide the choices, and the world remembers what happened?

A roll may reveal an Oracle beneath a crystal shop, a forgotten memory guarded by an Inventor, or a relic that points toward questions no one has learned how to ask.

The dice provide the spark.

The players decide what it means.

The **Soulkeeper** connects the fragments, guides the encounter, and records what becomes canon.

Months later, that same Oracle may return. The forgotten city may have changed. A relic discovered by one player may become the missing piece in another player's story.

SoulSmith is not merely a storytelling game.

It is a **persistent AI-generated mythology**.

---

## What Is SoulSmith?

SoulSmith is a collaborative narrative game for solo players, small groups, gatherings, and eventually connected communities.

It combines:

- A 3D STL seven-die RPG set (`d20`, `d12`, `d10`, `d%`, `d8`, `d6`, `d4`)
- Player-driven storytelling
- AI-assisted interpretation & 5-Gate Canon Guardian
- Persistent world memory (SQLite / Postgres DB)
- Evolving relics, locations, relationships, and mysteries
- Optional astrological character resonance
- Real-time WebSocket multiplayer story convergence

There is no required game master and no enormous rulebook standing between the players and the first strange thing that happens.

Players roll, discover, decide, converge, and remember.

<img width="1311" height="1775" alt="image" src="https://github.com/user-attachments/assets/4ecec4f9-1b58-4513-ba91-199186784f9b" />

---

## The Seven-Dice Language

Every die contributes a different dimension to the encounter.

| Die | Narrative Function | Example |
|---|---|---|
| **d20** | What is discovered | Memory, fear, wisdom, power, destiny |
| **d12** | Where it happens | Hall of Echoes, Starforge, Dream Forest |
| **d10** | Intensity | Faint, rising, powerful, overwhelming |
| **d%** | Rarity and significance | Common, rare, legendary, world-changing |
| **d8** | Who or what is encountered | Oracle, Guardian, Inventor, Trickster |
| **d6** | Element or emotional energy | Fire, water, air, earth, light, shadow |
| **d4** | Outcome or narrative turn | Blessing, challenge, clue, transformation |

A roll does not produce a pass-or-fail result.

It produces a **story grammar**.

```text
Discovery + Place + Intensity + Rarity + Presence + Energy + Turn
                              ↓
                       Mythic Encounter
```

Example:

> Beneath the Hall of Echoes, an Inventor guards a forgotten memory. The encounter carries the energy of Light, but the memory can only be restored through Transformation.

The interpretation opens the story. It does not close it.

---

## How It Works

### 1. Roll

Cast all seven dice in the 3D STL Polyhedral Sanctuary to generate the raw structure of an encounter.

### 2. Discover

The Soulkeeper interprets the result using the current location, player histories, active mysteries, relics, relationships, and world state.

### 3. Decide

Players ask questions and choose how to engage.

An encounter may be:

- Understood
- Transformed
- Released
- Healed
- Joined
- Resisted
- Escaped
- Confronted

Violence may exist, but it is one possible language rather than the entire dictionary.

### 4. Converge

In multiplayer sessions, separate rolls are woven into one shared event over WebSockets.

```text
Player One: Oracle + Water + Transformation
Player Two: Lost Memory + Light + Challenge
Player Three: Guardian + Shadow + Clue
                              ↓
A Guardian sealed the Oracle's memory beneath a flooded archive.
One player can find it. One can restore it. One may be the reason it was erased.
```

### 5. Remember

Important events are written into the World Chronicle.

The mythology persists.

---

## The Soulkeeper

The **Soulkeeper** is the player-facing intelligence at the center of SoulSmith.

It is not merely a fantasy text generator. It is responsible for continuity, interpretation, pacing, consequence, and memory.

```text
                         SOULKEEPER
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   Interpreter             Weaver              Chronicler
        │                     │                     │
   Dice + Soulprint      Convergence         Persistent Canon
        │
  Resonance Guide
```

Internally, the Soulkeeper can be divided into specialized roles:

### Interpreter

Decodes dice rolls using the current narrative context.

### Weaver

Finds thematic connections between multiple players and unresolved world events.

### Chronicler

Stores and retrieves canon, including locations, NPCs, relics, promises, scars, factions, and mysteries.

### Resonance Guide

Runs encounters and determines how player choices transform relationships and world state.

### Worldsmith

Creates new phenomena, locations, entities, relics, and consequences without contradicting established history.

### Astrologer

Calculates optional symbolic affinities from player birth information and supplies them to the Interpreter as narrative weights.

---

## Astrological Soulprints

Players may optionally enter their birth date, time, and place to create an **Astrological Soulprint**.

This is not intended to dictate behavior, predict a player's future, or lock anyone into an astrological class.

It acts as a symbolic character lens.

A Soulprint may influence:

- Elemental affinities
- Starting archetypes
- Resonant locations
- Recurring themes
- Shadow material
- Relic compatibility
- Multiplayer convergence patterns
- Celestial timing for special events

Example:

```text
Strong Water emphasis
Transformation resonance
Affinity with hidden places and memory phenomena
Tension between preservation and release
Higher resonance with Veils, Wells, and Echoes
```

The player always retains agency. Astrology adds texture, not rails.

---

## The Soul Sheet & Character Arsenal

SoulSmith characters are defined by lived history and mythic gear rather than stacks of combat statistics.

A Soul Sheet contains:

```text
Calling & Avatar Portrait (10 Framed NPC / Ally Portraits)
Resonance (6/6 Token Pool)
Strain (6/6 Load Counter)
Threads (5/5 Continuity Tokens)
Astrological Soulprint
Relics & Artifacts (25 Mythic Relic Cards)
Scars & Promises
Unanswered Questions
```

A developed character might be described as:

> Keeper of the Compass of Better Questions  
> Friend of the Silent Archivist  
> Marked by the Weeping Door  
> Known within the Starforge  
> Still pursued by the King Without a Reflection

---

## Phenomena, Not Monster Lists

SoulSmith encounters are built around phenomena with motives, needs, origins, and transformation conditions.

### Echoes

Memories, emotions, or events that continue repeating.

### Knots

Conflicts and promises bound together so tightly that force only strengthens them.

### Veils

Hidden truths, altered perceptions, and thresholds between realities.

### Wells

Sources of power, healing, corruption, knowledge, or longing.

### Awakenings

Dormant places, beings, abilities, or truths beginning to stir.

Each phenomenon includes:

- Origin
- Visible signs
- Hidden need
- Escalation meter
- Transformation condition
- Reward or consequence

---

## Relics That Evolve

Relics are not disposable loot.

They carry history and awaken through use.

```text
Dormant → Remembered → Awakened → Overdrawn → Fractured
```

A simple compass may begin by allowing a reroll.

Later, it may reveal hidden relationships between events.

Eventually, it may allow a player to change the question governing an entire encounter.

---

## Game Modes

### Solo Journey

A guided imagination experience for one player and the Soulkeeper.

### Fireside

A small group gathers around a table and creates a shared Chronicle.

### Wandering

Players roll in real-world locations and allow those places to enter the mythology.

### Chronicle

A continuing campaign focused on persistent history and evolving relationships.

### Gathering

A larger event where many players contribute rolls to one unfolding legend.

---

## Architecture & Technical Stack

```text
Web / Mobile Client (React, Vite, Three.js 3D STL Engine, Tailwind)
        │
        ▼
Game Session API (FastAPI, Python 3.10+)
        │
        ├── 3D STL Dice Engine (STLLoader, MeshPhongMaterial, Glass Optics)
        ├── Computer Vision Optical Scanner (YOLO & OpenCV Ingest)
        ├── Soul Sheet & Relics Ledger (25 Extracted Artifacts)
        ├── Resonance & Strain Engine
        └── WebSocket Convergence Room Manager
        │
        ▼
Soulkeeper Orchestrator
        │
        ├── Interpreter & Weaver
        ├── Chronicler & 5-Gate Canon Guardian
        └── Astrologer
        │
        ▼
World Memory (SQLite / Postgres DB + Vector Storage)
```

---

## Quickstart & Running Locally

### 1. Backend Engine (FastAPI & Python)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

* API Health Check: `http://localhost:8000/api/v1/health`
* Optical CV Photo Ingest API: `POST /api/v1/dice/photo-ingest`
* Phenomena Codex API: `GET /api/v1/phenomena`
* Relic Attunement API: `POST /api/v1/relics/attune`
* WebSocket Convergence Endpoint: `ws://localhost:8000/ws/v1/convergence/{room_id}`

### 2. Frontend Web Application (React, Vite, Three.js 3D STL Engine)

```bash
cd frontend
npm install
npm run dev
```

* Local Web App URL: `http://localhost:5173`

---

## Project Status

SoulSmith is at **Advanced Playable Production Engine (Phase 1–4 Complete Core)**.

Key Features Built:
1. **3D STL Polyhedral Dice Sanctuary**: Real-time Three.js `STLLoader` engine for 6 custom polyhedral STL dice (`d20.stl`, `d12.stl`, `d10.stl`, `d8.stl`, `d6.stl`, `d4.stl`) with translucent sapphire resin optics, clearcoat gloss, transparent glass mode toggle, custom hex color picker, and opacity slider.
2. **Static Under-Dice Floating Descriptions**: Camera-facing, non-rotating description badges floating underneath each 3D STL die displaying Category (*WHAT*, *WHERE*, etc.), pure white embossed outcome values, and discovery sub-descriptions.
3. **Pure White Embossed Numerals**: High-contrast white embossed text rendered on 3D STL meshes and 2D dice cards.
4. **Extracted Relic & Art Pack**: 25 mythic relic icons, 10 framed NPC portraits, 10 elemental essences, 10 action icons, and 10 weapons extracted from official high-resolution artwork (`recils-art-assets.png`).
5. **Optical CV Camera Scanner**: Computer Vision photo ingest & YOLO face confidence detection with 1-tap face overrides.
6. **Living Phenomena Codex**: World-scale non-monster encounters (*Echoes, Knots, Veils, Wells, Awakenings, Rifts, Storms*) with escalation meters, hidden needs, and transformation payoffs.
7. **Relic Attunement Ledger**: Evolving relic lifecycle management (*Dormant → Remembered → Awakened → Overdrawn → Fractured → Transfigured*).
8. **Canon Guardian 5-Gate Audit**: Automated verification (*Schema, Rules, Canon Contradictions, Moderation, Memory Routing*).
9. **Persistent SQLite/Postgres Database**: Transactional event chronicle logging (`worlds`, `souls`, `scene_events`, `seeds`, `open_questions`, `local_threads`, `integration_events`).
10. **Real-time Convergence Sanctuary**: WebSocket multi-player room role rotation (*Focus, Anchor, Witness, Tempest*).
11. **Curiosity & Thread Integration Engine**: Persistent Seed planting and symbol tracking (*planted → echoed → recognized → integrated → retired*), open questions tracking with evidence logs, local thread evidence accumulation, and interactive Integration Events that transform player choices into canonical world progression.
12. **Soul Constellation Engine**: Multi-Aspect identity management across eras, shared Deep Threads, Constellation Anchors, Cross-Aspect Bonds (scars, promises, memory echoes), and interactive Awakening Stage progression (*Veiled → Echoing → Recognizing → Resonant → Woven → Lucid*).
13. **Probable Paths Engine**: Automatic persistence of unchosen approaches, probability branch tracking, manifestation state transitions (*Dreams, Rumors, Alternate Scenes, Echo Aspects*), and interactive "What-If" scene simulations while preserving canonical event integrity.
14. **User Authentication & Token System**: Full user registration, password hashing (`bcrypt`), JWT token generation/validation, profile retrieval (`/api/v1/auth/me`), local storage token management, and custom authentication header badge in the frontend UI.
15. **Relic Recognition Engine & Ledger**: Narrative-driven relic attunement based on Chronicle evidence, full 6-stage lifecycle management (*Dormant → Remembered → Awakened → Overdrawn → Fractured → Transfigured*), evocative dormant question prompts, overdraw strain/fracture mechanics, narrative fracture repair, and cross-Aspect Constellation Anchors.
16. **Convergence & Community Mythology Engine**: Multi-player gathering sessions where multiple rolls contribute to evolving phenomena, role rotation (*Focus, Anchor, Witness, Tempest*), world-level community symbols, consent-aware canon merge controls, and explicit private campaign forking.
17. **Reflection & Accessibility Control Vault**: Optional end-of-session narrative reflection prompts with explicit AI opt-in toggles, secure vault for private notes strictly excluded from AI models, narrative intensity levels (*Gentle, Balanced, Deep Mythic, Unfiltered*), spiritual framing options, reduced motion & high contrast accessibility toggles, and JSON data export sovereignty.
18. **Visual Identity Foundation & Timeline Canon**: Structured avatar identity persistence (*Face, Hair, Body, Species, Eyes*), provenance-backed Story Marks linked to canonical event IDs, equipment appearance layers, and immutable portrait timeline snapshots that preserve historical states.
19. **Portrait Generation & Continuity Workflow**: Deterministic portrait prompt compilation, provider-abstracted candidate generation, review states (*pending → generated → approved/rejected/failed*), idempotent approval into canonical versions, and continuity safeguards that keep earlier portraits unchanged.
20. **Chronicle Memory Object Pipeline**: Auditable `MemoryObject` compilation with participant event-time portrait locking, strict portrait reference validation, significance scoring for painting eligibility, public-canon consent enforcement, and automatic real-person tag redaction when consent is missing.
21. **ComfyUI Portrait Generation**: Pluggable image provider (`mock`, `external`, `comfyui`) with static API-format workflows, a workflow-role selector (`initial` vs `reference`), deterministic seed handling, and SoulSmith-owned image storage — generated PNGs are archived under `/assets/` rather than left on ComfyUI `/view`.
22. **Reference-Image Character Continuity**: Approved historical `PortraitVersion`s are resolved, uploaded, and bound into an img2img workflow with a configurable reference strength, so story-mark, equipment, and age updates keep the same recognisable character while only applying the canonical change.
23. **Visual Worldsmith (World Atlas)**: Persistent visual identities for locations, relics, and phenomena — immutable `VisualEntityVersion`s, deterministic world-entity compilers with visual anchors, a canonical-delta diff, environment/object workflow roles, and a reviewable candidate flow that never rewrites history.
24. **Chronicle Paintings & Visual Canon Guardian**: Canonical Memory Objects compiled into generated scene paintings through a `CANON → SCENE → IMAGE → VISUAL CANON GUARDIAN → CANDIDATE` pipeline — historical participant portrait locking, a deterministic composition selector, quarantine-then-promote storage, mandatory vision review with a deterministic mock Guardian (PASS/RETRY/BLOCK), and an approval flow that supersedes prior art without deleting history.
25. **Group Memories & Tags**: A relational `GroupMemory` linking participant-specific Memory Objects to the same shared event without rewriting them — deterministic exact-event-ID grouping, typed ID-anchored tags, shared anchors locked to historical visual versions, participant-specific consent filtering, and a narrative "everyone remembers the same moment differently" perspective view. See [`docs/GROUP_MEMORIES.md`](docs/GROUP_MEMORIES.md).
26. **Living Biography**: An evolving, provenance-aware life story derived from the Chronicle (never rewriting it) — a deterministic structured compiler, immutable version/section/provenance model, chronology without invented dates, recurring-thread extraction, fact-vs-perspective classification, a deterministic narrative provider, a Biography Guardian, draft/current/version lifecycle, consent-aware public/private publication, and a reading experience with expandable "From the Chronicle" provenance. See [`docs/LIVING_BIOGRAPHY.md`](docs/LIVING_BIOGRAPHY.md).
27. **Art Director & World Gallery**: Persistent, versioned Art Direction Profiles that give portraits, world visuals, and Chronicle artwork a coherent visual language *without changing what they depict* — a deterministic style hierarchy and inspectable Art Direction Spec, honest provider-capability degradation, an optional style reviewer that can never override a Visual Canon Guardian BLOCK, and a consent-safe, accessible World Gallery with curated Collections and immutable timelines. See [`docs/ART_DIRECTOR_AND_WORLD_GALLERY.md`](docs/ART_DIRECTOR_AND_WORLD_GALLERY.md).

---

<div align="center">

## Begin with nothing. Leave a legend.

**The dice spark it. You write the legend.**

[Explore SoulSmith](https://quantummindsunited.com/soulsmith/)

</div>

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Useful backend checks:

```bash
python -m pytest
ruff check .
ruff format --check .
```

### Frontend

Create `frontend/.env` from `frontend/.env.example` when the API URL differs from local defaults.

```bash
cd frontend
npm ci
npm run dev
```

Useful frontend checks:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## Running with ComfyUI

SoulSmith renders portrait candidates through a pluggable image provider. By default it uses the deterministic `mock` provider (no external service). To generate real images locally, point it at a running [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance:

```bash
# 1. Start ComfyUI separately on port 8188 (outside this repo).

# 2. Point SoulSmith at it.
export SOULSMITH_IMAGE_PROVIDER=comfyui
export COMFYUI_SERVER_URL=http://127.0.0.1:8188
export COMFYUI_PORTRAIT_INITIAL_WORKFLOW=portrait_initial_v1_api.json
export COMFYUI_PORTRAIT_REFERENCE_WORKFLOW=portrait_reference_v1_api.json
export COMFYUI_PORTRAIT_REFERENCE_STRENGTH=0.75

# 3. Start the backend.
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The Visual Memory "Synthesize Imagery" action then submits the compiled prompt to ComfyUI, polls for completion, copies the generated PNG into SoulSmith-owned storage, and returns a candidate `generated_image_url` for the existing Approve/Reject flow.

### ComfyUI details

- **Workflow files** live at `backend/app/comfyui/workflows/`. They must be ComfyUI **API-format** JSON (a top-level map of `node_id -> {class_type, inputs}`), not the default UI export (which carries `nodes`/`links` arrays). Two roles are bundled:
  - `portrait_initial_v1_api.json` — plain text-to-image (no reference).
  - `portrait_reference_v1_api.json` — reference image-to-image continuity (`LoadImage` → `VAEEncode` → `KSampler` with a `denoise` derived from reference strength → `VAEDecode` → `SaveImage`).
- **Workflow roles** are selected centrally in `backend/app/comfyui/workflow_roles.py`: `initial` → `portrait_initial`; `story_mark_update` / `equipment_update` / `age_update` / `manual_regeneration` → `portrait_reference`. Continuity types *require* a source portrait and fail cleanly (never silently fall back to text-to-image).
- **Node bindings** map SoulSmith concepts to workflow inputs and are declared in `backend/app/comfyui/workflow_binder.py`:
  - Base `DEFAULT_PORTRAIT_BINDINGS`:
    - `positive_prompt` -> node `6` `CLIPTextEncode.text`
    - `negative_prompt` -> node `7` `CLIPTextEncode.text`
    - `seed` -> node `10` `KSampler.seed`
    - `filename_prefix` -> node `24` `SaveImage.filename_prefix`
  - `REFERENCE_PORTRAIT_BINDINGS` add:
    - `reference_image` -> node `11` `LoadImage.image` (uploaded reference filename)
    - `denoise` -> node `10` `KSampler.denoise` (derived from `COMFYUI_PORTRAIT_REFERENCE_STRENGTH` as `denoise = 1 - strength`)
- **Reference-image continuity**: when a continuity candidate carries a `reference_image_url` (resolved from its `source_portrait_version_id` at creation), the provider uploads the approved historical portrait to ComfyUI (`/upload/image`) and binds it into the reference workflow. Files are resolved from `SOULSMITH_ASSET_ROOT` with path-traversal protection.
- **Reference strength** (`COMFYUI_PORTRAIT_REFERENCE_STRENGTH`, `0..1`, default `0.75`) controls how strongly the reference is preserved; higher = closer to the source portrait. It maps to `KSampler.denoise = 1 - strength`.
- **Diagnostics** are exposed at `GET /api/v1/visual-memory/providers/comfyui/status` (reachability, workflow availability, output-storage writability).
- **Generated images** are saved to `backend/assets/portraits/candidates/` (configurable via `SOULSMITH_ASSET_ROOT`) and served by the backend at `/assets/...`. ComfyUI `/view` URLs are never stored as canonical image URLs.
- **Switch back to mock mode** with `unset SOULSMITH_IMAGE_PROVIDER` (or set it to `mock`).

### ComfyUI environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SOULSMITH_IMAGE_PROVIDER` | `mock` | Selects the provider (`mock`, `external`, or `comfyui`). |
| `COMFYUI_SERVER_URL` | `http://127.0.0.1:8188` | ComfyUI server base URL. |
| `COMFYUI_PORTRAIT_INITIAL_WORKFLOW` | `portrait_initial_v1_api.json` | Text-to-image workflow (resolved under `workflows/`) or absolute path. |
| `COMFYUI_PORTRAIT_REFERENCE_WORKFLOW` | `portrait_reference_v1_api.json` | Reference img2img workflow for continuity generations. |
| `COMFYUI_PORTRAIT_REFERENCE_STRENGTH` | `0.75` | How strongly the reference is preserved (0..1); maps to `denoise = 1 - strength`. |
| `COMFYUI_TIMEOUT_SECONDS` | `180` | Maximum time to wait for a generation. |
| `COMFYUI_POLL_INTERVAL_SECONDS` | `1` | Delay between completion polls. |
| `SOULSMITH_ASSET_ROOT` | `backend/assets` | SoulSmith-owned directory for generated images. |

### Reference-image technique

The bundled reference workflow uses a dependency-free **img2img** approach (`LoadImage` + `VAEEncode` + `KSampler` with `denoise < 1`), so it works on a stock ComfyUI install with no custom nodes. The checkpoint (`v1-5-pruned-emaonly.safetensors`) must exist in your `models/checkpoints/` directory, or you can export your own workflow and update the node bindings.

For stronger identity preservation you may later swap in an IPAdapter / InstantID / FaceID workflow (which require custom nodes under `ComfyUI/custom_nodes/`). SoulSmith only cares that a generation *has* a reference portrait; the workflow owns the technique. Administrators install those custom nodes explicitly — the application never auto-installs them.

## Character continuity

SoulSmith keeps a character visually recognisable across time:

```text
Initial Portrait
    → approve → PortraitVersion v1 (immutable)
        → later generations reference v1 as visual guidance
            → new candidate → approve → PortraitVersion v2
```

- **Continuity generations** (`story_mark_update`, `equipment_update`, `age_update`, `manual_regeneration`) require a `source_portrait_version_id` and render through the reference workflow, preserving facial structure, species, eyes, hair, and existing canonical marks while applying only the requested change.
- **Historical integrity** is preserved: approving a candidate creates a *new* `PortraitVersion` and never mutates the referenced one, so `v1` remains independently retrievable and events referencing `v1` keep using it.
- The compiled prompt is sectioned into `CANONICAL IDENTITY`, `CANONICAL CHANGES`, `MUST PRESERVE`, `MUST NOT INVENT`, and `ARTISTIC FRAMING`, with reinforced continuity instructions and negative constraints for reference generations.

## Visual Worldsmith (World Atlas)

Beyond character portraits, SoulSmith gives world entities a persistent visual memory: **locations**, **relics**, and **phenomena** each have immutable visual versions that evolve only through canonical state changes.

```text
CANON → visual snapshot → candidate → ComfyUI → generated representation
        → human approval → immutable VisualEntityVersion
```

- **Entity types**: `location` (environment workflows), `relic` (object workflows), `phenomenon` (environment workflows). NPCs reuse the portrait pipeline.
- **Visual anchors** (landmarks, persistent details, motifs) are compiled into every prompt so an evolved version stays recognisably the same place/object/phenomenon.
- **Canonical delta** diffs the previous vs current snapshot into `PRESERVE` / `CHANGE` / `REMOVE` so continuity generations apply only the recorded change.
- **Historical integrity**: approving a new version creates a new immutable `VisualEntityVersion` and never mutates older versions.

### World API

```text
POST /api/v1/visual-world/candidates
POST /api/v1/visual-world/candidates/{candidate_id}/generate
POST /api/v1/visual-world/candidates/{candidate_id}/approve
POST /api/v1/visual-world/candidates/{candidate_id}/reject
GET  /api/v1/visual-world/{entity_type}/{entity_id}/versions
GET  /api/v1/visual-world/{entity_type}/{entity_id}/candidates
```

Generated assets are stored under `/assets/world/{entity_type}/candidates/` (SoulSmith-owned, never ComfyUI `/view` URLs).

### World workflow roles & configuration

| Role | Workflow file | Used by |
|---|---|---|
| `environment_initial` / `environment_reference` | `environment_*_v1_api.json` | locations, phenomena |
| `object_initial` / `object_reference` | `object_*_v1_api.json` | relics |

| Variable | Default | Purpose |
|---|---|---|
| `COMFYUI_ENVIRONMENT_INITIAL_WORKFLOW` | `environment_initial_v1_api.json` | Landscape environment text-to-image. |
| `COMFYUI_ENVIRONMENT_REFERENCE_WORKFLOW` | `environment_reference_v1_api.json` | Landscape environment img2img continuity. |
| `COMFYUI_OBJECT_INITIAL_WORKFLOW` | `object_initial_v1_api.json` | Square object text-to-image. |
| `COMFYUI_OBJECT_REFERENCE_WORKFLOW` | `object_reference_v1_api.json` | Square object img2img continuity. |
| `COMFYUI_WORLD_REFERENCE_STRENGTH` | `0.6` | Reference preservation strength (maps to `denoise = 1 - strength`). |

## Art Director & World Gallery

Phase 15 unifies the approved visual history (portraits, world visuals, Chronicle
Paintings, Group Memories, and the Living Biography) into a coherent art-direction
system and an explorable World Gallery, without letting style rewrite canon.

```text
CANON + HISTORICAL VISUAL REFERENCES + ART DIRECTION
    -> GENERATION -> VISUAL CANON GUARDIAN -> APPROVAL -> WORLD GALLERY
```

- **Art Direction Profiles** are persistent and versioned; updating always creates
  a new version and older artwork keeps its original instructions. Profiles store
  only stylistic treatment, never canonical facts.
- **Style hierarchy** (`World -> artifact-type treatment -> override`) resolves
  deterministically into an inspectable Art Direction Spec with canonical and
  stylistic requirements kept separate.
- **Provider capability awareness** degrades honestly instead of pretending
  unsupported capabilities exist.
- **Optional style reviewer** checks profile compliance but can never override a
  Visual Canon Guardian BLOCK.
- **World Gallery** curates only approved, consent-safe artifacts across modes
  (The World, The People, The Chronicle, Shared Moments, A Life, Then & Now), with
  provenance, curated Collections, immutable timelines, conservative alt text,
  keyboard navigation, reduced motion, and lazy-loaded images.

```text
POST  /api/v1/art-direction/profiles
POST  /api/v1/art-direction/profiles/{profile_id}/versions
POST  /api/v1/art-direction/resolve
POST  /api/v1/art-direction/preview
GET   /api/v1/gallery?mode=world|people|chronicle|shared|life|all
GET   /api/v1/gallery/timeline?entity_type=...&entity_id=...
POST  /api/v1/gallery/collections
POST  /api/v1/gallery/collections/{id}/reorder
```

See [`docs/ART_DIRECTOR_AND_WORLD_GALLERY.md`](docs/ART_DIRECTOR_AND_WORLD_GALLERY.md).

## Canonical Roll Contract

SoulSmith now treats the seven numeric dice faces as the immutable roll record. Symbolic values are derived through a versioned grammar and persisted alongside the raw values in the Chronicle. See [`docs/ROLL_CONTRACT.md`](docs/ROLL_CONTRACT.md) for schemas, workflows, compatibility policy, and the initial `1.0.0` vocabulary.
