# Relationships & Promises (Phase 19)

> **A RELATIONSHIP IS HISTORY BETWEEN PEOPLE. A PROMISE IS A CLAIM ON THE
> FUTURE. NEITHER MAY BE INVENTED BY THE NARRATOR.**

Phase 19 closes the architectural gap left by Phase 17: `relationship_callback`
and `promise_consequence` opportunities existed conceptually, but the North-Star
promise reaction reached the world only indirectly through World Memory. SoulSmith
now gives relationships and promises first-class, provenance-backed persistence so
bonds between people become durable story machinery across encounters, Aspects,
generations, relics, and World Memory.

---

## Authority model

Four layers must never collapse into each other:

1. **Canonical interaction** — what the Chronicle records actually happened.
2. **Participant perspective** — how one party remembers/interprets the bond.
3. **Public/world interpretation** — what World Memory/NPCs later believe.
4. **Narrator presentation** — how the Soulkeeper phrases it.

The domain systems (Chronicle, Relationship & Promise Engine) decide what is
true. The Soulkeeper decides how it is told. The narrator may phrase a
relationship or promise only from structured authority supplied by the domain
model.

```
CANONICAL INTERACTIONS -> RELATIONSHIP HISTORY -> PROMISES / OBLIGATIONS
        -> CONSEQUENCES -> ORCHESTRATOR CALLBACKS
```

Never:

```
NARRATIVE CHEMISTRY -> INVENTED CANONICAL RELATIONSHIP
```

---

## Relationships

A relationship is derived from canonical interactions and explicit state, never
narrative vibes. It has:

- a stable `relationship_id`,
- participant/entity IDs (any entity type: Aspect, NPC, faction, relic, place),
- structured, extensible `kind`s (friendship, alliance, mentorship, rivalry,
  family/lineage, duty/service, creator/creation, bearer/relic bond, custom),
- canonical source-event links,
- creation context,
- a current status (`active`, `distant`, `ended`, `unknown`, `historical`),
- an immutable events/history timeline (`met`, `allied`, `betrayed`,
  `protected`, `promise_made`, ...), and
- visibility/consent scope.

Do not infer sensitive or intimate relationship categories from prose.

### Participant-specific perspectives

A shared relationship does not imply shared interpretation. Rowan may consider
Mira a friend while Mira considers Rowan an ally but not a friend, and a later
historian calls them legendary companions. Those three statements may coexist.

Perspectives are stored separately from canonical interaction facts and are
marked `is_canonical_interaction`. A perspective never becomes objective
emotional truth, and there is no numeric affection meter that silently becomes
canonical.

### Relationship significance

When an internal score is useful for ranking callbacks it is treated as
**derived scheduling metadata**, never as canonical emotional truth. The
inspectable signal is the number and significance of canonical interactions,
shared StoryMarks, promises, consequences, and relic/world connections.

---

## Promises

A promise must have a canonical source event or explicit player-authorized
creation. It has:

- a stable `promise_id`,
- a maker/promisor, recipient(s), and (optionally) a beneficiary,
- the original immutable wording plus structured meaning,
- explicit conditions and scope,
- relevant entity/relic/place/group links,
- visibility/secrecy,
- a lifecycle state and immutable state-change history, and
- provenance.

Do not require every promise to have a deadline, and do not invent a deadline,
condition, or beneficiary that was not established.

### Lifecycle

```
proposed -> made -> acknowledged -> active -> fulfilled | broken | released
                                 |-> disputed | impossible | unresolved
                                 |-> inherited | transferred (with provenance)
                                 |-> forgotten -> rediscovered
```

The original promise remains immutable historical evidence even as its state
evolves. Release is historical, not deletion.

### Canonical wording vs interpretation

What was actually promised is separate from what later people believe was
promised. A legend that "Rowan swore the lantern would guard Mira's bloodline
forever" is valid World Memory but must never mutate the canonical promise
"Rowan promised to return the lantern to Mira's family." Phase 16 drift/provenance
architecture applies.

### Fulfillment and breach

Promise resolution is evidence-backed. A promise may be fulfilled or broken only
when the domain rules can cite a relevant canonical event, or when an authorized
player explicitly resolves an inherently subjective/negotiated condition.
Ambiguous evidence is represented as `disputed`/`unresolved`, never forced into a
verdict.

