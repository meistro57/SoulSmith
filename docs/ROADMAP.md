# SoulSmith Roadmap

> **Mission:** Plant seeds of curiosity. Trust the player to grow the forest.

SoulSmith is evolving from an AI-assisted narrative RPG into a **persistent myth-making engine**. Its systems should not preach a worldview or hand players predetermined answers. They should create encounters, echoes, choices, and consequences that help players notice their own patterns and become curious about what those patterns mean.

The core progression principle is:

> **Experience can be accumulated. Transformation must be integrated.**

A player does not level merely because enough events occurred. Growth appears when choices, consequences, reflection, and recognition form a meaningful pattern.

---

## Product Pillars

### 1. Curiosity Before Explanation

The Soulkeeper should reveal enough to invite a better question, not enough to close interpretation.

- Prefer evocative clues over exposition dumps.
- Let recurring symbols gain meaning through context.
- Never require the player to accept a spiritual, psychological, or philosophical interpretation.
- Preserve ambiguity where ambiguity deepens participation.

### 2. Recognition as Progression

SoulSmith progression is not primarily numerical.

- Experiences create potential for growth.
- Repeated choices form patterns.
- Reflection makes patterns visible.
- Integration changes future possibilities.
- Abilities, relics, and Threads awaken when the narrative supports readiness.

### 3. The Chronicle as a Mirror

The Chronicle is more than a quest log. It is the persistent memory through which players can notice:

- repeated choices,
- unresolved promises,
- recurring symbols,
- transformed relationships,
- probable paths not taken,
- echoes across multiple Aspects.

### 4. Agency Without Doctrine

SoulSmith may explore identity, belief, probability, memory, and transformation, but it must not tell players what those ideas mean.

The world demonstrates hidden laws through play. The player decides how to interpret them.

### 5. Immutable Rolls, Evolving Meaning

The seven numeric dice faces are the canonical event seed. Their symbolic interpretation is derived through a versioned grammar.

This supports replay, multiplayer convergence, physical dice, digital dice, camera scanning, and future vocabulary revisions without rewriting history.

---

## The Hidden Laws

These are design laws, not teachings presented to the player.

### Identity

A playable character is one perspective within a potentially larger pattern of identity.

### Belief

Repeated assumptions influence what a character notices, attempts, fears, and makes possible.

### Probability

Unchosen possibilities remain narratively meaningful and may return as dreams, echoes, alternate Aspects, or transformed opportunities.

### Memory

The past is persistent but not inert. Its meaning can change when viewed from a new perspective.

### Attention

What players repeatedly investigate becomes more detailed, connected, and consequential.

### Transformation

Change becomes durable when a pattern is recognized and expressed through a new choice.

---

## Soulkeeper Direction: The Curiosity Engineer

The Soulkeeper is not a teacher, guru, or authorial mouthpiece. It is a **Curiosity Engineer** and mythic facilitator.

Its job is to:

1. notice meaningful patterns,
2. preserve continuity,
3. turn patterns into playable symbols,
4. present choices without prescribing conclusions,
5. reward deeper questions with deeper relationships and possibilities,
6. recognize integration without reducing it to a morality score.

### Soulkeeper Success Signals

Future evaluation should measure more than completion or retention.

- Did the encounter produce a meaningful question?
- Did the player notice a recurring pattern?
- Did a previous choice gain new meaning?
- Did the player act differently after recognition?
- Did the world respond coherently to that change?

These signals must remain player-centered and non-manipulative.

---

## Progression Model

### Local Threads

Patterns tied to one character, place, relationship, promise, or unresolved event.

Examples:

- fear of being forgotten,
- loyalty to a particular community,
- a promise made to an NPC,
- an unanswered question surrounding a relic.

### Deep Threads

Patterns that persist across multiple Aspects, eras, worlds, or probable selves.

Deep Threads should emerge gradually. They are inferred from Chronicle evidence rather than selected from a class menu.

### Integration Events

An Integration Event occurs when accumulated experience is expressed through a meaningful new choice.

It may:

- transform a Thread,
- awaken a relic,
- reveal a Constellation connection,
- alter the interpretation of an earlier memory,
- open or close a probable path,
- change how the Soulkeeper frames future encounters.

Integration must never be equated with one universally correct behavior. The same pattern may transform differently for different players.

---

## Soul Constellation

Players may eventually discover that multiple playable **Aspects** belong to a larger Soul Constellation.

