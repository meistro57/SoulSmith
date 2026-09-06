# backend/tests/test_world_gallery.py
import uuid

import pytest
from app import db
from app.main import app
from app.world_gallery import (
    conservative_alt_text,
    list_gallery_artifacts,
)
from fastapi.testclient import TestClient

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
        "relics_involved": ["Dormant Salt Bell"],
        "emotional_tone": "Tense awakening",
        "action_composition": "Kaelen channels starlight.",
        "lasting_consequence": "The Salt Bell awakened.",
        "privacy_consent_scope": "public_canon",
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory_object"]


def _approved_painting(soul_id: str, portrait_version_id: str) -> dict:
    mem = _compile_memory(soul_id, portrait_version_id)
    painting = client.post(
        "/api/v1/chronicle-paintings", json={"memory_object_id": mem["id"]}
    ).json()["painting"]
    generated = client.post(
        f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate"
    ).json()["painting"]
    approved = client.post(
        f"/api/v1/chronicle-paintings/{painting['painting_id']}/approve"
    ).json()["painting"]
    assert approved["status"] == "approved"
    assert generated["image_url"]
    return approved


def _set_consent(soul_id: str, allow_shared_gallery: bool) -> None:
    db.get_or_create_visual_consent_record(soul_id)
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visual_consent_settings SET allow_shared_gallery = ? WHERE soul_id = ?",
        (1 if allow_shared_gallery else 0, soul_id),
    )
    conn.commit()
    conn.close()


def test_gallery_returns_only_approved_public_paintings():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    approved = _approved_painting(soul, pv)

    # A candidate (unapproved) painting must not appear.
    mem = _compile_memory(soul, pv)
    candidate = client.post(
        "/api/v1/chronicle-paintings", json={"memory_object_id": mem["id"]}
    ).json()["painting"]

    artifacts = list_gallery_artifacts(viewer_soul_id=None, mode="chronicle")
    ids = {a.artifact_id for a in artifacts}
    assert approved["painting_id"] in ids
    assert candidate["painting_id"] not in ids


def test_quarantined_rejected_blocked_never_appear(monkeypatch):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = client.post(
        "/api/v1/chronicle-paintings", json={"memory_object_id": mem["id"]}
    ).json()["painting"]
    blocked = client.post(
        f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate"
    ).json()["painting"]
    assert blocked["guardian_status"] == "blocked"

    artifacts = list_gallery_artifacts(viewer_soul_id=None, mode="chronicle")
    assert painting["painting_id"] not in {a.artifact_id for a in artifacts}


def test_private_portrait_not_leak_into_public_gallery():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    _make_soul(soul)
    _set_consent(soul, allow_shared_gallery=False)

    # Public (anonymous) viewer sees nothing for this soul.
    artifacts = list_gallery_artifacts(viewer_soul_id=None, mode="people")
    assert all(a.entity_id != soul for a in artifacts)

    # The soul themselves still sees their own portrait history.
    own = list_gallery_artifacts(viewer_soul_id=soul, mode="people")
    assert any(a.entity_id == soul for a in own)


def test_timeline_preserves_immutable_visual_history():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    _make_soul(soul)
    client.post(
        "/api/v1/visual/portraits/snapshot",
        json={"soul_id": soul, "label": "v2", "image_url": "/assets/portraits/v2.png"},
    )
    res = client.get(f"/api/v1/gallery/timeline?entity_type=portrait&entity_id={soul}")
    assert res.status_code == 200
    versions = res.json()["artifacts"]
    labels = [v["chronology_label"] for v in versions]
    assert "v1" in labels
    assert "v2" in labels
    assert len(versions) == 2


def test_collections_reference_artifacts_without_mutating_source():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    before = client.get(f"/api/v1/visual-memory/portraits/versions/{pv}").json()[
        "portrait_version"
    ]

    collection = client.post(
        "/api/v1/gallery/collections",
        json={"title": "Relics of the First Era"},
    ).json()["collection"]

    item = client.post(
        f"/api/v1/gallery/collections/{collection['collection_id']}/items",
        json={"artifact_type": "portrait", "artifact_ref": pv, "caption": "v1"},
    ).json()["item"]
    assert item["artifact_ref"] == pv

    reordered = client.post(
        f"/api/v1/gallery/collections/{collection['collection_id']}/reorder",
        json={"ordered_item_ids": [item["item_id"]]},
    ).json()["collection"]
    assert len(reordered["items"]) == 1

    after = client.get(f"/api/v1/visual-memory/portraits/versions/{pv}").json()[
        "portrait_version"
    ]
    assert before == after


def test_reorder_does_not_alter_canon(monkeypatch):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "pass")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before_mem = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    collection = client.post(
        "/api/v1/gallery/collections", json={"title": "Memories"}
    ).json()["collection"]
    client.post(
        f"/api/v1/gallery/collections/{collection['collection_id']}/items",
        json={"artifact_type": "chronicle_painting", "artifact_ref": "pnt_fake"},
    )
    client.post(
        f"/api/v1/gallery/collections/{collection['collection_id']}/reorder",
        json={"ordered_item_ids": []},
    )

    after_mem = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert before_mem["event_id"] == after_mem["event_id"]
    assert before_mem["event_title"] == after_mem["event_title"]


def test_conservative_alt_text_has_no_unsupported_facts():
    alt = conservative_alt_text("portrait", "Kaelen the Star-Watcher — v1", "v1")
    assert "Kaelen the Star-Watcher" in alt
    assert "scar" not in alt
    assert "left cheek" not in alt


def test_biography_life_mode_surfaces_approved_illustration(monkeypatch):
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    approved = _approved_painting(soul, pv)

    fake_biography = {
        "biography_id": "bio_test",
        "soul_id": soul,
        "status": "current",
        "sections": [
            {
                "section_id": "sec_1",
                "title": "The Salt Spire Awakening",
                "provenance": [
                    {
                        "source_type": "chronicle_painting",
                        "source_id": approved["painting_id"],
                        "claim_kind": "canonical_fact",
                        "note": None,
                    }
                ],
            }
        ],
    }
    monkeypatch.setattr(
        "app.db.get_current_biography_record",
        lambda soul_id: fake_biography,
    )
    artifacts = list_gallery_artifacts(viewer_soul_id=soul, mode="life", entity_id=soul)
    assert any(a.image_url == approved["image_url"] for a in artifacts)
