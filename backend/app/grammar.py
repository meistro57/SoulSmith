"""
SoulSmith Seven-Dice Grammar Definitions & Tables
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

class DieDefinition(BaseModel):
    role: str
    die_type: str
    narrative_function: str
    faces: Dict[str, str]  # face_name -> meaning

SEVEN_DICE_GRAMMAR: Dict[str, DieDefinition] = {
    "spark": DieDefinition(
        role="Spark",
        die_type="d20",
        narrative_function="Who moves / Core Motif",
        faces={
            "Heart": "Motivated by deep devotion, love, or emotional truth",
            "Mind": "Guided by intellect, logic, calculation, or strategy",
            "Shadow": "Influenced by secret motives, doubt, or hidden trauma",
            "Wild": "Instinctive, untamed, unpredictable, or elemental",
            "Wound": "Driven by past scars, loss, pain, or grief",
            "Wonder": "Moved by curiosity, mystery, beauty, or discovery"
        }
    ),
    "domain": DieDefinition(
        role="Domain",
        die_type="d12",
        narrative_function="Where it lands / Location context",
        faces={
            "Self": "Internal realm, mind, spirit, or personal identity",
            "Ally": "A trusted companion, mentor, or friendly faction",
            "Foe": "An adversary, opposing force, or rival power",
            "Place": "The physical environment, architecture, or landscape",
            "Relic": "An ancient artifact, tool, weapon, or strange mechanism",
            "Omen": "A prophetic sign, celestial event, or impending threat"
        }
    ),
    "pressure": DieDefinition(
        role="Pressure",
        die_type="d10",
        narrative_function="What resists / Escalation force",
        faces={
            "Time": "A ticking clock, fading light, or imminent deadline",
            "Fear": "Paralyzing doubt, terror, or psychological dread",
            "Debt": "An unpaid vow, past favor owed, or spiritual weight",
            "Exposure": "Vulnerability to observation, betrayal, or environment",
            "Corruption": "Spreading blight, decay, madness, or distortion",
            "Scarcity": "Depleted resources, lacking materials, or hunger"
        }
    ),
    "aim": DieDefinition(
        role="Aim",
        die_type="d%",
        narrative_function="What is wanted / Intended goal",
        faces={
            "Seek": "To search for, locate, or track down a truth or item",
            "Protect": "To shield, defend, preserve, or guard someone/something",
            "Bind": "To seal, capture, restrain, or forge a binding pact",
            "Break": "To shatter, destroy, sever, or unmake a bond/barrier",
            "Reveal": "To uncover, unmask, decipher, or expose what was hidden",
            "Transform": "To alter, heal, convert, or mutate the nature of a thing"
        }
    ),
    "approach": DieDefinition(
        role="Approach",
        die_type="d8",
        narrative_function="How it is done / Action method",
        faces={
            "Edge": "Direct, swift, high-risk, decisive, or aggressive force",
            "Grace": "Fluid, silent, stealthy, elegant, or frictionless movement",
            "Guile": "Deceptive, subtle, manipulative, or clever subterfuge",
            "Lore": "Analytical, ritualistic, system-literate, or ancient wisdom",
            "Empathy": "Compassionate, emotionally attuned, relational, or healing",
            "Craft": "Material manipulation, invention, repair, or tool use"
        }
    ),
    "verdict": DieDefinition(
        role="Verdict",
        die_type="d6",
        narrative_function="Immediate result / Resolution quality",
        faces={
            "Ascend": "Triumph, clean success, momentum, or elevation",
            "Scar": "Costly victory, permanent mark, singe, or sacrifice",
            "Stall": "Falter, hesitation, delay, or temporary friction",
            "Twist": "Unexpected turn, betrayal, complication, or side effect",
            "Reveal": "Unforeseen disclosure, sign, or deeper truth uncovered",
            "Collapse": "Ruin, breach, damage, or sudden breakdown"
        }
    ),
    "thread": DieDefinition(
        role="Thread",
        die_type="d4",
        narrative_function="Lasting mark / Persistent continuity token",
        faces={
            "Bond": "A vow, tie, or allegiance forged with a entity/person",
            "Memory": "An indelible record, chronicle entry, or insight logged",
            "Mark": "A physical or spiritual brand, scar, or trace left behind",
            "Debt": "A tithe, promise, or invoice owed to reality or a faction",
            "Portal": "A gate, path, or doorway opened for future travel",
            "Prophecy": "A forecast, warning, or doombell set into motion"
        }
    )
}

class DiceRollRead(BaseModel):
    spark: str
    domain: str
    pressure: str
    aim: str
    approach: str
    verdict: str
    thread: str

    def to_grammar_sentence(self) -> str:
        return (
            f"Driven by [{self.spark}], the Soul attempts to [{self.aim}] upon [{self.domain}] "
            f"using [{self.approach}] against the pressure of [{self.pressure}]. "
            f"The immediate turn yields [{self.verdict}], weaving a lasting [{self.thread}] Thread."
        )
