# backend/app/painting_reference.py
"""
Historical participant appearance resolution for Chronicle Paintings.

When painting a historical memory we use the appearance that belonged to that
memory. If the Memory Object references a historical ``PortraitVersion`` we use
that exact version and never substitute the participant's newest portrait. When
canonical appearance is unavailable we do not invent identity details; we select
a non-identifying framing strategy and record the decision in generation
metadata.
"""

from __future__ import annotations

from app.chronicle_paintings import ParticipantAppearanceModel
from app.db import get_portrait_version_record
from app.visual_memory import (
    EquipmentAppearanceModel,
    MemoryObjectModel,
    StoryMarkModel,
)


class ParticipantResolutionError(ValueError):
    """Raised when a participant's historical portrait reference is unusable."""


def resolve_historical_participants(
    memory_object: MemoryObjectModel,
) -> list[ParticipantAppearanceModel]:
    """
    Resolve each Memory Object participant to their exact historical appearance.

    - An explicit ``portrait_version_id`` must resolve to a real, soul-owned,
      imaged portrait version. Mismatched or missing versions raise (never
      silently fall back to the newest portrait).
    - When no portrait reference is available, we emit a non-identifying
      strategy and deliberately omit identity-specific details.
    """
    resolved: list[ParticipantAppearanceModel] = []
    for participant in memory_object.participants:
        portrait_version_id = participant.portrait_version_id or None
        if portrait_version_id:
            version = get_portrait_version_record(portrait_version_id)
            if not version:
                raise ParticipantResolutionError(
                    f"Participant '{participant.soul_id}' references unknown "
                    f"portrait version '{portrait_version_id}'"
                )
            if version.get("soul_id") != participant.soul_id:
                raise ParticipantResolutionError(
                    f"Portrait version '{portrait_version_id}' does not belong to "
                    f"soul '{participant.soul_id}'"
                )
            if not version.get("image_url"):
                raise ParticipantResolutionError(
                    f"Portrait version '{portrait_version_id}' has no image"
                )

            story_marks = [
                StoryMarkModel(**m) for m in (version.get("story_marks_snapshot") or [])
            ]
            equipment = (
                EquipmentAppearanceModel(**version["equipment_snapshot"])
                if version.get("equipment_snapshot")
                else None
            )
            resolved.append(
                ParticipantAppearanceModel(
                    soul_id=participant.soul_id,
                    character_name=participant.character_name,
                    role_in_event=participant.role_in_event,
                    portrait_version_id=portrait_version_id,
                    identity_strategy="historical_portrait",
                    portrait_image_url=version["image_url"],
                    story_marks=story_marks,
                    equipment=equipment,
                )
            )
        else:
            # No canonical appearance: never invent. Record a non-identifying
            # strategy so the compiler and Guardian both know identity was omitted.
            resolved.append(
                ParticipantAppearanceModel(
                    soul_id=participant.soul_id,
                    character_name=participant.character_name,
                    role_in_event=participant.role_in_event,
                    portrait_version_id=None,
                    identity_strategy="silhouette",
                    portrait_image_url=None,
                    story_marks=[],
                    equipment=None,
                )
            )
    return resolved


def primary_reference_image(
    participants: list[ParticipantAppearanceModel],
) -> str | None:
    """
    Return the single participant reference image when exactly one participant
    has a historical portrait. Multiple distinct references cannot be preserved
    by the v1 img2img workflow, so this returns ``None`` for multi-identity
    scenes (the caller degrades honestly instead of pretending).
    """
    imaged = [p for p in participants if p.portrait_image_url]
    if len(imaged) == 1:
        return imaged[0].portrait_image_url
    return None
