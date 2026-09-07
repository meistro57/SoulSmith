# backend/app/campaign_orchestrator.py
"""
SoulSmith Phase 17: Campaign Orchestrator service.

The orchestrator coordinates the Phase 0-16 domain systems into one continuous,
deterministic, playable loop. It decides *what gets an opportunity to act next*;
it never decides *what the player's story means*. Every canonical mutation is
delegated to the domain system that owns it. Every callback carries provenance.
Every reaction is recorded in an auditable ``CampaignTransition``.

Key invariants:

- Eligibility is computed from structured state *before* any narration.
- Existing domain services remain authoritative for their own rules.
- Player agency (recognize / reject / rename / reinterpret / postpone / hide)
  outranks pacing convenience; rejection never punishes or re-injects a fact.
- A failure in a derived/noncanonical subsystem never rolls back canonical
  history unless the domain transaction itself requires atomicity.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.campaign import (
    CAMPAIGN_COMPILER_VERSION,
    NarrativeContext,
    RecognitionDecision,
    build_aspect_switch_candidates,
    build_chronicle_painting_candidates,
    build_cross_aspect_echo_candidates,
    build_cross_aspect_meeting_candidates,
    build_group_memory_callback_candidates,
    build_integration_candidates,
    build_location_bound_seed_candidates,
    build_new_encounter_candidate,
    build_npc_historical_reaction_candidates,
    build_probable_path_echo_candidates,
    build_promise_consequence_candidates,
    build_recognition_candidates,
    build_recurring_location_candidates,
    build_recurring_symbol_candidates,
    build_reflection_prompt_candidate,
    build_relationship_callback_candidates,
    build_relic_awakening_candidates,
    build_relic_memory_candidates,
    build_seed_echo_candidates,
    build_unresolved_question_candidates,
    build_world_memory_legend_candidates,
    cooldown_satisfied,
    cooldown_window,
)
from app.campaign_provider import get_campaign_provider
from app.narrative_context_compiler import (
    compile_narrative_context,
    compile_npc_narrative_context,
)
from app.narrative_runtime import NarrativeRuntime

# Each subsystem's follow-up candidate types. The reaction pipeline records one
# structured result per subsystem so a transition is fully auditable.
SUBSYSTEM_CANDIDATE_TYPES: dict[str, list[str]] = {
    "Curiosity Engine": [
        "seed_echo",
        "recurring_symbol",
        "unresolved_question_callback",
    ],
    "Probable Paths": ["probable_path_echo"],
    "Relic Recognition": ["relic_memory", "relic_awakening_candidate"],
    "Soul Constellation": ["cross_aspect_echo"],
    "World Memory": ["npc_historical_reaction", "world_memory_legend_encounter"],
    "Group Memories": ["group_memory_callback"],
    "Relationship & Promises": ["relationship_callback", "promise_consequence"],
    "Threads & Integration": ["integration_candidate", "recognition"],
    "Reflection": ["reflection_prompt"],
    "Chronicle Paintings": ["chronicle_painting_eligibility"],
    "Multi-Aspect": ["aspect_switch", "cross_aspect_meeting"],
    "Wandering": ["recurring_location", "location_bound_seed"],
}


class CampaignOrchestratorError(ValueError):
    """Raised when the orchestrator cannot complete a request safely."""


def start_or_resume_session(
    *, soul_id: str = "Kaelen the Star-Watcher", campaign_id: str | None = None
) -> dict[str, Any]:
    """Create or resume a campaign session. The session is campaign-level; the
    requested ``soul_id`` is registered as a playable Aspect and becomes the
    active Aspect. Idempotent: replaying start/resume never creates a second
    session for the same campaign."""
    from app import db
    from app.multi_aspect import ensure_campaign_aspect_registered

    campaign_id = campaign_id or "north_star_campaign"
    ensure_campaign_aspect_registered(campaign_id, soul_id)

    existing = db.get_active_campaign_session_for_campaign(campaign_id)
    if existing:
        if existing.get("active_soul_id") != soul_id:
            existing = db.set_campaign_session_active_soul(
                existing["session_id"], soul_id
            )
            db.set_campaign_aspect_active(campaign_id, soul_id)
        return {"session": existing, "resumed": True}

    constellation = db.get_or_create_primary_constellation()
    session = db.create_campaign_session_record(
        campaign_id=campaign_id,
        soul_id=soul_id,
        constellation_id=constellation.get("id"),
        active_soul_id=soul_id,
    )
    db.set_campaign_aspect_active(campaign_id, soul_id)
    return {"session": session, "resumed": False}


def get_session_state(session_id: str) -> dict[str, Any]:
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")
    return {
        "session": session,
        "opportunities": db.list_campaign_opportunities_records(session_id),
        "transitions": db.list_campaign_transitions_records(session_id),
    }


def _gather_state(session: dict[str, Any]) -> dict[str, Any]:
    from app import db
    from app.multi_aspect import active_soul_id
    from app.relationship import (
        promise_visible_to,
        relationship_visible_to,
    )
    from app.world_memory import memory_object_visible_to, world_memory_visible_to

    soul_id = active_soul_id(session)
    events = db.get_canonical_events_for_soul(soul_id)
    world_memories = [
        m for m in db.list_world_memory_records() if world_memory_visible_to(m, soul_id)
    ]
    memory_objects = [
        mo
        for mo in db.get_memory_objects_records()
        if memory_object_visible_to(mo, soul_id)
    ]
    group_memories = _group_memories_with_members()
    relationships = [
        rel
        for rel in db.list_relationship_records()
        if relationship_visible_to(rel, soul_id)
    ]
    promises = [p for p in db.list_promise_records() if promise_visible_to(p, soul_id)]
    return {
        "soul_id": soul_id,
        "seeds": db.get_seeds_for_soul(soul_id),
        "open_questions": db.get_open_questions_for_soul(soul_id),
        "threads": db.get_all_local_threads(soul_id=soul_id),
        "probable_paths": db.get_probable_paths_records(soul_id=soul_id),
        "relics": db.get_or_create_relics_records(soul_id=soul_id),
        "constellation": db.get_or_create_primary_constellation(),
        "memory_objects": memory_objects,
        "group_memories": group_memories,
        "world_memories": world_memories,
        "relationships": relationships,
        "promises": promises,
        "events": events,
        "recent_event": events[0] if events else None,
        "campaign_aspects": db.list_campaign_aspect_records(session["campaign_id"]),
        "place_history": db.list_all_place_history_records(),
    }


def _group_memories_with_members() -> list[dict[str, Any]]:
    from app import db

    groups = []
    for group in db.list_group_memory_records():
        group["members"] = db.get_group_memory_members_records(group["group_id"])
        groups.append(group)
    return groups


def _build_subsystem_candidates(
    state: dict[str, Any], system_name: str
) -> list[dict[str, Any]]:
    """Build candidate specs for a single subsystem, filtering out Nones."""
    soul_id = state["soul_id"]
    if system_name == "Curiosity Engine":
        built = (
            build_seed_echo_candidates(state["seeds"])
            + build_recurring_symbol_candidates(state["seeds"])
            + build_unresolved_question_candidates(state["open_questions"])
        )
    elif system_name == "Probable Paths":
        built = build_probable_path_echo_candidates(state["probable_paths"])
    elif system_name == "Relic Recognition":
        built = build_relic_memory_candidates(
            state["relics"], state["constellation"]
        ) + build_relic_awakening_candidates(
            state["relics"], state["threads"], state["seeds"]
        )
    elif system_name == "Soul Constellation":
        built = build_cross_aspect_echo_candidates(state["constellation"], soul_id)
    elif system_name == "World Memory":
        built = build_npc_historical_reaction_candidates(
            state["world_memories"], soul_id
        ) + build_world_memory_legend_candidates(state["world_memories"])
    elif system_name == "Group Memories":
        built = build_group_memory_callback_candidates(state["group_memories"], soul_id)
    elif system_name == "Relationship & Promises":
        built = build_relationship_callback_candidates(
            state["relationships"], soul_id
        ) + build_promise_consequence_candidates(state["promises"], soul_id)
    elif system_name == "Threads & Integration":
        built = build_integration_candidates(
            state["threads"], state["seeds"]
        ) + build_recognition_candidates(state["threads"], state["seeds"])
    elif system_name == "Reflection":
        candidate = build_reflection_prompt_candidate(state["recent_event"])
        built = [candidate] if candidate else []
    elif system_name == "Chronicle Paintings":
        built = build_chronicle_painting_candidates(state["memory_objects"])
    elif system_name == "Multi-Aspect":
        built = build_aspect_switch_candidates(
            state["campaign_aspects"], soul_id
        ) + build_cross_aspect_meeting_candidates(
            state["campaign_aspects"], soul_id, state["relationships"]
        )
    elif system_name == "Wandering":
        built = build_recurring_location_candidates(
            state["place_history"], soul_id
        ) + build_location_bound_seed_candidates(
            state["seeds"], state["place_history"], soul_id
        )
    else:
        built = []
    return [c for c in built if c is not None]


def _build_candidates(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Defensively build all candidates; a failing derived builder is skipped."""
    candidates: list[dict[str, Any]] = [build_new_encounter_candidate(state["soul_id"])]
    for system_name in SUBSYSTEM_CANDIDATE_TYPES:
        try:
            built = _build_subsystem_candidates(state, system_name)
        except Exception:  # noqa: BLE001 - a derived builder failure must not block the loop
            built = []
        candidates.extend(built)
    return [c for c in candidates if c is not None]


