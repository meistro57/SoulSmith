# backend/tests/test_relic_recognition.py
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_relic_recognition_full_lifecycle():
    soul_id = f"Test_Soul_{str(uuid.uuid4())[:6]}"

    # 1. Fetch default relics
    list_res = client.get(f"/api/v1/relics?soul_id={soul_id}")
    assert list_res.status_code == 200
    relics = list_res.json()["relics"]
    assert len(relics) >= 3

    # Pick a dormant or remembered relic
    dormant_relic = next(r for r in relics if r["stage"] == "Dormant")
    relic_id = dormant_relic["id"]

    # 2. Attune relic with narrative condition & chronicle evidence
    attune_res = client.post(
        "/api/v1/relics/attune-narrative",
        json={
            "relic_id": relic_id,
            "soul_id": soul_id,
            "narrative_condition_met": "Answered the open question of the Lantern.",
            "chronicle_evidence_summary": "Discovered the Sol Prism in the Flooded Archives.",
        },
    )
    assert attune_res.status_code == 200
    data = attune_res.json()
    assert data["relic"]["stage"] == "Remembered"
    assert data["relic_event"]["action"] == "attune"

    # 3. Overdraw relic power
    overdraw_res = client.post(
        "/api/v1/relics/overdraw",
        json={
            "relic_id": relic_id,
            "soul_id": soul_id,
            "intensity_boost": "Ascendancy Score +2",
        },
    )
    assert overdraw_res.status_code == 200
    assert overdraw_res.json()["relic"]["stage"] == "Overdrawn"

    # 4. Overdraw twice to trigger fracture
    fracture_res = client.post(
        "/api/v1/relics/overdraw",
        json={
            "relic_id": relic_id,
            "soul_id": soul_id,
            "intensity_boost": "Overdraw overload",
        },
    )
    assert fracture_res.status_code == 200
    assert fracture_res.json()["relic"]["stage"] == "Fractured"

    # 5. Repair fractured relic with evidence
    repair_res = client.post(
        "/api/v1/relics/repair",
        json={
            "relic_id": relic_id,
            "soul_id": soul_id,
            "repair_evidence_summary": "Integrated Memory Thread #4 to mend the shattered vessel.",
        },
    )
    assert repair_res.status_code == 200
    assert repair_res.json()["relic"]["stage"] == "Awakened"

    # 6. Transfigure relic into Constellation Anchor
    transfigure_res = client.post(
        "/api/v1/relics/transfigure",
        json={
            "relic_id": relic_id,
            "soul_id": soul_id,
            "anchor_name": "Anchor of Sol Suns",
            "transfigured_form": "Sol Prism Beacon",
        },
    )
    assert transfigure_res.status_code == 200
    t_data = transfigure_res.json()
    assert t_data["relic"]["stage"] == "Transfigured"
    assert t_data["relic"]["is_anchor"] is True

    # 7. Check relic history log
    hist_res = client.get(f"/api/v1/relics/{relic_id}/history")
    assert hist_res.status_code == 200
    history = hist_res.json()["history"]
    assert len(history) >= 5
