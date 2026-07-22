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

## Canonical Roll Contract

SoulSmith now treats the seven numeric dice faces as the immutable roll record. Symbolic values are derived through a versioned grammar and persisted alongside the raw values in the Chronicle. See [`docs/ROLL_CONTRACT.md`](docs/ROLL_CONTRACT.md) for schemas, workflows, compatibility policy, and the initial `1.0.0` vocabulary.
