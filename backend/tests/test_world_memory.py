# backend/tests/test_world_memory.py
import uuid

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from app.world_memory import (
    GeneratedWorldMemoryArtifact,
    WorldMemorySourceRef,
    WorldMemorySpec,
)
from app.world_memory_guardian import get_world_memory_guardian
from app.world_memory_provider import get_world_memory_provider

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


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
        "relics_involved": [],
        "emotional_tone": "Tense awakening",
        "action_composition": "Kaelen channels starlight.",
        "lasting_consequence": "The Salt Bell awakened.",
        "privacy_consent_scope": "public_canon",
        "importance_tier": "personal",
        "importance_score": 5,
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory_object"]


def _compile_world_memory(
    subject_entity_type: str, subject_entity_id: str, **overrides
) -> dict:
    payload = {
        "subject_entity_type": subject_entity_type,
        "subject_entity_id": subject_entity_id,
    }
    payload.update(overrides)
    res = client.post("/api/v1/world-memory/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory"]


def test_canonical_event_produces_derived_world_memory():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    memory = _compile_world_memory(
        "event", mem["event_id"], memory_form="historical_account"
    )

    assert memory["subject_entity_id"] == mem["event_id"]
    assert memory["interpretation_type"] == "faithful"
    assert any(r["source_type"] == "memory_object" for r in memory["source_refs"])


def test_source_chronicle_record_remains_unchanged():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    _compile_world_memory("event", mem["event_id"])

    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert before == after


def test_faithful_historical_account_preserves_provenance():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    memory = _compile_world_memory(
        "event",
        mem["event_id"],
        memory_form="historical_account",
        interpretation_type="faithful",
    )

    assert memory["interpretation_type"] == "faithful"
    assert memory["source_refs"], "faithful account must preserve provenance"
    assert memory["deviations"] == []


def test_exaggerated_legend_stores_explicit_drift():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    memory = _compile_world_memory(
        "event", mem["event_id"], interpretation_type="exaggerated"
    )

    assert memory["interpretation_type"] == "exaggerated"
    assert any(d["deviation_kind"] == "exaggeration" for d in memory["deviations"])


def test_undeclared_hallucinated_fact_fails_validation():
    guardian = get_world_memory_guardian()
    spec = WorldMemorySpec(
        subject_entity_type="event",
        subject_entity_id="evt_1",
        memory_form="legend",
        interpretation_type="faithful",
        allowed_claims=["Rowan defeated three giants at the northern gate."],
        source_refs=[
            WorldMemorySourceRef(source_type="memory_object", source_id="mo_1")
        ],
    )
    artifact = GeneratedWorldMemoryArtifact(
        title="The Legend of Rowan",
        narrative="Rowan slew twelve giants alone beneath a blood-red moon.",
        claims=["Rowan slew twelve giants alone beneath a blood-red moon."],
        source_refs=list(spec.source_refs),
    )
    report = guardian.validate(artifact=artifact, spec=spec)
    assert report.status == "block"
    assert any(v["type"] == "undeclared_hallucinated_fact" for v in report.violations)


def test_multiple_cultures_hold_conflicting_legends_without_altering_canon():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    a = _compile_world_memory(
        "event", mem["event_id"], culture="Salt Kingdom", interpretation_type="faithful"
    )
    b = _compile_world_memory(
        "event",
        mem["event_id"],
        culture="River Baronies",
        interpretation_type="contradictory",
    )

    assert a["culture"] != b["culture"]
    assert a["interpretation_type"] != b["interpretation_type"]

    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert before == after


def test_legendary_figure_links_without_mutating_identity():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv, importance_tier="world", importance_score=9)
    portrait_before = client.get(
        f"/api/v1/visual-memory/portraits/versions/{pv}"
    ).json()["portrait_version"]

    res = client.post(
        "/api/v1/legendary-figures/promote",
        json={
            "subject_entity_type": "person",
            "subject_entity_id": soul,
            "subject_soul_id": soul,
            "figure_title": "Kaelen the Star-Watcher",
            "later_cultural_titles": ["The Salt Saint"],
        },
    )
    assert res.status_code == 200, res.text
    figure = res.json()["figure"]
    assert figure["figure_title"] == "Kaelen the Star-Watcher"
    assert "The Salt Saint" in figure["later_cultural_titles"]

    portrait_after = client.get(
        f"/api/v1/visual-memory/portraits/versions/{pv}"
    ).json()["portrait_version"]
    assert portrait_before == portrait_after


def test_later_cultural_title_remains_distinct_from_canonical_title():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv, importance_tier="world", importance_score=9)

    res = client.post(
        "/api/v1/legendary-figures/promote",
        json={
            "subject_entity_type": "person",
            "subject_entity_id": soul,
            "subject_soul_id": soul,
            "figure_title": "Kaelen the Star-Watcher",
            "later_cultural_titles": ["The Salt Saint"],
        },
    )
    figure = res.json()["figure"]
    assert figure["figure_title"] != figure["later_cultural_titles"][0]


