"""
SoulSmith Relic Attunement & Evolution Engine
"""

from pydantic import BaseModel


class RelicAttuneRequest(BaseModel):
    relic_id: str
    relic_name: str
    current_stage: str
    action: str  # attune | overdraw | repair | transfigure


class RelicAttuneResponse(BaseModel):
    relic_id: str
    new_stage: str
    effect_unlocked: str
    strain_penalty: int
    canon_note: str


RELIC_STAGES = [
    "Dormant",
    "Remembered",
    "Awakened",
    "Overdrawn",
    "Fractured",
    "Transfigured",
]


def process_relic_attunement(req: RelicAttuneRequest) -> RelicAttuneResponse:
    curr_idx = (
        RELIC_STAGES.index(req.current_stage)
        if req.current_stage in RELIC_STAGES
        else 0
    )

    strain_penalty = 0
    if req.action == "attune":
        new_idx = min(len(RELIC_STAGES) - 1, curr_idx + 1)
        new_stage = RELIC_STAGES[new_idx]
        effect = f"Gains active move: Can substitute one [{new_stage}] Domain face per session."
        note = f"Relic [{req.relic_name}] attuned to stage [{new_stage}]."
    elif req.action == "overdraw":
        new_stage = "Overdrawn"
        strain_penalty = 1
        effect = "Overdrawn power active! Grants automatic Ascendancy score +1, but adds +1 Strain."
        note = f"Relic [{req.relic_name}] overdrawn beyond safe limits."
    elif req.action == "repair":
        new_stage = "Awakened"
        effect = "Repaired and cleansed of glitch strain."
        note = f"Relic [{req.relic_name}] repaired to Awakened stage."
    else:  # transfigure
        new_stage = "Transfigured"
        effect = "Permanently alters one world rule or character gift."
        note = f"Relic [{req.relic_name}] transfigured into mythic legend!"

    return RelicAttuneResponse(
        relic_id=req.relic_id,
        new_stage=new_stage,
        effect_unlocked=effect,
        strain_penalty=strain_penalty,
        canon_note=note,
    )
