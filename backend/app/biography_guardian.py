# backend/app/biography_guardian.py
"""
Biography Guardian: deterministic validation of generated biography output.

This is not the Visual Canon Guardian. It validates narrative claims against the
structured, consent-filtered source/provenance set before a draft may become
player-visible or current. Only a PASS allows a draft to be approved.

Deterministic structural validation is mandatory and runs without an LLM.
Semantic claim review would be added behind a provider abstraction; the mock
covers PASS/FAIL behavior.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from app.biography import (
    BiographyNarrativeSection,
    BiographySpec,
    GuardianReportModel,
)

# Narrow calendar patterns so canonical relative phrasing (e.g. "Year 3") is
# never flagged; these match invented absolute dates/ages/durations only.
_INVENTED_DATE_PATTERNS = [
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
    ),
    re.compile(r"\b\d{4}\s*(?:BCE|CE|AD|BC)\b"),
    re.compile(r"\baged\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+years?\s+old\b", re.IGNORECASE),
]


class BiographyGuardian(ABC):
    @abstractmethod
    def validate(
        self,
        *,
        sections: list[BiographyNarrativeSection],
        spec: BiographySpec,
    ) -> GuardianReportModel:
        """Validate generated narrative sections against their canonical sources."""


class MockBiographyGuardian(BiographyGuardian):
    """
    Deterministic mock Guardian.

    - Every provenance source must exist in the spec's allowed source set.
    - Factual sections require provenance (no unsupported factual claims).
    - Perspective passages must not be presented as objective fact.
    - Narrative must not invent absolute dates/ages/durations.
    - Any referenced Chronicle Painting must be approved before it may illustrate.
    """

    def validate(
        self,
        *,
        sections: list[BiographyNarrativeSection],
        spec: BiographySpec,
    ) -> GuardianReportModel:
        allowed_sources = _collect_allowed_sources(spec)
        violations: list[dict[str, Any]] = []
        instructions: list[str] = []

        for section in sections:
            for ref in section.provenance:
                key = f"{ref.source_type}:{ref.source_id}"
                if key not in allowed_sources:
                    violations.append(
                        _violation(
                            "unknown_source",
                            "critical",
                            f"Provenance references an unknown or out-of-scope source '{key}'.",
                            "a source present in the structured specification",
                            key,
                        )
                    )
                if (
                    ref.source_type == "chronicle_painting"
                    and not _painting_is_approved(ref.source_id)
                ):
                    violations.append(
                        _violation(
                            "unapproved_visual_reference",
                            "critical",
                            f"Chronicle painting '{ref.source_id}' is not approved and cannot illustrate canon.",
                            "an approved painting",
                            ref.source_id,
                        )
                    )

            if section.claim_kind == "canonical_fact" and not section.provenance:
                violations.append(
                    _violation(
                        "unsupported_factual_claim",
                        "critical",
                        f"Section '{section.title}' asserts a canonical fact without any source.",
                        "at least one canonical provenance reference",
                        "no provenance",
                    )
                )

            if section.perspective_of and section.claim_kind in (
                "canonical_fact",
                "shared_perspective",
            ):
                violations.append(
                    _violation(
                        "perspective_presented_as_objective_fact",
                        "critical",
                        f"Section '{section.title}' records a participant perspective as objective fact.",
                        "perspective marked with claim_kind participant_perspective",
                        f"claim_kind {section.claim_kind} with perspective_of {section.perspective_of}",
                    )
                )

            for pattern in _INVENTED_DATE_PATTERNS:
                if pattern.search(section.narrative):
                    violations.append(
                        _violation(
                            "invented_date",
                            "critical",
                            f"Section '{section.title}' invents an absolute date, age, or duration.",
                            "relative chronology only",
                            pattern.pattern,
                        )
                    )
                    break

        if violations:
            instructions = [
                "Recompile the biography from canonical sources only.",
                "Ensure every factual claim carries a valid provenance reference.",
                "Present participant recollections as perspective, never as objective fact.",
            ]
            return GuardianReportModel(
                status="fail",
                confidence=0.9,
                violations=violations,
                correction_instructions=instructions,
            )

        return GuardianReportModel(
            status="pass",
            confidence=0.99,
            violations=[],
            correction_instructions=[],
        )


def _violation(
    vtype: str, severity: str, description: str, expected: str, observed: str
) -> dict[str, Any]:
    return {
        "type": vtype,
        "severity": severity,
        "description": description,
        "canonical_expected": expected,
        "observed": observed,
    }


def _collect_allowed_sources(spec: BiographySpec) -> set[str]:
    allowed: set[str] = set()
    for section in spec.sections:
        for ref in section.source_refs:
            allowed.add(f"{ref.source_type}:{ref.source_id}")
    return allowed


def _painting_is_approved(painting_id: str) -> bool:
    from app.db import get_chronicle_painting_record

    record = get_chronicle_painting_record(painting_id)
    return bool(record and record.get("status") == "approved")


def get_biography_guardian() -> BiographyGuardian:
    return MockBiographyGuardian()
