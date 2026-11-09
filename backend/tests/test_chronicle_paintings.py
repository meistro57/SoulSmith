# backend/tests/test_chronicle_paintings.py
import uuid

import pytest
from app import db
from app.chronicle_paintings import SceneSpecModel
from app.comfyui.storage import ChronicleImageStore
from app.main import app
from app.painting_pipeline import generate_chronicle_painting
from app.painting_provider import (
    MockPaintingImageProvider,
    PaintingGenerationRequest,
    PaintingGenerationResult,
    get_painting_provider,
)
from app.painting_reference import (
    ParticipantResolutionError,
    resolve_historical_participants,
)
from app.visual_canon_guardian import MockVisualCanonGuardian
from app.visual_memory import MemoryObjectModel, ParticipantRefModel
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
                "character_name": "Kaelen",
                "portrait_version_id": portrait_version_id,
                "role_in_event": "Focus",
                "real_person_tag_opt_in": False,
            }
        ],
        "location_environment": "Salt-encrusted subterranean sanctuary",
        "relics_involved": ["Dormant Salt Bell"],
        "emotional_tone": "Tense awakening, solemn reverence",
        "action_composition": "Kaelen channels starlight to anchor the altar.",
        "lasting_consequence": "The Salt Bell awakened.",
        "privacy_consent_scope": "public_canon",
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200
    return res.json()["memory_object"]


def _create_painting(memory_object_id: str, **extra) -> dict:
    payload = {"memory_object_id": memory_object_id, **extra}
    res = client.post("/api/v1/chronicle-paintings", json=payload)
    assert res.status_code == 200
    return res.json()["painting"]


def test_painting_creation_from_memory_object():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    painting = _create_painting(mem["id"])
    assert painting["memory_object_id"] == mem["id"]
    assert painting["status"] == "candidate"
    assert painting["guardian_status"] == "pending"
    assert painting["compiled_prompt"]
    assert "PARTICIPANTS" in painting["compiled_prompt"]
    assert painting["scene_spec"]["event_id"] == mem["event_id"]
    assert painting["historical_participant_refs"][0]["portrait_version_id"] == pv


def test_memory_object_remains_unchanged_after_painting():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    before = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]

    _create_painting(mem["id"])
    # Generate to completion.
    painting = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")

    after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    # Canonical fields unchanged.
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


def test_historical_portrait_selected_instead_of_newest():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv1 = _make_soul(soul)
    # Create a newer portrait (v2) so v1 is no longer the newest.
    client.post(
        "/api/v1/visual/story-marks/add",
        json={
            "soul_id": soul,
            "mark_type": "scar",
            "location": "left_cheek",
            "origin_event_id": "evt_x",
            "acquired_at": "Year 3",
        },
    )
    v2 = client.post(
        "/api/v1/visual/portraits/snapshot",
        json={"soul_id": soul, "label": "v2", "image_url": "/assets/portraits/v2.png"},
    ).json()["portrait"]

    mem = _compile_memory(soul, pv1)  # references the historical v1
    painting = _create_painting(mem["id"])
    refs = painting["historical_participant_refs"]
    assert refs[0]["portrait_version_id"] == pv1
    assert refs[0]["portrait_version_id"] != v2["version_id"]


def test_invalid_historical_portrait_link_rejected_safely():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    mem = MemoryObjectModel(
        id="mem_x",
        event_id="evt_x",
        event_title="Broken",
        participants=[
            ParticipantRefModel(
                soul_id=soul,
                character_name="Ghost",
                portrait_version_id="pv_unknown_000",
                role_in_event="Witness",
            )
        ],
        location_environment="hall",
        emotional_tone="quiet",
        action_composition="none",
        lasting_consequence="none",
    )
    with pytest.raises(ParticipantResolutionError, match="unknown portrait version"):
        resolve_historical_participants(mem)


def test_guardian_pass_allows_player_visible_candidate():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])

    res = client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")
    assert res.status_code == 200
    result = res.json()["painting"]
    assert result["guardian_status"] == "passed"
    assert result["status"] == "candidate"
    assert result["image_url"]
    assert result["image_url"].startswith("/assets/chronicle/paintings/")
    assert result["quarantined_image_url"].startswith("/assets/chronicle/quarantine/")


