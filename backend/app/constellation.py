# backend/app/constellation.py
"""
SoulSmith Phase 4: Soul Constellation Models & API Logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

AwakeningStage = Literal[
    "veiled",
    "echoing",
    "recognizing",
    "resonant",
    "woven",
    "lucid",
]

AWAKENING_STAGE_DESCRIPTIONS: Dict[AwakeningStage, Dict[str, str]] = {
    "veiled": {
        "title": "Veiled",
        "description": "One life appears self-contained. The larger Constellation remains unseen.",
    },
    "echoing": {
        "title": "Echoing",
        "description": "Symbols and patterns recur without explanation across distinct eras or worlds.",
    },
    "recognizing": {
        "title": "Recognizing",
        "description": "The player identifies relationships between echoes across different Aspects.",
    },
    "resonant": {
        "title": "Resonant",
        "description": "Choices in one Aspect begin affecting another through shared Deep Threads.",
    },
    "woven": {
        "title": "Woven",
        "description": "Multiple Aspects intentionally collaborate across the Chronicle through Constellation Anchors.",
    },
    "lucid": {
        "title": "Lucid",
        "description": "The player engages the Constellation as a larger identity while preserving each Aspect's distinct agency.",
    },
}


class AspectModel(BaseModel):
    id: str
    constellation_id: str
    aspect_name: str
    calling: str
    origin: str
    era_or_world: str
    sheet: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class AnchorModel(BaseModel):
    id: str
    constellation_id: str
    anchor_name: str
    relic_id: Optional[str] = None
    connected_aspect_ids: List[str] = Field(default_factory=list)
    relic_form: str
    status: str = "dormant"
    created_at: Optional[str] = None


class CrossAspectBondModel(BaseModel):
    id: str
    constellation_id: str
    source_aspect_id: str
    target_aspect_id: str
    bond_type: str
    description: str
    created_at: Optional[str] = None


class ConstellationModel(BaseModel):
    id: str
    name: str
    unresolved_pattern: str
    awakening_stage: AwakeningStage = "veiled"
    deep_threads: List[str] = Field(default_factory=list)
    aspects: List[AspectModel] = Field(default_factory=list)
    anchors: List[AnchorModel] = Field(default_factory=list)
    bonds: List[CrossAspectBondModel] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateAspectRequest(BaseModel):
    constellation_id: str
    aspect_name: str
    calling: str
    origin: str
    era_or_world: str


class CreateBondRequest(BaseModel):
    constellation_id: str
    source_aspect_id: str
    target_aspect_id: str
    bond_type: str
    description: str


class AdvanceAwakeningRequest(BaseModel):
    constellation_id: str
    target_stage: Optional[AwakeningStage] = None
