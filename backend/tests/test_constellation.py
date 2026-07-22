# backend/tests/test_constellation.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_constellation():
    response = client.get("/api/v1/constellation")
    assert response.status_code == 200
    data = response.json()
    assert "constellation" in data
    assert "stage_info" in data
    const = data["constellation"]
    assert "id" in const
    assert len(const["aspects"]) >= 2
    assert len(const["deep_threads"]) >= 1


def test_create_aspect_and_bond():
    # 1. Get primary constellation
    c_res = client.get("/api/v1/constellation")
    const_id = c_res.json()["constellation"]["id"]
    aspects = c_res.json()["constellation"]["aspects"]
    aspect1_id = aspects[0]["id"]

    # 2. Create a 3rd Aspect
    a_res = client.post(
        "/api/v1/constellation/aspects/create",
        json={
            "constellation_id": const_id,
            "aspect_name": "Seer Lyra of the Void",
            "calling": "Watcher of Unwritten Stars",
            "origin": "Threshold of the Outer Veils",
            "era_or_world": "Future Era (Age of Silence)",
        },
    )
    assert a_res.status_code == 200
    new_aspect = a_res.json()["aspect"]
    assert new_aspect["aspect_name"] == "Seer Lyra of the Void"

    # 3. Create a Cross-Aspect Bond
    b_res = client.post(
        "/api/v1/constellation/bonds/create",
        json={
            "constellation_id": const_id,
            "source_aspect_id": aspect1_id,
            "target_aspect_id": new_aspect["id"],
            "bond_type": "scar",
            "description": "Inherited the same singed mark across two millennia.",
        },
    )
    assert b_res.status_code == 200
    bond = b_res.json()["bond"]
    assert bond["bond_type"] == "scar"

    # 4. Check updated constellation
    updated_res = client.get("/api/v1/constellation")
    updated_const = updated_res.json()["constellation"]
    assert len(updated_const["aspects"]) >= 3


def test_advance_awakening_stage():
    c_res = client.get("/api/v1/constellation")
    const_id = c_res.json()["constellation"]["id"]

    adv_res = client.post(
        "/api/v1/constellation/advance",
        json={
            "constellation_id": const_id,
            "target_stage": "woven",
        },
    )
    assert adv_res.status_code == 200
    assert adv_res.json()["awakening_stage"] == "woven"
