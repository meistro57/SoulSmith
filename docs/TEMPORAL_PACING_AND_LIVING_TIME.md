# Phase 22: Temporal Pacing & Living Time

> **TIME MAY CHANGE WHAT IS POSSIBLE. IT MUST NEVER DECIDE WHAT THE PLAYER'S
> STORY MEANS.**
>
> **THE WORLD MAY WAIT FOR YOU. IT MUST NEVER PUNISH YOU FOR HAVING A LIFE
> OUTSIDE THE GAME.**

SoulSmith gives the world a trustworthy sense of elapsed time so it can wait,
age, recur, remember, and change between sessions — without turning real time
into an engagement weapon.

The conceptual pipeline is:

```
CANONICAL STATE + TRUSTED TIME CONTEXT -> TEMPORAL ELIGIBILITY -> CAMPAIGN OPPORTUNITY
```

Never:

```
IT HAS BEEN 24 HOURS -> INVENT DRAMA
```

---

## Time authority model

One module owns time: `backend/app/temporal.py`. It provides a single injectable
trusted clock (`now_utc()` / `iso_now()`) and the bounded `TemporalContext`
that every eligibility system consumes. Domain systems never call the system
clock ad hoc.

The clock defaults to server UTC. Tests (and the authorized debug endpoint)
freeze or advance it deterministically via `freeze_time(iso)`, which never
rewrites persisted canonical timestamps.

## Time domains

SoulSmith distinguishes these clocks and never overloads one timestamp field:

| Domain | Source | Mutable? |
|---|---|---|
| Canonical event time | `scene_events.created_at` | Immutable |
| Server/recorded wall-clock time | SQLite `CURRENT_TIMESTAMP` (UTC) | Append-only |
| Session time | `campaign_sessions.last_active_at` / `updated_at` | Bookkeeping |
| Elapsed real time | derived (`temporal.elapsed_since`) | Derived |
| Fictional/world time | `campaign_time_settings.fictional_now_iso` | Policy-gated |
| Aspect-relative time | `aspect_temporal_state` (campaign, soul) | Per-Aspect |
| Place/history time | `place_history.created_at` / `places.last_visited_at` | Append-only |

## TemporalContext

`TemporalContext` is the bounded statement of trusted time handed to eligibility
systems:

- trusted current timestamp (`now_iso`),
- campaign timezone,
- session start / last-active timestamps,
- elapsed duration since last active,
- deterministic turn/event counts (campaign and Aspect),
- fictional policy and fictional now (when configured),
- confidence/source (`server_utc`, `test_frozen`, or `provisional` offline),
- offline/sync status.

Build it with `temporal.build_temporal_context(session, ...)`; inspect it via
`GET /api/v1/campaign/session/{session_id}/temporal-context`.

## Count vs wall-clock vs hybrid pacing

- **Count-based pacing** (`COOLDOWN_WINDOW`) remains the authoritative,
  deterministic, offline-testable path. It is unchanged.
- **Wall-clock cooldowns** (`WALL_CLOCK_COOLDOWN_SECONDS`) are *optional* and
  *empty by default*. A configured entry adds a minimum elapsed interval on top
  of the count-based cooldown. Completing a cooldown only makes something
  *eligible*; it never forces presentation.
- **Hybrid rules** (`evaluate_hybrid_rule`) combine deterministic and temporal
  conditions, e.g. `>= 3 canonical events AND >= 2 real days`, and return an
  inspectable reasoning dict.

The wall-clock ledger (`temporal_cooldowns`) is keyed by `cooldown_key` and is
upsert-idempotent, so repeated scheduler/evaluation runs at the same effective
time never duplicate opportunities.

## Real vs fictional time

`campaign_time_settings` records an explicit, opt-in time policy. v1 policies:

- `none` — no fictional clock (default),
- `event_driven` — fictional time advances only via canonical events,
- `manual` — a player/administrator advances fictional time explicitly,
- `real_time_linked` — fictional time follows real time,
- `accelerated` — ratio-based fictional time (future deepening).

One real day is **never** assumed to equal one world day. Changing policy never
retroactively reorders canonical history; it only changes future derived
eligibility. Manual advancement is rejected for `none`/`event_driven`.

## Scheduled and delayed consequences

`ScheduledConsequence` (`scheduled_consequences`) is a provenance-backed delayed
consequence. It must reference the canonical event/rule that created it
(`source_type` + `source_id`). It is inert until its condition becomes true, and
then only *becomes eligible* — never forced. The narrator cannot mint a hidden
timer.