def test_public_legend_cannot_leak_private_participant_information():
    guardian = get_world_memory_guardian()
    spec = WorldMemorySpec(
        subject_entity_type="event",
        subject_entity_id="evt_1",
        memory_form="legend",
        interpretation_type="faithful",
        visibility="public_canon",
        allowed_claims=["The battle was fought."],
        source_refs=[
            WorldMemorySourceRef(
                source_type="memory_object",
                source_id="mo_private",
                claim_kind="participant_perspective",
            )
        ],
    )
    artifact = GeneratedWorldMemoryArtifact(
        title="The Legend",
        narrative="A private recollection is told.",
        claims=["The battle was fought."],
        source_refs=list(spec.source_refs),
    )
    report = guardian.validate(artifact=artifact, spec=spec)
    assert report.status == "block"
    assert any(v["type"] == "private_information_leak" for v in report.violations)


def test_npc_knowledge_scoped_by_culture_and_access():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    _compile_world_memory(
        "event",
        mem["event_id"],
        culture="Salt Kingdom",
        memory_form="folk_tale",
        interpretation_type="mythologized",
    )

    peasant = client.post(
        "/api/v1/world-memory/npc-knowledge",
        json={
            "subject_entity_type": "event",
            "subject_entity_id": mem["event_id"],
            "culture": "River Baronies",
            "social_role": "commoner",
        },
    ).json()["knowledge"]
    assert peasant["entries"] == []

    local = client.post(
        "/api/v1/world-memory/npc-knowledge",
        json={
            "subject_entity_type": "event",
            "subject_entity_id": mem["event_id"],
            "culture": "Salt Kingdom",
            "social_role": "commoner",
        },
    ).json()["knowledge"]
    assert local["entries"]


def test_npc_cannot_automatically_access_omniscient_canon():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    _compile_world_memory(
        "event",
        mem["event_id"],
        culture="Salt Kingdom",
        memory_form="folk_tale",
        interpretation_type="mythologized",
    )

    knowledge = client.post(
        "/api/v1/world-memory/npc-knowledge",
        json={
            "subject_entity_type": "event",
            "subject_entity_id": mem["event_id"],
            "culture": "Salt Kingdom",
            "social_role": "commoner",
            "education_level": "low",
            "access_to_archives": False,
        },
    ).json()["knowledge"]
    assert knowledge["canonical_truth_accessible"] is False
    assert all(not e["canonical_truth_visible"] for e in knowledge["entries"])


def test_relic_legend_remains_distinct_from_relic_history():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    relic_id = "relic_legend_test_01"
    mem = _compile_memory(soul, pv, relics_involved=[relic_id])
    history_before = db.get_relic_history_records(relic_id)

    memory = _compile_world_memory(
        "relic",
        relic_id,
        memory_form="relic_legend",
        interpretation_type="mythologized",
    )

    assert memory["memory_form"] == "relic_legend"
    assert memory["interpretation_type"] == "mythologized"
    assert db.get_relic_history_records(relic_id) == history_before
    assert mem["relics_involved"] == [relic_id]


def test_world_forgetting_does_not_delete_canon():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    memory = _compile_world_memory("event", mem["event_id"])
    res = client.post(
        f"/api/v1/world-memory/{memory['memory_id']}/mark-state",
        json={"new_state": "forgotten", "reason": "A later age lost the telling."},
    )
    assert res.json()["memory"]["memory_state"] == "forgotten"

    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert before == after


def test_rediscovery_restores_visibility_not_canon():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    memory = _compile_world_memory("event", mem["event_id"])
    client.post(
        f"/api/v1/world-memory/{memory['memory_id']}/mark-state",
        json={"new_state": "forgotten"},
    )
    rediscovered = client.post(
        f"/api/v1/world-memory/{memory['memory_id']}/mark-state",
        json={"new_state": "rediscovered", "reason": "Ruins revealed the old account."},
    ).json()["memory"]
    assert rediscovered["memory_state"] == "rediscovered"

    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert before == after


def test_monument_placement_retains_provenance():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    memory = _compile_world_memory(
        "event", mem["event_id"], memory_form="monument_statue"
    )

    res = client.post(
        f"/api/v1/world-memory/{memory['memory_id']}/placements",
        json={"placement_type": "location", "placement_ref": "Northern Gate"},
    )
    placement = res.json()["placement"]
    assert placement["placement_ref"] == "Northern Gate"
    assert memory["source_refs"]


def test_gallery_artifact_placement_does_not_mutate_source_art():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    portrait_before = client.get(
        f"/api/v1/visual-memory/portraits/versions/{pv}"
    ).json()["portrait_version"]
    mem = _compile_memory(soul, pv)

    memory = _compile_world_memory(
        "event", mem["event_id"], memory_form="displayed_artwork"
    )
    client.post(
        f"/api/v1/world-memory/{memory['memory_id']}/placements",
        json={"placement_type": "gallery_collection", "placement_ref": "col_test"},
    )

    portrait_after = client.get(
        f"/api/v1/visual-memory/portraits/versions/{pv}"
    ).json()["portrait_version"]
    assert portrait_before == portrait_after


