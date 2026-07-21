# backend/app/curiosity.py
"""
SoulSmith Curiosity & Thread Integration Engine.
Manages Seeds, Open Questions, Local Threads, and Integration Events.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Seed(BaseModel):
    id: str
    world_id: str = "default"
    soul_id: Optional[str] = None
    symbol: str
    thread_type: str  # Bond, Memory, Mark, Prophecy
    stage: str = "planted"  # planted, echoed, recognized, integrated, retired
    echo_count: int = 1
    narrative_context: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OpenQuestion(BaseModel):
    id: str
    seed_id: Optional[str] = None
    question_text: str
    stakes: Optional[str] = None
    status: str = "open"  # open, investigated, resolved, reinterpreted
    evidence_event_ids: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class LocalThread(BaseModel):
    id: str
    soul_id: str
    name: str
    thread_type: str  # Bond, Memory, Mark, Prophecy
    status: str = "active"  # active, pattern_recognized, integrated, dormant
    evidence_count: int = 1
    evidence_summary: str
    created_at: Optional[str] = None


class IntegrationEvent(BaseModel):
    id: str
    soul_id: str
    thread_id: str
    choice_made: str
    relic_awakened_id: Optional[str] = None
    transformation_summary: str
    created_at: Optional[str] = None


class SeedPlantRequest(BaseModel):
    symbol: str
    thread_type: str
    narrative_context: str
    soul_id: Optional[str] = "Unbound Soul"
    initial_question: Optional[str] = None


class QuestionResolveRequest(BaseModel):
    question_id: str
    resolution_notes: str
    status: str = "resolved"  # resolved | reinterpreted


class IntegrateThreadRequest(BaseModel):
    thread_id: str
    soul_name: str
    choice_made: str
    target_relic_id: Optional[str] = None
