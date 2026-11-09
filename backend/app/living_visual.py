# backend/app/living_visual.py
"""
SoulSmith Phase 21: Living Visual World runtime.

> SOULSMITH DOES NOT ILLUSTRATE EVERYTHING. IT PAINTS WHAT BECOMES WORTH
> REMEMBERING.  MEMORY IS CANON. ART IS INTERPRETATION.

This module ties the completed visual architecture into the playable loop:

    CANONICAL STATE -> ART DIRECTOR ELIGIBILITY -> SCENE/PORTRAIT/OBJECT SPEC
    -> VISUAL PROVIDER -> QUARANTINE -> VISUAL CANON GUARDIAN -> APPROVAL
    -> GALLERY / MEMORY

It never does ``GENERATED IMAGE -> NEW CANON``. The Art Director (this
module's eligibility pass) decides *which* structured canonical moments are
worth painting; the provider only interprets; the Guardian keeps pixels out of
history when they contradict canon.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.living_visual_compiler import (
    CONTINUITY_TYPES,
    SourceEvidenceRefModel,
    VisualJobType,
    VisualSceneSpecModel,
    compile_visual_prompt,
    compile_visual_scene_spec,
)
from app.living_visual_provider import (
    VisualJobGenerationRequest,
    VisualJobGenerationResult,
    get_living_visual_provider,
    requires_reference,
)

LIVING_VISUAL_COMPILER_VERSION = "1.0.0"

ArtMomentStatus = Literal[
    "eligible", "queued", "curated", "deferred", "rejected", "completed", "hidden"
]

VisualJobState = Literal[
    "queued",
    "running",
    "completed",
    "guardian_review",
    "approved",
    "rejected",
    "hidden",
    "blocked",
    "failed",
    "cancelled",
    "deferred",
]

GuardianVerdict = Literal["pass", "retry", "block"]


class ArtMomentModel(BaseModel):
    art_moment_id: str
    session_id: str
    campaign_id: str
    soul_id: str
    visual_type: VisualJobType
    cooldown_key: str | None = None
    eligibility_rule: str
    source_entity_type: str | None = None
    source_entity_id: str | None = None
    title: str
    source_evidence: list[dict[str, Any]] = Field(default_factory=list)
    reference_asset_ids: list[str] = Field(default_factory=list)
    spec: dict[str, Any] = Field(default_factory=dict)
    status: ArtMomentStatus = "eligible"
    created_at: str | None = None
    updated_at: str | None = None


class VisualJobModel(BaseModel):
    job_id: str
    art_moment_id: str
    session_id: str
    campaign_id: str
    soul_id: str
    visual_type: VisualJobType
    provider: str = "mock"
    provider_model: str | None = None
    workflow_role: str | None = None
    workflow_version: str = "1.0.0"
    provider_request_id: str | None = None
    generation_seed: int | None = None
    generation_state: VisualJobState = "queued"
    retry_count: int = 0
    spec: dict[str, Any] = Field(default_factory=dict)
    reference_asset_ids: list[str] = Field(default_factory=list)
    quarantined_image_url: str | None = None
    final_image_url: str | None = None
    guardian_status: str = "pending"
    guardian_report: dict[str, Any] | None = None
    failure_reason: str | None = None
    superseded_job_id: str | None = None
    contributor_id: str | None = None
    contributor_name: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class HumanCurationModel(BaseModel):
    """Human creative direction. May interpret, never rewrite locked facts."""

    curation_id: str
    art_moment_id: str
    contributor_id: str
    contributor_name: str | None = None
    style_guidance: str = ""
    composition: str = ""
    mood: str = ""
    motif: str = ""
    symbolism: str = ""
    provenance_note: str = ""
    created_at: str | None = None


class QueueArtMomentsRequest(BaseModel):
    session_id: str


class ProcessVisualJobRequest(BaseModel):
    provider_type: str | None = None
    seed: int | None = None


class CurateArtMomentRequest(BaseModel):
    contributor_id: str
    contributor_name: str | None = None
    style_guidance: str = ""
    composition: str = ""
    mood: str = ""
    motif: str = ""
    symbolism: str = ""
    provenance_note: str = ""


# ---------------------------------------------------------------------------
# Guardian
# ---------------------------------------------------------------------------


class GuardianViolationModel(BaseModel):
    type: str
    severity: str = "medium"
    description: str
    canonical_expected: str
    observed: str


class GuardianReportModel(BaseModel):
    status: GuardianVerdict
    confidence: float = 0.0
    violations: list[GuardianViolationModel] = Field(default_factory=list)
    correction_instructions: list[str] = Field(default_factory=list)


class LivingVisualGuardian(ABC):
    @abstractmethod
    def inspect(
        self,
        *,
        image_bytes: bytes,
        spec: VisualSceneSpecModel,
        visual_type: VisualJobType,
        provider: str,
        provider_model: str | None = None,
        workflow_role: str | None = None,
    ) -> GuardianReportModel:
        """Inspect a generated image and return a structured verdict."""


def _violation(
    vtype: str, severity: str, description: str, expected: str, observed: str
) -> GuardianViolationModel:
    return GuardianViolationModel(
        type=vtype,
        severity=severity,
        description=description,
        canonical_expected=expected,
        observed=observed,
    )


class MockLivingVisualGuardian(LivingVisualGuardian):
    """Deterministic guardian honoring ``SOULSMITH_MOCK_GUARDIAN_VERDICT``."""

    def __init__(self, forced_verdict: GuardianVerdict | None = None) -> None:
        self._forced_verdict = forced_verdict

    @classmethod
    def from_env(cls) -> MockLivingVisualGuardian:
        raw = os.environ.get("SOULSMITH_MOCK_GUARDIAN_VERDICT", "").strip().lower()
        verdict: GuardianVerdict | None = (
            raw if raw in ("pass", "retry", "block") else None
        )
        return cls(forced_verdict=verdict)

    def inspect(
        self,
        *,
        image_bytes: bytes,
        spec: VisualSceneSpecModel,
        visual_type: VisualJobType,
        provider: str,
        provider_model: str | None = None,
        workflow_role: str | None = None,
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
                        f"{len(spec.permitted_participants)} participant(s)",
                        "uncertain count",
                    )
                ],
                correction_instructions=[
                    "Re-render with the exact recorded participant set."
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
                        "Generated output could expose identity forbidden by consent.",
                        "no forbidden identity",
                        "unverifiable identity disclosure",
                    )
                ],
                correction_instructions=[],
            )

        # Deterministic spec validation.
        violations: list[GuardianViolationModel] = []
        if requires_reference(visual_type) and not spec.permitted_participants:
            violations.append(
                _violation(
                    "missing_reference",
                    "critical",
                    "Continuity generation has no locked source reference.",
                    "a locked historical reference",
                    "no reference",
                )
            )
        if visual_type in CONTINUITY_TYPES and not any(
            p.reference_image_url or p.portrait_version_id
            for p in spec.permitted_participants
        ):
            violations.append(
                _violation(
                    "missing_reference",
                    "high",
                    "Continuity scene has no historical portrait reference.",
                    "at least one locked portrait version",
                    "no portrait version",
                )
            )
        if not spec.permitted_participants and visual_type in (
            "memory_object",
            "group_memory",
            "relationship",
        ):
            violations.append(
                _violation(
                    "unknown_foreground_people",
                    "high",
                    "Scene has no canonical participants but implies people.",
                    "participants or non-identifying framing",
                    "possible invented people",
                )
            )

        if violations:
            return GuardianReportModel(
                status="retry",
                confidence=0.7,
                violations=violations,
                correction_instructions=[
                    "Align the scene specification to the canonical structured state."
                ],
            )

        return GuardianReportModel(
            status="pass",
            confidence=0.99,
            violations=[],
            correction_instructions=[],
        )


def get_living_visual_guardian() -> LivingVisualGuardian:
    return MockLivingVisualGuardian.from_env()


# ---------------------------------------------------------------------------
# Art Director eligibility
# ---------------------------------------------------------------------------


def evaluate_art_moments(state: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Deterministically decide which canonical moments are eligible for visual
    interpretation. Silence is valid: most events produce no Art Moment.
    """
    moments: list[dict[str, Any]] = []
    soul_id = state.get("soul_id", "")

    moments.extend(_memory_object_moments(state.get("memory_objects", [])))
    moments.extend(_relic_moments(state.get("relics", [])))
    moments.extend(_relationship_moments(state.get("relationships", [])))
    moments.extend(_promise_moments(state.get("promises", [])))
    moments.extend(_group_memory_moments(state.get("group_memories", [])))
    moments.extend(_world_memory_moments(state.get("world_memories", [])))
    moments.extend(_thread_moments(state.get("threads", []), state.get("seeds", [])))
    moments.extend(_place_moments(state.get("place_history", []), soul_id))
    return moments


