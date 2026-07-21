# SoulSmith Implementation Audit

## Current State

SoulSmith already has a strong vertical prototype:

- React + Vite frontend
- Three.js STL dice sanctuary
- FastAPI backend
- deterministic scene outcome ladder
- placeholder Soulkeeper narration layer
- SQLite Chronicle persistence
- relic, phenomenon, Soulprint, vision, and WebSocket prototypes
- polished visual identity

The project is visually coherent and mechanically suggestive, but several systems currently behave as demonstrations rather than as one complete game loop.

---

## Highest-Priority Design Issue: Dice Face Mapping

The current grammar exposes six symbolic values for most dice, including the d20, d12, d10, d8, d6, and d4. This means the symbolic result is selected from category names rather than from the actual numeric face rolled.

That creates three problems:

1. Physical dice cannot be interpreted consistently from photographed numeric values.
2. The d4 currently contains six possible Thread results, which cannot map directly to four faces.
3. The visual 3D roll, manual entry, and camera scan cannot share one deterministic interpretation contract.

### Required correction

Every roll must first produce numeric values:

```json
{
  "d20": 17,
  "d12": 4,
  "d10": 8,
  "percentile": 70,
  "d8": 3,
  "d6": 5,
  "d4": 2
}
```

A versioned interpretation table must then map each numeric value or range into symbolic meaning.

Example:

```json
{
  "grammar_version": "core-v1",
  "raw_roll": {
    "d20": 17,
    "d12": 4,
    "d10": 8,
    "percentile": 70,
    "d8": 3,
    "d6": 5,
    "d4": 2
  },
  "reading": {
    "spark": "Wonder",
    "domain": "Place",
    "pressure": "Corruption",
    "aim": "Reveal",
    "approach": "Guile",
    "verdict": "Reveal",
    "thread": "Memory"
  }
}
```

The numeric roll must be canonical. The symbolic reading is derived data.

---

## Core Game Loop Target

The first complete playable loop should be:

```text
Create or load Soul
    -> choose world and session
    -> roll digitally, enter manually, or scan a photo
    -> confirm numeric roll
    -> derive symbolic reading
    -> generate encounter frame
    -> state intent and choose approach
    -> invest Resonance / accept Strain / invoke relic
    -> resolve with deterministic rules
    -> generate constrained Soulkeeper narration
    -> review proposed canon changes
    -> commit Chronicle event
    -> update Soul, relics, phenomena, mysteries, and world state
    -> continue from remembered consequences
```

No subsystem should bypass this loop.

---

## System Audit

### 1. Dice Sanctuary

**Already present**

- STL dice rendering
- animated roll presentation
- symbolic description cards
- material controls

**Needed**

- canonical numeric results for all seven dice
- percentile handling as d10 tens plus d10 ones, or one explicit d100 result
- seeded roll option for replay and testing
- manual numeric entry
- roll history
- shared validation schema used by digital, manual, and camera inputs
- grammar version attached to every roll

### 2. Dice Camera

**Already present**

- photo-ingest endpoint and confidence-oriented prototype

**Needed**

- real upload payload rather than a simulated read
- image quality gate
- die detection
- die-type classification
- top-face value recognition
- confidence per die
- correction interface
- explicit player confirmation before canon submission
- training image collection workflow

The camera must never silently create a canonical roll from low-confidence recognition.

### 3. Soul Sheet

**Already present**

- name, calling, origin, desire, fear, wound
- Resonance, Strain, and Thread counters
- relics, bonds, and scars

**Needed**

- persistent database model
- create, edit, archive, and load flows
- Gift, Shadow, Need, Bond, Soulmark, and unanswered questions
- resource constraints enforced server-side
- per-session refresh rules
- progression through story changes rather than conventional XP
- privacy controls for optional birth data

### 4. Encounter Framing

**Current behavior**

The frontend moves directly from a symbolic dice reading to intent selection and scene resolution.

**Needed**

Add an explicit Encounter Frame generated before player action:

