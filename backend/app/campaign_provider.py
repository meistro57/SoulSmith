# backend/app/campaign_provider.py
"""
Campaign narrative provider abstraction and provider runtime entry points.

Providers receive the deterministic, consent-safe ``NarrativeContext`` and
return a structured ``NarrativeOutput`` whose claims are limited to the facts
already authorized by deterministic systems.

> DOMAIN SYSTEMS DECIDE WHAT IS TRUE. THE SOULKEEPER DECIDES HOW IT IS TOLD.

The mock requires no external AI and is the default. A real provider
(OpenAI-compatible chat completions) is wired behind the same interface; it may
choose wording, tone, dialogue, and connective prose, but may never invent
canonical relationships, prior events, Thread truths, unearned relic abilities,
cross-Aspect connections, private knowledge, dates/ages/durations, or override a
player's rejection.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.campaign import (
    NARRATIVE_TEMPLATE_VERSION,
    NarrativeContext,
    NarrativeDialogue,
    NarrativeOutput,
    NarrativeQuestion,
)

PROVIDER_MOCK = "mock"
PROVIDER_OPENAI_COMPATIBLE = "openai_compatible"


class CampaignNarrativeProvider(ABC):
    """A replaceable narrative backend. Implementations are pure: they turn an
    authorized context into structured prose and never mutate state."""

    provider: str
    provider_model: str
    narration_source: str

    @abstractmethod
    def narrate(self, context: NarrativeContext) -> NarrativeOutput:
        """Render an authorized opportunity into bounded, structured prose."""


class MockCampaignNarrativeProvider(CampaignNarrativeProvider):
    """Deterministic mock narrative generator; offline and stable."""

    provider = PROVIDER_MOCK
    provider_model = "soulsmith-mock-campaign-v1"
    narration_source = "deterministic"

    def narrate(self, context: NarrativeContext) -> NarrativeOutput:
        claims = list(context.allowed_claims)
        prose = _compose_prose(context, claims)
        title = context.title_hint or _derive_title(context.opportunity_type)
        question = None
        if "player_choice_pending" in context.constraints:
            question = NarrativeQuestion(
                prompt="Before you, a pattern waits to be named or refused.",
                kind="choice",
            )
        return NarrativeOutput(
            title=title,
            prose=prose,
            scene_prose=prose,
            soulkeeper_narration=prose,
            dialogue=[],
            question=question,
            flavor_lines=[],
            presentation_cues=[],
            claims=claims,
            source_evidence=list(context.source_evidence),
            referenced_provenance_ids=list(context.provenance_ids),
            declared_uncertainty=list(context.allowed_uncertainty),
            provider=self.provider,
            provider_model=self.provider_model,
            template_version=NARRATIVE_TEMPLATE_VERSION,
        )


class OpenAICompatibleCampaignProvider(CampaignNarrativeProvider):
    """A real, configurable provider backed by any OpenAI-compatible chat
    completions endpoint (local or remote). No vendor SDK is hard-wired."""

    provider = PROVIDER_OPENAI_COMPATIBLE
    narration_source = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("SOULSMITH_NARRATIVE_BASE_URL", "")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("SOULSMITH_NARRATIVE_API_KEY", "")
        self.model = model or os.environ.get("SOULSMITH_NARRATIVE_MODEL", "local-model")
        self.timeout = timeout_seconds or float(
            os.environ.get("SOULSMITH_NARRATIVE_TIMEOUT_SECONDS", "30")
        )
        self.provider_model = self.model

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def narrate(self, context: NarrativeContext) -> NarrativeOutput:
        if not self.configured:
            raise RuntimeError(
                "OpenAI-compatible provider is not configured "
                "(set SOULSMITH_NARRATIVE_BASE_URL)."
            )
        messages = _build_messages(context)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return _parse_provider_content(
            content, context, self.provider, self.provider_model
        )


def get_campaign_provider(
    provider_type: str | None = None,
) -> CampaignNarrativeProvider:
    """Select a narrative provider from configuration. Unknown providers fall
    back to the deterministic mock so provider failure can never invent canon."""
    selected = provider_type or os.environ.get(
        "SOULSMITH_CAMPAIGN_PROVIDER", PROVIDER_MOCK
    )
    if selected == PROVIDER_MOCK:
        return MockCampaignNarrativeProvider()
    if selected == PROVIDER_OPENAI_COMPATIBLE:
        return OpenAICompatibleCampaignProvider()
    return MockCampaignNarrativeProvider()


def list_campaign_provider_capabilities() -> dict[str, Any]:
    """Capability and status reporting without exposing secrets."""
    selected = os.environ.get("SOULSMITH_CAMPAIGN_PROVIDER", PROVIDER_MOCK)
    real = OpenAICompatibleCampaignProvider()
    return {
        "selected": selected,
        "available": [PROVIDER_MOCK, PROVIDER_OPENAI_COMPATIBLE],
        "capabilities": {
            PROVIDER_MOCK: {
                "configured": True,
                "deterministic": True,
                "offline": True,
                "model": MockCampaignNarrativeProvider.provider_model,
            },
            PROVIDER_OPENAI_COMPATIBLE: {
                "configured": real.configured,
                "deterministic": False,
                "offline": False,
                "model": real.model,
                "base_url_configured": bool(real.base_url),
                "api_key_configured": bool(real.api_key),
            },
        },
        "template_version": NARRATIVE_TEMPLATE_VERSION,
    }


def _derive_title(opportunity_type: str | None) -> str | None:
    if not opportunity_type:
        return None
    return {
        "seed_echo": "A Familiar Echo",
        "recurring_symbol": "The Symbol Returns",
        "unresolved_question_callback": "An Unanswered Question",
        "relic_memory": "The Relic Remembers",
        "relic_awakening_candidate": "A Relic on the Threshold",
        "probable_path_echo": "The Path Not Taken",
        "cross_aspect_echo": "An Echo From Another Life",
        "npc_historical_reaction": "A Voice From the Past",
        "group_memory_callback": "A Shared Memory",
        "world_memory_legend_encounter": "A Living Legend",
        "integration_candidate": "A Pattern Ready to Change",
        "recognition": "A Pattern You May Recognize",
        "reflection_prompt": "A Quiet Question",
        "chronicle_painting_eligibility": "A Moment Worth Remembering",
    }.get(opportunity_type)


def _compose_prose(context: NarrativeContext, claims: list[str]) -> str:
    if not claims:
        return "The world holds its breath. Nothing needs to echo right now."
    joined = "; ".join(claims)
    constraints = context.constraints
    if "player_choice_pending" in constraints:
        return "Before you, a pattern waits to be named or refused: " + joined + "."
    if "npc_knowledge_scoped" in constraints:
        return "A voice from the world offers this much, and no more: " + joined + "."
    return f"The Chronicle offers this much, and no more: {joined}."


def _build_messages(context: NarrativeContext) -> list[dict[str, str]]:
    style = context.style
    system = (
        "You are the Soulkeeper of SoulSmith, a Curiosity Engineer and mythic "
        "facilitator. You narrate an authorized scene. DOMAIN SYSTEMS DECIDE "
        "WHAT IS TRUE; YOU DECIDE HOW IT IS TOLD.\n"
        "You may write scene description, dialogue, atmosphere, and connective "
        "prose. You may NEVER invent prior events, relationships, promises, "
        "StoryMarks, relic history or abilities, Thread truth, Integration "
        "Events, cross-Aspect relationships, participant presence, locations, "
        "dates/ages/durations, private facts, or NPC omniscience.\n"
        "If a fact is not in the authorized context, omit it or phrase around "
        "the gap. Never claim authority over the player's soul or interior life.\n"
        f"Template version: {NARRATIVE_TEMPLATE_VERSION}. "
        f"Style: {json.dumps(style)}. "
        "Return ONLY a JSON object with keys: title, prose, dialogue "
        "(array of {speaker,line,kind}), question ({prompt,kind} or null), "
        "flavor_lines (array of strings), referenced_provenance_ids (array), "
        "declared_uncertainty (array of strings)."
    )
    user = {
        "soul_id": context.soul_id,
        "opportunity_type": context.opportunity_type,
        "allowed_claims": context.allowed_claims,
        "visible_entities": [e.model_dump() for e in context.visible_entities],
        "constraints": context.constraints,
        "provenance_ids": context.provenance_ids,
        "continuity": context.continuity.model_dump() if context.continuity else None,
        "corrections": context.corrections,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user)},
    ]


def _parse_provider_content(
    content: str, context: NarrativeContext, provider: str, provider_model: str
) -> NarrativeOutput:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Provider returned malformed structured output.") from exc
    if not isinstance(data, dict):
        raise TypeError("Provider output is not a JSON object.")

    dialogue = [
        NarrativeDialogue(**d)
        if isinstance(d, dict)
        else NarrativeDialogue(speaker="", line=str(d))
        for d in data.get("dialogue", []) or []
    ]
    question = data.get("question")
    if isinstance(question, dict):
        question = NarrativeQuestion(**question)
    elif question:
        question = NarrativeQuestion(prompt=str(question))
    else:
        question = None

    prose = str(data.get("prose") or data.get("scene_prose") or "")
    return NarrativeOutput(
        title=data.get("title"),
        prose=prose,
        scene_prose=prose or None,
        soulkeeper_narration=data.get("soulkeeper_narration"),
        dialogue=dialogue,
        question=question,
        flavor_lines=[str(f) for f in (data.get("flavor_lines") or [])],
        presentation_cues=[],
        claims=list(context.allowed_claims),
        source_evidence=list(context.source_evidence),
        referenced_provenance_ids=[
            str(p) for p in (data.get("referenced_provenance_ids") or [])
        ],
        declared_uncertainty=[str(u) for u in (data.get("declared_uncertainty") or [])],
        provider=provider,
        provider_model=provider_model,
        template_version=NARRATIVE_TEMPLATE_VERSION,
    )
