# backend/tests/test_reflection_accessibility.py
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_reflection_and_accessibility_flow():
    soul_id = f"Test_Soul_{str(uuid.uuid4())[:6]}"

    # 1. Fetch default player preferences
    pref_res = client.get(f"/api/v1/reflection/preferences?soul_id={soul_id}")
    assert pref_res.status_code == 200
    pref = pref_res.json()["preferences"]
    assert pref["narrative_intensity"] == "balanced"
    assert pref["reduced_motion"] is False

    # 2. Update player preferences
    update_res = client.post(
        "/api/v1/reflection/preferences",
        json={
            "soul_id": soul_id,
            "narrative_intensity": "deep_mythic",
            "spiritual_framing": "secular_mythology",
            "reduced_motion": True,
            "high_contrast": True,
            "allow_ai_indexing_default": False,
        },
    )
    assert update_res.status_code == 200
    up_pref = update_res.json()["preferences"]
    assert up_pref["narrative_intensity"] == "deep_mythic"
    assert up_pref["reduced_motion"] is True
    assert up_pref["high_contrast"] is True

    # 3. Create optional end-of-session reflection
    ref_res = client.post(
        "/api/v1/reflection/sessions/create",
        json={
            "soul_id": soul_id,
            "prompt_question": "What pattern did you notice in today's choices?",
            "player_reflection": "I noticed a recurring theme of choosing truth over immediate safety.",
            "share_with_ai": False,
        },
    )
    assert ref_res.status_code == 200
    ref_session = ref_res.json()["session"]
    assert ref_session["share_with_ai"] is False

    # 4. List reflection sessions
    list_ref_res = client.get(f"/api/v1/reflection/sessions?soul_id={soul_id}")
    assert list_ref_res.status_code == 200
    sessions = list_ref_res.json()["sessions"]
    assert len(sessions) >= 1

    # 5. Create private note with default AI exclusion
    note_res = client.post(
        "/api/v1/reflection/notes/create",
        json={
            "soul_id": soul_id,
            "title": "Private Observations on the Salt Spire",
            "content": "Personal reflections on the choice made at the altar.",
            "allow_ai_indexing": False,
        },
    )
    assert note_res.status_code == 200
    note = note_res.json()["note"]
    assert note["allow_ai_indexing"] is False

    # 6. List private notes
    list_notes_res = client.get(f"/api/v1/reflection/notes?soul_id={soul_id}")
    assert list_notes_res.status_code == 200
    notes = list_notes_res.json()["notes"]
    assert len(notes) >= 1