```json
{
  "title": "The Lantern Beneath the Harbor",
  "phenomenon_type": "Echo",
  "visible_situation": "A drowned lantern speaks in borrowed voices.",
  "hidden_need": "It wants the erased harbor oath remembered.",
  "stakes": "Each question causes another name to vanish from the quay.",
  "pressure_clock": 2,
  "questions": [],
  "suggested_actions": []
}
```

The frame establishes what exists before the player decides what to do.

### 5. Resolution Engine

**Already present**

- deterministic outcome ladder
- approach match
- Resonance spending
- Strain acceptance
- resource deltas
- fracture threshold

**Needed**

- strict validation against overspending resources
- approach definitions and mechanical strengths
- intent difficulty or pressure tier
- phenomenon escalation effects
- relic invocation modifiers
- bonds, scars, promises, and Soulprint as bounded modifiers
- outcome classes that preserve forward motion
- tests for every score boundary
- distinction between accepted Strain and Strain actually charged

Potential outcome ladder:

1. Transformation
2. Harmony
3. Costly Resonance
4. Revelation Through Dissonance
5. Fracture / Escalation

### 6. Soulkeeper

**Current behavior**

The Soulkeeper is deterministic template prose. The five Canon Guardian gates currently report success unconditionally.

**Needed**

- provider abstraction for OpenRouter and optional local models
- structured JSON output with Pydantic validation
- task-specific prompts
- creative narration separated from rule calculation
- context assembler that retrieves only relevant canon
- retry and repair path for invalid output
- model timeout and fallback narration
- token and cost logging
- no direct database write permissions for the LLM

### 7. Canon Guardian

The Guardian must become an actual pipeline rather than a decorative audit display.

Proposed gates:

1. **Schema Gate**: valid structured output
2. **Rules Gate**: no changes to locked mechanical results
3. **Canon Gate**: no contradiction with known facts
4. **Boundary Gate**: respects tone, safety, and player limits
5. **Memory Gate**: proposed writes are normalized and auditable

Each gate must be capable of failing, repairing, rejecting, or requesting player confirmation.

### 8. Chronicle

**Already present**

- event logging
- event listing
- simple persistent database

**Needed**

- users, worlds, souls, sessions, rolls, encounter frames, choices, outcomes, and canon writes as separate records
- immutable event ledger
- projections for current world state
- event versioning
- entity links for NPCs, locations, relics, mysteries, promises, scars, and phenomena
- rollback or correction events rather than destructive editing
- semantic-memory indexing only after canonical commit

### 9. Relics

**Already present**

- attunement prototype
- stages and overdraw concept
- art assets

**Needed**

- relic instance separate from relic template
- current owner and history
- abilities as structured effects
- awakening condition
- overdraw cost
- fracture behavior
- Chronicle events for every stage change

### 10. Phenomena

**Already present**

- categories and escalation concept

**Needed**

- phenomenon templates and world instances
- hidden need
- visible signs
- escalation clock
- transformation condition
- linked entities and locations
- state transitions caused by Chronicle events

### 11. Convergence

**Already present**

- WebSocket room broadcast prototype

**Needed**

- authenticated room membership
- room host and session state
- per-player confirmed rolls
- convergence deadline and readiness state
- Weaver synthesis schema
- individual hooks for every player
- conflict resolution and reconnect handling
- persistence beyond process memory

### 12. Soulprints

**Already present**

- preview flow and symbolic-affinity concept

**Needed**

- explicit consent
- optionality throughout the application
- proper chart calculation service if retained
- symbolic weighting schema
- adjustable influence level
- birth-data deletion
- no deterministic personality or fate claims

---

## Technical Risks Found

### Hardcoded backend URL

The frontend calls `http://localhost:8000` directly. This should become a typed API client using an environment variable such as `VITE_API_BASE_URL`.

### Open CORS

The backend currently allows all origins with credentials. Production must use an explicit origin allowlist.

### Deprecated startup hook

FastAPI lifespan handling should replace `@app.on_event("startup")`.

