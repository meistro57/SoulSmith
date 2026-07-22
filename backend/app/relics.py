# backend/app/relics.py
"""
SoulSmith Phase 6: Relic Recognition Engine
Relic progression driven by narrative conditions and Chronicle evidence.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

RelicStage = Literal[
    "Dormant",
    "Remembered",
    "Awakened",
    "Overdrawn",
    "Fractured",
    "Transfigured",
]

RELIC_STAGES_ORDER: List[RelicStage] = [
    "Dormant",
    "Remembered",
    "Awakened",
    "Overdrawn",
    "Fractured",
    "Transfigured",
]


class RelicModel(BaseModel):
    id: str
    soul_id: str
    constellation_id: Optional[str] = None
    name: str
    stage: RelicStage = "Dormant"
    effect: str
    overdraw_consequence: str
    evocative_question: str
    required_thread_type: Optional[str] = None
    cross_aspect_forms: Dict[str, str] = Field(default_factory=dict)
    is_anchor: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelicEventModel(BaseModel):
    id: str
    relic_id: str
    soul_id: str
    action: str  # attune | overdraw | fracture | repair | transfigure
    previous_stage: str
    new_stage: str
    narrative_condition_met: str
    chronicle_evidence_summary: str
    created_at: Optional[str] = None


# Deprecated simple request format maintained for backward compatibility
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


# Phase 6 Narrative-Driven Relic Request Schemas


class RelicNarrativeAttuneRequest(BaseModel):
    relic_id: str
    soul_id: str = "Kaelen the Star-Watcher"
    narrative_condition_met: str
    chronicle_evidence_summary: str


class RelicOverdrawRequest(BaseModel):
    relic_id: str
    soul_id: str = "Kaelen the Star-Watcher"
    intensity_boost: str = "Ascendancy Score +1"


class RelicRepairRequest(BaseModel):
    relic_id: str
    soul_id: str = "Kaelen the Star-Watcher"
    repair_evidence_summary: str


class RelicTransfigureRequest(BaseModel):
    relic_id: str
    soul_id: str = "Kaelen the Star-Watcher"
    anchor_name: str
    transfigured_form: str


# Legacy processor
def process_relic_attunement(req: RelicAttuneRequest) -> RelicAttuneResponse:
    curr_idx = (
        RELIC_STAGES_ORDER.index(req.current_stage)
        if req.current_stage in RELIC_STAGES_ORDER
        else 0
    )

    strain_penalty = 0
    if req.action == "attune":
        new_idx = min(len(RELIC_STAGES_ORDER) - 1, curr_idx + 1)
        new_stage = RELIC_STAGES_ORDER[new_idx]
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