def _cooldown_filter(
    session_id: str, candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    from app import db

    max_window = max(cooldown_window(c["opportunity_type"]) for c in candidates)
    if max_window <= 0:
        return candidates
    recent_keys = set(db.get_recent_campaign_cooldown_keys(session_id, max_window))
    return [c for c in candidates if cooldown_satisfied(c, recent_keys)]


def _dedupe_existing(
    session_id: str, candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    from app import db

    existing = db.list_campaign_opportunities_records(session_id)
    open_keys = {
        f"{o['opportunity_type']}:{o.get('cooldown_key')}"
        for o in existing
        if o["lifecycle_state"] in ("eligible", "selected")
    }
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = f"{candidate['opportunity_type']}:{candidate.get('cooldown_key')}"
        if key in open_keys or key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result


def _narrate(
    context: NarrativeContext,
    *,
    opportunity_id: str | None = None,
    transition_id: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    provider = get_campaign_provider()
    result = NarrativeRuntime(provider=provider).narrate(context)
    _persist_narrative_generation(context, result, opportunity_id, transition_id)
    if result.failure:
        return None, result.failure
    output = result.output
    return _output_dict(output, result), None


def _output_dict(output, result) -> dict[str, Any]:
    return {
        "title": output.title,
        "prose": output.prose,
        "scene_prose": output.scene_prose,
        "soulkeeper_narration": output.soulkeeper_narration,
        "dialogue": [d.model_dump() for d in output.dialogue],
        "question": output.question.model_dump() if output.question else None,
        "flavor_lines": output.flavor_lines,
        "presentation_cues": [c.model_dump() for c in output.presentation_cues],
        "claims": output.claims,
        "source_evidence": [e.model_dump() for e in output.source_evidence],
        "referenced_provenance_ids": output.referenced_provenance_ids,
        "declared_uncertainty": output.declared_uncertainty,
        "provider": output.provider,
        "provider_model": output.provider_model,
        "template_version": output.template_version,
        "narration_source": _narration_source(output),
        "validation": result.validation.model_dump() if result.validation else None,
        "used_fallback": result.used_fallback,
    }


def _narration_source(output) -> str:
    if output.provider == "mock":
        return "deterministic"
    return output.provider


def _persist_narrative_generation(
    context: NarrativeContext,
    result,
    opportunity_id: str | None,
    transition_id: str | None,
) -> None:
    from app import db

    metadata = result.metadata
    output_dict = result.output.model_dump() if result.output else {}
    db.create_narrative_generation_record(
        generation_id=metadata["generation_id"],
        session_id=context.session_id,
        opportunity_id=opportunity_id,
        transition_id=transition_id,
        provider=metadata["provider"],
        provider_model=metadata["provider_model"],
        template_version=metadata["template_version"],
        retry_count=metadata.get("retry_count", 0),
        validation_outcome=(
            result.validation.verdict
            if result.validation
            else metadata.get("validation_outcome", "provider_failure")
        ),
        latency_ms=metadata.get("latency_ms"),
        used_fallback=result.used_fallback,
        context_stats=metadata.get("context_stats", {}),
        output=output_dict,
        error=result.failure,
    )


def _narrative_context_for(
    opportunity: dict[str, Any], session: dict[str, Any]
) -> NarrativeContext:
    return compile_narrative_context(opportunity, session)


def _persist_opportunity(
    session: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    from app import db

    opportunity = db.create_campaign_opportunity_record(
        session_id=session["session_id"],
        opportunity_type=candidate["opportunity_type"],
        eligibility_rule=candidate["eligibility_rule"],
        source_evidence=candidate.get("source_evidence", []),
        involved_entities=candidate.get("involved_entities", []),
        visibility_scope=candidate.get("visibility_scope", "public_canon"),
        urgency_class=candidate.get("urgency_class", "normal"),
        participation=candidate.get("participation", "optional"),
        cooldown_key=candidate.get("cooldown_key"),
        domain_action=candidate.get("domain_action", "none"),
        domain_action_payload=candidate.get("domain_action_payload", {}),
        reasoning=candidate.get("reasoning", {}),
    )
    narrative, _ = _narrate(
        _narrative_context_for(opportunity, session),
        opportunity_id=opportunity["opportunity_id"],
    )
    if narrative:
        opportunity = db.update_campaign_opportunity_state_record(
            opportunity["opportunity_id"],
            "eligible",
            narration=narrative["prose"],
            narration_source=narrative.get("narration_source", "deterministic"),
        )
    return opportunity


def evaluate_opportunities(
    session_id: str, include_encounter: bool = True
) -> dict[str, Any]:
    """Evaluate a bounded set of eligible next opportunities deterministically."""
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")
    if session["status"] != "active":
        raise CampaignOrchestratorError("Session is not active")

    state = _gather_state(session)
    candidates = _build_candidates(state)
    if not include_encounter:
        candidates = [c for c in candidates if c["opportunity_type"] != "new_encounter"]
    candidates = _cooldown_filter(session_id, candidates)
    candidates = _dedupe_existing(session_id, candidates)

    for candidate in candidates:
        _persist_opportunity(session, candidate)

    opportunities = db.list_campaign_opportunities_records(session_id, "eligible")
    return {
        "session_id": session_id,
        "opportunities": opportunities,
        "silence": len(opportunities) == 0,
    }


def _run_reaction_pipeline(
    session: dict[str, Any], event: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate each subsystem's reaction to a committed canonical event."""
    state = _gather_state(session)

    reactions: list[dict[str, Any]] = []
    follow_ups: list[dict[str, Any]] = []
    for system_name in SUBSYSTEM_CANDIDATE_TYPES:
        try:
            matched = _build_subsystem_candidates(state, system_name)
            matched = [c for c in matched if c["opportunity_type"] != "new_encounter"]
            matched = _cooldown_filter(session["session_id"], matched)
            if matched:
                reactions.append(
                    {
                        "system_name": system_name,
                        "result_kind": "future_opportunity_scheduled",
                        "details": {
                            "candidate_count": len(matched),
                            "types": [c["opportunity_type"] for c in matched],
                        },
                    }
                )
                follow_ups.extend(matched)
            else:
                reactions.append(
                    {
                        "system_name": system_name,
                        "result_kind": "no_action",
                        "details": {"reason": "No eligible follow-up."},
                    }
                )
        except Exception as exc:  # noqa: BLE001 - derived failure must not corrupt canon
            reactions.append(
                {
                    "system_name": system_name,
                    "result_kind": "no_action",
                    "details": {"error": str(exc)},
                }
            )

    # Chronicle itself always "reacts" to a committed event.
    reactions.insert(
        0,
        {
            "system_name": "Chronicle",
            "result_kind": "state_updated",
            "details": {"event_id": event["id"]},
        },
    )
    return reactions, follow_ups


def commit_canonical_event(session_id: str, event_id: str) -> dict[str, Any]:
    """Commit an already-canonical event and run the reaction pipeline."""
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")

    event = db.get_canonical_event_record(event_id)
    if not event:
        raise CampaignOrchestratorError(f"Canonical event '{event_id}' not found")

    existing = db.get_campaign_transition_by_event_record(session_id, event_id)
    if existing:
        return {
            "transition": existing,
            "opportunities": db.list_campaign_opportunities_records(
                session_id, "eligible"
            ),
            "idempotent": True,
        }

    reactions, follow_ups = _run_reaction_pipeline(session, event)
    transition_id = str(uuid.uuid4())
    systems_invoked = [r["system_name"] for r in reactions]
    outcomes = [
        {
            "system_name": r["system_name"],
            "result_kind": r["result_kind"],
            "details": r["details"],
        }
        for r in reactions
    ]
    transition = db.create_campaign_transaction_record(
        transition_id=transition_id,
        session_id=session_id,
        opportunity_id=None,
        canonical_event_id=event_id,
        transition_type="commit_event",
        systems_invoked=systems_invoked,
        outcomes=outcomes,
        canonical_change=False,
        provider_failure=None,
        rejected_invalid_transition=False,
    )
    for reaction in reactions:
        db.create_campaign_reaction_record(
            transition_id=transition_id,
            system_name=reaction["system_name"],
            result_kind=reaction["result_kind"],
            details=reaction["details"],
        )

    follow_ups = _dedupe_existing(session_id, follow_ups)
    opportunities = [_persist_opportunity(session, c) for c in follow_ups]
    transition = db.get_campaign_transition_record(transition_id)

    # Phase 21: evaluate Art Director eligibility and queue living visual jobs.
    # This is deferred bookkeeping; a failure here never rolls back canon.
    try:
        living_visuals = queue_eligible_art_moments(session_id)
    except Exception:  # noqa: BLE001 - visual generation is never canonical
        living_visuals = {"error": "living visual evaluation failed", "created": 0}

    return {
        "transition": transition,
        "opportunities": opportunities,
        "living_visuals": living_visuals,
        "idempotent": False,
    }


def resolve_opportunity(
    session_id: str,
    opportunity_id: str,
    decision: str | None = None,
    recognition: RecognitionDecision | None = None,
    player_intent: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Resolve a selected opportunity, delegating canonical mutations to the
    domain system that owns them. Idempotent: resolving twice returns the prior
    transition and never duplicates a canonical mutation."""
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")

    opportunity = db.get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise CampaignOrchestratorError(f"Opportunity '{opportunity_id}' not found")
    if opportunity["session_id"] != session_id:
        raise CampaignOrchestratorError("Opportunity does not belong to session")

    if opportunity["lifecycle_state"] == "resolved":
        existing = _find_transition_for_opportunity(session_id, opportunity_id)
        return {
            "transition": existing,
            "opportunity": opportunity,
            "idempotent": True,
        }

    canonical_change = False
    provider_failure = None
    systems_invoked: list[str] = []
    outcomes: list[dict[str, Any]] = []
    next_lifecycle = "resolved"

    opportunity_type = opportunity["opportunity_type"]
    payload = opportunity.get("domain_action_payload", {})

    if opportunity_type == "new_encounter":
        systems_invoked.append("Encounter")
        outcomes.append(
            {
                "system_name": "Encounter",
                "result_kind": "state_updated",
                "details": {"note": "Proceed to the canonical dice/roll path."},
            }
        )

    elif opportunity_type in ("seed_echo", "recurring_symbol"):
        systems_invoked.append("Curiosity Engine")
        result = db.plant_or_echo_seed(
            symbol=payload.get("symbol"),
            thread_type=payload.get("thread_type"),
            narrative_context=player_intent
            or note
            or "Echoed through the campaign loop.",
            soul_id=session["soul_id"],
        )
        canonical_change = True
        outcomes.append(
            {
                "system_name": "Curiosity Engine",
                "result_kind": "state_updated",
                "details": result,
            }
        )

    elif opportunity_type == "integration_candidate":
        thread_id = payload.get("thread_id")
        if decision in ("integrate", "recognize") and thread_id:
            systems_invoked.append("Threads & Integration")
            result = db.execute_integration_event(
                thread_id=thread_id,
                soul_id=session["soul_id"],
                choice_made=player_intent
                or note
                or "Chose differently after recognizing the pattern.",
                target_relic_id=payload.get("relic_id"),
            )
            canonical_change = True
            outcomes.append(
                {
                    "system_name": "Threads & Integration",
                    "result_kind": "state_updated",
                    "details": result,
                }
            )
        else:
            systems_invoked.append("Threads & Integration")
            outcomes.append(
                {
                    "system_name": "Threads & Integration",
                    "result_kind": "player_review_required",
                    "details": {"note": "Integration requires a player decision."},
                }
            )
            next_lifecycle = "postponed"

    elif opportunity_type == "recognition":
        systems_invoked.append("Threads & Integration")
        recognition_decision = recognition or RecognitionDecision(
            decision=decision or "postpone"
        )
        outcomes.append(
            {
                "system_name": "Threads & Integration",
                "result_kind": "state_updated",
                "details": {"recognition": recognition_decision.model_dump()},
            }
        )
        # Rejection/postponement/hiding never mutates canonical Thread state.
        if recognition_decision.decision == "reject":
            next_lifecycle = "rejected"
        elif recognition_decision.decision == "postpone":
            next_lifecycle = "postponed"
        elif recognition_decision.decision == "hide":
            next_lifecycle = "hidden"

    elif opportunity_type == "relic_awakening_candidate":
        systems_invoked.append("Relic Recognition")
        outcomes.append(
            {
                "system_name": "Relic Recognition",
                "result_kind": "player_review_required",
                "details": {
                    "note": "The orchestrator surfaced the candidate; the Relic "
                    "Recognition system decides awakening via /api/v1/relics/attune-narrative.",
                    "relic_id": payload.get("relic_id"),
                },
            }
        )
        next_lifecycle = "resolved"

    elif opportunity_type == "npc_historical_reaction":
        systems_invoked.append("World Memory")
        narration, failure = _npc_reaction(opportunity, session)
        if narration is None:
            outcomes.append(
                {
                    "system_name": "World Memory",
                    "result_kind": "no_action",
                    "details": {
                        "reason": "The NPC has no legitimate access to this knowledge."
                    },
                }
            )
        else:
            outcomes.append(
                {
                    "system_name": "World Memory",
                    "result_kind": "state_updated",
                    "details": narration,
                }
            )
            opportunity = db.update_campaign_opportunity_state_record(
                opportunity_id,
                "resolved",
                narration=narration["prose"],
                narration_source=narration.get("narration_source", "deterministic"),
            )

    elif opportunity_type == "relic_memory":
        systems_invoked.append("Relic Recognition")
        narration, failure = _surface_opportunity(opportunity, session)
        provider_failure = provider_failure or failure
        outcomes.append(
            {
                "system_name": "Relic Recognition",
                "result_kind": "state_updated",
                "details": {"narration": narration, "provider_failure": failure},
            }
        )
        if narration:
            opportunity = db.update_campaign_opportunity_state_record(
                opportunity_id,
                "resolved",
                narration=narration["prose"],
                narration_source=narration.get("narration_source", "deterministic"),
            )

    elif opportunity_type == "aspect_switch":
        systems_invoked.append("Multi-Aspect")
        target_soul_id = payload.get("target_soul_id")
        if target_soul_id:
            from app.multi_aspect import switch_aspect

            switch_result = switch_aspect(
                session["campaign_id"], session_id, target_soul_id
            )
            outcomes.append(
                {
                    "system_name": "Multi-Aspect",
                    "result_kind": "state_updated",
                    "details": {
                        "from_soul_id": switch_result["from_soul_id"],
                        "to_soul_id": switch_result["to_soul_id"],
                        "idempotent": switch_result["idempotent"],
                    },
                }
            )
        else:
            outcomes.append(
                {
                    "system_name": "Multi-Aspect",
                    "result_kind": "no_action",
                    "details": {"reason": "No switch target specified."},
                }
            )
        next_lifecycle = "resolved"

    elif opportunity_type == "cross_aspect_meeting":
        systems_invoked.append("Multi-Aspect")
        other_soul_id = payload.get("other_soul_id")
        if other_soul_id:
            from app.multi_aspect import resolve_cross_aspect_encounter

            meeting = resolve_cross_aspect_encounter(session_id, other_soul_id)
            outcomes.append(
                {
                    "system_name": "Multi-Aspect",
                    "result_kind": "state_updated",
                    "details": meeting,
                }
            )
        else:
            outcomes.append(
                {
                    "system_name": "Multi-Aspect",
                    "result_kind": "no_action",
                    "details": {"reason": "No other Aspect specified."},
                }
            )
        next_lifecycle = "resolved"

    else:
        # Cue-only opportunities (reflection, probable path echo, group memory,
        # legend encounter, painting eligibility, unresolved question, etc.).
        systems_invoked.append(_system_for_type(opportunity_type))
        narration, failure = _surface_opportunity(opportunity, session)
        provider_failure = provider_failure or failure
        outcomes.append(
            {
                "system_name": _system_for_type(opportunity_type),
                "result_kind": "state_updated" if narration else "no_action",
                "details": {"narration": narration, "provider_failure": failure},
            }
        )
        if narration:
            opportunity = db.update_campaign_opportunity_state_record(
                opportunity_id,
                "resolved",
                narration=narration["prose"],
                narration_source=narration.get("narration_source", "deterministic"),
            )

    transition_id = str(uuid.uuid4())
    transition = db.create_campaign_transaction_record(
        transition_id=transition_id,
        session_id=session_id,
        opportunity_id=opportunity_id,
        canonical_event_id=None,
        transition_type=f"resolve_{opportunity_type}",
        systems_invoked=systems_invoked,
        outcomes=outcomes,
        canonical_change=canonical_change,
        provider_failure=provider_failure,
        rejected_invalid_transition=False,
    )
    opportunity = db.update_campaign_opportunity_state_record(
        opportunity_id, next_lifecycle
    )
    db.set_campaign_session_current_opportunity(session_id, None)
    transition = db.get_campaign_transition_record(transition_id)
    return {
        "transition": transition,
        "opportunity": opportunity,
        "idempotent": False,
    }


def _system_for_type(opportunity_type: str) -> str:
    return {
        "seed_echo": "Curiosity Engine",
        "recurring_symbol": "Curiosity Engine",
        "unresolved_question_callback": "Curiosity Engine",
        "probable_path_echo": "Probable Paths",
        "cross_aspect_echo": "Soul Constellation",
        "group_memory_callback": "Group Memories",
        "world_memory_legend_encounter": "World Memory",
        "chronicle_painting_eligibility": "Chronicle Paintings",
        "reflection_prompt": "Reflection",
        "relationship_callback": "Relationship & Promises",
        "promise_consequence": "Relationship & Promises",
        "aspect_switch": "Multi-Aspect",
        "cross_aspect_meeting": "Multi-Aspect",
        "recurring_location": "Wandering",
        "location_bound_seed": "Wandering",
    }.get(opportunity_type, opportunity_type)


def _find_transition_for_opportunity(
    session_id: str, opportunity_id: str
) -> dict[str, Any] | None:
    from app import db

    for transition in db.list_campaign_transitions_records(session_id):
        if transition.get("opportunity_id") == opportunity_id:
            return transition
    return None


def _surface_opportunity(
    opportunity: dict[str, Any], session: dict[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    context = _narrative_context_for(opportunity, session)
    return _narrate(context, opportunity_id=opportunity.get("opportunity_id"))


def _npc_reaction(
    opportunity: dict[str, Any], session: dict[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    """Project what an in-world NPC could plausibly know, then narrate only the
    knowledge the projection legitimately grants. No canonical mutation."""
    from app import db
    from app.world_memory import NPCKnowledgeRequest, project_npc_knowledge

    payload = opportunity.get("domain_action_payload", {})
    memory_id = payload.get("memory_id")
    memory = db.get_world_memory_record(memory_id)
    if not memory:
        return None, "World Memory not found."

    npc = NPCKnowledgeRequest(
        subject_entity_type=payload.get("subject_entity_type", "person"),
        subject_entity_id=payload.get("subject_entity_id", ""),
        culture=payload.get("culture", ""),
        location="",
        era_context=payload.get("era_context", ""),
        social_role="commoner",
        access_to_archives=False,
        education_level="low",
        local_tradition=True,
        direct_relationship=False,
        secrecy_aware=False,
    )
    projection = project_npc_knowledge(
        subject_entity_type=npc.subject_entity_type,
        subject_entity_id=npc.subject_entity_id,
        npc=npc,
        memories=[memory],
    )
    if not projection.entries:
        return None, "No legitimate NPC knowledge projected."

    context = compile_npc_narrative_context(
        opportunity, session, npc_projection=projection
    )
    return _narrate(context, opportunity_id=opportunity.get("opportunity_id"))


def get_transition_provenance(transition_id: str) -> dict[str, Any]:
    from app import db

    transition = db.get_campaign_transition_record(transition_id)
    if not transition:
        raise CampaignOrchestratorError(f"Transition '{transition_id}' not found")
    provenance = []
    for reaction in transition.get("reactions", []):
        provenance.append(
            {
                "system_name": reaction["system_name"],
                "result_kind": reaction["result_kind"],
                "details": reaction["details"],
            }
        )
    return {
        "transition_id": transition_id,
        "transition_type": transition["transition_type"],
        "canonical_event_id": transition["canonical_event_id"],
        "systems_invoked": transition["systems_invoked"],
        "outcomes": transition["outcomes"],
        "provenance": provenance,
        "canonical_change": transition["canonical_change"],
        "provider_failure": transition["provider_failure"],
    }


def get_pending_reviews(session_id: str) -> dict[str, Any]:
    from app import db

    reviews = [
        o
        for o in db.list_campaign_opportunities_records(session_id)
        if o["participation"] == "player_triggered"
        and o["lifecycle_state"] in ("eligible", "selected")
    ]
    return {"pending_reviews": reviews}


def get_aftermath(session_id: str) -> dict[str, Any]:
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")
    transitions = db.list_campaign_transitions_records(session_id)
    opportunities = db.list_campaign_opportunities_records(session_id)
    state = _gather_state(session)
    return {
        "session_id": session_id,
        "soul_id": session["soul_id"],
        "transition_count": len(transitions),
        "open_opportunity_count": len(
            [
                o
                for o in opportunities
                if o["lifecycle_state"] in ("eligible", "selected")
            ]
        ),
        "unresolved_seed_count": len(state["seeds"]),
        "open_question_count": len(
            [q for q in state["open_questions"] if q["status"] == "open"]
        ),
        "recognized_thread_count": len(
            [t for t in state["threads"] if t["status"] == "pattern_recognized"]
        ),
        "remembered_relic_count": len(
            [r for r in state["relics"] if r["stage"] == "Remembered"]
        ),
        "compiler_version": CAMPAIGN_COMPILER_VERSION,
    }


def inspect_opportunity(opportunity_id: str) -> dict[str, Any]:
    from app import db

    opportunity = db.get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise CampaignOrchestratorError(f"Opportunity '{opportunity_id}' not found")
    return {
        "opportunity_id": opportunity["opportunity_id"],
        "opportunity_type": opportunity["opportunity_type"],
        "eligibility_rule": opportunity["eligibility_rule"],
        "source_evidence": opportunity["source_evidence"],
        "involved_entities": opportunity["involved_entities"],
        "systems_consulted": [opportunity["opportunity_type"]],
        "cooldown": {
            "key": opportunity.get("cooldown_key"),
            "window": cooldown_window(opportunity["opportunity_type"]),
        },
        "consent_scope": opportunity["visibility_scope"],
        "narration_source": opportunity["narration_source"],
        "narration": opportunity["narration"],
        "lifecycle_state": opportunity["lifecycle_state"],
    }


def get_narrative_provider_status() -> dict[str, Any]:
    """Report provider status/capabilities without exposing secrets."""
    from app.campaign_provider import list_campaign_provider_capabilities

    return list_campaign_provider_capabilities()


def preview_narrative_context(opportunity_id: str) -> dict[str, Any]:
    """Authorized-debug preview of the compiled NarrativeContext. Never mutates."""
    from app import db
    from app.narrative_context_compiler import context_stats

    opportunity = db.get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise CampaignOrchestratorError(f"Opportunity '{opportunity_id}' not found")
    session = db.get_campaign_session_record(opportunity["session_id"])
    if not session:
        raise CampaignOrchestratorError("Opportunity session not found")
    context = compile_narrative_context(opportunity, session)
    return {
        "opportunity_id": opportunity_id,
        "context": context.model_dump(),
        "stats": context_stats(context),
    }


def inspect_narrative(opportunity_id: str) -> dict[str, Any]:
    """Inspect generation metadata and validation report for an opportunity."""
    from app import db

    opportunity = db.get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise CampaignOrchestratorError(f"Opportunity '{opportunity_id}' not found")
    generations = db.list_narrative_generation_records(opportunity_id=opportunity_id)
    return {
        "opportunity_id": opportunity_id,
        "narration": opportunity["narration"],
        "narration_source": opportunity["narration_source"],
        "generations": generations,
    }


def regenerate_narrative(opportunity_id: str) -> dict[str, Any]:
    """Regenerate phrasing for an opportunity without changing campaign/domain
    state. A new generation record is written; the opportunity's lifecycle and
    canon are untouched."""
    from app import db

    opportunity = db.get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise CampaignOrchestratorError(f"Opportunity '{opportunity_id}' not found")
    session = db.get_campaign_session_record(opportunity["session_id"])
    if not session:
        raise CampaignOrchestratorError("Opportunity session not found")

    context = compile_narrative_context(opportunity, session)
    provider = get_campaign_provider()
    result = NarrativeRuntime(provider=provider).narrate(context)
    _persist_narrative_generation(context, result, opportunity_id, None)

    if result.failure:
        return {
            "opportunity_id": opportunity_id,
            "narration": None,
            "failure": result.failure,
            "canonical_state": opportunity["lifecycle_state"],
        }

    narration = _output_dict(result.output, result)
    db.update_campaign_opportunity_state_record(
        opportunity_id,
        opportunity["lifecycle_state"],
        narration=narration["prose"],
        narration_source=narration.get("narration_source", "deterministic"),
    )
    return {
        "opportunity_id": opportunity_id,
        "narration": narration,
        "failure": None,
        "canonical_state": opportunity["lifecycle_state"],
    }


# ---------------------------------------------------------------------------
# Phase 20: multi-Aspect campaign surfaces. These coordinate switching and
# knowledge projection through the existing domain systems; they never merge
# viewpoints or leak private state across Aspects.
# ---------------------------------------------------------------------------


def list_campaign_aspects(campaign_id: str) -> dict[str, Any]:
    from app.multi_aspect import list_campaign_aspects as _list

    return _list(campaign_id)


def switch_campaign_aspect(
    campaign_id: str, session_id: str, target_soul_id: str
) -> dict[str, Any]:
    """Switch the active Aspect, then return the destination Aspect's view and a
    freshly evaluated opportunity set. Idempotent switching is a no-op for state
    but still returns the current view."""
    from app import db
    from app.multi_aspect import (
        active_soul_id,
        compile_aspect_view,
        switch_aspect,
    )

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")

    switch_result = switch_aspect(campaign_id, session_id, target_soul_id)
    session = switch_result["session"]
    view = compile_aspect_view(session)
    return {
        "switch": switch_result,
        "active_aspect": active_soul_id(session),
        "view": view,
    }


def inspect_aspect_view(session_id: str) -> dict[str, Any]:
    """Authorized-debug view of the active Aspect's bounded knowledge projection,
    including the canonical events it is *not* shown. Never mutates."""
    from app import db
    from app.multi_aspect import compile_aspect_view, knowledge_projection

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise CampaignOrchestratorError(f"Session '{session_id}' not found")
    return {
        "session_id": session_id,
        "active_aspect": session.get("active_soul_id") or session["soul_id"],
        "knowledge_projection": knowledge_projection(session).model_dump(),
        "view": compile_aspect_view(session),
    }


def resolve_cross_aspect_encounter(
    session_id: str, other_soul_id: str
) -> dict[str, Any]:
    from app.multi_aspect import resolve_cross_aspect_encounter as _resolve

    return _resolve(session_id, other_soul_id)


# ---------------------------------------------------------------------------
# Phase 21: Living Visual World integration. The Art Director decides which
# canonical moments deserve a painting; the runtime paints them asynchronously.
# ---------------------------------------------------------------------------


def queue_eligible_art_moments(session_id: str) -> dict[str, Any]:
    """Evaluate Art Director eligibility and enqueue queued VisualJobs. Never
    mutates canonical state; a VisualJob failure must not roll back history."""
    from app.living_visual import queue_art_moments

    return queue_art_moments(session_id)
