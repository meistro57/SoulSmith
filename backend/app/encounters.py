# backend/app/encounters.py
"""
SoulSmith structured encounter framing service.
"""

from __future__ import annotations

import hashlib
from typing import List

from pydantic import BaseModel, Field

from app.grammar import InterpretedDiceRoll


class EncounterFrameRequest(BaseModel):
    dice_read: InterpretedDiceRoll
    soul_name: str = "Unbound Soul"
    world_context: List[str] = Field(default_factory=list)


class EncounterFrame(BaseModel):
    title: str
    phenomenon_type: str
    visible_situation: str
    hidden_need: str
    stakes: str
    pressure_clock: int = Field(..., ge=1, le=6)
    questions: List[str]
    suggested_actions: List[str]


PHENOMENA_BY_PRESSURE = {
    "Time": "Echo",
    "Fear": "Veil",
    "Debt": "Knot",
    "Exposure": "Rift",
    "Corruption": "Corruption",
    "Scarcity": "Well",
}

DOMAIN_NOUNS = {
    "Self": "mirror",
    "Ally": "companion",
    "Foe": "adversary",
    "Place": "threshold",
    "Relic": "relic",
    "Omen": "sign",
}

AIM_VERBS = {
    "Seek": "calls to be found",
    "Protect": "asks to be guarded",
    "Bind": "waits to be bound",
    "Break": "strains to be broken",
    "Reveal": "wants to be revealed",
    "Transform": "is ready to change its shape",
}


def _stable_clock(dice_read: InterpretedDiceRoll) -> int:
    raw = dice_read.raw
    seed = ":".join(
        str(raw[die]) for die in ("d20", "d12", "d10", "percentile", "d8", "d6", "d4")
    )
    digest = hashlib.sha256(
        f"{dice_read.grammar_version}:{seed}".encode("utf-8")
    ).digest()
    return digest[0] % 5 + 1


def generate_encounter_frame(req: EncounterFrameRequest) -> EncounterFrame:
    """
    Create the encounter's pre-action fiction from the canonical roll.

    This is intentionally deterministic and bounded: it establishes what exists before
    the player chooses an intent, without resolving the scene or prescribing meaning.
    """
    from app.db import get_all_open_questions, get_all_seeds

    read = req.dice_read.interpretation
    phenomenon = PHENOMENA_BY_PRESSURE.get(read.pressure, "Echo")
    domain_noun = DOMAIN_NOUNS.get(read.domain, "sign")
    aim_phrase = AIM_VERBS.get(read.aim, "waits for attention")
    context_hint = (
        req.world_context[0]
        if req.world_context
        else "an old promise no one present remembers making"
    )

    # Check for active seeds or open questions for context richness
    seeds = get_all_seeds()
    questions_list = get_all_open_questions()
    active_seed = seeds[0] if seeds else None
    active_question = questions_list[0]["question_text"] if questions_list else None

    title = f"The {read.spark} {domain_noun.title()} Under {read.pressure}"
    visible = (
        f"A {domain_noun} touched by {phenomenon.lower()}-light {aim_phrase}; "
        f"every attempt to ignore it makes the air taste faintly of {read.thread.lower()}."
    )
    if active_seed:
        visible += f" (Echo of symbol '{active_seed['symbol']}' [{active_seed['stage']} stage])."

    hidden = (
        f"It needs {req.soul_name} to notice how {read.pressure.lower()} has bent the shape of {context_hint}, "
        "but it will not explain itself first."
    )
    stakes = (
        f"If the moment is mishandled, the {read.domain.lower()} becomes harder to approach and the "
        f"next {read.thread} Thread will arrive already tangled."
    )

    frame_questions = [
        f"What part of the {read.domain.lower()} feels too familiar?",
        f"Who benefits if the {read.pressure.lower()} remains unnamed?",
        f"What would {read.aim.lower()} change that mere success would not?",
    ]
    if active_question:
        frame_questions.append(f"Unresolved Question: {active_question}")

    return EncounterFrame(
        title=title,
        phenomenon_type=phenomenon,
        visible_situation=visible,
        hidden_need=hidden,
        stakes=stakes,
        pressure_clock=_stable_clock(req.dice_read),
        questions=frame_questions,
        suggested_actions=[
            f"Approach with {read.approach} and ask what the {domain_noun} refuses to show directly.",
            "Spend Resonance to stabilise one vivid clue before acting.",
            "Accept Strain to force the hidden need into the open, consequences and all.",
        ],
    )
