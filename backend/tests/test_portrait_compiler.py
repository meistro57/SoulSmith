# backend/tests/test_portrait_compiler.py
from app.portrait_compiler import compile_portrait_prompt
from app.visual_memory import (
    AvatarIdentityModel,
    EquipmentAppearanceModel,
    StoryMarkModel,
)


def test_deterministic_prompt_compilation():
    identity = AvatarIdentityModel(
        soul_id="Kaelen the Star-Watcher",
        face="Defined features, sharp jawline",
        hair="Raven hair tied back",
        body="Athletic build",
        species="Human Aspect",
        eyes="Amber eyes",
    )
    equipment = EquipmentAppearanceModel(
        soul_id="Kaelen the Star-Watcher",
        armor="Weathered iron pauldrons",
        clothing="Ash-colored travel cloak",
        weapons=["Seer's Starlight Blade"],
        relics=["Dormant Salt Bell"],
        backpacks_cloaks="Wool cloak",
    )
    marks = [
        StoryMarkModel(
            id="mark_1",
            soul_id="Kaelen the Star-Watcher",
            mark_type="scar",
            location="left_cheek",
            origin_event_id="evt_salt_spire_01",
            acquired_at="Year 3, Frostwane",
            visibility="prominent",
            status="permanent",
        )
    ]

    res1 = compile_portrait_prompt(
        identity=identity,
        equipment=equipment,
        story_marks=marks,
        generation_type="story_mark_update",
        emotional_state="focused",
    )

    res2 = compile_portrait_prompt(
        identity=identity,
        equipment=equipment,
        story_marks=marks,
        generation_type="story_mark_update",
        emotional_state="focused",
    )

    # Assert determinism
    assert res1.compiled_prompt == res2.compiled_prompt
    assert res1.subject_identity == res2.subject_identity
    assert len(res1.continuity_requirements) >= 6
    assert "Preserve facial structure" in res1.continuity_requirements[0]
    assert "Scar on left cheek" in res1.story_marks[0]
    assert res1.equipment["armor"] == "Weathered iron pauldrons"
    assert "unrecorded scars" in res1.negative_constraints[2]
