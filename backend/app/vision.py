"""
SoulSmith Optical Dice Photo Recognition Pipeline
Combines computer vision preprocessing with candidate face detection.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
import random
from app.grammar import SEVEN_DICE_GRAMMAR

class DetectedDiePrediction(BaseModel):
    die_role: str
    poly_type: str
    detected_face: str
    confidence: float
    alternates: List[str]

class PhotoIngestRequest(BaseModel):
    image_base64: Optional[str] = None
    expected_set: str = "standard_mythic_v1"

class PhotoIngestResponse(BaseModel):
    status: str  # exact_match | needs_confirmation | low_confidence
    detected_dice: List[DetectedDiePrediction]
    ui_hints: Dict[str, List[str]]
    overall_confidence: float

def process_dice_photo(req: PhotoIngestRequest) -> PhotoIngestResponse:
    """
    Simulates OpenCV contour preprocessing + YOLO detector prediction pipeline.
    Identifies 7 polyhedral dice with confidence ratings and alternate suggestions.
    """
    roles = ["spark", "domain", "pressure", "aim", "approach", "verdict", "thread"]
    predictions: List[DetectedDiePrediction] = []
    total_conf = 0.0

    low_conf_roles = []

    for role in roles:
        grammar_def = SEVEN_DICE_GRAMMAR[role]
        faces = list(grammar_def.faces.keys())
        chosen = random.choice(faces)
        alts = [f for f in faces if f != chosen][:2]

        # Simulate camera lighting & glare confidence thresholding
        confidence = round(random.uniform(0.82, 0.98), 2)
        if random.random() < 0.2:  # Occasional ambiguous face read
            confidence = round(random.uniform(0.65, 0.78), 2)
            low_conf_roles.append(role)

        total_conf += confidence
        predictions.append(DetectedDiePrediction(
            die_role=role,
            poly_type=grammar_def.die_type,
            detected_face=chosen,
            confidence=confidence,
            alternates=alts
        ))

    avg_conf = round(total_conf / len(roles), 2)
    status = "exact_match" if avg_conf >= 0.90 and not low_conf_roles else "needs_confirmation"

    return PhotoIngestResponse(
        status=status,
        detected_dice=predictions,
        ui_hints={
            "highlight_low_confidence": low_conf_roles,
            "suggest_retake": ["lighting_uneven"] if avg_conf < 0.85 else []
        },
        overall_confidence=avg_conf
    )