### Inheritance and transfer

A promise can outlive its original maker (another Aspect, a lineage, a faction, a
relic bearer, an office, a place). But inheritance/transfer must itself have
canonical provenance or explicit domain semantics. A later character does not
become obligated simply because the narrator finds it dramatic.

---

## Relic integration

Relics may witness a promise, be the subject/object of a promise, preserve
evidence of a promise, pass between bearers, or react when promise conditions
recur. The Relationship & Promise Engine may supply evidence to Relic
Recognition (`promise_entity_links` with `link_type="relic"`), but it never
directly awakens or transfigures a relic.

```
Aspect A makes promise -> relic records/anchors it -> centuries pass ->
Aspect B carries relic -> world/NPC recognizes promise -> callback ->
player choice -> Integration evidence -> relic awakening candidate
```

Every link remains traceable.

---

## Soul Constellation integration

Promises and relationship patterns may become Constellation anchors when existing
Constellation rules allow it (recurring roles, repeated promise themes, unfinished
obligations, inherited scars). The system may present the pattern; the player
decides what it means. No metaphysical interpretation is forced.

---

## World Memory integration

Relationships and promises may become cultural memory (famous friendships,
legendary vows, misunderstood betrayals, songs about broken promises, relic
legends). The World Memory compiler records relationship/promise rows as canonical
source refs without copying or mutating them. World Memory interpretation remains
distinct from canonical relationship/promise history.

---

## NPC knowledge

An NPC may know a promise because of direct participation, direct witness,
family/lineage transmission, faction records, local tradition, World Memory,
archive access, relic evidence, or relationship network. An NPC must not know a
secret promise merely because it exists in the database. The projection is
consent-safe and scoped, mirroring Phase 16.

---

## Campaign Orchestrator callbacks

The orchestrator now auto-generates first-class `relationship_callback` and
`promise_consequence` opportunities from structured eligibility (a new
"Relationship & Promises" subsystem). Eligibility is deterministic before
narration, cooldowns are count-based, and every callback carries source evidence.
The orchestrator decides when a callback deserves an opportunity; the engine
decides what relationship/promise state actually exists.

---

## Soulkeeper narration boundaries

The Soulkeeper may phrase dialogue, describe tension supported by explicit scene
state, remind the player of known promise evidence, present ambiguity/dispute,
and ask questions. It may not invent attraction/friendship/hostility, invent a
promise, change promise wording, decide fulfillment/breach without domain
evidence, reveal secret relationship information, or turn one participant's
interpretation into objective truth. The Phase 18 narrative Guardian enforces
these boundaries (`invented_promise`, `invented_relationship`,
`promise_state_authority`).

---

## Consent and privacy

Relationship information can be especially sensitive in shared campaigns. A
public event involving two people does not automatically make their private
relationship interpretation public. Public APIs project relationships and
promises through consent filters and never leak private participant lists,
promise text, counts, or metadata to unauthorized viewers.

---

## Persistence & API

Normalized SQLite tables (no opaque JSON graph, no new migration framework):

- `relationships`, `relationship_participants`, `relationship_source_events`,
  `relationship_events`, `relationship_perspectives`, `relationship_entity_links`
- `promises`, `promise_participants`, `promise_state_history`,
  `promise_entity_links`

Key endpoints (all under `/api/v1`):

- `POST /relationships`, `GET /relationships`, `GET /relationships/{id}`,
  `GET /relationships/query`
- `POST /relationships/{id}/events`, `.../perspectives`, `.../links`
- `POST /promises`, `GET /promises`, `GET /promises/{id}`, `GET /promises/query`
- `POST /promises/{id}/transition`, `POST /promises/{id}/evaluate`,
  `POST /promises/{id}/links`
- `POST /relationships/npc-knowledge`

No endpoint silently mutates Chronicle history.

---

## Known v1 limitations

- Relationship/promise facts are structured state, not generated prose; narration
  flows through the Phase 18 runtime rather than a dedicated relationship provider.
- NPC knowledge projection is deterministic and conservative; richer per-NPC
  social graphs (faction records, lineage transmission) are future work.
- Fulfillment/breach evaluation is evidence-cited but not semantic-keyword
  matching; subjective conditions require explicit player resolution.
