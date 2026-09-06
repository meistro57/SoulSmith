# backend/app/comfyui/workflow_roles.py
"""
Centralised workflow-role selection for portrait and world-entity generation.

SoulSmith thinks in terms of generation intents (initial, story_mark_update,
equipment_update, age_update, manual_regeneration for portraits; initial,
state_update, damage_update, etc. for world entities); this module maps those
intents to a concrete ComfyUI workflow role. All path/role decisions live here so
no route handler or provider scatters workflow choices.
"""

from __future__ import annotations

from typing import Dict

INITIAL_ROLE = "portrait_initial"
REFERENCE_ROLE = "portrait_reference"

# Chronicle Paintings (Phase 12) use their own text-to-image workflow. v1 does
# not support multi-participant identity conditioning, so this is a single
# role, not an initial/reference pair.
CHRONICLE_PAINTING_ROLE = "chronicle_painting"

#: Generation types that require a source portrait for identity continuity.
REFERENCE_REQUIRED_GENERATION_TYPES = frozenset(
    {
        "story_mark_update",
        "equipment_update",
        "age_update",
        "manual_regeneration",
    }
)

# World entity workflow roles (Phase 4). Locations/phenomena use environment
# workflows; relics use object workflows.
ENVIRONMENT_INITIAL_ROLE = "environment_initial"
ENVIRONMENT_REFERENCE_ROLE = "environment_reference"
OBJECT_INITIAL_ROLE = "object_initial"
OBJECT_REFERENCE_ROLE = "object_reference"

WORLD_ENTITY_ROLES: Dict[str, tuple[str, str]] = {
    "location": (ENVIRONMENT_INITIAL_ROLE, ENVIRONMENT_REFERENCE_ROLE),
    "relic": (OBJECT_INITIAL_ROLE, OBJECT_REFERENCE_ROLE),
    "phenomenon": (ENVIRONMENT_INITIAL_ROLE, ENVIRONMENT_REFERENCE_ROLE),
}

#: World generation types that represent a continuity update (reference required).
WORLD_REFERENCE_GENERATION_TYPES = frozenset(
    {
        "state_update",
        "stage_update",
        "damage_update",
        "restoration",
        "seasonal_update",
        "environmental_shift",
        "magical_transformation",
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


def select_world_workflow_role(entity_type: str, generation_type: str) -> str:
    """
    Map a world entity type + generation type to a world workflow role.

    Non-initial world generation types are continuity updates and use the
    reference workflow for the entity's category (environment or object).
    """
    initial_role, reference_role = WORLD_ENTITY_ROLES.get(
        entity_type, (ENVIRONMENT_INITIAL_ROLE, ENVIRONMENT_REFERENCE_ROLE)
    )
    if generation_type == "initial":
        return initial_role
    return reference_role


def requires_world_reference(generation_type: str) -> bool:
    return generation_type in WORLD_REFERENCE_GENERATION_TYPES
