# backend/tests/test_group_memories.py
import uuid

import pytest
from app import db
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    """Keep mock painting bytes out of the real backend/assets directory."""
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
                "character_name": soul_id,
                "portrait_version_id": portrait_version_id,
                "role_in_event": "Focus",
                "real_person_tag_opt_in": False,
            }
        ],
        "location_environment": "Salt-encrusted subterranean sanctuary",
        "relics_involved": ["Dormant Salt Bell"],
        "emotional_tone": "Tense awakening, solemn reverence",
        "action_composition": "The seeker channels starlight to anchor the altar.",
        "lasting_consequence": "The Salt Bell awakened.",
        "privacy_consent_scope": "public_canon",
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200
    return res.json()["memory_object"]


def _auto_group(event_id: str) -> dict:
    res = client.post(
        "/api/v1/group-memories/auto-group", params={"event_id": event_id}
    )
    assert res.status_code == 200
    return res.json()


def test_multiple_memory_objects_link_to_one_group_memory():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    b = _compile_memory(soul_b, _make_soul(soul_b), event_id=event_id)

    group = _auto_group(event_id)["group_memory"]
    assert group["event_id"] == event_id
    member_ids = {m["memory_object_id"] for m in group["members"]}
    assert a["id"] in member_ids
    assert b["id"] in member_ids
    assert len(group["members"]) == 2


def test_participant_memory_objects_remain_unchanged():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    before = client.get(f"/api/v1/visual/memory-objects/{a['id']}").json()[
        "memory_object"
    ]

    _auto_group(event_id)

    after = client.get(f"/api/v1/visual/memory-objects/{a['id']}").json()[
        "memory_object"
    ]
    for key in (
        "event_id",
        "event_title",
        "participants",
        "location_environment",
        "relics_involved",
        "emotional_tone",
        "action_composition",
        "lasting_consequence",
    ):
        assert before[key] == after[key]


def test_exact_shared_event_id_groups_safely():
    shared = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    soul_c = f"SoulC_{str(uuid.uuid4())[:6]}"
    _compile_memory(soul_a, _make_soul(soul_a), event_id=shared)
    _compile_memory(soul_b, _make_soul(soul_b), event_id=shared)
    # A different event with the same title must NOT join the group.
    _compile_memory(
        soul_c,
        _make_soul(soul_c),
        event_id=f"evt_{str(uuid.uuid4())[:8]}",
        event_title="The Salt Spire Awakening",
    )

    group = _auto_group(shared)["group_memory"]
    assert len(group["members"]) == 2


def test_semantic_similarity_alone_does_not_assert_equivalence():
    title = "The Last Warm Fire"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(
        soul_a,
        _make_soul(soul_a),
        event_id=f"evt_{str(uuid.uuid4())[:8]}",
        event_title=title,
    )
    _compile_memory(
        soul_b,
        _make_soul(soul_b),
        event_id=f"evt_{str(uuid.uuid4())[:8]}",
        event_title=title,
    )

    # Similarity produces suggestions, never canonical grouping.
    res = client.get(f"/api/v1/group-memories/suggestions/{a['id']}")
    assert res.status_code == 200
    suggestions = res.json()["suggestions"]
    assert any(s["canonical"] is False for s in suggestions)


def test_different_participant_perspectives_are_preserved():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    _compile_memory(
        soul_a, _make_soul(soul_a), event_id=event_id, emotional_tone="Fear"
    )
    _compile_memory(
        soul_b, _make_soul(soul_b), event_id=event_id, emotional_tone="Triumph"
    )

    group = _auto_group(event_id)["group_memory"]
    perspectives = client.get(
        f"/api/v1/group-memories/{group['group_id']}/perspectives",
        params={"viewer_soul_id": None},
    ).json()
    tones = {p["emotional_tone"] for p in perspectives["perspectives"]}
    assert "Fear" in tones
    assert "Triumph" in tones


def test_conflicting_recollections_remain_distinct():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    _compile_memory(
        soul_a,
        _make_soul(soul_a),
        event_id=event_id,
        lasting_consequence="The door closed forever.",
    )
    _compile_memory(
        soul_b,
        _make_soul(soul_b),
        event_id=event_id,
        lasting_consequence="The way reopened.",
    )

    group = _auto_group(event_id)["group_memory"]
    comparison = client.get(
        f"/api/v1/group-memories/{group['group_id']}/perspectives"
    ).json()
    disagree_fields = {d["field"] for d in comparison["disagreements"]}
    assert "lasting_consequence" in disagree_fields


