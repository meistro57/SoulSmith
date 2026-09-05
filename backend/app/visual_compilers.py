# backend/app/visual_compilers.py
"""
Phase 4: deterministic visual prompt compilers for world entities.

Each compiler transforms a canonical snapshot into a structured scene description
without embedding model-specific syntax into canonical data. A shared canonical
delta helper diffs the previous vs current snapshot so continuity generations
preserve identity and apply only the recorded change.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

STYLE_PRESETS: Dict[str, str] = {
    "soulsmith_painterly": "painterly mythic realism, rich HSL palette, soft brushwork",
    "etched_chronicle": "etched chronicle plate, fine linework, archival engraving",
    "dark_mythic": "dark mythic atmosphere, deep shadows, dramatic specular detail",
    "luminous_storybook": "luminous storybook illustration, warm glow, storybook framing",
    "ancient_manuscript": "ancient illuminated manuscript, aged parchment, gold leaf accents",
    "dream_memory": "dreamlike memory, soft focus, hazy edges, nostalgic light",
}

DEFAULT_STYLE = "soulsmith_painterly"


class VisualCompilationResult(BaseModel):
    entity_type: str
    subject: str
    visual_anchors: List[str]
    continuity_requirements: List[str]
    requested_changes: List[str]
    composition: str
    style: str
    negative_constraints: List[str]
    compiled_prompt: str


def compile_canonical_delta(
    previous: Optional[Dict[str, Any]], current: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Deterministically diff two snapshots into preserve/change/remove descriptions.

    ``previous`` is the source version's snapshot (may be None for initial
    generations). Anchored identity fields are compared textually; no semantic
    diff engine is assumed.
    """
    previous = previous or {}
    preserve: List[str] = []
    change: List[str] = []
    remove: List[str] = []

    for key in sorted(previous):
        old = previous[key]
        if key not in current:
            remove.append(f"{key}: {_fmt(old)} (removed)")
        elif _fmt(old) == _fmt(current[key]):
            preserve.append(f"{key}: {_fmt(old)}")
        else:
            change.append(f"{key}: {_fmt(old)} -> {_fmt(current[key])}")

    for key in sorted(current):
        if key not in previous:
            change.append(f"{key}: {_fmt(current[key])} (added)")

    return {"preserve": preserve, "change": change, "remove": remove}


def _fmt(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def _anchors_from_state(state: Dict[str, Any], keys: List[str]) -> List[str]:
    anchors: List[str] = []
    for key in keys:
        value = state.get(key)
        if isinstance(value, list):
            anchors.extend(str(v) for v in value if v)
        elif value:
            anchors.append(str(value))
    return anchors


def _assemble(
    entity_type: str,
    subject: str,
    anchors: List[str],
    changes: List[str],
    continuity: List[str],
    composition: str,
    style_key: str,
    negative: List[str],
) -> VisualCompilationResult:
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS[DEFAULT_STYLE])
    anchors_text = "; ".join(anchors) if anchors else "None recorded."
    changes_text = "; ".join(changes) if changes else "None."
    preserve_text = (
        "; ".join(continuity) if continuity else "Preserve recorded identity."
    )
    negative_text = "; ".join(negative)

    compiled_prompt = (
        f"CANONICAL IDENTITY: {subject} "
        f"VISUAL ANCHORS: {anchors_text} "
        f"CANONICAL CHANGES: {changes_text} "
        f"MUST PRESERVE: {preserve_text} "
        f"MUST NOT INVENT: {negative_text} "
        f"ARTISTIC FRAMING: {composition} Style: {style}."
    )
    return VisualCompilationResult(
        entity_type=entity_type,
        subject=subject,
        visual_anchors=anchors,
        continuity_requirements=continuity,
        requested_changes=changes,
        composition=composition,
        style=style,
        negative_constraints=negative,
        compiled_prompt=compiled_prompt,
    )


def compile_location_prompt(
    *,
    name: str,
    state: Dict[str, Any],
    previous_snapshot: Optional[Dict[str, Any]] = None,
    generation_type: str = "initial",
    style: str = DEFAULT_STYLE,
) -> VisualCompilationResult:
    location_type = state.get("location_type", "location")
    subject = (
        f"{name}, a {location_type}. "
        f"Architecture: {state.get('architecture', 'unspecified')}. "
        f"Geography: {state.get('geography', 'unspecified')}. "
        f"Lighting: {state.get('lighting', 'unspecified')}. "
        f"Atmosphere: {state.get('atmosphere', 'unspecified')}."
    )
    anchors = _anchors_from_state(
        state,
        ["landmarks", "persistent_identifiers", "symbols", "materials"],
    )
    delta = compile_canonical_delta(previous_snapshot, state)
    continuity = [
        "Preserve overall architecture, spatial layout, and landmark geometry",
        f"Keep identifying landmarks: {', '.join(anchors)}"
        if anchors
        else "Keep recorded landmarks",
    ]
    changes = delta["change"]
    if generation_type == "damage_update":
        changes.append("Apply only the recorded damage; do not invent new destruction")
    elif generation_type == "restoration":
        changes.append("Remove only the damage explicitly repaired by canon")
    composition = "Wide environmental establishing shot, landmark-scale composition, atmosphere-dominant framing"
    negative = [
        "unrelated location",
        "invented landmarks",
        "changed architecture style",
        "modern signage",
        "text or labels",
        "inconsistent geography",
    ]
    return _assemble(
        "location", subject, anchors, changes, continuity, composition, style, negative
    )


