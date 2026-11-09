# backend/app/narrative_runtime.py
"""
SoulSmith Phase 18: narrative provider runtime.

The runtime turns an authorized ``NarrativeContext`` into validated, player-safe
``NarrativeOutput`` while enforcing every boundary:

- provider selection/configuration,
- timeout and bounded retry,
- deterministic narrative validation,
- retry with correction instructions (never widening context),
- safe deterministic fallback on validation exhaustion,
- graceful failure on provider errors (canon is never corrupted),
- generation metadata (provider/model/template/timestamp/retry/validation).

The runtime is intentionally independent of any vendor SDK.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.campaign import NARRATIVE_TEMPLATE_VERSION, NarrativeContext, NarrativeOutput
from app.campaign_provider import (
    MockCampaignNarrativeProvider,
    get_campaign_provider,
)
from app.narrative_context_compiler import context_stats
from app.narrative_guardian import NarrativeValidationReport, validate_narrative

DEFAULT_MAX_RETRIES = 2


@dataclass
class RuntimeResult:
    output: NarrativeOutput | None
    failure: str | None
    validation: NarrativeValidationReport | None
    metadata: dict[str, Any] = field(default_factory=dict)
    used_fallback: bool = False


class NarrativeRuntime:
    """Orchestrates one provider into one validated result."""

    def __init__(
        self,
        *,
        provider=None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        fallback_provider=None,
    ) -> None:
        self.provider = provider
        self.max_retries = max_retries
        self.fallback_provider = fallback_provider or MockCampaignNarrativeProvider()

    def narrate(self, context: NarrativeContext) -> RuntimeResult:
        started = time.monotonic()
        provider = self.provider or get_campaign_provider()

        metadata = {
            "generation_id": str(uuid.uuid4()),
            "provider": getattr(provider, "provider", "unknown"),
            "provider_model": getattr(provider, "provider_model", "unknown"),
            "template_version": NARRATIVE_TEMPLATE_VERSION,
            "retry_count": 0,
            "used_fallback": False,
            "context_stats": context_stats(context),
        }

        # 1. Provider call with bounded retry on transient failures.
        output = self._call_with_retry(provider, context, metadata)
        if output is None:
            metadata["latency_ms"] = int((time.monotonic() - started) * 1000)
            metadata["validation_outcome"] = "provider_failure"
            return RuntimeResult(
                output=None,
                failure=metadata.get("error") or "Narrative provider failed.",
                validation=None,
                metadata=metadata,
                used_fallback=False,
            )

        # 2. Deterministic validation.
        validation = validate_narrative(context, output)
        metadata["validation_outcome"] = validation.verdict

        # 3. Retry with correction instructions when validation is recoverable.
        attempt = 0
        while validation.verdict == "retry" and attempt < self.max_retries:
            attempt += 1
            context.corrections.append(
                validation.correction or "Rephrase without asserting undeclared facts."
            )
            retried = self._call_with_retry(provider, context, metadata)
            if retried is None:
                break
            validation = validate_narrative(context, retried)
            output = retried
            metadata["retry_count"] = attempt
            metadata["validation_outcome"] = validation.verdict

        # 4. Fallback to the deterministic mock on validation exhaustion/block.
        if validation.verdict in ("retry", "block"):
            fallback = self.fallback_provider.narrate(context)
            fallback_validation = validate_narrative(context, fallback)
            metadata["used_fallback"] = True
            metadata["validation_outcome"] = fallback_validation.verdict
            metadata["latency_ms"] = int((time.monotonic() - started) * 1000)
            metadata["fallback_reason"] = validation.verdict
            return RuntimeResult(
                output=fallback,
                failure=None,
                validation=fallback_validation,
                metadata=metadata,
                used_fallback=True,
            )

        metadata["latency_ms"] = int((time.monotonic() - started) * 1000)
        return RuntimeResult(
            output=output,
            failure=None,
            validation=validation,
            metadata=metadata,
            used_fallback=False,
        )

    def _call_with_retry(self, provider, context, metadata) -> NarrativeOutput | None:
        attempt = 0
        last_error = None
        while attempt <= self.max_retries:
            try:
                return provider.narrate(context)
            except Exception as exc:  # noqa: BLE001 - any provider failure is contained
                last_error = str(exc)
                attempt += 1
        metadata["error"] = last_error
        metadata["retry_count"] = attempt - 1
        return None


def narrate_context(
    context: NarrativeContext,
    *,
    provider=None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> RuntimeResult:
    """Convenience wrapper used by the orchestrator and tests."""
    return NarrativeRuntime(provider=provider, max_retries=max_retries).narrate(context)
