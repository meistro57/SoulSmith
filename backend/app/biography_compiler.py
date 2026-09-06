# backend/app/biography_compiler.py
"""
Living Biography compiler service.

Gathers consent-filtered canonical Chronicle records for a soul, organizes them
into a deterministic, inspectable ``BiographySpec`` (chronology, recurring
threads, section structure, approved visual references), hands that spec to the
narrative provider, validates the output with the Biography Guardian, and
persists an immutable version. Regenerating always creates a new version.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.biography import (
    BIOGRAPHY_COMPILER_VERSION,
    BiographySectionSpec,
    BiographySourceRef,
    BiographySpec,
    compile_chronology,
    derive_biography_title,
    derive_current_chapter,
    extract_recurring_threads,
    memory_object_visible_to,
)
from app.biography_guardian import get_biography_guardian
from app.biography_provider import get_biography_provider


class BiographyCompilationError(ValueError):
    """Raised when a biography cannot be compiled from available canon."""


def compile_biography(
    *,
    soul_id: str,
    viewer_soul_id: str | None,
    visibility: str = "public_canon",
    scope_type: str = "full_life",
    scope_ref: str | None = None,
    provider_type: str | None = None,
) -> dict[str, Any]:
    """
    Compile and persist a new biography version. Returns the stored biography
    dict plus the Guardian report. A failed Guardian review produces a ``failed``
    version and never becomes current.
    """
    memory_objects = _gather_memory_objects(
        soul_id=soul_id,
        viewer_soul_id=viewer_soul_id,
        scope_type=scope_type,
        scope_ref=scope_ref,
    )
    if not memory_objects:
        raise BiographyCompilationError(
            f"No canonical Chronicle records found for soul '{soul_id}'."
        )

    spec = build_biography_spec(
        soul_id=soul_id,
        memory_objects=memory_objects,
        viewer_soul_id=viewer_soul_id,
        visibility=visibility,
        scope_type=scope_type,
        scope_ref=scope_ref,
    )

    provider = get_biography_provider(provider_type)
    narrative_sections = provider.generate(spec)

    guardian = get_biography_guardian()
    report = guardian.validate(sections=narrative_sections, spec=spec)

    guardian_status = "passed" if report.status == "pass" else "failed"
    status = "draft" if report.status == "pass" else "failed"

    from app.db import create_biography_version_transaction

    biography = create_biography_version_transaction(
        soul_id=soul_id,
        status=status,
        title=spec.title,
        current_chapter=spec.current_chapter,
        scope_type=scope_type,
        scope_ref=scope_ref,
        visibility=visibility,
        source_snapshot=spec.source_snapshot,
        provider=provider.PROVIDER,
        provider_model=provider.PROVIDER_MODEL,
        compiler_version=BIOGRAPHY_COMPILER_VERSION,
        guardian_status=guardian_status,
        guardian_report=report.model_dump(),
        sections=[
            {
                "section_type": s.section_type,
                "title": s.title,
                "narrative": s.narrative,
                "claim_kind": s.claim_kind,
                "perspective_of": s.perspective_of,
                "visual_reference": s.visual_reference,
                "provenance": [ref.model_dump() for ref in s.provenance],
            }
            for s in narrative_sections
        ],
    )

    return {"biography": biography, "guardian_report": report.model_dump()}


def build_biography_spec(
    *,
    soul_id: str,
    memory_objects: list[dict[str, Any]],
    viewer_soul_id: str | None,
    visibility: str = "public_canon",
    scope_type: str = "full_life",
    scope_ref: str | None = None,
) -> BiographySpec:
    """Deterministically assemble the structured specification before prose."""
    chronology = compile_chronology(memory_objects)
    title = derive_biography_title(memory_objects)
    current_chapter = derive_current_chapter(memory_objects, chronology)

    group_tags = _gather_group_tags(soul_id)
    threads = extract_recurring_threads(memory_objects, group_tags)

    sections = _build_sections(
        soul_id=soul_id,
        memory_objects=memory_objects,
        chronology=chronology,
        threads=threads,
        viewer_soul_id=viewer_soul_id,
    )

    ordered = sorted(memory_objects, key=lambda mo: mo.get("created_at") or "")
    source_snapshot = {
        "memory_object_count": len(memory_objects),
        "event_ids": sorted(
            {mo.get("event_id") for mo in memory_objects if mo.get("event_id")}
        ),
        "earliest_event_created_at": ordered[0].get("created_at"),
        "latest_event_created_at": ordered[-1].get("created_at"),
        "scope_type": scope_type,
        "scope_ref": scope_ref,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }

    return BiographySpec(
        soul_id=soul_id,
        title=title,
        current_chapter=current_chapter,
        scope_type=scope_type,  # type: ignore[arg-type]
        scope_ref=scope_ref,
        visibility=visibility,
        source_snapshot=source_snapshot,
        sections=sections,
    )


# Gathering


def _gather_memory_objects(
    *,
    soul_id: str,
    viewer_soul_id: str | None,
    scope_type: str,
    scope_ref: str | None,
) -> list[dict[str, Any]]:
    from app.db import get_memory_objects_records

    candidates = []
    for mo in get_memory_objects_records():
        if not _subject_participates(soul_id, mo):
            continue
        if not memory_object_visible_to(mo, viewer_soul_id):
            continue
        if not _in_scope(mo, scope_type, scope_ref):
            continue
        candidates.append(mo)
    return sorted(candidates, key=lambda mo: mo.get("created_at") or "")


def _subject_participates(soul_id: str, memory_object: dict[str, Any]) -> bool:
    participants = memory_object.get("participants", []) or []
    return any(p.get("soul_id") == soul_id for p in participants)


def _in_scope(
    memory_object: dict[str, Any], scope_type: str, scope_ref: str | None
) -> bool:
    if scope_type == "full_life" or not scope_ref:
        return True
    if scope_type == "location":
        return memory_object.get("location_environment") == scope_ref
    if scope_type == "relationship":
        participants = memory_object.get("participants", []) or []
        return any(p.get("soul_id") == scope_ref for p in participants)
    if scope_type == "thread":
        # Thread scoping is resolved through typed tags in _build_sections; at
        # the memory-object layer we keep everything and let tags narrow it.
        return True
    return True


def _gather_group_tags(soul_id: str) -> dict[str, list[dict[str, Any]]]:
    from app.db import (
        get_group_memory_members_records,
        get_group_memory_tags_records,
        list_group_memory_records,
    )

    result: dict[str, list[dict[str, Any]]] = {}
    for group in list_group_memory_records():
        members = get_group_memory_members_records(group["group_id"])
        if not any(m["soul_id"] == soul_id for m in members):
            continue
        tags = get_group_memory_tags_records(group["group_id"])
        result[group["group_id"]] = tags
    return result


# Section building


def _build_sections(
    *,
    soul_id: str,
    memory_objects: list[dict[str, Any]],
    chronology: dict[str, dict[str, str]],
    threads: list[dict[str, Any]],
    viewer_soul_id: str | None,
) -> list[BiographySectionSpec]:
    sections: list[BiographySectionSpec] = []
    ordered = sorted(memory_objects, key=lambda mo: mo.get("created_at") or "")

    # Origins
    if ordered:
        sections.append(
            _single_memory_section(
                section_type="origins",
                title="Origins and Earliest Remembered Self",
                memory_object=ordered[0],
                chronology=chronology,
            )
        )

    # Formative moments (high significance)
    formative = [mo for mo in ordered if int(mo.get("importance_score", 0) or 0) >= 7]
    if formative:
        sections.append(
            _multi_memory_section(
                section_type="formative_moments",
                title="Formative Moments",
                memory_objects=formative,
                chronology=chronology,
            )
        )

    # Bonds and relationships (recurring people)
    for thread in threads:
        if thread.get("kind") == "recurring_person":
            mem_ids = thread["source_memory_object_ids"]
            related = [mo for mo in ordered if mo["id"] in mem_ids]
            if related:
                sections.append(
                    _perspective_section(
                        section_type="bonds",
                        title=f"A Recurring Bond: {thread['label']}",
                        memory_objects=related,
                        perspective_of=thread["label"],
                        chronology=chronology,
                    )
                )

    # Discoveries (relic-involving memories)
    discoveries = [mo for mo in ordered if mo.get("relics_involved")]
    if discoveries:
        sections.append(
            _multi_memory_section(
                section_type="discoveries",
                title="Discoveries",
                memory_objects=discoveries,
                chronology=chronology,
            )
        )

    # Relics and meaningful objects
    relic_memories = [mo for mo in ordered if mo.get("relics_involved")]
    if relic_memories:
        sections.append(
            _multi_memory_section(
                section_type="relics",
                title="Relics and Meaningful Objects",
                memory_objects=relic_memories,
                chronology=chronology,
            )
        )

    # StoryMarks and lasting changes
    story_marks = _gather_story_marks(soul_id, viewer_soul_id)
    if story_marks:
        sections.append(_story_mark_section(soul_id=soul_id, story_marks=story_marks))

    # Places that shaped the soul (recurring places)
    for thread in threads:
        if thread.get("kind") == "recurring_place":
            mem_ids = thread["source_memory_object_ids"]
            related = [mo for mo in ordered if mo["id"] in mem_ids]
            if related:
                sections.append(
                    _multi_memory_section(
                        section_type="places",
                        title=f"A Place That Shaped the Soul: {thread['label']}",
                        memory_objects=related,
                        chronology=chronology,
                    )
                )

    # Shared memories (group perspectives)
    shared = _build_shared_memory_sections(soul_id, viewer_soul_id)
    sections.extend(shared)

    # Recurring motifs / typed tags (inferred themes, never canonical facts)
    for thread in threads:
        if thread.get("kind") == "typed_tag":
            sections.append(_thread_section(soul_id=soul_id, thread=thread))

    # Consequences
    consequences = [mo for mo in ordered if mo.get("lasting_consequence")]
    if consequences:
        sections.append(
            _multi_memory_section(
                section_type="consequences",
                title="Consequences",
                memory_objects=consequences,
                chronology=chronology,
            )
        )

    # Unresolved threads
    unresolved = _build_unresolved_section(soul_id, viewer_soul_id)
    if unresolved:
        sections.append(unresolved)

    # Current chapter
    if ordered:
        sections.append(
            _single_memory_section(
                section_type="current_chapter",
                title="Current Chapter",
                memory_object=ordered[-1],
                chronology=chronology,
                claim_kind="narrative_connective",
            )
        )

    # Deduplicate by (section_type, title) while preserving order.
    seen: set[tuple[str, str]] = set()
    unique: list[BiographySectionSpec] = []
    for section in sections:
        key = (section.section_type, section.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(section)
    return unique


def _single_memory_section(
    *,
    section_type: str,
    title: str,
    memory_object: dict[str, Any],
    chronology: dict[str, dict[str, str]],
    claim_kind: str = "canonical_fact",
) -> BiographySectionSpec:
    facts = _facts_for_memory(memory_object)
    refs = _refs_for_memory(memory_object)
    return BiographySectionSpec(
        section_type=section_type,  # type: ignore[arg-type]
        title=title,
        claim_kind=claim_kind,  # type: ignore[arg-type]
        facts=facts,
        chronology=chronology.get(memory_object["id"], {}).get("era"),
        visual_reference=_approved_painting_for(memory_object),
        source_refs=refs,
    )


def _multi_memory_section(
    *,
    section_type: str,
    title: str,
    memory_objects: list[dict[str, Any]],
    chronology: dict[str, dict[str, str]],
    claim_kind: str = "canonical_fact",
) -> BiographySectionSpec:
    facts: list[str] = []
    refs: list[BiographySourceRef] = []
    for mo in memory_objects:
        facts.extend(_facts_for_memory(mo))
        refs.extend(_refs_for_memory(mo))
    return BiographySectionSpec(
        section_type=section_type,  # type: ignore[arg-type]
        title=title,
        claim_kind=claim_kind,  # type: ignore[arg-type]
        facts=_dedupe(facts),
        chronology=chronology.get(memory_objects[0]["id"], {}).get("era")
        if memory_objects
        else None,
        visual_reference=_approved_painting_for(memory_objects[0])
        if memory_objects
        else None,
        source_refs=_dedupe_refs(refs),
    )


def _perspective_section(
    *,
    section_type: str,
    title: str,
    memory_objects: list[dict[str, Any]],
    perspective_of: str,
    chronology: dict[str, dict[str, str]],
) -> BiographySectionSpec:
    section = _multi_memory_section(
        section_type=section_type,
        title=title,
        memory_objects=memory_objects,
        chronology=chronology,
        claim_kind="participant_perspective",
    )
    section.perspective_of = perspective_of
    return section


def _story_mark_section(
    *, soul_id: str, story_marks: list[dict[str, Any]]
) -> BiographySectionSpec:
    facts = [
        f"{m.get('mark_type')} at {m.get('location')} (acquired {m.get('acquired_at')})"
        for m in story_marks
    ]
    refs = [
        BiographySourceRef(
            source_type="story_mark",
            source_id=m["id"],
            claim_kind="canonical_fact",
            note=f"StoryMark {m.get('mark_type')}",
        )
        for m in story_marks
    ]
    return BiographySectionSpec(
        section_type="story_marks",
        title="StoryMarks and Lasting Changes",
        claim_kind="canonical_fact",
        facts=facts,
        source_refs=refs,
    )


def _build_shared_memory_sections(
    soul_id: str, viewer_soul_id: str | None
) -> list[BiographySectionSpec]:
    from app.db import (
        get_group_memory_members_records,
        get_memory_object_record,
        list_group_memory_records,
    )

    sections: list[BiographySectionSpec] = []
    for group in list_group_memory_records():
        members = get_group_memory_members_records(group["group_id"])
        subject_members = [m for m in members if m["soul_id"] == soul_id]
        if not subject_members:
            continue
        other_members = [m for m in members if m["soul_id"] != soul_id]
        facts: list[str] = []
        refs: list[BiographySourceRef] = [
            BiographySourceRef(
                source_type="group_memory",
                source_id=group["group_id"],
                claim_kind="shared_perspective",
            )
        ]
        for member in other_members:
            record = get_memory_object_record(member["memory_object_id"])
            if not record:
                continue
            if not memory_object_visible_to(record, viewer_soul_id):
                continue
            facts.append(
                f"{member['soul_id']} remembers this as: {record.get('emotional_tone') or 'an unstated feeling'}"
            )
            refs.append(
                BiographySourceRef(
                    source_type="memory_object",
                    source_id=record["id"],
                    claim_kind="participant_perspective",
                )
            )
        if facts:
            sections.append(
                BiographySectionSpec(
                    section_type="shared_memories",
                    title=group.get("title") or "A Shared Event",
                    claim_kind="shared_perspective",
                    facts=facts,
                    source_refs=_dedupe_refs(refs),
                )
            )
    return sections


def _thread_section(*, soul_id: str, thread: dict[str, Any]) -> BiographySectionSpec:
    """Build an inferred-theme section from a typed tag/thread, with traceable sources."""
    from app.db import get_group_memory_members_records

    refs: list[BiographySourceRef] = []
    group_id = thread.get("group_id")
    if group_id:
        refs.append(
            BiographySourceRef(
                source_type="group_memory",
                source_id=group_id,
                claim_kind="inferred_theme",
            )
        )
        for member in get_group_memory_members_records(group_id):
            if member["soul_id"] == soul_id and member.get("memory_object_id"):
                refs.append(
                    BiographySourceRef(
                        source_type="memory_object",
                        source_id=member["memory_object_id"],
                        claim_kind="canonical_fact",
                    )
                )
    return BiographySectionSpec(
        section_type="phenomena",
        title=f"Recurring Motif: {thread.get('label')}",
        claim_kind="inferred_theme",
        facts=[f"the motif '{thread.get('label')}' recurs across the Chronicle"],
        source_refs=_dedupe_refs(refs),
    )


def _build_unresolved_section(
    soul_id: str, viewer_soul_id: str | None
) -> BiographySectionSpec | None:
    from app.db import get_all_open_questions, get_probable_paths_records

    facts: list[str] = []
    refs: list[BiographySourceRef] = []
    for question in get_all_open_questions():
        if question.get("status") == "open":
            facts.append(question.get("question_text"))
    for path in get_probable_paths_records(soul_id):
        if path.get("status") == "dormant" and path.get("soul_id") == soul_id:
            facts.append(path.get("path_title"))
            refs.append(
                BiographySourceRef(
                    source_type="probable_path",
                    source_id=path["id"],
                    claim_kind="unresolved",
                )
            )
    if not facts:
        return None
    return BiographySectionSpec(
        section_type="unresolved_threads",
        title="Unresolved Threads",
        claim_kind="unresolved",
        facts=_dedupe(facts),
        source_refs=refs,
    )


# Source/fact helpers


def _facts_for_memory(memory_object: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    if memory_object.get("event_title"):
        facts.append(memory_object["event_title"])
    if memory_object.get("location_environment"):
        facts.append(f"at {memory_object['location_environment']}")
    if memory_object.get("action_composition"):
        facts.append(memory_object["action_composition"])
    for relic in memory_object.get("relics_involved", []) or []:
        facts.append(f"involving {relic}")
    if memory_object.get("lasting_consequence"):
        facts.append(f"consequence: {memory_object['lasting_consequence']}")
    return facts


def _refs_for_memory(memory_object: dict[str, Any]) -> list[BiographySourceRef]:
    refs = [
        BiographySourceRef(
            source_type="memory_object",
            source_id=memory_object["id"],
            claim_kind="canonical_fact",
        )
    ]
    for participant in memory_object.get("participants", []) or []:
        portrait_version_id = participant.get("portrait_version_id")
        if portrait_version_id:
            refs.append(
                BiographySourceRef(
                    source_type="portrait_version",
                    source_id=portrait_version_id,
                    claim_kind="canonical_fact",
                    note=f"Historical portrait for {participant.get('soul_id')}",
                )
            )
    return refs


def _approved_painting_for(memory_object: dict[str, Any]) -> str | None:
    from app.db import get_chronicle_paintings_records

    for painting in get_chronicle_paintings_records(memory_object["id"]):
        if painting.get("status") == "approved" and painting.get("image_url"):
            return painting["image_url"]
    return None


def _gather_story_marks(
    soul_id: str, viewer_soul_id: str | None
) -> list[dict[str, Any]]:
    from app.biography import soul_visible_to
    from app.db import get_story_marks_records

    marks = get_story_marks_records(soul_id)
    return [m for m in marks if soul_visible_to(m["soul_id"], viewer_soul_id)]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _dedupe_refs(refs: list[BiographySourceRef]) -> list[BiographySourceRef]:
    seen: set[tuple[str, str]] = set()
    result: list[BiographySourceRef] = []
    for ref in refs:
        key = (ref.source_type, ref.source_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(ref)
    return result
