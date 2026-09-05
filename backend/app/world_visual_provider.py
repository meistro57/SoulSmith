# backend/app/world_visual_provider.py
"""
Phase 4: provider abstraction for world-entity visual generation.

Mirrors :mod:`app.portrait_provider` but renders locations, relics, and
phenomena through ComfyUI workflow roles (environment/object, initial/reference).
Generated images are owned by SoulSmith and never become canonical automatically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
import secrets
from typing import Dict, Optional

from pydantic import BaseModel

from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.errors import ComfyUIError, ComfyUIOutputMissing
from app.comfyui.storage import (
    CandidateImageStore,
    resolve_asset_path,
    sanitize_filename,
)
from app.comfyui.workflow_binder import (
    DEFAULT_PORTRAIT_BINDINGS,
    REFERENCE_PORTRAIT_BINDINGS,
    WorkflowBinder,
)
from app.comfyui.workflow_loader import load_workflow, resolve_workflow_path
from app.comfyui.workflow_roles import (
    ENVIRONMENT_INITIAL_ROLE,
    ENVIRONMENT_REFERENCE_ROLE,
    OBJECT_INITIAL_ROLE,
    OBJECT_REFERENCE_ROLE,
)


class WorldVisualGenerationRequest(BaseModel):
    candidate_id: str
    entity_id: str
    entity_type: str
    compiled_prompt: str
    workflow_role: str
    generation_type: str = "initial"
    negative_prompt: Optional[str] = None
    reference_image_url: Optional[str] = None
    seed: Optional[int] = None


class WorldVisualGenerationResult(BaseModel):
    success: bool
    generated_image_url: Optional[str] = None
    provider: str = "comfyui"
    provider_model: str = "soulsmith-comfyui-world-v1"
    provider_request_id: Optional[str] = None
    generation_seed: Optional[int] = None
    failure_reason: Optional[str] = None


class WorldVisualProvider(ABC):
    @abstractmethod
    def generate(
        self, request: WorldVisualGenerationRequest
    ) -> WorldVisualGenerationResult:
        """Generate a world-entity visual candidate."""
        pass


class MockWorldVisualProvider(WorldVisualProvider):
    def generate(
        self, request: WorldVisualGenerationRequest
    ) -> WorldVisualGenerationResult:
        seed = (
            request.seed
            if request.seed is not None
            else (abs(hash(request.candidate_id)) % 1000000)
        )
        return WorldVisualGenerationResult(
            success=True,
            generated_image_url=(
                f"/assets/world/{request.entity_type}/candidates/"
                f"candidate_{request.candidate_id}.png"
            ),
            provider="mock",
            provider_model="soulsmith-mock-world-v1",
            provider_request_id=f"mock_req_{request.candidate_id[:8]}",
            generation_seed=seed,
        )


class ComfyUIWorldVisualProvider(WorldVisualProvider):
    PROVIDER = "comfyui"

    def __init__(
        self,
        *,
        server_url: str,
        workflow_paths: Dict[str, str],
        reference_strength: float = 0.6,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 1.0,
        asset_root: Optional[str] = None,
        client: Optional[ComfyUIClient] = None,
    ) -> None:
        self._workflow_paths = workflow_paths
        self._reference_strength = min(max(reference_strength, 0.0), 1.0)
        self._client = client or ComfyUIClient(
            server_url,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        self._binder = WorkflowBinder(DEFAULT_PORTRAIT_BINDINGS)
        self._reference_binder = WorkflowBinder(REFERENCE_PORTRAIT_BINDINGS)
        self._store = CandidateImageStore(
            None if asset_root is None else Path(asset_root)
        )

    @classmethod
    def from_env(cls) -> "ComfyUIWorldVisualProvider":
        server_url = os.environ.get("COMFYUI_SERVER_URL", "http://127.0.0.1:8188")
        workflow_paths = {
            ENVIRONMENT_INITIAL_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_ENVIRONMENT_INITIAL_WORKFLOW",
                        "environment_initial_v1_api.json",
                    )
                )
            ),
            ENVIRONMENT_REFERENCE_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_ENVIRONMENT_REFERENCE_WORKFLOW",
                        "environment_reference_v1_api.json",
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
            OBJECT_REFERENCE_ROLE: str(
                resolve_workflow_path(
                    os.environ.get(
                        "COMFYUI_OBJECT_REFERENCE_WORKFLOW",
                        "object_reference_v1_api.json",
                    )
                )
            ),
        }
        timeout_seconds = float(os.environ.get("COMFYUI_TIMEOUT_SECONDS", "180"))
        poll_interval_seconds = float(
            os.environ.get("COMFYUI_POLL_INTERVAL_SECONDS", "1")
        )
        reference_strength = float(
            os.environ.get("COMFYUI_WORLD_REFERENCE_STRENGTH", "0.6")
        )
        return cls(
            server_url=server_url,
            workflow_paths=workflow_paths,
            reference_strength=reference_strength,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    def generate(
        self, request: WorldVisualGenerationRequest
    ) -> WorldVisualGenerationResult:
        try:
            role = request.workflow_role
            workflow_path = self._workflow_paths.get(role)
            if not workflow_path:
                raise ComfyUIError(f"No workflow configured for role '{role}'")

            workflow = load_workflow(Path(workflow_path))
            seed = (
                request.seed if request.seed is not None else secrets.randbelow(2**31)
            )
            filename_prefix = f"soulsmith_{sanitize_filename(request.candidate_id)}"

            if role.endswith("_reference"):
                if not request.reference_image_url:
                    raise ComfyUIOutputMissing(
                        f"Continuity generation '{request.generation_type}' requires a "
                        "source visual version"
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
            subdir = Path("world") / request.entity_type / "candidates"
            generated_image_url = self._store.save_in_subdir(
                subdir, f"candidate_{request.candidate_id}", image_bytes
            )

            return WorldVisualGenerationResult(
                success=True,
                generated_image_url=generated_image_url,
                provider=self.PROVIDER,
                provider_model=f"soulsmith-comfyui-{role}",
                provider_request_id=prompt_id,
                generation_seed=seed,
            )
        except Exception as exc:  # convert any rendering failure into a clean result
            return WorldVisualGenerationResult(
                success=False,
                provider=self.PROVIDER,
                provider_model=f"soulsmith-comfyui-{request.workflow_role}",
                failure_reason=str(exc) or exc.__class__.__name__,
            )

    def _resolve_reference_image(self, request: WorldVisualGenerationRequest) -> str:
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


def get_world_visual_provider(
    provider_type: Optional[str] = None,
) -> WorldVisualProvider:
    selected = provider_type or os.environ.get("SOULSMITH_IMAGE_PROVIDER", "mock")
    if selected == "comfyui":
        return ComfyUIWorldVisualProvider.from_env()
    return MockWorldVisualProvider()
