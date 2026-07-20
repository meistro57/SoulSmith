"""
SoulSmith Phenomena Engine
Manages non-monster world-scale forces, needs, escalations, and transformation conditions.
"""

from typing import List, Optional
from pydantic import BaseModel


class Phenomenon(BaseModel):
    id: str
    name: str
    typology: str  # Echo | Knot | Veil | Well | Awakening | Breach | Mirror | Sovereign
    origin: str
    visible_signs: List[str]
    hidden_need: str
    escalation_level: int  # 1 to 5
    transformation_condition: str
    reward_or_payoff: str


PHENOMENON_TYPOLOGY = {
    "Echo": "Memories, emotions, or past traumas repeating across time and location.",
    "Knot": "Conflicts and vows bound so tightly that force only tightens the tangle.",
    "Veil": "Hidden truths, illusions, or threshold barriers separating reality layers.",
    "Well": "Conduits of immense power, healing, longing, or corruption.",
    "Awakening": "Ancient dormant beings, places, or prophecies beginning to stir.",
    "Breach": "Rifts in reality allowing incompatible truths to bleed into the world.",
    "Mirror": "Reflections of a Soul's internal shadow material into physical form.",
    "Sovereign": "Entity or place-spirit enforcing its own unbending physical laws.",
}

DEFAULT_ACTIVE_PHENOMENA: List[Phenomenon] = [
    Phenomenon(
        id="phen-1",
        name="The Weeping Floodgate of Cinder",
        typology="Echo",
        origin="Formed during the drowning of the Starforge Archive.",
        visible_signs=[
            "Water dripping upwards",
            "Echoes of unsaid goodbyes in cold air",
        ],
        hidden_need="Requires a forgotten secret to be confessed aloud.",
        escalation_level=2,
        transformation_condition="When a Soul offers a Memory Thread without fear.",
        reward_or_payoff="Transforms into the Well of Clear Answers.",
    ),
    Phenomenon(
        id="phen-2",
        name="The King Without a Reflection",
        typology="Mirror",
        origin="Forged from the collective doubt of lost Keepers.",
        visible_signs=[
            "Mirrors showing different faces",
            "Shadows detaching from walls",
        ],
        hidden_need="Needs a Soul to embrace their inner Shadow without violence.",
        escalation_level=3,
        transformation_condition="When a Revelatory Failure yields an Empathy approach.",
        reward_or_payoff="Awakens the Relic [Glass Oath].",
    ),
]


def escalate_phenomenon(phenomenon_id: str, delta: int = 1) -> Optional[Phenomenon]:
    for p in DEFAULT_ACTIVE_PHENOMENA:
        if p.id == phenomenon_id:
            p.escalation_level = max(1, min(5, p.escalation_level + delta))
            return p
    return None
