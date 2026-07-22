# backend/app/reflection.py
"""
SoulSmith Phase 8: Reflection & Accessibility Engine
Optional end-of-session reflection prompts, private notes controls, intensity settings, and accessibility preferences.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel

NarrativeIntensity = Literal["gentle", "balanced", "deep_mythic", "unfiltered"]
SpiritualFraming = Literal["secular_mythology", "opt_in_spiritual"]


class PlayerPreferencesModel(BaseModel):
    soul_id: str
    narrative_intensity: NarrativeIntensity = "balanced"
    spiritual_framing: SpiritualFraming = "secular_mythology"
    reduced_motion: bool = False
    high_contrast: bool = False
    allow_ai_indexing_default: bool = False
    updated_at: Optional[str] = None


class ReflectionSessionModel(BaseModel):
    id: str
    soul_id: str
    prompt_question: str
    player_reflection: str
    share_with_ai: bool = False
    created_at: Optional[str] = None


class PrivateNoteModel(BaseModel):
    id: str
    soul_id: str
    title: str
    content: str
    allow_ai_indexing: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateReflectionRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    prompt_question: str
    player_reflection: str
    share_with_ai: bool = False


class CreatePrivateNoteRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    title: str
    content: str
    allow_ai_indexing: bool = False


class UpdatePreferencesRequest(BaseModel):
    soul_id: str = "Kaelen the Star-Watcher"
    narrative_intensity: NarrativeIntensity = "balanced"
    spiritual_framing: SpiritualFraming = "secular_mythology"
    reduced_motion: bool = False
    high_contrast: bool = False
    allow_ai_indexing_default: bool = False
