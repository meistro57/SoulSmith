# backend/app/curiosity.py
"""
SoulSmith Curiosity & Thread Integration Engine.
Manages Seeds, Open Questions, Local Threads, and Integration Events.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Seed(BaseModel):
    id: str
    world_id: str = "default"
    soul_id: str | None = None
    symbol: str
    thread_type: str  # Bond, Memory, Mark, Prophecy
    stage: str = "planted"  # planted, echoed, recognized, integrated, retired
    echo_count: int = 1
    narrative_context: str
    created_at: str | None = None
    updated_at: str | None = None


class OpenQuestion(BaseModel):
    id: str
    seed_id: str | None = None
    question_text: str
    stakes: str | None = None
    status: str = "open"  # open, investigated, resolved, reinterpreted
    evidence_event_ids: list[str] = Field(default_factory=list)
    created_at: str | None = None


class LocalThread(BaseModel):
    id: str
    soul_id: str
    name: str
    thread_type: str  # Bond, Memory, Mark, Prophecy
    status: str = "active"  # active, pattern_recognized, integrated, dormant
    evidence_count: int = 1
    evidence_summary: str
    created_at: str | None = None


class IntegrationEvent(BaseModel):
    id: str
    soul_id: str
    thread_id: str
    choice_made: str
    relic_awakened_id: str | None = None
    transformation_summary: str
    created_at: str | None = None


class SeedPlantRequest(BaseModel):
    symbol: str
    thread_type: str
    narrative_context: str
    soul_id: str | None = "Unbound Soul"
    initial_question: str | None = None


class QuestionResolveRequest(BaseModel):
    question_id: str
    resolution_notes: str
    status: str = "resolved"  # resolved | reinterpreted


class IntegrateThreadRequest(BaseModel):
    thread_id: str
    soul_name: str
    choice_made: str
    target_relic_id: str | None = None
