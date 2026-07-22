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


def test_phase_10_portrait_candidate_generation_and_continuity_workflow():
    soul_id = f"Phase10_Soul_{str(uuid.uuid4())[:6]}"

    # 1. Initialize identity
    client.post(
        "/api/v1/visual/avatar/create",
        json={
            "soul_id": soul_id,
            "face": "Defined features, sharp jawline",
            "hair": "Dark raven hair tied back",
            "body": "Athletic build",
            "species": "Human Aspect",
            "eyes": "Deep amber eyes",
        },
    )

    # 2. Compile prompt preview without saving candidate
    compile_prompt_res = client.post(
        "/api/v1/visual-memory/portraits/compile",
        json={
            "soul_id": soul_id,
            "generation_type": "initial",
            "emotional_state": "focused",
        },
    )
    assert compile_prompt_res.status_code == 200
    compiled_data = compile_prompt_res.json()
    assert "Preserve facial structure" in compiled_data["continuity_requirements"][0]

    # 3. Create initial candidate
    cand1_res = client.post(
        "/api/v1/visual-memory/portraits/candidates",
        json={
            "soul_id": soul_id,
            "generation_type": "initial",
            "emotional_state": "focused",
        },
    )
    assert cand1_res.status_code == 200
    cand1 = cand1_res.json()["candidate"]
    cand1_id = cand1["candidate_id"]
    assert cand1["status"] == "pending"

    # 4. Generate candidate imagery using mock provider
    gen1_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand1_id}/generate",
        json={"seed": 42},
    )
    assert gen1_res.status_code == 200
    gen1_cand = gen1_res.json()["candidate"]
    assert gen1_cand["status"] == "generated"
    assert gen1_cand["generated_image_url"] is not None

    # 5. Approve candidate 1 into canonical PortraitVersion 1
    app1_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand1_id}/approve",
        json={"soul_id": soul_id, "label": "Initial Baseline (v1)"},
    )
    assert app1_res.status_code == 200
    pv1 = app1_res.json()["portrait_version"]
    assert pv1["version_number"] == 1
    assert len(pv1["story_marks_snapshot"]) == 0
    pv1_id = pv1["version_id"]

    # 6. Test idempotency of approval
    idempotent_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand1_id}/approve",
        json={"soul_id": soul_id},
    )
    assert idempotent_res.status_code == 200
    assert idempotent_res.json()["portrait_version"]["version_id"] == pv1_id

    # 7. Record a Chronicle Event + Story Mark (Scar from "The Glass Observatory Collapse")
    client.post(
        "/api/v1/visual/story-marks/add",
        json={
            "soul_id": soul_id,
            "mark_type": "scar",
            "location": "left_cheek",
            "origin_event_id": "evt_glass_observatory_01",
            "acquired_at": "Year 3, Frostwane",
            "visibility": "prominent",
            "status": "permanent",
        },
    )

    # 8. Create updated candidate (referencing pv1 baseline and including the scar)
    cand2_res = client.post(
        "/api/v1/visual-memory/portraits/candidates",
        json={
            "soul_id": soul_id,
            "source_portrait_version_id": pv1_id,
            "generation_type": "story_mark_update",
            "emotional_state": "resolute",
        },
    )
    assert cand2_res.status_code == 200
    cand2_id = cand2_res.json()["candidate"]["candidate_id"]

    # Generate imagery for candidate 2
    client.post(f"/api/v1/visual-memory/portraits/candidates/{cand2_id}/generate")

    # Approve candidate 2 into PortraitVersion 2
    app2_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand2_id}/approve",
        json={"soul_id": soul_id, "label": "Post-Observatory Scar (v2)"},
    )
    assert app2_res.status_code == 200
    pv2 = app2_res.json()["portrait_version"]
    assert pv2["version_number"] == 2
    assert len(pv2["story_marks_snapshot"]) == 1
    assert pv2["story_marks_snapshot"][0]["mark_type"] == "scar"

    # 9. Verify Version 1 remains unchanged in history
    v1_check = client.get(f"/api/v1/visual-memory/portraits/versions/{pv1_id}").json()[
        "portrait_version"
    ]
    assert len(v1_check["story_marks_snapshot"]) == 0

    # 10. Rejection workflow: Create a candidate, reject it, verify it does not enter canon
    cand3_res = client.post(
        "/api/v1/visual-memory/portraits/candidates",
        json={"soul_id": soul_id, "generation_type": "manual_regeneration"},
    )
    cand3_id = cand3_res.json()["candidate"]["candidate_id"]

    client.post(f"/api/v1/visual-memory/portraits/candidates/{cand3_id}/generate")

    rej_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand3_id}/reject",
        json={"soul_id": soul_id, "reason": "Style did not match expectation"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["candidate"]["status"] == "rejected"

    # Attempting to approve a rejected candidate must fail with HTTP 400
    app_rejected_res = client.post(
        f"/api/v1/visual-memory/portraits/candidates/{cand3_id}/approve",
        json={"soul_id": soul_id},
    )
    assert app_rejected_res.status_code == 400

    # 11. Verify 404 for unknown candidate
    assert (
        client.get("/api/v1/visual-memory/portraits/candidates/unknown_id").status_code
        == 404
    )
