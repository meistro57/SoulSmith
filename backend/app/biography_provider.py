# backend/app/biography_provider.py
"""
Narrative provider abstraction for Living Biography prose.

Providers receive the deterministic, consent-filtered ``BiographySpec`` and
return structured ``BiographyNarrativeSection`` items with provenance
references. The deterministic mock requires no internet or external AI and is
the default. A real LLM provider would be added behind this same interface.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from app.biography import (
    BiographyNarrativeSection,
    BiographySectionSpec,
    BiographySpec,
)


class BiographyNarrativeProvider(ABC):
    @abstractmethod
    def generate(self, spec: BiographySpec) -> list[BiographyNarrativeSection]:
        """Render the structured spec into provenance-carrying narrative sections."""


class MockBiographyNarrativeProvider(BiographyNarrativeProvider):
    """Deterministic mock prose generator; stable for tests and offline use."""

    PROVIDER = "mock"
    PROVIDER_MODEL = "soulsmith-mock-biography-v1"

    def generate(self, spec: BiographySpec) -> list[BiographyNarrativeSection]:
        sections: list[BiographyNarrativeSection] = []
        for section in spec.sections:
            sections.append(_render_section(section))
        return sections


def _render_section(section: BiographySectionSpec) -> BiographyNarrativeSection:
    facts = [f for f in section.facts if f]
    narrative = _compose_narrative(section, facts)
    return BiographyNarrativeSection(
        section_type=section.section_type,
        title=section.title,
        narrative=narrative,
        claim_kind=section.claim_kind,
        perspective_of=section.perspective_of,
        visual_reference=section.visual_reference,
        provenance=list(section.source_refs),
    )


def _compose_narrative(section: BiographySectionSpec, facts: list[str]) -> str:
    connective = (
        f"Across these memories, the Chronicle shows the {section.title.lower()}."
    )
    if not facts:
        return connective

    joined = "; ".join(facts)
    if section.claim_kind == "participant_perspective" and section.perspective_of:
        return f"From {section.perspective_of}'s recollection: {joined}."
    if section.claim_kind == "shared_perspective":
        return f"Those who were present remember: {joined}."
    if section.claim_kind == "unresolved":
        return f"This remains unresolved in the Chronicle: {joined}."
    if section.claim_kind == "inferred_theme":
        return f"The Chronicle repeatedly shows a theme, not a new fact: {joined}."
    return f"{connective} {joined}."


def get_biography_provider(
    provider_type: str | None = None,
) -> BiographyNarrativeProvider:
    selected = provider_type or os.environ.get("SOULSMITH_BIOGRAPHY_PROVIDER", "mock")
    if selected == "mock":
        return MockBiographyNarrativeProvider()
    # Only the deterministic mock is wired in v1; unknown providers fall back to
    # the mock so provider failure can never damage Chronicle data.
    return MockBiographyNarrativeProvider()