def compile_relic_prompt(
    *,
    name: str,
    state: Dict[str, Any],
    previous_snapshot: Optional[Dict[str, Any]] = None,
    generation_type: str = "initial",
    style: str = DEFAULT_STYLE,
) -> VisualCompilationResult:
    object_type = state.get("object_type", "relic")
    stage = state.get("energy_state", state.get("stage", "Dormant"))
    subject = (
        f"{name}, a {object_type}. "
        f"Materials: {state.get('materials', 'unspecified')}. "
        f"Shape: {state.get('shape', 'unspecified')}. "
        f"Engraving: {state.get('engraving', 'none')}. "
        f"Energy state: {stage}."
    )
    anchors = _anchors_from_state(
        state,
        ["persistent_details", "symbol", "engraving", "materials", "colour_language"],
    )
    delta = compile_canonical_delta(previous_snapshot, state)
    continuity = [
        "Preserve the object's physical identity: materials, shape, and permanent marks",
        f"Keep persistent details: {', '.join(anchors)}"
        if anchors
        else "Keep recorded persistent details",
    ]
    changes = delta["change"]
    if generation_type in ("state_update", "stage_update"):
        changes.append(
            f"Render the canonical energy state '{stage}' without altering physical identity"
        )
    composition = "Centered single-object still life, studio presentation, clear silhouette, object-dominant framing"
    negative = [
        "different object",
        "altered materials",
        "missing permanent marks",
        "invented decorations",
        "text or labels",
        "hands or figure",
    ]
    return _assemble(
        "relic", subject, anchors, changes, continuity, composition, style, negative
    )


def compile_phenomenon_prompt(
    *,
    name: str,
    state: Dict[str, Any],
    previous_snapshot: Optional[Dict[str, Any]] = None,
    generation_type: str = "initial",
    style: str = DEFAULT_STYLE,
) -> VisualCompilationResult:
    typology = state.get("typology", "phenomenon")
    stage = state.get("escalation_stage", state.get("stage", "unknown"))
    subject = (
        f"{name}, a {typology}. "
        f"Visible signs: {_fmt(state.get('visible_signs', []))}. "
        f"Energy behaviour: {state.get('energy_behaviour', 'unspecified')}. "
        f"Colour language: {state.get('colour_language', 'unspecified')}. "
        f"Escalation: {stage}."
    )
    anchors = _anchors_from_state(
        state,
        ["persistent_motifs", "visible_signs", "symbol_language", "colour_language"],
    )
    delta = compile_canonical_delta(previous_snapshot, state)
    continuity = [
        "Preserve the phenomenon's visual vocabulary and recurring motifs",
        f"Keep persistent motifs: {', '.join(anchors)}"
        if anchors
        else "Keep recorded motifs",
    ]
    changes = delta["change"]
    if generation_type in ("state_update", "escalation_update"):
        changes.append(
            f"Reflect escalation stage '{stage}' without inventing new motifs"
        )
    composition = "Atmospheric environmental scene, phenomenon-dominant, environment-affected framing"
    negative = [
        "unrelated phenomenon",
        "invented motifs",
        "different colour language",
        "monster anatomy",
        "text or labels",
    ]
    return _assemble(
        "phenomenon",
        subject,
        anchors,
        changes,
        continuity,
        composition,
        style,
        negative,
    )


def compile_visual_prompt(
    *,
    entity_type: str,
    name: str,
    canonical_state: Dict[str, Any],
    generation_type: str = "initial",
    previous_snapshot: Optional[Dict[str, Any]] = None,
    style: str = DEFAULT_STYLE,
) -> VisualCompilationResult:
    if entity_type == "location":
        return compile_location_prompt(
            name=name,
            state=canonical_state,
            previous_snapshot=previous_snapshot,
            generation_type=generation_type,
            style=style,
        )
    if entity_type == "relic":
        return compile_relic_prompt(
            name=name,
            state=canonical_state,
            previous_snapshot=previous_snapshot,
            generation_type=generation_type,
            style=style,
        )
    if entity_type == "phenomenon":
        return compile_phenomenon_prompt(
            name=name,
            state=canonical_state,
            previous_snapshot=previous_snapshot,
            generation_type=generation_type,
            style=style,
        )
    raise ValueError(f"Unsupported visual entity type: {entity_type}")
