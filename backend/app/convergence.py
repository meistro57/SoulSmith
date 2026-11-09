# backend/app/convergence.py
"""
SoulSmith Phase 7: Convergence & Community Mythology Engine
Multiplayer gatherings, consent-aware shared canon, community world symbols, and merge/fork controls.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CanonStatus = Literal["private", "opt_in_shared", "public_canon"]
GatheringStatus = Literal["active", "reconciled", "diverged"]


class CommunitySymbolModel(BaseModel):
    id: str
    symbol_name: str
    world_id: str = "world_starforge_01"
    description: str
    significance_score: int = 1
    contributing_souls: list[str] = Field(default_factory=list)
    canon_status: CanonStatus = "opt_in_shared"
    created_at: str | None = None


class GatheringContributionModel(BaseModel):
    id: str
    contributor_soul: str
    role: Literal["Focus", "Anchor", "Witness", "Tempest"]
    resonance_amount: int
    notes: str
    timestamp: str | None = None


class GatheringSessionModel(BaseModel):
    id: str
    room_id: str
    phenomenon_name: str
    target_resonance: int = 10
    current_resonance: int = 0
    roles: dict[str, str] = Field(default_factory=dict)  # Role -> Soul Name
    contributions: list[GatheringContributionModel] = Field(default_factory=list)
    status: GatheringStatus = "active"
    outcome_summary: str | None = None


class CreateCommunitySymbolRequest(BaseModel):
    symbol_name: str
    description: str
    contributing_souls: list[str] = Field(default_factory=list)
    canon_status: CanonStatus = "opt_in_shared"


class GatheringContributeRequest(BaseModel):
    gathering_id: str
    contributor_soul: str
    role: Literal["Focus", "Anchor", "Witness", "Tempest"]
    resonance_amount: int = Field(default=1, ge=1, le=10)
    notes: str


class CanonMergeRequest(BaseModel):
    gathering_id: str
    symbol_name: str
    description: str
    consenting_souls: list[str]


class CanonForkRequest(BaseModel):
    gathering_id: str
    forking_soul: str
    reason: str
