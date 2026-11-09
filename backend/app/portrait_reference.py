# backend/app/portrait_reference.py
"""
Resolution of canonical source portraits for continuity generation.

When a portrait candidate references a prior ``PortraitVersion`` (via
``source_portrait_version_id``), this module verifies the version exists, belongs
to the requesting soul, and has an image, then returns it. It never silently
substitutes a newer portrait for the explicitly requested one.
"""

from __future__ import annotations

from typing import Any

from app.db import get_portrait_version_record


class SourcePortraitError(ValueError):
    """Raised when a requested source portrait cannot be used."""


def resolve_source_portrait(
    soul_id: str, source_portrait_version_id: str | None
) -> dict[str, Any] | None:
    """
    Resolve and validate a source portrait version.

    Returns ``None`` when no source version was requested, or the version dict
    (including ``image_url``) when the version is a valid canonical portrait owned
    by ``soul_id``.
    """
    if not source_portrait_version_id:
        return None

    version = get_portrait_version_record(source_portrait_version_id)
    if not version:
        raise SourcePortraitError(
            f"Source portrait version '{source_portrait_version_id}' not found"
        )
    if version.get("soul_id") != soul_id:
        raise SourcePortraitError(
            f"Source portrait '{source_portrait_version_id}' does not belong to soul '{soul_id}'"
        )
    if not version.get("image_url"):
        raise SourcePortraitError(
            f"Source portrait '{source_portrait_version_id}' has no image_url"
        )
    return version
