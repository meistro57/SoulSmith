"""
SoulSmith Deterministic Rules Engine
Calculates outcome classes, resource deltas, and state progression.
"""

from typing import List
from pydantic import BaseModel
from app.grammar import InterpretedDiceRoll


class SoulSheetResources(BaseModel):
    resonance: int = 3  # 0 to 6
    strain: int = 0  # 0 to 6
    thread_count: int = 1  # 0 to 5


class ResolveSceneRequest(BaseModel):
    dice_read: InterpretedDiceRoll
    chosen_approach: str
    resonance_spent: int = 0
    strain_accepted: int = 0
    player_intent: str
    soul_name: str = "Unbound Soul"
    resources: SoulSheetResources


class ResolveSceneResponse(BaseModel):
    outcome_class: str  # ascendancy | marked_success | revelatory_failure | collapse
    outcome_title: str
    rules_summary: str
    resonance_delta: int
    strain_delta: int
    thread_delta: int
    new_resources: SoulSheetResources
    fracture_triggered: bool
    canon_facts: List[str]


VERDICT_OUTCOME_MAP = {
    "Ascend": "ascendancy",
    "Scar": "marked_success",
    "Stall": "revelatory_failure",
    "Twist": "marked_success",
    "Reveal": "revelatory_failure",
    "Collapse": "collapse",
}


def evaluate_scene_outcome(req: ResolveSceneRequest) -> ResolveSceneResponse:
    base_verdict = req.dice_read.interpretation.verdict
    raw_outcome = VERDICT_OUTCOME_MAP.get(base_verdict, "marked_success")

    # Modifiers
    resonance_bonus = req.resonance_spent
    strain_boost = req.strain_accepted
    approach_match = (
        req.chosen_approach.lower() == req.dice_read.interpretation.approach.lower()
    )

    score = 0
    if raw_outcome == "ascendancy":
        score += 3
    elif raw_outcome == "marked_success":
        score += 2
    elif raw_outcome == "revelatory_failure":
        score += 1
    else:  # collapse
        score += 0

    score += resonance_bonus
    score += strain_boost
    if approach_match:
        score += 1

    # Final Outcome Determination
    if score >= 4:
        final_outcome = "ascendancy"
        title = "Ascendancy"
        res_delta = -req.resonance_spent + (
            1 if req.dice_read.interpretation.spark == "Wonder" else 0
        )
        str_delta = req.strain_accepted - 1 if req.resources.strain > 0 else 0
        thr_delta = 1
        fact = f"{req.soul_name} cleanly achieved their intent with mythic momentum."
    elif score == 3:
        final_outcome = "marked_success"
        title = "Marked Success"
        res_delta = -req.resonance_spent
        str_delta = req.strain_accepted + 1
        thr_delta = 1
        fact = f"{req.soul_name} accomplished their intent, but paid a price in Strain and pressure."
    elif score == 2:
        final_outcome = "revelatory_failure"
        title = "Revelatory Failure"
        res_delta = -req.resonance_spent + 1
        str_delta = req.strain_accepted
        thr_delta = 0
        fact = f"{req.soul_name} failed to reach their primary intent, but unlocked a crucial revelation."
    else:
        final_outcome = "collapse"
        title = "Collapse"
        res_delta = -req.resonance_spent
        str_delta = req.strain_accepted + 2
        thr_delta = -1 if req.resources.thread_count > 0 else 0
        fact = f"Reality buckled around {req.soul_name}, escalating threat and straining the Soul."

    # Clamp resources
    new_res = max(0, min(6, req.resources.resonance + res_delta))
    new_str = max(0, min(6, req.resources.strain + str_delta))
    new_thr = max(0, min(5, req.resources.thread_count + thr_delta))

    fracture = new_str >= 6

    canon_list = [fact]
    if fracture:
        canon_list.append(
            f"CRITICAL: {req.soul_name}'s Strain reached maximum (6/6). A Soul Fracture has occurred!"
        )
    if req.dice_read.interpretation.thread in ["Bond", "Memory", "Mark", "Prophecy"]:
        canon_list.append(
            f"A lasting [{req.dice_read.interpretation.thread}] Thread has been recorded into the World Chronicle."
        )

    summary_text = (
        f"Outcome: {title}. "
        f"Resonance: {new_res}/6 ({res_delta:+d}), "
        f"Strain: {new_str}/6 ({str_delta:+d}), "
        f"Threads: {new_thr}/5 ({thr_delta:+d})."
    )

    return ResolveSceneResponse(
        outcome_class=final_outcome,
        outcome_title=title,
        rules_summary=summary_text,
        resonance_delta=res_delta,
        strain_delta=str_delta,
        thread_delta=thr_delta,
        new_resources=SoulSheetResources(
            resonance=new_res, strain=new_str, thread_count=new_thr
        ),
        fracture_triggered=fracture,
        canon_facts=canon_list,
    )