An Aspect is a complete playable identity, not a disposable avatar. Different Aspects may exist in different eras, worlds, cultures, or probable histories.

### Constellation Sheet

The future Constellation model should track:

- Known Aspects
- Local Threads
- Deep Threads
- Recurring Symbols
- Cross-Aspect Bonds
- Constellation Anchors
- Inherited Scars and Promises
- Unresolved Pattern
- Awakening Stage

### Awakening Stages

1. **Veiled**: one life appears self-contained.
2. **Echoing**: symbols and patterns recur without explanation.
3. **Recognizing**: the player identifies relationships between echoes.
4. **Resonant**: choices in one Aspect begin affecting another.
5. **Woven**: multiple Aspects can intentionally collaborate across the Chronicle.
6. **Lucid**: the player can engage the Constellation as a larger identity while preserving each Aspect's agency.

These stages are narrative capabilities, not claims about the player or the nature of reality.

---

## Relics as Constellation Anchors

Relics should awaken through relationship, history, and integration rather than ordinary item levels.

A relic may:

- remember a promise its current bearer did not make,
- recur in different forms across Aspects,
- reveal hidden relationships between Chronicle events,
- respond to a transformed Deep Thread,
- remain dormant despite frequent use when its narrative condition has not been met.

The player may feel that they unlocked the relic. The fiction should allow the more interesting possibility that the relic recognized the player.

---

## Campaign Shape

### Act I: One Life

Establish an Aspect, local relationships, and unresolved questions.

### Act II: First Echo

Introduce an impossible familiarity, recurring symbol, dream, relic memory, or displaced consequence.

### Act III: Second Aspect

Make another full perspective playable without immediately explaining the connection.

### Act IV: Recognition

Allow the player to discover evidence of shared Deep Threads.

### Act V: Constellation

Enable cross-Aspect consequences, bonds, and collaborative choices.

### Act VI: Integration

Create opportunities to respond differently to a recurring pattern.

### Act VII: Choice

Let the player decide what relationship the Aspects will have with the larger pattern they have discovered.

The campaign must support alternate pacing. These acts are a narrative scaffold, not a mandatory script.

---

## Delivery Roadmap

### Phase 0: Canonical Foundation

**Status: in progress / partially implemented**

- Treat numeric dice faces as immutable canonical rolls.
- Persist grammar version with interpreted output.
- Maintain backward compatibility for earlier Chronicle events.
- Complete automated backend and frontend contract tests.
- Ensure physical, digital, and scanned dice share one ingestion path.

**Exit criteria**

- A saved roll can be replayed under its original grammar.
- A new grammar can reinterpret a roll without mutating canonical history.
- All clients use one typed roll contract.

### Phase 1: Reliable Chronicle

- Expand Chronicle event schemas for relationships, promises, symbols, scars, relic changes, and unresolved questions.
- Add provenance for AI-generated interpretations and player-authored canon.
- Add contradiction detection and repair workflows.
- Implement retrieval by character, location, symbol, Thread, relic, and session.
- Add export and backup support.

**Exit criteria**

- The Soulkeeper can explain which Chronicle evidence supports a callback.
- Canon changes are traceable and reversible.
- Long-running campaigns retain continuity across sessions.

### Phase 2: Curiosity Engine

- Add a structured Question and Seed model.
- Track open questions without forcing immediate resolution.
- Generate clues with bounded information release.
- Add recurring-symbol detection.
- Add curiosity-oriented encounter evaluation.
- Create guardrails against manipulative engagement patterns and false psychological certainty.

**Exit criteria**

- The Soulkeeper can plant, revisit, deepen, transform, and retire a Seed.
- Questions emerge from player history rather than generic mystery templates.
- The system distinguishes productive ambiguity from missing information.

### Phase 3: Threads and Integration

- Implement Local Thread lifecycle.
- Infer candidate patterns from Chronicle evidence.
- Require explicit player confirmation before treating inferred personal meaning as canon.
- Detect potential Integration Events from changed choices and consequences.
- Connect Integration Events to abilities, relationships, and relic states.
- Add player controls to reject, rename, reinterpret, or hide a Thread.

**Exit criteria**

- Progression can occur without XP thresholds.
- Every transformation cites supporting story events.
- No Thread is presented as an authoritative diagnosis of the player.

### Phase 4: Soul Constellation

