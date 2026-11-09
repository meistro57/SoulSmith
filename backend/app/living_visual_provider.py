# backend/app/living_visual_provider.py
"""
SoulSmith Phase 21: unified living-visual provider runtime.

This is a *thin* runtime over the existing ``app.comfyui`` client/workflow
stack. It does not introduce a second image-generation stack; it maps a
``VisualJobType`` to a workflow role and delegates submit/poll/download to the
same ``ComfyUIClient``, ``WorkflowBinder``, and workflow files used by the
portrait/chronicle/world providers.

Providers return image *bytes*. The runtime owns quarantine/promotion so
unreviewed output can never be served as a normal player-visible asset.
A deterministic mock keeps the whole loop testable without GPU or internet.
"""

from __future__ import annotations

import os
import secrets
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.errors import ComfyUIError, ComfyUIOutputMissing
from app.comfyui.storage import CandidateImageStore, resolve_asset_path
from app.comfyui.workflow_binder import REFERENCE_PORTRAIT_BINDINGS, WorkflowBinder
from app.comfyui.workflow_loader import load_workflow, resolve_workflow_path
from app.living_visual_compiler import VisualJobType

# Workflow-role selection for living visual jobs. Domain/campaign code never
# sees ComfyUI node IDs; only this provider adapter knows role -> workflow.
PORTRAIT_INITIAL_ROLE = "portrait_initial"
PORTRAIT_REFERENCE_ROLE = "portrait_reference"
CHRONICLE_ROLE = "chronicle_painting"
OBJECT_INITIAL_ROLE = "object_initial"
ENVIRONMENT_INITIAL_ROLE = "environment_initial"

#: Which visual types are continuity updates requiring a locked reference.
_REFERENCE_TYPES: frozenset[str] = frozenset({"portrait_continuity"})

_VISUAL_TYPE_ROLE: dict[VisualJobType, str] = {
    "portrait": PORTRAIT_INITIAL_ROLE,
    "portrait_continuity": PORTRAIT_REFERENCE_ROLE,
    "memory_object": CHRONICLE_ROLE,
    "chronicle_painting": CHRONICLE_ROLE,
    "relic": OBJECT_INITIAL_ROLE,
    "relationship": ENVIRONMENT_INITIAL_ROLE,
    "group_memory": ENVIRONMENT_INITIAL_ROLE,
    "legendary_figure": ENVIRONMENT_INITIAL_ROLE,
    "world_memory": ENVIRONMENT_INITIAL_ROLE,
    "place": ENVIRONMENT_INITIAL_ROLE,
    "environment": ENVIRONMENT_INITIAL_ROLE,
}

_PROVIDER_MODEL_BY_ROLE: dict[str, str] = {
    PORTRAIT_INITIAL_ROLE: "soulsmith-comfyui-portrait-initial-v1",
    PORTRAIT_REFERENCE_ROLE: "soulsmith-comfyui-portrait-reference-v1",
    CHRONICLE_ROLE: "soulsmith-comfyui-chronicle-painting-v1",
    OBJECT_INITIAL_ROLE: "soulsmith-comfyui-object-initial-v1",
    ENVIRONMENT_INITIAL_ROLE: "soulsmith-comfyui-environment-initial-v1",
}


def workflow_role_for(visual_type: VisualJobType) -> str:
    return _VISUAL_TYPE_ROLE.get(visual_type, ENVIRONMENT_INITIAL_ROLE)


def requires_reference(visual_type: VisualJobType) -> bool:
    return visual_type in _REFERENCE_TYPES


class VisualJobGenerationRequest(BaseModel):
    job_id: str
    visual_type: VisualJobType
    compiled_prompt: str
    negative_prompt: str | None = None
    reference_image_url: str | None = None
    seed: int | None = None


