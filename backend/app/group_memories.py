# backend/app/group_memories.py
"""
SoulSmith Phase 13: Group Memories & Tags.

A Group Memory is a relational structure that links participant-specific
canonical Memory Objects to the same shared event. It never rewrites,
reconciles, or flattens those memories into one authoritative narrative.

> SHARED EVENT DOES NOT MEAN SHARED MEMORY.

Key invariants:

- Canonical grouping is keyed by exact shared ``event_id`` only. Semantic
  similarity may produce a *suggestion*, never a canonical assertion.
- Perspective differences (fear vs triumph vs the sound of a door closing) are
  preserved and made inspectable, never resolved by silently choosing a winner.
- Tags are typed and, where they reference canonical entities, anchored to
  stable historical IDs (PortraitVersions, VisualEntityVersions, Chronicle
  Paintings). Free-form descriptors are secondary metadata and are never a
  backdoor for inventing canon.
- Consent is participant-specific. Projecting a Group Memory for a viewer
  filters every private identity, portrait reference, StoryMark, and emotional
  detail according to existing public-canon/consent rules.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TagType = Literal[
    "person",
    "location",
    "relic",
    "phenomenon",
    "faction",
    "relationship",
    "emotional_theme",
    "event_type",
    "recurring_motif",
    "consequence",
    "thread",
]

AnchorType = Literal[
    "portrait",
    "location",
    "relic",
    "phenomenon",
    "chronicle_painting",
]

GroupSignificanceTier = Literal[
    "personal",
    "relationship",
    "community",
    "world",
    "legendary",
]

_TIER_RANK = {
    "personal": 0,
    "relationship": 1,
    "community": 2,
    "world": 3,
    "legendary": 4,
}


class GroupMemoryMemberModel(BaseModel):
    memory_object_id: str
    soul_id: str
    role_in_event: str | None = None
    portrait_version_id: str | None = None


class GroupMemoryTagModel(BaseModel):
    tag_id: str
    tag_type: TagType
    value: str
    anchor_kind: AnchorType | None = None
    anchor_id: str | None = None
    is_descriptor: bool = False


class GroupMemoryAnchorModel(BaseModel):
    anchor_type: AnchorType
    anchor_ref: str
    entity_id: str | None = None
    entity_type: str | None = None
    label: str


class GroupMemoryModel(BaseModel):
    group_id: str
    event_id: str
    title: str
    summary: str
    visibility: str = "public_canon"
    group_significance: GroupSignificanceTier = "personal"
    group_significance_score: int = Field(default=5, ge=1, le=10)
    group_significance_rationale: str | None = None
    members: list[GroupMemoryMemberModel] = Field(default_factory=list)
    tags: list[GroupMemoryTagModel] = Field(default_factory=list)
    anchors: list[GroupMemoryAnchorModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


# Request schemas


class CreateGroupMemoryRequest(BaseModel):
    event_id: str
    visibility: str = "public_canon"
    memory_object_ids: list[str] = Field(default_factory=list)


class AttachMemoryObjectRequest(BaseModel):
    memory_object_id: str
    soul_id: str
    role_in_event: str | None = None
    portrait_version_id: str | None = None


class AddGroupTagRequest(BaseModel):
    tag_type: TagType
    value: str
    anchor_kind: AnchorType | None = None
    anchor_id: str | None = None
    is_descriptor: bool = False


class AddGroupAnchorRequest(BaseModel):
    anchor_type: AnchorType
    anchor_ref: str
    label: str | None = None


# Perspective comparison (never reconciles; never mutates).


class ParticipantPerspectiveModel(BaseModel):
    soul_id: str
    character_name: str
    role_in_event: str | None = None
    memory_object_id: str
    event_title: str
    location_environment: str
    emotional_tone: str | None = None
    action_composition: str | None = None
    lasting_consequence: str | None = None
    is_self: bool = False
    is_public: bool = False


class PerspectiveComparisonModel(BaseModel):
    group_id: str
    event_id: str
    perspectives: list[ParticipantPerspectiveModel] = Field(default_factory=list)
    shared_facts: list[str] = Field(default_factory=list)
    disagreements: list[dict[str, Any]] = Field(default_factory=list)


class RelatedMemorySuggestionModel(BaseModel):
    memory_object_id: str
    event_id: str
    reason: str
    canonical: bool = False


# Pure helpers


def _derive_group_significance(
    memory_objects: list[dict[str, Any]],
) -> tuple[str, int, str]:
    """
    Derive a group-level significance signal from canonical participant/event
    information. Individual Memory Object significance is never overwritten.
    """
    if not memory_objects:
        return "personal", 5, "No linked memories; significance unknown."

    tiers = [mo.get("importance_tier", "personal") for mo in memory_objects]
    scores = [int(mo.get("importance_score", 5) or 5) for mo in memory_objects]
    max_score = max(1, min(10, max(scores)))

    if "world" in tiers:
        tier: GroupSignificanceTier = "legendary" if max_score >= 9 else "world"
    elif "community" in tiers:
        tier = "community"
    elif len(memory_objects) >= 2:
        tier = "relationship"
    else:
        tier = "personal"

    rationale = (
        f"Derived from {len(memory_objects)} linked memory object(s); "
        f"highest individual tier was {max(tiers, key=_tier_rank_for_importance)} "
        f"with score {max_score}/10."
    )
    return tier, max_score, rationale


def derive_group_significance(
    memory_objects: list[dict[str, Any]],
) -> tuple[str, int, str]:
    """Public wrapper for group-level significance derivation."""
    return _derive_group_significance(memory_objects)


def derive_title_summary(memory_objects: list[dict[str, Any]]) -> tuple[str, str]:
    """Public wrapper for safe title/summary derivation."""
    return _derive_title_summary(memory_objects)


def _tier_rank_for_importance(tier: str) -> int:
    return {"personal": 0, "community": 1, "world": 2}.get(tier, 0)


def _derive_title_summary(
    memory_objects: list[dict[str, Any]],
) -> tuple[str, str]:
    """
    Derive a title/summary from safe shared facts only. When no public fact is
    available the result stays generic so private identity/emotion never leaks.
    """
    if not memory_objects:
        return "A Shared Event", "The details of this shared event remain private."

    titles = {mo.get("event_title") for mo in memory_objects if mo.get("event_title")}
    locations = {
        mo.get("location_environment")
        for mo in memory_objects
        if mo.get("location_environment")
    }

    title = next(iter(sorted(titles))) if titles else "A Shared Event"
    location = next(iter(sorted(locations))) if locations else None

    parts = [f"{len(memory_objects)} participant(s) remember this event."]
    if location:
        parts.append(f"Location: {location}")
    summary = " ".join(parts)
    return title, summary


def _participant_is_public(memory_object: dict[str, Any], soul_id: str) -> bool:
    return memory_object.get(
        "privacy_consent_scope"
    ) == "public_canon" and _consent_allows_shared_gallery(soul_id)


def _consent_allows_shared_gallery(soul_id: str) -> bool:
    # Imported lazily to avoid a circular import with app.db.
    from app.db import get_or_create_visual_consent_record

    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return bool(consent.get("allow_shared_gallery", True))


def _memory_object_for(memory_object_id: str) -> dict[str, Any] | None:
    from app.db import get_memory_object_record

    return get_memory_object_record(memory_object_id)


def _portrait_owner(anchor_id: str | None) -> str | None:
    if not anchor_id:
        return None
    from app.db import get_portrait_version_record

    portrait = get_portrait_version_record(anchor_id)
    return portrait.get("soul_id") if portrait else anchor_id


def _participant_character_name(memory_object: dict[str, Any], soul_id: str) -> str:
    for participant in memory_object.get("participants", []):
        if participant.get("soul_id") == soul_id:
            return participant.get("character_name", soul_id)
    return soul_id


def derive_members_from_memory_objects(
    memory_objects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deterministically derive participant membership from Memory Objects. Each
    Memory Object is treated as one participant's memory; the participant is the
    first matching soul in its participant list (never inferred by similarity).
    """
    members: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for memory_object in memory_objects:
        participants = memory_object.get("participants", [])
        if not participants:
            continue
        first = participants[0]
        soul_id = first.get("soul_id")
        if not soul_id:
            continue
        key = (memory_object["id"], soul_id)
        if key in seen:
            continue
        seen.add(key)
        members.append(
            {
                "memory_object_id": memory_object["id"],
                "soul_id": soul_id,
                "role_in_event": first.get("role_in_event"),
                "portrait_version_id": first.get("portrait_version_id"),
            }
        )
    return members


