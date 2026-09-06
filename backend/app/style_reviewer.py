# backend/app/style_reviewer.py
"""
Phase 15: optional Art Direction (style) reviewer.

The style reviewer answers whether a generated candidate follows the selected
Art Direction Profile. It is deliberately separate from the Visual Canon
Guardian, which answers whether the depicted event is canonical and safe.

A style verdict may never override a Visual Canon Guardian BLOCK. A beautiful
image that violates canon still fails.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.art_director import ResolvedArtDirectionModel

StyleReviewVerdict = Literal["pass", "retry"]


class StyleReviewResultModel(BaseModel):
    status: StyleReviewVerdict
    style_confidence: float = 0.0
    style_deviations: list[str] = Field(default_factory=list)
    correction_instructions: list[str] = Field(default_factory=list)


class ArtDirectionReviewer(ABC):
    @abstractmethod
    def review(
        self,
        *,
        resolved: ResolvedArtDirectionModel,
        generated_metadata: dict | None = None,
    ) -> StyleReviewResultModel:
        """Review style compliance without judging canonical validity."""


class MockArtDirectionReviewer(ArtDirectionReviewer):
    """
    Deterministic mock style reviewer (no GPU/vision required).

    - With no forced verdict it PASSes with high confidence, treating the mock
      generated image as style-compliant.
    - ``forced_verdict`` (``retry``) lets tests exercise a style correction loop.
    """

    def __init__(self, forced_verdict: StyleReviewVerdict | None = None) -> None:
        self._forced_verdict = forced_verdict

    @classmethod
    def from_env(cls) -> MockArtDirectionReviewer:
        raw = (
            os.environ.get("SOULSMITH_MOCK_STYLE_REVIEWER_VERDICT", "").strip().lower()
        )
        verdict: StyleReviewVerdict | None = raw if raw in ("pass", "retry") else None
        return cls(forced_verdict=verdict)

    def review(
        self,
        *,
        resolved: ResolvedArtDirectionModel,
        generated_metadata: dict | None = None,
    ) -> StyleReviewResultModel:
        if self._forced_verdict == "retry":
            return StyleReviewResultModel(
                status="retry",
                style_confidence=0.5,
                style_deviations=[
                    (
                        "Generated candidate may not fully reflect the selected "
                        "palette and treatment guidance."
                    )
                ],
                correction_instructions=[
                    "Re-render with the selected Art Direction Profile applied.",
                ],
            )
        return StyleReviewResultModel(
            status="pass",
            style_confidence=0.98,
            style_deviations=[],
            correction_instructions=[],
        )


def get_art_direction_reviewer() -> ArtDirectionReviewer:
    """Return the configured style reviewer (mock only in this phase)."""
    return MockArtDirectionReviewer.from_env()


def final_verdict_after_style_review(
    guardian_status: str,
    style_review: StyleReviewResultModel,
) -> str:
    """
    Combine Visual Canon Guardian and style review. The Guardian is authoritative:
    a ``block`` or ``retry`` from the Guardian always wins over a style ``pass``,
    and a Guardian ``block`` can never be overridden by a style approval.
    """
    if guardian_status in ("block", "blocked", "failed"):
        return guardian_status
    if guardian_status == "retry":
        return "retry"
    # Guardian passed; style review can only downgrade to retry, never block.
    if style_review.status == "retry":
        return "retry"
    return guardian_status
