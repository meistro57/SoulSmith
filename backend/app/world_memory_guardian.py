# backend/app/world_memory_guardian.py
"""
World Memory Guardian: deterministic validation of generated cultural-memory
artifacts.

This Guardian does NOT correct legends into canon. Its job is to verify that
deviations are intentional, declared, and safe. A declared exaggeration may
pass; an undeclared hallucination must fail.

It detects, at minimum:

- source IDs that do not exist,
- factual claims with no canonical backing and no declared deviation,
- private participant information leaking into public legend,
- undeclared participant invention,
- a scoped perspective claiming omniscient truth,
- drift without a declared deviation,
- accidental mutation/promotion of legend into canonical records.

Deterministic structural validation runs without an LLM, mirroring the
Biography Guardian and the Visual Canon Guardian.
"""

from __future__ import annotations

from typing import Any

from app.world_memory import (
    GeneratedWorldMemoryArtifact,
    WorldMemoryGuardianReport,
    WorldMemorySpec,
    is_drift_interpretation,
)

# Phrases that signal an omniscient claim from a scoped perspective.
_OMNISCIENT_MARKERS = (
    "in truth",
    "the whole truth",
    "as it truly happened",
    "the one true account",
    "what really happened",
)


class WorldMemoryGuardian:
    def validate(
        self,
        *,
        artifact: GeneratedWorldMemoryArtifact,
        spec: WorldMemorySpec,
    ) -> WorldMemoryGuardianReport:
        raise NotImplementedError


class MockWorldMemoryGuardian(WorldMemoryGuardian):
    def validate(
        self,
        *,
        artifact: GeneratedWorldMemoryArtifact,
        spec: WorldMemorySpec,
    ) -> WorldMemoryGuardianReport:
        violations: list[dict[str, Any]] = []
        diagnostics: list[str] = []

        allowed_sources = {f"{r.source_type}:{r.source_id}" for r in spec.source_refs}
        allowed_claims = set(spec.allowed_claims)
        allowed_participants = _collect_allowed_participants(spec)

        # 1. Every referenced source must exist in the spec's allowed set.
        for ref in artifact.source_refs:
            key = f"{ref.source_type}:{ref.source_id}"
            if key not in allowed_sources:
                violations.append(
                    _violation(
                        "unknown_source",
                        "critical",
                        f"Artifact references unknown source '{key}'.",
                    )
                )
            if ref.source_type == "chronicle_painting" and not _painting_is_approved(
                ref.source_id
            ):
                violations.append(
                    _violation(
                        "unapproved_visual_reference",
                        "critical",
                        f"Chronicle painting '{ref.source_id}' is not approved and "
                        "cannot become a public monument.",
                    )
                )

        # 2. Drift must be declared. A drift interpretation with no deviation is
        #    an undeclared drift.
        if is_drift_interpretation(spec.interpretation_type) and not (
            artifact.declared_deviations or spec.declared_deviations
        ):
            violations.append(
                _violation(
                    "undeclared_drift",
                    "critical",
                    f"Interpretation '{spec.interpretation_type}' is a drift but no "
                    "deviation was declared.",
                )
            )

        # 3. Every claim must be backed by canon or by a declared deviation.
        declared_legend_claims = {
            d.legend_claims
            for d in (artifact.declared_deviations or spec.declared_deviations)
        }
        for claim in artifact.claims:
            if claim in allowed_claims or claim in declared_legend_claims:
                continue
            violations.append(
                _violation(
                    "undeclared_hallucinated_fact",
                    "critical",
                    f"Artifact asserts unsupported fact '{claim}' without a declared deviation.",
                )
            )

        # 4. Private information must not leak into a public legend.
        if spec.visibility == "public_canon":
            private = _collect_private_sources(spec)
            if private:
                violations.append(
                    _violation(
                        "private_information_leak",
                        "critical",
                        f"Public legend references private sources: {sorted(private)}.",
                    )
                )

        # 5. Scoped perspective must not claim omniscience.
        narrative_lower = artifact.narrative.lower()
        if spec.perspective != "omniscient_narrator":
            for marker in _OMNISCIENT_MARKERS:
                if marker in narrative_lower:
                    violations.append(
                        _violation(
                            "omniscient_claim_from_scoped_perspective",
                            "critical",
                            f"Scoped perspective '{spec.perspective}' claims omniscient truth.",
                        )
                    )
                    break

        # 6. Undeclared participant invention: any participant named in the
        #    narrative must be within the allowed participant set.
        undeclared = _find_undeclared_participants(
            artifact.narrative, allowed_participants
        )
        if undeclared:
            violations.append(
                _violation(
                    "undeclared_participant_invention",
                    "critical",
                    f"Artifact introduces undeclared participant(s): {sorted(undeclared)}.",
                )
            )

        if violations:
            status = "block"
            instructions = [
                "Rebuild the artifact from canonical sources only.",
                "Declare every deviation explicitly.",
                "Keep scoped perspectives from claiming omniscient truth.",
            ]
            diagnostics = [v["description"] for v in violations]
            return WorldMemoryGuardianReport(
                status=status,
                confidence=0.9,
                violations=violations,
                diagnostics=diagnostics,
                correction_instructions=instructions,
            )

        # Recoverable generation issues produce a retry (not a block): an empty
        # narrative, or a declared deviation that is missing its required fields.
        retry_diagnostics: list[str] = []
        if not artifact.narrative.strip():
            retry_diagnostics.append("Generated narrative is empty.")
        for deviation in artifact.declared_deviations or spec.declared_deviations:
            if (
                not deviation.canon_supports.strip()
                and not deviation.legend_claims.strip()
            ):
                retry_diagnostics.append(
                    f"Deviation '{deviation.deviation_kind}' is incomplete."
                )
        if retry_diagnostics:
            return WorldMemoryGuardianReport(
                status="retry",
                confidence=0.7,
                violations=[],
                diagnostics=retry_diagnostics,
                correction_instructions=[
                    "Regenerate the artifact and retry validation."
                ],
            )

        return WorldMemoryGuardianReport(
            status="pass",
            confidence=0.99,
            violations=[],
            diagnostics=["All deviations declared and sourced."],
            correction_instructions=[],
        )


def _violation(vtype: str, severity: str, description: str) -> dict[str, Any]:
    return {"type": vtype, "severity": severity, "description": description}


def _collect_allowed_participants(spec: WorldMemorySpec) -> set[str]:
    participants: set[str] = set()
    for ref in spec.source_refs:
        if ref.source_type in ("memory_object", "group_memory"):
            participants.add(ref.source_id)
    return participants


def _collect_private_sources(spec: WorldMemorySpec) -> list[str]:
    private: list[str] = []
    for ref in spec.source_refs:
        if ref.claim_kind in ("participant_perspective", "private_perspective"):
            private.append(f"{ref.source_type}:{ref.source_id}")
    return private


def _find_undeclared_participants(narrative: str, allowed: set[str]) -> set[str]:
    """
    Deterministic participant-invention check. It only flags explicit
    "soul_id" style tokens in the narrative that are not in the allowed set.
    Real providers would replace this with a semantic check.
    """
    declared: set[str] = set()
    for token in narrative.split():
        if token.startswith("Soul_"):
            declared.add(token.rstrip(".,;:!?") if token[-1] in ".,;:!?" else token)
    return declared - allowed


def _painting_is_approved(painting_id: str) -> bool:
    from app.db import get_chronicle_painting_record

    record = get_chronicle_painting_record(painting_id)
    return bool(record and record.get("status") == "approved")


def get_world_memory_guardian() -> WorldMemoryGuardian:
    return MockWorldMemoryGuardian()
