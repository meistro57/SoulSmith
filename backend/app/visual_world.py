# backend/app/visual_world.py
"""
Phase 4: Visual Worldsmith models.

Persistent visual identities for world entities (locations, relics, phenomena).
The image represents the world; it never defines it. Generated candidates are
separate from immutable visual versions, mirroring the portrait candidate flow.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

VisualEntityType = Literal["location", "relic", "phenomenon"]
WorldCandidateStatus = Literal["pending", "generated", "approved", "rejected", "failed"]


class VisualEntityVersionModel(BaseModel):
    """An immutable snapshot of what a world entity looked like at a point in time."""

    version_id: str
    entity_id: str
    entity_type: VisualEntityType
    version_number: int
    label: str
    canonical_snapshot: Dict[str, Any] = Field(default_factory=dict)
    image_url: str
    source_version_id: Optional[str] = None
    provider: str = "comfyui"
    provider_model: Optional[str] = None
    created_at: Optional[str] = None


class WorldVisualCandidateModel(BaseModel):
    """A generated representation awaiting human approval; never canonical on its own."""

    candidate_id: str
    entity_id: str
    entity_type: VisualEntityType
    source_visual_version_id: Optional[str] = None
    generation_type: str = "initial"
    canonical_snapshot: Dict[str, Any] = Field(default_factory=dict)
    canonical_delta: Dict[str, Any] = Field(default_factory=dict)
    compiled_prompt: str
    negative_prompt: Optional[str] = None
    reference_image_url: Optional[str] = None
    workflow_role: Optional[str] = None
    provider: str = "mock"
    provider_model: Optional[str] = None
    provider_request_id: Optional[str] = None
    generation_seed: Optional[int] = None
    generated_image_url: Optional[str] = None
    status: WorldCandidateStatus = "pending"
    failure_reason: Optional[str] = None
    resulting_visual_version_id: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None


class CreateWorldVisualCandidateRequest(BaseModel):
    entity_type: VisualEntityType
    entity_id: str
    name: str
    canonical_state: Dict[str, Any] = Field(default_factory=dict)
    generation_type: str = "initial"
    source_visual_version_id: Optional[str] = None
    style: str = "soulsmith_painterly"


class GenerateWorldVisualCandidateRequest(BaseModel):
    provider_type: Optional[str] = None
    seed: Optional[int] = None
