# backend/app/temporal.py
"""
SoulSmith Phase 22: Temporal Pacing & Living Time.

> TIME MAY CHANGE WHAT IS POSSIBLE. IT MUST NEVER DECIDE WHAT THE PLAYER'S
> STORY MEANS.
>
> THE WORLD MAY WAIT FOR YOU. IT MUST NEVER PUNISH YOU FOR HAVING A LIFE
> OUTSIDE THE GAME.

This module owns SoulSmith's time authority model. It deliberately separates the
different clocks the game may care about so no single timestamp is overloaded:

- **canonical event time**  — ``scene_events.created_at`` (immutable Chronicle),
- **server/recorded wall-clock time** — SQLite ``CURRENT_TIMESTAMP`` (UTC),
- **session time** — ``campaign_sessions.last_active_at`` / ``updated_at``,
- **elapsed real time** — derived from the trusted clock and a prior timestamp,
- **fictional/world time** — ``campaign_time_settings`` (policy + fictional now),
- **Aspect-relative time** — ``aspect_temporal_state`` per (campaign, Aspect),
- **place/history time** — ``place_history.created_at`` / ``places.last_visited_at``.

Domain systems consume a bounded :class:`TemporalContext` instead of calling the
system clock ad hoc. Wall-clock time is an *additional* eligibility input, never
a substitute for domain evidence; count-based pacing remains authoritative for
offline fixtures and deterministic tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

TEMPORAL_VERSION = "1.0.0"

# Time policies a campaign may use. ``none`` keeps fictional time fully off;
# the others are explicit, opt-in policies — never an implicit 1 real day = 1
# world day.
TIME_POLICIES: frozenset[str] = frozenset(
    {"none", "event_driven", "manual", "real_time_linked", "accelerated"}
)

# Optional wall-clock cooldowns keyed by opportunity type. This is EMPTY by
# default so deterministic/count-based pacing remains the authoritative path and
# existing fixtures are unaffected. Enable specific entries (in tests, via env,
# or via future config) to add a *minimum elapsed interval* on top of the
# existing count-based cooldown. Completing a cooldown only makes something
# eligible; it never forces presentation.
WALL_CLOCK_COOLDOWN_SECONDS: dict[str, float] = {}


class TemporalContext(BaseModel):
    """A bounded, inspectable statement of trusted time for one eligibility run.

    ``now_iso`` is the authoritative current timestamp. Everything else is
    derived, provenance-bearing metadata so callers can *inspect why* something
    became eligible now.
    """

    now_iso: str
    timezone: str = "UTC"
    time_source: str = "server_utc"  # server_utc | test_frozen | provisional_offline
    confidence: str = "trusted"
    offline: bool = False
    sync_status: str = "synced"

    session_started_at: str | None = None
    last_active_at: str | None = None
    elapsed_since_last_active_seconds: float | None = None

    deterministic_event_count: int = 0
    aspect_event_count: int = 0

    fictional_policy: str = "none"
    fictional_now_iso: str | None = None
    fictional_calendar: dict[str, Any] = Field(default_factory=dict)

    aspect_soul_id: str | None = None


# ---------------------------------------------------------------------------
# Trusted, injectable clock. Tests and the authorized debug endpoint may freeze
# or advance this clock deterministically; production always uses server UTC.
# ---------------------------------------------------------------------------

_CLOCK_OVERRIDE: datetime | None = None
_CLOCK_OFFLINE_PROVISIONAL: bool = False


def now_utc() -> datetime:
    """Return the authoritative current time. Frozen for tests when overridden."""
    if _CLOCK_OVERRIDE is not None:
        return _CLOCK_OVERRIDE
    return datetime.now(timezone.utc)


def iso_now() -> str:
    """Authoritative current timestamp as timezone-aware ISO-8601 UTC."""
    return now_utc().isoformat()


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse a stored timestamp into an aware UTC datetime. Returns None when
    absent/unparseable rather than raising, so eligibility degrades safely."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        # SQLite CURRENT_TIMESTAMP produces "YYYY-MM-DD HH:MM:SS" (naive UTC).
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None
    return _ensure_aware(dt)


def to_utc_iso(value: datetime) -> str:
    """Normalize any aware datetime to a canonical UTC ISO string."""
    return _ensure_aware(value).astimezone(timezone.utc).isoformat()


def elapsed_since(value: str | None, *, now: str | None = None) -> float | None:
    """Elapsed seconds from ``value`` to ``now`` (or the trusted clock)."""
    start = parse_timestamp(value)
    if start is None:
        return None
    end = parse_timestamp(now) if now else now_utc()
    return max(0.0, (end - start).total_seconds())


@contextmanager
def freeze_time(iso: str | None) -> Iterator[None]:
    """Deterministically freeze the trusted clock to ``iso`` for a test scope.

    ``iso=None`` clears any override. Freezing is test/debug-only; it never
    rewrites persisted canonical timestamps.
    """
    global _CLOCK_OVERRIDE
    previous = _CLOCK_OVERRIDE
    _CLOCK_OVERRIDE = parse_timestamp(iso) if iso else None
    try:
        yield
    finally:
        _CLOCK_OVERRIDE = previous


def set_offline_provisional(offline: bool) -> None:
    """Mark the clock source as provisional/offline for a test scope."""
    global _CLOCK_OFFLINE_PROVISIONAL
    _CLOCK_OFFLINE_PROVISIONAL = offline


def is_offline_provisional() -> bool:
    return _CLOCK_OFFLINE_PROVISIONAL


def clock_is_frozen() -> bool:
    return _CLOCK_OVERRIDE is not None


# ---------------------------------------------------------------------------
# Time policy resolution. Fictional time is opt-in and explicit.
# ---------------------------------------------------------------------------


def resolve_time_policy(campaign_id: str) -> dict[str, Any]:
    """Resolve the campaign's time policy, defaulting to ``none`` (no fictional
    clock). Never invents a policy."""
    from app import db

    settings = db.get_or_create_campaign_time_settings_record(campaign_id)
    return settings


def fictional_now(campaign_id: str) -> str | None:
    """Return the campaign's current fictional timestamp, or None if no policy."""
    settings = resolve_time_policy(campaign_id)
    if settings.get("time_policy") == "none":
        return None
    return settings.get("fictional_now_iso")


