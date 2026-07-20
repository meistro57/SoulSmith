"""
SoulSmith versioned seven-dice grammar and canonical numeric roll contract.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

CURRENT_GRAMMAR_VERSION = "1.0.0"
DIE_LIMITS = {
    "d20": 20,
    "d12": 12,
    "d10": 10,
    "percentile": 100,
    "d8": 8,
    "d6": 6,
    "d4": 4,
}


class DieDefinition(BaseModel):
    role: str
    die_type: str
    narrative_function: str
    faces: Dict[str, str]


class NumericDiceRoll(BaseModel):
    d20: int = Field(..., ge=1, le=20)
    d12: int = Field(..., ge=1, le=12)
    d10: int = Field(..., ge=1, le=10)
    percentile: int = Field(..., ge=1, le=100)
    d8: int = Field(..., ge=1, le=8)
    d6: int = Field(..., ge=1, le=6)
    d4: int = Field(..., ge=1, le=4)
    grammar_version: str = CURRENT_GRAMMAR_VERSION

    @field_validator("grammar_version")
    @classmethod
    def grammar_must_exist(cls, value: str) -> str:
        if value not in GRAMMAR_REGISTRY:
            raise ValueError(f"Unknown grammar_version '{value}'")
        return value

    def raw_values(self) -> Dict[str, int]:
        return {die: getattr(self, die) for die in DIE_LIMITS}


class RollRequest(BaseModel):
    grammar_version: str = CURRENT_GRAMMAR_VERSION
    seed: Optional[int | str] = None

    @field_validator("grammar_version")
    @classmethod
    def grammar_must_exist(cls, value: str) -> str:
        if value not in GRAMMAR_REGISTRY:
            raise ValueError(f"Unknown grammar_version '{value}'")
        return value


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


class InterpretedDiceRoll(BaseModel):
    raw: Dict[str, int]
    grammar_version: str
    interpretation: DiceRollRead
    grammar_sentence: str


CanonicalRollRecord = InterpretedDiceRoll


class GrammarEntry(BaseModel):
    value_min: int
    value_max: int
    symbol: str
    description: str

    def contains(self, value: int) -> bool:
        return self.value_min <= value <= self.value_max


class VersionedGrammar(BaseModel):
    version: str
    dice: Dict[str, DieDefinition]
    mappings: Dict[str, List[GrammarEntry]]

    @model_validator(mode="after")
    def validate_full_coverage(self) -> "VersionedGrammar":
        for die, limit in DIE_LIMITS.items():
            covered = {
                value
                for entry in self.mappings[die]
                for value in range(entry.value_min, entry.value_max + 1)
            }
            expected = set(range(1, limit + 1))
            if covered != expected:
                raise ValueError(
                    f"Grammar {self.version} does not cover every {die} face"
                )
        return self


def _entries(symbols: List[tuple[int, int, str, str]]) -> List[GrammarEntry]:
    return [
        GrammarEntry(value_min=a, value_max=b, symbol=s, description=d)
        for a, b, s, d in symbols
    ]


V1_DICE: Dict[str, DieDefinition] = {
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
            "Wonder": "Moved by curiosity, mystery, beauty, or discovery",
        },
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
            "Omen": "A prophetic sign, celestial event, or impending threat",
        },
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
            "Scarcity": "Depleted resources, lacking materials, or hunger",
        },
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
            "Transform": "To alter, heal, convert, or mutate the nature of a thing",
        },
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
            "Craft": "Material manipulation, invention, repair, or tool use",
        },
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
            "Collapse": "Ruin, breach, damage, or sudden breakdown",
        },
    ),
    "thread": DieDefinition(
        role="Thread",
        die_type="d4",
        narrative_function="Lasting mark / Persistent continuity token",
        faces={
            "Bond": "A vow, tie, or allegiance forged with an entity/person",
            "Memory": "An indelible record, chronicle entry, or insight logged",
            "Mark": "A physical or spiritual brand, scar, or trace left behind",
            "Prophecy": "A forecast, warning, or doombell set into motion",
        },
    ),
}

V1_GRAMMAR = VersionedGrammar(
    version=CURRENT_GRAMMAR_VERSION,
    dice=V1_DICE,
    mappings={
        "d20": _entries(
            [
                (1, 3, "Heart", V1_DICE["spark"].faces["Heart"]),
                (4, 6, "Mind", V1_DICE["spark"].faces["Mind"]),
                (7, 9, "Shadow", V1_DICE["spark"].faces["Shadow"]),
                (10, 13, "Wild", V1_DICE["spark"].faces["Wild"]),
                (14, 16, "Wound", V1_DICE["spark"].faces["Wound"]),
                (17, 20, "Wonder", V1_DICE["spark"].faces["Wonder"]),
            ]
        ),
        "d12": _entries(
            [
                (1, 2, "Self", V1_DICE["domain"].faces["Self"]),
                (3, 4, "Ally", V1_DICE["domain"].faces["Ally"]),
                (5, 6, "Foe", V1_DICE["domain"].faces["Foe"]),
                (7, 8, "Place", V1_DICE["domain"].faces["Place"]),
                (9, 10, "Relic", V1_DICE["domain"].faces["Relic"]),
                (11, 12, "Omen", V1_DICE["domain"].faces["Omen"]),
            ]
        ),
        "d10": _entries(
            [
                (1, 2, "Time", V1_DICE["pressure"].faces["Time"]),
                (3, 4, "Fear", V1_DICE["pressure"].faces["Fear"]),
                (5, 5, "Debt", V1_DICE["pressure"].faces["Debt"]),
                (6, 7, "Exposure", V1_DICE["pressure"].faces["Exposure"]),
                (8, 9, "Corruption", V1_DICE["pressure"].faces["Corruption"]),
                (10, 10, "Scarcity", V1_DICE["pressure"].faces["Scarcity"]),
            ]
        ),
        "percentile": _entries(
            [
                (1, 16, "Seek", V1_DICE["aim"].faces["Seek"]),
                (17, 33, "Protect", V1_DICE["aim"].faces["Protect"]),
                (34, 50, "Bind", V1_DICE["aim"].faces["Bind"]),
                (51, 66, "Break", V1_DICE["aim"].faces["Break"]),
                (67, 83, "Reveal", V1_DICE["aim"].faces["Reveal"]),
                (84, 100, "Transform", V1_DICE["aim"].faces["Transform"]),
            ]
        ),
        "d8": _entries(
            [
                (1, 1, "Edge", V1_DICE["approach"].faces["Edge"]),
                (2, 2, "Grace", V1_DICE["approach"].faces["Grace"]),
                (3, 4, "Guile", V1_DICE["approach"].faces["Guile"]),
                (5, 5, "Lore", V1_DICE["approach"].faces["Lore"]),
                (6, 7, "Empathy", V1_DICE["approach"].faces["Empathy"]),
                (8, 8, "Craft", V1_DICE["approach"].faces["Craft"]),
            ]
        ),
        "d6": _entries(
            [
                (1, 1, "Ascend", V1_DICE["verdict"].faces["Ascend"]),
                (2, 2, "Scar", V1_DICE["verdict"].faces["Scar"]),
                (3, 3, "Stall", V1_DICE["verdict"].faces["Stall"]),
                (4, 4, "Twist", V1_DICE["verdict"].faces["Twist"]),
                (5, 5, "Reveal", V1_DICE["verdict"].faces["Reveal"]),
                (6, 6, "Collapse", V1_DICE["verdict"].faces["Collapse"]),
            ]
        ),
        "d4": _entries(
            [
                (1, 1, "Bond", V1_DICE["thread"].faces["Bond"]),
                (2, 2, "Memory", V1_DICE["thread"].faces["Memory"]),
                (3, 3, "Mark", V1_DICE["thread"].faces["Mark"]),
                (4, 4, "Prophecy", V1_DICE["thread"].faces["Prophecy"]),
            ]
        ),
    },
)

GRAMMAR_REGISTRY: Dict[str, VersionedGrammar] = {CURRENT_GRAMMAR_VERSION: V1_GRAMMAR}
SEVEN_DICE_GRAMMAR = V1_DICE


def get_available_versions() -> Dict[str, Any]:
    return {
        "current_default": CURRENT_GRAMMAR_VERSION,
        "versions": list(GRAMMAR_REGISTRY.keys()),
    }


def get_versioned_grammar(version: str = CURRENT_GRAMMAR_VERSION) -> VersionedGrammar:
    try:
        return GRAMMAR_REGISTRY[version]
    except KeyError as exc:
        raise ValueError(f"Unknown grammar_version '{version}'") from exc


def _lookup(grammar: VersionedGrammar, die: str, value: int) -> str:
    for entry in grammar.mappings[die]:
        if entry.contains(value):
            return entry.symbol
    raise ValueError(f"No {die} grammar mapping for value {value}")


def interpret_numeric_roll(roll: NumericDiceRoll) -> InterpretedDiceRoll:
    grammar = get_versioned_grammar(roll.grammar_version)
    read = DiceRollRead(
        spark=_lookup(grammar, "d20", roll.d20),
        domain=_lookup(grammar, "d12", roll.d12),
        pressure=_lookup(grammar, "d10", roll.d10),
        aim=_lookup(grammar, "percentile", roll.percentile),
        approach=_lookup(grammar, "d8", roll.d8),
        verdict=_lookup(grammar, "d6", roll.d6),
        thread=_lookup(grammar, "d4", roll.d4),
    )
    return InterpretedDiceRoll(
        raw=roll.raw_values(),
        grammar_version=roll.grammar_version,
        interpretation=read,
        grammar_sentence=read.to_grammar_sentence(),
    )


def generate_numeric_roll(
    grammar_version: str = CURRENT_GRAMMAR_VERSION, seed: Optional[int | str] = None
) -> InterpretedDiceRoll:
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    roll = NumericDiceRoll(
        d20=rng.randint(1, 20),
        d12=rng.randint(1, 12),
        d10=rng.randint(1, 10),
        percentile=rng.randint(1, 100),
        d8=rng.randint(1, 8),
        d6=rng.randint(1, 6),
        d4=rng.randint(1, 4),
        grammar_version=grammar_version,
    )
    return interpret_numeric_roll(roll)
