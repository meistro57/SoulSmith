# backend/app/comfyui/workflow_binder.py
"""
Maps SoulSmith concepts to ComfyUI node inputs and mutates a deep copy of a
workflow. Keeps node-id knowledge isolated so different workflows can be bound
later (reference-image, chronicle-painting, relic-card, etc.) without scattering
brittle index logic through the provider.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel

from app.comfyui.errors import WorkflowBindingError


class BindingTarget(BaseModel):
    """A single (node id, input name) location inside a workflow."""

    node_id: str
    input_name: str


#: Default bindings for the bundled ``portrait_initial_v1_api.json`` workflow.
#:
#: - ``positive_prompt`` -> node ``6`` ``CLIPTextEncode.inputs.text``
#: - ``negative_prompt`` -> node ``7`` ``CLIPTextEncode.inputs.text``
#: - ``seed``            -> node ``10`` ``KSampler.inputs.seed``
#: - ``filename_prefix`` -> node ``24`` ``SaveImage.inputs.filename_prefix``
DEFAULT_PORTRAIT_BINDINGS: dict[str, BindingTarget] = {
    "positive_prompt": BindingTarget(node_id="6", input_name="text"),
    "negative_prompt": BindingTarget(node_id="7", input_name="text"),
    "seed": BindingTarget(node_id="10", input_name="seed"),
    "filename_prefix": BindingTarget(node_id="24", input_name="filename_prefix"),
}

#: Bindings for the bundled ``portrait_reference_v1_api.json`` workflow. Identical
#: to the initial bindings plus:
#:
#: - ``reference_image`` -> node ``11`` ``LoadImage.inputs.image``
#: - ``denoise``         -> node ``10`` ``KSampler.inputs.denoise``
#:
#: ``denoise`` is how SoulSmith's reference-strength setting is expressed: a
#: higher reference strength maps to a lower denoise (stronger identity
#: preservation), so this is the Phase 2 reference-image continuity extension.
REFERENCE_PORTRAIT_BINDINGS: dict[str, BindingTarget] = {
    **DEFAULT_PORTRAIT_BINDINGS,
    "reference_image": BindingTarget(node_id="11", input_name="image"),
    "denoise": BindingTarget(node_id="10", input_name="denoise"),
}


class WorkflowBinder:
    """Applies a set of concept bindings to a workflow, returning a new dict."""

    def __init__(self, bindings: dict[str, BindingTarget] | None = None) -> None:
        self._bindings: dict[str, BindingTarget] = dict(
            bindings if bindings is not None else DEFAULT_PORTRAIT_BINDINGS
        )

    @property
    def bindings(self) -> dict[str, BindingTarget]:
        return dict(self._bindings)

    def bind(self, workflow: dict[str, Any], **values: Any) -> dict[str, Any]:
        """
        Return a deep copy of ``workflow`` with known inputs overwritten.

        Only concepts present in ``values`` are applied; unspecified concepts are
        left untouched so unrelated workflow nodes are preserved verbatim.
        """
        result = deepcopy(workflow)
        for concept, target in self._bindings.items():
            if concept not in values:
                continue
            self._set_input(result, target, values[concept], concept)
        return result

    @staticmethod
    def _set_input(
        workflow: dict[str, Any],
        target: BindingTarget,
        value: Any,
        concept: str,
    ) -> None:
        node = workflow.get(target.node_id)
        if not isinstance(node, dict):
            raise WorkflowBindingError(
                f"Binding '{concept}' references missing node '{target.node_id}'"
            )
        inputs = node.get("inputs")
        if not isinstance(inputs, dict) or target.input_name not in inputs:
            raise WorkflowBindingError(
                f"Binding '{concept}' references missing input "
                f"'{target.node_id}.inputs.{target.input_name}'"
            )
        inputs[target.input_name] = value
