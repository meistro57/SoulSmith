# backend/app/portrait_provider.py
"""
SoulSmith Image Provider Abstraction for Portrait Generation.
Provides mock and external provider adapters for candidate portrait synthesis without mutating canonical character state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
import uuid
from typing import Optional
from pydantic import BaseModel


class ProviderGenerationRequest(BaseModel):
    candidate_id: str
    soul_id: str
    compiled_prompt: str
    generation_type: str = "initial"
    reference_image_url: Optional[str] = None
    seed: Optional[int] = None


class ProviderGenerationResult(BaseModel):
    success: bool
    generated_image_url: Optional[str] = None
    provider: str = "mock"
    provider_model: str = "soulsmith-mock-v1"
    provider_request_id: Optional[str] = None
    generation_seed: Optional[int] = None
    failure_reason: Optional[str] = None


class PortraitImageProvider(ABC):
    @abstractmethod
    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResult:
        """Generate a portrait candidate representation."""
        pass


class MockPortraitImageProvider(PortraitImageProvider):
    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResult:
        req_id = f"mock_req_{request.candidate_id[:8]}"
        seed = (
            request.seed
            if request.seed is not None
            else (abs(hash(request.candidate_id)) % 1000000)
        )

        # Deterministic mock image path
        image_url = f"/assets/portraits/candidates/candidate_{request.candidate_id}.png"

        return ProviderGenerationResult(
            success=True,
            generated_image_url=image_url,
            provider="mock",
            provider_model="soulsmith-mock-v1",
            provider_request_id=req_id,
            generation_seed=seed,
        )


class ExternalPortraitImageProvider(PortraitImageProvider):
    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResult:
        api_key = os.environ.get("SOULSMITH_IMAGE_PROVIDER_API_KEY")
        if not api_key:
            return ProviderGenerationResult(
                success=False,
                provider="external",
                provider_model="soulsmith-diffusion-v1",
                failure_reason="External image provider unconfigured: SOULSMITH_IMAGE_PROVIDER_API_KEY environment variable missing.",
            )

        # External provider scaffold - simulation when key present
        req_id = f"ext_req_{str(uuid.uuid4())[:8]}"
        return ProviderGenerationResult(
            success=True,
            generated_image_url=f"/assets/portraits/candidates/ext_{request.candidate_id}.png",
            provider="external",
            provider_model="soulsmith-diffusion-v1",
            provider_request_id=req_id,
            generation_seed=request.seed or 12345,
        )


def get_portrait_provider(provider_type: Optional[str] = None) -> PortraitImageProvider:
    selected = provider_type or os.environ.get("SOULSMITH_IMAGE_PROVIDER", "mock")
    if selected == "external":
        return ExternalPortraitImageProvider()
    return MockPortraitImageProvider()
