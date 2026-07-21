# backend/tests/test_roll_contract.py
import importlib

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.grammar import NumericDiceRoll, generate_numeric_roll, interpret_numeric_roll
from app.main import app

client = TestClient(app)

VALID = {
    "d20": 17,
    "d12": 4,
    "d10": 8,
    "percentile": 70,
    "d8": 3,
    "d6": 5,
    "d4": 2,
    "grammar_version": "1.0.0",
}


@pytest.mark.parametrize(
    "die,low,high",
    [
        ("d20", 1, 20),
        ("d12", 1, 12),
        ("d10", 1, 10),
        ("percentile", 1, 100),
        ("d8", 1, 8),
        ("d6", 1, 6),
        ("d4", 1, 4),
    ],
)
def test_numeric_boundaries_accept_legal_faces(die, low, high):
    low_roll = {**VALID, die: low}
    high_roll = {**VALID, die: high}
    assert NumericDiceRoll(**low_roll).model_dump()[die] == low
    assert NumericDiceRoll(**high_roll).model_dump()[die] == high


@pytest.mark.parametrize(
    "die,bad",
    [
        ("d20", 0),
        ("d12", 13),
        ("d10", 11),
        ("percentile", 0),
        ("percentile", 101),
        ("d8", 9),
        ("d6", 7),
        ("d4", 5),
    ],
)
def test_rejects_illegal_faces(die, bad):
    with pytest.raises(ValidationError):
        NumericDiceRoll(**{**VALID, die: bad})


def test_deterministic_interpretation_and_manual_endpoint():
    first = interpret_numeric_roll(NumericDiceRoll(**VALID))
    second = interpret_numeric_roll(NumericDiceRoll(**VALID))
    assert first == second
    response = client.post("/api/v1/dice/interpret", json=VALID)
    assert response.status_code == 200
    assert response.json()["raw"]["percentile"] == 70
    assert response.json()["interpretation"] == first.interpretation.model_dump()


def test_grammar_version_lookup_and_unknown_rejection():
    assert client.get("/api/v1/dice/grammar/versions").json() == {
        "current_default": "1.0.0",
        "versions": ["1.0.0"],
    }
    assert (
        client.post(
            "/api/v1/dice/interpret", json={**VALID, "grammar_version": "nope"}
        ).status_code
        == 422
    )


def test_seeded_roll_repeatability_and_legal_ranges():
    one = client.post("/api/v1/dice/roll", json={"seed": "omen"}).json()
    two = client.post("/api/v1/dice/roll", json={"seed": "omen"}).json()
    assert one == two
    assert one["raw"] == generate_numeric_roll(seed="omen").raw


def test_d4_has_only_four_valid_threads():
    threads = {
        interpret_numeric_roll(
            NumericDiceRoll(**{**VALID, "d4": value})
        ).interpretation.thread
        for value in range(1, 5)
    }
    assert threads == {"Bond", "Memory", "Mark", "Prophecy"}


def test_scene_resolution_preserves_raw_values_and_chronicle(monkeypatch, tmp_path):
    db = importlib.import_module("app.db")
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "chronicle.db"))
    import app.main as main

    monkeypatch.setattr(main, "log_canonical_event", db.log_canonical_event)
    monkeypatch.setattr(main, "get_all_canonical_events", db.get_all_canonical_events)
    db.init_database()

    dice = client.post("/api/v1/dice/interpret", json=VALID).json()
    payload = {
        "dice_read": dice,
        "chosen_approach": "Guile",
        "resonance_spent": 1,
        "strain_accepted": 0,
        "player_intent": "Reveal the oath.",
        "soul_name": "Test Soul",
        "resources": {"resonance": 3, "strain": 1, "thread_count": 2},
    }
    resolved = client.post("/api/v1/scenes/resolve", json=payload)
    assert resolved.status_code == 200
    assert resolved.json()["dice_read"]["raw"] == {
        k: VALID[k] for k in ["d20", "d12", "d10", "percentile", "d8", "d6", "d4"]
    }

    events = client.get("/api/v1/chronicle/events").json()["events"]
    assert events[0]["raw_roll"] == resolved.json()["dice_read"]["raw"]
    assert (
        events[0]["interpreted_roll"] == resolved.json()["dice_read"]["interpretation"]
    )
    assert events[0]["grammar_version"] == "1.0.0"


def test_encounter_frame_is_deterministic_and_pre_action():
    dice = client.post("/api/v1/dice/interpret", json=VALID).json()
    payload = {
        "dice_read": dice,
        "soul_name": "Test Soul",
        "world_context": ["The salt bell remembers the drowned quay."],
    }
    first = client.post("/api/v1/encounters/frame", json=payload)
    second = client.post("/api/v1/encounters/frame", json=payload)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.json()["phenomenon_type"] == "Corruption"
    assert 1 <= first.json()["pressure_clock"] <= 6
    assert "outcome" not in first.json()