def advance_fictional_time(
    campaign_id: str,
    *,
    delta_seconds: float | None = None,
    to_iso: str | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    """Advance a campaign's fictional clock. Only legal for policies that
    authorize manual advancement (``manual``, ``accelerated``, or a configured
    real-time link); ``none`` and ``event_driven`` reject manual advancement so
    time policy changes never retroactively reorder canonical history."""
    from app import db

    settings = resolve_time_policy(campaign_id)
    policy = settings.get("time_policy", "none")
    if policy not in ("manual", "accelerated", "real_time_linked"):
        raise ValueError(
            f"Campaign time policy '{policy}' does not authorize manual advancement."
        )

    base = parse_timestamp(settings.get("fictional_now_iso")) or now_utc()
    if to_iso:
        target = parse_timestamp(to_iso)
        if target is None:
            raise ValueError("Invalid target fictional timestamp.")
    elif delta_seconds is not None:
        target = base + timedelta(seconds=delta_seconds)
    else:
        raise ValueError("Provide delta_seconds or to_iso to advance fictional time.")

    updated = db.update_campaign_time_settings_record(
        campaign_id,
        fictional_now_iso=to_utc_iso(target),
    )
    return {"campaign_id": campaign_id, "settings": updated, "source": source}


# ---------------------------------------------------------------------------
# TemporalContext assembly. Callers pass structured state; the module never
# reaches for the system clock in arbitrary places.
# ---------------------------------------------------------------------------


def build_temporal_context(
    session: dict[str, Any],
    *,
    campaign_time_settings: dict[str, Any] | None = None,
    aspect_temporal_state: dict[str, Any] | None = None,
    deterministic_event_count: int = 0,
    aspect_event_count: int = 0,
) -> TemporalContext:
    """Assemble a bounded TemporalContext for the active session/Aspect."""
    from app.multi_aspect import active_soul_id

    now = iso_now()
    last_active_at = session.get("last_active_at") or session.get("updated_at")
    settings = campaign_time_settings or resolve_time_policy(session["campaign_id"])
    aspect_soul_id = active_soul_id(session)

    offline = is_offline_provisional()
    return TemporalContext(
        now_iso=now,
        timezone=settings.get("timezone") or "UTC",
        time_source="test_frozen" if clock_is_frozen() else "server_utc",
        confidence="trusted" if not offline else "provisional",
        offline=offline,
        sync_status="pending" if offline else "synced",
        session_started_at=session.get("created_at"),
        last_active_at=last_active_at,
        elapsed_since_last_active_seconds=elapsed_since(last_active_at, now=now),
        deterministic_event_count=deterministic_event_count,
        aspect_event_count=aspect_event_count,
        fictional_policy=settings.get("time_policy") or "none",
        fictional_now_iso=settings.get("fictional_now_iso"),
        fictional_calendar={},
        aspect_soul_id=aspect_soul_id,
    )


def _aspect_state(campaign_id: str, soul_id: str) -> dict[str, Any]:
    from app import db

    return db.get_or_create_aspect_temporal_state_record(campaign_id, soul_id)


# ---------------------------------------------------------------------------
# Wall-clock and hybrid eligibility (pure).
# ---------------------------------------------------------------------------


def wall_clock_cooldown_seconds(opportunity_type: str) -> float | None:
    """Return the configured minimum elapsed interval for an opportunity type,
    or None when wall-clock pacing is off for it."""
    value = WALL_CLOCK_COOLDOWN_SECONDS.get(opportunity_type)
    return float(value) if value is not None else None


def wall_clock_cooldown_satisfied(
    opportunity_type: str,
    *,
    last_offered_at: str | None,
    now_iso: str | None = None,
) -> tuple[bool, str | None]:
    """True when a wall-clock cooldown (if any) has elapsed. Returns an
    inspectable reason string. ``None`` interval means 'no wall-clock cooldown'."""
    interval = wall_clock_cooldown_seconds(opportunity_type)
    if interval is None:
        return True, None
    if last_offered_at is None:
        return True, None
    elapsed = elapsed_since(last_offered_at, now=now_iso)
    if elapsed is None:
        return True, None
    if elapsed >= interval:
        return True, f"{elapsed:.0f}s elapsed >= {interval:.0f}s"
    return False, f"Only {elapsed:.0f}s elapsed; requires {interval:.0f}s"


def evaluate_hybrid_rule(
    *,
    event_count_since: int,
    elapsed_seconds_since: float | None,
    min_events: int | None = None,
    min_elapsed_seconds: float | None = None,
    fictional_before_iso: str | None = None,
    fictional_now_iso: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Evaluate a hybrid eligibility rule that may combine deterministic and
    temporal conditions. Returns (satisfied, inspectable_reasoning). All provided
    conditions must hold; absent conditions are ignored."""
    reasons: dict[str, Any] = {}
    satisfied = True

    if min_events is not None:
        reasons["min_events"] = min_events
        reasons["event_count_since"] = event_count_since
        event_met = event_count_since >= min_events
        reasons["event_condition_met"] = event_met
        if not event_met:
            satisfied = False

    if min_elapsed_seconds is not None:
        reasons["min_elapsed_seconds"] = min_elapsed_seconds
        reasons["elapsed_seconds_since"] = elapsed_seconds_since
        time_met = (
            elapsed_seconds_since is not None
            and elapsed_seconds_since >= min_elapsed_seconds
        )
        reasons["time_condition_met"] = time_met
        if not time_met:
            satisfied = False

    if fictional_before_iso is not None and fictional_now_iso is not None:
        reasons["fictional_before"] = fictional_before_iso
        reasons["fictional_now"] = fictional_now_iso
        before = parse_timestamp(fictional_before_iso)
        now = parse_timestamp(fictional_now_iso)
        fictional_met = not (before is not None and now is not None and now < before)
        reasons["fictional_condition_met"] = fictional_met
        if not fictional_met:
            satisfied = False

    reasons["satisfied"] = satisfied
    return satisfied, reasons


# ---------------------------------------------------------------------------
# Scheduled / delayed consequences. A consequence must reference the canonical
# event/rule that created it; the narrator cannot mint a hidden timer.
# ---------------------------------------------------------------------------


class ScheduleConsequenceRequest(BaseModel):
    session_id: str
    source_type: str  # chronicle_event | promise | relic_event | ...
    source_id: str
    rule: str
    eligible_after_iso: str | None = None
    min_elapsed_seconds: float | None = None
    min_events: int | None = None
    note: str = ""


class AdvanceFictionalTimeRequest(BaseModel):
    campaign_id: str
    delta_seconds: float | None = None
    to_iso: str | None = None


class EvaluateTemporalEligibilityRequest(BaseModel):
    session_id: str


class ResumeRecapRequest(BaseModel):
    session_id: str


def schedule_consequence(
    *,
    session_id: str,
    source_type: str,
    source_id: str,
    rule: str,
    eligible_after_iso: str | None = None,
    min_elapsed_seconds: float | None = None,
    min_events: int | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Persist a provenance-backed delayed consequence. It is inert until its
    temporal condition becomes true, and even then it only *becomes eligible* —
    presentation is never forced."""
    from app import db

    if not source_id:
        raise ValueError("A scheduled consequence must cite its originating evidence.")
    session = db.get_campaign_session_record(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found.")
    return db.create_scheduled_consequence_record(
        session_id=session_id,
        campaign_id=session["campaign_id"],
        source_type=source_type,
        source_id=source_id,
        rule=rule,
        eligible_after_iso=eligible_after_iso,
        min_elapsed_seconds=min_elapsed_seconds,
        min_events=min_events,
        note=note,
    )
