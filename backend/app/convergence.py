# backend/app/convergence.py
"""
SoulSmith Phase 7: Convergence & Community Mythology Engine
Multiplayer gatherings, consent-aware shared canon, community world symbols, and merge/fork controls.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

CanonStatus = Literal["private", "opt_in_shared", "public_canon"]
GatheringStatus = Literal["active", "reconciled", "diverged"]


class CommunitySymbolModel(BaseModel):
    id: str
    symbol_name: str
    world_id: str = "world_starforge_01"
    description: str
    significance_score: int = 1
    contributing_souls: List[str] = Field(default_factory=list)
    canon_status: CanonStatus = "opt_in_shared"
    created_at: Optional[str] = None


class GatheringContributionModel(BaseModel):
    id: str
    contributor_soul: str
    role: Literal["Focus", "Anchor", "Witness", "Tempest"]
    resonance_amount: int
    notes: str
    timestamp: Optional[str] = None


class GatheringSessionModel(BaseModel):
    id: str
    room_id: str
    phenomenon_name: str
    target_resonance: int = 10
    current_resonance: int = 0
    roles: Dict[str, str] = Field(default_factory=dict)  # Role -> Soul Name
    contributions: List[GatheringContributionModel] = Field(default_factory=list)
    status: GatheringStatus = "active"
    outcome_summary: Optional[str] = None


class CreateCommunitySymbolRequest(BaseModel):
    symbol_name: str
    description: str
    contributing_souls: List[str] = Field(default_factory=list)
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
    consenting_souls: List[str]


class CanonForkRequest(BaseModel):
    gathering_id: str
    forking_soul: str
    reason: str