class VisualJobGenerationResult(BaseModel):
    success: bool
    image_bytes: bytes | None = None
    provider: str = "mock"
    provider_model: str | None = None
    workflow_role: str | None = None
    workflow_version: str = "1.0.0"
    provider_request_id: str | None = None
    generation_seed: int | None = None
    failure_reason: str | None = None


class LivingVisualProvider(ABC):
    @abstractmethod
    def generate(
        self, request: VisualJobGenerationRequest
    ) -> VisualJobGenerationResult:
        """Generate an image candidate for a visual job."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Report provider capabilities without exposing secrets."""

    def status(self) -> dict[str, Any]:
        """Report provider health. The mock is always healthy."""
        return {"provider": self.capabilities()["provider"], "healthy": True}


def _deterministic_png(job_id: str, seed: int) -> bytes:
    marker = f"SoulSmith-LivingVisual-{job_id}-{seed}".encode()
    header = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000a49444154789c6360000002000100"
    )
    return header + marker


class MockLivingVisualProvider(LivingVisualProvider):
    PROVIDER = "mock"

    def generate(
        self, request: VisualJobGenerationRequest
    ) -> VisualJobGenerationResult:
        seed = (
            request.seed
            if request.seed is not None
            else (abs(hash(request.job_id)) % 1000000)
        )
        role = workflow_role_for(request.visual_type)
        return VisualJobGenerationResult(
            success=True,
            image_bytes=_deterministic_png(request.job_id, seed),
            provider=self.PROVIDER,
            provider_model=f"soulsmith-mock-{role}-v1",
            workflow_role=role,
            workflow_version="1.0.0",
            provider_request_id=f"mock_req_{request.job_id[:8]}",
            generation_seed=seed,
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.PROVIDER,
            "text_to_image": True,
            "single_reference": True,
            "multiple_references": False,
            "identity_conditioning": False,
            "deterministic_seed": True,
            "async": False,
        }