def build_perspective_comparison(
    *,
    group_id: str,
    event_id: str,
    members: list[dict[str, Any]],
    viewer_soul_id: str | None,
) -> PerspectiveComparisonModel:
    """
    Build an inspectable, consent-filtered comparison of participant
    perspectives. Conflicting recollections are listed side by side and never
    reconciled into a single agreed narrative.
    """
    perspectives: list[ParticipantPerspectiveModel] = []
    visible_fields: dict[str, list[tuple[str, str]]] = {
        "emotional_tone": [],
        "action_composition": [],
        "lasting_consequence": [],
    }
    locations: list[str] = []

    for member in members:
        soul_id = member["soul_id"]
        memory_object = _memory_object_for(member["memory_object_id"])
        if not memory_object:
            continue

        is_self = soul_id == viewer_soul_id
        is_public = _participant_is_public(memory_object, soul_id)

        # Private, non-self participants are omitted entirely so their identity
        # and emotional content never leak through counts or metadata.
        if not is_self and not is_public:
            continue

        perspectives.append(
            ParticipantPerspectiveModel(
                soul_id=soul_id,
                character_name=_participant_character_name(memory_object, soul_id),
                role_in_event=member.get("role_in_event"),
                memory_object_id=member["memory_object_id"],
                event_title=memory_object.get("event_title", ""),
                location_environment=memory_object.get("location_environment", ""),
                emotional_tone=memory_object.get("emotional_tone"),
                action_composition=memory_object.get("action_composition"),
                lasting_consequence=memory_object.get("lasting_consequence"),
                is_self=is_self,
                is_public=is_public,
            )
        )

        locations.append(memory_object.get("location_environment", ""))
        visible_fields["emotional_tone"].append(
            (soul_id, memory_object.get("emotional_tone", ""))
        )
        visible_fields["action_composition"].append(
            (soul_id, memory_object.get("action_composition", ""))
        )
        visible_fields["lasting_consequence"].append(
            (soul_id, memory_object.get("lasting_consequence", ""))
        )

    # Shared facts are the deterministic intersection of safe canonical fields,
    # derived only (never written back to any Memory Object).
    shared_facts: list[str] = []
    if locations and all(loc == locations[0] for loc in locations):
        shared_facts.append(f"Location: {locations[0]}")

    disagreements: list[dict[str, Any]] = []
    for field, values in visible_fields.items():
        unique = {value for _, value in values}
        if len(unique) > 1:
            disagreements.append(
                {
                    "field": field,
                    "perspectives": [
                        {"soul_id": soul_id, field: value} for soul_id, value in values
                    ],
                }
            )

    return PerspectiveComparisonModel(
        group_id=group_id,
        event_id=event_id,
        perspectives=perspectives,
        shared_facts=shared_facts,
        disagreements=disagreements,
    )