- Add multiple playable Aspects per Constellation.
- Separate Aspect-local state from shared Deep Threads.
- Introduce cross-Aspect symbols, bonds, and anchors.
- Support era/world separation while preserving coherent causality.
- Add awakening-stage capabilities.
- Build Constellation Sheet UI.

**Exit criteria**

- Two Aspects can share a Deep Thread without collapsing into the same personality.
- Cross-Aspect effects are understandable and Chronicle-backed.
- Players can engage the system as fantasy, psychology, spirituality, or metaphor without mechanical penalty.

### Phase 5: Probable Paths

- Persist meaningful unchosen alternatives.
- Let probable paths return as dreams, rumors, alternate scenes, or playable Aspects.
- Add probability-branch provenance and convergence rules.
- Prevent branches from silently overwriting canon.
- Allow player-directed exploration of selected alternatives.

**Exit criteria**

- The system can revisit a path not taken while preserving the significance of the original choice.
- Branches remain legible and reversible.
- Probability mechanics deepen agency instead of trivializing consequence.

### Phase 6: Relic Recognition

- Convert relic progression to narrative conditions and Chronicle evidence.
- Add Constellation Anchor behavior.
- Support cross-Aspect relic forms.
- Add awakening, overdraw, fracture, repair, and transfiguration events.
- Surface dormant conditions as evocative questions rather than mechanical checklists.

**Exit criteria**

- Relic changes arise from story integration rather than usage counters alone.
- Players can understand the history of every relic state.
- Relics create curiosity without becoming arbitrary puzzle locks.

### Phase 7: Convergence and Community Mythology

- Expand WebSocket multiplayer convergence.
- Support consent-aware shared canon.
- Add world-level symbols and community Threads.
- Provide moderation, privacy, separation, and merge controls.
- Enable gatherings where many rolls contribute to one evolving phenomenon.
- Preserve individual agency when stories intersect.

**Exit criteria**

- Multiple campaigns can contribute to a shared mythology without exposing private Chronicle material.
- Conflicting canon can coexist, branch, or reconcile explicitly.
- Community events remain playable rather than becoming passive generated lore.

### Phase 8: Reflection and Accessibility

- Add optional end-of-session reflection prompts.
- Support private notes that are never used by AI unless explicitly permitted.
- Add content controls, intensity settings, and graceful disengagement.
- Improve screen reader, keyboard, motion, contrast, and cognitive accessibility.
- Add transparent explanations of memory, inference, and data controls.

**Exit criteria**

- Reflection is always optional.
- Players control what the system remembers and interprets.
- The experience remains useful without spiritual framing or personal disclosure.

---

## Near-Term Implementation Priorities

1. Finish the canonical roll contract migration across API, persistence, frontend types, and tests.
2. Strengthen Chronicle provenance, retrieval, and contradiction handling.
3. Define schemas for Seeds, Questions, Symbols, Local Threads, and Integration Events.
4. Prototype the Curiosity Engine using deterministic rules before adding model-driven inference.
5. Build one vertical slice:
   - plant a Seed,
   - echo it across three encounters,
   - let the player recognize or reject the pattern,
   - trigger a Chronicle-backed Integration Event,
   - awaken one relic capability.
6. Test the vertical slice with players who hold different philosophical interpretations.
7. Use those sessions to refine pacing, ambiguity, consent, and player control before implementing the full Constellation.

---

## Design Guardrails

SoulSmith must not:

- diagnose the player,
- claim privileged knowledge of the player's soul or true nature,
- manufacture urgency around personal transformation,
- punish players for rejecting an interpretation,
- equate one moral choice with universal enlightenment,
- use private reflections without explicit permission,
- disguise engagement optimization as spiritual guidance,
- turn ambiguity into arbitrary withholding.

SoulSmith should:

- invite questions,
- preserve agency,
- cite its narrative evidence,
- allow reinterpretation,
- make uncertainty visible,
- let meaning emerge through play.

---

## North-Star Experience

A player encounters a symbol they barely notice.

It returns in another form.

Later, a relic remembers something the player does not.

An NPC reacts to a promise made by another Aspect.

The player begins asking a better question.

Eventually, they recognize a pattern and choose differently, not because the game declared an answer, but because the story made a new possibility visible.

The Chronicle changes. A Thread integrates. A relic awakens.

The system does not announce enlightenment.

It simply remembers that the player saw the river differently.