class ComfyUILivingVisualProvider(LivingVisualProvider):
    PROVIDER = "comfyui"

    def __init__(
        self,
        *,
        server_url: str,
        workflow_paths: dict[str, str],
        reference_strength: float = 0.75,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 1.0,
        bindings: dict | None = None,
        reference_bindings: dict | None = None,
        asset_root: str | None = None,
        client: ComfyUIClient | None = None,
    ) -> None:
        self._workflow_paths = workflow_paths
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
    def from_env(cls) -> ComfyUILivingVisualProvider:
        server_url = os.environ.get("COMFYUI_SERVER_URL", "http://127.0.0.1:8188")
        timeout_seconds = float(os.environ.get("COMFYUI_TIMEOUT_SECONDS", "180"))
        poll_interval_seconds = float(
            os.environ.get("COMFYUI_POLL_INTERVAL_SECONDS", "1")
        )
        reference_strength = float(
            os.environ.get("COMFYUI_PORTRAIT_REFERENCE_STRENGTH", "0.75")
        )
        workflow_paths = {
            PORTRAIT_INITIAL_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_PORTRAIT_INITIAL_WORKFLOW",
                        os.environ.get(
                            "COMFYUI_PORTRAIT_WORKFLOW", "portrait_initial_v1_api.json"
                        ),
                    )
                )
            ),
            PORTRAIT_REFERENCE_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_PORTRAIT_REFERENCE_WORKFLOW",
                        os.environ.get(
                            "COMFYUI_REFERENCE_WORKFLOW",
                            "portrait_reference_v1_api.json",
                        ),
                    )
                )
            ),
            CHRONICLE_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_CHRONICLE_PAINTING_WORKFLOW",
                        "chronicle_painting_v1_api.json",
                    )
                )
            ),
            OBJECT_INITIAL_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_OBJECT_INITIAL_WORKFLOW", "object_initial_v1_api.json"
                    )
                )
            ),
            ENVIRONMENT_INITIAL_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_ENVIRONMENT_INITIAL_WORKFLOW",
                        "environment_initial_v1_api.json",
                    )
                )
            ),
        }
        return cls(
            server_url=server_url,
            workflow_paths=workflow_paths,
            reference_strength=reference_strength,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    def generate(
        self, request: VisualJobGenerationRequest
    ) -> VisualJobGenerationResult:
        try:
            role = workflow_role_for(request.visual_type)
            workflow_path = self._workflow_paths.get(role)
            if not workflow_path:
                raise ComfyUIError(f"No workflow configured for role '{role}'")
            workflow = load_workflow(Path(workflow_path))
            seed = (
                request.seed if request.seed is not None else secrets.randbelow(2**31)
            )
            from app.comfyui.storage import sanitize_filename

            filename_prefix = f"soulsmith_{sanitize_filename(request.job_id)}"

            if role == PORTRAIT_REFERENCE_ROLE:
                if not request.reference_image_url:
                    raise ComfyUIOutputMissing(
                        "Continuity generation requires a locked source reference"
                    )
                reference_image = self._resolve_reference_image(request)
                denoise = round(1.0 - self._reference_strength, 4)
                bound = self._reference_binder.bind(
                    workflow,
                    positive_prompt=request.compiled_prompt,
                    negative_prompt=request.negative_prompt or "",
                    seed=seed,
                    filename_prefix=filename_prefix,
                    reference_image=reference_image,
                    denoise=denoise,
                )
            else:
                bound = self._binder.bind(
                    workflow,
                    positive_prompt=request.compiled_prompt,
                    negative_prompt=request.negative_prompt or "",
                    seed=seed,
                    filename_prefix=filename_prefix,
                )

            prompt_id = self._client.submit_workflow(bound)
            history = self._client.wait_for_completion(prompt_id)
            images = extract_output_images(history)
            if not images:
                raise ComfyUIOutputMissing(
                    f"ComfyUI prompt '{prompt_id}' completed without an output image"
                )
            image_bytes = self._client.download_image(images[0])
            return VisualJobGenerationResult(
                success=True,
                image_bytes=image_bytes,
                provider=self.PROVIDER,
                provider_model=_PROVIDER_MODEL_BY_ROLE.get(role),
                workflow_role=role,
                workflow_version="1.0.0",
                provider_request_id=prompt_id,
                generation_seed=seed,
            )
        except Exception as exc:  # noqa: BLE001 - convert any failure into a clean result
            return VisualJobGenerationResult(
                success=False,
                provider=self.PROVIDER,
                provider_model=_PROVIDER_MODEL_BY_ROLE.get(
                    workflow_role_for(request.visual_type)
                ),
                workflow_role=workflow_role_for(request.visual_type),
                failure_reason=str(exc) or exc.__class__.__name__,
            )

    def _resolve_reference_image(self, request: VisualJobGenerationRequest) -> str:
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

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.PROVIDER,
            "text_to_image": True,
            "single_reference": True,
            "multiple_references": False,
            "identity_conditioning": False,
            "deterministic_seed": True,
            "async": False,
        }

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.PROVIDER,
            "healthy": self._client.health_check(),
            "workflows_available": {
                role: self._workflow_available(path)
                for role, path in self._workflow_paths.items()
            },
            "output_storage_writable": self._store.is_writable(),
        }

    @staticmethod
    def _workflow_available(path: str) -> bool:
        try:
            load_workflow(Path(path))
            return True
        except ComfyUIError:
            return False


def get_living_visual_provider(
    provider_type: str | None = None,
) -> LivingVisualProvider:
    selected = provider_type or os.environ.get("SOULSMITH_IMAGE_PROVIDER", "mock")
    if selected == "comfyui":
        return ComfyUILivingVisualProvider.from_env()
    return MockLivingVisualProvider()


def get_living_visual_status() -> dict[str, Any]:
    """Authorized diagnostics for the living-visual provider runtime."""
    provider = get_living_visual_provider()
    return {
        "status": provider.status(),
        "capabilities": provider.capabilities(),
        "workflow_roles": dict(_VISUAL_TYPE_ROLE),
    }
