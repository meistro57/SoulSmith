# backend/tests/test_campaign_orchestrator.py
"""Phase 17: Campaign Orchestrator tests.

These prove the orchestrator coordinates existing systems without claiming
authority over their meaning, that callbacks carry provenance, that cooldowns
prevent repetitive callbacks, that recognition/rejection is player-controlled,
that NPC knowledge respects consent boundaries, that relic awakening stays with
Relic Recognition, and that the North-Star loop runs deterministically offline.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app import campaign_orchestrator
from app.campaign import (
    build_integration_candidates,
    build_npc_historical_reaction_candidates,
    build_relic_awakening_candidates,
    build_seed_echo_candidates,
)
from app.main import app
from app.world_memory import NPCKnowledgeRequest, project_npc_knowledge

client = TestClient(app)

SOUL = "Kaelen the Star-Watcher"
OTHER = "Archivist Vael"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


def _start(soul_id: str = SOUL, campaign_id: str | None = None) -> dict:
    payload: dict = {"soul_id": soul_id}
    if campaign_id:
        payload["campaign_id"] = campaign_id
    res = client.post("/api/v1/campaign/session", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["session"]


def _interpret(thread_d4: int = 3, domain_d12: int = 9, spark_d20: int = 17) -> dict:
    res = client.post(
        "/api/v1/dice/interpret",
        json={
            "d20": spark_d20,
            "d12": domain_d12,
            "d10": 5,
            "percentile": 70,
            "d8": 3,
            "d6": 4,
            "d4": thread_d4,
            "grammar_version": "1.0.0",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def _resolve_scene(read: dict, soul_id: str = SOUL, intent: str | None = None) -> dict:
    res = client.post(
        "/api/v1/scenes/resolve",
        json={
            "dice_read": read,
            "chosen_approach": "Guile",
            "resonance_spent": 1,
            "strain_accepted": 0,
            "player_intent": intent or "I want to understand the recurring symbol.",
            "soul_name": soul_id,
            "resources": {"resonance": 3, "strain": 0, "thread_count": 1},
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def _commit(session_id: str, event_id: str) -> dict:
    res = client.post(
        "/api/v1/campaign/commit",
        json={"session_id": session_id, "event_id": event_id},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _evaluate(session_id: str, include_encounter: bool = True) -> dict:
    res = client.post(
        "/api/v1/campaign/opportunities/evaluate",
        json={"session_id": session_id, "include_encounter": include_encounter},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _resolve_opp(opportunity_id: str, **payload) -> dict:
    res = client.post(
        f"/api/v1/campaign/opportunities/{opportunity_id}/resolve", json=payload
    )
    assert res.status_code == 200, res.text
    return res.json()


def _of_type(opportunities: list[dict], opportunity_type: str) -> list[dict]:
    return [o for o in opportunities if o["opportunity_type"] == opportunity_type]


def _scene_and_commit(session_id: str, thread_d4: int = 3) -> dict:
    read = _interpret(thread_d4=thread_d4)
    scene = _resolve_scene(read)
    return _commit(session_id, scene["event_id"])


def _event_count() -> int:
    return len(client.get("/api/v1/chronicle/events").json()["events"])


def _make_avatar(soul_id: str) -> str:
    res = client.post(
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
    assert res.status_code == 200, res.text
    profile = client.get(f"/api/v1/visual/avatar/{soul_id}").json()
    return profile["portraits"][0]["version_id"]


def _make_memory(soul_id: str, portrait_version_id: str, **overrides) -> dict:
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_title": "The Unbroken Promise",
        "participants": [
            {
                "soul_id": soul_id,
                "character_name": soul_id,
                "portrait_version_id": portrait_version_id,
                "role_in_event": "Focus",
                "real_person_tag_opt_in": False,
            }
        ],
        "location_environment": "The Sunken Spire",
        "relics_involved": [],
        "emotional_tone": "Solemn vow",
        "action_composition": f"{soul_id} swore to remember the Starforge.",
        "lasting_consequence": "The promise passed into legend.",
        "privacy_consent_scope": "public_canon",
        "importance_tier": "personal",
        "importance_score": 5,
    }
    payload.update(overrides)
    res = client.post("/api/v1/visual/memory-objects/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory_object"]


def _make_world_memory(subject_type: str, subject_id: str, **overrides) -> dict:
    payload = {
        "subject_entity_type": subject_type,
        "subject_entity_id": subject_id,
    }
    payload.update(overrides)
    res = client.post("/api/v1/world-memory/compile", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["memory"]


# 1. Deterministic, structured opportunities without model inference.
def test_evaluate_produces_structured_opportunities():
    session = _start()
    result = _evaluate(session["session_id"])
    assert isinstance(result["silence"], bool)
    for opportunity in result["opportunities"]:
        assert opportunity["eligibility_rule"]
        assert opportunity["narration_source"] == "deterministic"
        assert opportunity["lifecycle_state"] == "eligible"


# 2. "No eligible opportunity" is a valid result at the eligibility layer.
def test_pure_builders_return_empty_for_empty_state():
    assert build_seed_echo_candidates([]) == []
    assert build_npc_historical_reaction_candidates([], SOUL) == []
    assert build_integration_candidates([], []) == []
    assert build_relic_awakening_candidates([], [], []) == []


# 3. Cooldown prevents repetitive callbacks.
def test_cooldown_prevents_repetitive_seed_echo():
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    seed_echoes = _of_type(commit["opportunities"], "seed_echo")
    assert seed_echoes
    seed_id = seed_echoes[0]["source_evidence"][0]["source_id"]

    _resolve_opp(seed_echoes[0]["opportunity_id"])

    result = _evaluate(session["session_id"])
    reoffered = [
        o
        for o in _of_type(result["opportunities"], "seed_echo")
        if o["source_evidence"][0]["source_id"] == seed_id
    ]
    assert reoffered == []


# 4. Seed echo retains provenance.
def test_seed_echo_retains_provenance():
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    seed_echo = _of_type(commit["opportunities"], "seed_echo")[0]
    resolved = _resolve_opp(seed_echo["opportunity_id"])
    outcome = resolved["transition"]["outcomes"][0]
    assert outcome["system_name"] == "Curiosity Engine"
    assert outcome["result_kind"] == "state_updated"
    assert seed_echo["source_evidence"][0]["source_type"] == "seed"


# 5. Callbacks cannot reference nonexistent Chronicle evidence.
def test_npc_reaction_requires_existing_world_memory():
    session = _start()
    # A world memory that does not exist yields no narration and no canon change.
    fake = {
        "opportunity_id": "x",
        "session_id": session["session_id"],
        "opportunity_type": "npc_historical_reaction",
        "source_evidence": [],
        "involved_entities": [],
        "domain_action_payload": {"memory_id": "missing_memory"},
    }
    narration, failure = campaign_orchestrator._npc_reaction(fake, session)
    assert narration is None
    assert failure is not None


# 6. Rejected Thread interpretation remains rejected (no canonical mutation).
def test_rejected_thread_interpretation_remains_rejected():
    session = _start()
    for _ in range(3):
        _scene_and_commit(session["session_id"], thread_d4=1)
    result = _evaluate(session["session_id"])
    recognition = _of_type(result["opportunities"], "recognition")[0]
    resolved = _resolve_opp(
        recognition["opportunity_id"], recognition={"decision": "reject"}
    )
    assert resolved["opportunity"]["lifecycle_state"] == "rejected"
    assert resolved["transition"]["canonical_change"] is False
    threads = client.get(f"/api/v1/curiosity/threads?soul_name={SOUL}").json()[
        "threads"
    ]
    bond = [t for t in threads if t["thread_type"] == "Bond"]
    assert bond and bond[0]["status"] == "pattern_recognized"


# 7. Player can postpone recognition.
def test_player_can_postpone_recognition():
    session = _start()
    for _ in range(3):
        _scene_and_commit(session["session_id"], thread_d4=1)
    recognition = _of_type(
        _evaluate(session["session_id"])["opportunities"], "recognition"
    )[0]
    resolved = _resolve_opp(
        recognition["opportunity_id"], recognition={"decision": "postpone"}
    )
    assert resolved["opportunity"]["lifecycle_state"] == "postponed"


# 8. Cross-Aspect callback respects knowledge boundaries (no omniscience).
def test_cross_aspect_echo_is_evidence_only():
    session = _start()
    result = _evaluate(session["session_id"])
    echoes = _of_type(result["opportunities"], "cross_aspect_echo")
    assert echoes
    for echo in echoes:
        for evidence in echo["source_evidence"]:
            assert evidence["source_type"] in (
                "cross_aspect_bond",
                "constellation_anchor",
            )


# 9. NPC cannot access omniscient Chronicle state.
def test_npc_cannot_access_omniscient_state():
    memory = {
        "visibility": "public_canon",
        "culture": "Northern",
        "era_context": "Age of Echoes",
    }
    npc = NPCKnowledgeRequest(
        subject_entity_type="person",
        subject_entity_id="someone_else",
        culture="Southern",  # non-matching culture
        era_context="Age of Echoes",
        social_role="commoner",
    )
    projection = project_npc_knowledge(
        subject_entity_type="person",
        subject_entity_id="someone_else",
        npc=npc,
        memories=[memory],
    )
    assert projection.entries == []


# 10. NPC can react when knowledge projection legitimately permits.
def test_npc_reacts_when_permitted():
    session = _start(SOUL)
    other_portrait = _make_avatar(OTHER)
    _make_memory(OTHER, other_portrait)
    memory = _make_world_memory(
        "person", OTHER, culture="Northern", era_context="Age of Echoes"
    )

    result = _evaluate(session["session_id"])
    reactions = _of_type(result["opportunities"], "npc_historical_reaction")
    assert reactions
    reaction = reactions[0]
    assert reaction["source_evidence"][0]["source_id"] == memory["memory_id"]

    resolved = _resolve_opp(reaction["opportunity_id"])
    outcome = resolved["transition"]["outcomes"][0]
    assert outcome["result_kind"] == "state_updated"
    assert outcome["details"].get("prose")


# 11. Relic memory preserves original provenance.
def test_relic_memory_preserves_provenance():
    session = _start()
    result = _evaluate(session["session_id"])
    memories = _of_type(result["opportunities"], "relic_memory")
    assert memories
    evidence_types = {e["source_type"] for e in memories[0]["source_evidence"]}
    assert "relic" in evidence_types


# 12. The orchestrator cannot directly awaken a relic.
def test_orchestrator_cannot_awaken_relic():
    session = _start()
    for _ in range(3):
        _scene_and_commit(session["session_id"], thread_d4=1)
    result = _evaluate(session["session_id"])
    candidates = _of_type(result["opportunities"], "relic_awakening_candidate")
    assert candidates
    candidate = candidates[0]
    relic_id = candidate["domain_action_payload"]["relic_id"]

    before = client.get(f"/api/v1/relics?soul_id={SOUL}").json()["relics"]
    before_stage = next(r["stage"] for r in before if r["id"] == relic_id)
    resolved = _resolve_opp(candidate["opportunity_id"])
    assert resolved["transition"]["canonical_change"] is False
    after = client.get(f"/api/v1/relics?soul_id={SOUL}").json()["relics"]
    after_stage = next(r["stage"] for r in after if r["id"] == relic_id)
    assert before_stage == after_stage == "Remembered"


# 13. Valid Integration evidence produces a relic-awakening candidate.
def test_integration_evidence_produces_awakening_candidate():
    session = _start()
    for _ in range(3):
        _scene_and_commit(session["session_id"], thread_d4=1)
    result = _evaluate(session["session_id"])
    candidates = _of_type(result["opportunities"], "relic_awakening_candidate")
    assert candidates
    # The candidate must point at a Remembered relic whose required Thread is Bond.
    relics = client.get(f"/api/v1/relics?soul_id={SOUL}").json()["relics"]
    relic_ids = {c["domain_action_payload"]["relic_id"] for c in candidates}
    assert any(
        r["id"] in relic_ids and r["stage"] == "Remembered" and r["effect"]
        for r in relics
    )


# 14. A failed derived subsystem does not corrupt committed canon.
def test_failed_derived_subsystem_does_not_corrupt_canon(monkeypatch):
    session = _start()
    read = _interpret(thread_d4=1)
    scene = _resolve_scene(read)
    committed_event_id = scene["event_id"]

    def _boom(*args, **kwargs):
        raise RuntimeError("derived subsystem failure")

    monkeypatch.setattr(campaign_orchestrator, "build_relic_memory_candidates", _boom)
    result = _commit(session["session_id"], committed_event_id)

    assert result["transition"]["canonical_event_id"] == committed_event_id
    relic_reaction = next(
        r
        for r in result["transition"]["reactions"]
        if r["system_name"] == "Relic Recognition"
    )
    assert relic_reaction["result_kind"] == "no_action"
    assert "error" in relic_reaction["details"]
    assert _event_count() == 1  # canon intact


# 15. Session resume is deterministic.
def test_session_resume_is_deterministic():
    first = _start(SOUL, campaign_id="resume_test")
    second = _start(SOUL, campaign_id="resume_test")
    assert first["session_id"] == second["session_id"]


# 16. Duplicate requests do not duplicate canonical events.
def test_duplicate_commit_and_resolve_are_idempotent():
    session = _start()
    read = _interpret(thread_d4=1)
    scene = _resolve_scene(read)
    event_id = scene["event_id"]

    first = _commit(session["session_id"], event_id)
    second = _commit(session["session_id"], event_id)
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert _event_count() == 1

    seed_echo = _of_type(first["opportunities"], "seed_echo")[0]
    seed_id = seed_echo["source_evidence"][0]["source_id"]
    before = next(
        s
        for s in client.get("/api/v1/curiosity/seeds").json()["seeds"]
        if s["id"] == seed_id
    )["echo_count"]

    _resolve_opp(seed_echo["opportunity_id"])
    _resolve_opp(seed_echo["opportunity_id"])  # duplicate resolve is a no-op

    after = next(
        s
        for s in client.get("/api/v1/curiosity/seeds").json()["seeds"]
        if s["id"] == seed_id
    )["echo_count"]
    assert after == before + 1  # echoed exactly once


# 17. Provider failure does not invent fallback canon.
def test_provider_failure_does_not_invent_canon(monkeypatch):
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    probable = _of_type(commit["opportunities"], "probable_path_echo")[0]

    class _FailingProvider:
        def narrate(self, context):
            raise RuntimeError("provider down")

    monkeypatch.setattr(
        campaign_orchestrator, "get_campaign_provider", lambda: _FailingProvider()
    )
    resolved = _resolve_opp(probable["opportunity_id"])

    assert resolved["transition"]["provider_failure"] is not None
    assert resolved["transition"]["canonical_change"] is False
    assert _event_count() == 1  # no invented canonical event


# 18. Consent filtering survives NarrativeContext compilation.
def test_consent_filtering_survives_narrative_context():
    session = _start(SOUL)
    other_portrait = _make_avatar(OTHER)
    # A private memory object owned by another soul must never surface as art.
    _make_memory(
        OTHER,
        other_portrait,
        privacy_consent_scope="private",
        importance_tier="world",
        importance_score=9,
    )
    result = _evaluate(session["session_id"])
    paintings = _of_type(result["opportunities"], "chronicle_painting_eligibility")
    assert paintings == []


# 19. Transition records list systems and outcomes.
def test_transition_records_systems_and_outcomes():
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    transition = commit["transition"]
    assert transition["systems_invoked"]
    assert transition["outcomes"]
    assert any(r["system_name"] == "Chronicle" for r in transition["reactions"])


# 20. Dice still converge on the canonical roll contract through the loop.
def test_dice_roll_still_converges_on_canonical_contract():
    session = _start()
    read = _interpret(thread_d4=2)
    assert read["raw"]["d4"] == 2
    assert read["interpretation"]["thread"] == "Memory"
    scene = _resolve_scene(read)
    commit = _commit(session["session_id"], scene["event_id"])
    assert commit["transition"]["canonical_event_id"] == scene["event_id"]


# 21. Probable Path callback remains noncanonical.
def test_probable_path_callback_is_noncanonical():
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    probable = _of_type(commit["opportunities"], "probable_path_echo")[0]
    resolved = _resolve_opp(probable["opportunity_id"])
    assert resolved["transition"]["canonical_change"] is False


# 22. Group Memory perspectives remain distinct (private groups are not surfaced).
def test_group_memory_callback_respects_membership():
    session = _start(SOUL)
    other_portrait = _make_avatar(OTHER)
    other_memory = _make_memory(OTHER, other_portrait)
    # Group the OTHER soul's memory; the current soul is not a member.
    res = client.post(
        "/api/v1/group-memories",
        json={"event_id": other_memory["event_id"], "visibility": "public_canon"},
    )
    assert res.status_code == 200, res.text

    result = _evaluate(session["session_id"])
    callbacks = _of_type(result["opportunities"], "group_memory_callback")
    assert callbacks == []


# 23. World Memory legend remains distinct from Chronicle truth.
def test_world_memory_legend_is_noncanonical():
    session = _start()
    other_portrait = _make_avatar(OTHER)
    _make_memory(OTHER, other_portrait)
    _make_world_memory(
        "person", OTHER, memory_form="legend", interpretation_type="exaggerated"
    )

    result = _evaluate(session["session_id"])
    legends = _of_type(result["opportunities"], "world_memory_legend_encounter")
    assert legends
    resolved = _resolve_opp(legends[0]["opportunity_id"])
    assert resolved["transition"]["canonical_change"] is False


# 24/25. North-Star end-to-end scenario with traceable provenance.
def test_north_star_end_to_end():
    session = _start(SOUL)

    # 1-2. Encounter a symbol and record it canonically.
    read = _interpret(thread_d4=1, domain_d12=9, spark_d20=17)
    scene = _resolve_scene(read, intent="I notice a faint symbol by the archive door.")
    event_id = scene["event_id"]
    commit = _commit(session["session_id"], event_id)

    # 3-4. Echo the symbol later through the Curiosity system.
    seed_echo = _of_type(commit["opportunities"], "seed_echo")[0]
    symbol = seed_echo["domain_action_payload"]["symbol"]
    _resolve_opp(seed_echo["opportunity_id"])
    seeds = client.get("/api/v1/curiosity/seeds").json()["seeds"]
    assert any(s["symbol"] == symbol and s["echo_count"] >= 2 for s in seeds)

    # 5-6. Introduce a relic with historical significance (relic_memory candidate).
    relic_memory = _of_type(commit["opportunities"], "relic_memory")[0]
    assert relic_memory["source_evidence"]
    _resolve_opp(relic_memory["opportunity_id"])

    # 7-8. Create/load another Aspect with a canonical promise and make it world-known.
    other_portrait = _make_avatar(OTHER)
    _make_memory(OTHER, other_portrait)
    world_memory = _make_world_memory(
        "person", OTHER, culture="Northern", era_context="Age of Echoes"
    )

    # 9-10. Project appropriate knowledge to an NPC and have the NPC react.
    reactions = _of_type(
        _evaluate(session["session_id"])["opportunities"], "npc_historical_reaction"
    )
    assert reactions
    npc_reaction = reactions[0]
    assert npc_reaction["source_evidence"][0]["source_id"] == world_memory["memory_id"]
    npc_resolved = _resolve_opp(npc_reaction["opportunity_id"])
    assert npc_resolved["transition"]["outcomes"][0]["result_kind"] == "state_updated"

    # 11-12. Accumulate Chronicle evidence for a recurring Thread.
    for _ in range(2):
        read2 = _interpret(thread_d4=1, domain_d12=9, spark_d20=17)
        scene2 = _resolve_scene(read2, intent="I choose differently this time.")
        _commit(session["session_id"], scene2["event_id"])

    evaluated = _evaluate(session["session_id"])
    recognition = _of_type(evaluated["opportunities"], "recognition")
    assert recognition

    # 13. Surface a recognition opportunity and let the player recognize.
    recognized = _resolve_opp(
        recognition[0]["opportunity_id"], recognition={"decision": "recognize"}
    )
    assert recognized["transition"]["canonical_change"] is False

    # 14. Validate an Integration Event through the existing Integration system.
    integration = _of_type(
        _evaluate(session["session_id"])["opportunities"], "integration_candidate"
    )[0]
    integrated = _resolve_opp(
        integration["opportunity_id"],
        decision="integrate",
        player_intent="I chose differently after recognizing the pattern.",
    )
    assert integrated["transition"]["canonical_change"] is True
    assert integrated["transition"]["systems_invoked"][0] == "Threads & Integration"

    # 15. Trigger a relic-awakening candidate and validate via Relic Recognition.
    candidates = _of_type(
        _evaluate(session["session_id"])["opportunities"], "relic_awakening_candidate"
    )
    assert candidates
    relic_id = candidates[0]["domain_action_payload"]["relic_id"]
    _resolve_opp(candidates[0]["opportunity_id"])

    attune = client.post(
        "/api/v1/relics/attune-narrative",
        json={
            "relic_id": relic_id,
            "soul_id": SOUL,
            "narrative_condition_met": "The Bond Thread was recognized and integrated.",
            "chronicle_evidence_summary": "Three Bond Thread events and a player-chosen different response.",
        },
    )
    assert attune.status_code == 200, attune.text
    assert attune.json()["relic"]["stage"] == "Awakened"

    # 16-18. Persist consequences and prove callbacks are traceable.
    relics = client.get(f"/api/v1/relics?soul_id={SOUL}").json()["relics"]
    assert next(r["stage"] for r in relics if r["id"] == relic_id) == "Awakened"

    state = client.get(f"/api/v1/campaign/session/{session['session_id']}").json()
    assert state["transitions"]
    for transition in state["transitions"]:
        assert transition["systems_invoked"]
        assert transition["outcomes"]
