# backend/app/comfyui/__init__.py
"""
ComfyUI rendering integration for SoulSmith portrait generation.

Exposes the client, workflow loader/binder, and candidate image storage as a
small, dependency-light adapter layer. SoulSmith game models remain unaware of
ComfyUI concepts; this package translates SoulSmith notions (prompt, seed,
filename) into ComfyUI API-format workflow nodes.
"""

from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.storage import (
    CandidateImageStore,
    ChronicleImageStore,
    get_asset_root,
    resolve_asset_path,
    sanitize_filename,
)
from app.comfyui.workflow_binder import (
    BindingTarget,
    WorkflowBinder,
    DEFAULT_PORTRAIT_BINDINGS,
    REFERENCE_PORTRAIT_BINDINGS,
)
from app.comfyui.workflow_loader import (
    load_workflow,
    resolve_workflow_path,
    validate_workflow,
)
from app.comfyui.workflow_roles import (
    CHRONICLE_PAINTING_ROLE,
    ENVIRONMENT_INITIAL_ROLE,
    ENVIRONMENT_REFERENCE_ROLE,
    INITIAL_ROLE,
    OBJECT_INITIAL_ROLE,
    OBJECT_REFERENCE_ROLE,
    REFERENCE_ROLE,
    requires_reference,
    requires_world_reference,
    select_workflow_role,
    select_world_workflow_role,
)

__all__ = [
    "ComfyUIClient",
    "extract_output_images",
    "CandidateImageStore",
    "ChronicleImageStore",
    "get_asset_root",
    "resolve_asset_path",
    "sanitize_filename",
    "BindingTarget",
    "WorkflowBinder",
    "DEFAULT_PORTRAIT_BINDINGS",
    "REFERENCE_PORTRAIT_BINDINGS",
    "load_workflow",
    "resolve_workflow_path",
    "validate_workflow",
    "INITIAL_ROLE",
    "REFERENCE_ROLE",
    "requires_reference",
    "select_workflow_role",
    "CHRONICLE_PAINTING_ROLE",
    "ENVIRONMENT_INITIAL_ROLE",
    "ENVIRONMENT_REFERENCE_ROLE",
    "OBJECT_INITIAL_ROLE",
    "OBJECT_REFERENCE_ROLE",
    "requires_world_reference",
    "select_world_workflow_role",
]
