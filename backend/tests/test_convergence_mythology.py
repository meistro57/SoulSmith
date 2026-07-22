# backend/tests/test_convergence_mythology.py
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_convergence_community_mythology_flow():
    room_id = f"room_{str(uuid.uuid4())[:6]}"

    # 1. Fetch community world symbols
    symbols_res = client.get("/api/v1/convergence/symbols")
    assert symbols_res.status_code == 200
    symbols = symbols_res.json()["symbols"]
    assert len(symbols) >= 3

    # 2. Get or create active gathering session
    g_res = client.get(
        f"/api/v1/convergence/gatherings/{room_id}?phenomenon_name=Awakening%20of%20the%20Salt%20Spire"
    )
    assert g_res.status_code == 200
    gathering = g_res.json()["gathering"]
    assert gathering["room_id"] == room_id
    assert gathering["status"] == "active"
    gathering_id = gathering["id"]

    # 3. Submit roll contribution from Focus
    contrib_1 = client.post(
        "/api/v1/convergence/gatherings/contribute",
        json={
            "gathering_id": gathering_id,
            "contributor_soul": "Kaelen the Star-Watcher",
            "role": "Focus",
            "resonance_amount": 4,
            "notes": "Channeled [Heart] spark to initiate starlight resonance.",
        },
    )
    assert contrib_1.status_code == 200
    g1_data = contrib_1.json()["gathering"]
    assert g1_data["current_resonance"] == 4
    assert g1_data["status"] == "active"

    # 4. Submit roll contribution from Anchor to reach target resonance (10)
    contrib_2 = client.post(
        "/api/v1/convergence/gatherings/contribute",
        json={
            "gathering_id": gathering_id,
            "contributor_soul": "Archivist Vael",
            "role": "Anchor",
            "resonance_amount": 6,
            "notes": "Anchored the Salt Bell to stabilize physical manifestation.",
        },
    )
    assert contrib_2.status_code == 200
    g2_data = contrib_2.json()["gathering"]
    assert g2_data["current_resonance"] == 10
    assert g2_data["status"] == "reconciled"
    assert "awakened" in g2_data["outcome_summary"].lower()

    # 5. Merge shared canon into community myth
    merge_res = client.post(
        "/api/v1/convergence/canon/merge",
        json={
            "gathering_id": gathering_id,
            "symbol_name": "Awakened Salt Spire Phenomenon",
            "description": "Multi-soul gathering where Kaelen and Vael awakened the salt spire.",
            "consenting_souls": ["Kaelen the Star-Watcher", "Archivist Vael"],
        },
    )
    assert merge_res.status_code == 200
    assert merge_res.json()["success"] is True
    assert merge_res.json()["symbol"]["canon_status"] == "public_canon"

    # 6. Test canon fork for a dissenting soul
    fork_res = client.post(
        "/api/v1/convergence/canon/fork",
        json={
            "gathering_id": gathering_id,
            "forking_soul": "Ember Vanguard",
            "reason": "Rejected the salt spire awakening outcome to pursue the Shadow Veil path.",
        },
    )
    assert fork_res.status_code == 200
    assert fork_res.json()["success"] is True
