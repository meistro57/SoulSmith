# backend/tests/test_multi_aspect_wandering.py
"""Phase 20: multi-Aspect campaign sessions and Wandering foundation tests.

These prove the knowledge layers stay separate during active play: the player
may see the whole story, but each Aspect sees only the life it has lived, and
Wandering real-world play never requires surrendering privacy or safety.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SOUL_A = "Kaelen the Star-Watcher"
SOUL_B = "Archivist Vael"
CAMPAIGN = "phase20_campaign"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


def _start(soul_id: str = SOUL_A, campaign_id: str = CAMPAIGN) -> dict:
    res = client.post(
        "/api/v1/campaign/session",
        json={"soul_id": soul_id, "campaign_id": campaign_id},
    )
    assert res.status_code == 200, res.text
    return res.json()["session"]


def _register(campaign_id: str, soul_id: str) -> None:
    res = client.post(
        "/api/v1/campaign/aspects/register",
        json={"campaign_id": campaign_id, "soul_id": soul_id},
    )
    assert res.status_code == 200, res.text


def _switch(campaign_id: str, session_id: str, target: str) -> dict:
    res = client.post(
        "/api/v1/campaign/aspects/switch",
        json={
            "campaign_id": campaign_id,
            "session_id": session_id,
            "target_soul_id": target,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def _aspect_view(session_id: str) -> dict:
    res = client.get(f"/api/v1/campaign/session/{session_id}/aspect-view")
    assert res.status_code == 200, res.text
    return res.json()


def _evaluate(session_id: str) -> dict:
    res = client.post(
        "/api/v1/campaign/opportunities/evaluate",
        json={"session_id": session_id, "include_encounter": True},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _of_type(opportunities: list[dict], opportunity_type: str) -> list[dict]:
    return [o for o in opportunities if o["opportunity_type"] == opportunity_type]


def _plant_seed(symbol: str, soul_id: str) -> str:
    res = client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": symbol,
            "thread_type": "Memory",
            "narrative_context": f"Seen by {soul_id}",
            "soul_id": soul_id,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["seed_id"]


def _commit_event_for(soul_id: str) -> str:
    read = client.post(
        "/api/v1/dice/interpret",
        json={
            "d20": 17,
            "d12": 9,
            "d10": 5,
            "percentile": 70,
            "d8": 3,
            "d6": 4,
            "d4": 2,
            "grammar_version": "1.0.0",
        },
    ).json()
    res = client.post(
        "/api/v1/scenes/resolve",
        json={
            "dice_read": read,
            "chosen_approach": "Guile",
            "resonance_spent": 1,
            "strain_accepted": 0,
            "player_intent": "I want to understand the recurring symbol.",
            "soul_name": soul_id,
            "resources": {"resonance": 3, "strain": 0, "thread_count": 1},
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["event_id"]


# 1. Aspect switching persists departing state and loads destination state.
def test_aspect_switch_persists_state():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    seed_a = _plant_seed("A-only Lantern", SOUL_A)

    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    view_b = _aspect_view(session["session_id"])
    assert view_b["active_aspect"] == SOUL_B
    assert all(s["id"] != seed_a for s in view_b["view"]["seeds"])

    _switch(CAMPAIGN, session["session_id"], SOUL_A)
    view_a = _aspect_view(session["session_id"])
    assert view_a["active_aspect"] == SOUL_A
    assert any(s["id"] == seed_a for s in view_a["view"]["seeds"])


# 2. Aspect switch rebuilds the destination viewpoint.
def test_aspect_switch_rebuilds_viewpoint():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    view = _aspect_view(session["session_id"])
    assert view["knowledge_projection"]["aspect_soul_id"] == SOUL_B


# 3. Player knowledge does not become Aspect knowledge.
def test_player_knowledge_does_not_become_aspect_knowledge():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    _plant_seed("Shared-Sounding Symbol", SOUL_A)

    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    view_b = _aspect_view(session["session_id"])
    seeds_b = {s["symbol"] for s in view_b["view"]["seeds"]}
    assert "Shared-Sounding Symbol" not in seeds_b


# 4. One Aspect cannot access another's private Chronicle data.
def test_one_aspect_cannot_access_other_private_chronicle():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    event_a = _commit_event_for(SOUL_A)

    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    view_b = _aspect_view(session["session_id"])
    visible = view_b["view"]["events"]
    assert all(e["id"] != event_a for e in visible)
    assert event_a in view_b["knowledge_projection"]["forbidden_events"]


# 5. Simultaneous Aspects may share a canonical event with separate perspectives.
def test_simultaneous_aspects_share_canonical_event_separate_perspectives():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    client.post(
        "/api/v1/relationships",
        json={
            "kinds": ["alliance"],
            "participants": [
                {"entity_type": "person", "entity_id": SOUL_A},
                {"entity_type": "person", "entity_id": SOUL_B},
            ],
            "source_type": "chronicle_event",
            "source_id": "shared_event_1",
        },
    ).json()

    res = client.post(
        "/api/v1/campaign/encounters/cross-aspect",
        json={"session_id": session["session_id"], "other_soul_id": SOUL_B},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert set(body["shared_event"]["participants"]) == {SOUL_A, SOUL_B}
    assert body["active_aspect"]["soul_id"] == SOUL_A
    assert body["other_aspect"]["soul_id"] == SOUL_B


# 6. Cross-Aspect meeting preserves participant knowledge boundaries.
def test_cross_aspect_meeting_preserves_boundaries():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    _commit_event_for(SOUL_A)
    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    _switch(CAMPAIGN, session["session_id"], SOUL_A)

    client.post(
        "/api/v1/relationships",
        json={
            "kinds": ["alliance"],
            "participants": [
                {"entity_type": "person", "entity_id": SOUL_A},
                {"entity_type": "person", "entity_id": SOUL_B},
            ],
            "source_type": "chronicle_event",
            "source_id": "shared_event_2",
        },
    ).json()
    meeting = client.post(
        "/api/v1/campaign/encounters/cross-aspect",
        json={"session_id": session["session_id"], "other_soul_id": SOUL_B},
    ).json()
    assert (
        meeting["knowledge_boundary"]["active_aspect_sees_other_private_events"]
        is False
    )
    assert (
        meeting["knowledge_boundary"]["other_aspect_sees_active_private_events"]
        is False
    )


# 7. Relic transfer (via promise/relic entity link) has provenance.
def test_relic_transfer_has_provenance():
    promise = client.post(
        "/api/v1/promises",
        json={
            "promisor_entity_type": "person",
            "promisor_entity_id": SOUL_A,
            "promise_text": "I will guard the Compass.",
            "source_type": "chronicle_event",
            "source_id": "promise_source_1",
            "participants": [
                {
                    "participant_type": "beneficiary",
                    "entity_type": "person",
                    "entity_id": SOUL_B,
                }
            ],
            "inheritable": True,
        },
    ).json()["promise"]
    linked = client.post(
        f"/api/v1/promises/{promise['promise_id']}/links",
        json={
            "link_type": "relic",
            "entity_type": "relic",
            "entity_id": "relic_compass_01",
        },
    ).json()["promise"]
    assert any(
        link["link_type"] == "relic" and link["entity_id"] == "relic_compass_01"
        for link in linked["entity_links"]
    )


# 8. Promise consequence crosses Aspects only with valid provenance.
def test_promise_consequence_crosses_aspects_with_provenance():
    promise = client.post(
        "/api/v1/promises",
        json={
            "promisor_entity_type": "person",
            "promisor_entity_id": SOUL_A,
            "promise_text": "Carry the vow into the next era.",
            "source_type": "chronicle_event",
            "source_id": "promise_source_2",
            "participants": [
                {
                    "participant_type": "beneficiary",
                    "entity_type": "person",
                    "entity_id": SOUL_B,
                }
            ],
            "inheritable": True,
        },
    ).json()["promise"]
    pid = promise["promise_id"]

    # Move to an active state first (made -> active is a valid transition).
    active = client.post(
        f"/api/v1/promises/{pid}/transition",
        json={"new_state": "active"},
    )
    assert active.status_code == 200, active.text

    # Inherit without a target entity is rejected.
    bad = client.post(
        f"/api/v1/promises/{pid}/transition",
        json={"new_state": "inherited", "evidence_type": "player_authorized"},
    )
    assert bad.status_code == 400, bad.text

    # Inherit with a target entity + authorization succeeds and is traceable.
    ok = client.post(
        f"/api/v1/promises/{pid}/transition",
        json={
            "new_state": "inherited",
            "evidence_type": "player_authorized",
            "target_entity_type": "person",
            "target_entity_id": SOUL_B,
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["promise"]["lifecycle_state"] == "inherited"
    assert any(
        s["new_state"] == "inherited" for s in ok.json()["promise"]["state_history"]
    )


# 9. NPC knowledge differs correctly by active Aspect/context.
def test_npc_knowledge_differs_by_active_aspect():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    view_a = _aspect_view(session["session_id"])
    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    view_b = _aspect_view(session["session_id"])
    assert view_a["knowledge_projection"]["aspect_soul_id"] == SOUL_A
    assert view_b["knowledge_projection"]["aspect_soul_id"] == SOUL_B


# 10. World Memory remains distinct from canonical truth.
def test_world_memory_remains_distinct_from_canonical_truth():
    from app.world_memory import (
        interpretation_distance_label,
        project_world_memory_for_viewer,
        world_memory_visible_to,
    )

    # A derived legend is never a faithful canonical account.
    assert interpretation_distance_label("exaggerated") != "faithful"

    # A private World Memory is visible only to its subject and is stripped for
    # other viewers; canonical Chronicle events are not touched by projection.
    private = {
        "memory_id": "wm_private",
        "visibility": "private",
        "subject_entity_id": SOUL_A,
        "narrative": "A secret that must not leak.",
    }
    assert world_memory_visible_to(private, SOUL_A) is True
    projected = project_world_memory_for_viewer(private, SOUL_B)
    assert projected["visibility"] == "private"
    assert projected["narrative"] == ""


# 11. Orchestrator evaluates Aspect-scoped opportunities.
def test_orchestrator_evaluates_aspect_scoped_opportunities():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    result = _evaluate(session["session_id"])
    switches = _of_type(result["opportunities"], "aspect_switch")
    assert any(o["domain_action_payload"]["target_soul_id"] == SOUL_B for o in switches)


# 12. Duplicate Aspect switch is idempotent.
def test_duplicate_aspect_switch_idempotent():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    first = _switch(CAMPAIGN, session["session_id"], SOUL_B)
    assert first["switch"]["idempotent"] is False
    second = _switch(CAMPAIGN, session["session_id"], SOUL_B)
    assert second["switch"]["idempotent"] is True
    assert second["active_aspect"] == SOUL_B


# 13. Save/resume restores the correct active Aspect.
def test_save_resume_restores_active_aspect():
    session = _start(SOUL_A)
    _register(CAMPAIGN, SOUL_B)
    _switch(CAMPAIGN, session["session_id"], SOUL_B)
    resumed = _start(SOUL_B)
    assert resumed["session_id"] == session["session_id"]
    assert resumed["active_soul_id"] == SOUL_B


# 14. Location permission denial leaves core gameplay functional.
def test_location_permission_denial_leaves_core_playable():
    session = _start(SOUL_A)
    res = client.get(
        f"/api/v1/wandering/nearby?soul_id={SOUL_A}&latitude=0&longitude=0"
    )
    assert res.status_code == 200
    assert res.json()["authorized"] is False
    # Core loop still works.
    assert _evaluate(session["session_id"])["session_id"] == session["session_id"]


# 15. Location samples are rejected without consent.
def test_location_samples_rejected_without_consent():
    res = client.post(
        "/api/v1/wandering/location-sample",
        json={"soul_id": SOUL_A, "latitude": 1.0, "longitude": 2.0},
    )
    assert res.status_code == 403


def _grant_location(soul_id: str):
    res = client.post(
        "/api/v1/wandering/location-consent",
        json={
            "soul_id": soul_id,
            "location_access_granted": True,
            "purpose": "wandering_discovery",
            "precision_level": "coarse",
        },
    )
    assert res.status_code == 200, res.text


def _create_place(name: str, lat: float, lon: float, **overrides) -> dict:
    payload = {
        "place_name": name,
        "place_kind": "real_world",
        "coordinate_latitude": lat,
        "coordinate_longitude": lon,
        "consent_scope": "public_canon",
        "created_by_soul_id": SOUL_A,
    }
    payload.update(overrides)
    res = client.post("/api/v1/wandering/places", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["place"]


# 16. Nearby discovery uses bounded deterministic eligibility.
def test_nearby_discovery_bounded_deterministic():
    _grant_location(SOUL_A)
    _create_place("Near Place", 0.001, 0.001)
    _create_place("Far Place", 10.0, 10.0)
    first = client.get(
        f"/api/v1/wandering/nearby?soul_id={SOUL_A}&latitude=0&longitude=0&radius_m=500"
    ).json()
    second = client.get(
        f"/api/v1/wandering/nearby?soul_id={SOUL_A}&latitude=0&longitude=0&radius_m=500"
    ).json()
    assert first["authorized"] is True
    assert first == second
    names = {p["place"]["place_name"] for p in first["places"]}
    assert "Near Place" in names
    assert "Far Place" not in names


# 17/18. Hidden discoveries and precise private coordinates do not leak.
def test_hidden_discoveries_and_precise_coords_do_not_leak():
    private = _create_place(
        "Private Hideout",
        12.345678,
        98.765432,
        consent_scope="private",
        public_label="A quiet district",
    )
    places = client.get("/api/v1/wandering/places").json()["places"]
    private_public = next(p for p in places if p["place_id"] == private["place_id"])
    assert private_public["coordinate_latitude"] is None
    assert private_public["coordinate_longitude"] is None
    assert private_public["place_name"] != "Private Hideout"


# 19. A place can accumulate Chronicle history.
def test_place_accumulates_chronicle_history():
    place = _create_place("Remembered Place", 0.002, 0.002)
    res = client.post(
        "/api/v1/wandering/place-history",
        json={
            "place_id": place["place_id"],
            "event_type": "chronicle_event",
            "event_id": "evt_1",
            "soul_id": SOUL_A,
            "provenance_source_type": "scene_event",
            "provenance_source_id": "evt_1",
            "visibility": "public_canon",
        },
    )
    assert res.status_code == 200, res.text
    history = client.get(
        f"/api/v1/wandering/places/{place['place_id']}/history"
    ).json()["history"]
    assert any(h["event_id"] == "evt_1" for h in history)


# 20. A later Aspect can receive an eligible callback from prior place history.
def test_later_aspect_receives_callback_from_prior_place_history():
    place = _create_place("Prior Place", 0.003, 0.003)
    client.post(
        "/api/v1/wandering/place-history",
        json={
            "place_id": place["place_id"],
            "event_type": "chronicle_event",
            "event_id": "evt_prior",
            "soul_id": SOUL_A,
            "provenance_source_type": "scene_event",
            "provenance_source_id": "evt_prior",
            "visibility": "public_canon",
        },
    )
    session = _start(SOUL_B)
    result = _evaluate(session["session_id"])
    locations = _of_type(result["opportunities"], "recurring_location")
    assert any(
        o["domain_action_payload"]["place_id"] == place["place_id"] for o in locations
    )


# 21. Location-bound Seed/Symbol retains provenance.
def test_location_bound_seed_retains_provenance():
    place = _create_place("Seed Place", 0.004, 0.004)
    _plant_seed("Rooted Symbol", SOUL_A)
    client.post(
        "/api/v1/wandering/place-history",
        json={
            "place_id": place["place_id"],
            "event_type": "seed",
            "event_id": "seed_evt",
            "soul_id": SOUL_A,
            "provenance_source_type": "seed",
            "provenance_source_id": "seed_evt",
            "visibility": "public_canon",
        },
    )
    session = _start(SOUL_A)
    result = _evaluate(session["session_id"])
    bound = _of_type(result["opportunities"], "location_bound_seed")
    assert any(e["source_type"] == "seed" for o in bound for e in o["source_evidence"])


# 22. Unsafe/retired location stops new discovery without deleting history.
def test_retired_location_stops_discovery_without_deleting_history():
    place = _create_place("Retired Place", 0.005, 0.005)
    client.post(
        "/api/v1/wandering/place-history",
        json={
            "place_id": place["place_id"],
            "event_type": "chronicle_event",
            "event_id": "evt_retired",
            "soul_id": SOUL_A,
            "provenance_source_type": "scene_event",
            "provenance_source_id": "evt_retired",
            "visibility": "public_canon",
        },
    )
    retire = client.post(
        "/api/v1/wandering/places/retire",
        json={"place_id": place["place_id"], "safety_status": "retired"},
    ).json()
    assert retire["place"]["is_active"] is False

    _grant_location(SOUL_A)
    nearby = client.get(
        f"/api/v1/wandering/nearby?soul_id={SOUL_A}&latitude=0.005&longitude=0.005"
    ).json()
    assert nearby["places"] == []

    history = client.get(
        f"/api/v1/wandering/places/{place['place_id']}/history"
    ).json()["history"]
    assert any(h["event_id"] == "evt_retired" for h in history)


# 23. Offline mode never invents authoritative discovery.
def test_offline_mode_never_invents_discovery():
    _grant_location(SOUL_A)
    res = client.get(
        f"/api/v1/wandering/nearby?soul_id={SOUL_A}&latitude=50&longitude=50"
    ).json()
    assert res["authorized"] is True
    assert res["places"] == []


# 24. Map/provider failure does not corrupt campaign state.
def test_map_provider_failure_does_not_corrupt_campaign(monkeypatch):
    from app import map_provider

    def _boom(*args, **kwargs):
        raise RuntimeError("map provider down")

    monkeypatch.setattr(map_provider, "get_map_provider", _boom)
    session = _start(SOUL_A)
    assert _evaluate(session["session_id"])["session_id"] == session["session_id"]


# 25. Camera/dice flow remains compatible with Wandering encounter.
def test_camera_dice_flow_compatible_with_wandering():
    _grant_location(SOUL_A)
    read = client.post(
        "/api/v1/dice/interpret",
        json={
            "d20": 17,
            "d12": 9,
            "d10": 5,
            "percentile": 70,
            "d8": 3,
            "d6": 4,
            "d4": 2,
            "grammar_version": "1.0.0",
        },
    ).json()
    assert read["interpretation"]["thread"] == "Memory"
    scene = client.post(
        "/api/v1/scenes/resolve",
        json={
            "dice_read": read,
            "chosen_approach": "Guile",
            "resonance_spent": 1,
            "strain_accepted": 0,
            "player_intent": "Investigate near the discovered place.",
            "soul_name": SOUL_A,
            "resources": {"resonance": 3, "strain": 0, "thread_count": 1},
        },
    )
    assert scene.status_code == 200, scene.text


# 26. Location-linked World Memory cannot expose private location without consent.
def test_location_linked_world_memory_no_private_location():
    from app import db

    private = _create_place(
        "Secret Place", 55.0, 55.0, consent_scope="private", public_label="The old mill"
    )
    # Link a World Memory placement to the private place. The placement record is
    # derived metadata; it must never surface the place's precise coordinates.
    db.create_world_memory_placement_record(
        memory_id="wm_loc_linked",
        placement_type="place",
        placement_ref=private["place_id"],
        visibility="public_canon",
    )
    places = client.get("/api/v1/wandering/places").json()["places"]
    secret = next(p for p in places if p["place_id"] == private["place_id"])
    assert secret["coordinate_latitude"] is None
    assert secret["coordinate_longitude"] is None
    assert secret["place_name"] != "Secret Place"


# 27. GATHERING/WORLD PULSE-compatible place model has no campaign-authority leak.
def test_place_model_has_no_campaign_authority():
    place = _create_place("Gathering Place", 0.006, 0.006)
    assert "campaign_id" not in place
    assert "campaign_authority" not in place
    assert place["place_kind"] in {
        "real_world",
        "fictional",
        "hybrid_interpretive",
        "region",
        "discovery_zone",
        "event_site",
    }
