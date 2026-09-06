# backend/app/constellation.py
"""
SoulSmith Phase 4: Soul Constellation Models & API Logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AwakeningStage = Literal[
    "veiled",
    "echoing",
    "recognizing",
    "resonant",
    "woven",
    "lucid",
]

AWAKENING_STAGE_DESCRIPTIONS: dict[AwakeningStage, dict[str, str]] = {
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
    sheet: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class AnchorModel(BaseModel):
    id: str
    constellation_id: str
    anchor_name: str
    relic_id: str | None = None
    connected_aspect_ids: list[str] = Field(default_factory=list)
    relic_form: str
    status: str = "dormant"
    created_at: str | None = None


class CrossAspectBondModel(BaseModel):
    id: str
    constellation_id: str
    source_aspect_id: str
    target_aspect_id: str
    bond_type: str
    description: str
    created_at: str | None = None


class ConstellationModel(BaseModel):
    id: str
    name: str
    unresolved_pattern: str
    awakening_stage: AwakeningStage = "veiled"
    deep_threads: list[str] = Field(default_factory=list)
    aspects: list[AspectModel] = Field(default_factory=list)
    anchors: list[AnchorModel] = Field(default_factory=list)
    bonds: list[CrossAspectBondModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


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
    target_stage: AwakeningStage | None = None
