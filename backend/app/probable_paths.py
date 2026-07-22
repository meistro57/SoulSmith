# backend/app/probable_paths.py
"""
SoulSmith Phase 5: Probable Paths Models & What-If Simulation Engine.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ManifestationType = Literal["dream", "rumor", "alternate_scene", "echo_aspect"]
ProbablePathStatus = Literal["dormant", "echoing", "manifested", "reconciled"]


class ProbablePathModel(BaseModel):
    id: str
    event_id: Optional[str] = None
    soul_id: str
    path_title: str
    chosen_path: str
    unchosen_approach: str
    potential_outcome_class: str
    manifestation_type: ManifestationType = "dream"
    status: ProbablePathStatus = "dormant"
    provenance_summary: str
    created_at: Optional[str] = None


class CreateProbablePathRequest(BaseModel):
    soul_id: str
    path_title: str
    chosen_path: str
    unchosen_approach: str
    potential_outcome_class: str = "marked_success"
    event_id: Optional[str] = None
    manifestation_type: ManifestationType = "dream"
    provenance_summary: Optional[str] = None


class ManifestPathRequest(BaseModel):
    path_id: str
    manifestation_type: ManifestationType
    status: ProbablePathStatus = "echoing"


class ExploreAlternateSceneRequest(BaseModel):
    path_id: str
    soul_name: str = "Kaelen the Star-Watcher"


class AlternateSceneResult(BaseModel):
    path_id: str
    path_title: str
    unchosen_approach: str
    alternate_prose: str
    divergence_notes: str
    canonical_integrity_preserved: bool = True
    suggested_insights: List[str] = Field(default_factory=list)


def simulate_alternate_scene_exploration(
    path: ProbablePathModel, soul_name: str
) -> AlternateSceneResult:
    """
    Generates a deterministic What-If narrative simulation of the unchosen approach,
    guaranteeing that canonical history remains unmutated while giving the player
    rich insight into the unchosen probability branch.
    """
    prose = (
        f"In the shadow of what might have been, {soul_name} chose {path.unchosen_approach} "
        f"instead of {path.chosen_path}. Where silence once reigned, the unchosen path unreeled "
        f"like an unspooled thread across the salt mirrors. A quiet ripple of {path.potential_outcome_class} "
        f"spread through the lower archives, demonstrating that no choice dies completely."
    )

    divergence = (
        f"Probability Branch #{path.id[:6]}: Explored '{path.unchosen_approach}'. "
        f"Canonical history retained main timeline record without mutation."
    )

    insights = [
        f"How would {soul_name}'s relationship with the Foe change if '{path.unchosen_approach}' were canon?",
        "What relic would have awakened if this branch were integrated into a Deep Thread?",
        "Notice that both choices sprang from the same core desire.",
    ]

    return AlternateSceneResult(
        path_id=path.id,
        path_title=path.path_title,
        unchosen_approach=path.unchosen_approach,
        alternate_prose=prose,
        divergence_notes=divergence,
        canonical_integrity_preserved=True,
        suggested_insights=insights,
    )