Surfaces:
- `POST /api/v1/campaign/scheduled-consequences` (create, requires evidence),
- `GET /api/v1/campaign/scheduled-consequences`,
- `POST /api/v1/campaign/scheduled-consequences/{id}/retire`,
- `POST /api/v1/campaign/time/evaluate` (eligibility + reason).

## Relationship and promise time

Time may affect relationship/promise opportunities without pretending to know
private emotions. Valid temporal signals include time since last canonical
interaction (`relationships.last_interaction_at`), an explicit promise deadline
(`promises.deadline_iso` + provenance), anniversaries, and time since
fulfillment/breach/release. Elapsed time never infers anger, loneliness,
forgiveness, or emotional change.

## Multi-Aspect chronology

Each Aspect keeps independent temporal state in `aspect_temporal_state`
(campaign, soul). Switching Aspects preserves each Aspect's last-active time and
deterministic event count. Wall-clock inactivity of one Aspect does not imply
fictional inactivity unless policy says so. Cross-Aspect callbacks use
canonical/fictive chronology, never player session order alone, and a historical
Aspect cannot receive future knowledge.

## Wandering temporal context

Place discovery may consult time since last visit (`places.last_visited_at`) and
time since a place event. Local day/night is available only with explicit
consent. Missing a time-limited Wandering window never damages canonical
progression; it only means an opportunity was not offered.

## Relic, Curiosity, and World Memory integration

- **Relics**: time may accumulate dormancy intervals, but time alone can never
  awaken/transfigure a relic; existing Relic Recognition/Integration evidence
  remains required.
- **Curiosity/Seeds**: `seeds.last_echo_at` enables temporal echo spacing. The
  goal is narrative spacing, not retention or streak mechanics.
- **World Memory**: elapsed time never manufactures cultural significance.
  Existing evidence/significance/publication rules still apply; legends may drift
  under Phase 16 rules while canonical timestamps stay immutable.

## Visual integration

Temporal context may influence an Art Moment or visual spec when it is
canonical/relevant (aging portrait update, anniversary painting, seasonal
location, relic weathering). Generated visuals cannot establish that time passed
canonically; the temporal domain supplies that fact first.

## Return after absence

`GET .../resume-recap` (or `POST .../resume-recap`) returns a concise, optional
recap: where this Aspect was, unresolved promises, active Threads/Seeds, and
eligible opportunities. No guilt, no streaks, no decay penalties, no mandatory
backlog.

> **WELCOME BACK IS A MEMORY SERVICE, NOT A RETENTION TRICK.**

## Notification extension point

Eligibility is computed domain-level (`/time/evaluate`) so future
reminders/notifications can subscribe to opt-in, evidence-backed conditions
without a push service. Notifications are never inferred psychological pressure.

## Clock trust and offline sync

Online, server timestamps are authoritative. Offline, observations may carry
provisional time metadata (`TemporalContext.offline`, `time_source`) and
reconcile on sync. Clock rollback/forward never duplicates rewards/opportunities
and never reorders committed Chronicle history.

## Timezone and DST

Authoritative timestamps are stored as timezone-aware UTC ISO strings
(`to_utc_iso`). Presentation timezone is preserved separately in
`campaign_time_settings.timezone`. DST transitions and timezone travel never
corrupt canonical ordering; a player cannot satisfy the same local-calendar
condition twice unless a rule explicitly permits it.

## Idempotency

Wall-clock cooldowns, scheduled consequences, and aspect temporal state are all
idempotent (upsert keyed by `cooldown_key` / `consequence_id` /
`(campaign, soul)`). Repeated evaluation never duplicates opportunities, events,
promise resolutions, relic awakenings, VisualJobs, or World Memories.

## Privacy and observability

Temporal metadata records the effective time source, rule, source event ids,
elapsed duration, event-count spacing, eligibility result, and idempotency key —
without logging unnecessary private activity patterns.

## Known v1 limitations

- Wall-clock cooldowns are empty by default and configured in code; no
  administrator UI yet.
- Fictional `accelerated`/ratio policy is represented but not simulated.
- Scheduled consequences expose eligibility but are not yet auto-injected into
  the opportunity loop (evaluation is inspectable/retirable).
- No push-notification transport (only domain-level eligibility).
