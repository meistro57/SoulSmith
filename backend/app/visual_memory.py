# backend/app/visual_memory.py
"""
SoulSmith Phase 9: Visual Identity Foundation & Chronicle Memory Objects.
Structured character identity, provenance-backed story marks, portrait timeline snapshots, and Memory Object compilation.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

VisibilityLevel = Literal["prominent", "subtle", "hidden_under_armor"]
MarkStatus = Literal["permanent", "fading", "magically_sealed"]
VisualGenStatus = Literal["pending", "compiled", "painting_approved", "rejected"]


class AvatarIdentityModel(BaseModel):
    soul_id: str
    face: str = "Defined features, sharp jawline, observant expression"
    hair: str = "Dark raven hair worn tied back"
    body: str = "Athletic, enduring build worn by travel"
    species: str = "Human Aspect"
    eyes: str = "Deep amber eyes reflecting starlight"


class StoryMarkModel(BaseModel):
    id: str
    soul_id: str
    mark_type: str  # scar, burn_mark, broken_horn, blessed_tattoo, gray_hair, missing_finger, etc.
    location: str   # left_cheek, right_forearm, forehead, chest, etc.
    origin_event_id: str
    acquired_at: str
    visibility: VisibilityLevel = "prominent"
    status: MarkStatus = "permanent"


class EquipmentAppearanceModel(BaseModel):
    soul_id: str
    armor: str = "Weathered iron pauldrons and salt-crusted leather doublet"
    clothing: str = "Ash-colored travel cloak with silver thread embroidery"
    weapons: List[str] = Field(default_factory=lambda: ["Seer's Starlight Blade", "Etched Runic Dagger"])
    relics: List[str] = Field(default_factory=lambda: ["Dormant Salt Bell"])
    backpacks_cloaks: str = "Heavy wool cloak with raven brooch"


class PortraitVersionModel(BaseModel):
    version_id: str
    soul_id: str
    version_number: int
    label: str
    image_url: str
    story_marks_snapshot: List[StoryMarkModel] = Field(default_factory=list)
    equipment_snapshot: Optional[EquipmentAppearanceModel] = None
    created_at: Optional[str] = None


class ConsentSettingsModel(BaseModel):
    soul_id: str
    allow_shared_gallery: bool = True
    allow_character_tagging: bool = True
    allow_real_person_tagging: bool = False
    real_person_photo_url: Optional[str] = None
    real_person_display_name: Optional[str] = None


class ParticipantRefModel(BaseModel):
    soul_id: str
    character_name: str
    portrait_version_id: str
    role_in_event: str
    real_person_tag_opt_in: bool = False


class MemoryObjectModel(BaseModel):
    id: str
    event_id: str
    event_title: str
    participants: List[ParticipantRefModel] = Field(default_factory=list)
    location_environment: str
    relics_involved: List[str] = Field(default_factory=list)
    emotional_tone: str
    action_composition: str
    lasting_consequence: str
    privacy_consent_scope: str = "public_canon"
    visual_generation_status: VisualGenStatus = "compiled"
    painting_image_url: Optional[str] = None
    created_at: Optional[str] = None


# Request Schemas
class CreateAvatarIdentityRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    face: str = "Defined features, sharp jawline, observant expression"
    hair: str = "Dark raven hair worn tied back"
    body: str = "Athletic build worn by travel"
    species: str = "Human Aspect"
    eyes: str = "Deep amber eyes reflecting starlight"


class AddStoryMarkRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    mark_type: str = "scar"
    location: str = "left_cheek"
    origin_event_id: str
    acquired_at: str = "Year 3, Frostwane"
    visibility: VisibilityLevel = "prominent"
    status: MarkStatus = "permanent"


class CreatePortraitVersionRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    label: str
    image_url: str = "/assets/portraits/kaelen_v1.png"


class CompileMemoryObjectRequest(BaseModel):
    event_id: str
    event_title: str
    participants: List[ParticipantRefModel]
    location_environment: str
    relics_involved: List[str] = Field(default_factory=list)
    emotional_tone: str
    action_composition: str
    lasting_consequence: str
    privacy_consent_scope: str = "public_canon"
