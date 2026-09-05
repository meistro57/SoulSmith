# backend/app/comfyui/workflow_loader.py
"""
Loading and validation for static ComfyUI API-format workflow templates.

SoulSmith does not construct ComfyUI graphs dynamically. It ships static JSON
workflow files (exported in ComfyUI "API format") and mutates only a small set of
known inputs through :mod:`app.comfyui.workflow_binder`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.comfyui.errors import WorkflowLoadError

_WORKFLOWS_DIR = Path(__file__).resolve().parent / "workflows"


def resolve_workflow_path(name_or_path: str) -> Path:
    """
    Resolve a workflow reference to a concrete file path.

    Absolute paths and existing relative paths are used verbatim; a bare filename
    is resolved against the bundled ``workflows/`` directory.
    """
    candidate = Path(name_or_path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    return _WORKFLOWS_DIR / candidate.name


def load_workflow(path: Path) -> Dict[str, Any]:
    """Load and validate an API-format workflow file."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise WorkflowLoadError(f"ComfyUI workflow file not found: {path}") from exc
    except OSError as exc:
        raise WorkflowLoadError(
            f"Could not read ComfyUI workflow '{path}': {exc}"
        ) from exc

    try:
        workflow = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowLoadError(
            f"Malformed ComfyUI workflow JSON '{path}': {exc}"
        ) from exc

    return validate_workflow(workflow)


def validate_workflow(workflow: Any) -> Dict[str, Any]:
    """Validate that a parsed workflow is in ComfyUI API format."""
    if not isinstance(workflow, dict):
        raise WorkflowLoadError("Workflow must be a JSON object of node_id -> node")

    # UI-format exports carry top-level "nodes"/"links" arrays instead.
    if "nodes" in workflow or "links" in workflow:
        raise WorkflowLoadError(
            "Workflow appears to be in UI format. Export it in ComfyUI 'API format' "
            "instead (a top-level map of node id -> {class_type, inputs})."
        )

    for node_id, node in workflow.items():
        if (
            not isinstance(node, dict)
            or "class_type" not in node
            or "inputs" not in node
        ):
            raise WorkflowLoadError(
                f"Workflow node '{node_id}' is missing 'class_type' or 'inputs'"
            )
    return workflow
