# backend/tests/test_living_visual.py
"""Phase 21: Living Visual World runtime tests.

These prove the canonical invariant: canon determines what may be depicted,
generated pixels never become canonical facts, and the Visual Canon Guardian
keeps false/hallucinated output out of history.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.living_visual import (
    evaluate_art_moments,
    get_art_moment,
    get_guardian_verdict,
    get_visual_job,
    process_visual_job,
)
from app.living_visual_compiler import compile_visual_scene_spec
from app.living_visual_provider import (
    VisualJobGenerationResult,
    requires_reference,
    workflow_role_for,
)
from app.main import app

client = TestClient(app)

SOUL = "Kaelen the Star-Watcher"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))
    monkeypatch.delenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", raising=False)


# ---------------------------------------------------------------------------
# Art Director eligibility (pure, deterministic)
# ---------------------------------------------------------------------------


def _state(**overrides) -> dict:
    base = {
        "soul_id": SOUL,
        "threads": [],
        "seeds": [],
        "relics": [],
        "memory_objects": [],
        "group_memories": [],
        "relationships": [],
        "promises": [],
        "world_memories": [],
        "place_history": [],
    }
    base.update(overrides)
    return base


def test_ordinary_state_yields_no_art_moment():
    assert evaluate_art_moments(_state()) == []


def test_integration_thread_becomes_eligible():
    state = _state(
        threads=[{"id": "t1", "name": "Salt", "status": "pattern_recognized"}]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "chronicle_painting" for m in moments)


def test_remembered_relic_does_not_produce_relic_visual():
    # A Remembered relic is an awakening *candidate*, not a validated change.
    state = _state(relics=[{"id": "r1", "name": "Salt Bell", "stage": "Remembered"}])
    assert not any(m["visual_type"] == "relic" for m in evaluate_art_moments(state))


def test_awakened_relic_produces_visual_opportunity():
    state = _state(relics=[{"id": "r1", "name": "Salt Bell", "stage": "Awakened"}])
    moments = evaluate_art_moments(state)
    assert any(
        m["visual_type"] == "relic" and m["source_entity_id"] == "r1" for m in moments
    )


def test_significant_memory_object_is_eligible():
    state = _state(
        memory_objects=[
            {
                "id": "mem1",
                "event_title": "The Awakening",
                "is_painting_eligible": True,
                "importance_tier": "community",
                "importance_score": 8,
                "relics_involved": ["Salt Bell"],
                "location_environment": "Salt spire",
                "emotional_tone": "Solemn",
                "action_composition": "Channeling starlight",
                "lasting_consequence": "The bell awoke",
                "participants": [
                    {
                        "soul_id": SOUL,
                        "character_name": "Kaelen",
                        "role_in_event": "Focus",
                        "portrait_version_id": "pv1",
                    }
                ],
            }
        ]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "memory_object" for m in moments)


def test_relationship_with_events_is_eligible():
    state = _state(
        relationships=[
            {
                "relationship_id": "rel1",
                "kinds": ["mentor"],
                "events": [{"summary": "A reunion"}],
                "participants": [],
            }
        ]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "relationship" for m in moments)


def test_promise_fulfillment_is_eligible():
    state = _state(
        promises=[
            {
                "promise_id": "p1",
                "promise_text": "I will return.",
                "lifecycle_state": "fulfilled",
                "participants": [],
            }
        ]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "relationship" for m in moments)


def test_significant_group_memory_is_eligible():
    state = _state(
        group_memories=[
            {
                "group_id": "g1",
                "title": "The shared vigil",
                "group_significance": "community",
                "summary": "Many witnessed.",
                "members": [],
            }
        ]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "group_memory" for m in moments)


def test_place_accumulating_history_is_eligible():
    state = _state(
        place_history=[
            {"place_id": "place1", "event_type": "encounter"},
            {"place_id": "place1", "event_type": "return"},
        ]
    )
    moments = evaluate_art_moments(state)
    assert any(m["visual_type"] == "place" for m in moments)


def test_continuity_types_require_reference():
    assert requires_reference("portrait_continuity") is True
    assert requires_reference("portrait") is False
    assert workflow_role_for("portrait_continuity") == "portrait_reference"


def test_unknown_facts_remain_unknown_in_scene_spec():
    spec = compile_visual_scene_spec(
        visual_type="place",
        title="A place",
        unknown_fields=["time_of_day", "weather"],
    )
    assert spec.unknown_fields == ["time_of_day", "weather"]
    assert spec.location is None
    # Unknown facts are not back-filled with invented specificity.
    assert "time_of_day" not in spec.action_facts


# ---------------------------------------------------------------------------
# Runtime flow (mock provider, deterministic)
# ---------------------------------------------------------------------------


def _make_soul(soul_id: str) -> str:
    client.post(
        "/api/v1/visual/avatar/create",
        json={
            "soul_id": soul_id,
            "face": "Defined features",
            "hair": "Dark hair",
            "body": "Athletic build",
            "species": "Human Aspect",
            "eyes": "Amber eyes",
        },
    )
    profile = client.get(f"/api/v1/visual/avatar/{soul_id}").json()
    return profile["portraits"][0]["version_id"]


def _compile_memory(soul_id: str, portrait_version_id: str, **overrides) -> dict:
    payload = {
        "event_id": f"evt_{str(uuid.uuid4())[:8]}",
        "event_title": "The Salt Spire Awakening",
        "participants": [
            {
                "soul_id": soul_id,
                "character_name": "Kaelen",
                "portrait_version_id": portrait_version_id,
                "role_in_event": "Focus",
                "real_person_tag_opt_in": False,
            }
        ],
        "location_environment": "Salt-encrusted subterranean sanctuary",
        "relics_involved": ["Dormant Salt Bell"],
        "emotional_tone": "Tense awakening",
        "action_composition": "Kaelen channels starlight.",
        "lasting_consequence": "The Salt Bell awakened.",
        "privacy_consent_scope": "public_canon",
        "importance_tier": "community",
        "importance_score": 8,
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory_object"]


def _start_session(soul_id: str = SOUL) -> dict:
    res = client.post(
        "/api/v1/campaign/session",
        json={"soul_id": soul_id, "campaign_id": "phase21_campaign"},
    )
    assert res.status_code == 200, res.text
    return res.json()["session"]


def test_queue_is_idempotent():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)

    first = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()
    second = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()
    assert first["created"] >= 1
    assert second["created"] == 0


def test_process_quarantines_then_approves_with_provenance():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    queued = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()
    job = queued["jobs"][0]
    assert job["generation_state"] == "queued"
    assert job["provider"] == "mock"

    processed = client.post(
        f"/api/v1/living-visuals/jobs/{job['job_id']}/process"
    ).json()["job"]
    assert processed["generation_state"] == "completed"
    assert processed["guardian_status"] == "passed"
    assert processed["quarantined_image_url"]
    assert processed["final_image_url"]
    assert processed["provider_model"]
    assert processed["workflow_role"]
    assert processed["workflow_version"]

    approved = client.post(
        f"/api/v1/living-visuals/jobs/{job['job_id']}/approve"
    ).json()["job"]
    assert approved["generation_state"] == "approved"

    verdict = client.get(f"/api/v1/living-visuals/jobs/{job['job_id']}/guardian").json()
    assert verdict["guardian_status"] == "passed"
    assert len(verdict["history"]) >= 1


def test_blocked_output_never_becomes_approved(monkeypatch):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    job = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()["jobs"][0]

    processed = client.post(
        f"/api/v1/living-visuals/jobs/{job['job_id']}/process"
    ).json()["job"]
    assert processed["generation_state"] == "blocked"

    res = client.post(f"/api/v1/living-visuals/jobs/{job['job_id']}/approve")
    assert res.status_code == 400


def test_provider_failure_does_not_touch_canon(monkeypatch):
    from app import living_visual as lv

    class FailingProvider:
        def generate(self, request):
            return VisualJobGenerationResult(
                success=False, provider="mock", failure_reason="outage"
            )

        def capabilities(self):
            return {"provider": "mock"}

        def status(self):
            return {"provider": "mock", "healthy": False}

    monkeypatch.setattr(
        lv, "get_living_visual_provider", lambda *a, **k: FailingProvider()
    )

    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    session = _start_session(soul)
    job = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()["jobs"][0]

    processed = client.post(
        f"/api/v1/living-visuals/jobs/{job['job_id']}/process"
    ).json()["job"]
    assert processed["generation_state"] == "failed"

    # Canonical memory object is untouched.
    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert after["event_title"] == mem["event_title"]
    assert after["visual_generation_status"] == "compiled"


def test_regenerate_creates_new_job_without_mutating_canon():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    job = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()["jobs"][0]

    regenerated = client.post(
        f"/api/v1/living-visuals/jobs/{job['job_id']}/regenerate"
    ).json()["job"]
    assert regenerated["job_id"] != job["job_id"]
    assert regenerated["superseded_job_id"] == job["job_id"]
    assert regenerated["retry_count"] == job["retry_count"] + 1


def test_human_curation_cannot_change_locked_facts():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    queued = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()
    moment_id = queued["art_moments"][0]["art_moment_id"]
    before = get_art_moment(moment_id)["art_moment"]

    res = client.post(
        f"/api/v1/living-visuals/art-moments/{moment_id}/curate",
        json={
            "contributor_id": "curator1",
            "contributor_name": "Mythmaker",
            "style_guidance": "watercolor",
            "mood": "hopeful",
        },
    )
    assert res.status_code == 200
    after = get_art_moment(moment_id)["art_moment"]
    # Locked facts unchanged.
    assert after["spec"]["title"] == before["spec"]["title"]
    assert (
        after["spec"]["permitted_participants"]
        == before["spec"]["permitted_participants"]
    )
    # Interpretation fields updated.
    assert after["spec"]["style_guidance"] == "watercolor"
    assert after["spec"]["mood"] == "hopeful"


def test_restart_recovers_queued_job():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    job = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()["jobs"][0]

    # Simulate a fresh read (recovery after restart): the job is still queued
    # and can be processed without re-enqueueing.
    recovered = get_visual_job(job["job_id"])["job"]
    assert recovered["generation_state"] == "queued"
    processed = process_visual_job(job["job_id"])
    assert processed["job"]["generation_state"] == "completed"


def test_guardian_verdict_history_persists():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    session = _start_session(soul)
    job = client.post(
        "/api/v1/living-visuals/art-moments/evaluate",
        json={"session_id": session["session_id"]},
    ).json()["jobs"][0]
    client.post(f"/api/v1/living-visuals/jobs/{job['job_id']}/process")
    verdict = get_guardian_verdict(job["job_id"])
    assert verdict["guardian_report"]["status"] == "pass"
    assert len(verdict["history"]) == 1
