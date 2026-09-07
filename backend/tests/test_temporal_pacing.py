# backend/tests/test_temporal_pacing.py
"""Phase 22: Temporal Pacing & Living Time tests.

These prove time is an *additional* eligibility input, never a substitute for
domain evidence, and never an engagement weapon. Deterministic clock freezing,
wall-clock cooldowns, hybrid rules, fictional time, scheduled consequences,
aspect-relative time, and the return recap are all exercised without weakening
the existing count-based pacing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import temporal
from app.campaign import NarrativeContext, NarrativeOutput
from app.main import app
from app.narrative_guardian import validate_narrative

client = TestClient(app)

SOUL = "Kaelen the Star-Watcher"
OTHER = "Archivist Vael"

T0 = "2026-01-01T00:00:00+00:00"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


def _start(soul_id: str = SOUL, campaign_id: str | None = None) -> dict:
    payload: dict = {"soul_id": soul_id}
    if campaign_id:
        payload["campaign_id"] = campaign_id
    res = client.post("/api/v1/campaign/session", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["session"]


# --- Trusted clock & time domains ---------------------------------------------


def test_frozen_clock_is_deterministic():
    with temporal.freeze_time(T0):
        assert temporal.iso_now() == T0
        assert temporal.now_utc().isoformat() == T0


def test_elapsed_since_is_monotonic():
    start = "2026-01-01T00:00:00+00:00"
    end = "2026-01-01T01:30:00+00:00"
    assert temporal.elapsed_since(start, now=end) == 5400.0
    assert temporal.elapsed_since(None, now=end) is None
    assert temporal.elapsed_since("garbage", now=end) is None


def test_to_utc_iso_normalizes_offsets_without_altering_instant():
    # Timezone presentation must not alter the canonical UTC timestamp.
    eastern = datetime(2026, 3, 8, 1, 30, tzinfo=timezone(timedelta(hours=-5)))
    utc = temporal.to_utc_iso(eastern)
    assert utc == "2026-03-08T06:30:00+00:00"
    # An equivalent UTC instant produces the same canonical string.
    assert temporal.to_utc_iso(datetime(2026, 3, 8, 6, 30, tzinfo=timezone.utc)) == utc


# --- Wall-clock cooldown + hybrid rules ---------------------------------------


def test_wall_clock_cooldown_blocks_before_and_allows_after():
    temporal.WALL_CLOCK_COOLDOWN_SECONDS["seed_echo"] = 3600.0
    try:
        # Never offered -> eligible.
        assert wall_satisfied("seed_echo", None, T0)[0] is True
        # Offered 30 minutes ago -> blocked.
        ok, reason = wall_satisfied("seed_echo", "2025-12-31T23:30:00+00:00", T0)
        assert ok is False and reason
        # Offered >= 1 hour ago -> eligible.
        assert wall_satisfied("seed_echo", "2025-12-31T23:00:00+00:00", T0)[0] is True
    finally:
        temporal.WALL_CLOCK_COOLDOWN_SECONDS.pop("seed_echo", None)


def wall_satisfied(kind, last_offered_at, now_iso):
    return temporal.wall_clock_cooldown_satisfied(
        kind, last_offered_at=last_offered_at, now_iso=now_iso
    )


def test_wall_clock_off_by_default_never_creates_eligibility():
    # With no wall-clock config, time is not consulted; it cannot invent drama.
    assert temporal.wall_clock_cooldown_seconds("relationship_callback") is None
    assert wall_satisfied("relationship_callback", None, T0) == (True, None)


def test_hybrid_rule_requires_both_conditions():
    # Count satisfied, time not -> false.
    ok, reasons = temporal.evaluate_hybrid_rule(
        event_count_since=5,
        elapsed_seconds_since=100.0,
        min_events=3,
        min_elapsed_seconds=3600.0,
    )
    assert ok is False
    assert reasons["event_condition_met"] is not False
    assert reasons["time_condition_met"] is False

    # Both satisfied -> true.
    ok, _ = temporal.evaluate_hybrid_rule(
        event_count_since=5,
        elapsed_seconds_since=7200.0,
        min_events=3,
        min_elapsed_seconds=3600.0,
    )
    assert ok is True


def test_hybrid_fictional_date_condition():
    ok, _ = temporal.evaluate_hybrid_rule(
        event_count_since=0,
        elapsed_seconds_since=None,
        fictional_before_iso="2026-06-01T00:00:00+00:00",
        fictional_now_iso="2026-07-01T00:00:00+00:00",
    )
    assert ok is True
    ok, _ = temporal.evaluate_hybrid_rule(
        event_count_since=0,
        elapsed_seconds_since=None,
        fictional_before_iso="2026-06-01T00:00:00+00:00",
        fictional_now_iso="2026-01-01T00:00:00+00:00",
    )
    assert ok is False


# --- Provider cannot invent temporal consequences -----------------------------


def _ctx(**overrides) -> NarrativeContext:
    base = {
        "soul_id": SOUL,
        "campaign_id": "north_star_campaign",
        "session_id": "sess_1",
        "opportunity_type": "relationship_callback",
        "allowed_claims": ["A relationship exists."],
        "source_evidence": [],
        "visible_entities": [],
        "provenance_ids": ["relationship:1"],
    }
    base.update(overrides)
    return NarrativeContext(**base)


def _out(prose: str) -> NarrativeOutput:
    return NarrativeOutput(prose=prose, provider="test", provider_model="test-model")


def test_provider_cannot_invent_temporal_consequence():
    context = _ctx()
    output = _out("After all this time, the village has fallen to ruin.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_temporal_consequence" for i in report.issues)


def test_authorized_temporal_fact_allows_phrasing():
    context = _ctx(
        temporal_facts=[
            "After all this time, the village has fallen to ruin.",
            "an elapsed interval of one year",
        ]
    )
    output = _out("After all this time, the village has fallen to ruin.")
    report = validate_narrative(context, output)
    assert report.verdict == "pass"


# --- Fictional time -----------------------------------------------------------


def test_fictional_time_is_distinct_from_real_time():
    with temporal.freeze_time(T0):
        real_now = temporal.iso_now()
        assert real_now == T0
        # A campaign with policy 'none' has no fictional clock.
        assert temporal.fictional_now("no_policy_campaign") is None


def test_manual_advance_obeys_policy():
    # Policy 'none' cannot be advanced manually.
    with pytest.raises(ValueError):
        temporal.advance_fictional_time("no_policy_campaign", delta_seconds=3600)

    from app import db

    db.update_campaign_time_settings_record(
        "manual_campaign", time_policy="manual", timezone="UTC"
    )
    result = temporal.advance_fictional_time("manual_campaign", delta_seconds=86400)
    assert result["settings"]["time_policy"] == "manual"
    assert result["settings"]["fictional_now_iso"] is not None


# --- Scheduled consequences ---------------------------------------------------


def test_schedule_consequence_requires_source():
    with pytest.raises(ValueError):
        temporal.schedule_consequence(
            session_id="sess_1",
            source_type="chronicle_event",
            source_id="",
            rule="rule",
        )


def test_scheduled_consequence_lifecycle_and_retire():
    from app.campaign_orchestrator import (
        list_scheduled_consequences,
        retire_scheduled_consequence,
    )

    session = _start()
    consequence = temporal.schedule_consequence(
        session_id=session["session_id"],
        source_type="chronicle_event",
        source_id="event_123",
        rule="promise deadline passes",
        min_elapsed_seconds=3600,
    )
    assert consequence["source_type"] == "chronicle_event"
    assert consequence["source_id"] == "event_123"
    assert consequence["lifecycle_state"] == "scheduled"

    listed = list_scheduled_consequences(session_id=session["session_id"])
    assert any(
        c["consequence_id"] == consequence["consequence_id"]
        for c in listed["scheduled_consequences"]
    )

    retired = retire_scheduled_consequence(consequence["consequence_id"])
    assert retired["consequence"]["lifecycle_state"] == "retired"
    # Idempotent.
    assert retire_scheduled_consequence(consequence["consequence_id"])["idempotent"]


# --- Temporal context & aspect-relative time ----------------------------------


def test_temporal_context_assembly():
    from app.campaign_orchestrator import inspect_temporal_context

    session = _start()
    with temporal.freeze_time(T0):
        result = inspect_temporal_context(session["session_id"])
    assert result["temporal_context"]["now_iso"] == T0
    assert result["temporal_context"]["time_source"] == "test_frozen"
    assert result["temporal_context"]["fictional_policy"] == "none"
    assert result["active_aspect"] == SOUL


def test_aspect_switch_preserves_independent_temporal_context():
    from app import db
    from app.campaign_orchestrator import inspect_temporal_context

    session = _start()
    # Register a second playable Aspect and switch to it.
    client.post(
        "/api/v1/campaign/aspects/register",
        json={"campaign_id": session["campaign_id"], "soul_id": OTHER},
    )
    switch = client.post(
        "/api/v1/campaign/aspects/switch",
        json={
            "campaign_id": session["campaign_id"],
            "session_id": session["session_id"],
            "target_soul_id": OTHER,
        },
    )
    assert switch.status_code == 200, switch.text

    first = db.get_or_create_aspect_temporal_state_record(session["campaign_id"], SOUL)
    second = db.get_or_create_aspect_temporal_state_record(
        session["campaign_id"], OTHER
    )
    assert first["soul_id"] == SOUL
    assert second["soul_id"] == OTHER

    view = inspect_temporal_context(session["session_id"])
    assert view["active_aspect"] == OTHER


def test_return_recap_is_gentle_and_optional():
    from app.campaign_orchestrator import build_return_recap

    session = _start()
    recap = build_return_recap(session["session_id"])
    assert recap["no_penalty"] is True
    assert recap["no_mandatory_chores"] is True
    assert "welcome_back" in recap
    assert recap["welcome_back"]["aspect"] == SOUL


def test_evaluate_temporal_eligibility_endpoint():
    session = _start()
    with temporal.freeze_time(T0):
        res = client.post(
            "/api/v1/campaign/time/evaluate",
            json={"session_id": session["session_id"]},
        )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["now_iso"] == T0
    assert body["fictional_policy"] == "none"
    assert "cooldowns" in body
    assert "scheduled_consequences" in body
