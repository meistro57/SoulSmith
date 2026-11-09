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
    DEFAULT_PORTRAIT_BINDINGS,
    REFERENCE_PORTRAIT_BINDINGS,
    BindingTarget,
    WorkflowBinder,
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
    "CHRONICLE_PAINTING_ROLE",
    "DEFAULT_PORTRAIT_BINDINGS",
    "ENVIRONMENT_INITIAL_ROLE",
    "ENVIRONMENT_REFERENCE_ROLE",
    "INITIAL_ROLE",
    "OBJECT_INITIAL_ROLE",
    "OBJECT_REFERENCE_ROLE",
    "REFERENCE_PORTRAIT_BINDINGS",
    "REFERENCE_ROLE",
    "BindingTarget",
    "CandidateImageStore",
    "ChronicleImageStore",
    "ComfyUIClient",
    "WorkflowBinder",
    "extract_output_images",
    "get_asset_root",
    "load_workflow",
    "requires_reference",
    "requires_world_reference",
    "resolve_asset_path",
    "resolve_workflow_path",
    "sanitize_filename",
    "select_workflow_role",
    "select_world_workflow_role",
    "validate_workflow",
]
