# backend/app/chronicle_paintings.py
"""
SoulSmith Phase 12: Chronicle Paintings + Visual Canon Guardian.

Models for the canonical-memory-to-visual-interpretation pipeline. A Chronicle
Painting is always a generated interpretation of a canonical Memory Object; it
may be regenerated, rejected, superseded, or stylistically reinterpreted without
altering the event it depicts.

Canon rule: CANON -> SCENE SPEC -> IMAGE GENERATION -> VISUAL CANON GUARDIAN
-> PLAYER-VISIBLE CANDIDATE. Never ART -> CANON.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.visual_memory import EquipmentAppearanceModel, StoryMarkModel

# Lifecycle statuses (artistic interpretation, never canon).
PaintingStatus = Literal["candidate", "approved", "rejected", "superseded", "failed"]

# Pipeline stage tracked separately from lifecycle status so a failed Guardian
# review is auditable without conflating "failed artwork" with "failed canon".
GuardianStatus = Literal[
    "pending", "generating", "reviewing", "passed", "retry", "blocked", "failed"
]

PaintingGenerationType = Literal[
    "initial",
    "retry",
    "composition_change",
    "style_change",
    "reference_upgrade",
    "manual_regeneration",
]

GuardianVerdict = Literal["pass", "retry", "block"]
ViolationSeverity = Literal["low", "medium", "high", "critical"]

COMPOSITION_MODES = [
    "intimate",
    "environmental",
    "confrontation",
    "discovery",
    "aftermath",
    "journey",
    "ritual",
    "relic_focus",
    "phenomenon_focus",
    "group_memory",
]

# Canonical appearance strategy when a participant has no usable portrait
# reference. We deliberately prefer non-identifying framing over inventing
# identity-specific details.
IdentityStrategy = Literal[
    "historical_portrait",
    "rear_view",
    "silhouette",
    "distant",
    "environmental",
    "omitted",
    "non_identifying",
]

CHRONICLE_COMPILER_VERSION = "1.0.0"


class ParticipantAppearanceModel(BaseModel):
    """Resolved appearance facts for one memory participant."""

    soul_id: str
    character_name: str
    role_in_event: str
    portrait_version_id: str | None = None
    identity_strategy: IdentityStrategy = "historical_portrait"
    portrait_image_url: str | None = None
    story_marks: list[StoryMarkModel] = Field(default_factory=list)
    equipment: EquipmentAppearanceModel | None = None


class SceneSpecModel(BaseModel):
    """
    Inspectable structured scene specification. Canonical extraction is kept
    separate from artistic phrasing so the Guardian can judge against facts.
    """

    event_title: str
    event_id: str
    location: str
    environment: str
    time_context: str = "The moment the memory was made."
    participants: list[ParticipantAppearanceModel] = Field(default_factory=list)
    story_marks: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    relic_state: str = "No relics involved."
    pose_action: str
    phenomena: list[str] = Field(default_factory=list)
    emotional_tone: str
    composition: str = "environmental"
    must_preserve: list[str] = Field(default_factory=list)
    must_not_invent: list[str] = Field(default_factory=list)
    style: str = (
        "cinematic painterly realism, grounded fantasy, atmospheric storytelling, "
        "tactile environments, natural dramatic lighting, expressive but believable "
        "characters, strong depth, environmental detail, restrained magical phenomena"
    )


class GuardianViolationModel(BaseModel):
    type: str
    severity: ViolationSeverity = "medium"
    description: str
    canonical_expected: str
    observed: str


class GuardianReportModel(BaseModel):
    status: GuardianVerdict
    confidence: float = 0.0
    violations: list[GuardianViolationModel] = Field(default_factory=list)
    correction_instructions: list[str] = Field(default_factory=list)


class ProviderCapabilitiesModel(BaseModel):
    provider: str
    text_to_image: bool = False
    single_reference: bool = False
    multiple_references: bool = False
    identity_conditioning: bool = False
    regional_conditioning: bool = False
    deterministic_seed: bool = False
    aspect_ratio_control: bool = False


class ChroniclePaintingModel(BaseModel):
    painting_id: str
    memory_object_id: str
    source_painting_id: str | None = None
    generation_type: PaintingGenerationType = "initial"
    status: PaintingStatus = "candidate"
    guardian_status: GuardianStatus = "pending"
    compiler_version: str = CHRONICLE_COMPILER_VERSION
    scene_spec: dict[str, Any] = Field(default_factory=dict)
    composition: str = "environmental"
    historical_participant_refs: list[dict[str, Any]] = Field(default_factory=list)
    compiled_prompt: str
    negative_prompt: str | None = None
    provider: str = "mock"
    provider_model: str | None = None
    provider_request_id: str | None = None
    generation_seed: int | None = None
    quarantined_image_url: str | None = None
    image_url: str | None = None
    guardian_report: dict[str, Any] | None = None
    failure_reason: str | None = None
    retry_count: int = 0
    art_direction_profile_id: str | None = None
    art_direction_profile_version_id: str | None = None
    created_at: str | None = None
    reviewed_at: str | None = None
    approved_at: str | None = None


# Request schemas


class CreateChroniclePaintingRequest(BaseModel):
    memory_object_id: str
    generation_type: PaintingGenerationType = "initial"
    source_painting_id: str | None = None
    composition: str | None = None
    style: str | None = None
    art_direction_profile_version_id: str | None = None


class GenerateChroniclePaintingRequest(BaseModel):
    provider_type: str | None = None
    seed: int | None = None


class ApproveChroniclePaintingRequest(BaseModel):
    pass


class RejectChroniclePaintingRequest(BaseModel):
    pass