def test_guardian_retry_prevents_exposure_and_tracks_source(
    monkeypatch,
):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "retry")
    monkeypatch.setenv("SOULSMITH_CHRONICLE_MAX_RETRIES", "2")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])

    res = client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")
    result = res.json()["painting"]
    # Final result is blocked after retries exhausted; never player-visible.
    assert result["image_url"] is None
    assert result["status"] == "failed"

    history = client.get(
        f"/api/v1/chronicle-paintings?memory_object_id={mem['id']}"
    ).json()["paintings"]
    assert len(history) == 3  # initial + 2 retries
    retries = [p for p in history if p["generation_type"] == "retry"]
    assert len(retries) == 2
    assert retries[0]["source_painting_id"] == painting["painting_id"]
    assert retries[0]["memory_object_id"] == mem["id"]
    assert all(p["image_url"] is None for p in history)


def test_guardian_block_prevents_exposure(monkeypatch):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])

    res = client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")
    result = res.json()["painting"]
    assert result["guardian_status"] == "blocked"
    assert result["status"] == "failed"
    assert result["image_url"] is None
    assert result["quarantined_image_url"].startswith("/assets/chronicle/quarantine/")


def test_quarantined_images_never_returned_as_player_assets(monkeypatch):
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")

    result = client.get(
        f"/api/v1/chronicle-paintings/{painting['painting_id']}"
    ).json()["painting"]
    assert result["image_url"] is None
    store = ChronicleImageStore()
    assert store.is_quarantined_url(result["quarantined_image_url"])
    assert not store.is_promoted_url(result["quarantined_image_url"])
    # Gallery must not contain it.
    gallery = client.get("/api/v1/chronicle-paintings/gallery").json()["paintings"]
    assert all(p["painting_id"] != painting["painting_id"] for p in gallery)


def test_guardian_report_persists():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")

    reports = db.get_chronicle_painting_guardian_reports(painting["painting_id"])
    assert len(reports) == 1
    assert reports[0]["status"] == "pass"
    assert reports[0]["painting_id"] == painting["painting_id"]


def test_candidate_approval_and_second_approval_supersedes_first():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    p1 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/generate")
    appr1 = client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/approve")
    assert appr1.status_code == 200
    assert appr1.json()["painting"]["status"] == "approved"

    # Memory object points at the first painting.
    mem_after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    assert mem_after["visual_generation_status"] == "painting_approved"
    assert mem_after["painting_image_url"].startswith("/assets/chronicle/paintings/")

    p2 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p2['painting_id']}/generate")
    appr2 = client.post(f"/api/v1/chronicle-paintings/{p2['painting_id']}/approve")
    assert appr2.json()["painting"]["status"] == "approved"

    # First is superseded, not deleted.
    p1_after = client.get(f"/api/v1/chronicle-paintings/{p1['painting_id']}").json()[
        "painting"
    ]
    assert p1_after["status"] == "superseded"

    gallery = client.get("/api/v1/chronicle-paintings/gallery").json()["paintings"]
    ids = [p["painting_id"] for p in gallery]
    assert p2["painting_id"] in ids
    assert p1["painting_id"] not in ids


def test_rejection_remains_auditable():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")

    res = client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/reject")
    assert res.status_code == 200
    assert res.json()["painting"]["status"] == "rejected"

    history = client.get(
        f"/api/v1/chronicle-paintings?memory_object_id={mem['id']}"
    ).json()["paintings"]
    assert any(
        p["painting_id"] == painting["painting_id"] and p["status"] == "rejected"
        for p in history
    )


def test_failed_review_leaves_approved_painting_untouched(monkeypatch):
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)

    p1 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/generate")
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/approve")

    # Now force a block on a second painting.
    monkeypatch.setenv("SOULSMITH_MOCK_GUARDIAN_VERDICT", "block")
    p2 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p2['painting_id']}/generate")

    mem_after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    p1_after = client.get(f"/api/v1/chronicle-paintings/{p1['painting_id']}").json()[
        "painting"
    ]
    assert p1_after["status"] == "approved"
    assert mem_after["painting_image_url"] == p1_after["image_url"]


def test_provider_capability_reporting():
    caps = get_painting_provider("mock").capabilities()
    assert caps.provider == "mock"
    assert caps.text_to_image is True
    assert caps.multiple_references is False
    assert caps.identity_conditioning is False
    assert caps.deterministic_seed is True


