# backend/app/comfyui/errors.py
"""
Typed exception hierarchy for the ComfyUI rendering layer.

Expected failures surface as subclasses of :class:`ComfyUIError` so the portrait
provider can convert them into clean ``ProviderGenerationResult(success=False)``
objects without leaking stack traces into the Visual Memory workflow.
"""

from __future__ import annotations


class ComfyUIError(Exception):
    """Base error for any expected ComfyUI rendering failure."""


class ComfyUIUnavailable(ComfyUIError):
    """The ComfyUI server could not be reached or returned a transport error."""


class ComfyUITimeout(ComfyUIError):
    """A submitted workflow did not finish within the configured timeout."""


class ComfyUIWorkflowRejected(ComfyUIError):
    """ComfyUI rejected the submitted workflow or reported node errors."""


class ComfyUIGenerationFailed(ComfyUIError):
    """ComfyUI executed the workflow but reported an error status."""


class ComfyUIOutputMissing(ComfyUIError):
    """The completed workflow produced no retrievable output image."""


class ComfyUIDownloadFailed(ComfyUIError):
    """The generated image could not be downloaded from ComfyUI."""


class WorkflowLoadError(ComfyUIError):
    """The workflow file is missing, malformed, or not API-format JSON."""


class WorkflowBindingError(ComfyUIError):
    """A SoulSmith concept maps to a node/input that does not exist in the workflow."""
