# backend/app/composition_selector.py
"""
Deterministic Chronicle Painting composition selector.

Maps canonical facts (participant count, significance, phenomena, relic
involvement, event type, emotional tone) to a lightweight composition mode.
The selector is deliberately simple and deterministic so the same memory always
frames the same way. Significance influences framing and scale without turning
every important memory into a glowing superhero poster.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from app.chronicle_paintings import COMPOSITION_MODES

_DEFAULT = "environmental"

_CONFRONTATION_TONES = {"confrontation", "tense", "conflict", "battle", "duel"}
_JOURNEY_TONES = {"journey", "travel", "departure", "pilgrimage", "march"}
_RITUAL_TONES = {"ritual", "ceremony", "ritualistic", "solemn", "oath", "burial"}
_AFTERMATH_TONES = {"aftermath", "loss", "grief", "ruin", "consequence", "mourning"}
_DISCOVERY_TONES = {"discovery", "revelation", "unveiling", "mystery", "wonder"}

_EVENT_CONFRONTATION = {"confrontation", "battle", "duel", "siege", "pursuit"}
_EVENT_DISCOVERY = {"discovery", "unveiling", "revelation", "finding"}
_EVENT_JOURNEY = {"journey", "travel", "quest", "departure"}
_EVENT_RITUAL = {"ritual", "ceremony", "oath", "funeral"}
_EVENT_AFTERMATH = {"aftermath", "consequence", "ruin", "loss"}


def _has_any(text: Optional[str], keywords: Iterable[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def select_composition(
    *,
    participant_count: int = 1,
    importance_tier: str = "personal",
    importance_score: int = 5,
    has_phenomena: bool = False,
    has_relic: bool = False,
    event_type: Optional[str] = None,
    emotional_tone: Optional[str] = None,
) -> str:
    """
    Return a composition mode from the canonical memory facts.

    Priority order is fixed and documented so the result is deterministic:

    1. Phenomena present -> phenomenon_focus
    2. Relic present -> relic_focus
    3. Ritual event/tone -> ritual
    4. Discovery event/tone -> discovery
    5. Aftermath event/tone -> aftermath
    6. Journey event/tone -> journey
    7. Confrontation event/tone or >=2 participants -> confrontation / group_memory
    8. Single participant -> intimate
    9. Fallback -> environmental

    World-tier memories broaden the frame to ``environmental`` only when no
    stronger canonical signal is already selected, so significance adds scale
    without producing a hero poster.
    """
    if has_phenomena:
        return "phenomenon_focus"

    if has_relic:
        return "relic_focus"

    if _has_any(event_type, _EVENT_RITUAL) or _has_any(emotional_tone, _RITUAL_TONES):
        return "ritual"

    if _has_any(event_type, _EVENT_DISCOVERY) or _has_any(
        emotional_tone, _DISCOVERY_TONES
    ):
        return "discovery"

    if _has_any(event_type, _EVENT_AFTERMATH) or _has_any(
        emotional_tone, _AFTERMATH_TONES
    ):
        return "aftermath"

    if _has_any(event_type, _EVENT_JOURNEY) or _has_any(emotional_tone, _JOURNEY_TONES):
        return "journey"

    if _has_any(event_type, _EVENT_CONFRONTATION) or _has_any(
        emotional_tone, _CONFRONTATION_TONES
    ):
        return "confrontation"

    if participant_count >= 3:
        return "group_memory"

    if participant_count == 2:
        return "confrontation"

    if importance_tier == "world" and importance_score >= 8:
        return "environmental"

    return "intimate"


def composition_guidance(mode: str) -> str:
    """Return deterministic framing guidance for a composition mode."""
    return {
        "intimate": (
            "intimate close framing on a single participant, shallow depth of "
            "field, emotional micro-expression, tactile detail"
        ),
        "environmental": (
            "wide environmental establishing shot, landmark-scale composition, "
            "small figures within a large readable space"
        ),
        "confrontation": (
            "two figures in tension across the frame, eye-line opposition, "
            "negative space between them, restrained drama"
        ),
        "discovery": (
            "figure discovering a threshold or reveal, the discovered thing "
            "dominant in the frame, wonder restrained to posture and light"
        ),
        "aftermath": (
            "the quiet after the event, evidence of consequence in the "
            "environment, low energy, reflective stillness"
        ),
        "journey": (
            "figures on a path or threshold, distance ahead, the landscape as "
            "the emotional subject"
        ),
        "ritual": (
            "ceremonial grouping around a central act, symmetrical or processional "
            "structure, reverent stillness"
        ),
        "relic_focus": (
            "the relic as compositional anchor, participants contextual but "
            "subordinate, tactile material detail"
        ),
        "phenomenon_focus": (
            "the phenomenon as the dominant subject, environment affected by it, "
            "restrained magical intensity"
        ),
        "group_memory": (
            "multiple participants in a shared moment, group orientation and "
            "spacing communicate relationships, no heroic isolation"
        ),
    }.get(mode, "balanced painterly composition with clear focal separation")


def list_composition_modes() -> List[str]:
    """Return the supported composition modes."""
    return list(COMPOSITION_MODES)
