# backend/app/living_visual_compiler.py
"""
SoulSmith Phase 21: structured visual scene specifications.

> MEMORY IS CANON. ART IS INTERPRETATION.

A provider never receives only freeform prose. Every visual job is compiled into
a ``VisualSceneSpecModel`` that separates locked canonical facts from artistic
interpretation fields. Unknown facts stay unknown instead of being filled with
accidental specificity. Human/AI creative direction may only populate the
interpretation fields; the canonical fields are derived from structured state.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

VISUAL_SCENE_SPEC_VERSION = "1.0.0"

VisualJobType = Literal[
    "portrait",
    "portrait_continuity",
    "memory_object",
    "chronicle_painting",
    "relic",
    "relationship",
    "group_memory",
    "legendary_figure",
    "world_memory",
    "place",
    "environment",
]

# Visual types that require a locked historical reference for identity
# continuity. The runtime must never silently fall back to text-to-image for
# these when the reference is missing.
CONTINUITY_TYPES: frozenset[str] = frozenset(
    {"portrait_continuity", "memory_object", "group_memory"}
)


class ParticipantSpecModel(BaseModel):
    """A permitted participant with an explicit appearance strategy."""

    soul_id: str
    character_name: str
    role_in_event: str
    portrait_version_id: str | None = None
    reference_image_url: str | None = None
    identity_strategy: str = "historical_portrait"


class SourceEvidenceRefModel(BaseModel):
    """A provenance link backing one canonical fact in the scene spec."""

    source_type: str
    source_id: str
    claim_kind: str = "canonical_fact"
    note: str | None = None


class VisualSceneSpecModel(BaseModel):
    """Inspectable structured spec. Canonical and interpretation stay separate."""

    visual_type: VisualJobType
    spec_version: str = VISUAL_SCENE_SPEC_VERSION

    # Locked canonical facts.
    title: str
    source_entity_type: str | None = None
    source_entity_id: str | None = None
    permitted_participants: list[ParticipantSpecModel] = Field(default_factory=list)
    canonical_objects: list[str] = Field(default_factory=list)
    relic_state: str | None = None
    location: str | None = None
    environment: str | None = None
    time_context: str | None = None
    action_facts: list[str] = Field(default_factory=list)
    outcome_facts: list[str] = Field(default_factory=list)

    # Explicitly prohibited additions.
    prohibited_additions: list[str] = Field(default_factory=list)

    # Unknown/uncertain fields remain unknown rather than being guessed.
    unknown_fields: list[str] = Field(default_factory=list)

    # Interpretation fields (the painter may stylize these, never the facts).
    emotional_tone: str = "Solemn and resonant."
    composition: str = "environmental"
    style_guidance: str = (
        "cinematic painterly realism, grounded fantasy, atmospheric storytelling"
    )
    mood: str = ""
    motif: str = ""
    symbolism: str = ""

    # Provenance backing the locked facts.
    source_evidence: list[SourceEvidenceRefModel] = Field(default_factory=list)


def compile_visual_scene_spec(
    *,
    visual_type: VisualJobType,
    title: str,
    source_entity_type: str | None = None,
    source_entity_id: str | None = None,
    permitted_participants: list[ParticipantSpecModel] | None = None,
    canonical_objects: list[str] | None = None,
    relic_state: str | None = None,
    location: str | None = None,
    environment: str | None = None,
    time_context: str | None = None,
    action_facts: list[str] | None = None,
    outcome_facts: list[str] | None = None,
    prohibited_additions: list[str] | None = None,
    unknown_fields: list[str] | None = None,
    emotional_tone: str = "Solemn and resonant.",
    composition: str = "environmental",
    style_guidance: str = (
        "cinematic painterly realism, grounded fantasy, atmospheric storytelling"
    ),
    mood: str = "",
    motif: str = "",
    symbolism: str = "",
    source_evidence: list[SourceEvidenceRefModel] | None = None,
) -> VisualSceneSpecModel:
    """Compile a deterministic, inspectable scene specification."""
    prohibited = list(prohibited_additions or [])
    if not prohibited:
        prohibited = _default_prohibitions(visual_type)
    return VisualSceneSpecModel(
        visual_type=visual_type,
        title=title,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        permitted_participants=list(permitted_participants or []),
        canonical_objects=list(canonical_objects or []),
        relic_state=relic_state,
        location=location,
        environment=environment,
        time_context=time_context,
        action_facts=list(action_facts or []),
        outcome_facts=list(outcome_facts or []),
        prohibited_additions=prohibited,
        unknown_fields=list(unknown_fields or []),
        emotional_tone=emotional_tone,
        composition=composition,
        style_guidance=style_guidance,
        mood=mood,
        motif=motif,
        symbolism=symbolism,
        source_evidence=list(source_evidence or []),
    )


def _default_prohibitions(visual_type: VisualJobType) -> list[str]:
    base = [
        "no unrecorded participants or bystanders",
        "no invented scars, tattoos, burns, or injuries",
        "no text, captions, labels, logos, HUD, or UI",
    ]
    if visual_type in CONTINUITY_TYPES or visual_type == "portrait_continuity":
        base += [
            "no invented age, hair, facial features, or ethnicity",
            "no invented clothing, armor, or equipment",
        ]
    if visual_type in ("relic", "memory_object", "chronicle_painting"):
        base += ["no invented relics or phenomena", "no invented relic abilities"]
    if visual_type == "place":
        base += [
            "do not claim fictional elements physically exist at this real location"
        ]
    return base


def compile_visual_prompt(spec: VisualSceneSpecModel) -> str:
    """Compile the structured scene spec into sectioned provider instructions."""
    participants = (
        "; ".join(
            f"{p.character_name} ({p.role_in_event}, {p.identity_strategy.replace('_', ' ')})"
            for p in spec.permitted_participants
        )
        or "No participants."
    )
    references = (
        "; ".join(
            f"{p.character_name} -> {p.reference_image_url or p.portrait_version_id}"
            for p in spec.permitted_participants
            if p.reference_image_url or p.portrait_version_id
        )
        or "None recorded."
    )
    objects = "; ".join(spec.canonical_objects) or "None recorded."
    action = "; ".join(spec.action_facts) or "None recorded."
    outcome = "; ".join(spec.outcome_facts) or "None recorded."
    unknown = "; ".join(spec.unknown_fields) or "None."
    evidence = (
        "; ".join(f"{e.source_type}:{e.source_id}" for e in spec.source_evidence)
        or "None recorded."
    )
    sections = [
        ("SCENE", f"{spec.title}. {spec.location or 'Location unknown'}."),
        ("PARTICIPANTS", participants),
        ("HISTORICAL REFERENCES", references),
        ("CANONICAL OBJECTS", objects),
        ("RELIC STATE", spec.relic_state or "No relics involved."),
        ("ACTION", action),
        ("OUTCOME", outcome),
        ("PROHIBITED", "; ".join(spec.prohibited_additions)),
        ("UNKNOWN", unknown),
        ("ATMOSPHERE", spec.emotional_tone),
        ("COMPOSITION", spec.composition),
        ("MOOD/MOTIF", "; ".join(x for x in (spec.mood, spec.motif) if x)),
        ("SYMBOLISM", spec.symbolism or "None."),
        ("VISUAL STYLE", spec.style_guidance),
        ("SOURCE EVIDENCE", evidence),
    ]
    return " ".join(f"[{name}] {body}" for name, body in sections)


def scene_spec_dict(spec: VisualSceneSpecModel) -> dict[str, Any]:
    """Return the inspectable dict form of a scene spec."""
    return spec.model_dump()
