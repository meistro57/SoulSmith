# backend/app/world_memory_compiler.py
"""
World Memory compiler service.

Gathers consent-filtered canonical sources for a subject, organizes them into a
deterministic ``WorldMemorySpec`` (allowed claims, source links, declared
deviations, significance), hands that spec to the cultural-artifact provider,
validates the output with the World Memory Guardian, and persists an immutable
World Memory version. Regenerating always creates a new version; it never
mutates the underlying Chronicle, Memory Object, Group Memory, Biography, relic,
or approved visual history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.world_memory import (
    KNOWN_INTERPRETATION_TYPES,
    KNOWN_MEMORY_FORMS,
    KNOWN_REMEMBRANCE_SCALES,
    KNOWN_SUBJECT_TYPES,
    WORLD_MEMORY_COMPILER_VERSION,
    WorldMemoryDeviationSpec,
    WorldMemorySourceRef,
    WorldMemorySpec,
    derive_significance,
    is_drift_interpretation,
    memory_object_visible_to,
)
from app.world_memory_guardian import get_world_memory_guardian
from app.world_memory_provider import get_world_memory_provider


class WorldMemoryCompilationError(ValueError):
    """Raised when a World Memory cannot be compiled from available canon."""


def compile_world_memory(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    culture: str = "",
    era_context: str = "",
    memory_form: str = "legend",
    interpretation_type: str = "faithful",
    remembrance_scale: str = "local",
    visibility: str = "public_canon",
    perspective: str = "omniscient_narrator",
    viewer_soul_id: str | None = None,
    provider_type: str | None = None,
) -> dict[str, Any]:
    """
    Compile and persist a new World Memory version. Returns the stored memory
    dict plus the Guardian report. A blocked Guardian review produces a
    ``failed`` version and never becomes current.
    """
    _validate_request(
        subject_entity_type=subject_entity_type,
        memory_form=memory_form,
        interpretation_type=interpretation_type,
        remembrance_scale=remembrance_scale,
        visibility=visibility,
    )

    gathered = gather_world_memory_sources(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        viewer_soul_id=viewer_soul_id,
    )
    if not gathered["allowed_claims"]:
        raise WorldMemoryCompilationError(
            f"No canonical sources found for {subject_entity_type} "
            f"'{subject_entity_id}'."
        )

    declared_deviations = _build_declared_deviations(
        interpretation_type=interpretation_type,
        memory_form=memory_form,
        allowed_claims=gathered["allowed_claims"],
    )

    significance_rationale = derive_significance(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        memory_objects=gathered["memory_objects"],
        group_significance=gathered["group_significance"],
    )[1]

    spec = WorldMemorySpec(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        culture=culture,
        era_context=era_context,
        memory_form=memory_form,
        interpretation_type=interpretation_type,
        remembrance_scale=remembrance_scale,
        visibility=visibility,
        perspective=perspective,
        allowed_claims=gathered["allowed_claims"],
        source_refs=gathered["source_refs"],
        declared_deviations=declared_deviations,
        significance_rationale=significance_rationale,
        source_snapshot={
            "source_count": len(gathered["source_refs"]),
            "memory_object_count": len(gathered["memory_objects"]),
            "group_significance": gathered["group_significance"],
            "compiled_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    provider = get_world_memory_provider(provider_type)
    artifact = provider.generate(spec)

    guardian = get_world_memory_guardian()
    report = guardian.validate(artifact=artifact, spec=spec)

    guardian_status = "passed" if report.status == "pass" else "blocked"
    status = "draft" if report.status == "pass" else "failed"

    from app.db import create_world_memory_transaction

    memory = create_world_memory_transaction(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        culture=culture,
        era_context=era_context,
        memory_form=memory_form,
        interpretation_type=interpretation_type,
        title=artifact.title,
        narrative=artifact.narrative,
        memory_state="widely_remembered",
        remembrance_scale=remembrance_scale,
        visibility=visibility,
        perspective=perspective,
        status=status,
        guardian_status=guardian_status,
        guardian_report=report.model_dump(),
        compiler_version=WORLD_MEMORY_COMPILER_VERSION,
        provider=provider.PROVIDER,
        provider_model=provider.PROVIDER_MODEL,
        significance_rationale=significance_rationale,
        source_refs=[ref.model_dump() for ref in artifact.source_refs],
        deviations=[d.model_dump() for d in artifact.declared_deviations],
    )

    return {"memory": memory, "guardian_report": report.model_dump()}


def _validate_request(
    *,
    subject_entity_type: str,
    memory_form: str,
    interpretation_type: str,
    remembrance_scale: str,
    visibility: str,
) -> None:
    if subject_entity_type not in KNOWN_SUBJECT_TYPES:
        raise WorldMemoryCompilationError(
            f"Unknown subject_entity_type '{subject_entity_type}'."
        )
    if memory_form not in KNOWN_MEMORY_FORMS:
        raise WorldMemoryCompilationError(f"Unknown memory_form '{memory_form}'.")
    if interpretation_type not in KNOWN_INTERPRETATION_TYPES:
        raise WorldMemoryCompilationError(
            f"Unknown interpretation_type '{interpretation_type}'."
        )
    if remembrance_scale not in KNOWN_REMEMBRANCE_SCALES:
        raise WorldMemoryCompilationError(
            f"Unknown remembrance_scale '{remembrance_scale}'."
        )
    if visibility not in ("public_canon", "private"):
        raise WorldMemoryCompilationError(f"Unknown visibility '{visibility}'.")


def _build_declared_deviations(
    *,
    interpretation_type: str,
    memory_form: str,
    allowed_claims: list[str],
) -> list[WorldMemoryDeviationSpec]:
    if not is_drift_interpretation(interpretation_type):
        return []
    kind = {
        "selective": "omission",
        "symbolic": "reinterpretation",
        "exaggerated": "exaggeration",
        "contradictory": "contradiction",
        "corrupted": "reinterpretation",
        "fragmented": "omission",
        "mythologized": "reinterpretation",
        "disputed": "contradiction",
        "unknown": "unknown",
    }.get(interpretation_type, "reinterpretation")
    canon = "Canon records: " + "; ".join(allowed_claims) if allowed_claims else ""
    legend = (
        f"The {memory_form} retells these events as {interpretation_type} "
        f"rather than a faithful account."
    )
    return [
        WorldMemoryDeviationSpec(
            deviation_kind=kind,
            canon_supports=canon,
            legend_claims=legend,
            entry_note=f"Auto-declared drift for {interpretation_type} interpretation.",
        )
    ]


# Gathering


def gather_world_memory_sources(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    viewer_soul_id: str | None,
) -> dict[str, Any]:
    """
    Gather consent-filtered canonical sources for a subject. Returns memory
    objects, group significance, allowed claims, and source refs.
    """
    memory_objects = _memory_objects_for_subject(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        viewer_soul_id=viewer_soul_id,
    )
    group_significance = _group_significance_for_subject(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
    )

    allowed_claims: list[str] = []
    source_refs: list[WorldMemorySourceRef] = []

    for mo in memory_objects:
        source_refs.append(
            WorldMemorySourceRef(
                source_type="memory_object",
                source_id=mo["id"],
                claim_kind="canonical_fact",
            )
        )
        if mo.get("event_title"):
            allowed_claims.append(mo["event_title"])
        if mo.get("location_environment"):
            allowed_claims.append(f"At {mo['location_environment']}")
        if mo.get("action_composition"):
            allowed_claims.append(mo["action_composition"])
        if mo.get("lasting_consequence"):
            allowed_claims.append(mo["lasting_consequence"])

    _append_biography_sources(subject_entity_type, subject_entity_id, source_refs)
    _append_relic_sources(
        subject_entity_type, subject_entity_id, allowed_claims, source_refs
    )
    _append_painting_sources(memory_objects, viewer_soul_id, source_refs)
    _append_identity_sources(subject_entity_type, subject_entity_id, source_refs)

    return {
        "memory_objects": memory_objects,
        "group_significance": group_significance,
        "allowed_claims": _dedupe(allowed_claims),
        "source_refs": source_refs,
    }


def _memory_objects_for_subject(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    viewer_soul_id: str | None,
) -> list[dict[str, Any]]:
    from app.db import get_memory_objects_records

    matches: list[dict[str, Any]] = []
    for mo in get_memory_objects_records():
        if not _memory_object_matches_subject(
            mo, subject_entity_type, subject_entity_id
        ):
            continue
        if not memory_object_visible_to(mo, viewer_soul_id):
            continue
        matches.append(mo)
    return sorted(matches, key=lambda mo: mo.get("created_at") or "")


def _memory_object_matches_subject(
    mo: dict[str, Any], subject_entity_type: str, subject_entity_id: str
) -> bool:
    if subject_entity_type == "event":
        return mo.get("event_id") == subject_entity_id
    if subject_entity_type == "person":
        participants = mo.get("participants", []) or []
        return any(p.get("soul_id") == subject_entity_id for p in participants)
    if subject_entity_type == "place":
        return mo.get("location_environment") == subject_entity_id
    if subject_entity_type == "relic":
        relics = mo.get("relics_involved", []) or []
        return subject_entity_id in relics
    if subject_entity_type == "phenomenon":
        return (
            mo.get("event_title") == subject_entity_id
            or mo.get("location_environment") == subject_entity_id
        )
    if subject_entity_type == "group":
        return mo.get("event_id") == subject_entity_id
    return False


def _group_significance_for_subject(
    subject_entity_type: str, subject_entity_id: str
) -> str | None:
    from app.db import (
        get_group_memory_by_event_record,
        get_group_memory_members_records,
        list_group_memory_records,
    )

    if subject_entity_type == "event":
        group = get_group_memory_by_event_record(subject_entity_id)
        return group.get("group_significance") if group else None
    if subject_entity_type == "person":
        for group in list_group_memory_records():
            for member in get_group_memory_members_records(group["group_id"]):
                if member.get("soul_id") == subject_entity_id:
                    return group.get("group_significance")
    return None


def _append_biography_sources(
    subject_entity_type: str,
    subject_entity_id: str,
    source_refs: list[WorldMemorySourceRef],
) -> None:
    if subject_entity_type != "person":
        return
    from app.db import get_current_biography_record

    biography = get_current_biography_record(subject_entity_id)
    if biography:
        source_refs.append(
            WorldMemorySourceRef(
                source_type="biography",
                source_id=biography["biography_id"],
                claim_kind="canonical_fact",
            )
        )


def _append_relic_sources(
    subject_entity_type: str,
    subject_entity_id: str,
    allowed_claims: list[str],
    source_refs: list[WorldMemorySourceRef],
) -> None:
    if subject_entity_type != "relic":
        return
    from app.db import get_relic_history_records

    for event in get_relic_history_records(subject_entity_id):
        source_refs.append(
            WorldMemorySourceRef(
                source_type="relic_event",
                source_id=event["id"],
                claim_kind="canonical_fact",
            )
        )
        if event.get("chronicle_evidence_summary"):
            allowed_claims.append(event["chronicle_evidence_summary"])


def _append_painting_sources(
    memory_objects: list[dict[str, Any]],
    viewer_soul_id: str | None,
    source_refs: list[WorldMemorySourceRef],
) -> None:
    from app.db import get_approved_chronicle_paintings_records

    approved_ids = {
        p["memory_object_id"] for p in get_approved_chronicle_paintings_records()
    }
    for mo in memory_objects:
        if mo["id"] in approved_ids:
            source_refs.append(
                WorldMemorySourceRef(
                    source_type="chronicle_painting",
                    source_id=mo["id"],
                    claim_kind="canonical_fact",
                )
            )


def _append_identity_sources(
    subject_entity_type: str,
    subject_entity_id: str,
    source_refs: list[WorldMemorySourceRef],
) -> None:
    if subject_entity_type != "person":
        return
    from app.db import get_portrait_versions_records, get_story_marks_records

    for portrait in get_portrait_versions_records(subject_entity_id):
        source_refs.append(
            WorldMemorySourceRef(
                source_type="portrait_version",
                source_id=portrait["version_id"],
                claim_kind="canonical_fact",
            )
        )
    for mark in get_story_marks_records(subject_entity_id):
        source_refs.append(
            WorldMemorySourceRef(
                source_type="story_mark",
                source_id=mark["id"],
                claim_kind="canonical_fact",
            )
        )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
