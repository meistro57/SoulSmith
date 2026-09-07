# backend/app/campaign.py
"""
SoulSmith Phase 17: Campaign Orchestrator models and deterministic helpers.

> THE ORCHESTRATOR DECIDES WHAT GETS AN OPPORTUNITY TO ACT NEXT. IT DOES NOT
> DECIDE WHAT THE PLAYER'S STORY MEANS.

This module holds the persistent data models for the continuous playable loop
plus the pure, deterministic eligibility and pacing helpers that run *before*
any narration. The orchestrator service (``campaign_orchestrator.py``)
coordinates existing domain systems through their established contracts; it
never re-implements their rules. Narration is produced behind the provider
abstraction in ``campaign_provider.py`` from a consent-safe ``NarrativeContext``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CAMPAIGN_COMPILER_VERSION = "1.0.0"

# Version of the Soulkeeper narrative template/system prompt used by real
# providers. Changing this must never rewrite prior canonical events or
# historical generated prose records.
NARRATIVE_TEMPLATE_VERSION = "1.0.0"

OpportunityType = Literal[
    "new_encounter",
    "seed_echo",
    "recurring_symbol",
    "unresolved_question_callback",
    "relationship_callback",
    "promise_consequence",
    "relic_memory",
    "relic_awakening_candidate",
    "probable_path_echo",
    "cross_aspect_echo",
    "npc_historical_reaction",
    "group_memory_callback",
    "world_memory_legend_encounter",
    "integration_candidate",
    "recognition",
    "reflection_prompt",
    "chronicle_painting_eligibility",
]

# The bounded, extensible vocabulary of opportunity types. New types may be
# added without changing the model, but the orchestrator only ever emits types
# for which a deterministic eligibility rule exists.
OPPORTUNITY_TYPES: frozenset[str] = frozenset(
    {
        "new_encounter",
        "seed_echo",
        "recurring_symbol",
        "unresolved_question_callback",
        "relationship_callback",
        "promise_consequence",
        "relic_memory",
        "relic_awakening_candidate",
        "probable_path_echo",
        "cross_aspect_echo",
        "npc_historical_reaction",
        "group_memory_callback",
        "world_memory_legend_encounter",
        "integration_candidate",
        "recognition",
        "reflection_prompt",
        "chronicle_painting_eligibility",
    }
)

ParticipationKind = Literal["optional", "passive", "player_triggered"]
LifecycleState = Literal[
    "eligible", "selected", "resolved", "rejected", "postponed", "hidden", "expired"
]
UrgencyClass = Literal["low", "normal", "high"]
RecognitionDecisionKind = Literal[
    "recognize", "reject", "rename", "reinterpret", "postpone", "hide"
]

# Pacing windows: how many of the session's most recent resolutions are
# considered "hot" for a given opportunity type. A candidate whose cooldown key
# appears in that window is not re-offered. This is count-based (not wall-clock)
# so it is deterministic and offline-testable.
COOLDOWN_WINDOW: dict[str, int] = {
    "new_encounter": 0,
    "seed_echo": 1,
    "recurring_symbol": 1,
    "unresolved_question_callback": 2,
    "relationship_callback": 3,
    "promise_consequence": 3,
    "relic_memory": 2,
    "relic_awakening_candidate": 1,
    "probable_path_echo": 2,
    "cross_aspect_echo": 3,
    "npc_historical_reaction": 2,
    "group_memory_callback": 2,
    "world_memory_legend_encounter": 2,
    "integration_candidate": 1,
    "recognition": 1,
    "reflection_prompt": 1,
    "chronicle_painting_eligibility": 1,
}


class SourceEvidence(BaseModel):
    """A machine-readable provenance link for a callback or opportunity."""

    source_type: str
    source_id: str
    claim_kind: str = "canonical_fact"
    note: str | None = None


class InvolvedEntity(BaseModel):
    entity_type: str
    entity_id: str
    label: str | None = None


class RecognitionDecision(BaseModel):
    """Player-controlled decision on a proposed pattern interpretation."""

    decision: RecognitionDecisionKind
    new_name: str | None = None
    reinterpretation: str | None = None


class CampaignOpportunityModel(BaseModel):
    opportunity_id: str
    session_id: str
    opportunity_type: OpportunityType
    eligibility_rule: str
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    involved_entities: list[InvolvedEntity] = Field(default_factory=list)
    visibility_scope: str = "public_canon"
    urgency_class: UrgencyClass = "normal"
    participation: ParticipationKind = "optional"
    lifecycle_state: LifecycleState = "eligible"
    cooldown_key: str | None = None
    cooldown_until: str | None = None
    domain_action: str = "none"
    domain_action_payload: dict[str, Any] = Field(default_factory=dict)
    reasoning: dict[str, Any] = Field(default_factory=dict)
    narration: str | None = None
    narration_source: str = "deterministic"
    created_at: str | None = None
    resolved_at: str | None = None


class CampaignReactionModel(BaseModel):
    reaction_id: str
    transition_id: str
    system_name: str
    result_kind: Literal[
        "no_action",
        "candidate_created",
        "state_updated",
        "player_review_required",
        "future_opportunity_scheduled",
    ]
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class CampaignTransitionModel(BaseModel):
    transition_id: str
    session_id: str
    opportunity_id: str | None = None
    canonical_event_id: str | None = None
    transition_type: str
    systems_invoked: list[str] = Field(default_factory=list)
    outcomes: list[dict[str, Any]] = Field(default_factory=list)
    reactions: list[CampaignReactionModel] = Field(default_factory=list)
    canonical_change: bool = False
    provider_failure: str | None = None
    rejected_invalid_transition: bool = False
    created_at: str | None = None


class CampaignSessionModel(BaseModel):
    session_id: str
    campaign_id: str
    soul_id: str
    constellation_id: str | None = None
    status: str = "active"
    current_opportunity_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class NarrativeDialogue(BaseModel):
    """A single attributable line of dialogue. The speaker must already be
    visible to the current scene; the runtime never invents participants."""

    speaker: str
    line: str
    kind: str = "spoken"  # spoken | thought | inscription | song | rumor


class NarrativeQuestion(BaseModel):
    """A player-facing prompt/question. It must not change structured choices."""

    prompt: str
    kind: str = "open"  # open | choice | reflection
    choice_hint: str | None = None


class NarrativeFlavorLine(BaseModel):
    text: str
    kind: str = "sensory"  # sensory | connective | atmosphere | aside


class NarrativePresentationCue(BaseModel):
    kind: str
    emphasis: str | None = None


class NarrativeContinuity(BaseModel):
    """Explicit, structured scene continuity. This is never raw chat history;
    it is the smallest set of SoulSmith-owned state needed to avoid amnesia."""

    location: str | None = None
    environment: str | None = None
    current_participants: list[str] = Field(default_factory=list)
    prior_transition_summary: str | None = None
    active_unresolved_opportunity: str | None = None
    recent_visible_actions: list[str] = Field(default_factory=list)
    current_relics: list[str] = Field(default_factory=list)


class NarrativeContext(BaseModel):
    """Consent-safe structured context handed to the narrative provider.

    The provider only receives information the current scene is allowed to know.
    It never receives the whole database, and it may never invent facts absent
    from this context.
    """

    soul_id: str
    campaign_id: str
    session_id: str
    opportunity_type: str | None = None
    title_hint: str | None = None
    allowed_claims: list[str] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    visible_entities: list[InvolvedEntity] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    # Authorized scene facts and viewpoint.
    active_aspect: str | None = None
    location: str | None = None
    environment: str | None = None
    participants: list[InvolvedEntity] = Field(default_factory=list)
    knowledge_boundaries: dict[str, Any] = Field(default_factory=dict)

    # Already-canonical, visible relationships/promises (never invented).
    relationships: list[str] = Field(default_factory=list)
    promises: list[str] = Field(default_factory=list)

    # Relic state: only what the scene is permitted to know.
    relic_state: dict[str, Any] | None = None
    permitted_relic_knowledge: list[str] = Field(default_factory=list)

    # Seeds / questions / symbols that may be echoed.
    seeds: list[dict[str, Any]] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)

    # Thread evidence only when the current opportunity allows it.
    thread_evidence: list[dict[str, Any]] = Field(default_factory=list)

    # World Memory / NPC knowledge projection where applicable.
    world_memory_context: list[dict[str, Any]] = Field(default_factory=list)
    npc_knowledge: list[dict[str, Any]] = Field(default_factory=list)

    # Player-visible consequences and allowed uncertainty.
    player_visible_consequences: list[str] = Field(default_factory=list)
    allowed_uncertainty: list[str] = Field(default_factory=list)

    # Style/tone hints (interpretation only, never new information).
    style: dict[str, Any] = Field(default_factory=dict)
    art_direction_refs: list[str] = Field(default_factory=list)

    # Facts explicitly forbidden/private (must never leak).
    forbidden_facts: list[str] = Field(default_factory=list)

    # Provenance ids backing every meaningful claim.
    provenance_ids: list[str] = Field(default_factory=list)

    # Scene continuity (structured, not chat history).
    continuity: NarrativeContinuity | None = None

    # Correction instructions appended by the runtime during retry; providers
    # may phrase around a gap but must not widen context on their own.
    corrections: list[str] = Field(default_factory=list)


class NarrativeOutput(BaseModel):
    """Structured provider output. ``prose`` remains the primary scene prose;
    the optional fields give the UI and validator bounded control without
    turning prose into bureaucracy."""

    title: str | None = None
    prose: str = ""
    scene_prose: str | None = None
    soulkeeper_narration: str | None = None
    dialogue: list[NarrativeDialogue] = Field(default_factory=list)
    question: NarrativeQuestion | None = None
    flavor_lines: list[str] = Field(default_factory=list)
    presentation_cues: list[NarrativePresentationCue] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    referenced_provenance_ids: list[str] = Field(default_factory=list)
    declared_uncertainty: list[str] = Field(default_factory=list)
    provider: str
    provider_model: str
    template_version: str = "1.0.0"


# Request schemas.


class StartSessionRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    campaign_id: str | None = None


class EvaluateOpportunitiesRequest(BaseModel):
    session_id: str
    include_encounter: bool = True


class ResolveOpportunityRequest(BaseModel):
    decision: str | None = None
    recognition: RecognitionDecision | None = None
    player_intent: str | None = None
    note: str | None = None


class CommitEventRequest(BaseModel):
    session_id: str
    event_id: str


class SelectNarrativeProviderRequest(BaseModel):
    provider: str = "mock"


class PreviewNarrativeContextRequest(BaseModel):
    opportunity_id: str


# Candidate shape produced by deterministic eligibility builders. The orchestrator
# enriches these with a stable id, session id, lifecycle state, and narration.
CandidateSpec = dict[str, Any]


def _evidence(
    source_type: str, source_id: str, note: str | None = None
) -> dict[str, Any]:
    return {
        "source_type": source_type,
        "source_id": source_id,
        "claim_kind": "canonical_fact",
        "note": note,
    }


def _entity(
    entity_type: str, entity_id: str, label: str | None = None
) -> dict[str, Any]:
    return {"entity_type": entity_type, "entity_id": entity_id, "label": label}


# Deterministic eligibility builders. Each takes only structured state and
# returns candidate specs (or an empty list). No narration happens here.


def build_new_encounter_candidate(soul_id: str) -> CandidateSpec | None:
    """The primary loop driver: continuing to the next encounter is always open."""
    return {
        "opportunity_type": "new_encounter",
        "eligibility_rule": "The campaign loop is always permitted to continue.",
        "source_evidence": [],
        "involved_entities": [_entity("soul", soul_id, soul_id)],
        "visibility_scope": "public_canon",
        "urgency_class": "normal",
        "participation": "player_triggered",
        "cooldown_key": "new_encounter",
        "domain_action": "await_dice",
        "domain_action_payload": {"soul_id": soul_id},
        "reasoning": {"always_eligible": True},
    }


def build_seed_echo_candidates(seeds: list[dict[str, Any]]) -> list[CandidateSpec]:
    """A planted or echoing Seed may be echoed again (Curiosity engine)."""
    candidates: list[CandidateSpec] = []
    for seed in seeds:
        stage = seed.get("stage")
        if stage in ("retired", "integrated"):
            continue
        seed_id = seed.get("id")
        symbol = seed.get("symbol")
        thread_type = seed.get("thread_type")
        candidates.append(
            {
                "opportunity_type": "seed_echo",
                "eligibility_rule": "Seed exists + not retired/integrated + cooldown satisfied.",
                "source_evidence": [
                    _evidence("seed", seed_id, f"Symbol '{symbol}' at stage '{stage}'.")
                ],
                "involved_entities": [_entity("seed", seed_id, symbol)],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "optional",
                "cooldown_key": f"seed_echo:{seed_id}",
                "domain_action": "echo_seed",
                "domain_action_payload": {
                    "seed_id": seed_id,
                    "symbol": symbol,
                    "thread_type": thread_type,
                },
                "reasoning": {"stage": stage, "echo_count": seed.get("echo_count", 1)},
            }
        )
    return candidates


def build_recurring_symbol_candidates(
    seeds: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """A symbol that has already recurred is surfaced as a passive cue."""
    candidates: list[CandidateSpec] = []
    for seed in seeds:
        if int(seed.get("echo_count", 1)) < 2:
            continue
        if seed.get("stage") in ("retired", "integrated"):
            continue
        seed_id = seed.get("id")
        symbol = seed.get("symbol")
        candidates.append(
            {
                "opportunity_type": "recurring_symbol",
                "eligibility_rule": "Seed echo_count >= 2 and not retired.",
                "source_evidence": [
                    _evidence("seed", seed_id, f"'{symbol}' has recurred.")
                ],
                "involved_entities": [_entity("seed", seed_id, symbol)],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "passive",
                "cooldown_key": f"recurring_symbol:{seed_id}",
                "domain_action": "none",
                "domain_action_payload": {"seed_id": seed_id, "symbol": symbol},
                "reasoning": {"echo_count": seed.get("echo_count", 1)},
            }
        )
    return candidates


def build_unresolved_question_candidates(
    questions: list[dict[str, Any]],
) -> list[CandidateSpec]:
    candidates: list[CandidateSpec] = []
    for question in questions:
        if question.get("status") != "open":
            continue
        qid = question.get("id")
        text = question.get("question_text")
        candidates.append(
            {
                "opportunity_type": "unresolved_question_callback",
                "eligibility_rule": "Open question exists + cooldown satisfied.",
                "source_evidence": [
                    _evidence("open_question", qid, text),
                ],
                "involved_entities": [_entity("open_question", qid, text)],
                "visibility_scope": "public_canon",
                "urgency_class": "normal",
                "participation": "optional",
                "cooldown_key": f"unresolved_question_callback:{qid}",
                "domain_action": "none",
                "domain_action_payload": {"question_id": qid},
                "reasoning": {"question_text": text},
            }
        )
    return candidates


def build_probable_path_echo_candidates(
    paths: list[dict[str, Any]],
) -> list[CandidateSpec]:
    candidates: list[CandidateSpec] = []
    for path in paths:
        if path.get("status") not in ("dormant", "echoing"):
            continue
        pid = path.get("id")
        title = path.get("path_title")
        candidates.append(
            {
                "opportunity_type": "probable_path_echo",
                "eligibility_rule": "Dormant/echoing Probable Path exists + cooldown satisfied.",
                "source_evidence": [
                    _evidence("probable_path", pid, "Unchosen branch remains potent.")
                ],
                "involved_entities": [_entity("probable_path", pid, title)],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "optional",
                "cooldown_key": f"probable_path_echo:{pid}",
                "domain_action": "none",
                "domain_action_payload": {"path_id": pid, "path_title": title},
                "reasoning": {
                    "status": path.get("status"),
                    "manifestation_type": path.get("manifestation_type"),
                },
            }
        )
    return candidates


def build_relic_memory_candidates(
    relics: list[dict[str, Any]],
    constellation: dict[str, Any] | None = None,
) -> list[CandidateSpec]:
    """A relic that predates the current Aspect may remember something they did not."""
    anchors = (constellation or {}).get("anchors", [])
    anchor_by_relic = {a.get("relic_id"): a for a in anchors if a.get("relic_id")}
    candidates: list[CandidateSpec] = []
    for relic in relics:
        if relic.get("stage") not in ("Dormant", "Remembered"):
            continue
        forms = relic.get("cross_aspect_forms") or {}
        anchor = anchor_by_relic.get(relic.get("id"))
        if not forms and not anchor:
            continue
        rid = relic.get("id")
        name = relic.get("name")
        evidence = []
        if forms:
            evidence.append(
                _evidence(
                    "relic", rid, f"Cross-Aspect forms: {', '.join(forms.keys())}."
                )
            )
        if anchor:
            evidence.append(
                _evidence(
                    "constellation_anchor",
                    anchor.get("id"),
                    "The relic is a Constellation Anchor.",
                )
            )
        candidates.append(
            {
                "opportunity_type": "relic_memory",
                "eligibility_rule": "Relic has cross-Aspect forms or is an anchor + stage Dormant/Remembered.",
                "source_evidence": evidence,
                "involved_entities": [_entity("relic", rid, name)],
                "visibility_scope": "public_canon",
                "urgency_class": "normal",
                "participation": "optional",
                "cooldown_key": f"relic_memory:{rid}",
                "domain_action": "surface_relic_memory",
                "domain_action_payload": {"relic_id": rid, "relic_name": name},
                "reasoning": {
                    "stage": relic.get("stage"),
                    "cross_aspect_form_count": len(forms),
                },
            }
        )
    return candidates


def build_relic_awakening_candidates(
    relics: list[dict[str, Any]],
    threads: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """A Remembered relic whose required Thread has reached recognition."""
    recognized_thread_types = {
        t.get("thread_type")
        for t in threads
        if t.get("status") in ("pattern_recognized",)
    }
    recognized_seed_types = {
        s.get("thread_type") for s in seeds if s.get("stage") in ("recognized",)
    }
    recognized = recognized_thread_types | recognized_seed_types
    candidates: list[CandidateSpec] = []
    for relic in relics:
        if relic.get("stage") != "Remembered":
            continue
        required = relic.get("required_thread_type")
        if not required or required not in recognized:
            continue
        rid = relic.get("id")
        name = relic.get("name")
        candidates.append(
            {
                "opportunity_type": "relic_awakening_candidate",
                "eligibility_rule": "Remembered relic + required Thread recognized (not awakened by the orchestrator).",
                "source_evidence": [
                    _evidence("relic", rid, "Relic is Remembered."),
                    _evidence(
                        "local_thread",
                        "thread:" + required,
                        f"Thread '{required}' is recognized.",
                    ),
                ],
                "involved_entities": [_entity("relic", rid, name)],
                "visibility_scope": "public_canon",
                "urgency_class": "high",
                "participation": "player_triggered",
                "cooldown_key": f"relic_awakening_candidate:{rid}",
                "domain_action": "surface_awakening",
                "domain_action_payload": {"relic_id": rid, "relic_name": name},
                "reasoning": {
                    "stage": relic.get("stage"),
                    "required_thread_type": required,
                },
            }
        )
    return candidates


def build_cross_aspect_echo_candidates(
    constellation: dict[str, Any] | None,
    current_soul_id: str,
) -> list[CandidateSpec]:
    """A shared Anchor or Bond hints at another Aspect without granting omniscience."""
    if not constellation:
        return []
    aspects = constellation.get("aspects", [])
    bonds = constellation.get("bonds", [])
    anchors = constellation.get("anchors", [])
    if len(aspects) < 2:
        return []
    current_aspect = next(
        (
            a
            for a in aspects
            if a.get("aspect_name") == current_soul_id or a.get("id") == current_soul_id
        ),
        None,
    )
    current_id = current_aspect.get("id") if current_aspect else current_soul_id
    candidates: list[CandidateSpec] = []
    for bond in bonds:
        if (
            bond.get("source_aspect_id") != current_id
            and bond.get("target_aspect_id") != current_id
        ):
            continue
        bid = bond.get("id")
        candidates.append(
            {
                "opportunity_type": "cross_aspect_echo",
                "eligibility_rule": "A Cross-Aspect Bond touches the current Aspect + cooldown satisfied.",
                "source_evidence": [
                    _evidence("cross_aspect_bond", bid, bond.get("description"))
                ],
                "involved_entities": [
                    _entity("aspect", bond.get("source_aspect_id")),
                    _entity("aspect", bond.get("target_aspect_id")),
                ],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "passive",
                "cooldown_key": f"cross_aspect_echo:{bid}",
                "domain_action": "none",
                "domain_action_payload": {"bond_id": bid},
                "reasoning": {"bond_type": bond.get("bond_type")},
            }
        )
    for anchor in anchors:
        connected = anchor.get("connected_aspect_ids") or []
        if current_id not in connected or len(connected) < 2:
            continue
        aid = anchor.get("id")
        candidates.append(
            {
                "opportunity_type": "cross_aspect_echo",
                "eligibility_rule": "A shared Constellation Anchor links the current Aspect to another + cooldown satisfied.",
                "source_evidence": [
                    _evidence("constellation_anchor", aid, anchor.get("anchor_name"))
                ],
                "involved_entities": [
                    _entity("anchor", aid, anchor.get("anchor_name"))
                ],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "passive",
                "cooldown_key": f"cross_aspect_echo:{aid}",
                "domain_action": "none",
                "domain_action_payload": {"anchor_id": aid},
                "reasoning": {"anchor_name": anchor.get("anchor_name")},
            }
        )
    return candidates


def build_npc_historical_reaction_candidates(
    world_memories: list[dict[str, Any]],
    current_soul_id: str,
) -> list[CandidateSpec]:
    """A remembered public World Memory about another subject may be known to an NPC."""
    candidates: list[CandidateSpec] = []
    for memory in world_memories:
        subject_id = memory.get("subject_entity_id")
        if subject_id == current_soul_id:
            continue
        state = memory.get("memory_state")
        if state not in ("widely_remembered", "locally_remembered", "rediscovered"):
            continue
        if memory.get("visibility") != "public_canon":
            continue
        mid = memory.get("memory_id")
        title = memory.get("title")
        candidates.append(
            {
                "opportunity_type": "npc_historical_reaction",
                "eligibility_rule": "Public, remembered World Memory about another subject + cooldown satisfied.",
                "source_evidence": [
                    _evidence("world_memory", mid, title),
                ],
                "involved_entities": [
                    _entity("world_memory", mid, title),
                    _entity(
                        memory.get("subject_entity_type"),
                        subject_id,
                        subject_id,
                    ),
                ],
                "visibility_scope": "public_canon",
                "urgency_class": "normal",
                "participation": "optional",
                "cooldown_key": f"npc_historical_reaction:{mid}",
                "domain_action": "project_npc_reaction",
                "domain_action_payload": {
                    "memory_id": mid,
                    "subject_entity_type": memory.get("subject_entity_type"),
                    "subject_entity_id": subject_id,
                    "culture": memory.get("culture") or "",
                    "era_context": memory.get("era_context") or "",
                },
                "reasoning": {
                    "memory_state": state,
                    "memory_form": memory.get("memory_form"),
                },
            }
        )
    return candidates


def build_group_memory_callback_candidates(
    group_memories: list[dict[str, Any]],
    current_soul_id: str,
) -> list[CandidateSpec]:
    """A consent-visible Group Memory the current soul participated in."""
    candidates: list[CandidateSpec] = []
    for group in group_memories:
        members = group.get("members", [])
        if not any(m.get("soul_id") == current_soul_id for m in members):
            continue
        gid = group.get("group_id")
        title = group.get("title")
        candidates.append(
            {
                "opportunity_type": "group_memory_callback",
                "eligibility_rule": "Consent-visible Group Memory includes the current soul + cooldown satisfied.",
                "source_evidence": [_evidence("group_memory", gid, title)],
                "involved_entities": [_entity("group_memory", gid, title)],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "optional",
                "cooldown_key": f"group_memory_callback:{gid}",
                "domain_action": "none",
                "domain_action_payload": {"group_id": gid, "title": title},
                "reasoning": {"member_count": len(members)},
            }
        )
    return candidates


def build_world_memory_legend_candidates(
    world_memories: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """A remembered cultural memory may surface as a legend encounter."""
    candidates: list[CandidateSpec] = []
    for memory in world_memories:
        state = memory.get("memory_state")
        if state not in ("widely_remembered", "locally_remembered", "rediscovered"):
            continue
        if memory.get("visibility") != "public_canon":
            continue
        mid = memory.get("memory_id")
        title = memory.get("title")
        candidates.append(
            {
                "opportunity_type": "world_memory_legend_encounter",
                "eligibility_rule": "Remembered public World Memory exists + cooldown satisfied.",
                "source_evidence": [_evidence("world_memory", mid, title)],
                "involved_entities": [_entity("world_memory", mid, title)],
                "visibility_scope": "public_canon",
                "urgency_class": "low",
                "participation": "optional",
                "cooldown_key": f"world_memory_legend_encounter:{mid}",
                "domain_action": "none",
                "domain_action_payload": {"memory_id": mid, "title": title},
                "reasoning": {
                    "memory_state": state,
                    "memory_form": memory.get("memory_form"),
                },
            }
        )
    return candidates


def build_integration_candidates(
    threads: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """A recognized Thread or Seed is eligible for an Integration Event."""
    candidates: list[CandidateSpec] = []
    for thread in threads:
        if thread.get("status") != "pattern_recognized":
            continue
        tid = thread.get("id")
        name = thread.get("name")
        candidates.append(
            {
                "opportunity_type": "integration_candidate",
                "eligibility_rule": "Local Thread reached pattern_recognized (Chronicle-backed evidence).",
                "source_evidence": [
                    _evidence(
                        "local_thread",
                        tid,
                        f"Thread '{name}' has {thread.get('evidence_count', 1)} evidence.",
                    )
                ],
                "involved_entities": [_entity("local_thread", tid, name)],
                "visibility_scope": "public_canon",
                "urgency_class": "high",
                "participation": "player_triggered",
                "cooldown_key": f"integration_candidate:{tid}",
                "domain_action": "integrate_thread",
                "domain_action_payload": {"thread_id": tid, "thread_name": name},
                "reasoning": {"evidence_count": thread.get("evidence_count", 1)},
            }
        )
    return candidates


def build_recognition_candidates(
    threads: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """Surfaced when enough evidence exists for a pattern; recognition is player-controlled."""
    candidates: list[CandidateSpec] = []
    for thread in threads:
        if thread.get("status") != "pattern_recognized":
            continue
        tid = thread.get("id")
        name = thread.get("name")
        candidates.append(
            {
                "opportunity_type": "recognition",
                "eligibility_rule": "Local Thread reached pattern_recognized; player may recognize/reject/postpone.",
                "source_evidence": [
                    _evidence(
                        "local_thread",
                        tid,
                        f"Thread '{name}' accumulated {thread.get('evidence_count', 1)} evidence.",
                    )
                ],
                "involved_entities": [_entity("local_thread", tid, name)],
                "visibility_scope": "public_canon",
                "urgency_class": "normal",
                "participation": "player_triggered",
                "cooldown_key": f"recognition:{tid}",
                "domain_action": "recognition_decision",
                "domain_action_payload": {"thread_id": tid, "thread_name": name},
                "reasoning": {"evidence_count": thread.get("evidence_count", 1)},
            }
        )
    for seed in seeds:
        if seed.get("stage") != "recognized":
            continue
        sid = seed.get("id")
        symbol = seed.get("symbol")
        candidates.append(
            {
                "opportunity_type": "recognition",
                "eligibility_rule": "Recognized Seed; player may recognize/reject/postpone.",
                "source_evidence": [
                    _evidence("seed", sid, f"Seed '{symbol}' is recognized.")
                ],
                "involved_entities": [_entity("seed", sid, symbol)],
                "visibility_scope": "public_canon",
                "urgency_class": "normal",
                "participation": "player_triggered",
                "cooldown_key": f"recognition:{sid}",
                "domain_action": "recognition_decision",
                "domain_action_payload": {"seed_id": sid, "symbol": symbol},
                "reasoning": {"stage": "recognized"},
            }
        )
    return candidates


def build_reflection_prompt_candidate(
    recent_event: dict[str, Any] | None,
) -> CandidateSpec | None:
    if not recent_event:
        return None
    event_id = recent_event.get("id")
    return {
        "opportunity_type": "reflection_prompt",
        "eligibility_rule": "A canonical event was committed + cooldown satisfied.",
        "source_evidence": [
            _evidence("chronicle_event", event_id, "Scene just resolved.")
        ],
        "involved_entities": [_entity("chronicle_event", event_id)],
        "visibility_scope": "public_canon",
        "urgency_class": "low",
        "participation": "optional",
        "cooldown_key": f"reflection_prompt:{event_id}",
        "domain_action": "none",
        "domain_action_payload": {"event_id": event_id},
        "reasoning": {"event_id": event_id},
    }


def build_chronicle_painting_candidates(
    memory_objects: list[dict[str, Any]],
) -> list[CandidateSpec]:
    """A significant, unpainted Memory Object is eligible for a Chronicle Painting."""
    candidates: list[CandidateSpec] = []
    for mo in memory_objects:
        if not mo.get("is_painting_eligible"):
            continue
        if mo.get("visual_generation_status") in ("generated", "approved"):
            continue
        tier = mo.get("importance_tier")
        score = int(mo.get("importance_score") or 0)
        if tier not in ("community", "world", "legendary") and score < 7:
            continue
        mid = mo.get("id")
        title = mo.get("event_title")
        candidates.append(
            {
                "opportunity_type": "chronicle_painting_eligibility",
                "eligibility_rule": "Significant Memory Object is painting-eligible and unpainted.",
                "source_evidence": [_evidence("memory_object", mid, title)],
                "involved_entities": [_entity("memory_object", mid, title)],
                "visibility_scope": mo.get("privacy_consent_scope", "public_canon"),
                "urgency_class": "low",
                "participation": "optional",
                "cooldown_key": f"chronicle_painting_eligibility:{mid}",
                "domain_action": "surface_painting",
                "domain_action_payload": {"memory_object_id": mid, "title": title},
                "reasoning": {
                    "importance_tier": tier,
                    "importance_score": score,
                },
            }
        )
    return candidates


def build_relationship_callback_candidates(
    relationships: list[dict[str, Any]],
    current_soul_id: str,
) -> list[CandidateSpec]:
    """A canonical relationship the current soul participates in may surface as a
    callback. Eligibility comes from structured relationship state (participants,
    canonical source events, status), never from narrative chemistry."""
    candidates: list[CandidateSpec] = []
    for rel in relationships:
        participants = rel.get("participants", []) or []
        if not any(p.get("entity_id") == current_soul_id for p in participants):
            continue
        if rel.get("status") not in ("active", "distant", "historical"):
            continue
        rid = rel.get("relationship_id")
        kinds = ", ".join(rel.get("kinds", []) or []) or "relationship"
        evidence = [
            _evidence("relationship", rid, f"A {kinds} relationship exists."),
        ]
        for ref in rel.get("source_refs", []) or []:
            evidence.append(_evidence(ref.get("source_type"), ref.get("source_id")))
        candidates.append(
            {
                "opportunity_type": "relationship_callback",
                "eligibility_rule": "Current soul participates in an active/distant/historical relationship + cooldown satisfied.",
                "source_evidence": evidence,
                "involved_entities": [
                    _entity("relationship", rid, kinds),
                    *[
                        _entity(p.get("entity_type"), p.get("entity_id"))
                        for p in participants
                    ],
                ],
                "visibility_scope": rel.get("visibility", "public_canon"),
                "urgency_class": "normal",
                "participation": "optional",
                "cooldown_key": f"relationship_callback:{rid}",
                "domain_action": "surface_relationship",
                "domain_action_payload": {"relationship_id": rid},
                "reasoning": {
                    "status": rel.get("status"),
                    "kind_count": len(rel.get("kinds", []) or []),
                    "event_count": len(rel.get("events", []) or []),
                },
            }
        )
    return candidates


def build_promise_consequence_candidates(
    promises: list[dict[str, Any]],
    current_soul_id: str,
) -> list[CandidateSpec]:
    """An unresolved (or newly rediscovered) promise the current soul is bound to
    may surface a consequence. Only promises the current scene is allowed to know
    reach this builder; the eligibility layer has already consent-filtered them."""
    candidates: list[CandidateSpec] = []
    for promise in promises:
        if not _entity_involved_in_promise(promise, current_soul_id):
            continue
        state = promise.get("lifecycle_state")
        if state not in (
            "made",
            "acknowledged",
            "active",
            "disputed",
            "inherited",
            "rediscovered",
            "unresolved",
        ):
            continue
        pid = promise.get("promise_id")
        candidates.append(
            {
                "opportunity_type": "promise_consequence",
                "eligibility_rule": "Current soul is bound to an unresolved promise + cooldown satisfied.",
                "source_evidence": [
                    _evidence("promise", pid, promise.get("promise_text")),
                    _evidence(
                        promise.get("source_type"),
                        promise.get("source_id"),
                        "Canonical promise source.",
                    ),
                ],
                "involved_entities": [
                    _entity("promise", pid, promise.get("promise_text")),
                    _entity(
                        promise.get("promisor_entity_type"),
                        promise.get("promisor_entity_id"),
                    ),
                ],
                "visibility_scope": promise.get("visibility", "public_canon"),
                "urgency_class": "normal",
                "participation": "optional",
                "cooldown_key": f"promise_consequence:{pid}",
                "domain_action": "surface_promise",
                "domain_action_payload": {"promise_id": pid},
                "reasoning": {
                    "lifecycle_state": state,
                    "scope": promise.get("scope"),
                },
            }
        )
    return candidates


def _entity_involved_in_promise(promise: dict[str, Any], entity_id: str) -> bool:
    if promise.get("promisor_entity_id") == entity_id:
        return True
    for participant in promise.get("participants", []) or []:
        if participant.get("entity_id") == entity_id:
            return True
    return False


# Cooldown helper (pure).


def cooldown_window(opportunity_type: str) -> int:
    return COOLDOWN_WINDOW.get(opportunity_type, 1)


def cooldown_satisfied(
    candidate: CandidateSpec, recent_cooldown_keys: list[str]
) -> bool:
    """A candidate is eligible only if its cooldown key is not hot."""
    key = candidate.get("cooldown_key")
    if not key:
        return True
    return key not in recent_cooldown_keys