def _memory_object_moments(
    memory_objects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for mo in memory_objects:
        if not mo.get("is_painting_eligible"):
            continue
        tier = mo.get("importance_tier")
        score = int(mo.get("importance_score") or 0)
        if tier not in ("community", "world", "legendary") and score < 7:
            continue
        participants = _participants_from_memory_object(mo)
        moments.append(
            {
                "visual_type": "memory_object",
                "cooldown_key": f"art_moment:memory_object:{mo.get('id')}",
                "eligibility_rule": "Significant Memory Object is painting-eligible.",
                "source_entity_type": "memory_object",
                "source_entity_id": mo.get("id"),
                "title": mo.get("event_title", "Untitled memory"),
                "source_evidence": [
                    {"source_type": "memory_object", "source_id": mo.get("id")}
                ],
                "reference_asset_ids": [
                    p["portrait_version_id"]
                    for p in participants
                    if p.get("portrait_version_id")
                ],
                "spec": {
                    "permitted_participants": participants,
                    "canonical_objects": list(mo.get("relics_involved") or []),
                    "relic_state": ", ".join(mo.get("relics_involved") or [])
                    or "No relics involved.",
                    "location": mo.get("location_environment"),
                    "environment": mo.get("location_environment"),
                    "action_facts": [mo.get("action_composition", "")],
                    "outcome_facts": [mo.get("lasting_consequence", "")],
                    "emotional_tone": mo.get("emotional_tone", "Solemn."),
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _participants_from_memory_object(mo: dict[str, Any]) -> list[dict[str, Any]]:
    participants: list[dict[str, Any]] = []
    for p in mo.get("participants", []) or []:
        participants.append(
            {
                "soul_id": p.get("soul_id"),
                "character_name": p.get("character_name", p.get("soul_id")),
                "role_in_event": p.get("role_in_event", "participant"),
                "portrait_version_id": p.get("portrait_version_id"),
                "reference_image_url": None,
                "identity_strategy": (
                    "historical_portrait"
                    if p.get("portrait_version_id")
                    else "silhouette"
                ),
            }
        )
    return participants


def _relic_moments(relics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for relic in relics:
        stage = relic.get("stage")
        if stage not in ("Awakened", "Transfigured", "Overdrawn", "Fractured"):
            continue
        rid = relic.get("id")
        name = relic.get("name", rid)
        moments.append(
            {
                "visual_type": "relic",
                "cooldown_key": f"art_moment:relic:{rid}:{stage}",
                "eligibility_rule": "Relic entered a visually significant canonical state.",
                "source_entity_type": "relic",
                "source_entity_id": rid,
                "title": f"{name} ({stage})",
                "source_evidence": [{"source_type": "relic", "source_id": rid}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": [],
                    "canonical_objects": [name],
                    "relic_state": stage,
                    "location": None,
                    "environment": None,
                    "action_facts": [],
                    "outcome_facts": [f"Relic stage: {stage}"],
                    "emotional_tone": "Solemn and resonant.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _relationship_moments(relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for rel in relationships:
        events = rel.get("events") or []
        if not events:
            continue
        rid = rel.get("relationship_id")
        kinds = ", ".join(rel.get("kinds", []) or []) or "relationship"
        participants = _participants_from_entities(rel.get("participants", []))
        moments.append(
            {
                "visual_type": "relationship",
                "cooldown_key": f"art_moment:relationship:{rid}",
                "eligibility_rule": "Relationship has canonical interaction history.",
                "source_entity_type": "relationship",
                "source_entity_id": rid,
                "title": f"A {kinds} relationship",
                "source_evidence": [{"source_type": "relationship", "source_id": rid}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": participants,
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": None,
                    "environment": None,
                    "action_facts": [e.get("summary", "") for e in events],
                    "outcome_facts": [],
                    "emotional_tone": "Warm, layered, human.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _participants_from_entities(
    participants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "soul_id": p.get("entity_id"),
            "character_name": p.get("entity_id", "figure"),
            "role_in_event": p.get("role", "participant"),
            "portrait_version_id": None,
            "reference_image_url": None,
            "identity_strategy": "non_identifying",
        }
        for p in participants
    ]


def _promise_moments(promises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for promise in promises:
        state = promise.get("lifecycle_state")
        if state not in ("fulfilled", "broken", "released", "inherited", "transferred"):
            continue
        pid = promise.get("promise_id")
        moments.append(
            {
                "visual_type": "relationship",
                "cooldown_key": f"art_moment:promise:{pid}:{state}",
                "eligibility_rule": "Promise reached a visually significant state.",
                "source_entity_type": "promise",
                "source_entity_id": pid,
                "title": promise.get("promise_text", "A promise"),
                "source_evidence": [{"source_type": "promise", "source_id": pid}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": _participants_from_entities(
                        promise.get("participants", [])
                    ),
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": None,
                    "environment": None,
                    "action_facts": [],
                    "outcome_facts": [f"Promise state: {state}"],
                    "emotional_tone": "Weighted, consequential.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _group_memory_moments(group_memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for group in group_memories:
        significance = group.get("group_significance")
        if significance not in ("community", "world", "legendary"):
            continue
        gid = group.get("group_id")
        members = group.get("members", []) or []
        participants = [
            {
                "soul_id": m.get("soul_id"),
                "character_name": m.get("soul_id", "figure"),
                "role_in_event": m.get("role_in_event", "participant"),
                "portrait_version_id": m.get("portrait_version_id"),
                "reference_image_url": None,
                "identity_strategy": (
                    "historical_portrait"
                    if m.get("portrait_version_id")
                    else "non_identifying"
                ),
            }
            for m in members
        ]
        moments.append(
            {
                "visual_type": "group_memory",
                "cooldown_key": f"art_moment:group_memory:{gid}",
                "eligibility_rule": "Significant Group Memory may be interpreted.",
                "source_entity_type": "group_memory",
                "source_entity_id": gid,
                "title": group.get("title", "A shared memory"),
                "source_evidence": [{"source_type": "group_memory", "source_id": gid}],
                "reference_asset_ids": [
                    m.get("portrait_version_id")
                    for m in members
                    if m.get("portrait_version_id")
                ],
                "spec": {
                    "permitted_participants": participants,
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": None,
                    "environment": None,
                    "action_facts": [],
                    "outcome_facts": [group.get("summary", "")],
                    "emotional_tone": "Shared but not collapsed.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _world_memory_moments(world_memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for memory in world_memories:
        scale = memory.get("remembrance_scale")
        if scale not in ("community", "world", "legendary"):
            continue
        mid = memory.get("memory_id")
        moments.append(
            {
                "visual_type": "world_memory",
                "cooldown_key": f"art_moment:world_memory:{mid}",
                "eligibility_rule": "Cultural memory is significant enough to illustrate.",
                "source_entity_type": "world_memory",
                "source_entity_id": mid,
                "title": memory.get("title", "A remembered legend"),
                "source_evidence": [{"source_type": "world_memory", "source_id": mid}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": [],
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": None,
                    "environment": None,
                    "action_facts": [],
                    "outcome_facts": [memory.get("memory_form", "legend")],
                    "emotional_tone": "Legendary, distant.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _thread_moments(
    threads: list[dict[str, Any]], seeds: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for thread in threads:
        if thread.get("status") not in ("pattern_recognized", "integrated"):
            continue
        tid = thread.get("id")
        moments.append(
            {
                "visual_type": "chronicle_painting",
                "cooldown_key": f"art_moment:thread:{tid}",
                "eligibility_rule": "A major Thread transition is worth a painting.",
                "source_entity_type": "local_thread",
                "source_entity_id": tid,
                "title": thread.get("name", "A recognized thread"),
                "source_evidence": [{"source_type": "local_thread", "source_id": tid}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": [],
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": None,
                    "environment": None,
                    "action_facts": [],
                    "outcome_facts": [thread.get("evidence_summary", "")],
                    "emotional_tone": "Revelatory.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


def _place_moments(
    place_history: list[dict[str, Any]], soul_id: str
) -> list[dict[str, Any]]:
    by_place: dict[str, list[dict[str, Any]]] = {}
    for entry in place_history:
        by_place.setdefault(entry.get("place_id"), []).append(entry)
    moments: list[dict[str, Any]] = []
    for place_id, entries in by_place.items():
        if len(entries) < 2:
            continue
        moments.append(
            {
                "visual_type": "place",
                "cooldown_key": f"art_moment:place:{place_id}:{len(entries)}",
                "eligibility_rule": "A place accumulates a SoulSmith visual history.",
                "source_entity_type": "place",
                "source_entity_id": place_id,
                "title": f"A place, revisited ({len(entries)} times)",
                "source_evidence": [{"source_type": "place", "source_id": place_id}],
                "reference_asset_ids": [],
                "spec": {
                    "permitted_participants": [],
                    "canonical_objects": [],
                    "relic_state": None,
                    "location": place_id,
                    "environment": None,
                    "action_facts": [e.get("event_type", "") for e in entries],
                    "outcome_facts": [],
                    "emotional_tone": "Layered, accumulating memory.",
                    "unknown_fields": [],
                },
            }
        )
    return moments


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def _max_retries() -> int:
    return int(os.environ.get("SOULSMITH_VISUAL_MAX_RETRIES", "2"))


def _quarantine_dir() -> Any:
    from pathlib import Path

    return Path("living-visuals") / "quarantine"


def _approved_dir() -> Any:
    from pathlib import Path

    return Path("living-visuals") / "approved"


class LivingVisualRuntimeError(ValueError):
    """Raised when a living-visual request cannot be satisfied safely."""


def _store():
    from app.comfyui.storage import CandidateImageStore

    return CandidateImageStore()


def queue_art_moments(session_id: str) -> dict[str, Any]:
    """Evaluate Art Director eligibility and enqueue queued VisualJobs. Idempotent."""
    from app import db
    from app.multi_aspect import active_soul_id

    session = db.get_campaign_session_record(session_id)
    if not session:
        raise LivingVisualRuntimeError(f"Session '{session_id}' not found")
    state = _gather_state(session)
    moments = evaluate_art_moments(state)
    created: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    for spec in moments:
        result = enqueue_art_moment(session, spec)
        if result["created"]:
            created.append(result["art_moment"])
            jobs.append(result["job"])
    return {
        "session_id": session_id,
        "active_soul_id": active_soul_id(session),
        "art_moments": created,
        "jobs": jobs,
        "created": len(created),
    }


def _gather_state(session: dict[str, Any]) -> dict[str, Any]:
    from app import db
    from app.multi_aspect import active_soul_id
    from app.relationship import promise_visible_to, relationship_visible_to
    from app.world_memory import memory_object_visible_to, world_memory_visible_to

    soul_id = active_soul_id(session)
    memory_objects = [
        mo
        for mo in db.get_memory_objects_records()
        if memory_object_visible_to(mo, soul_id)
    ]
    group_memories = []
    for group in db.list_group_memory_records():
        group["members"] = db.get_group_memory_members_records(group["group_id"])
        group_memories.append(group)
    relationships = [
        rel
        for rel in db.list_relationship_records()
        if relationship_visible_to(rel, soul_id)
    ]
    promises = [p for p in db.list_promise_records() if promise_visible_to(p, soul_id)]
    world_memories = [
        m for m in db.list_world_memory_records() if world_memory_visible_to(m, soul_id)
    ]
    return {
        "soul_id": soul_id,
        "threads": db.get_all_local_threads(soul_id=soul_id),
        "seeds": db.get_seeds_for_soul(soul_id),
        "relics": db.get_or_create_relics_records(soul_id=soul_id),
        "memory_objects": memory_objects,
        "group_memories": group_memories,
        "relationships": relationships,
        "promises": promises,
        "world_memories": world_memories,
        "place_history": db.list_all_place_history_records(),
    }


def enqueue_art_moment(
    session: dict[str, Any], moment_spec: dict[str, Any]
) -> dict[str, Any]:
    """Create an ArtMoment and a queued VisualJob (idempotent by cooldown key)."""
    from app import db

    cooldown_key = moment_spec.get("cooldown_key")
    existing = (
        db.get_art_moment_by_cooldown_key_record(cooldown_key) if cooldown_key else None
    )
    if existing:
        job = db.get_latest_visual_job_for_art_moment_record(existing["art_moment_id"])
        return {
            "created": False,
            "art_moment": existing,
            "job": job,
        }

    spec = compile_visual_scene_spec(
        visual_type=moment_spec["visual_type"],
        title=moment_spec["title"],
        source_entity_type=moment_spec.get("source_entity_type"),
        source_entity_id=moment_spec.get("source_entity_id"),
        source_evidence=[
            SourceEvidenceRefModel(**e) for e in moment_spec.get("source_evidence", [])
        ],
        **moment_spec.get("spec", {}),
    )

    art_moment = db.create_art_moment_record(
        session_id=session["session_id"],
        campaign_id=session["campaign_id"],
        soul_id=session.get("active_soul_id") or session["soul_id"],
        visual_type=moment_spec["visual_type"],
        cooldown_key=cooldown_key,
        eligibility_rule=moment_spec["eligibility_rule"],
        source_entity_type=moment_spec.get("source_entity_type"),
        source_entity_id=moment_spec.get("source_entity_id"),
        title=moment_spec["title"],
        source_evidence=moment_spec.get("source_evidence", []),
        reference_asset_ids=moment_spec.get("reference_asset_ids", []),
        spec=spec.model_dump(),
    )

    job = db.create_visual_job_record(
        art_moment_id=art_moment["art_moment_id"],
        session_id=session["session_id"],
        campaign_id=session["campaign_id"],
        soul_id=art_moment["soul_id"],
        visual_type=moment_spec["visual_type"],
        spec=spec.model_dump(),
        reference_asset_ids=moment_spec.get("reference_asset_ids", []),
    )
    return {"created": True, "art_moment": art_moment, "job": job}


def process_visual_job(
    job_id: str, provider_type: str | None = None, seed: int | None = None
) -> dict[str, Any]:
    """Run generate -> quarantine -> Guardian -> pass/retry/block for a job."""
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    if job["generation_state"] in ("approved", "rejected", "hidden"):
        return {"job": job, "idempotent": True}

    provider = get_living_visual_provider(provider_type)
    guardian = get_living_visual_guardian()

    current_id = job_id
    while True:
        current = db.get_visual_job_record(current_id)
        if not current:
            raise LivingVisualRuntimeError(f"VisualJob '{current_id}' not found")
        current_spec = VisualSceneSpecModel(**current["spec"])

        db.update_visual_job_generation_record(current_id, generation_state="running")
        reference_url = _reference_image_url(current)
        req = VisualJobGenerationRequest(
            job_id=current_id,
            visual_type=current["visual_type"],
            compiled_prompt=compile_visual_prompt(current_spec),
            negative_prompt=", ".join(current_spec.prohibited_additions),
            reference_image_url=reference_url,
            seed=seed,
        )
        result: VisualJobGenerationResult = provider.generate(req)

        if not result.success:
            db.update_visual_job_generation_record(
                current_id,
                generation_state="failed",
                provider=result.provider,
                provider_model=result.provider_model,
                workflow_role=result.workflow_role,
                workflow_version=result.workflow_version,
                failure_reason=result.failure_reason,
            )
            return {"job": db.get_visual_job_record(current_id), "idempotent": False}

        quarantined_url = _store().save_in_subdir(
            _quarantine_dir(), current_id, result.image_bytes or b""
        )
        db.update_visual_job_generation_record(
            current_id,
            generation_state="guardian_review",
            provider=result.provider,
            provider_model=result.provider_model,
            workflow_role=result.workflow_role,
            workflow_version=result.workflow_version,
            quarantined_image_url=quarantined_url,
            provider_request_id=result.provider_request_id,
        )

        report = guardian.inspect(
            image_bytes=result.image_bytes or b"",
            spec=current_spec,
            visual_type=current["visual_type"],
            provider=result.provider,
            provider_model=result.provider_model,
            workflow_role=result.workflow_role,
        )
        db.record_visual_job_guardian_report(current_id, report.model_dump())

        if report.status == "pass":
            final_url = _store().save_in_subdir(
                _approved_dir(), current_id, result.image_bytes or b""
            )
            db.update_visual_job_promotion_record(
                current_id,
                final_image_url=final_url,
                guardian_status="passed",
                guardian_report=report.model_dump(),
                generation_state="completed",
            )
            return {"job": db.get_visual_job_record(current_id), "idempotent": False}

        if report.status == "block":
            db.update_visual_job_generation_record(
                current_id,
                generation_state="blocked",
                guardian_status="blocked",
                failure_reason="Visual Canon Guardian blocked this image: "
                + "; ".join(v.description for v in report.violations),
            )
            return {"job": db.get_visual_job_record(current_id), "idempotent": False}

        # RETRY
        db.update_visual_job_generation_record(
            current_id,
            generation_state="failed",
            guardian_status="retry",
            failure_reason="Visual Canon Guardian requested regeneration.",
        )
        if current["retry_count"] >= _max_retries():
            db.update_visual_job_generation_record(
                current_id,
                generation_state="blocked",
                guardian_status="blocked",
                failure_reason="Visual Canon Guardian retry limit reached.",
            )
            return {"job": db.get_visual_job_record(current_id), "idempotent": False}

        retry = db.create_visual_job_record(
            art_moment_id=current["art_moment_id"],
            session_id=current["session_id"],
            campaign_id=current["campaign_id"],
            soul_id=current["soul_id"],
            visual_type=current["visual_type"],
            spec=current["spec"],
            reference_asset_ids=current["reference_asset_ids"],
            retry_count=current["retry_count"] + 1,
            superseded_job_id=current_id,
        )
        current_id = retry["job_id"]


def _reference_image_url(job: dict[str, Any]) -> str | None:
    """Resolve the locked source reference for continuity jobs."""
    from app import db

    if not requires_reference(job["visual_type"]):
        return None
    ref_ids = job.get("reference_asset_ids") or []
    if ref_ids:
        version = db.get_portrait_version_record(ref_ids[0])
        if version and version.get("image_url"):
            return version["image_url"]
    spec = job.get("spec") or {}
    for p in spec.get("permitted_participants", []):
        if p.get("reference_image_url"):
            return p["reference_image_url"]
    return None


def approve_visual_job(job_id: str) -> dict[str, Any]:
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    if job["generation_state"] != "completed":
        raise LivingVisualRuntimeError(
            "Only Guardian-passed, completed jobs may be approved."
        )
    updated = db.update_visual_job_state_record(job_id, "approved")
    return {"job": updated}


def reject_visual_job(job_id: str) -> dict[str, Any]:
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    updated = db.update_visual_job_state_record(job_id, "rejected")
    return {"job": updated}


def hide_visual_job(job_id: str) -> dict[str, Any]:
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    updated = db.update_visual_job_state_record(job_id, "hidden")
    return {"job": updated}


def regenerate_visual_job(job_id: str) -> dict[str, Any]:
    """Regenerate interpretation without changing canon. Creates a new job."""
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    retry = db.create_visual_job_record(
        art_moment_id=job["art_moment_id"],
        session_id=job["session_id"],
        campaign_id=job["campaign_id"],
        soul_id=job["soul_id"],
        visual_type=job["visual_type"],
        spec=job["spec"],
        reference_asset_ids=job["reference_asset_ids"],
        retry_count=job["retry_count"] + 1,
        superseded_job_id=job_id,
    )
    return {"job": retry}


def record_human_curation(
    art_moment_id: str,
    *,
    contributor_id: str,
    contributor_name: str | None = None,
    style_guidance: str = "",
    composition: str = "",
    mood: str = "",
    motif: str = "",
    symbolism: str = "",
    provenance_note: str = "",
) -> dict[str, Any]:
    """
    Record human creative direction. Interpretation fields only; locked facts
    are never rewritten. Applies the interpretation to the Art Moment's spec.
    """
    from app import db

    moment = db.get_art_moment_record(art_moment_id)
    if not moment:
        raise LivingVisualRuntimeError(f"ArtMoment '{art_moment_id}' not found")

    curation = db.create_visual_curation_record(
        art_moment_id=art_moment_id,
        contributor_id=contributor_id,
        contributor_name=contributor_name,
        style_guidance=style_guidance,
        composition=composition,
        mood=mood,
        motif=motif,
        symbolism=symbolism,
        provenance_note=provenance_note,
    )

    # Apply interpretation-only overrides to the spec, never locked facts.
    spec = dict(moment.get("spec") or {})
    for key, value in (
        ("style_guidance", style_guidance),
        ("composition", composition),
        ("mood", mood),
        ("motif", motif),
        ("symbolism", symbolism),
    ):
        if value:
            spec[key] = value
    db.update_art_moment_spec_record(art_moment_id, spec)
    return {"curation": curation, "art_moment": db.get_art_moment_record(art_moment_id)}


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def list_art_moments(session_id: str | None = None) -> dict[str, Any]:
    from app import db

    records = db.list_art_moments_records(session_id=session_id)
    return {"art_moments": [ArtMomentModel(**r).model_dump() for r in records]}


def get_art_moment(art_moment_id: str) -> dict[str, Any]:
    from app import db

    record = db.get_art_moment_record(art_moment_id)
    if not record:
        raise LivingVisualRuntimeError(f"ArtMoment '{art_moment_id}' not found")
    return {"art_moment": ArtMomentModel(**record).model_dump()}


def list_visual_jobs(
    session_id: str | None = None, art_moment_id: str | None = None
) -> dict[str, Any]:
    from app import db

    records = db.list_visual_jobs_records(
        session_id=session_id, art_moment_id=art_moment_id
    )
    return {"jobs": [VisualJobModel(**r).model_dump() for r in records]}


def get_visual_job(job_id: str) -> dict[str, Any]:
    from app import db

    record = db.get_visual_job_record(job_id)
    if not record:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    return {"job": VisualJobModel(**record).model_dump()}


def inspect_scene_spec(job_id: str) -> dict[str, Any]:
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    spec = VisualSceneSpecModel(**job["spec"])
    return {
        "job_id": job_id,
        "scene_spec": spec.model_dump(),
        "spec_version": spec.spec_version,
        "compiler_version": LIVING_VISUAL_COMPILER_VERSION,
    }


def get_guardian_verdict(job_id: str) -> dict[str, Any]:
    from app import db

    job = db.get_visual_job_record(job_id)
    if not job:
        raise LivingVisualRuntimeError(f"VisualJob '{job_id}' not found")
    reports = db.list_visual_job_guardian_reports_records(job_id)
    return {
        "job_id": job_id,
        "guardian_status": job["guardian_status"],
        "guardian_report": job["guardian_report"],
        "history": reports,
    }


def visual_history(
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    soul_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Approved visual history for an Aspect/relic/place/event."""
    from app import db

    jobs = db.list_visual_jobs_records(session_id=session_id)
    if entity_type and entity_id:
        moments = db.list_art_moments_records(session_id=session_id)
        moment_ids = {
            m["art_moment_id"]
            for m in moments
            if m.get("source_entity_type") == entity_type
            and m.get("source_entity_id") == entity_id
        }
        jobs = [j for j in jobs if j["art_moment_id"] in moment_ids]
    if soul_id:
        jobs = [j for j in jobs if j["soul_id"] == soul_id]
    approved = [j for j in jobs if j["generation_state"] == "approved"]
    return {"visual_history": [VisualJobModel(**j).model_dump() for j in approved]}
