# Canonical Numeric Roll Contract

Milestone 1 makes numeric dice faces the immutable source of truth. Symbolic readings are derived data produced by a named grammar version, so a physical d20 showing `17` means the same thing as a digital or camera-confirmed d20 showing `17`.

## Canonical request schema

```json
{
  "d20": 17,
  "d12": 4,
  "d10": 8,
  "percentile": 70,
  "d8": 3,
  "d6": 5,
  "d4": 2,
  "grammar_version": "1.0.0"
}
```

Ranges are validated server-side: d20 1-20, d12 1-12, d10 1-10, percentile 1-100, d8 1-8, d6 1-6, and d4 1-4.

## Canonical response schema

```json
{
  "raw": { "d20": 17, "d12": 4, "d10": 8, "percentile": 70, "d8": 3, "d6": 5, "d4": 2 },
  "grammar_version": "1.0.0",
  "interpretation": { "spark": "Wonder", "domain": "Ally", "pressure": "Corruption", "aim": "Reveal", "approach": "Guile", "verdict": "Reveal", "thread": "Memory" },
  "grammar_sentence": "..."
}
```

## Lifecycle

1. Digital, manual, or camera input produces numeric values.
2. The backend validates the numeric roll and grammar version.
3. The grammar registry deterministically maps values/ranges to symbols.
4. Scene resolution consumes the canonical interpreted roll.
5. Chronicle events store raw values, interpretation, grammar version, player intent, approach, resource investment, deterministic outcome, narration, canon facts, timestamp, and stable event ID.

## Grammar versioning

`1.0.0` is the default grammar. Future grammars can be added to the registry without mutating historical rolls. The d4 Thread vocabulary intentionally contains exactly four primary faces: Bond, Memory, Mark, and Prophecy. Portal and Debt are reserved for future Chronicle consequences rather than primary d4 faces.

## Input workflows

- Digital dice call `POST /api/v1/dice/roll`, optionally with a test seed.
- Manual dice call `POST /api/v1/dice/interpret` with player-entered numbers.
- Camera dice currently use a simulated `POST /api/v1/dice/photo-ingest`; confirmed numeric values are then interpreted through `POST /api/v1/dice/interpret`.

## Compatibility policy

Legacy symbolic `DiceRollRead` remains as a deprecated interpretation alias on the frontend and backend. New canon-writing paths must use the canonical interpreted roll object and must not let frontend or narration code overwrite raw numeric values.
