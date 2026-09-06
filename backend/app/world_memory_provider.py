# backend/app/world_memory_provider.py
"""
Cultural-artifact provider abstraction for World Memory.

Providers receive the deterministic, consent-filtered ``WorldMemorySpec`` and
return a structured ``GeneratedWorldMemoryArtifact`` whose claims are backed by
canonical facts or explicitly declared deviations. The deterministic mock
requires no external AI and is the default. A real LLM provider would be added
behind this same interface.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from app.world_memory import (
    GeneratedWorldMemoryArtifact,
    WorldMemorySpec,
)


class WorldMemoryArtifactProvider(ABC):
    @abstractmethod
    def generate(self, spec: WorldMemorySpec) -> GeneratedWorldMemoryArtifact:
        """Render the structured spec into a provenance-carrying artifact."""


class MockWorldMemoryArtifactProvider(WorldMemoryArtifactProvider):
    """Deterministic mock cultural-memory generator; offline and stable."""

    PROVIDER = "mock"
    PROVIDER_MODEL = "soulsmith-mock-world-memory-v1"

    def generate(self, spec: WorldMemorySpec) -> GeneratedWorldMemoryArtifact:
        title = _derive_title(spec)
        claims = list(spec.allowed_claims)
        # Drift claims are taken only from declared deviations, never invented.
        for deviation in spec.declared_deviations:
            if deviation.legend_claims and deviation.legend_claims not in claims:
                claims.append(deviation.legend_claims)
        narrative = _compose_narrative(spec, claims)
        return GeneratedWorldMemoryArtifact(
            title=title,
            narrative=narrative,
            claims=claims,
            perspective=spec.perspective,
            source_refs=list(spec.source_refs),
            declared_deviations=list(spec.declared_deviations),
        )


def _derive_title(spec: WorldMemorySpec) -> str:
    subject = spec.subject_entity_id or "the unnamed"
    if spec.memory_form == "legend":
        return f"The Legend of {subject}"
    if spec.memory_form == "song_ballad":
        return f"The Ballad of {subject}"
    if spec.memory_form == "monument_statue":
        return f"The Monument to {subject}"
    if spec.memory_form == "festival_tradition":
        return f"The Festival of {subject}"
    if spec.memory_form == "place_name_inheritance":
        return f"The Name of {subject}"
    if spec.memory_form == "relic_legend":
        return f"The Tale of the {subject}"
    if spec.memory_form == "forgotten_fragment":
        return f"Fragments Concerning {subject}"
    return f"The Account of {subject}"


def _compose_narrative(spec: WorldMemorySpec, claims: list[str]) -> str:
    culture = f"Among the {spec.culture}, " if spec.culture else ""
    era = f" in the {spec.era_context}" if spec.era_context else ""
    if not claims:
        body = (
            "the people remember little, and what remains is more silence than story."
        )
    elif spec.interpretation_type == "faithful":
        body = "it is recorded that " + "; ".join(claims) + "."
    elif spec.interpretation_type == "mythologized":
        body = "the telling has grown: " + "; ".join(claims) + "."
    elif spec.interpretation_type == "exaggerated":
        body = "the telling exaggerates: " + "; ".join(claims) + "."
    elif spec.interpretation_type == "contradictory":
        body = "the accounts conflict: " + "; ".join(claims) + "."
    elif spec.interpretation_type == "fragmented":
        body = "only fragments survive: " + "; ".join(claims) + "."
    else:
        body = "the story is told as: " + "; ".join(claims) + "."
    return f"{culture}this is how the world remembers it{era}: {body}"


def get_world_memory_provider(
    provider_type: str | None = None,
) -> WorldMemoryArtifactProvider:
    selected = provider_type or os.environ.get(
        "SOULSMITH_WORLD_MEMORY_PROVIDER", "mock"
    )
    if selected == "mock":
        return MockWorldMemoryArtifactProvider()
    # Only the deterministic mock is wired in v1; unknown providers fall back to
    # the mock so provider failure can never damage Chronicle data.
    return MockWorldMemoryArtifactProvider()
