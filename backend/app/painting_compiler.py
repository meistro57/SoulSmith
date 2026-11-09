# backend/app/painting_compiler.py
"""
Dedicated Chronicle Painting compiler.

Separates canonical extraction (a structured, inspectable ``SceneSpec``) from
artistic phrasing (a provider-specific prompt with explicit conceptual sections).
This compiler never mutates the Memory Object and never invents identity-specific
details when canonical appearance is unavailable.
"""

from __future__ import annotations

from app.chronicle_paintings import (
    ParticipantAppearanceModel,
    SceneSpecModel,
)
from app.composition_selector import composition_guidance, select_composition
from app.visual_memory import MemoryObjectModel


def _format_story_marks(
    participants: list[ParticipantAppearanceModel],
) -> list[str]:
    """Collect distinct, provenance-backed story marks across participants."""
    marks: list[str] = []
    seen: set[str] = set()
    for p in participants:
        for m in p.story_marks:
            key = f"{p.character_name}:{m.mark_type}:{m.location}"
            if key in seen:
                continue
            seen.add(key)
            marks.append(
                f"{m.mark_type.replace('_', ' ')} on {m.location.replace('_', ' ')} "
                f"({p.character_name})"
            )
    return marks


def _format_equipment(
    participants: list[ParticipantAppearanceModel],
) -> list[str]:
    """Collect distinct canonical equipment facts across participants."""
    items: list[str] = []
    seen: set[str] = set()
    for p in participants:
        equip = p.equipment
        if not equip:
            continue
        for field in ("armor", "clothing", "backpacks_cloaks"):
            value = getattr(equip, field, None)
            if value:
                key = f"{p.character_name}:{field}:{value}"
                if key not in seen:
                    seen.add(key)
                    items.append(f"{p.character_name}: {value}")
        for weapon in equip.weapons:
            key = f"{p.character_name}:weapon:{weapon}"
            if key not in seen:
                seen.add(key)
                items.append(f"{p.character_name}: wields {weapon}")
        for relic in equip.relics:
            key = f"{p.character_name}:relic:{relic}"
            if key not in seen:
                seen.add(key)
                items.append(f"{p.character_name}: bears {relic}")
    return items


def compile_chronicle_painting_scene(
    *,
    memory_object: MemoryObjectModel,
    participants: list[ParticipantAppearanceModel],
    composition: str | None = None,
    style: str | None = None,
    correction_instructions: list[str] | None = None,
) -> SceneSpecModel:
    """
    Compile a canonical Memory Object into a structured scene specification.

    ``correction_instructions`` (from a prior Visual Canon Guardian RETRY) are
    folded into the ``must_preserve`` constraints so regeneration applies only
    the correction, never new canonical facts.
    """
    participant_count = len(participants)
    has_phenomena = bool(memory_object.relics_involved) and _looks_like_phenomena(
        memory_object
    )
    has_relic = bool(memory_object.relics_involved) and not has_phenomena

    chosen_composition = composition or select_composition(
        participant_count=participant_count,
        importance_tier=memory_object.importance_tier,
        importance_score=memory_object.importance_score,
        has_phenomena=has_phenomena,
        has_relic=has_relic,
        event_type=memory_object.event_title,
        emotional_tone=memory_object.emotional_tone,
    )

    story_marks = _format_story_marks(participants)
    equipment = _format_equipment(participants)
    phenomena = [
        r for r in memory_object.relics_involved if r.lower() in _PHENOMENA_NAMES
    ]
    relic_state = (
        "; ".join(memory_object.relics_involved)
        if memory_object.relics_involved
        else "No relics involved."
    )

    must_preserve = [
        f"Depict exactly {participant_count} participant(s) as recorded",
        "Preserve historical appearance from locked portrait version(s)",
        f"Location: {memory_object.location_environment}",
        f"Event: {memory_object.event_title} ({memory_object.event_id})",
        f"Tone: {memory_object.emotional_tone}",
    ]
    if memory_object.relics_involved:
        must_preserve.append(f"Relics/equipment state: {relic_state}")
    if correction_instructions:
        must_preserve.extend(
            f"Correction (Guardian): {instr}" for instr in correction_instructions
        )

    must_not_invent = [
        "no unrecorded participants or bystanders",
        "no duplicated participants",
        "no invented scars, tattoos, burns, or injuries",
        "no invented clothing, armor, or equipment",
        "no invented age, hair, facial features, or ethnicity",
        "no invented relics or phenomena",
        "no text, captions, labels, logos, HUD, or UI",
        "no tarot borders or MMO-poster composition",
    ]

    scene_spec = SceneSpecModel(
        event_title=memory_object.event_title,
        event_id=memory_object.event_id,
        location=memory_object.location_environment,
        environment=memory_object.location_environment,
        participants=participants,
        story_marks=story_marks,
        equipment=equipment,
        relic_state=relic_state,
        pose_action=memory_object.action_composition,
        phenomena=phenomena,
        emotional_tone=memory_object.emotional_tone,
        composition=chosen_composition,
        must_preserve=must_preserve,
        must_not_invent=must_not_invent,
        style=style or SceneSpecModel.model_fields["style"].default,
    )
    return scene_spec


