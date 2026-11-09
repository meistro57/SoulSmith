# backend/app/world_memory.py
"""
SoulSmith Phase 16: Legendary Figures & World Memory.

> HISTORY MAY BECOME LEGEND. LEGEND MUST NEVER BECOME HISTORY BY ACCIDENT.

World Memory is the derived, cultural interpretation of canonical Chronicle
history. It is never authoritative: the Chronicle, Memory Objects, Group
Memories, Living Biographies, relics, and approved visual history remain the
source of truth, and no legend, monument, song, or rumor may retroactively
rewrite them.

This module holds the persistent data models plus the pure, deterministic
helpers for:

- drift/truth-distance representation,
- significance and Legendary Figure eligibility,
- forgetting/rediscovery lifecycle,
- consent-safe projection, and
- NPC historical-knowledge projection.

The compiler, cultural-artifact provider, and World Memory Guardian live in
sibling modules, mirroring the Biography (Phase 14) architecture.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

WORLD_MEMORY_COMPILER_VERSION = "1.0.0"

# Extensible memory forms. New forms may be added without changing the model.
KNOWN_MEMORY_FORMS: frozenset[str] = frozenset(
    {
        "legend",
        "historical_account",
        "folk_tale",
        "rumor",
        "oral_tradition",
        "song_ballad",
        "inscription",
        "memorial",
        "monument_statue",
        "displayed_artwork",
        "archival_document",
        "festival_tradition",
        "place_name_inheritance",
        "relic_legend",
        "lineage_tradition",
        "religious_mythic_interpretation",
        "forgotten_fragment",
    }
)

# Truth distance / drift. ``faithful`` is not a drift; the rest are.
KNOWN_INTERPRETATION_TYPES: frozenset[str] = frozenset(
    {
        "faithful",
        "simplified",
        "selective",
        "symbolic",
        "exaggerated",
        "contradictory",
        "corrupted",
        "fragmented",
        "mythologized",
        "disputed",
        "unknown",
    }
)

# Interpretation types that are, by construction, a deviation from canon.
_DRIFT_TYPES: frozenset[str] = frozenset(
    {
        "selective",
        "symbolic",
        "exaggerated",
        "contradictory",
        "corrupted",
        "fragmented",
        "mythologized",
        "disputed",
        "unknown",
    }
)

KNOWN_DEVIATION_KINDS: frozenset[str] = frozenset(
    {
        "omission",
        "exaggeration",
        "reinterpretation",
        "conflation",
        "contradiction",
        "unknown",
    }
)

KNOWN_MEMORY_STATES: frozenset[str] = frozenset(
    {
        "widely_remembered",
        "locally_remembered",
        "archived_obscure",
        "fragmented",
        "misattributed",
        "suppressed",
        "forgotten",
        "rediscovered",
    }
)

KNOWN_REMEMBRANCE_SCALES: frozenset[str] = frozenset(
    {"personal", "local", "regional", "world_famous", "forgotten"}
)

KNOWN_SUBJECT_TYPES: frozenset[str] = frozenset(
    {"event", "person", "place", "relic", "phenomenon", "group"}
)

KNOWN_LINK_TYPES: frozenset[str] = frozenset(
    {
        "identity",
        "biography",
        "portrait",
        "chronicle_event",
        "story_mark",
        "relationship",
        "relic",
        "location",
        "group_memory",
        "artwork",
        "monument",
        "contradiction",
    }
)


class WorldMemorySourceRef(BaseModel):
    """A machine-readable provenance link to one canonical source record."""

    source_type: str
    source_id: str
    claim_kind: str = "canonical_fact"
    note: str | None = None


class WorldMemoryDeviationSpec(BaseModel):
    """
    A declared, inspectable difference between what canon supports and what the
    cultural memory claims. Every drift must be traceable to a source record and
    must never rewrite that source.
    """

    deviation_kind: str = "reinterpretation"
    canon_supports: str = ""
    legend_claims: str = ""
    entry_note: str = ""


class WorldMemorySpec(BaseModel):
    """
    Structured, consent-filtered specification handed to the cultural-artifact
    provider. It is built only from canonical sources and never invents them.
    """

    subject_entity_type: str
    subject_entity_id: str
    culture: str = ""
    era_context: str = ""
    memory_form: str = "legend"
    interpretation_type: str = "faithful"
    remembrance_scale: str = "local"
    visibility: str = "public_canon"
    perspective: str = "omniscient_narrator"
    allowed_claims: list[str] = Field(default_factory=list)
    source_refs: list[WorldMemorySourceRef] = Field(default_factory=list)
    declared_deviations: list[WorldMemoryDeviationSpec] = Field(default_factory=list)
    significance_rationale: str = ""
    source_snapshot: dict[str, Any] = Field(default_factory=dict)


class GeneratedWorldMemoryArtifact(BaseModel):
    """Provider output. Claims must be backed by canon or a declared deviation."""

    title: str
    narrative: str
    claims: list[str] = Field(default_factory=list)
    perspective: str = "omniscient_narrator"
    source_refs: list[WorldMemorySourceRef] = Field(default_factory=list)
    declared_deviations: list[WorldMemoryDeviationSpec] = Field(default_factory=list)


class WorldMemoryGuardianReport(BaseModel):
    status: str = "pass"  # pass | retry | block
    confidence: float = 0.0
    violations: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    correction_instructions: list[str] = Field(default_factory=list)


class WorldMemoryDeviationModel(BaseModel):
    deviation_id: str
    memory_id: str
    deviation_kind: str
    canon_supports: str
    legend_claims: str
    entry_note: str
    created_at: str | None = None


class WorldMemoryModel(BaseModel):
    memory_id: str
    subject_entity_type: str
    subject_entity_id: str
    culture: str
    era_context: str
    memory_form: str
    interpretation_type: str
    title: str
    narrative: str
    memory_state: str
    remembrance_scale: str
    visibility: str
    perspective: str
    status: str
    guardian_status: str
    guardian_report: WorldMemoryGuardianReport | None = None
    version_number: int
    compiler_version: str
    provider: str
    provider_model: str | None = None
    significance_rationale: str
    source_refs: list[WorldMemorySourceRef] = Field(default_factory=list)
    deviations: list[WorldMemoryDeviationModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class LegendaryFigureLinkModel(BaseModel):
    link_id: str
    figure_id: str
    link_type: str
    link_ref: str
    link_label: str
    is_canonical: bool = True
    created_at: str | None = None


class LegendaryFigureModel(BaseModel):
    figure_id: str
    subject_soul_id: str | None = None
    subject_entity_type: str
    subject_entity_id: str
    figure_title: str
    later_cultural_titles: list[str] = Field(default_factory=list)
    remembrance_scale: str
    memory_state: str
    eligibility_rationale: str
    status: str
    links: list[LegendaryFigureLinkModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class WorldMemoryPlacementModel(BaseModel):
    placement_id: str
    memory_id: str
    placement_type: str
    placement_ref: str
    visibility: str
    created_at: str | None = None


class MemoryStateTransitionModel(BaseModel):
    state_id: str
    memory_id: str
    previous_state: str
    new_state: str
    reason: str
    created_at: str | None = None


class NPCKnowledgeEntryModel(BaseModel):
    memory: WorldMemoryModel
    fidelity: str  # faithful | degraded | distorted | forgotten_hint
    canonical_truth_visible: bool = False
    reason: str


class NPCKnowledgeProjectionModel(BaseModel):
    npc: dict[str, Any]
    subject_entity_type: str
    subject_entity_id: str
    entries: list[NPCKnowledgeEntryModel] = Field(default_factory=list)
    canonical_truth_accessible: bool = False


# Request schemas


class CompileWorldMemoryRequest(BaseModel):
    subject_entity_type: str
    subject_entity_id: str
    culture: str = ""
    era_context: str = ""
    memory_form: str = "legend"
    interpretation_type: str = "faithful"
    remembrance_scale: str = "local"
    visibility: str = "public_canon"
    perspective: str = "omniscient_narrator"
    viewer_soul_id: str | None = None


class PromoteLegendaryFigureRequest(BaseModel):
    subject_entity_type: str = "person"
    subject_entity_id: str
    subject_soul_id: str | None = None
    figure_title: str
    later_cultural_titles: list[str] = Field(default_factory=list)
    remembrance_scale: str = "regional"
    memory_state: str = "widely_remembered"


class PlaceWorldMemoryRequest(BaseModel):
    placement_type: str  # location | relic | gallery_collection
    placement_ref: str
    visibility: str = "public_canon"


class MarkMemoryStateRequest(BaseModel):
    new_state: str
    reason: str = ""


class NPCKnowledgeRequest(BaseModel):
    subject_entity_type: str = "event"
    subject_entity_id: str = ""
    npc_id: str = "npc_default"
    culture: str = ""
    location: str = ""
    era_context: str = ""
    social_role: str = (
        "commoner"  # commoner | archivist | descendant | scholar | priest
    )
    access_to_archives: bool = False
    education_level: str = "low"  # low | moderate | high
    local_tradition: bool = True
    direct_relationship: bool = False
    secrecy_aware: bool = False


# Consent helpers (shared with Biography/Gallery semantics).


def _consent_allows_shared_gallery(soul_id: str) -> bool:
    from app.db import get_or_create_visual_consent_record

    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return bool(consent.get("allow_shared_gallery", True))


def soul_visible_to(soul_id: str, viewer_soul_id: str | None) -> bool:
    if soul_id == viewer_soul_id:
        return True
    return _consent_allows_shared_gallery(soul_id)


def memory_object_owner(memory_object: dict[str, Any]) -> str | None:
    participants = memory_object.get("participants", []) or []
    if not participants:
        return None
    return participants[0].get("soul_id")


def memory_object_visible_to(
    memory_object: dict[str, Any], viewer_soul_id: str | None
) -> bool:
    owner = memory_object_owner(memory_object)
    if owner is None:
        return False
    if owner == viewer_soul_id:
        return True
    if memory_object.get("privacy_consent_scope") != "public_canon":
        return False
    return _consent_allows_shared_gallery(owner)


def world_memory_visible_to(memory: dict[str, Any], viewer_soul_id: str | None) -> bool:
    """A public world memory is visible to all; a private one only to its owner."""
    if memory.get("visibility") == "public_canon":
        return True
    return memory.get("subject_entity_id") == viewer_soul_id


def project_world_memory_for_viewer(
    memory: dict[str, Any], viewer_soul_id: str | None
) -> dict[str, Any]:
    """
    Return a consent-safe copy of a World Memory. Public-canon memories are
    returned unchanged; private memories are returned only to their owner.
    Hidden canonical source links are stripped, never mutated on the stored row.
    """
    projected = dict(memory)
    if not world_memory_visible_to(memory, viewer_soul_id):
        projected["narrative"] = ""
        projected["claims"] = []
        projected["source_refs"] = []
        projected["deviations"] = []
        projected["visibility"] = "private"
        return projected
    return projected


# Truth distance / drift helpers.


def is_drift_interpretation(interpretation_type: str) -> bool:
    return interpretation_type in _DRIFT_TYPES


def interpretation_distance_label(interpretation_type: str) -> str:
    return {
        "faithful": "faithful",
        "simplified": "simplified",
        "selective": "selective",
        "symbolic": "symbolic",
        "exaggerated": "exaggerated",
        "contradictory": "contradictory",
        "corrupted": "corrupted",
        "fragmented": "fragmented",
        "mythologized": "mythologized",
        "disputed": "disputed",
        "unknown": "unknown",
    }.get(interpretation_type, interpretation_type)


# Significance and Legendary Figure eligibility.


def derive_significance(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    memory_objects: list[dict[str, Any]],
    group_significance: str | None = None,
) -> tuple[str, str]:
    """
    Derive a remembrance scale and a human-readable rationale from canonical
    significance signals only. Never uses a popularity counter.
    """
    tiers = [mo.get("importance_tier", "personal") for mo in memory_objects]
    scores = [int(mo.get("importance_score", 5) or 5) for mo in memory_objects]
    max_score = max(scores) if scores else 0

    if (
        group_significance == "legendary"
        or "legendary" in tiers
        or group_significance == "world"
        or "world" in tiers
        or max_score >= 9
    ):
        scale = "world_famous"
    elif group_significance == "community" or "community" in tiers or max_score >= 7:
        scale = "regional"
    elif len(memory_objects) >= 2 or max_score >= 5:
        scale = "local"
    else:
        scale = "personal"

    rationale = (
        f"Derived from {len(memory_objects)} canonical memory object(s) "
        f"(max importance score {max_score}"
        + (f", group significance '{group_significance}'" if group_significance else "")
        + ")."
    )
    return scale, rationale


def evaluate_legendary_eligibility(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    memory_objects: list[dict[str, Any]],
    group_significance: str | None = None,
) -> tuple[bool, str, str]:
    """
    Determine whether a subject is eligible to become a Legendary Figure.
    Eligibility requires canonical significance: world/legendary importance,
    world/legendary group significance, or multiple recurring references.
    """
    scale, rationale = derive_significance(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        memory_objects=memory_objects,
        group_significance=group_significance,
    )
    tiers = {mo.get("importance_tier") for mo in memory_objects}
    recurring = (
        len({mo.get("event_id") for mo in memory_objects if mo.get("event_id")}) >= 2
    )

    eligible = bool(
        group_significance in ("world", "legendary")
        or ("world" in tiers or "legendary" in tiers)
        or recurring
        or scale in ("world_famous", "regional")
    )
    detail = (
        f"Eligibility for '{subject_entity_id}': "
        f"{'eligible' if eligible else 'not eligible'} "
        f"(scale={scale}, recurring_references={recurring}). {rationale}"
    )
    return eligible, scale, detail


# NPC historical-knowledge projection.


def project_npc_knowledge(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    npc: NPCKnowledgeRequest,
    memories: list[dict[str, Any]],
) -> NPCKnowledgeProjectionModel:
    """
    Project what an in-world character could plausibly know. NPCs are scoped by
    culture, location, era, social role, archive access, education, local
    tradition, and direct relationship. An NPC never automatically receives the
    canonical database truth.
    """
    entries: list[NPCKnowledgeEntryModel] = []
    canonical_truth_accessible = npc.access_to_archives and npc.education_level in (
        "moderate",
        "high",
    )

    for memory in memories:
        if not _npc_can_see_memory(memory, npc):
            continue
        fidelity, reason = _npc_fidelity(memory, npc)
        entry_memory = WorldMemoryModel(**dict(memory))
        if fidelity in ("degraded", "distorted", "forgotten_hint"):
            # The NPC does not receive the canonical provenance chain.
            entry_memory = entry_memory.model_copy(
                update={
                    "source_refs": [],
                    "deviations": [],
                    "guardian_report": None,
                }
            )
        entries.append(
            NPCKnowledgeEntryModel(
                memory=entry_memory,
                fidelity=fidelity,
                canonical_truth_visible=fidelity == "faithful"
                and canonical_truth_accessible,
                reason=reason,
            )
        )

    return NPCKnowledgeProjectionModel(
        npc=npc.model_dump(),
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        entries=entries,
        canonical_truth_accessible=canonical_truth_accessible,
    )


def _npc_can_see_memory(memory: dict[str, Any], npc: NPCKnowledgeRequest) -> bool:
    visibility = memory.get("visibility")
    if visibility != "public_canon" and not npc.direct_relationship:
        return False
    if npc.culture and memory.get("culture") and memory.get("culture") != npc.culture:
        return False
    if (
        npc.era_context
        and memory.get("era_context")
        and memory.get("era_context") != npc.era_context
        and not npc.access_to_archives
    ):
        return False
    state = memory.get("memory_state")
    return not (
        state in ("forgotten", "suppressed")
        and not (npc.direct_relationship or npc.secrecy_aware)
    )


def _npc_fidelity(memory: dict[str, Any], npc: NPCKnowledgeRequest) -> tuple[str, str]:
    form = memory.get("memory_form")
    interpretation = memory.get("interpretation_type")
    state = memory.get("memory_state")

    if npc.social_role in ("archivist", "scholar") and npc.access_to_archives:
        if state in ("fragmented", "archived_obscure"):
            return "degraded", "The archivist holds a damaged, partial record."
        return "faithful", "A near-contemporary archive grants faithful access."
    if npc.social_role == "descendant" or npc.direct_relationship:
        return "faithful", "A private family tradition preserves the account."
    if form in ("folk_tale", "oral_tradition", "song_ballad", "rumor", "legend"):
        if interpretation in (
            "mythologized",
            "exaggerated",
            "corrupted",
            "contradictory",
        ):
            return "distorted", "Only the distorted folk version has survived here."
        return "degraded", "The common telling simplifies what happened."
    if state in ("forgotten", "suppressed"):
        return "forgotten_hint", "Only a faint, unverified trace remains."
    if interpretation in ("faithful", "historical_account"):
        if npc.education_level in ("moderate", "high"):
            return "faithful", "Education and access preserve the account."
        return "degraded", "The uneducated hear the gist but not the detail."
    return "degraded", "The telling has drifted from canonical detail."
