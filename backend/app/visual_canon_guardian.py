# backend/app/visual_canon_guardian.py
"""
Visual Canon Guardian: vision-based review of generated Chronicle Paintings.

The Guardian inspects the *actual generated image* against canonical inputs and
never the other way around. It may judge art against canon but may never modify
canon to match the art. Only PASS allows a candidate to become player-visible.

A deterministic mock is provided so development and tests exercise PASS, RETRY,
and BLOCK without GPU, ComfyUI, external AI, or internet access.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List, Optional

from app.chronicle_paintings import (
    GuardianReportModel,
    GuardianVerdict,
    GuardianViolationModel,
    SceneSpecModel,
)
from app.visual_memory import MemoryObjectModel


class VisualCanonGuardian(ABC):
    @abstractmethod
    def inspect(
        self,
        *,
        image_bytes: bytes,
        memory_object: MemoryObjectModel,
        scene_spec: SceneSpecModel,
        provider: str,
        provider_model: Optional[str] = None,
    ) -> GuardianReportModel:
        """Inspect a generated image and return a structured review verdict."""


def _violation(
    vtype: str,
    severity: str,
    description: str,
    expected: str,
    observed: str,
) -> GuardianViolationModel:
    return GuardianViolationModel(
        type=vtype,
        severity=severity,  # type: ignore[arg-type]
        description=description,
        canonical_expected=expected,
        observed=observed,
    )


class MockVisualCanonGuardian(VisualCanonGuardian):
    """
    Deterministic mock Guardian.

    - With no forced verdict, it inspects canonical inputs for a small set of
      hard canon/consent violations and otherwise PASSes (mock images are trusted).
    - ``forced_verdict`` (``pass``/``retry``/``block``) deterministically returns
      that verdict so tests can exercise every pipeline branch.
    """

    def __init__(self, forced_verdict: Optional[GuardianVerdict] = None) -> None:
        self._forced_verdict = forced_verdict

    @classmethod
    def from_env(cls) -> "MockVisualCanonGuardian":
        raw = os.environ.get("SOULSMITH_MOCK_GUARDIAN_VERDICT", "").strip().lower()
        verdict: Optional[GuardianVerdict] = (
            raw if raw in ("pass", "retry", "block") else None
        )
        return cls(forced_verdict=verdict)

    def inspect(
        self,
        *,
        image_bytes: bytes,
        memory_object: MemoryObjectModel,
        scene_spec: SceneSpecModel,
        provider: str,
        provider_model: Optional[str] = None,
    ) -> GuardianReportModel:
        if not image_bytes:
            return GuardianReportModel(
                status="block",
                confidence=1.0,
                violations=[
                    _violation(
                        "image_corruption",
                        "critical",
                        "Generated image is empty or missing.",
                        "a non-empty PNG image",
                        "zero bytes",
                    )
                ],
                correction_instructions=[],
            )

        if self._forced_verdict == "retry":
            return GuardianReportModel(
                status="retry",
                confidence=0.6,
                violations=[
                    _violation(
                        "participant_count",
                        "high",
                        "Participant count could not be verified in the rendered image.",
                        f"{len(memory_object.participants)} participant(s)",
                        "uncertain count",
                    )
                ],
                correction_instructions=[
                    "Re-render with the exact recorded participant count.",
                    "Keep historical appearance locked to the recorded portrait version(s).",
                ],
            )

        if self._forced_verdict == "block":
            return GuardianReportModel(
                status="block",
                confidence=0.95,
                violations=[
                    _violation(
                        "consent_violation",
                        "critical",
                        "Generated output could expose identity forbidden by consent state.",
                        "no forbidden identity",
                        "unverifiable identity disclosure",
                    )
                ],
                correction_instructions=[],
            )

        # Deterministic default: inspect canonical inputs for hard violations.
        violations: List[GuardianViolationModel] = []
        if not memory_object.participants and not _is_environmental(scene_spec):
            violations.append(
                _violation(
                    "unknown_foreground_people",
                    "high",
                    "Scene has no canonical participants but framing implies foreground figures.",
                    "environment-only or omitted participants",
                    "possible invented foreground people",
                )
            )

        participant_souls = {p.soul_id for p in memory_object.participants}
        spec_souls = {p.soul_id for p in scene_spec.participants}
        if participant_souls != spec_souls:
            violations.append(
                _violation(
                    "participant_count",
                    "high",
                    "Scene spec participant set diverges from canonical Memory Object.",
                    f"{sorted(participant_souls)}",
                    f"{sorted(spec_souls)}",
                )
            )

        if violations:
            return GuardianReportModel(
                status="retry",
                confidence=0.7,
                violations=violations,
                correction_instructions=[
                    "Align the scene specification to the canonical participant set."
                ],
            )

        return GuardianReportModel(
            status="pass",
            confidence=0.99,
            violations=[],
            correction_instructions=[],
        )


def _is_environmental(scene_spec: SceneSpecModel) -> bool:
    return scene_spec.composition in {
        "environmental",
        "phenomenon_focus",
        "relic_focus",
    }


def get_visual_canon_guardian() -> VisualCanonGuardian:
    """Return the configured Visual Canon Guardian (mock only in this phase)."""
    return MockVisualCanonGuardian.from_env()
