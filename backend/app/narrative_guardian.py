# backend/app/narrative_guardian.py
"""
SoulSmith Phase 18: narrative Guardian / validator.

A deterministic validation stage for real provider output before it reaches the
player. It is distinct from the Visual Canon Guardian and the World Memory
Guardian, but follows the same philosophy: history is fixed, narration is
derived, and provider prose must never create canonical facts.

The validator only ever checks *against* the authorized ``NarrativeContext``.
It cannot correct canon; it can only pass, retry (with correction instructions),
or block/fallback.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from app.campaign import NarrativeContext, NarrativeOutput

Verdict = Literal["pass", "retry", "block"]

NARRATOR_NAMES = frozenset({"soulkeeper", "the soulkeeper", "narrator", "the narrator"})

# Authoritative psychological/spiritual conclusions the Soulkeeper must not make
# about the player. Providers phrase around these; the player's interior life is
# not a fact the world may assert.
PSYCH_AUTHORITY_PHRASES = (
    "your soul is",
    "your true nature",
    "you are destined",
    "you have always been",
    "deep down you",
    "you will never",
    "you must become",
)

# Markers that introduce a *prior* canonical event. A provider may only reuse
# such an event from declared context; it may never invent one.
PRIOR_EVENT_MARKERS = (
    "you once",
    "you remember",
    "the last time",
    "years ago you",
    "when you first",
    "you have met",
    "long ago you",
)

# Definitive-canon markers that are forbidden inside perspective-bounded scenes.
PERSPECTIVE_VIOLATION_PHRASES = (
    "in fact",
    "the chronicle records",
    "canonically",
    "it truly was",
    "the truth is that",
)

# Duration patterns that a provider must only reuse from declared context.
_DURATION_RE = re.compile(
    r"\b(\d+)\s*(year|month|week|day|night|cycle|winter|summer|season|age)s?\b"
)
_BARE_YEAR_RE = re.compile(r"\b(1[0-9]{3}|2[0-9]{3})\b")

# Verbs that assert a relic gained an ability; only permitted when the context
# already authorizes that ability.
_RELIC_ABILITY_VERBS = ("grant", "bestow", "unlock", "awaken", "summon", "command")


class NarrativeValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["retry", "block"]


class NarrativeValidationReport(BaseModel):
    verdict: Verdict
    issues: list[NarrativeValidationIssue] = Field(default_factory=list)
    checked: list[str] = Field(default_factory=list)
    correction: str | None = None


def _issue(
    severity: Literal["retry", "block"], code: str, message: str
) -> NarrativeValidationIssue:
    return NarrativeValidationIssue(code=code, message=message, severity=severity)


def _blob(output: NarrativeOutput) -> str:
    parts = [output.prose, output.scene_prose, output.soulkeeper_narration]
    parts += [d.line for d in output.dialogue]
    parts += list(output.flavor_lines)
    if output.question:
        parts.append(output.question.prompt)
    return (" ".join(p for p in parts if p)).lower()


def _declared_text(context: NarrativeContext) -> str:
    """All text the context already authorizes. Durations found here are safe."""
    parts = list(context.allowed_claims)
    parts += [c for c in context.constraints]
    parts += [c for c in context.corrections]
    if context.relic_state:
        parts += [str(v) for v in context.relic_state.values()]
    parts += list(context.permitted_relic_knowledge)
    parts += [str(q) for q in context.questions]
    parts += list(context.symbols)
    for t in context.thread_evidence:
        parts += [str(v) for v in t.values()]
    for w in context.world_memory_context:
        parts += [str(v) for v in w.values()]
    for k in context.npc_knowledge:
        parts += [str(v) for v in k.values()]
    parts += list(context.player_visible_consequences)
    parts += list(context.allowed_uncertainty)
    if context.continuity:
        parts.append(context.continuity.model_dump_json())
    return " ".join(parts).lower()


def _undeclared_durations(
    context: NarrativeContext, output: NarrativeOutput
) -> list[str]:
    declared = _declared_text(context)
    blob = _blob(output)
    hits: list[str] = []
    for match in _DURATION_RE.finditer(blob):
        number = match.group(1)
        if number not in declared:
            hits.append(match.group(0))
    for match in _BARE_YEAR_RE.finditer(blob):
        year = match.group(1)
        if year not in declared:
            hits.append(year)
    return hits


def validate_narrative(
    context: NarrativeContext, output: NarrativeOutput
) -> NarrativeValidationReport:
    """Validate provider output against its authorized context."""
    issues: list[NarrativeValidationIssue] = []
    checked: list[str] = []
    blob = _blob(output)

    # 1. Referenced provenance ids must be authorized.
    allowed_provenance = set(context.provenance_ids)
    for pid in output.referenced_provenance_ids:
        if pid not in allowed_provenance:
            issues.append(
                _issue(
                    "block",
                    "unknown_provenance",
                    f"Provenance '{pid}' is not authorized.",
                )
            )
    checked.append("provenance_ids")

    # 2. Dialogue speakers must already be visible; no invented participants.
    visible_names = {(e.label or e.entity_id) for e in context.visible_entities} | {
        e.entity_id for e in context.visible_entities
    }
    for d in output.dialogue:
        if d.speaker.strip().lower() in NARRATOR_NAMES:
            continue
        if d.speaker not in visible_names:
            issues.append(
                _issue(
                    "block",
                    "unknown_participant",
                    f"Dialogue speaker '{d.speaker}' is not visible in the scene.",
                )
            )
    checked.append("participants")

    # 3. Forbidden/private facts must never leak.
    for secret in context.forbidden_facts:
        if secret.lower() in blob:
            issues.append(
                _issue(
                    "block",
                    "private_leak",
                    f"Private/forbidden fact surfaced: '{secret}'.",
                )
            )
    checked.append("private_facts")

    # 4. Dates/ages/durations must be reused from declared context, not invented.
    for duration in _undeclared_durations(context, output):
        issues.append(
            _issue(
                "block",
                "invented_duration",
                f"Undeclared date/age/duration '{duration}' was introduced.",
            )
        )
    checked.append("dates_durations")

    # 5. Relic state/ability claims must match structured context.
    permitted_relic = set(context.permitted_relic_knowledge)
    if context.relic_state is None and not permitted_relic:
        for verb in _RELIC_ABILITY_VERBS:
            if (
                f"relic {verb}" in blob
                or f"relic can {verb}" in blob
                or f"relic {verb}s" in blob
            ):
                issues.append(
                    _issue(
                        "block",
                        "invented_relic_ability",
                        f"The relic is claimed to '{verb}', which is not authorized.",
                    )
                )
    elif context.relic_state is not None:
        relic_blob = (context.relic_state.get("name") or "").lower()
        for ability in permitted_relic:
            if ability.lower() not in blob and ability.lower() not in relic_blob:
                continue
    checked.append("relic_state")

    # 6. Thread / Integration claims must not exceed domain status.
    if context.opportunity_type not in ("integration_candidate", "recognition"):
        if "integration event" in blob and not context.thread_evidence:
            issues.append(
                _issue(
                    "block",
                    "invented_integration",
                    "An Integration Event was asserted without domain status.",
                )
            )
        for phrase in ("the pattern is true", "the thread is true", "it is now canon"):
            if phrase in blob:
                issues.append(
                    _issue(
                        "block",
                        "thread_truth_promoted",
                        "A Thread candidate was promoted to truth by narration.",
                    )
                )
    checked.append("thread_integration")

    # 7. Cross-Aspect / perspective boundaries: no objective-fact conversion.
    if (
        "perspective_boundary" in context.constraints
        or "npc_knowledge_scoped" in context.constraints
    ):
        for phrase in PERSPECTIVE_VIOLATION_PHRASES:
            if phrase in blob:
                issues.append(
                    _issue(
                        "block",
                        "perspective_violation",
                        f"Perspective-bounded narration asserted objective canon ('{phrase}').",
                    )
                )
    checked.append("cross_aspect")

    # 8. No authoritative psychological/spiritual conclusions about the player.
    for phrase in PSYCH_AUTHORITY_PHRASES:
        if phrase in blob:
            issues.append(
                _issue(
                    "block",
                    "psychological_authority",
                    f"Narration claims authority over the player ('{phrase}').",
                )
            )
    checked.append("psychological_authority")

    # 9. No invented prior canonical event.
    if not context.allowed_claims:
        for marker in PRIOR_EVENT_MARKERS:
            if marker in blob:
                issues.append(
                    _issue(
                        "block",
                        "invented_prior_event",
                        f"Narration invented a prior event ('{marker}').",
                    )
                )
    checked.append("prior_events")

    # 10. Undeclared canonical fact heuristics: prose must not introduce new facts
    #     with certainty markers when none were authorized.
    for marker in ("it is known that", "as everyone knows", "it has always been"):
        if marker in blob and not context.allowed_claims:
            issues.append(
                _issue(
                    "retry",
                    "undeclared_fact",
                    f"Narration asserted an undeclared canonical fact ('{marker}').",
                )
            )
    checked.append("undeclared_facts")

    if any(i.severity == "block" for i in issues):
        verdict: Verdict = "block"
        correction = None
    elif any(i.severity == "retry" for i in issues):
        verdict = "retry"
        correction = "; ".join(i.message for i in issues)
    else:
        verdict = "pass"
        correction = None

    return NarrativeValidationReport(
        verdict=verdict,
        issues=issues,
        checked=checked,
        correction=correction,
    )
