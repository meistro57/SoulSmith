# backend/tests/test_narrative_engine.py
"""Phase 18: Soulkeeper Narrative Engine & Provider Runtime tests.

These prove the provider runtime turns authorized, provenance-backed campaign
state into structured player-facing story *without* ever inventing canon. They
cover the NarrativeContext contract, the deterministic narrative Guardian,
bounded retry/fallback, provider metadata, scene continuity, and the API
surfaces, while keeping the deterministic mock first-class.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import campaign_orchestrator
from app.campaign import (
    NARRATIVE_TEMPLATE_VERSION,
    NarrativeContext,
    NarrativeDialogue,
    NarrativeOutput,
)
from app.campaign_provider import (
    MockCampaignNarrativeProvider,
    get_campaign_provider,
)
from app.main import app
from app.narrative_context_compiler import (
    compile_narrative_context,
    compile_npc_narrative_context,
    context_stats,
)
from app.narrative_guardian import validate_narrative
from app.narrative_runtime import NarrativeRuntime

client = TestClient(app)

SOUL = "Kaelen the Star-Watcher"


@pytest.fixture(autouse=True)
def isolate_assets(monkeypatch, tmp_path):
    monkeypatch.setenv("SOULSMITH_ASSET_ROOT", str(tmp_path / "assets"))


def _ctx(**overrides) -> NarrativeContext:
    base = {
        "soul_id": SOUL,
        "campaign_id": "north_star_campaign",
        "session_id": "sess_1",
        "opportunity_type": "seed_echo",
        "allowed_claims": ["Symbol 'Ash' at stage 'planted'."],
        "source_evidence": [],
        "visible_entities": [],
        "provenance_ids": ["seed:1"],
    }
    base.update(overrides)
    return NarrativeContext(**base)


def _out(
    prose: str = "The Chronicle offers this much.", **overrides
) -> NarrativeOutput:
    base = {
        "prose": prose,
        "provider": "test",
        "provider_model": "test-model",
    }
    base.update(overrides)
    return NarrativeOutput(**base)


# --- NarrativeContext contract -------------------------------------------------


def test_context_contains_only_authorized_facts():
    opportunity = {
        "opportunity_id": "opp_1",
        "session_id": "sess_1",
        "opportunity_type": "seed_echo",
        "eligibility_rule": "Seed exists.",
        "source_evidence": [
            {"source_type": "seed", "source_id": "1", "note": "Symbol 'Ash'."}
        ],
        "involved_entities": [{"entity_type": "seed", "entity_id": "1"}],
        "visibility_scope": "public_canon",
    }
    session = {
        "session_id": "sess_1",
        "campaign_id": "north_star_campaign",
        "soul_id": SOUL,
    }
    context = compile_narrative_context(opportunity, session)
    assert context.allowed_claims == ["Symbol 'Ash'."]
    assert context.provenance_ids == ["seed:1"]
    # Bounded continuity, not a whole-chronicle dump.
    assert context.continuity is not None
    assert len(context.continuity.recent_visible_actions) <= 3


def test_context_excludes_private_facts():
    context = _ctx(forbidden_facts=["secret_sanctum"])
    output = _out(prose="You enter the secret_sanctum.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "private_leak" for i in report.issues)


class _Entry:
    def __init__(self, memory_id, title, narrative, fidelity):
        self.memory = _Memory(memory_id, title, narrative)
        self.fidelity = fidelity
        self.canonical_truth_visible = False
        self.reason = "local tradition"


class _Memory:
    def __init__(self, memory_id, title, narrative):
        self.memory_id = memory_id
        self.title = title
        self.narrative = narrative


class _Projection:
    def __init__(self):
        self.entries = [
            _Entry(
                "wm_1",
                "The Sunken Spire",
                "The village says a promise was sworn.",
                "distorted",
            )
        ]


def test_npc_context_uses_projection_not_omniscient_chronicle():
    opportunity = {
        "opportunity_id": "opp_1",
        "session_id": "sess_1",
        "opportunity_type": "npc_historical_reaction",
        "source_evidence": [],
        "involved_entities": [{"entity_type": "world_memory", "entity_id": "wm_1"}],
    }
    session = {
        "session_id": "sess_1",
        "campaign_id": "north_star_campaign",
        "soul_id": SOUL,
    }
    context = compile_npc_narrative_context(
        opportunity, session, npc_projection=_Projection()
    )
    assert "npc_knowledge_scoped" in context.constraints
    assert context.npc_knowledge[0]["memory_id"] == "wm_1"
    assert context.npc_knowledge[0]["fidelity"] == "distorted"


# --- Narrative Guardian --------------------------------------------------------


def test_validator_blocks_unknown_participant():
    context = _ctx(
        visible_entities=[{"entity_type": "soul", "entity_id": SOUL, "label": SOUL}]
    )
    output = _out(
        dialogue=[NarrativeDialogue(speaker="Mysterious Stranger", line="I know you.")]
    )
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "unknown_participant" for i in report.issues)


def test_validator_blocks_invented_prior_event():
    context = _ctx(allowed_claims=[])
    output = _out(prose="You remember the burning of the old archive.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_prior_event" for i in report.issues)


def test_validator_blocks_invented_duration():
    context = _ctx(allowed_claims=["Symbol 'Ash'."])
    output = _out(prose="You have carried this for 300 years.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_duration" for i in report.issues)


def test_validator_blocks_invented_relic_ability():
    context = _ctx(
        opportunity_type="relic_memory", relic_state=None, permitted_relic_knowledge=[]
    )
    output = _out(prose="The relic can summon storms at will.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_relic_ability" for i in report.issues)


def test_validator_blocks_thread_truth_promotion():
    context = _ctx(opportunity_type="seed_echo", allowed_claims=[])
    output = _out(prose="The thread is true now.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "thread_truth_promoted" for i in report.issues)


def test_validator_blocks_invented_integration_event():
    context = _ctx(opportunity_type="seed_echo", allowed_claims=[])
    output = _out(prose="An Integration Event has occurred.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "invented_integration" for i in report.issues)


def test_validator_preserves_perspective_boundary():
    context = _ctx(constraints=["perspective_boundary"], allowed_claims=[])
    output = _out(prose="In fact, it truly was a promise.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "perspective_violation" for i in report.issues)


def test_validator_blocks_psychological_authority():
    context = _ctx()
    output = _out(prose="Your soul is destined for the river.")
    report = validate_narrative(context, output)
    assert report.verdict == "block"
    assert any(i.code == "psychological_authority" for i in report.issues)


def test_validator_retries_on_undeclared_fact():
    context = _ctx(allowed_claims=[])
    output = _out(prose="It is known that the sky fell.")
    report = validate_narrative(context, output)
    assert report.verdict == "retry"
    assert report.correction


def test_validator_passes_authorized_output():
    context = _ctx(allowed_claims=["Symbol 'Ash'."])
    output = _out(prose="The Chronicle offers this much: Symbol 'Ash'.")
    report = validate_narrative(context, output)
    assert report.verdict == "pass"


# --- Provider runtime ----------------------------------------------------------


class _RetryThenPass:
    provider = "test"
    provider_model = "test-model"
    narration_source = "test"

    def __init__(self):
        self.calls = 0

    def narrate(self, context):
        self.calls += 1
        if self.calls == 1:
            return _out(prose="It is known that the sky fell.")
        return _out(prose="The Chronicle offers this much.")


class _AlwaysBlock:
    provider = "test"
    provider_model = "test-model"
    narration_source = "test"

    def narrate(self, context):
        return _out(
            dialogue=[NarrativeDialogue(speaker="Stranger", line="I know you.")]
        )


def test_retry_uses_same_authoritative_facts():
    context = _ctx(allowed_claims=[])
    claims_before = list(context.allowed_claims)
    result = NarrativeRuntime(provider=_RetryThenPass(), max_retries=2).narrate(context)
    assert result.failure is None
    assert result.validation.verdict == "pass"
    assert result.metadata["retry_count"] == 1
    # Corrections were appended; authoritative facts were never widened.
    assert context.allowed_claims == claims_before
    assert context.corrections


def test_retry_exhaustion_falls_back_safely():
    context = _ctx(allowed_claims=["Symbol 'Ash'."])
    result = NarrativeRuntime(provider=_AlwaysBlock(), max_retries=1).narrate(context)
    assert result.used_fallback is True
    assert result.output.provider == "mock"
    assert result.output.prose  # safe deterministic fallback


def test_provider_error_returns_graceful_failure():
    class _Boom:
        provider = "test"
        provider_model = "test-model"
        narration_source = "test"

        def narrate(self, context):
            raise RuntimeError("provider down")

    result = NarrativeRuntime(provider=_Boom(), max_retries=1).narrate(_ctx())
    assert result.output is None
    assert result.failure is not None


def test_malformed_structured_output_rejected():
    from app.campaign_provider import _parse_provider_content

    with pytest.raises(RuntimeError):
        _parse_provider_content("not-json", _ctx(), "test", "test-model")


def test_deterministic_mock_is_stable():
    mock = MockCampaignNarrativeProvider()
    context = _ctx(allowed_claims=["Symbol 'Ash'."])
    assert mock.narrate(context).prose == mock.narrate(context).prose


def test_provider_metadata_and_template_recorded():
    result = NarrativeRuntime(provider=_RetryThenPass(), max_retries=2).narrate(_ctx())
    assert result.metadata["template_version"] == NARRATIVE_TEMPLATE_VERSION
    assert result.metadata["provider"] == "test"
    assert result.metadata["provider_model"] == "test-model"


# --- Context/continuity --------------------------------------------------------


def test_context_compiler_limits_unrelated_material():
    opportunity = {
        "opportunity_id": "opp_1",
        "session_id": "sess_1",
        "opportunity_type": "probable_path_echo",
        "source_evidence": [
            {
                "source_type": "probable_path",
                "source_id": "1",
                "note": "Unchosen branch.",
            }
        ],
        "involved_entities": [],
    }
    session = {
        "session_id": "sess_1",
        "campaign_id": "north_star_campaign",
        "soul_id": SOUL,
    }
    context = compile_narrative_context(opportunity, session)
    stats = context_stats(context)
    # Only the single authorized source is compiled; no whole-Chronicle dump.
    assert stats["source_count"] == 1
    assert stats["allowed_claim_count"] == 1
    assert "recent_visible_actions" not in stats  # stats are non-sensitive summaries


def test_scene_continuity_reconstructs_from_structured_state():
    # Continuity is built from structured transition/event state, not chat logs.
    opportunity = {
        "opportunity_id": "opp_1",
        "session_id": "sess_1",
        "opportunity_type": "seed_echo",
        "source_evidence": [],
        "involved_entities": [
            {"entity_type": "location", "entity_id": "spire", "label": "The Spire"}
        ],
    }
    session = {
        "session_id": "sess_1",
        "campaign_id": "north_star_campaign",
        "soul_id": SOUL,
    }
    context = compile_narrative_context(opportunity, session)
    assert context.continuity.location == "The Spire"


# --- HTTP integration ----------------------------------------------------------


def _start(soul_id: str = SOUL) -> dict:
    res = client.post("/api/v1/campaign/session", json={"soul_id": soul_id})
    assert res.status_code == 200, res.text
    return res.json()["session"]


def _scene_and_commit(session_id: str, thread_d4: int = 2) -> dict:
    read = client.post(
        "/api/v1/dice/interpret",
        json={
            "d20": 17,
            "d12": 9,
            "d10": 5,
            "percentile": 70,
            "d8": 3,
            "d6": 4,
            "d4": thread_d4,
            "grammar_version": "1.0.0",
        },
    ).json()
    scene = client.post(
        "/api/v1/scenes/resolve",
        json={
            "dice_read": read,
            "chosen_approach": "Guile",
            "resonance_spent": 1,
            "strain_accepted": 0,
            "player_intent": "I notice a faint symbol.",
            "soul_name": SOUL,
            "resources": {"resonance": 3, "strain": 0, "thread_count": 1},
        },
    ).json()
    return client.post(
        "/api/v1/campaign/commit",
        json={"session_id": session_id, "event_id": scene["event_id"]},
    ).json()


def test_provider_timeout_does_not_corrupt_transition(monkeypatch):
    import httpx

    session = _start()
    commit = _scene_and_commit(session["session_id"])
    probable = next(
        o
        for o in commit["opportunities"]
        if o["opportunity_type"] == "probable_path_echo"
    )

    class _TimeoutProvider:
        provider = "test"
        provider_model = "test-model"
        narration_source = "test"

        def narrate(self, context):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(
        campaign_orchestrator, "get_campaign_provider", lambda: _TimeoutProvider()
    )
    res = client.post(
        f"/api/v1/campaign/opportunities/{probable['opportunity_id']}/resolve", json={}
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["transition"]["provider_failure"] is not None
    assert body["transition"]["canonical_change"] is False


class _VaryingProvider:
    provider = "test"
    provider_model = "test-model"
    narration_source = "test"

    def __init__(self):
        self.n = 0

    def narrate(self, context):
        self.n += 1
        return NarrativeOutput(
            prose=f"Phrasing {self.n}.",
            claims=list(context.allowed_claims),
            provider=self.provider,
            provider_model=self.provider_model,
        )


def test_regeneration_changes_wording_without_changing_state(monkeypatch):
    session = _start()
    commit = _scene_and_commit(session["session_id"])
    probable = next(
        o
        for o in commit["opportunities"]
        if o["opportunity_type"] == "probable_path_echo"
    )
    opp_id = probable["opportunity_id"]

    before = client.get(f"/api/v1/campaign/opportunities/{opp_id}/inspect").json()
    monkeypatch.setattr(
        campaign_orchestrator, "get_campaign_provider", lambda: _VaryingProvider()
    )
    regen = client.post(f"/api/v1/campaign/opportunities/{opp_id}/regenerate").json()
    after = client.get(f"/api/v1/campaign/opportunities/{opp_id}/inspect").json()

    assert regen["canonical_state"] == before["lifecycle_state"]
    assert after["lifecycle_state"] == before["lifecycle_state"]
    assert regen["narration"]["prose"] == "Phrasing 1."

    generations = client.get(
        f"/api/v1/campaign/opportunities/{opp_id}/narrative"
    ).json()["generations"]
    assert generations
    assert generations[0]["template_version"] == NARRATIVE_TEMPLATE_VERSION


def test_narrative_status_and_provider_selection():
    status = client.get("/api/v1/campaign/narrative/status").json()
    assert status["selected"] in ("mock", "openai_compatible")
    assert status["template_version"] == NARRATIVE_TEMPLATE_VERSION

    selected = client.post(
        "/api/v1/campaign/narrative/select", json={"provider": "mock"}
    ).json()
    assert selected["effective"] == "mock"


def test_default_provider_is_mock():
    provider = get_campaign_provider()
    assert provider.provider == "mock"
    assert provider.narration_source == "deterministic"
