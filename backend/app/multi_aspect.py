# backend/app/multi_aspect.py
"""
SoulSmith Phase 20: multi-Aspect campaign sessions and knowledge boundaries.

> THE PLAYER MAY KNOW THE WHOLE STORY. EACH ASPECT KNOWS ONLY THE LIFE THEY
> HAVE LIVED.

This module makes the Phase 0-19 knowledge layers operational during active play:

- **canonical truth**  — what the Chronicle records actually happened,
- **player knowledge** — the whole campaign-level view the controlling player
  is permitted to see,
- **Aspect knowledge** — what the currently active playable Aspect has
  legitimately experienced through provenance-backed systems,
- **NPC knowledge**    — a consent-safe projection derived from World Memory,
- **World Memory**     — derived cultural belief, never canonical history.

An Aspect may feel familiarity only when an existing system legitimately
supplies it (Soul Constellation, Relic Recognition, Probable Paths, World
Memory, Relationships/Promises). Raw provider/model memory is never knowledge
provenance.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

MULTI_ASPECT_VERSION = "1.0.0"


def active_soul_id(session: dict[str, Any]) -> str:
    """Resolve the currently active Aspect for a session. Falls back to the
    session's default ``soul_id`` for pre-Phase-20 rows."""
    return session.get("active_soul_id") or session.get("soul_id")


class CampaignAspectModel(BaseModel):
    campaign_id: str
    soul_id: str
    aspect_id: str | None = None
    display_name: str
    viewpoint_location: str | None = None
    is_active: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class RegisterCampaignAspectRequest(BaseModel):
    campaign_id: str
    soul_id: str
    display_name: str | None = None
    aspect_id: str | None = None
    viewpoint_location: str | None = None


class SwitchAspectRequest(BaseModel):
    campaign_id: str
    session_id: str
    target_soul_id: str


class AspectKnowledgeProjectionModel(BaseModel):
    """A bounded, inspectable statement of what one Aspect may know. It is a
    projection, never a copy of canonical truth, and never the player's
    omniscient view."""

    aspect_soul_id: str
    campaign_id: str
    visible_events: list[str] = Field(default_factory=list)
    seeds: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    threads: list[str] = Field(default_factory=list)
    relics: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    promises: list[str] = Field(default_factory=list)
    world_memories: list[str] = Field(default_factory=list)
    forbidden_events: list[str] = Field(default_factory=list)
    provenance_ids: list[str] = Field(default_factory=list)


class CrossAspectEncounterRequest(BaseModel):
    session_id: str
    other_soul_id: str


def _aspect_id_for(constellation: dict[str, Any], soul_id: str) -> str | None:
    for aspect in constellation.get("aspects", []):
        if aspect.get("aspect_name") == soul_id or aspect.get("id") == soul_id:
            return aspect.get("id")
    return None


def ensure_campaign_aspect_registered(
    campaign_id: str,
    soul_id: str,
    display_name: str | None = None,
    viewpoint_location: str | None = None,
) -> dict[str, Any]:
    """Register an Aspect as playable in a campaign (idempotent), linking it to
    its Constellation Aspect when one exists."""
    from app import db

    constellation = db.get_or_create_primary_constellation()
    aspect_id = _aspect_id_for(constellation, soul_id)
    return db.ensure_campaign_aspect(
        campaign_id=campaign_id,
        soul_id=soul_id,
        display_name=display_name or soul_id,
        aspect_id=aspect_id,
        viewpoint_location=viewpoint_location,
    )


def list_campaign_aspects(campaign_id: str) -> dict[str, Any]:
    from app import db

    aspects = db.list_campaign_aspect_records(campaign_id)
    return {"campaign_id": campaign_id, "aspects": aspects}


def switch_aspect(
    campaign_id: str, session_id: str, target_soul_id: str
) -> dict[str, Any]:
    """Switch the active Aspect, persisting the departing Aspect's state and
    loading the destination Aspect's viewpoint. Idempotent: switching to the
    already-active Aspect returns without creating a new switch record."""
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found")
    if session["campaign_id"] != campaign_id:
        raise ValueError("Session does not belong to the requested campaign")

    # Ensure both aspects are registered playable Aspects.
    ensure_campaign_aspect_registered(campaign_id, session["soul_id"])
    target = ensure_campaign_aspect_registered(campaign_id, target_soul_id)

    current = active_soul_id(session)
    if current == target_soul_id:
        db.set_campaign_aspect_active(campaign_id, target_soul_id)
        return {
            "session": db.get_campaign_session_record(session_id),
            "from_soul_id": current,
            "to_soul_id": target_soul_id,
            "idempotent": True,
        }

    # Persist the departing Aspect's viewpoint (structured state lives in the
    # domain tables keyed by soul_id, which are untouched by switching).
    db.update_campaign_aspect_viewpoint(
        campaign_id,
        current,
        db.get_campaign_aspect_record(campaign_id, current)["viewpoint_location"] or "",
    )

    # Load the destination Aspect and mark it active.
    db.set_campaign_session_active_soul(session_id, target_soul_id)
    db.set_campaign_aspect_active(campaign_id, target_soul_id)
    db.create_aspect_switch_record(
        campaign_id=campaign_id,
        session_id=session_id,
        from_soul_id=current,
        to_soul_id=target_soul_id,
        idempotent=False,
    )

    return {
        "session": db.get_campaign_session_record(session_id),
        "from_soul_id": current,
        "to_soul_id": target_soul_id,
        "idempotent": False,
        "viewpoint": target.get("viewpoint_location"),
    }


