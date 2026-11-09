# backend/app/relationship.py
"""
SoulSmith Phase 19: Relationship & Promise Engine.

> A RELATIONSHIP IS HISTORY BETWEEN PEOPLE. A PROMISE IS A CLAIM ON THE FUTURE.
> NEITHER MAY BE INVENTED BY THE NARRATOR.

This module gives relationships and promises first-class, provenance-backed
persistence so bonds between people can become durable story machinery across
encounters, Aspects, generations, relics, and World Memory.

The engine separates four layers that must never collapse into each other:

- **canonical interaction**  (what the Chronicle records actually happened),
- **participant perspective** (how one party remembers/interprets the bond),
- **public/world interpretation** (what World Memory/NPCs later believe), and
- **narrator presentation**  (how the Soulkeeper phrases it).

It holds the persistent data models plus the pure, deterministic helpers for
lifecycle validation, evidence-backed fulfillment/breach evaluation, consent
filtering, and NPC knowledge projection. Persistence lives in ``db.py`` and
the orchestrator/narrative wiring lives in ``campaign.py`` /
``campaign_orchestrator.py`` / ``narrative_context_compiler.py``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

RELATIONSHIP_ENGINE_VERSION = "1.0.0"

# Structured, extensible relationship kinds. Do not infer sensitive/intimate
# categories from prose; these exist only when the game/player establishes them.
KNOWN_RELATIONSHIP_KINDS: frozenset[str] = frozenset(
    {
        "family_lineage",
        "friendship",
        "alliance",
        "mentorship",
        "rivalry",
        "adversarial",
        "romantic",
        "duty_service",
        "factional",
        "creator_creation",
        "bearer_relic_bond",
        "custom_other",
    }
)

KNOWN_RELATIONSHIP_STATUSES: frozenset[str] = frozenset(
    {"active", "distant", "ended", "unknown", "historical"}
)

KNOWN_RELATIONSHIP_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "met",
        "allied",
        "separated",
        "reconciled",
        "betrayed",
        "protected",
        "rescued",
        "challenged",
        "taught",
        "inherited_responsibility",
        "promise_made",
        "promise_acknowledged",
        "promise_disputed",
        "promise_fulfilled",
        "promise_broken",
        "promise_released",
        "relationship_ended",
    }
)

# Promise lifecycle states. The original promise remains immutable historical
# evidence even as this state evolves.
KNOWN_PROMISE_STATES: frozenset[str] = frozenset(
    {
        "proposed",
        "made",
        "acknowledged",
        "active",
        "fulfilled",
        "broken",
        "released",
        "impossible",
        "disputed",
        "inherited",
        "transferred",
        "forgotten",
        "rediscovered",
        "unresolved",
    }
)

KNOWN_PROMISE_PARTICIPANT_TYPES: frozenset[str] = frozenset(
    {"recipient", "beneficiary", "witness"}
)

KNOWN_PROMISE_LINK_TYPES: frozenset[str] = frozenset(
    {"relic", "place", "group", "relationship"}
)

# Evidence kinds a promise resolution may cite. ``player_authorized`` is only
# valid for inherently subjective/negotiated conditions; it never substitutes
# for a canonical event when one is required.
KNOWN_PROMISE_EVIDENCE_TYPES: frozenset[str] = frozenset(
    {"chronicle_event", "relic_event", "player_authorized"}
)

# Valid state transitions. Every meaningful transition must cite evidence for
# fulfillment/breach/release/inheritance/transfer, or be a deliberate player
# authorization. Forgotten/rediscovered represent knowledge state, never
# deletion of the original promise.
PROMISE_TRANSITIONS: dict[str, frozenset[str]] = {
    "proposed": frozenset({"made", "released", "forgotten"}),
    "made": frozenset(
        {
            "acknowledged",
            "active",
            "fulfilled",
            "broken",
            "released",
            "disputed",
            "impossible",
            "forgotten",
            "unresolved",
        }
    ),
    "acknowledged": frozenset(
        {
            "active",
            "fulfilled",
            "broken",
            "released",
            "disputed",
            "impossible",
            "forgotten",
            "unresolved",
        }
    ),
    "active": frozenset(
        {
            "fulfilled",
            "broken",
            "released",
            "disputed",
            "impossible",
            "forgotten",
            "inherited",
            "transferred",
            "unresolved",
        }
    ),
    "fulfilled": frozenset({"disputed", "rediscovered"}),
    "broken": frozenset({"disputed", "rediscovered", "released"}),
    "released": frozenset({"rediscovered", "forgotten"}),
    "impossible": frozenset({"released", "forgotten", "disputed"}),
    "disputed": frozenset(
        {"active", "fulfilled", "broken", "released", "unresolved", "forgotten"}
    ),
    "inherited": frozenset({"active", "fulfilled", "broken", "released", "forgotten"}),
    "transferred": frozenset(
        {"active", "fulfilled", "broken", "released", "forgotten"}
    ),
    "forgotten": frozenset({"rediscovered", "released"}),
    "rediscovered": frozenset(
        {"active", "fulfilled", "broken", "released", "disputed", "unresolved"}
    ),
    "unresolved": frozenset(
        {"active", "fulfilled", "broken", "released", "disputed", "impossible"}
    ),
}

# Resolution states that require evidence (a canonical source event or an
# explicit, authorized player resolution of a subjective condition).
EVIDENCE_BACKED_STATES: frozenset[str] = frozenset(
    {"fulfilled", "broken", "released", "inherited", "transferred"}
)


class RelationshipSourceRef(BaseModel):
    """A provenance link to the canonical interaction that establishes a bond."""

    source_type: str
    source_id: str
    claim_kind: str = "canonical_fact"


class RelationshipParticipant(BaseModel):
    entity_type: str
    entity_id: str
    role: str = "participant"


class RelationshipEventModel(BaseModel):
    event_id: str
    relationship_id: str
    event_type: str
    source_type: str
    source_id: str
    summary: str = ""
    created_at: str | None = None


class RelationshipPerspectiveModel(BaseModel):
    """One participant's interpretation. Never objective emotional truth."""

    perspective_id: str
    relationship_id: str
    entity_type: str
    entity_id: str
    kind: str
    view: str = ""
    is_canonical_interaction: bool = False
    visibility: str = "public_canon"
    created_at: str | None = None


