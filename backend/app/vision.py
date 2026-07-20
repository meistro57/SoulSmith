"""
SoulSmith optical dice photo recognition simulation.

The current camera pipeline is explicitly simulated: it produces tentative numeric
face readings that must be confirmed before interpretation/canon submission.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.grammar import DIE_LIMITS

ROLE_TO_DIE = {
    "spark": "d20",
    "domain": "d12",
    "pressure": "d10",
    "aim": "percentile",
    "approach": "d8",
    "verdict": "d6",
    "thread": "d4",
}


class DetectedDiePrediction(BaseModel):
    die_role: str
    poly_type: str
    detected_value: int
    confidence: float
    alternates: List[int]


class PhotoIngestRequest(BaseModel):
    image_base64: Optional[str] = None
    expected_set: str = "standard_mythic_v1"


class PhotoIngestResponse(BaseModel):
    status: str
    detected_dice: List[DetectedDiePrediction]
    ui_hints: Dict[str, List[str]]
    overall_confidence: float
    simulated: bool = True


def process_dice_photo(req: PhotoIngestRequest) -> PhotoIngestResponse:
    """Return simulated numeric face candidates for the seven dice."""
    predictions: List[DetectedDiePrediction] = []
    total_conf = 0.0
    low_conf_roles: List[str] = []

    for role, die in ROLE_TO_DIE.items():
        limit = DIE_LIMITS[die]
        chosen = random.randint(1, limit)
        alternates = [value for value in range(1, limit + 1) if value != chosen][:2]
        confidence = round(random.uniform(0.82, 0.98), 2)
        if random.random() < 0.2:
            confidence = round(random.uniform(0.65, 0.78), 2)
            low_conf_roles.append(role)
        total_conf += confidence
        predictions.append(
            DetectedDiePrediction(
                die_role=role,
                poly_type="d%" if die == "percentile" else die,
                detected_value=chosen,
                confidence=confidence,
                alternates=alternates,
            )
        )

    avg_conf = round(total_conf / len(predictions), 2)
    return PhotoIngestResponse(
        status="exact_match"
        if avg_conf >= 0.90 and not low_conf_roles
        else "needs_confirmation",
        detected_dice=predictions,
        ui_hints={
            "highlight_low_confidence": low_conf_roles,
            "suggest_retake": ["lighting_uneven"] if avg_conf < 0.85 else [],
        },
        overall_confidence=avg_conf,
    )