def _visible_relationships(soul_id: str) -> list[dict[str, Any]]:
    from app import db
    from app.relationship import relationship_visible_to

    return [
        rel
        for rel in db.list_relationship_records()
        if relationship_visible_to(rel, soul_id)
    ]


def _visible_promises(soul_id: str) -> list[dict[str, Any]]:
    from app import db
    from app.relationship import promise_visible_to

    return [p for p in db.list_promise_records() if promise_visible_to(p, soul_id)]


def compile_aspect_view(session: dict[str, Any]) -> dict[str, Any]:
    """Compile the currently-active Aspect's bounded knowledge view. This is the
    authoritative projection used by the orchestrator and the inspection API; it
    never includes another Aspect's private data."""
    from app import db
    from app.world_memory import (
        memory_object_visible_to,
        world_memory_visible_to,
    )

    soul_id = active_soul_id(session)
    events = db.get_canonical_events_for_soul(soul_id)
    all_events = db.get_all_canonical_events()
    world_memories = [
        m for m in db.list_world_memory_records() if world_memory_visible_to(m, soul_id)
    ]
    memory_objects = [
        mo
        for mo in db.get_memory_objects_records()
        if memory_object_visible_to(mo, soul_id)
    ]
    relationships = _visible_relationships(soul_id)
    promises = _visible_promises(soul_id)

    return {
        "aspect_soul_id": soul_id,
        "campaign_id": session["campaign_id"],
        "session_id": session["session_id"],
        "seeds": db.get_seeds_for_soul(soul_id),
        "open_questions": db.get_open_questions_for_soul(soul_id),
        "threads": db.get_all_local_threads(soul_id=soul_id),
        "probable_paths": db.get_probable_paths_records(soul_id=soul_id),
        "relics": db.get_or_create_relics_records(soul_id=soul_id),
        "constellation": db.get_or_create_primary_constellation(),
        "memory_objects": memory_objects,
        "world_memories": world_memories,
        "relationships": relationships,
        "promises": promises,
        "events": events,
        "recent_event": events[0] if events else None,
        "campaign_event_count": len(all_events),
        "aspect_event_count": len(events),
    }


def knowledge_projection(session: dict[str, Any]) -> AspectKnowledgeProjectionModel:
    """A compact, inspectable statement of Aspect knowledge vs forbidden data.
    ``forbidden_events`` is the canonical truth the Aspect is *not* shown."""
    view = compile_aspect_view(session)
    soul_id = view["aspect_soul_id"]
    visible_event_ids = {e["id"] for e in view["events"]}
    from app import db

    all_event_ids = {e["id"] for e in db.get_all_canonical_events()}
    return AspectKnowledgeProjectionModel(
        aspect_soul_id=soul_id,
        campaign_id=view["campaign_id"],
        visible_events=sorted(visible_event_ids),
        seeds=[s["id"] for s in view["seeds"]],
        questions=[q["id"] for q in view["open_questions"]],
        threads=[t["id"] for t in view["threads"]],
        relics=[r["id"] for r in view["relics"]],
        relationships=[r["relationship_id"] for r in view["relationships"]],
        promises=[p["promise_id"] for p in view["promises"]],
        world_memories=[m["memory_id"] for m in view["world_memories"]],
        forbidden_events=sorted(all_event_ids - visible_event_ids),
        provenance_ids=[f"{e['id']}" for e in view["events"]],
    )


def resolve_cross_aspect_encounter(
    session_id: str, other_soul_id: str
) -> dict[str, Any]:
    """Resolve a meeting between the active Aspect and another playable Aspect.
    Each receives a viewpoint-specific projection; the shared canonical event is
    one event with participant perspectives, never duplicated contradictory
    canon. No private knowledge crosses the boundary."""
    from app import db

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found")
    current = active_soul_id(session)
    if current == other_soul_id:
        raise ValueError("An Aspect cannot meet itself")

    ensure_campaign_aspect_registered(session["campaign_id"], other_soul_id)

    current_view = compile_aspect_view(session)
    # The other Aspect's view is compiled from its own structured state, never
    # from the current Aspect's view or the player's omniscient knowledge.
    other_session = dict(session)
    other_session["active_soul_id"] = other_soul_id
    other_view = compile_aspect_view(other_session)

    return {
        "shared_event": {
            "event_type": "cross_aspect_meeting",
            "participants": [current, other_soul_id],
            "canonical": "One shared event with participant perspectives.",
        },
        "active_aspect": {
            "soul_id": current,
            "visible_relationships": [
                r["relationship_id"] for r in current_view["relationships"]
            ],
            "visible_promises": [p["promise_id"] for p in current_view["promises"]],
            "seeds": [s["id"] for s in current_view["seeds"]],
        },
        "other_aspect": {
            "soul_id": other_soul_id,
            "visible_relationships": [
                r["relationship_id"] for r in other_view["relationships"]
            ],
            "visible_promises": [p["promise_id"] for p in other_view["promises"]],
            "seeds": [s["id"] for s in other_view["seeds"]],
        },
        "knowledge_boundary": {
            "active_aspect_sees_other_private_events": False,
            "other_aspect_sees_active_private_events": False,
        },
    }
