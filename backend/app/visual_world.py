# backend/app/visual_world.py
"""
Phase 4: Visual Worldsmith models.

Persistent visual identities for world entities (locations, relics, phenomena).
The image represents the world; it never defines it. Generated candidates are
separate from immutable visual versions, mirroring the portrait candidate flow.
"""

from __future__ import annotations

from typing import Any, Literal

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
    canonical_snapshot: dict[str, Any] = Field(default_factory=dict)
    image_url: str
    source_version_id: str | None = None
    provider: str = "comfyui"
    provider_model: str | None = None
    created_at: str | None = None


class WorldVisualCandidateModel(BaseModel):
    """A generated representation awaiting human approval; never canonical on its own."""

    candidate_id: str
    entity_id: str
    entity_type: VisualEntityType
    source_visual_version_id: str | None = None
    generation_type: str = "initial"
    canonical_snapshot: dict[str, Any] = Field(default_factory=dict)
    canonical_delta: dict[str, Any] = Field(default_factory=dict)
    compiled_prompt: str
    negative_prompt: str | None = None
    reference_image_url: str | None = None
    workflow_role: str | None = None
    provider: str = "mock"
    provider_model: str | None = None
    provider_request_id: str | None = None
    generation_seed: int | None = None
    generated_image_url: str | None = None
    status: WorldCandidateStatus = "pending"
    failure_reason: str | None = None
    resulting_visual_version_id: str | None = None
    created_at: str | None = None
    reviewed_at: str | None = None


class CreateWorldVisualCandidateRequest(BaseModel):
    entity_type: VisualEntityType
    entity_id: str
    name: str
    canonical_state: dict[str, Any] = Field(default_factory=dict)
    generation_type: str = "initial"
    source_visual_version_id: str | None = None
    style: str = "soulsmith_painterly"


class GenerateWorldVisualCandidateRequest(BaseModel):
    provider_type: str | None = None
    seed: int | None = None