_PHENOMENA_NAMES = {
    "echo",
    "knot",
    "veil",
    "well",
    "awakening",
    "rift",
    "storm",
    "echoes",
    "knots",
    "veils",
    "wells",
    "awakenings",
    "rifts",
    "storms",
}


def _looks_like_phenomena(memory_object: MemoryObjectModel) -> bool:
    return any(r.lower() in _PHENOMENA_NAMES for r in memory_object.relics_involved)


def compile_painting_prompt(scene_spec: SceneSpecModel) -> str:
    """
    Compile the structured scene spec into provider-specific image instructions
    with explicit conceptual sections.
    """
    participants_text = (
        "; ".join(
            f"{p.character_name} ({p.role_in_event})" for p in scene_spec.participants
        )
        or "No participants."
    )

    historical_lines: list[str] = []
    for p in scene_spec.participants:
        if p.identity_strategy == "historical_portrait" and p.portrait_image_url:
            historical_lines.append(
                f"{p.character_name}: use historical portrait ({p.portrait_version_id})"
            )
        elif p.identity_strategy == "silhouette":
            historical_lines.append(
                f"{p.character_name}: silhouette or rear view, identity not invented"
            )
        else:
            historical_lines.append(
                f"{p.character_name}: {p.identity_strategy.replace('_', ' ')} "
                "framing, identity not invented"
            )

    story_marks_text = "; ".join(scene_spec.story_marks) or "None recorded."
    equipment_text = "; ".join(scene_spec.equipment) or "None recorded."
    phenomena_text = "; ".join(scene_spec.phenomena) or "None recorded."
    composition_text = composition_guidance(scene_spec.composition)

    sections = [
        ("SCENE", f"{scene_spec.event_title}. {scene_spec.location}."),
        ("PARTICIPANTS", participants_text),
        ("HISTORICAL APPEARANCE", "; ".join(historical_lines) or "None."),
        ("ACTION", scene_spec.pose_action),
        (
            "RELICS/EQUIPMENT",
            f"Relics: {scene_spec.relic_state}. Equipment: {equipment_text}",
        ),
        ("STORYMARKS", story_marks_text),
        ("PHENOMENA", phenomena_text),
        ("ATMOSPHERE", scene_spec.emotional_tone),
        ("COMPOSITION", composition_text),
        ("PRESERVE", "; ".join(scene_spec.must_preserve)),
        ("DO NOT INVENT", "; ".join(scene_spec.must_not_invent)),
        ("VISUAL STYLE", scene_spec.style),
    ]
    return " ".join(f"[{name}] {body}" for name, body in sections)
