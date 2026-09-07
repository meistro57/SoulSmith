# backend/app/narrative_context_compiler.py
"""
SoulSmith Phase 18: consent-safe NarrativeContext compiler.

The compiler turns approved structured state (a ``CampaignOpportunity`` plus the
owning session) into a bounded, inspectable ``NarrativeContext``. It gathers the
smallest evidence set the current scene is allowed to know: the opportunity's
own source evidence, explicit scene continuity, and — only for NPC-scoped
narration — the Phase 16 NPC knowledge projection. It never dumps whole
biographies, Chronicles, or World Memory tables into a provider request.
"""

from __future__ import annotations

from typing import Any

from app.campaign import (
    NarrativeContext,
    NarrativeContinuity,
    SourceEvidence,
)
from app.narrative_style import SOULKEEPER_DEFAULT_STYLE, NarrativeStyle

# Bounds for scene continuity. Keep this small; it is continuity, not history.
MAX_RECENT_ACTIONS = 3


def _continuity_for(
    opportunity: dict[str, Any], session: dict[str, Any]
) -> NarrativeContinuity | None:
    from app import db

    location: str | None = None
    participants: list[str] = []
    for entity in opportunity.get("involved_entities", []):
        etype = entity.get("entity_type")
        if etype == "location":
            location = entity.get("label") or entity.get("entity_id")
        participants.append(entity.get("label") or entity.get("entity_id"))

    prior_summary: str | None = None
    transitions = db.list_campaign_transitions_records(session["session_id"])
    if transitions:
        last = transitions[-1]
        systems = ", ".join(last.get("systems_invoked", [])[:3])
        prior_summary = (
            f"Last transition was '{last.get('transition_type')}' "
            f"invoking {systems or 'no subsystems'}."
        )

    recent_actions: list[str] = []
    for event in db.get_all_canonical_events()[:MAX_RECENT_ACTIONS]:
        intent = event.get("player_intent")
        if intent:
            recent_actions.append(intent)

    return NarrativeContinuity(
        location=location,
        environment=None,
        current_participants=participants,
        prior_transition_summary=prior_summary,
        recent_visible_actions=recent_actions,
    )


def compile_narrative_context(
    opportunity: dict[str, Any],
    session: dict[str, Any],
    *,
    style: NarrativeStyle | None = None,
    include_continuity: bool = True,
) -> NarrativeContext:
    """Compile a player-facing context from one authorized opportunity."""
    allowed_claims: list[str] = []
    provenance_ids: list[str] = []
    source_evidence: list[SourceEvidence] = []
    for raw in opportunity.get("source_evidence", []):
        evidence = SourceEvidence(**raw)
        source_evidence.append(evidence)
        if evidence.note:
            allowed_claims.append(evidence.note)
        if evidence.source_id:
            provenance_ids.append(f"{evidence.source_type}:{evidence.source_id}")

    constraints = list(opportunity.get("constraints", []) or [])
    if opportunity["opportunity_type"] == "recognition":
        constraints.append("player_choice_pending")

    style = style or SOULKEEPER_DEFAULT_STYLE

    return NarrativeContext(
        soul_id=session["soul_id"],
        campaign_id=session["campaign_id"],
        session_id=session["session_id"],
        opportunity_type=opportunity["opportunity_type"],
        title_hint=None,
        allowed_claims=allowed_claims,
        source_evidence=source_evidence,
        visible_entities=opportunity.get("involved_entities", []),
        participants=opportunity.get("involved_entities", []),
        constraints=constraints,
        provenance_ids=provenance_ids,
        continuity=_continuity_for(opportunity, session)
        if include_continuity
        else None,
        style=style.model_dump(),
    )


def compile_npc_narrative_context(
    opportunity: dict[str, Any],
    session: dict[str, Any],
    *,
    npc_projection: Any,
    style: NarrativeStyle | None = None,
) -> NarrativeContext:
    """Compile an NPC-scoped context from a Phase 16 knowledge projection.

    The NPC speaks only from what the projection legitimately grants; the
    player's omniscient context is never used.
    """
    claims: list[str] = []
    npc_knowledge: list[dict[str, Any]] = []
    provenance_ids: list[str] = []
    for entry in npc_projection.entries:
        memory = entry.memory
        claims.append(memory.title)
        if memory.narrative:
            claims.append(memory.narrative)
        claims.append(f"Fidelity: {entry.fidelity} ({entry.reason})")
        npc_knowledge.append(
            {
                "memory_id": memory.memory_id,
                "title": memory.title,
                "fidelity": entry.fidelity,
                "canonical_truth_visible": entry.canonical_truth_visible,
                "reason": entry.reason,
            }
        )
        if memory.memory_id:
            provenance_ids.append(f"world_memory:{memory.memory_id}")

    style = style or SOULKEEPER_DEFAULT_STYLE
    return NarrativeContext(
        soul_id=session["soul_id"],
        campaign_id=session["campaign_id"],
        session_id=session["session_id"],
        opportunity_type="npc_historical_reaction",
        title_hint="A Voice From the Past",
        allowed_claims=claims,
        source_evidence=opportunity.get("source_evidence", []),
        visible_entities=opportunity.get("involved_entities", []),
        participants=opportunity.get("involved_entities", []),
        constraints=["npc_knowledge_scoped"],
        provenance_ids=provenance_ids,
        npc_knowledge=npc_knowledge,
        continuity=_continuity_for(opportunity, session),
        style=style.model_dump(),
    )


def estimate_context_tokens(context: NarrativeContext) -> int:
    """Cheap, deterministic token estimate for diagnostics. Not authoritative."""
    payload = context.model_dump_json()
    # Rough heuristic: ~4 characters per token for English prose.
    return max(1, len(payload) // 4)


def context_stats(context: NarrativeContext) -> dict[str, Any]:
    """Non-sensitive diagnostics about how much context was compiled."""
    return {
        "source_count": len(context.source_evidence),
        "allowed_claim_count": len(context.allowed_claims),
        "participant_count": len(context.participants),
        "provenance_id_count": len(context.provenance_ids),
        "npc_knowledge_entry_count": len(context.npc_knowledge),
        "approx_tokens": estimate_context_tokens(context),
    }
