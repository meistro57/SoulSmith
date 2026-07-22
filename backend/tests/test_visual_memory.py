# backend/tests/test_visual_memory.py
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_visual_identity_and_memory_object_flow():
    soul_id = f"Visual_Soul_{str(uuid.uuid4())[:6]}"

    # 1. Fetch visual avatar profile (auto-initializes default identity and v1 pre-scar portrait)
    prof_res = client.get(f"/api/v1/visual/avatar/{soul_id}")
    assert prof_res.status_code == 200
    profile = prof_res.json()
    assert profile["identity"]["soul_id"] == soul_id
    assert len(profile["portraits"]) == 1
    assert profile["portraits"][0]["version_number"] == 1
    v1_portrait_id = profile["portraits"][0]["version_id"]
    assert len(profile["portraits"][0]["story_marks_snapshot"]) == 0

    # 2. Record a story mark (scar) linked to a canonical event ID
    mark_res = client.post(
        "/api/v1/visual/story-marks/add",
        json={
            "soul_id": soul_id,
            "mark_type": "scar",
            "location": "left_cheek",
            "origin_event_id": "evt_salt_spire_01",
            "acquired_at": "Year 3, Frostwane",
            "visibility": "prominent",
            "status": "permanent",
        },
    )
    assert mark_res.status_code == 200
    mark = mark_res.json()["story_mark"]
    assert mark["mark_type"] == "scar"
    assert mark["origin_event_id"] == "evt_salt_spire_01"

    # 3. Snapshot a new portrait version (v2 post-scar portrait)
    snap_res = client.post(
        "/api/v1/visual/portraits/snapshot",
        json={
            "soul_id": soul_id,
            "label": "Post-Salt-Spire Scar (v2)",
            "image_url": "/assets/portraits/kaelen_v2_scar.png",
        },
    )
    assert snap_res.status_code == 200
    v2_portrait = snap_res.json()["portrait"]
    assert v2_portrait["version_number"] == 2
    assert len(v2_portrait["story_marks_snapshot"]) == 1
    assert v2_portrait["story_marks_snapshot"][0]["mark_type"] == "scar"

    # 4. Compile a Chronicle Event into a Memory Object using historical appearance locking
    # Event happened BEFORE scar was acquired -> links to v1_portrait_id (pre-scar)
    compile_res = client.post(
        "/api/v1/visual/memory-objects/compile",
        json={
            "event_id": "evt_salt_spire_01",
            "event_title": "Awakening of the Salt Spire",
            "participants": [
                {
                    "soul_id": soul_id,
                    "character_name": "Kaelen the Seeker",
                    "portrait_version_id": v1_portrait_id,  # Historical pre-scar portrait
                    "role_in_event": "Focus",
                    "real_person_tag_opt_in": False,
                },
                {
                    "soul_id": "Archivist Vael",
                    "character_name": "Archivist Vael",
                    "portrait_version_id": "pv_vael_1",
                    "role_in_event": "Witness",
                    "real_person_tag_opt_in": True,
                },
            ],
            "location_environment": "Salt-encrusted subterranean sanctuary",
            "relics_involved": ["Dormant Salt Bell"],
            "emotional_tone": "Tense awakening, solemn reverence",
            "action_composition": "Kaelen channels starlight while Vael anchors the physical altar.",
            "lasting_consequence": "Kaelen received a prominent scar on left cheek; Salt Bell awakened.",
            "privacy_consent_scope": "public_canon",
        },
    )
    assert compile_res.status_code == 200
    mem_obj = compile_res.json()["memory_object"]
    assert mem_obj["event_id"] == "evt_salt_spire_01"
    assert mem_obj["visual_generation_status"] == "compiled"
    assert mem_obj["participants"][0]["portrait_version_id"] == v1_portrait_id

    # 5. List compiled memory objects
    list_mem_res = client.get("/api/v1/visual/memory-objects")
    assert list_mem_res.status_code == 200
    mem_objects = list_mem_res.json()["memory_objects"]
    assert len(mem_objects) >= 1
