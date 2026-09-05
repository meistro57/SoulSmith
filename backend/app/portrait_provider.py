# backend/app/portrait_provider.py
"""
SoulSmith Image Provider Abstraction for Portrait Generation.
Provides mock, external, and ComfyUI provider adapters for candidate portrait
synthesis without mutating canonical character state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
import secrets
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.errors import ComfyUIError, ComfyUIOutputMissing
from app.comfyui.storage import (
    CandidateImageStore,
    resolve_asset_path,
    sanitize_filename,
)
from app.comfyui.workflow_binder import (
    REFERENCE_PORTRAIT_BINDINGS,
    WorkflowBinder,
)
from app.comfyui.workflow_loader import load_workflow, resolve_workflow_path
from app.comfyui.workflow_roles import REFERENCE_ROLE, select_workflow_role


class ProviderGenerationRequest(BaseModel):
    candidate_id: str
    soul_id: str
    compiled_prompt: str
    generation_type: str = "initial"
    reference_image_url: Optional[str] = None
    negative_prompt: Optional[str] = None
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


class ComfyUIPortraitImageProvider(PortraitImageProvider):
    """
    Renders compiled SoulSmith portrait prompts through a local ComfyUI instance.

    The provider owns no identity/continuity logic: a workflow-role selector picks
    the initial (text-to-image) or reference (img2img continuity) workflow, the
    binder injects the compiled prompt, negative prompt, seed, filename prefix,
    reference image, and reference strength, then the provider polls for completion
    and archives the resulting PNG into SoulSmith-owned storage.
    """

    PROVIDER = "comfyui"
    PROVIDER_MODEL_INITIAL = "soulsmith-comfyui-portrait-initial-v1"
    PROVIDER_MODEL_REFERENCE = "soulsmith-comfyui-portrait-reference-v1"

    def __init__(
        self,
        *,
        server_url: str,
        initial_workflow_path: str,
        reference_workflow_path: Optional[str] = None,
        reference_strength: float = 0.75,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 1.0,
        bindings: Optional[dict] = None,
        reference_bindings: Optional[dict] = None,
        asset_root: Optional[str] = None,
        client: Optional[ComfyUIClient] = None,
    ) -> None:
        self._initial_workflow_path = initial_workflow_path
        self._reference_workflow_path = reference_workflow_path
        self._reference_strength = min(max(reference_strength, 0.0), 1.0)
        self._client = client or ComfyUIClient(
            server_url,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        self._binder = WorkflowBinder(bindings)
        self._reference_binder = WorkflowBinder(
            reference_bindings or REFERENCE_PORTRAIT_BINDINGS
        )
        self._store = CandidateImageStore(
            None if asset_root is None else Path(asset_root)
        )

    @classmethod
    def from_env(cls) -> "ComfyUIPortraitImageProvider":
        server_url = os.environ.get("COMFYUI_SERVER_URL", "http://127.0.0.1:8188")
        initial_ref = os.environ.get(
            "COMFYUI_PORTRAIT_INITIAL_WORKFLOW",
            os.environ.get("COMFYUI_PORTRAIT_WORKFLOW", "portrait_initial_v1_api.json"),
        )
        reference_ref = os.environ.get(
            "COMFYUI_PORTRAIT_REFERENCE_WORKFLOW",
            os.environ.get(
                "COMFYUI_REFERENCE_WORKFLOW", "portrait_reference_v1_api.json"
            ),
        )
        timeout_seconds = float(os.environ.get("COMFYUI_TIMEOUT_SECONDS", "180"))
        poll_interval_seconds = float(
            os.environ.get("COMFYUI_POLL_INTERVAL_SECONDS", "1")
        )
        reference_strength = float(
            os.environ.get("COMFYUI_PORTRAIT_REFERENCE_STRENGTH", "0.75")
        )
        return cls(
            server_url=server_url,
            initial_workflow_path=str(resolve_workflow_path(initial_ref)),
            reference_workflow_path=str(resolve_workflow_path(reference_ref)),
            reference_strength=reference_strength,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResult:
        try:
            role = select_workflow_role(request.generation_type)
            seed = (
                request.seed if request.seed is not None else secrets.randbelow(2**31)
            )
            filename_prefix = f"soulsmith_{sanitize_filename(request.candidate_id)}"

            if role == REFERENCE_ROLE:
                if not request.reference_image_url:
                    raise ComfyUIOutputMissing(
                        f"Generation type '{request.generation_type}' requires a "
                        "source portrait version for identity continuity"
                    )
                reference_image = self._resolve_reference_image(request)
                denoise = round(1.0 - self._reference_strength, 4)
                workflow = load_workflow(Path(self._reference_workflow_path))
                bound = self._reference_binder.bind(
                    workflow,
                    positive_prompt=request.compiled_prompt,
                    negative_prompt=request.negative_prompt or "",
                    seed=seed,
                    filename_prefix=filename_prefix,
                    reference_image=reference_image,
                    denoise=denoise,
                )
                provider_model = self.PROVIDER_MODEL_REFERENCE
            else:
                workflow = load_workflow(Path(self._initial_workflow_path))
                bound = self._binder.bind(
                    workflow,
                    positive_prompt=request.compiled_prompt,
                    negative_prompt=request.negative_prompt or "",
                    seed=seed,
                    filename_prefix=filename_prefix,
                )
                provider_model = self.PROVIDER_MODEL_INITIAL

            prompt_id = self._client.submit_workflow(bound)
            history = self._client.wait_for_completion(prompt_id)
            images = extract_output_images(history)
            if not images:
                raise ComfyUIOutputMissing(
                    f"ComfyUI prompt '{prompt_id}' completed without an output image"
                )

            image_bytes = self._client.download_image(images[0])
            generated_image_url = self._store.save(request.candidate_id, image_bytes)

            return ProviderGenerationResult(
                success=True,
                generated_image_url=generated_image_url,
                provider=self.PROVIDER,
                provider_model=provider_model,
                provider_request_id=prompt_id,
                generation_seed=seed,
            )
        except Exception as exc:  # convert any rendering failure into a clean result
            return ProviderGenerationResult(
                success=False,
                provider=self.PROVIDER,
                provider_model=self.PROVIDER_MODEL_INITIAL,
                failure_reason=str(exc) or exc.__class__.__name__,
            )

    def _resolve_reference_image(self, request: ProviderGenerationRequest) -> str:
        """
        Upload the candidate's reference portrait to ComfyUI and return its
        ComfyUI filename. Raises a clean error when the source image is missing.
        """
        if not request.reference_image_url:
            raise ComfyUIOutputMissing(
                "Reference image is required for continuity generation"
            )
        try:
            ref_path = resolve_asset_path(
                request.reference_image_url, self._store.asset_root
            )
        except ValueError as exc:
            raise ComfyUIOutputMissing(str(exc)) from exc
        if not ref_path.exists():
            raise ComfyUIOutputMissing(
                f"Reference image not found: {request.reference_image_url}"
            )
        return self._client.upload_image(ref_path.name, ref_path.read_bytes())

    def diagnose(self) -> Dict[str, Any]:
        """Return provider health and configuration diagnostics."""
        return {
            "provider": self.PROVIDER,
            "reachable": self._client.health_check(),
            "initial_workflow_available": self._workflow_available(
                self._initial_workflow_path
            ),
            "reference_workflow_available": (
                self._reference_workflow_path is not None
                and self._workflow_available(self._reference_workflow_path)
            ),
            "output_storage_writable": self._store.is_writable(),
        }

    @staticmethod
    def _workflow_available(path: str) -> bool:
        try:
            load_workflow(Path(path))
            return True
        except ComfyUIError:
            return False


def get_portrait_provider(provider_type: Optional[str] = None) -> PortraitImageProvider:
    selected = provider_type or os.environ.get("SOULSMITH_IMAGE_PROVIDER", "mock")
    if selected == "comfyui":
        return ComfyUIPortraitImageProvider.from_env()
    if selected == "external":
        return ExternalPortraitImageProvider()
    return MockPortraitImageProvider()


def get_comfyui_status() -> Dict[str, Any]:
    """Diagnostics for the ComfyUI portrait provider (used by the status endpoint)."""
    return ComfyUIPortraitImageProvider.from_env().diagnose()
