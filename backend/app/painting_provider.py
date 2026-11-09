# backend/app/painting_provider.py
"""
Chronicle Painting image provider abstraction.

Extends the existing ComfyUI architecture (``app/comfyui/*``) rather than
introducing a second client. Providers return image *bytes*; the orchestration
pipeline owns quarantine/promotion so unreviewed output can never be served as a
normal player-visible asset. Providers also report honest capability levels so
multi-identity limitations degrade gracefully instead of pretending ordinary
img2img preserves many faces.
"""

from __future__ import annotations

import os
import secrets
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel

from app.chronicle_paintings import ProviderCapabilitiesModel
from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.errors import ComfyUIOutputMissing
from app.comfyui.workflow_binder import DEFAULT_PORTRAIT_BINDINGS, WorkflowBinder
from app.comfyui.workflow_loader import load_workflow, resolve_workflow_path


class PaintingGenerationRequest(BaseModel):
    painting_id: str
    memory_object_id: str
    compiled_prompt: str
    negative_prompt: str | None = None
    seed: int | None = None
    reference_image_url: str | None = None


class PaintingGenerationResult(BaseModel):
    success: bool
    image_bytes: bytes | None = None
    provider: str = "mock"
    provider_model: str | None = None
    provider_request_id: str | None = None
    generation_seed: int | None = None
    failure_reason: str | None = None


class PaintingImageProvider(ABC):
    @abstractmethod
    def generate(self, request: PaintingGenerationRequest) -> PaintingGenerationResult:
        """Generate a Chronicle Painting candidate representation."""

    @abstractmethod
    def capabilities(self) -> ProviderCapabilitiesModel:
        """Report the provider's actual visual capabilities."""


def _deterministic_png(painting_id: str, seed: int) -> bytes:
    """Deterministic minimal PNG bytes for mock mode (no GPU/network)."""
    # A tiny 1x1 PNG whose byte payload varies with the seed so the file is
    # stable and non-empty without requiring an image library.
    marker = f"SoulSmith-Chronicle-{painting_id}-{seed}".encode()
    header = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000a49444154789c6360000002000100"
    )
    return header + marker


class MockPaintingImageProvider(PaintingImageProvider):
    """Deterministic mock provider requiring no external services."""

    PROVIDER = "mock"
    PROVIDER_MODEL = "soulsmith-mock-chronicle-v1"

    def generate(self, request: PaintingGenerationRequest) -> PaintingGenerationResult:
        seed = (
            request.seed
            if request.seed is not None
            else (abs(hash(request.painting_id)) % 1000000)
        )
        return PaintingGenerationResult(
            success=True,
            image_bytes=_deterministic_png(request.painting_id, seed),
            provider=self.PROVIDER,
            provider_model=self.PROVIDER_MODEL,
            provider_request_id=f"mock_req_{request.painting_id[:8]}",
            generation_seed=seed,
        )

    def capabilities(self) -> ProviderCapabilitiesModel:
        return ProviderCapabilitiesModel(
            provider=self.PROVIDER,
            text_to_image=True,
            single_reference=True,
            multiple_references=False,
            identity_conditioning=False,
            regional_conditioning=False,
            deterministic_seed=True,
            aspect_ratio_control=False,
        )


class ComfyUIChroniclePaintingProvider(PaintingImageProvider):
    """
    Renders Chronicle Painting scenes through the existing ComfyUI client.

    v1 is text-to-image only. Multi-participant identity preservation is not yet
    supported; the compiled scene prompt encodes historical appearance textually
    and the provider reports ``multiple_references=False`` so callers degrade
    honestly instead of pretending img2img preserves many identities.
    """

    PROVIDER = "comfyui"
    PROVIDER_MODEL = "soulsmith-comfyui-chronicle-painting-v1"

    def __init__(
        self,
        *,
        server_url: str,
        workflow_path: str,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 1.0,
        bindings: dict | None = None,
        client: ComfyUIClient | None = None,
    ) -> None:
        self._workflow_path = workflow_path
        self._client = client or ComfyUIClient(
            server_url,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        self._binder = WorkflowBinder(bindings or DEFAULT_PORTRAIT_BINDINGS)

    @classmethod
    def from_env(cls) -> ComfyUIChroniclePaintingProvider:
        server_url = os.environ.get("COMFYUI_SERVER_URL", "http://127.0.0.1:8188")
        workflow_ref = os.environ.get(
            "COMFYUI_CHRONICLE_PAINTING_WORKFLOW", "chronicle_painting_v1_api.json"
        )
        timeout_seconds = float(os.environ.get("COMFYUI_TIMEOUT_SECONDS", "180"))
        poll_interval_seconds = float(
            os.environ.get("COMFYUI_POLL_INTERVAL_SECONDS", "1")
        )
        return cls(
            server_url=server_url,
            workflow_path=str(resolve_workflow_path(workflow_ref)),
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    def generate(self, request: PaintingGenerationRequest) -> PaintingGenerationResult:
        try:
            workflow = load_workflow(Path(self._workflow_path))
            seed = (
                request.seed if request.seed is not None else secrets.randbelow(2**31)
            )
            bound = self._binder.bind(
                workflow,
                positive_prompt=request.compiled_prompt,
                negative_prompt=request.negative_prompt or "",
                seed=seed,
                filename_prefix=f"soulsmith_chronicle_{request.painting_id[:16]}",
            )
            prompt_id = self._client.submit_workflow(bound)
            history = self._client.wait_for_completion(prompt_id)
            images = extract_output_images(history)
            if not images:
                raise ComfyUIOutputMissing(
                    f"ComfyUI prompt '{prompt_id}' completed without an output image"
                )
            image_bytes = self._client.download_image(images[0])
            return PaintingGenerationResult(
                success=True,
                image_bytes=image_bytes,
                provider=self.PROVIDER,
                provider_model=self.PROVIDER_MODEL,
                provider_request_id=prompt_id,
                generation_seed=seed,
            )
        except Exception as exc:  # noqa: BLE001 - convert any rendering failure into a clean result
            return PaintingGenerationResult(
                success=False,
                provider=self.PROVIDER,
                provider_model=self.PROVIDER_MODEL,
                failure_reason=str(exc) or exc.__class__.__name__,
            )

    def capabilities(self) -> ProviderCapabilitiesModel:
        return ProviderCapabilitiesModel(
            provider=self.PROVIDER,
            text_to_image=True,
            single_reference=True,
            multiple_references=False,
            identity_conditioning=False,
            regional_conditioning=False,
            deterministic_seed=True,
            aspect_ratio_control=False,
        )


def get_painting_provider(
    provider_type: str | None = None,
) -> PaintingImageProvider:
    selected = provider_type or os.environ.get("SOULSMITH_IMAGE_PROVIDER", "mock")
    if selected == "comfyui":
        return ComfyUIChroniclePaintingProvider.from_env()
    return MockPaintingImageProvider()
