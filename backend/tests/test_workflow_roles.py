# backend/tests/test_workflow_roles.py
from app.comfyui.workflow_roles import (
    INITIAL_ROLE,
    REFERENCE_ROLE,
    requires_reference,
    select_workflow_role,
)


def test_initial_uses_initial_role():
    assert select_workflow_role("initial") == INITIAL_ROLE


def test_story_mark_update_uses_reference_role():
    assert select_workflow_role("story_mark_update") == REFERENCE_ROLE


def test_equipment_update_uses_reference_role():
    assert select_workflow_role("equipment_update") == REFERENCE_ROLE


def test_age_update_uses_reference_role():
    assert select_workflow_role("age_update") == REFERENCE_ROLE


def test_manual_regeneration_uses_reference_role():
    assert select_workflow_role("manual_regeneration") == REFERENCE_ROLE


def test_unknown_type_defaults_to_initial():
    assert select_workflow_role("something_else") == INITIAL_ROLE


def test_requires_reference():
    assert requires_reference("story_mark_update")
    assert requires_reference("equipment_update")
    assert requires_reference("age_update")
    assert requires_reference("manual_regeneration")
    assert not requires_reference("initial")