def test_shared_facts_do_not_overwrite_participant_facts():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(
        soul_a,
        _make_soul(soul_a),
        event_id=event_id,
        location_environment="The Salt Hall",
        lasting_consequence="A private wound.",
    )
    _compile_memory(
        soul_b,
        _make_soul(soul_b),
        event_id=event_id,
        location_environment="The Salt Hall",
        lasting_consequence="A public victory.",
    )

    _auto_group(event_id)
    after = client.get(f"/api/v1/visual/memory-objects/{a['id']}").json()[
        "memory_object"
    ]
    assert after["lasting_consequence"] == "A private wound."


def test_structured_tags_and_anchors_query_related_memories():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    group = _auto_group(event_id)["group_memory"]

    client.post(
        f"/api/v1/group-memories/{group['group_id']}/tags",
        json={"tag_type": "recurring_motif", "value": "closed_doors"},
    )
    related = client.get(
        "/api/v1/group-memories/related",
        params={"tag_type": "recurring_motif", "tag_value": "closed_doors"},
    ).json()
    ids = [g["group_id"] for g in related["group_memories"]]
    assert group["group_id"] in ids


def test_anchor_retains_historical_visual_version_reference():
    entity_id = f"loc_{str(uuid.uuid4())[:8]}"
    create = client.post(
        "/api/v1/visual-world/candidates",
        json={
            "entity_type": "location",
            "entity_id": entity_id,
            "name": "The Hall of Echoes",
            "canonical_state": {"architecture": "limestone hall"},
        },
    )
    cand = create.json()["candidate"]
    client.post(f"/api/v1/visual-world/candidates/{cand['candidate_id']}/generate")
    approved = client.post(
        f"/api/v1/visual-world/candidates/{cand['candidate_id']}/approve"
    ).json()["visual_version"]

    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    group = _auto_group(event_id)["group_memory"]

    res = client.post(
        f"/api/v1/group-memories/{group['group_id']}/anchors",
        json={
            "anchor_type": "location",
            "anchor_ref": approved["version_id"],
        },
    )
    assert res.status_code == 200
    anchor = res.json()["anchor"]
    assert anchor["anchor_ref"] == approved["version_id"]
    assert anchor["entity_id"] == entity_id

    anchors = client.get(f"/api/v1/group-memories/{group['group_id']}/anchors").json()[
        "anchors"
    ]
    assert any(a["anchor_ref"] == approved["version_id"] for a in anchors)


def test_removing_link_does_not_delete_memory_object():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    group = _auto_group(event_id)["group_memory"]

    res = client.delete(f"/api/v1/group-memories/{group['group_id']}/members/{a['id']}")
    assert res.status_code == 200
    assert res.json()["memory_object_still_exists"] is True
    still = client.get(f"/api/v1/visual/memory-objects/{a['id']}")
    assert still.status_code == 200


def test_participant_specific_consent_filtering():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)
    _compile_memory(soul_b, _make_soul(soul_b), event_id=event_id)

    # Soul B revokes shared gallery consent.
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visual_consent_settings SET allow_shared_gallery = 0 WHERE soul_id = ?",
        (soul_b,),
    )
    conn.commit()
    conn.close()

    group = _auto_group(event_id)["group_memory"]

    # Anonymous viewer sees only the public participant.
    public_view = client.get(f"/api/v1/group-memories/{group['group_id']}").json()[
        "group_memory"
    ]
    assert all(m["soul_id"] != soul_b for m in public_view["members"])

    # Soul B themselves still sees their own memory.
    self_view = client.get(
        f"/api/v1/group-memories/{group['group_id']}",
        params={"viewer_soul_id": soul_b},
    ).json()["group_memory"]
    assert any(m["soul_id"] == soul_b for m in self_view["members"])


