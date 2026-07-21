# backend/tests/test_curiosity_engine.py
import importlib
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_DICE_PAYLOAD = {
    "d20": 17,
    "d12": 4,
    "d10": 8,
    "percentile": 70,
    "d8": 3,
    "d6": 5,
    "d4": 2,
    "grammar_version": "1.0.0",
}


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    db = importlib.import_module("app.db")
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "test_curiosity.db"))
    import app.main as main

    monkeypatch.setattr(main, "init_database", db.init_database)
    monkeypatch.setattr(main, "plant_or_echo_seed", db.plant_or_echo_seed)
    monkeypatch.setattr(main, "get_all_seeds", db.get_all_seeds)
    monkeypatch.setattr(main, "get_all_open_questions", db.get_all_open_questions)
    monkeypatch.setattr(main, "resolve_open_question", db.resolve_open_question)
    monkeypatch.setattr(main, "get_all_local_threads", db.get_all_local_threads)
    monkeypatch.setattr(main, "execute_integration_event", db.execute_integration_event)

    db.init_database()


def test_seed_planting_and_echoing():
    # Plant first seed
    res1 = client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": "Drowned Lantern",
            "thread_type": "Memory",
            "narrative_context": "Found under harbor ruins",
            "soul_id": "Kaelen",
            "initial_question": "Who drowned the lantern?",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["symbol"] == "Drowned Lantern"
    assert data1["stage"] == "planted"
    assert data1["echo_count"] == 1

    # Echo same seed second time
    res2 = client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": "Drowned Lantern",
            "thread_type": "Memory",
            "narrative_context": "Seen in a dream",
            "soul_id": "Kaelen",
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["stage"] == "echoed"
    assert data2["echo_count"] == 2

    # Echo third time -> stage becomes 'recognized'
    res3 = client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": "Drowned Lantern",
            "thread_type": "Memory",
            "narrative_context": "Reflected in salt crystal",
            "soul_id": "Kaelen",
        },
    )
    assert res3.json()["stage"] == "recognized"
    assert res3.json()["echo_count"] == 3


def test_list_seeds_and_open_questions():
    client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": "Salt Bell",
            "thread_type": "Bond",
            "narrative_context": "Rings when promises break",
            "soul_id": "Kaelen",
            "initial_question": "Whose promise cracked the bell?",
        },
    )

    seeds = client.get("/api/v1/curiosity/seeds").json()["seeds"]
    assert len(seeds) >= 1
    assert seeds[0]["symbol"] == "Salt Bell"

    questions = client.get("/api/v1/curiosity/questions").json()["questions"]
    assert len(questions) >= 1
    assert questions[0]["question_text"] == "Whose promise cracked the bell?"

    # Resolve question
    q_id = questions[0]["id"]
    res_q = client.post(
        "/api/v1/curiosity/questions/resolve",
        json={
            "question_id": q_id,
            "resolution_notes": "The harbor master broke the pact",
        },
    )
    assert res_q.json()["success"] is True

    updated_questions = client.get("/api/v1/curiosity/questions").json()["questions"]
    assert updated_questions[0]["status"] == "resolved"


def test_local_thread_lifecycle_and_integration():
    client.post(
        "/api/v1/curiosity/seeds/plant",
        json={
            "symbol": "Mirror Scar",
            "thread_type": "Mark",
            "narrative_context": "Reflects non-existent lights",
            "soul_id": "Kaelen",
        },
    )

    threads = client.get("/api/v1/curiosity/threads?soul_name=Kaelen").json()["threads"]
    assert len(threads) >= 1
    th = threads[0]
    assert th["thread_type"] == "Mark"
    assert th["status"] == "active"

    # Integrate Thread
    int_res = client.post(
        "/api/v1/curiosity/integrate",
        json={
            "thread_id": th["id"],
            "soul_name": "Kaelen",
            "choice_made": "Accepted the mirror mark as a true boundary",
            "target_relic_id": "relic-veil-glass",
        },
    )
    assert int_res.status_code == 200
    int_data = int_res.json()
    assert int_data["thread_name"] == th["name"]
    assert "integrated via choice" in int_data["transformation_summary"]

    # Verify status changed to integrated
    threads_after = client.get("/api/v1/curiosity/threads?soul_name=Kaelen").json()[
        "threads"
    ]
    assert threads_after[0]["status"] == "integrated"


def test_scene_resolution_autoplants_seed_when_thread_rolled():
    dice = client.post("/api/v1/dice/interpret", json=VALID_DICE_PAYLOAD).json()
    # VALID_DICE_PAYLOAD has d4=2 -> Memory Thread
    payload = {
        "dice_read": dice,
        "chosen_approach": "Guile",
        "resonance_spent": 1,
        "strain_accepted": 0,
        "player_intent": "Investigate the sunken archive.",
        "soul_name": "Kaelen",
        "resources": {"resonance": 3, "strain": 1, "thread_count": 2},
    }
    res = client.post("/api/v1/scenes/resolve", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["seed"] is not None
    assert body["seed"]["thread_type"] == "Memory"
    assert body["seed"]["stage"] == "planted"