class RelationshipEntityLinkModel(BaseModel):
    link_id: str
    relationship_id: str
    link_type: str
    entity_type: str
    entity_id: str
    created_at: str | None = None


class RelationshipModel(BaseModel):
    relationship_id: str
    kinds: list[str] = Field(default_factory=list)
    status: str = "active"
    visibility: str = "public_canon"
    creation_context: str = ""
    participants: list[RelationshipParticipant] = Field(default_factory=list)
    source_refs: list[RelationshipSourceRef] = Field(default_factory=list)
    events: list[RelationshipEventModel] = Field(default_factory=list)
    perspectives: list[RelationshipPerspectiveModel] = Field(default_factory=list)
    entity_links: list[RelationshipEntityLinkModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class PromiseParticipantModel(BaseModel):
    participant_type: str = "recipient"  # recipient | beneficiary | witness
    entity_type: str
    entity_id: str


class PromiseStateChangeModel(BaseModel):
    state_id: str
    promise_id: str
    previous_state: str
    new_state: str
    evidence_type: str | None = None
    evidence_id: str | None = None
    reason: str = ""
    created_at: str | None = None


class PromiseEntityLinkModel(BaseModel):
    link_id: str
    promise_id: str
    link_type: str
    entity_type: str
    entity_id: str
    created_at: str | None = None


class PromiseModel(BaseModel):
    promise_id: str
    promisor_entity_type: str
    promisor_entity_id: str
    promise_text: str
    structured_meaning: dict[str, Any] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    scope: str = "personal"
    visibility: str = "public_canon"
    source_type: str
    source_id: str
    source_authorization: str = "canonical_event"
    lifecycle_state: str = "made"
    inheritable: bool = False
    transferable: bool = False
    participants: list[PromiseParticipantModel] = Field(default_factory=list)
    state_history: list[PromiseStateChangeModel] = Field(default_factory=list)
    entity_links: list[PromiseEntityLinkModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


# Request schemas


class CreateRelationshipRequest(BaseModel):
    kinds: list[str] = Field(default_factory=list)
    participants: list[RelationshipParticipant] = Field(default_factory=list)
    source_type: str | None = None
    source_id: str | None = None
    creation_context: str = ""
    visibility: str = "public_canon"
    status: str = "active"


class AddRelationshipEventRequest(BaseModel):
    event_type: str
    source_type: str
    source_id: str
    summary: str = ""


class AddRelationshipPerspectiveRequest(BaseModel):
    entity_type: str
    entity_id: str
    kind: str
    view: str = ""
    is_canonical_interaction: bool = False
    visibility: str = "public_canon"


class LinkRelationshipEntityRequest(BaseModel):
    link_type: str
    entity_type: str
    entity_id: str


class CreatePromiseRequest(BaseModel):
    promisor_entity_type: str
    promisor_entity_id: str
    promise_text: str
    structured_meaning: dict[str, Any] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    scope: str = "personal"
    visibility: str = "public_canon"
    source_type: str
    source_id: str
    source_authorization: str = "canonical_event"
    participants: list[PromiseParticipantModel] = Field(default_factory=list)
    inheritable: bool = False
    transferable: bool = False


class TransitionPromiseRequest(BaseModel):
    new_state: str
    evidence_type: str | None = None
    evidence_id: str | None = None
    player_authorized: bool = False
    reason: str = ""
    target_entity_type: str | None = None
    target_entity_id: str | None = None


class EvaluatePromiseRequest(BaseModel):
    candidate_state: str  # fulfilled | broken
    evidence_type: str | None = None
    evidence_id: str | None = None
    player_authorized: bool = False
    reason: str = ""


class LinkPromiseEntityRequest(BaseModel):
    link_type: str
    entity_type: str
    entity_id: str


class RelationshipPromiseNPCKnowledgeRequest(BaseModel):
    subject_entity_type: str = "person"
    subject_entity_id: str = ""
    npc_id: str = "npc_default"
    culture: str = ""
    location: str = ""
    era_context: str = ""
    social_role: str = (
        "commoner"  # commoner | archivist | descendant | scholar | priest
    )
    access_to_archives: bool = False
    education_level: str = "low"
    local_tradition: bool = True
    direct_relationship: bool = False
    secrecy_aware: bool = False


class RelationshipKnowledgeEntryModel(BaseModel):
    relationship: RelationshipModel | None = None
    promise: PromiseModel | None = None
    fidelity: str = "faithful"  # faithful | degraded | forgotten_hint
    reason: str


class RelationshipPromiseKnowledgeProjectionModel(BaseModel):
    npc: dict[str, Any]
    subject_entity_type: str
    subject_entity_id: str
    relationships: list[RelationshipKnowledgeEntryModel] = Field(default_factory=list)
    promises: list[RelationshipKnowledgeEntryModel] = Field(default_factory=list)


# Consent / visibility helpers. A public event does not automatically make a
# private relationship interpretation public.


def _consent_allows_shared_gallery(soul_id: str) -> bool:
    from app.db import get_or_create_visual_consent_record

    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return bool(consent.get("allow_shared_gallery", True))


def _entity_is_viewer(entity_id: str, viewer_soul_id: str | None) -> bool:
    return entity_id == viewer_soul_id


def relationship_visible_to(rel: dict[str, Any], viewer_soul_id: str | None) -> bool:
    """A public relationship is visible; a private one only to its participants."""
    if rel.get("visibility") == "public_canon":
        return True
    if viewer_soul_id is None:
        return False
    for participant in rel.get("participants", []) or []:
        if participant.get("entity_id") == viewer_soul_id:
            return True
    return False


def promise_visible_to(promise: dict[str, Any], viewer_soul_id: str | None) -> bool:
    """A public promise is visible; private/secret promises only to participants."""
    visibility = promise.get("visibility")
    if visibility == "public_canon":
        return True
    if viewer_soul_id is None:
        return False
    if promise.get("promisor_entity_id") == viewer_soul_id:
        return True
    for participant in promise.get("participants", []) or []:
        if participant.get("entity_id") == viewer_soul_id:
            return True
    return False


def project_relationship_for_viewer(
    relationship: dict[str, Any], viewer_soul_id: str | None
) -> dict[str, Any]:
    """Return a consent-safe copy. Private relationships are stripped, never
    mutated on the stored row."""
    projected = dict(relationship)
    if not relationship_visible_to(relationship, viewer_soul_id):
        projected["participants"] = []
        projected["source_refs"] = []
        projected["events"] = []
        projected["perspectives"] = []
        projected["entity_links"] = []
        projected["visibility"] = "private"
    return projected


def project_promise_for_viewer(
    promise: dict[str, Any], viewer_soul_id: str | None
) -> dict[str, Any]:
    """Return a consent-safe copy. Private promises are stripped, never mutated."""
    projected = dict(promise)
    if not promise_visible_to(promise, viewer_soul_id):
        projected["promise_text"] = ""
        projected["structured_meaning"] = {}
        projected["conditions"] = []
        projected["participants"] = []
        projected["state_history"] = []
        projected["entity_links"] = []
        projected["visibility"] = "private"
    return projected


# Lifecycle validation and evidence-backed resolution.


class PromiseTransitionError(ValueError):
    """Raised when a promise state transition is not authorized by evidence."""


def _transition_allowed(current: str, new_state: str) -> bool:
    return new_state in PROMISE_TRANSITIONS.get(current, frozenset())


def _require_evidence(
    new_state: str,
    *,
    evidence_type: str | None,
    evidence_id: str | None,
    player_authorized: bool,
    promise: dict[str, Any],
) -> None:
    """Enforce that fulfillment/breach/release/inheritance/transfer are backed by
    evidence. Inheritance/transfer additionally require explicit provenance
    (a target entity), never narrative drama."""
    if new_state not in EVIDENCE_BACKED_STATES:
        return
    if new_state in ("inherited", "transferred"):
        if not player_authorized and not evidence_id:
            raise PromiseTransitionError(
                f"Promise '{new_state}' requires explicit provenance: "
                "a canonical source or an authorized domain action."
            )
        return
    if evidence_id:
        return
    if player_authorized and promise.get("source_authorization") == "player_authorized":
        return
    # Subjective/negotiated conditions may be resolved explicitly by the player.
    if player_authorized and any(
        "subjective" in c.lower() or "negotiated" in c.lower()
        for c in (promise.get("conditions", []) or [])
    ):
        return
    raise PromiseTransitionError(
        f"Promise '{new_state}' requires canonical evidence or an authorized "
        "player resolution of a subjective condition."
    )


def validate_promise_transition(
    promise: dict[str, Any],
    new_state: str,
    *,
    evidence_type: str | None = None,
    evidence_id: str | None = None,
    player_authorized: bool = False,
    target_entity_type: str | None = None,
    target_entity_id: str | None = None,
) -> None:
    """Validate a requested state transition without mutating anything."""
    if new_state not in KNOWN_PROMISE_STATES:
        raise PromiseTransitionError(f"Unknown promise state '{new_state}'.")
    current = promise.get("lifecycle_state", "made")
    if new_state == current:
        return  # idempotent, no history row needed
    if not _transition_allowed(current, new_state):
        raise PromiseTransitionError(
            f"Invalid promise transition '{current}' -> '{new_state}'."
        )
    _require_evidence(
        new_state,
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        player_authorized=player_authorized,
        promise=promise,
    )
    if new_state in ("inherited", "transferred") and (
        not target_entity_type or not target_entity_id
    ):
        raise PromiseTransitionError(
            f"Promise '{new_state}' requires a target entity "
            "(inheritor/transferee) with provenance."
        )


def evaluate_promise_resolution(
    promise: dict[str, Any],
    candidate_state: str,
    *,
    evidence_type: str | None = None,
    evidence_id: str | None = None,
    player_authorized: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    """Return an inspectable verdict for a fulfillment/breach candidate. Where
    evidence is ambiguous, the verdict is 'disputed'/'unresolved', never a forced
    verdict."""
    if candidate_state not in ("fulfilled", "broken"):
        raise PromiseTransitionError(
            f"Only fulfillment/breach can be evaluated; got '{candidate_state}'."
        )
    try:
        validate_promise_transition(
            promise,
            candidate_state,
            evidence_type=evidence_type,
            evidence_id=evidence_id,
            player_authorized=player_authorized,
        )
    except PromiseTransitionError as exc:
        return {
            "verdict": "disputed",
            "candidate_state": candidate_state,
            "authorized": False,
            "reason": str(exc),
        }
    return {
        "verdict": candidate_state,
        "candidate_state": candidate_state,
        "authorized": True,
        "reason": reason or "Evidence satisfies the requested resolution.",
        "evidence": {"type": evidence_type, "id": evidence_id},
    }


# Significance ranking: derived scheduling metadata, never canonical affection.


def derive_relationship_significance(relationship: dict[str, Any]) -> int:
    """A derived, inspectable scheduling score. It is *not* an affection meter and
    never becomes canonical emotional truth."""
    score = 1
    score += len(relationship.get("events", []) or [])
    score += 2 * len(relationship.get("source_refs", []) or [])
    score += len(relationship.get("entity_links", []) or [])
    return score


# NPC knowledge projection (extends Phase 16). An NPC never receives canonical
# database truth merely because a promise/relationship exists.


def project_relationship_promise_npc_knowledge(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    npc: RelationshipPromiseNPCKnowledgeRequest,
    relationships: list[dict[str, Any]],
    promises: list[dict[str, Any]],
) -> RelationshipPromiseKnowledgeProjectionModel:
    """Project what an in-world character could plausibly know about a subject's
    relationships/promises. Secret/private promises are excluded unless the NPC
    has a direct relationship or explicit secrecy awareness."""
    rel_entries: list[RelationshipKnowledgeEntryModel] = []
    promise_entries: list[RelationshipKnowledgeEntryModel] = []

    for rel in relationships:
        if not _npc_can_see_relationship(rel, npc, subject_entity_id):
            continue
        rel_entries.append(
            RelationshipKnowledgeEntryModel(
                relationship=RelationshipModel(**rel),
                fidelity="faithful",
                reason="A public relationship the NPC can know about.",
            )
        )

    for promise in promises:
        if not _npc_can_see_promise(promise, npc, subject_entity_id):
            continue
        fidelity = (
            "faithful" if promise.get("visibility") == "public_canon" else "degraded"
        )
        promise_entries.append(
            RelationshipKnowledgeEntryModel(
                promise=PromiseModel(**promise),
                fidelity=fidelity,
                reason=(
                    "The NPC holds the promise through legitimate, public access."
                    if fidelity == "faithful"
                    else "The NPC knows only an uncertain hint of a secret promise."
                ),
            )
        )

    return RelationshipPromiseKnowledgeProjectionModel(
        npc=npc.model_dump(),
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        relationships=rel_entries,
        promises=promise_entries,
    )


def _npc_can_see_relationship(
    rel: dict[str, Any],
    npc: RelationshipPromiseNPCKnowledgeRequest,
    subject_entity_id: str,
) -> bool:
    if rel.get("visibility") == "public_canon":
        return True
    return bool(npc.direct_relationship)


def _npc_can_see_promise(
    promise: dict[str, Any],
    npc: RelationshipPromiseNPCKnowledgeRequest,
    subject_entity_id: str,
) -> bool:
    visibility = promise.get("visibility")
    if visibility == "public_canon":
        return True
    return not (
        visibility in ("private", "secret")
        and not (npc.direct_relationship or npc.secrecy_aware)
    )