def project_group_for_viewer(
    *,
    group: dict[str, Any],
    members: list[dict[str, Any]],
    tags: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    viewer_soul_id: str | None,
) -> GroupMemoryModel:
    """
    Produce a consent-filtered Group Memory projection for a specific viewer.

    - Public members are included only when their Memory Object is public canon
      and the soul consents to shared gallery.
    - The viewer always sees their own member link, regardless of privacy.
    - Title/summary are re-derived from public facts so private identity and
      emotion never leak through generated summaries or metadata.
    - Anchors referencing private participants' portrait versions are omitted.
    """
    visible_members: list[GroupMemoryMemberModel] = []
    public_memory_objects: list[dict[str, Any]] = []

    for member in members:
        soul_id = member["soul_id"]
        memory_object = _memory_object_for(member["memory_object_id"])
        if not memory_object:
            continue
        is_self = soul_id == viewer_soul_id
        is_public = _participant_is_public(memory_object, soul_id)
        if not is_self and not is_public:
            continue
        if is_public:
            public_memory_objects.append(memory_object)
        visible_members.append(
            GroupMemoryMemberModel(
                memory_object_id=member["memory_object_id"],
                soul_id=soul_id,
                role_in_event=member.get("role_in_event"),
                portrait_version_id=member.get("portrait_version_id"),
            )
        )

    title, summary = _derive_title_summary(public_memory_objects)

    # Only keep portrait anchors that belong to a visible member; other anchor
    # types (location/relic/phenomenon/painting) are safe shared references.
    visible_soul_ids = {m.soul_id for m in visible_members}
    visible_anchors: list[GroupMemoryAnchorModel] = []
    for anchor in anchors:
        # Portrait anchors carry the owning soul via entity_id.
        if (
            anchor.get("anchor_type") == "portrait"
            and anchor.get("entity_id") not in visible_soul_ids
        ):
            continue
        visible_anchors.append(GroupMemoryAnchorModel(**anchor))

    # Strip tags that would leak a hidden participant's identity or emotion.
    visible_tags: list[GroupMemoryTagModel] = []
    for tag in tags:
        if tag.get("tag_type") == "person":
            anchor_id = tag.get("anchor_id")
            if anchor_id and _portrait_owner(anchor_id) not in visible_soul_ids:
                continue
        visible_tags.append(GroupMemoryTagModel(**tag))

    return GroupMemoryModel(
        group_id=group["group_id"],
        event_id=group["event_id"],
        title=title,
        summary=summary,
        visibility=group.get("visibility", "public_canon"),
        group_significance=group.get("group_significance", "personal"),
        group_significance_score=group.get("group_significance_score", 5),
        group_significance_rationale=group.get("group_significance_rationale"),
        members=visible_members,
        tags=visible_tags,
        anchors=visible_anchors,
        created_at=group.get("created_at"),
        updated_at=group.get("updated_at"),
    )