### In-memory multiplayer rooms

WebSocket rooms disappear on process restart and cannot scale across workers. Redis pub/sub or another shared room layer will eventually be needed.

### Claims ahead of implementation

The README describes Postgres, vector indexing, YOLO recognition, real Canon Guardian validation, and advanced production status more strongly than the current code demonstrates. Documentation should distinguish implemented, simulated, and planned capabilities.

### Missing test foundation

The deterministic game engine is ideal for comprehensive automated testing, but no test contract is currently visible in the primary project setup.

---

## Recommended Build Order

### Milestone 1: Canonical Roll Contract (Completed)

- raw numeric seven-dice model
- versioned numeric interpretation tables
- digital roll endpoint
- manual entry endpoint or shared validation route
- frontend display of numeric and symbolic values
- unit tests

### Milestone 2: Encounter Frame (Completed)

- structured encounter schema
- deterministic fallback generator
- LLM provider abstraction
- frame-generation endpoint
- encounter presentation before intent selection

### Milestone 3: Complete Resolution Transaction (Completed)

- server-side resource validation
- relic and phenomenon modifiers
- deterministic outcome
- constrained narration
- proposed canon writes
- explicit commit transaction

### Milestone 4: Curiosity & Thread Integration Engine (Completed)

- structured Seed and Open Question database models (`seeds`, `open_questions`, `local_threads`, `integration_events`)
- auto-seed planting and stage progression (*planted → echoed → recognized → integrated → retired*)
- open question tracking with resolution notes
- local thread lifecycle and interactive Integration Event execution
- Curiosity Engine UI view and unit test suite

### Milestone 5: Real Dice Camera Pipeline

- image upload
- recognition provider interface
- confidence correction UI
- confirmed-roll handoff into the same canonical roll contract

### Milestone 6: Convergence

- persistent rooms
- player readiness
- multi-roll Weaver
- shared encounter and Chronicle commit

---

## Immediate Coding Target

The best first code change is to replace `DiceRollRead` as the primary roll object with:

```python
class RawDiceRoll(BaseModel):
    d20: int
    d12: int
    d10: int
    percentile: int
    d8: int
    d6: int
    d4: int

class InterpretedDiceRoll(BaseModel):
    grammar_version: str
    raw: RawDiceRoll
    reading: DiceRollRead
```

All input modes should produce `RawDiceRoll`. Only the grammar service should produce `DiceRollRead`.

That one correction creates a stable foundation for digital rolling, manual rolling, photo recognition, replay, multiplayer convergence, testing, and persistent Chronicle history.

---

## CI Readiness Review — 2026-07-21

The repository now mirrors the GitHub Actions checks locally as closely as the current environment allows.

### Workflow compatibility

- `frontend-ci.yml` uses currently supported checkout and Node setup actions and runs `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build` from `frontend/`.
- `backend-ci.yml` uses currently supported checkout, Python setup, and artifact upload actions before running Ruff, Ruff format checking, and pytest coverage.
- `security.yml` uses currently supported checkout, dependency review, Node setup, and Python setup actions before running npm and pip vulnerability audits.

### Local verification notes

Frontend CI checks passed locally on Node with the existing lockfile. Vite emits a large-chunk advisory for the production bundle, but it does not fail the build.

Backend formatting initially drifted in three files and has been normalised with `ruff format`. The local Python package index blocked installation of currently requested development dependencies, so the full coverage command could not be completed in this container. The GitHub-hosted workflow should install from normal package infrastructure and then execute the canonical `python -m pytest backend --cov=backend/app --cov-report=xml` command.

### Maintainer checklist

Run the following before opening or merging future changes:

```bash
# Backend
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt
ruff check backend
ruff format --check backend
python -m pytest backend --cov=backend/app --cov-report=xml

# Frontend
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build

# Security
npm audit --audit-level=high
cd ..
python -m pip install --upgrade pip pip-audit
pip-audit -r backend/requirements.txt --severity high
```
