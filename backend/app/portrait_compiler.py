# backend/app/portrait_compiler.py
"""
SoulSmith Deterministic Portrait Prompt Compiler.
Compiles canonical character identity, active story marks, equipment state, and continuity rules into structured generation prompts.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.visual_memory import (
    AvatarIdentityModel,
    EquipmentAppearanceModel,
    StoryMarkModel,
)


class PromptCompilationResult(BaseModel):
    subject_identity: str
    continuity_requirements: list[str]
    story_marks: list[str]
    equipment: dict[str, Any]
    expression: str
    composition: str
    lighting: str
    style: str
    negative_constraints: list[str]
    compiled_prompt: str


def _build_changes_text(
    generation_type: str,
    marks: list[StoryMarkModel],
    equipment: EquipmentAppearanceModel,
) -> str:
    if generation_type == "story_mark_update":
        if marks:
            latest = marks[-1]
            return (
                f"Add the new canonical story mark: {latest.mark_type.replace('_', ' ')} "
                f"on {latest.location.replace('_', ' ')}."
            )
        return "Add the newly canonical story mark without inventing additional marks."
    if generation_type == "equipment_update":
        return (
            "Update equipment, clothing, and relic appearance to the canonical "
            f"equipment state (armor: {equipment.armor}; clothing: {equipment.clothing})."
        )
    if generation_type == "age_update":
        return "Age this same character forward while preserving facial identity."
    if generation_type == "manual_regeneration":
        return "Re-render the same canonical character state without altering identity or marks."
    return "None. This is an initial portrait with no prior canonical changes."


def compile_portrait_prompt(
    *,
    identity: AvatarIdentityModel,
    equipment: EquipmentAppearanceModel | None = None,
    story_marks: list[StoryMarkModel] | None = None,
    reference_image_url: str | None = None,
    generation_type: str = "initial",
    emotional_state: str = "focused",
    style_preset: str = "storybook_painterly",
) -> PromptCompilationResult:
    """
    Deterministically compiles a canonical character state into a structured prompt object.
    Separates canonical facts from artistic framing, and strengthens continuity
    instructions when a reference portrait is supplied (continuity generations).
    """
    marks = story_marks or []
    equip = equipment or EquipmentAppearanceModel(soul_id=identity.soul_id)

    # Subject identity
    subject_identity = (
        f"Portrait of {identity.soul_id}, a {identity.species}. "
        f"Face: {identity.face}. Eyes: {identity.eyes}. Hair: {identity.hair}. Build: {identity.body}."
    )

    # Story marks descriptions
    formatted_marks = [
        f"{m.mark_type.replace('_', ' ').title()} on {m.location.replace('_', ' ')} ({m.visibility}, {m.status}, acquired {m.acquired_at})"
        for m in marks
    ]

    # Equipment description dict
    equipment_dict = {
        "armor": equip.armor,
        "clothing": equip.clothing,
        "weapons": equip.weapons,
        "relics": equip.relics,
        "backpacks_cloaks": equip.backpacks_cloaks,
    }

    # Strict continuity rules
    continuity_requirements = [
        f"Preserve facial structure: {identity.face}",
        f"Preserve species and identifying features: {identity.species}, eyes: {identity.eyes}, hair: {identity.hair}",
        "Retain all existing permanent story marks without alteration",
        "Do not remove relics or equipment unless canonical state changed",
        "Do not alter character age unless explicitly requested in generation type",
        "Do not invent unrecorded scars, tattoos, burns, injuries, or uncanonical accessories",
    ]

    is_reference = bool(reference_image_url) or generation_type != "initial"
    if is_reference:
        continuity_requirements.extend(
            [
                "Same character as the reference portrait: identical facial structure",
                "Same identifying features (eyes, hair, species, build) as the reference portrait",
                "Apply only the requested canonical changes; preserve everything else from the reference",
            ]
        )

    if reference_image_url:
        continuity_requirements.append(
            f"Maintain strict visual continuity with reference portrait baseline: {reference_image_url}"
        )

    if generation_type == "story_mark_update" and marks:
        latest_mark = marks[-1]
        continuity_requirements.append(
            f"Add new canonical mark from recent Chronicle event: {latest_mark.mark_type} on {latest_mark.location}"
        )

    # Framing and artistic parameters
    expression = f"{emotional_state.title()} expression, observant and resolute"
    composition = (
        "Upper body hero portrait framing, centered alignment, clear focal separation"
    )
    lighting = "Chiaroscuro atmosphere with subtle starlight accent rim lighting"

    if style_preset == "storybook_painterly":
        style = "Storybook oil-on-canvas painterly style, rich HSL color palette, soft brushwork texture"
    elif style_preset == "dark_fantasy_chiaroscuro":
        style = "Dark fantasy chiaroscuro painting, deep shadows, mythic atmosphere, detailed specular highlights"
    else:
        style = (
            "Mythic fantasy character portrait style, fine detail, harmonious palette"
        )

    negative_constraints = [
        "deformed features",
        "extra limbs",
        "unrecorded scars or tattoos",
        "modern technology",
        "photorealistic photo frame",
        "out of character weapons",
        "blurry details",
    ]

    if is_reference:
        negative_constraints.extend(
            [
                "different character than the reference portrait",
                "altered facial structure",
                "changed species, eye color, or hair color",
                "invented marks, scars, or accessories",
            ]
        )

    # Assemble final compiled prompt deterministically
    marks_text = (
        f" Story Marks: {'; '.join(formatted_marks)}."
        if formatted_marks
        else " Story Marks: None."
    )
    equip_text = (
        f" Attire: {equip.clothing}, {equip.armor}. "
        f"Weapons: {', '.join(equip.weapons) if equip.weapons else 'None'}. "
        f"Relics: {', '.join(equip.relics) if equip.relics else 'None'}."
    )

    changes_text = _build_changes_text(generation_type, marks, equip)
    preserve_text = "; ".join(continuity_requirements)
    must_not_text = "; ".join(negative_constraints)

    compiled_prompt = (
        f"CANONICAL IDENTITY: {subject_identity}{marks_text}{equip_text} "
        f"CANONICAL CHANGES: {changes_text} "
        f"MUST PRESERVE: {preserve_text} "
        f"MUST NOT INVENT: {must_not_text} "
        f"ARTISTIC FRAMING: Expression: {expression}. Style: {style}. {composition}. {lighting}."
    )

    return PromptCompilationResult(
        subject_identity=subject_identity,
        continuity_requirements=continuity_requirements,
        story_marks=formatted_marks,
        equipment=equipment_dict,
        expression=expression,
        composition=composition,
        lighting=lighting,
        style=style,
        negative_constraints=negative_constraints,
        compiled_prompt=compiled_prompt,
    )