def test_rejected_visual_artifact_cannot_become_public_monument():
    guardian = get_world_memory_guardian()
    spec = WorldMemorySpec(
        subject_entity_type="event",
        subject_entity_id="evt_1",
        memory_form="monument_statue",
        interpretation_type="faithful",
        allowed_claims=["The battle was fought."],
        source_refs=[
            WorldMemorySourceRef(
                source_type="chronicle_painting",
                source_id="pnt_not_approved",
                claim_kind="canonical_fact",
            )
        ],
    )
    artifact = GeneratedWorldMemoryArtifact(
        title="A Monument",
        narrative="The battle was fought.",
        claims=["The battle was fought."],
        source_refs=list(spec.source_refs),
    )
    report = guardian.validate(artifact=artifact, spec=spec)
    assert report.status == "block"
    assert any(v["type"] == "unapproved_visual_reference" for v in report.violations)


def test_living_biography_source_remains_traceable():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv)
    bio = client.post(
        "/api/v1/biographies/compile", json={"soul_id": soul, "viewer_soul_id": soul}
    ).json()["biography"]
    approved = client.post(
        f"/api/v1/biographies/{bio['biography_id']}/approve?soul_id={soul}"
    ).json()["biography"]

    memory = _compile_world_memory("person", soul)

    assert any(r["source_type"] == "biography" for r in memory["source_refs"])
    after = client.get(
        f"/api/v1/biographies/{approved['biography_id']}?viewer_soul_id={soul}"
    ).json()["biography"]
    assert after["biography_id"] == approved["biography_id"]


def test_group_memory_perspective_remains_participant_specific():
    soul_a = f"Soul_{str(uuid.uuid4())[:6]}"
    soul_b = f"Soul_{str(uuid.uuid4())[:6]}"
    pv_a = _make_soul(soul_a)
    pv_b = _make_soul(soul_b)
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    _compile_memory(soul_a, pv_a, event_id=event_id)
    _compile_memory(soul_b, pv_b, event_id=event_id)

    group = client.post(
        "/api/v1/group-memories/auto-group", params={"event_id": event_id}
    ).json()["group_memory"]
    members_before = group["members"]

    memory = _compile_world_memory("event", event_id)

    group_after = client.get(f"/api/v1/group-memories/{group['group_id']}").json()[
        "group_memory"
    ]
    assert group_after["members"] == members_before
    assert len(memory["source_refs"]) >= 2


def test_cross_aspect_echo_does_not_force_metaphysical_interpretation():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    _compile_memory(soul, pv, importance_tier="world", importance_score=9)

    memory = _compile_world_memory("person", soul, interpretation_type="symbolic")

    assert memory["interpretation_type"] == "symbolic"
    assert any(d["deviation_kind"] == "reinterpretation" for d in memory["deviations"])
    assert "metaphysical" not in memory


def test_mock_generation_is_deterministic_and_offline():
    provider = get_world_memory_provider("mock")
    spec = WorldMemorySpec(
        subject_entity_type="event",
        subject_entity_id="evt_1",
        memory_form="legend",
        interpretation_type="faithful",
        allowed_claims=["Rowan defeated three giants."],
        source_refs=[
            WorldMemorySourceRef(source_type="memory_object", source_id="mo_1")
        ],
    )
    first = provider.generate(spec)
    second = provider.generate(spec)
    assert first.model_dump() == second.model_dump()
    assert provider.PROVIDER == "mock"


def test_world_memory_guardian_supports_pass_retry_block():
    guardian = get_world_memory_guardian()

    spec = WorldMemorySpec(
        subject_entity_type="event",
        subject_entity_id="evt_1",
        memory_form="legend",
        interpretation_type="faithful",
        allowed_claims=["The gate held."],
        source_refs=[
            WorldMemorySourceRef(source_type="memory_object", source_id="mo_1")
        ],
    )

    passed = guardian.validate(
        artifact=GeneratedWorldMemoryArtifact(
            title="The Legend",
            narrative="The gate held.",
            claims=["The gate held."],
            source_refs=list(spec.source_refs),
        ),
        spec=spec,
    )
    assert passed.status == "pass"

    blocked = guardian.validate(
        artifact=GeneratedWorldMemoryArtifact(
            title="The Legend",
            narrative="Twelve giants fell.",
            claims=["Twelve giants fell."],
            source_refs=list(spec.source_refs),
        ),
        spec=spec,
    )
    assert blocked.status == "block"

    retried = guardian.validate(
        artifact=GeneratedWorldMemoryArtifact(
            title="The Legend",
            narrative="",
            claims=["The gate held."],
            source_refs=list(spec.source_refs),
        ),
        spec=spec,
    )
    assert retried.status == "retry"
