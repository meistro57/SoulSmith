# backend/app/campaign_provider.py
"""
Campaign narrative provider abstraction.

Providers receive the deterministic, consent-safe ``NarrativeContext`` and
return a structured ``NarrativeOutput`` whose claims are limited to the
authorized facts already authorized by deterministic systems. The mock requires
no external AI and is the default. A real LLM provider would be added behind
this same interface and may choose wording, tone, and connective prose, but may
never invent canonical relationships, prior events, Thread truths, unearned
relic abilities, cross-Aspect connections, private knowledge, or override a
player's rejection.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from app.campaign import NarrativeContext, NarrativeOutput


class CampaignNarrativeProvider(ABC):
    @abstractmethod
    def narrate(self, context: NarrativeContext) -> NarrativeOutput:
        """Render an authorized opportunity into bounded prose."""


class MockCampaignNarrativeProvider(CampaignNarrativeProvider):
    """Deterministic mock narrative generator; offline and stable."""

    PROVIDER = "mock"
    PROVIDER_MODEL = "soulsmith-mock-campaign-v1"

    def narrate(self, context: NarrativeContext) -> NarrativeOutput:
        claims = list(context.allowed_claims)
        prose = _compose_prose(context, claims)
        title = context.title_hint or _derive_title(context.opportunity_type)
        return NarrativeOutput(
            title=title,
            prose=prose,
            claims=claims,
            source_evidence=list(context.source_evidence),
            provider=self.PROVIDER,
            provider_model=self.PROVIDER_MODEL,
        )


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
    return f"The Chronicle offers this much, and no more: {joined}."


def get_campaign_provider(
    provider_type: str | None = None,
) -> CampaignNarrativeProvider:
    selected = provider_type or os.environ.get("SOULSMITH_CAMPAIGN_PROVIDER", "mock")
    if selected == "mock":
        return MockCampaignNarrativeProvider()
    # Only the deterministic mock is wired in v1; unknown providers fall back to
    # the mock so provider failure can never invent canonical history.
    return MockCampaignNarrativeProvider()
