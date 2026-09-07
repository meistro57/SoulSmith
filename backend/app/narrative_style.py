# backend/app/narrative_style.py
"""
SoulSmith Phase 18: Soulkeeper narrative style layer.

The style layer controls *how* an authorized scene is told, never *what* is
true. Style settings must never add information unavailable in the structured
``NarrativeContext``. They are resolved from player preferences and deployment
configuration into an inspectable ``NarrativeStyle`` before a provider runs.

Curiosity before explanation. Evidence before interpretation. Agency without
doctrine.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ProseDensity = Literal["sparse", "moderate", "rich"]
DialogueFrequency = Literal["none", "low", "moderate", "high"]
Tone = Literal["lyrical", "direct", "mythic"]
MysteryLevel = Literal["low", "moderate", "high"]
SensoryRichness = Literal["minimal", "moderate", "rich"]
SceneLength = Literal["short", "medium", "long"]
SoulkeeperPresence = Literal["minimal", "moderate", "prominent"]


class NarrativeStyle(BaseModel):
    """Configurable, fact-free presentation settings."""

    name: str = "soulkeeper_default"
    prose_density: ProseDensity = "moderate"
    dialogue_frequency: DialogueFrequency = "moderate"
    tone: Tone = "lyrical"
    mystery_level: MysteryLevel = "moderate"
    humor_allowance: bool = False
    sensory_richness: SensoryRichness = "moderate"
    scene_length: SceneLength = "medium"
    soulkeeper_presence: SoulkeeperPresence = "moderate"
    plain_language: bool = False
    allow_uncertainty: bool = True


SOULKEEPER_DEFAULT_STYLE = NarrativeStyle()


def style_from_dict(data: dict | None) -> NarrativeStyle:
    """Merge a partial style dict over the default. Unknown keys are ignored."""
    base = SOULKEEPER_DEFAULT_STYLE.model_dump()
    if data:
        base.update({k: v for k, v in data.items() if k in base})
    return NarrativeStyle(**base)


def resolve_style(
    preferences: dict | None = None,
    style_override: dict | None = None,
) -> NarrativeStyle:
    """Resolve an effective style. Player preferences map narrative intensity
    to plain-language/density defaults; an explicit override wins."""
    data: dict = {}
    intensity = (preferences or {}).get("narrative_intensity")
    if intensity == "gentle":
        data.update(
            plain_language=True, prose_density="sparse", sensory_richness="minimal"
        )
    elif intensity == "deep_mythic":
        data.update(tone="mythic", sensory_richness="rich", prose_density="rich")
    elif intensity == "unfiltered":
        data.update(mystery_level="low", allow_uncertainty=False)
    if style_override:
        data.update(style_override)
    return style_from_dict(data or None)
