# backend/app/biography.py
"""
SoulSmith Phase 14: Living Biography.

The Biography is derived from the Chronicle. It never rewrites it.

Pipeline:

    CANONICAL CHRONICLE -> BIOGRAPHY COMPILER -> PROVENANCE-AWARE NARRATIVE
    -> PLAYER REVIEW / PRESENTATION

Never:

    GENERATED BIOGRAPHY -> RETROACTIVE CANON

This module holds the persistent Biography data models plus the pure helpers
for consent-safe projection, chronology, recurring-thread extraction, and
fact-vs-perspective classification. The compiler, narrative provider, and
Biography Guardian live in sibling modules.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

BiographyStatus = Literal["draft", "current", "superseded", "rejected", "failed"]
BiographyGuardianStatus = Literal["pending", "passed", "failed"]

ClaimKind = Literal[
    "canonical_fact",
    "participant_perspective",
    "shared_perspective",
    "inferred_theme",
    "narrative_connective",
    "unresolved",
]

SectionType = Literal[
    "origins",
    "formative_moments",
    "bonds",
    "discoveries",
    "trials",
    "relics",
    "story_marks",
    "places",
    "phenomena",
    "shared_memories",
    "consequences",
    "unresolved_threads",
    "current_chapter",
]

SourceType = Literal[
    "memory_object",
    "group_memory",
    "portrait_version",
    "visual_entity_version",
    "chronicle_painting",
    "story_mark",
    "relic",
    "probable_path",
]

ScopeType = Literal["full_life", "relationship", "location", "thread"]

BIOGRAPHY_COMPILER_VERSION = "1.0.0"

# Section types that may never assert new canon even if a source is present.
_CONNECTIVE_SECTION_TYPES: set[str] = {"current_chapter"}


class BiographySourceRef(BaseModel):
    """A machine-readable provenance link to one canonical source record."""

    source_type: SourceType
    source_id: str
    claim_kind: ClaimKind = "canonical_fact"
    note: str | None = None


class BiographySectionSpec(BaseModel):
    """
    Deterministic, inspectable section blueprint produced before prose. The
    narrative provider consumes this; it never invents new canonical sources.
    """

    section_type: SectionType
    title: str
    claim_kind: ClaimKind = "narrative_connective"
    perspective_of: str | None = None
    facts: list[str] = Field(default_factory=list)
    chronology: str | None = None
    threads: list[str] = Field(default_factory=list)
    visual_reference: str | None = None
    source_refs: list[BiographySourceRef] = Field(default_factory=list)


class BiographySpec(BaseModel):
    """Structured, consent-filtered specification handed to the provider."""

    soul_id: str
    title: str
    current_chapter: str
    scope_type: ScopeType = "full_life"
    scope_ref: str | None = None
    visibility: str = "public_canon"
    source_snapshot: dict[str, Any] = Field(default_factory=dict)
    sections: list[BiographySectionSpec] = Field(default_factory=list)


class BiographyNarrativeSection(BaseModel):
    """
    Provider output. ``perspective_of`` marks a passage as one participant's
    recollection so the Guardian can reject it if presented as objective fact.
    """

    section_type: SectionType
    title: str
    narrative: str
    claim_kind: ClaimKind = "narrative_connective"
    perspective_of: str | None = None
    visual_reference: str | None = None
    provenance: list[BiographySourceRef] = Field(default_factory=list)


class BiographySectionModel(BaseModel):
    section_id: str
    biography_id: str
    section_type: SectionType
    position: int
    title: str
    narrative: str
    claim_kind: ClaimKind = "narrative_connective"
    perspective_of: str | None = None
    visual_reference: str | None = None
    provenance: list[BiographySourceRef] = Field(default_factory=list)
    created_at: str | None = None


class BiographyModel(BaseModel):
    biography_id: str
    soul_id: str
    version_number: int
    status: BiographyStatus = "draft"
    title: str
    current_chapter: str | None = None
    scope_type: ScopeType = "full_life"
    scope_ref: str | None = None
    visibility: str = "public_canon"
    source_snapshot: dict[str, Any] = Field(default_factory=dict)
    provider: str = "mock"
    provider_model: str | None = None
    compiler_version: str = BIOGRAPHY_COMPILER_VERSION
    guardian_status: BiographyGuardianStatus = "pending"
    guardian_report: dict[str, Any] | None = None
    sections: list[BiographySectionModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class GuardianReportModel(BaseModel):
    status: Literal["pass", "fail"]
    confidence: float = 0.0
    violations: list[dict[str, Any]] = Field(default_factory=list)
    correction_instructions: list[str] = Field(default_factory=list)


# Request schemas


class CompileBiographyRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    scope_type: ScopeType = "full_life"
    scope_ref: str | None = None
    visibility: str = "public_canon"
    viewer_soul_id: str | None = None


# Pure consent/projection helpers


def _consent_allows_shared_gallery(soul_id: str) -> bool:
    from app.db import get_or_create_visual_consent_record

    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return bool(consent.get("allow_shared_gallery", True))


def soul_visible_to(soul_id: str, viewer_soul_id: str | None) -> bool:
    """A soul is visible to a viewer if it is the viewer or consents to sharing."""
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


def source_visible_to(
    source_type: str, source_id: str, viewer_soul_id: str | None
) -> bool:
    """Resolve whether a provenance source may be shown to a viewer."""
    from app.db import (
        get_chronicle_painting_record,
        get_group_memory_members_records,
        get_memory_object_record,
        get_portrait_version_record,
    )

    if source_type == "memory_object":
        record = get_memory_object_record(source_id)
        return record is not None and memory_object_visible_to(record, viewer_soul_id)
    if source_type == "group_memory":
        for member in get_group_memory_members_records(source_id):
            record = get_memory_object_record(member["memory_object_id"])
            if record and memory_object_visible_to(record, viewer_soul_id):
                return True
        return False
    if source_type == "portrait_version":
        record = get_portrait_version_record(source_id)
        return record is not None and soul_visible_to(record["soul_id"], viewer_soul_id)
    if source_type == "story_mark":
        from app.db import get_story_mark_record

        mark = get_story_mark_record(source_id)
        return mark is not None and soul_visible_to(mark["soul_id"], viewer_soul_id)
    if source_type == "probable_path":
        from app.db import get_probable_path_record

        path = get_probable_path_record(source_id)
        return path is not None and soul_visible_to(path["soul_id"], viewer_soul_id)
    if source_type == "chronicle_painting":
        record = get_chronicle_painting_record(source_id)
        if not record or record.get("status") != "approved":
            return False
        memory = get_memory_object_record(record["memory_object_id"])
        return memory is not None and memory_object_visible_to(memory, viewer_soul_id)
    # World entities and relics are public world canon.
    return True


def project_biography_for_viewer(
    biography: dict[str, Any], viewer_soul_id: str | None
) -> dict[str, Any]:
    """
    Return a consent-safe copy of a biography. Sections whose canonical sources
    are all hidden from the viewer are dropped; hidden provenance links are
    stripped. This never mutates the stored biography.
    """
    projected = dict(biography)
    visible_sections: list[dict[str, Any]] = []
    for section in biography.get("sections", []):
        raw_provenance = section.get("provenance", []) or []
        visible_provenance = [
            ref
            for ref in raw_provenance
            if source_visible_to(ref["source_type"], ref["source_id"], viewer_soul_id)
        ]
        had_sources = bool(raw_provenance)
        # Perspective passages with no visible source cannot be shown.
        if had_sources and not visible_provenance:
            continue
        section_copy = dict(section)
        section_copy["provenance"] = visible_provenance
        if (
            section_copy.get("perspective_of")
            and section_copy["perspective_of"] != viewer_soul_id
            and not soul_visible_to(section_copy["perspective_of"], viewer_soul_id)
        ):
            continue
        visible_sections.append(section_copy)
    projected["sections"] = visible_sections
    return projected


# Chronology helpers (relative ordering only; never invent calendar dates).


def compile_chronology(
    memory_objects: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """
    Assign safe relative-ordering labels. Exact ``created_at`` is used only to
    order; no calendar date, age, or duration is ever produced.
    """
    ordered = sorted(
        memory_objects,
        key=lambda mo: mo.get("created_at") or "",
    )
    labels: dict[str, dict[str, str]] = {}
    total = len(ordered)
    for idx, mo in enumerate(ordered):
        if total <= 1:
            era = "the only remembered moment"
        elif idx == 0:
            era = "earliest remembered moment"
        elif idx == total - 1:
            era = "latest remembered moment"
        else:
            era = "later in the Chronicle"
        relative = (
            "canonical order preserved"
            if mo.get("created_at")
            else "unknown relative date"
        )
        labels[mo["id"]] = {"era": era, "relative": relative}
    return labels


# Recurring-thread extraction (deterministic, traceable).


def extract_recurring_threads(
    memory_objects: list[dict[str, Any]],
    group_tags: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """
    Derive recurring threads from canonical repetition and typed tags only.
    Every thread links back to the source memory object IDs that support it.
    """
    threads: list[dict[str, Any]] = []
    tags = group_tags or {}

    people: dict[str, list[str]] = {}
    places: dict[str, list[str]] = {}
    relics: dict[str, list[str]] = {}
    for mo in memory_objects:
        for participant in mo.get("participants", []) or []:
            soul_id = participant.get("soul_id")
            if soul_id:
                people.setdefault(soul_id, []).append(mo["id"])
        location = mo.get("location_environment")
        if location:
            places.setdefault(location, []).append(mo["id"])
        for relic in mo.get("relics_involved", []) or []:
            relics.setdefault(relic, []).append(mo["id"])

    for soul_id, mem_ids in people.items():
        if len(set(mem_ids)) > 1:
            threads.append(
                {
                    "kind": "recurring_person",
                    "label": soul_id,
                    "source_memory_object_ids": sorted(set(mem_ids)),
                }
            )
    for location, mem_ids in places.items():
        if len(set(mem_ids)) > 1:
            threads.append(
                {
                    "kind": "recurring_place",
                    "label": location,
                    "source_memory_object_ids": sorted(set(mem_ids)),
                }
            )
    for relic, mem_ids in relics.items():
        if len(set(mem_ids)) > 1:
            threads.append(
                {
                    "kind": "recurring_relic",
                    "label": relic,
                    "source_memory_object_ids": sorted(set(mem_ids)),
                }
            )

    for tag_values in tags.values():
        for tag in tag_values:
            if tag.get("tag_type") in ("recurring_motif", "thread"):
                threads.append(
                    {
                        "kind": "typed_tag",
                        "label": tag.get("value"),
                        "tag_type": tag.get("tag_type"),
                        "group_id": tag.get("group_id"),
                        "source_memory_object_ids": [],
                    }
                )
    return threads


def derive_biography_title(memory_objects: list[dict[str, Any]]) -> str:
    if not memory_objects:
        return "A Life Not Yet Remembered"
    titles = [mo.get("event_title") for mo in memory_objects if mo.get("event_title")]
    return titles[0] if titles else "A Life in the Chronicle"


def derive_current_chapter(
    memory_objects: list[dict[str, Any]], chronology: dict[str, dict[str, str]]
) -> str:
    if not memory_objects:
        return "No chapter yet written"
    ordered = sorted(memory_objects, key=lambda mo: mo.get("created_at") or "")
    latest = ordered[-1]
    return latest.get("event_title") or "The present moment"
