# backend/tests/test_visual_compilers.py
from app.visual_compilers import (
    compile_canonical_delta,
    compile_location_prompt,
    compile_phenomenon_prompt,
    compile_relic_prompt,
    compile_visual_prompt,
)
from app.comfyui.workflow_roles import (
    ENVIRONMENT_INITIAL_ROLE,
    ENVIRONMENT_REFERENCE_ROLE,
    OBJECT_INITIAL_ROLE,
    OBJECT_REFERENCE_ROLE,
    select_world_workflow_role,
)

LOCATION_STATE = {
    "location_type": "subterranean hall",
    "architecture": "vast subterranean limestone hall",
    "geography": "flooded archive beneath the Hall of Echoes",
    "lighting": "cold reflected blue light",
    "atmosphere": "quiet, reverberant, ancient",
    "landmarks": [
        "seven black arches",
        "central dais",
        "broken brass observatory ring",
    ],
    "persistent_identifiers": [
        "triangular western doorway",
        "spiral engraving around dais",
    ],
    "damage_state": "intact",
}


def test_location_prompt_preserves_anchors():
    result = compile_location_prompt(name="The Hall of Echoes", state=LOCATION_STATE)
    assert "seven black arches" in result.compiled_prompt
    assert "MUST PRESERVE" in result.compiled_prompt
    assert "CANONICAL CHANGES" in result.compiled_prompt
    assert "The Hall of Echoes" in result.subject
    assert "seven black arches" in result.visual_anchors


def test_location_damage_delta_applied_not_historical():
    damaged = {**LOCATION_STATE, "damage_state": "western arch cracked"}
    result = compile_location_prompt(
        name="The Hall of Echoes",
        state=damaged,
        previous_snapshot=LOCATION_STATE,
        generation_type="damage_update",
    )
    assert "damage_state" in " ".join(result.requested_changes)
    # Anchor still preserved in continuity requirements.
    assert any("seven black arches" in c for c in result.continuity_requirements)


def test_relic_evolution_retains_identity():
    dormant = {
        "object_type": "hand bell",
        "materials": "aged silver and salt-white bronze",
        "shape": "small hand bell",
        "engraving": "spiral engraving around rim",
        "persistent_details": ["three vertical cracks", "black leather handle"],
        "energy_state": "Dormant",
    }
    awakened = {**dormant, "energy_state": "Awakened"}
    result = compile_relic_prompt(
        name="Salt Bell",
        state=awakened,
        previous_snapshot=dormant,
        generation_type="stage_update",
    )
    assert "three vertical cracks" in result.compiled_prompt
    assert "Awakened" in result.compiled_prompt
    assert any("three vertical cracks" in c for c in result.continuity_requirements)


def test_phenomenon_motif_preserved():
    state = {
        "typology": "Veil",
        "visible_signs": ["thin hanging layers of translucent grey light"],
        "persistent_motifs": ["letters appearing backwards inside reflections"],
        "colour_language": "pearl grey, muted violet, cold silver",
        "escalation_stage": 3,
    }
    result = compile_phenomenon_prompt(name="Veil of the Forgotten Name", state=state)
    assert "letters appearing backwards" in result.compiled_prompt
    assert "pearl grey" in result.compiled_prompt


def test_canonical_delta_preserve_change_remove():
    prev = {
        "architecture": "limestone hall",
        "damage_state": "intact",
        "old_trait": "gone",
    }
    curr = {
        "architecture": "limestone hall",
        "damage_state": "cracked",
        "water": "flooded",
    }
    delta = compile_canonical_delta(prev, curr)
    assert any("architecture" in p for p in delta["preserve"])
    assert any("damage_state" in c for c in delta["change"])
    assert any("water" in c for c in delta["change"])
    assert any("old_trait" in r for r in delta["remove"])


def test_compile_visual_prompt_dispatches():
    res = compile_visual_prompt(
        entity_type="relic", name="Salt Bell", canonical_state={"object_type": "bell"}
    )
    assert res.entity_type == "relic"


def test_world_workflow_role_selection():
    assert select_world_workflow_role("location", "initial") == ENVIRONMENT_INITIAL_ROLE
    assert (
        select_world_workflow_role("location", "damage_update")
        == ENVIRONMENT_REFERENCE_ROLE
    )
    assert select_world_workflow_role("relic", "initial") == OBJECT_INITIAL_ROLE
    assert select_world_workflow_role("relic", "stage_update") == OBJECT_REFERENCE_ROLE
    assert (
        select_world_workflow_role("phenomenon", "initial") == ENVIRONMENT_INITIAL_ROLE
    )
    assert (
        select_world_workflow_role("phenomenon", "escalation_update")
        == ENVIRONMENT_REFERENCE_ROLE
    )