def test_public_response_cannot_leak_private_participant_identity():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_private = f"PrivateSoul_{str(uuid.uuid4())[:6]}"
    soul_public = f"PublicSoul_{str(uuid.uuid4())[:6]}"
    _compile_memory(
        soul_private,
        _make_soul(soul_private),
        event_id=event_id,
        privacy_consent_scope="private_canon",
    )
    _compile_memory(soul_public, _make_soul(soul_public), event_id=event_id)

    group = _auto_group(event_id)["group_memory"]
    public_view = client.get(f"/api/v1/group-memories/{group['group_id']}").json()[
        "group_memory"
    ]
    souls = [m["soul_id"] for m in public_view["members"]]
    assert soul_private not in souls
    assert soul_public in souls


def test_private_emotional_details_cannot_leak_through_summary_or_tags():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_private = f"PrivateSoul_{str(uuid.uuid4())[:6]}"
    _compile_memory(
        soul_private,
        _make_soul(soul_private),
        event_id=event_id,
        privacy_consent_scope="private_canon",
        emotional_tone="Deep secret shame",
    )

    group = _auto_group(event_id)["group_memory"]
    public_view = client.get(f"/api/v1/group-memories/{group['group_id']}").json()[
        "group_memory"
    ]
    assert "shame" not in public_view["summary"].lower()
    assert "shame" not in public_view["title"].lower()
    assert all("shame" not in tag["value"].lower() for tag in public_view["tags"])


def test_group_significance_does_not_overwrite_individual_significance():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    soul_b = f"SoulB_{str(uuid.uuid4())[:6]}"
    a = _compile_memory(
        soul_a,
        _make_soul(soul_a),
        event_id=event_id,
        importance_tier="personal",
        importance_score=5,
    )
    _compile_memory(
        soul_b,
        _make_soul(soul_b),
        event_id=event_id,
        importance_tier="world",
        importance_score=9,
    )

    group = _auto_group(event_id)["group_memory"]
    assert group["group_significance"] in ("world", "legendary")

    after_a = client.get(f"/api/v1/visual/memory-objects/{a['id']}").json()[
        "memory_object"
    ]
    assert after_a["importance_tier"] == "personal"
    assert after_a["importance_score"] == 5


def test_approved_chronicle_painting_relationship_remains_valid():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    mem = _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)

    painting = client.post(
        "/api/v1/chronicle-paintings", json={"memory_object_id": mem["id"]}
    ).json()["painting"]
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/approve")

    group = _auto_group(event_id)["group_memory"]
    res = client.post(
        f"/api/v1/group-memories/{group['group_id']}/anchors",
        json={
            "anchor_type": "chronicle_painting",
            "anchor_ref": painting["painting_id"],
        },
    )
    assert res.status_code == 200
    anchor = res.json()["anchor"]
    assert anchor["anchor_ref"] == painting["painting_id"]

    # The painting remains art, not canon; the Memory Object is untouched.
    mem_after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert mem_after["visual_generation_status"] == "painting_approved"


def test_visual_canon_guardian_requirements_remain_intact(monkeypatch):
    from app.chronicle_paintings import SceneSpecModel
    from app.visual_canon_guardian import MockVisualCanonGuardian
    from app.visual_memory import MemoryObjectModel

    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    mem = MemoryObjectModel(
        id="mem_z",
        event_id="evt_z",
        event_title="x",
        participants=[],
        location_environment="hall",
        emotional_tone="quiet",
        action_composition="none",
        lasting_consequence="none",
    )
    spec = SceneSpecModel(
        event_title="x",
        event_id="evt_z",
        location="hall",
        environment="hall",
        participants=[],
        pose_action="none",
        emotional_tone="quiet",
        composition="environmental",
    )
    report = MockVisualCanonGuardian.from_env().inspect(
        image_bytes=b"png", memory_object=mem, scene_spec=spec, provider="mock"
    )
    assert report.status == "block"


def test_deterministic_mock_operation_requires_no_external_ai():
    event_id = f"evt_{str(uuid.uuid4())[:8]}"
    soul_a = f"SoulA_{str(uuid.uuid4())[:6]}"
    _compile_memory(soul_a, _make_soul(soul_a), event_id=event_id)

    # Auto-group is deterministic and offline.
    first = _auto_group(event_id)["group_memory"]
    second = client.post(
        "/api/v1/group-memories/auto-group", params={"event_id": event_id}
    ).json()["group_memory"]
    assert first["group_id"] == second["group_id"]
