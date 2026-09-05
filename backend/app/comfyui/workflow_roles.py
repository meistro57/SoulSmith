# backend/app/comfyui/workflow_roles.py
"""
Centralised workflow-role selection for portrait generation.

SoulSmith thinks in terms of generation intents (initial, story_mark_update,
equipment_update, age_update, manual_regeneration); this module maps those intents
to a concrete ComfyUI workflow role. All path/role decisions live here so no
route handler or provider scatters workflow choices.
"""

from __future__ import annotations

INITIAL_ROLE = "portrait_initial"
REFERENCE_ROLE = "portrait_reference"

#: Generation types that require a source portrait for identity continuity.
REFERENCE_REQUIRED_GENERATION_TYPES = frozenset(
    {
        "story_mark_update",
        "equipment_update",
        "age_update",
        "manual_regeneration",
    }
)


def select_workflow_role(generation_type: str) -> str:
    """
    Map a generation type to a workflow role.

    ``initial`` always uses the plain text-to-image role; every continuity type
    uses the reference role (the provider then enforces that a reference image is
    actually available rather than silently falling back to text-to-image).
    """
    if generation_type == "initial":
        return INITIAL_ROLE
    if generation_type in REFERENCE_REQUIRED_GENERATION_TYPES:
        return REFERENCE_ROLE
    return INITIAL_ROLE


def requires_reference(generation_type: str) -> bool:
    """Return True when a generation type is a continuity update needing a source."""
    return generation_type in REFERENCE_REQUIRED_GENERATION_TYPES