def suggest_related_by_similarity(
    *,
    memory_object_id: str,
    limit: int = 10,
) -> list[RelatedMemorySuggestionModel]:
    """
    Return *suggestions* of Memory Objects that may describe the same event
    based on title/participant similarity. These are never canonical grouping
    assertions; deterministic exact-event grouping is the only canonical path.
    """
    from app.db import get_memory_object_record, get_memory_objects_records

    source = get_memory_object_record(memory_object_id)
    if not source:
        return []

    source_title = (source.get("event_title") or "").lower()
    source_souls = {p.get("soul_id") for p in source.get("participants", [])}

    suggestions: list[RelatedMemorySuggestionModel] = []
    for candidate in get_memory_objects_records():
        if candidate["id"] == memory_object_id:
            continue
        if candidate.get("event_id") == source.get("event_id"):
            # Exact shared event IDs are canonical, not a "suggestion".
            continue

        reasons: list[str] = []
        cand_title = (candidate.get("event_title") or "").lower()
        if source_title and cand_title and source_title == cand_title:
            reasons.append("identical event title")
        cand_souls = {p.get("soul_id") for p in candidate.get("participants", [])}
        if source_souls & cand_souls:
            reasons.append("overlapping participants")

        if reasons:
            suggestions.append(
                RelatedMemorySuggestionModel(
                    memory_object_id=candidate["id"],
                    event_id=candidate["event_id"],
                    reason="; ".join(reasons),
                    canonical=False,
                )
            )

    return suggestions[:limit]
