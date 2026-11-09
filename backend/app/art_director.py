# backend/app/art_director.py
"""
SoulSmith Phase 15: Art Director.

> THE ART DIRECTOR CONTROLS INTERPRETATION. IT DOES NOT CONTROL CANON.

Persistent, versioned Art Direction Profiles describe *how* approved canon may be
visually interpreted. A profile stores stylistic treatment (medium, palette,
lighting, atmosphere, material, framing, composition, per-artifact treatments,
negative guidance, provider hints, and accessibility notes) and never stores
canonical character or world facts.

The compiler keeps canonical requirements and stylistic requirements in separate
fields so they cannot collapse into indistinguishable prompt prose. Resolution is
a small deterministic hierarchy:

    World Art Direction -> artifact-type treatment -> optional scene/collection override
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.chronicle_paintings import ProviderCapabilitiesModel

ProfileStatus = Literal["draft", "current", "superseded", "archived"]

ArtifactType = Literal[
    "portrait",
    "location",
    "relic",
    "phenomenon",
    "chronicle_painting",
]

_ARTIFACT_TREATMENT_FIELD: dict[str, str] = {
    "portrait": "portrait_treatment",
    "location": "environment_treatment",
    "relic": "relic_treatment",
    "phenomenon": "phenomenon_treatment",
    "chronicle_painting": "chronicle_treatment",
}


class ArtDirectionProfileModel(BaseModel):
    """Stable profile identity plus a pointer to its current version."""

    profile_id: str
    name: str
    description: str = ""
    status: ProfileStatus = "draft"
    current_version_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ArtDirectionProfileVersionModel(BaseModel):
    """
    An immutable snapshot of stylistic treatment. Contains no canonical facts.
    """

    version_id: str
    profile_id: str
    version_number: int
    medium_style: str = ""
    palette_guidance: str = ""
    lighting_guidance: str = ""
    atmosphere: str = ""
    texture_material: str = ""
    camera_framing: str = ""
    composition_guidance: str = ""
    portrait_treatment: str = ""
    environment_treatment: str = ""
    relic_treatment: str = ""
    phenomenon_treatment: str = ""
    chronicle_treatment: str = ""
    negative_guidance: str = ""
    provider_hints: dict[str, Any] = Field(default_factory=dict)
    accessibility_notes: str = ""
    created_at: str | None = None


class ArtDirectionProfileFullModel(BaseModel):
    profile: ArtDirectionProfileModel
    version: ArtDirectionProfileVersionModel


# Request schemas


class CreateArtDirectionProfileRequest(BaseModel):
    name: str
    description: str = ""
    medium_style: str = ""
    palette_guidance: str = ""
    lighting_guidance: str = ""
    atmosphere: str = ""
    texture_material: str = ""
    camera_framing: str = ""
    composition_guidance: str = ""
    portrait_treatment: str = ""
    environment_treatment: str = ""
    relic_treatment: str = ""
    phenomenon_treatment: str = ""
    chronicle_treatment: str = ""
    negative_guidance: str = ""
    provider_hints: dict[str, Any] = Field(default_factory=dict)
    accessibility_notes: str = ""


class UpdateArtDirectionProfileRequest(CreateArtDirectionProfileRequest):
    """Updating always creates a new immutable version rather than mutating."""


class ResolveArtDirectionRequest(BaseModel):
    profile_version_id: str
    artifact_type: ArtifactType
    override: dict[str, str] = Field(default_factory=dict)


class CompileArtDirectionSpecRequest(BaseModel):
    profile_version_id: str
    artifact_type: ArtifactType
    canonical: dict[str, Any] = Field(default_factory=dict)
    historical_references: list[dict[str, Any]] = Field(default_factory=list)
    composition_intent: str = ""
    accessibility: list[str] = Field(default_factory=list)
    override: dict[str, str] = Field(default_factory=dict)


# Resolution


class ResolvedArtDirectionModel(BaseModel):
    """The deterministic result of resolving profile + artifact type + override."""

    profile_id: str
    version_id: str
    artifact_type: ArtifactType
    medium_style: str
    palette_guidance: str
    lighting_guidance: str
    atmosphere: str
    texture_material: str
    camera_framing: str
    composition_guidance: str
    treatment: str
    negative_guidance: str
    provider_hints: dict[str, Any] = Field(default_factory=dict)
    accessibility_notes: str = ""
    override_applied: dict[str, str] = Field(default_factory=dict)


def resolve_art_direction(
    profile_version: ArtDirectionProfileVersionModel,
    artifact_type: ArtifactType,
    override: dict[str, str] | None = None,
) -> ResolvedArtDirectionModel:
    """
    Resolve a profile version into the treatment for a specific artifact type.

    Base world-level style fields are read from the profile version. The
    artifact-type treatment field is then applied as a refinement, and an
    optional scene/collection override may change presentation only (never
    canonical facts). Resolution is deterministic and inspectable.
    """
    override = override or {}
    treatment_field = _ARTIFACT_TREATMENT_FIELD.get(
        artifact_type, "chronicle_treatment"
    )
    base_treatment = getattr(profile_version, treatment_field, "")

    def _pick(field: str, base: str) -> str:
        return override.get(field, base)

    return ResolvedArtDirectionModel(
        profile_id=profile_version.profile_id,
        version_id=profile_version.version_id,
        artifact_type=artifact_type,
        medium_style=_pick("medium_style", profile_version.medium_style),
        palette_guidance=_pick("palette_guidance", profile_version.palette_guidance),
        lighting_guidance=_pick("lighting_guidance", profile_version.lighting_guidance),
        atmosphere=_pick("atmosphere", profile_version.atmosphere),
        texture_material=_pick("texture_material", profile_version.texture_material),
        camera_framing=_pick("camera_framing", profile_version.camera_framing),
        composition_guidance=_pick(
            "composition_guidance", profile_version.composition_guidance
        ),
        treatment=_pick("treatment", base_treatment),
        negative_guidance=_pick("negative_guidance", profile_version.negative_guidance),
        provider_hints=dict(profile_version.provider_hints),
        accessibility_notes=_pick(
            "accessibility_notes", profile_version.accessibility_notes
        ),
        override_applied=dict(override),
    )


# Provider capability awareness


def capability_limitations(
    capabilities: ProviderCapabilitiesModel,
    *,
    reference_count: int = 0,
    requires_identity: bool = False,
) -> list[str]:
    """
    Return honest limitations implied by provider capabilities. Never pretend
    unsupported capabilities exist.
    """
    limitations: list[str] = []
    if requires_identity and not capabilities.identity_conditioning:
        limitations.append(
            "selected provider cannot condition on identity; degrade to textual "
            "historical appearance or non-identifying framing"
        )
    if reference_count > 1 and not capabilities.multiple_references:
        limitations.append(
            "multiple historical references are unsupported by this provider; "
            "provide a single reference or degrade to textual appearance"
        )
    if reference_count == 1 and not capabilities.single_reference:
        limitations.append(
            "single reference is unsupported by this provider; degrade to "
            "text-to-image with textual appearance"
        )
    return limitations


# Art Direction Spec compiler


class ArtDirectionSpecModel(BaseModel):
    """Inspectable spec separating canonical and stylistic requirements."""

    artifact_type: str
    profile_id: str
    profile_version_id: str
    canonical: dict[str, Any] = Field(default_factory=dict)
    historical_references: list[dict[str, Any]] = Field(default_factory=list)
    style: ResolvedArtDirectionModel
    provider_capabilities: dict[str, Any] = Field(default_factory=dict)
    composition_intent: str = ""
    accessibility: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    provider_prompt: str = ""


def compile_art_direction_spec(
    *,
    artifact_type: ArtifactType,
    profile_version: ArtDirectionProfileVersionModel,
    canonical: dict[str, Any],
    historical_references: list[dict[str, Any]] | None = None,
    provider_capabilities: ProviderCapabilitiesModel | None = None,
    composition_intent: str = "",
    accessibility: list[str] | None = None,
    override: dict[str, str] | None = None,
) -> ArtDirectionSpecModel:
    """
    Combine canonical spec, historical references, artifact type, selected
    profile/version, provider capabilities, composition intent, and accessibility
    constraints into an inspectable structured Art Direction Spec plus a
    provider-facing prompt. Canonical and stylistic requirements stay separate.
    """
    historical_references = historical_references or []
    accessibility = accessibility or []
    capabilities = provider_capabilities or ProviderCapabilitiesModel(
        provider="unknown"
    )

    resolved = resolve_art_direction(profile_version, artifact_type, override)

    requires_identity = bool(historical_references) or artifact_type == "portrait"
    limitations = capability_limitations(
        capabilities,
        reference_count=len(historical_references),
        requires_identity=requires_identity,
    )

    canonical_text = _format_canonical(canonical)
    references_text = (
        "; ".join(_format_reference(ref) for ref in historical_references)
        if historical_references
        else "None recorded."
    )
    style_lines = _format_style(resolved)
    accessibility_text = "; ".join(accessibility) or resolved.accessibility_notes
    limitations_text = "; ".join(limitations) or "None."

    provider_prompt = (
        f"[CANONICAL] {canonical_text} "
        f"[HISTORICAL REFERENCES] {references_text} "
        f"[ART DIRECTION] {style_lines} "
        f"[COMPOSITION] {composition_intent or resolved.composition_guidance} "
        f"[ACCESSIBILITY] {accessibility_text} "
        f"[LIMITATIONS] {limitations_text}"
    )

    return ArtDirectionSpecModel(
        artifact_type=artifact_type,
        profile_id=resolved.profile_id,
        profile_version_id=resolved.version_id,
        canonical=canonical,
        historical_references=historical_references,
        style=resolved,
        provider_capabilities=capabilities.model_dump(),
        composition_intent=composition_intent or resolved.composition_guidance,
        accessibility=list(accessibility),
        limitations=limitations,
        provider_prompt=provider_prompt,
    )


def apply_art_direction_to_prompt(
    compiled_prompt: str, resolved: ResolvedArtDirectionModel
) -> str:
    """Append an explicit, sectioned art-direction block to an existing prompt."""
    style_lines = _format_style(resolved)
    return f"{compiled_prompt} [ART DIRECTION] {style_lines}"


def _format_style(resolved: ResolvedArtDirectionModel) -> str:
    parts = [
        f"Medium/style: {resolved.medium_style}",
        f"Palette: {resolved.palette_guidance}",
        f"Lighting: {resolved.lighting_guidance}",
        f"Atmosphere: {resolved.atmosphere}",
        f"Texture/material: {resolved.texture_material}",
        f"Camera/framing: {resolved.camera_framing}",
        f"Composition: {resolved.composition_guidance}",
        f"{resolved.artifact_type.replace('_', ' ')} treatment: {resolved.treatment}",
    ]
    if resolved.negative_guidance:
        parts.append(f"Avoid: {resolved.negative_guidance}")
    return "; ".join(p for p in parts if p.split(": ", 1)[-1])


def _format_canonical(canonical: dict[str, Any]) -> str:
    if not canonical:
        return "No canonical specification provided."
    return "; ".join(f"{k}: {_fmt(v)}" for k, v in sorted(canonical.items()))


def _format_reference(ref: dict[str, Any]) -> str:
    if not ref:
        return ""
    label = (
        ref.get("label")
        or ref.get("portrait_version_id")
        or ref.get("version_id")
        or ref.get("source_id")
        or "reference"
    )
    return f"{ref.get('artifact_type', 'reference')} {label}"


def _fmt(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)
