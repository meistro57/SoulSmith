# backend/app/world_gallery.py
"""
SoulSmith Phase 15: World Gallery.

A player-facing, consent-safe curation of the approved visual history of
SoulSmith. The Gallery curates approved artifacts; it never promotes rejected,
quarantined, blocked, or unreviewed work, and it never lets style, curation, or
generated artwork rewrite historical truth.

All reads go through consent/publication projection. Private participants are
omitted (never counted) from public projections, and captions/alt text are
derived only from safe known information.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

GalleryArtifactType = Literal[
    "portrait",
    "visual_entity",
    "chronicle_painting",
    "biography_illustration",
]

GalleryMode = Literal[
    "all", "world", "people", "chronicle", "shared", "life", "then_now"
]

CollectionVisibility = Literal["public_canon", "private"]


class GalleryProvenanceModel(BaseModel):
    source_type: str
    source_id: str
    label: str


class GalleryArtifactModel(BaseModel):
    artifact_id: str
    artifact_type: GalleryArtifactType
    image_url: str
    title: str
    caption: str
    alt_text: str
    provenance: list[GalleryProvenanceModel] = Field(default_factory=list)
    art_direction: dict[str, Any] | None = None
    guardian_status: str | None = None
    chronology_label: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    created_at: str | None = None


class GalleryCollectionItemModel(BaseModel):
    item_id: str
    collection_id: str
    artifact_type: GalleryArtifactType
    artifact_ref: str
    position: int = 0
    caption: str = ""
    created_at: str | None = None


class GalleryCollectionModel(BaseModel):
    collection_id: str
    title: str
    description: str = ""
    visibility: CollectionVisibility = "public_canon"
    curator_soul_id: str | None = None
    items: list[GalleryCollectionItemModel] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


# Request schemas


class CreateGalleryCollectionRequest(BaseModel):
    title: str
    description: str = ""
    visibility: CollectionVisibility = "public_canon"
    curator_soul_id: str | None = None


class UpdateGalleryCollectionRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    visibility: CollectionVisibility | None = None


class AddGalleryCollectionItemRequest(BaseModel):
    artifact_type: GalleryArtifactType
    artifact_ref: str
    caption: str = ""
    position: int | None = None


class ReorderGalleryCollectionRequest(BaseModel):
    ordered_item_ids: list[str]


# Consent helpers


def _consent_allows_shared_gallery(soul_id: str) -> bool:
    from app.db import get_or_create_visual_consent_record

    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return bool(consent.get("allow_shared_gallery", True))


def _soul_visible_to(soul_id: str, viewer_soul_id: str | None) -> bool:
    if soul_id == viewer_soul_id:
        return True
    return _consent_allows_shared_gallery(soul_id)


def _memory_owner(memory_object: dict[str, Any]) -> str | None:
    participants = memory_object.get("participants", []) or []
    if not participants:
        return None
    return participants[0].get("soul_id")


def _memory_visible_to(
    memory_object: dict[str, Any], viewer_soul_id: str | None
) -> bool:
    owner = _memory_owner(memory_object)
    if owner is None:
        return False
    if owner == viewer_soul_id:
        return True
    if memory_object.get("privacy_consent_scope") != "public_canon":
        return False
    return _consent_allows_shared_gallery(owner)


def conservative_alt_text(
    artifact_type: str, title: str, caption: str | None = None
) -> str:
    """
    Conservative alt text derived only from safe artifact metadata. It never
    invents visual or canonical details.
    """
    kind = {
        "portrait": "Portrait",
        "visual_entity": "World visual",
        "chronicle_painting": "Chronicle painting",
        "biography_illustration": "Biography illustration",
    }.get(artifact_type, "Artwork")
    suffix = f": {caption}" if caption else ""
    return f"{kind} titled {title}{suffix}"


def _profile_info_for_row(row: dict[str, Any]) -> dict[str, Any] | None:
    profile_id = row.get("art_direction_profile_id")
    version_id = row.get("art_direction_profile_version_id")
    if not profile_id and not version_id:
        return None
    return {
        "profile_id": profile_id,
        "profile_version_id": version_id,
    }


def _portrait_artifacts(viewer_soul_id: str | None) -> list[GalleryArtifactModel]:
    from app.db import list_all_portrait_versions_records

    artifacts: list[GalleryArtifactModel] = []
    for row in list_all_portrait_versions_records():
        soul_id = row["soul_id"]
        if not _soul_visible_to(soul_id, viewer_soul_id):
            continue
        label = row.get("label") or f"v{row.get('version_number')}"
        title = f"{soul_id} — {label}"
        caption = label
        artifacts.append(
            GalleryArtifactModel(
                artifact_id=row["version_id"],
                artifact_type="portrait",
                image_url=row["image_url"],
                title=title,
                caption=caption,
                alt_text=conservative_alt_text("portrait", title, caption),
                provenance=[
                    GalleryProvenanceModel(
                        source_type="portrait_version",
                        source_id=row["version_id"],
                        label=f"Portrait version {row.get('version_number')}",
                    )
                ],
                chronology_label=f"v{row.get('version_number')}",
                entity_id=soul_id,
                entity_type="portrait",
                created_at=row.get("created_at"),
            )
        )
    return artifacts


def _world_artifacts(viewer_soul_id: str | None) -> list[GalleryArtifactModel]:
    from app.db import list_all_visual_entity_versions_records

    artifacts: list[GalleryArtifactModel] = []
    for row in list_all_visual_entity_versions_records():
        entity_type = row["entity_type"]
        label = row.get("label") or f"{entity_type} v{row.get('version_number')}"
        title = f"{entity_type.title()} — {label}"
        artifacts.append(
            GalleryArtifactModel(
                artifact_id=row["version_id"],
                artifact_type="visual_entity",
                image_url=row["image_url"],
                title=title,
                caption=label,
                alt_text=conservative_alt_text("visual_entity", title, label),
                provenance=[
                    GalleryProvenanceModel(
                        source_type="visual_entity_version",
                        source_id=row["version_id"],
                        label=f"{entity_type} version {row.get('version_number')}",
                    )
                ],
                chronology_label=f"v{row.get('version_number')}",
                entity_id=row.get("entity_id"),
                entity_type=entity_type,
                created_at=row.get("created_at"),
            )
        )
    return artifacts


def _painting_artifacts(viewer_soul_id: str | None) -> list[GalleryArtifactModel]:
    from app.db import (
        get_approved_chronicle_paintings_records,
        get_memory_object_record,
    )

    artifacts: list[GalleryArtifactModel] = []
    for row in get_approved_chronicle_paintings_records():
        memory = get_memory_object_record(row["memory_object_id"])
        if not memory or not _memory_visible_to(memory, viewer_soul_id):
            continue
        title = row.get("memory_event_title") or memory.get("event_title") or "Memory"
        caption = memory.get("event_title") or "A remembered event"
        artifacts.append(
            GalleryArtifactModel(
                artifact_id=row["painting_id"],
                artifact_type="chronicle_painting",
                image_url=row["image_url"],
                title=title,
                caption=caption,
                alt_text=conservative_alt_text("chronicle_painting", title, caption),
                provenance=[
                    GalleryProvenanceModel(
                        source_type="chronicle_painting",
                        source_id=row["painting_id"],
                        label=memory.get("event_id", "chronicle event"),
                    )
                ],
                art_direction=_profile_info_for_row(row),
                guardian_status=row.get("guardian_status"),
                entity_id=memory.get("event_id"),
                entity_type="chronicle_event",
                created_at=row.get("created_at"),
            )
        )
    return artifacts


def _shared_artifacts(viewer_soul_id: str | None) -> list[GalleryArtifactModel]:
    from app.db import (
        get_approved_chronicle_paintings_records,
        get_group_memory_by_event_record,
        get_memory_object_record,
    )

    artifacts: list[GalleryArtifactModel] = []
    seen: set[str] = set()
    for row in get_approved_chronicle_paintings_records():
        memory = get_memory_object_record(row["memory_object_id"])
        if not memory or not _memory_visible_to(memory, viewer_soul_id):
            continue
        group = get_group_memory_by_event_record(memory.get("event_id", ""))
        if not group:
            continue
        key = group["group_id"]
        if key in seen:
            continue
        seen.add(key)
        title = group.get("title") or memory.get("event_title") or "A Shared Event"
        artifacts.append(
            GalleryArtifactModel(
                artifact_id=row["painting_id"],
                artifact_type="chronicle_painting",
                image_url=row["image_url"],
                title=title,
                caption=group.get("summary") or "A shared moment.",
                alt_text=conservative_alt_text("chronicle_painting", title),
                provenance=[
                    GalleryProvenanceModel(
                        source_type="group_memory",
                        source_id=group["group_id"],
                        label="Shared event",
                    )
                ],
                art_direction=_profile_info_for_row(row),
                guardian_status=row.get("guardian_status"),
                entity_id=group["event_id"],
                entity_type="group_memory",
                created_at=row.get("created_at"),
            )
        )
    return artifacts


def _life_artifacts(
    soul_id: str, viewer_soul_id: str | None
) -> list[GalleryArtifactModel]:
    from app.biography import source_visible_to
    from app.db import (
        get_chronicle_painting_record,
        get_current_biography_record,
        get_portrait_version_record,
    )

    biography = get_current_biography_record(soul_id)
    if not biography:
        return []

    artifacts: list[GalleryArtifactModel] = []
    seen: set[str] = set()
    for section in biography.get("sections", []):
        for ref in section.get("provenance", []):
            source_type = ref.get("source_type")
            source_id = ref.get("source_id")
            if not source_visible_to(source_type, source_id, viewer_soul_id):
                continue
            image_url: str | None = None
            label = source_id
            if source_type == "chronicle_painting":
                painting = get_chronicle_painting_record(source_id)
                if painting and painting.get("status") == "approved":
                    image_url = painting.get("image_url")
                    label = painting.get("painting_id")
            elif source_type == "portrait_version":
                portrait = get_portrait_version_record(source_id)
                if portrait:
                    image_url = portrait.get("image_url")
                    label = portrait.get("label") or source_id
            if not image_url or image_url in seen:
                continue
            seen.add(image_url)
            title = section.get("title") or "A life"
            artifacts.append(
                GalleryArtifactModel(
                    artifact_id=f"{source_type}_{source_id}",
                    artifact_type="biography_illustration",
                    image_url=image_url,
                    title=title,
                    caption=section.get("title") or "From the Chronicle",
                    alt_text=conservative_alt_text("biography_illustration", title),
                    provenance=[
                        GalleryProvenanceModel(
                            source_type=source_type,
                            source_id=source_id,
                            label=label,
                        )
                    ],
                    entity_id=soul_id,
                    entity_type="biography",
                    created_at=section.get("created_at"),
                )
            )
    return artifacts


def list_gallery_artifacts(
    *,
    viewer_soul_id: str | None,
    mode: GalleryMode = "all",
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[GalleryArtifactModel]:
    """
    Return consent-safe Gallery artifacts for a viewer. Only approved, public,
    consent-eligible work is returned. Rejected/quarantined/blocked candidates
    never appear.
    """
    if mode == "world":
        artifacts = _world_artifacts(viewer_soul_id)
    elif mode == "people":
        artifacts = _portrait_artifacts(viewer_soul_id)
    elif mode == "chronicle":
        artifacts = _painting_artifacts(viewer_soul_id)
    elif mode == "shared":
        artifacts = _shared_artifacts(viewer_soul_id)
    elif mode == "life":
        artifacts = _life_artifacts(entity_id or viewer_soul_id or "", viewer_soul_id)
    elif mode == "then_now":
        artifacts = build_timeline(
            viewer_soul_id=viewer_soul_id,
            entity_type=entity_type or "",
            entity_id=entity_id or "",
        )
    else:
        artifacts = (
            _portrait_artifacts(viewer_soul_id)
            + _world_artifacts(viewer_soul_id)
            + _painting_artifacts(viewer_soul_id)
        )

    if entity_type:
        artifacts = [a for a in artifacts if a.entity_type == entity_type]
    if entity_id:
        artifacts = [a for a in artifacts if a.entity_id == entity_id]
    return artifacts


def build_timeline(
    *,
    viewer_soul_id: str | None,
    entity_type: str,
    entity_id: str,
) -> list[GalleryArtifactModel]:
    """
    Return the immutable historical visual timeline for a person or world entity.
    Superseded historical art remains available here only; the newest version
    never overwrites the older ones.
    """
    if entity_type == "portrait":
        from app.db import get_portrait_versions_records

        records = get_portrait_versions_records(entity_id)
        if not _soul_visible_to(entity_id, viewer_soul_id):
            return []
        return [
            GalleryArtifactModel(
                artifact_id=r["version_id"],
                artifact_type="portrait",
                image_url=r["image_url"],
                title=f"{entity_id} — {r.get('label') or 'portrait'}",
                caption=r.get("label") or "portrait",
                alt_text=conservative_alt_text("portrait", entity_id, r.get("label")),
                provenance=[
                    GalleryProvenanceModel(
                        source_type="portrait_version",
                        source_id=r["version_id"],
                        label=f"Portrait version {r.get('version_number')}",
                    )
                ],
                chronology_label=f"v{r.get('version_number')}",
                entity_id=entity_id,
                entity_type="portrait",
                created_at=r.get("created_at"),
            )
            for r in records
        ]

    from app.db import get_visual_entity_versions_records

    records = get_visual_entity_versions_records(entity_type, entity_id)
    return [
        GalleryArtifactModel(
            artifact_id=r["version_id"],
            artifact_type="visual_entity",
            image_url=r["image_url"],
            title=f"{entity_type.title()} — {r.get('label') or 'visual'}",
            caption=r.get("label") or entity_type,
            alt_text=conservative_alt_text("visual_entity", entity_type),
            provenance=[
                GalleryProvenanceModel(
                    source_type="visual_entity_version",
                    source_id=r["version_id"],
                    label=f"{entity_type} version {r.get('version_number')}",
                )
            ],
            chronology_label=f"v{r.get('version_number')}",
            entity_id=entity_id,
            entity_type=entity_type,
            created_at=r.get("created_at"),
        )
        for r in records
    ]
