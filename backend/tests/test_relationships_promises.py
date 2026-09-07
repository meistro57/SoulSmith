# backend/tests/test_relationships_promises.py
"""Phase 19: Relationship & Promise Engine tests.

These prove that relationships are canonical history between people, promises
are claims on the future, neither may be invented by the narrator, participant
perspectives may differ without becoming objective truth, promise state changes
never rewrite the original wording/source, fulfillment/breach/release are
evidence-backed, inheritance/transfer require provenance, relics/World Memory
can reference a promise without mutating it, secret promises stay hidden from
unauthorized NPCs, and the Campaign Orchestrator auto-generates first-class
relationship/promise callbacks with cooldown pacing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import db
from app.campaign import (
    NarrativeContext,
    NarrativeOutput,
    build_promise_consequence_candidates,
    build_relationship_callback_candidates,
)
from app.main import app
from app.narrative_guardian import validate_narrative
from app.relationship import (
    RelationshipPromiseNPCKnowledgeRequest,
    evaluate_promise_resolution,
    project_relationship_promise_npc_knowledge,
)

client = TestClient(app)

SOUL = "Kaelen the Star-Watcher"
OTHER = "Archivist Vael"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


def _make_portrait(soul_id: str) -> str:
    res = client.post(
        "/api/v1/visual/portraits/snapshot",
        json={
            "soul_id": soul_id,
            "label": "v1",
            "image_url": "/assets/portraits/x.png",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["portrait"]["version_id"]


def _create_relationship(**overrides) -> dict:
    payload = {
        "kinds": ["friendship"],
        "participants": [
            {"entity_type": "person", "entity_id": SOUL, "role": "participant"},
            {"entity_type": "person", "entity_id": OTHER, "role": "participant"},
        ],
        "source_type": "chronicle_event",
        "source_id": "evt_1",
        "creation_context": "They met at the Sunken Spire.",
        "visibility": "public_canon",
        "status": "active",
    }
    payload.update(overrides)
    res = client.post("/api/v1/relationships", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["relationship"]


def _create_promise(**overrides) -> dict:
    payload = {
        "promisor_entity_type": "person",
        "promisor_entity_id": SOUL,
        "promise_text": "Rowan promised to return the lantern to Mira's family.",
        "structured_meaning": {"subject": "lantern", "obligation": "return"},
        "conditions": [],
        "scope": "personal",
        "visibility": "public_canon",
        "source_type": "chronicle_event",
        "source_id": "evt_1",
        "source_authorization": "canonical_event",
        "participants": [
            {
                "participant_type": "recipient",
                "entity_type": "person",
                "entity_id": OTHER,
            }
        ],
        "inheritable": False,
        "transferable": False,
    }
    payload.update(overrides)
    res = client.post("/api/v1/promises", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["promise"]


# 1. Canonical interaction can create a relationship.
def test_canonical_interaction_creates_relationship():
    rel = _create_relationship()
    assert rel["relationship_id"]
    assert rel["source_refs"][0]["source_type"] == "chronicle_event"
    assert {p["entity_id"] for p in rel["participants"]} == {SOUL, OTHER}


# 2. The narrator cannot create a relationship.
def test_narrator_cannot_create_relationship():
    context = NarrativeContext(
        soul_id=SOUL,
        campaign_id="north_star_campaign",
        session_id="sess_1",
        opportunity_type="relationship_callback",
        allowed_claims=[],
    )
    output = NarrativeOutput(
        prose="You and Mira were always friends.",
        provider="test",
        provider_model="test-model",
    )
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_relationship" for i in report.issues)


# 3/4. Participant perspectives may differ without becoming objective fact.
def test_participant_perspectives_may_differ_without_becoming_fact():
    rel = _create_relationship()
    kinds_before = list(rel["kinds"])

    client.post(
        f"/api/v1/relationships/{rel['relationship_id']}/perspectives",
        json={
            "entity_type": "person",
            "entity_id": SOUL,
            "kind": "friendship",
            "view": "Rowan considers Mira a friend.",
            "is_canonical_interaction": False,
            "visibility": "public_canon",
        },
    )
    client.post(
        f"/api/v1/relationships/{rel['relationship_id']}/perspectives",
        json={
            "entity_type": "person",
            "entity_id": OTHER,
            "kind": "alliance",
            "view": "Mira considers Rowan an ally but not a friend.",
            "is_canonical_interaction": False,
            "visibility": "public_canon",
        },
    )
    fetched = client.get(f"/api/v1/relationships/{rel['relationship_id']}").json()[
        "relationship"
    ]

    views = {p["entity_id"]: p["kind"] for p in fetched["perspectives"]}
    assert views[SOUL] == "friendship"
    assert views[OTHER] == "alliance"
    # Perspectives never mutate the canonical relationship kinds.
    assert fetched["kinds"] == kinds_before


# 5. Promise requires canonical/authorized source.
def test_promise_fulfillment_without_evidence_is_rejected():
    promise = _create_promise()
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition",
        json={"new_state": "fulfilled", "reason": "no evidence"},
    )
    assert res.status_code == 400
    assert "requires canonical evidence" in res.json()["detail"]


# 6. Original promise remains immutable after state changes.
def test_original_promise_remains_immutable_after_state_change():
    promise = _create_promise()
    original_text = promise["promise_text"]
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition",
        json={
            "new_state": "fulfilled",
            "evidence_type": "chronicle_event",
            "evidence_id": "evt_return",
            "reason": "The lantern was returned.",
        },
    )
    assert res.status_code == 200, res.text
    updated = res.json()["promise"]
    assert updated["promise_text"] == original_text
    assert updated["lifecycle_state"] == "fulfilled"
    assert updated["state_history"][-1]["new_state"] == "fulfilled"


# 7/8. Promise can be fulfilled or broken with evidence.
def test_promise_can_be_fulfilled_or_broken_with_evidence():
    fulfilled = _create_promise()
    res = client.post(
        f"/api/v1/promises/{fulfilled['promise_id']}/transition",
        json={
            "new_state": "fulfilled",
            "evidence_type": "chronicle_event",
            "evidence_id": "evt_fulfilled",
        },
    )
    assert res.json()["promise"]["lifecycle_state"] == "fulfilled"

    broken = _create_promise()
    res = client.post(
        f"/api/v1/promises/{broken['promise_id']}/transition",
        json={
            "new_state": "broken",
            "evidence_type": "chronicle_event",
            "evidence_id": "evt_broken",
        },
    )
    assert res.json()["promise"]["lifecycle_state"] == "broken"


# 9. Ambiguous evidence remains disputed/unresolved.
def test_ambiguous_evidence_remains_disputed():
    promise = _create_promise()
    verdict = evaluate_promise_resolution(promise, "fulfilled")
    assert verdict["verdict"] == "disputed"
    assert verdict["authorized"] is False


# 10. Promise release is historical, not deletion.
def test_promise_release_is_historical_not_deletion():
    promise = _create_promise(conditions=["subjective negotiated condition"])
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition",
        json={
            "new_state": "released",
            "evidence_type": "player_authorized",
            "reason": "The obligation was released by mutual agreement.",
        },
    )
    assert res.status_code == 200, res.text
    updated = res.json()["promise"]
    assert updated["lifecycle_state"] == "released"
    assert updated["state_history"][-1]["new_state"] == "released"
    # Still retrievable; the original record was not deleted.
    fetched = client.get(f"/api/v1/promises/{promise['promise_id']}").json()["promise"]
    assert fetched["promise_text"] == promise["promise_text"]


# 11/12. Inherited/transferred promises require provenance.
def test_inherited_promise_requires_provenance():
    promise = _create_promise(inheritable=True)
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition",
        json={"new_state": "inherited", "reason": "drama"},
    )
    assert res.status_code == 400


def test_transferred_promise_requires_provenance():
    promise = _create_promise(transferable=True)
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition",
        json={"new_state": "transferred", "reason": "drama"},
    )
    assert res.status_code == 400


# 13. Another Aspect does not inherit obligation automatically.
def test_another_aspect_does_not_inherit_obligation_automatically():
    _create_promise(promisor_entity_id=SOUL, inheritable=True)
    res = client.get(
        "/api/v1/promises/query?entity_type=person&entity_id=Wandering%20Aspect"
    ).json()
    assert res["promises"] == []


# 14/15. A relic can reference a promise without changing promise canon.
def test_relic_references_promise_without_changing_canon():
    promise = _create_promise()
    res = client.post(
        f"/api/v1/promises/{promise['promise_id']}/links",
        json={
            "link_type": "relic",
            "entity_type": "relic",
            "entity_id": "relic_compass_01",
        },
    )
    assert res.status_code == 200, res.text
    linked = res.json()["promise"]
    assert linked["entity_links"][0]["entity_id"] == "relic_compass_01"
    assert linked["promise_text"] == promise["promise_text"]

    # Relic Recognition can read the promise as evidence.
    res = client.get(
        "/api/v1/promises/query?entity_type=relic&entity_id=relic_compass_01"
    )
    assert res.status_code == 200, res.text
    assert any(p["promise_id"] == promise["promise_id"] for p in res.json()["promises"])


# 16/17. Relationship/promise can become World Memory without mutating source.
def test_world_memory_derives_from_promise_without_mutating_source():
    promise = _create_promise()
    portrait_id = _make_portrait(SOUL)
    # Give the promisor a memory object so World Memory has canonical claims.
    client.post(
        "/api/v1/visual/memory-objects/compile",
        json={
            "event_id": "evt_1",
            "event_title": "The Lantern Vow",
            "participants": [
                {
                    "soul_id": SOUL,
                    "character_name": SOUL,
                    "portrait_version_id": portrait_id,
                    "role_in_event": "Focus",
                    "real_person_tag_opt_in": False,
                }
            ],
            "location_environment": "The Sunken Spire",
            "relics_involved": [],
            "emotional_tone": "Solemn vow",
            "action_composition": f"{SOUL} swore to return the lantern.",
            "lasting_consequence": "The promise passed into legend.",
            "privacy_consent_scope": "public_canon",
        },
    )
    res = client.post(
        "/api/v1/world-memory/compile",
        json={
            "subject_entity_type": "person",
            "subject_entity_id": SOUL,
            "memory_form": "legend",
            "interpretation_type": "exaggerated",
        },
    )
    assert res.status_code == 200, res.text
    memory = res.json()["memory"]
    source_types = {ref["source_type"] for ref in memory["source_refs"]}
    assert "promise" in source_types
    # The promise itself is unchanged by the World Memory derivation.
    fetched = client.get(f"/api/v1/promises/{promise['promise_id']}").json()["promise"]
    assert fetched["promise_text"] == promise["promise_text"]
    assert fetched["lifecycle_state"] == "made"


# 18. Secret promise is excluded from unauthorized NPC knowledge.
def test_secret_promise_excluded_from_unauthorized_npc_knowledge():
    _create_promise(visibility="secret", promise_text="A hidden oath.")
    npc = RelationshipPromiseNPCKnowledgeRequest(
        subject_entity_type="person",
        subject_entity_id=SOUL,
        social_role="commoner",
        direct_relationship=False,
        secrecy_aware=False,
    )
    projection = project_relationship_promise_npc_knowledge(
        subject_entity_type="person",
        subject_entity_id=SOUL,
        npc=npc,
        relationships=[],
        promises=db.list_promise_records(),
    )
    assert projection.promises == []


# 19. Legitimate public promise is visible to an NPC.
def test_public_promise_visible_to_npc():
    _create_promise(visibility="public_canon", promise_text="A public oath.")
    npc = RelationshipPromiseNPCKnowledgeRequest(
        subject_entity_type="person",
        subject_entity_id=SOUL,
        social_role="commoner",
    )
    projection = project_relationship_promise_npc_knowledge(
        subject_entity_type="person",
        subject_entity_id=SOUL,
        npc=npc,
        relationships=[],
        promises=db.list_promise_records(),
    )
    assert any(
        p.promise and p.promise.promise_text == "A public oath."
        for p in projection.promises
    )


# 20/21/22. Orchestrator auto-generates first-class callbacks with cooldown.
def _start_session():
    res = client.post("/api/v1/campaign/session", json={"soul_id": SOUL})
    assert res.status_code == 200, res.text
    return res.json()["session"]


def _evaluate(session_id: str) -> dict:
    res = client.post(
        "/api/v1/campaign/opportunities/evaluate",
        json={"session_id": session_id, "include_encounter": True},
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_orchestrator_auto_generates_relationship_and_promise_callbacks():
    session = _start_session()
    _create_relationship()
    _create_promise()

    result = _evaluate(session["session_id"])
    types = {o["opportunity_type"] for o in result["opportunities"]}
    assert "relationship_callback" in types
    assert "promise_consequence" in types

    rel_cb = next(
        o
        for o in result["opportunities"]
        if o["opportunity_type"] == "relationship_callback"
    )
    assert any(e["source_type"] == "relationship" for e in rel_cb["source_evidence"])


def test_promise_callback_cooldown_prevents_spam():
    session = _start_session()
    _create_promise()
    result = _evaluate(session["session_id"])
    promise_cb = next(
        o
        for o in result["opportunities"]
        if o["opportunity_type"] == "promise_consequence"
    )
    client.post(
        f"/api/v1/campaign/opportunities/{promise_cb['opportunity_id']}/resolve",
        json={},
    )
    re_eval = _evaluate(session["session_id"])
    reoffered = [
        o
        for o in re_eval["opportunities"]
        if o["opportunity_type"] == "promise_consequence"
    ]
    assert reoffered == []


# 23. Soulkeeper context receives only authorized relationship facts.
def test_narrative_context_receives_only_authorized_relationship_facts():
    from app.narrative_context_compiler import compile_narrative_context

    session = {
        "session_id": "sess_1",
        "campaign_id": "north_star_campaign",
        "soul_id": SOUL,
    }
    opportunity = {
        "opportunity_id": "opp_1",
        "session_id": "sess_1",
        "opportunity_type": "relationship_callback",
        "source_evidence": [
            {
                "source_type": "relationship",
                "source_id": "rel_1",
                "note": "A friendship relationship exists.",
            }
        ],
        "involved_entities": [{"entity_type": "relationship", "entity_id": "rel_1"}],
    }
    context = compile_narrative_context(opportunity, session)
    assert "A friendship relationship exists." in context.allowed_claims
    assert context.relationships == ["A friendship relationship exists."]


# 24. Soulkeeper cannot change promise wording/state (domain + guardian).
def test_soulkeeper_cannot_change_promise_wording_or_state():
    # Deciding a new promise outcome without domain evidence is blocked.
    outcome = NarrativeOutput(
        prose="The promise was fulfilled.",
        provider="test",
        provider_model="test-model",
    )
    report = validate_narrative(
        NarrativeContext(
            soul_id=SOUL,
            campaign_id="north_star_campaign",
            session_id="sess_1",
            opportunity_type="seed_echo",
            allowed_claims=[],
        ),
        outcome,
    )
    assert report.verdict == "block"
    assert any(i.code == "promise_state_authority" for i in report.issues)


# 25. Relationship perspective remains separate from canonical interaction.
def test_relationship_perspective_separate_from_canonical_interaction():
    rel = _create_relationship()
    client.post(
        f"/api/v1/relationships/{rel['relationship_id']}/perspectives",
        json={
            "entity_type": "person",
            "entity_id": SOUL,
            "kind": "friendship",
            "view": "A private, non-canonical feeling.",
            "is_canonical_interaction": False,
            "visibility": "private",
        },
    )
    fetched = client.get(f"/api/v1/relationships/{rel['relationship_id']}").json()[
        "relationship"
    ]
    assert fetched["kinds"] == ["friendship"]
    assert fetched["perspectives"][0]["is_canonical_interaction"] is False


# 27. Public APIs do not leak private relationship/promise metadata.
def test_public_apis_do_not_leak_private_relationship_or_promise():
    _create_relationship(visibility="private")
    _create_promise(visibility="secret", promise_text="A secret promise.")

    stranger = "Wandering Aspect"
    rel_list = client.get(f"/api/v1/relationships?viewer_soul_id={stranger}").json()[
        "relationships"
    ]
    # A private relationship is excluded from an uninvolved third party.
    assert not any(
        any(p["entity_id"] == SOUL for p in r["participants"]) for r in rel_list
    )

    promise_list = client.get(f"/api/v1/promises?viewer_soul_id={stranger}").json()[
        "promises"
    ]
    # The secret promise is excluded from an unauthorized viewer's list.
    assert not any(p["promise_text"] == "A secret promise." for p in promise_list)


# 28. Historical relationship state remains inspectable.
def test_historical_relationship_state_remains_inspectable():
    rel = _create_relationship()
    client.post(
        f"/api/v1/relationships/{rel['relationship_id']}/events",
        json={
            "event_type": "met",
            "source_type": "chronicle_event",
            "source_id": "evt_1",
            "summary": "First meeting.",
        },
    )
    client.post(
        f"/api/v1/relationships/{rel['relationship_id']}/events",
        json={
            "event_type": "allied",
            "source_type": "chronicle_event",
            "source_id": "evt_2",
            "summary": "They allied.",
        },
    )
    fetched = client.get(f"/api/v1/relationships/{rel['relationship_id']}").json()[
        "relationship"
    ]
    assert [e["event_type"] for e in fetched["events"]] == ["met", "allied"]


# 29. Duplicate state transition is idempotent.
def test_duplicate_promise_transition_is_idempotent():
    promise = _create_promise()
    payload = {"new_state": "acknowledged"}
    first = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition", json=payload
    ).json()["promise"]
    second = client.post(
        f"/api/v1/promises/{promise['promise_id']}/transition", json=payload
    ).json()["promise"]
    assert first["lifecycle_state"] == second["lifecycle_state"] == "acknowledged"
    assert len(second["state_history"]) == len(first["state_history"]) == 1


# Pure builder coverage.
def test_pure_builders_return_empty_for_empty_state():
    assert build_relationship_callback_candidates([], SOUL) == []
    assert build_promise_consequence_candidates([], SOUL) == []
