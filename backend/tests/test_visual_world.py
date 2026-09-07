# backend/tests/test_visual_world.py
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_location_candidate(soul_prefix, state, **extra):
    return client.post(
        "/api/v1/visual-world/candidates",
        json={
            "entity_type": "location",
            "entity_id": soul_prefix,
            "name": "The Hall of Echoes",
            "canonical_state": state,
            **extra,
        },
    )


def test_location_visual_lifecycle_and_historical_integrity():
    entity_id = f"loc_{str(uuid.uuid4())[:8]}"
    v1_state = {
        "architecture": "vast subterranean limestone hall",
        "landmarks": ["seven black arches", "central dais"],
        "damage_state": "intact",
    }

    # 1. Create initial candidate.
    create = _create_location_candidate(entity_id, v1_state, generation_type="initial")
    assert create.status_code == 200
    cand1 = create.json()["candidate"]
    assert cand1["workflow_role"] == "environment_initial"
    assert cand1["canonical_snapshot"]["damage_state"] == "intact"
    assert cand1["status"] == "pending"

    # 2. Generate (mock provider).
    gen = client.post(
        f"/api/v1/visual-world/candidates/{cand1['candidate_id']}/generate", json={}
    )
    assert gen.status_code == 200
    assert gen.json()["candidate"]["status"] == "generated"
    v1_image_url = gen.json()["candidate"]["generated_image_url"]

    # 3. Approve -> immutable v1.
    appr = client.post(
        f"/api/v1/visual-world/candidates/{cand1['candidate_id']}/approve"
    )
    assert appr.status_code == 200
    v1 = appr.json()["visual_version"]
    assert v1["version_number"] == 1
    assert v1["canonical_snapshot"]["damage_state"] == "intact"
    assert v1["image_url"] == v1_image_url

    # 4. Canonical update -> damage_update with source v1.
    v2_state = {**v1_state, "damage_state": "western arch cracked"}
    create2 = _create_location_candidate(
        entity_id,
        v2_state,
        generation_type="damage_update",
        source_visual_version_id=v1["version_id"],
    )
    assert create2.status_code == 200
    cand2 = create2.json()["candidate"]
    assert cand2["workflow_role"] == "environment_reference"
    assert cand2["reference_image_url"] == v1["image_url"]
    assert cand2["source_visual_version_id"] == v1["version_id"]
    assert any("damage_state" in c for c in cand2["canonical_delta"]["change"])

    # 5. Approve v2.
    gen2 = client.post(
        f"/api/v1/visual-world/candidates/{cand2['candidate_id']}/generate", json={}
    )
    assert gen2.status_code == 200
    appr2 = client.post(
        f"/api/v1/visual-world/candidates/{cand2['candidate_id']}/approve"
    )
    assert appr2.status_code == 200
    v2 = appr2.json()["visual_version"]
    assert v2["version_number"] == 2

    # 6. Historical integrity: v1 unchanged.
    versions = client.get(f"/api/v1/visual-world/location/{entity_id}/versions").json()[
        "versions"
    ]
    assert len(versions) == 2
    assert versions[0]["canonical_snapshot"]["damage_state"] == "intact"
    assert versions[0]["version_id"] == v1["version_id"]
    assert versions[1]["canonical_snapshot"]["damage_state"] == "western arch cracked"


def test_world_candidate_reject_and_wrong_source():
    entity_id = f"loc_{str(uuid.uuid4())[:8]}"
    create = _create_location_candidate(
        entity_id, {"architecture": "hall"}, generation_type="initial"
    )
    cand_id = create.json()["candidate"]["candidate_id"]

    gen = client.post(f"/api/v1/visual-world/candidates/{cand_id}/generate", json={})
    assert gen.status_code == 200

    # Wrong-entity source must be rejected.
    bad = client.post(
        "/api/v1/visual-world/candidates",
        json={
            "entity_type": "location",
            "entity_id": entity_id,
            "name": "Other",
            "canonical_state": {"architecture": "x"},
            "generation_type": "damage_update",
            "source_visual_version_id": "wvv_1_deadbeef",
        },
    )
    assert bad.status_code == 404

    # Reject flow.
    rej = client.post(f"/api/v1/visual-world/candidates/{cand_id}/reject")
    assert rej.status_code == 200
    assert rej.json()["candidate"]["status"] == "rejected"


def test_relic_and_phenomenon_candidate_creation():
    relic = client.post(
        "/api/v1/visual-world/candidates",
        json={
            "entity_type": "relic",
            "entity_id": "relic_salt_bell",
            "name": "Salt Bell",
            "canonical_state": {"object_type": "bell", "energy_state": "Dormant"},
            "generation_type": "initial",
        },
    )
    assert relic.status_code == 200
    assert relic.json()["candidate"]["workflow_role"] == "object_initial"

    phen = client.post(
        "/api/v1/visual-world/candidates",
        json={
            "entity_type": "phenomenon",
            "entity_id": "phen_veil",
            "name": "Veil of the Forgotten Name",
            "canonical_state": {"typology": "Veil", "escalation_stage": 3},
            "generation_type": "initial",
        },
    )
    assert phen.status_code == 200
    assert phen.json()["candidate"]["workflow_role"] == "environment_initial"