def test_missing_references_use_non_identifying_strategy():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    mem = MemoryObjectModel(
        id="mem_y",
        event_id="evt_y",
        event_title="Forgotten witness",
        participants=[
            ParticipantRefModel(
                soul_id=soul,
                character_name="Unknown",
                portrait_version_id="",  # no canonical appearance
                role_in_event="Witness",
            )
        ],
        location_environment="hall",
        emotional_tone="quiet",
        action_composition="a figure turns away",
        lasting_consequence="none",
    )
    resolved = resolve_historical_participants(mem)
    assert resolved[0].identity_strategy == "silhouette"
    assert resolved[0].portrait_image_url is None


def test_stable_soulsmith_asset_url_and_no_comfyui_view_url():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    painting = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{painting['painting_id']}/generate")

    result = client.get(
        f"/api/v1/chronicle-paintings/{painting['painting_id']}"
    ).json()["painting"]
    assert result["image_url"].startswith("/assets/chronicle/paintings/")
    assert "/view" not in result["image_url"]
    assert "comfyui" not in result["image_url"].lower()


def test_gallery_returns_approved_public_paintings_only():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    p1 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/generate")
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/approve")

    gallery = client.get("/api/v1/chronicle-paintings/gallery").json()["paintings"]
    assert any(p["painting_id"] == p1["painting_id"] for p in gallery)
    assert all(p["status"] == "approved" and p["image_url"] for p in gallery)
    # Useful memory metadata present.
    assert gallery[0]["memory_event_title"] == mem["event_title"]


def test_gallery_excludes_private_canon_memory():
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv, privacy_consent_scope="private_canon")
    p1 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/generate")
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/approve")

    gallery = client.get("/api/v1/chronicle-paintings/gallery").json()["paintings"]
    assert all(p["painting_id"] != p1["painting_id"] for p in gallery)


def test_generation_failure_leaves_approved_painting_untouched(monkeypatch):
    soul = f"Soul_{str(uuid.uuid4())[:6]}"
    pv = _make_soul(soul)
    mem = _compile_memory(soul, pv)
    p1 = _create_painting(mem["id"])
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/generate")
    client.post(f"/api/v1/chronicle-paintings/{p1['painting_id']}/approve")

    p2 = _create_painting(mem["id"])

    class FailingProvider:
        def generate(self, request):
            return PaintingGenerationResult(
                success=False, provider="mock", failure_reason="provider down"
            )

        def capabilities(self):
            return MockPaintingImageProvider().capabilities()

    monkeypatch.setattr(
        "app.painting_pipeline.get_painting_provider",
        lambda provider_type=None: FailingProvider(),
    )
    mem_obj = MemoryObjectModel(
        **client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
            "memory_object"
        ]
    )
    result = generate_chronicle_painting(p2["painting_id"], mem_obj)
    assert result.status == "failed"

    mem_after = client.get(f"/api/v1/visual/memory-objects/{mem['id']}").json()[
        "memory_object"
    ]
    p1_after = client.get(f"/api/v1/chronicle-paintings/{p1['painting_id']}").json()[
        "painting"
    ]
    assert p1_after["status"] == "approved"
    assert mem_after["painting_image_url"] == p1_after["image_url"]


def test_mock_guardian_direct_pass_retry_block():
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
    assert (
        MockVisualCanonGuardian()
        .inspect(
            image_bytes=b"png", memory_object=mem, scene_spec=spec, provider="mock"
        )
        .status
        == "pass"
    )
    assert (
        MockVisualCanonGuardian("retry")
        .inspect(
            image_bytes=b"png", memory_object=mem, scene_spec=spec, provider="mock"
        )
        .status
        == "retry"
    )
    assert (
        MockVisualCanonGuardian("block")
        .inspect(
            image_bytes=b"png", memory_object=mem, scene_spec=spec, provider="mock"
        )
        .status
        == "block"
    )


def test_mock_provider_deterministic_bytes():
    provider = MockPaintingImageProvider()
    req = PaintingGenerationRequest(
        painting_id="pnt_x", memory_object_id="mem_x", compiled_prompt="x", seed=7
    )
    a = provider.generate(req)
    b = provider.generate(req)
    assert a.image_bytes == b.image_bytes
    assert a.success is True
