# backend/app/comfyui/client.py
"""
Thin synchronous client for the ComfyUI HTTP API.

The V1 provider is synchronous (the FastAPI generate route is a plain ``def`` and
runs in a threadpool), so this client uses ``httpx.Client`` and simple polling.
Polling is intentionally the only completion strategy in Phase 1; a job queue is
out of scope and can be introduced later without changing the public surface.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from app.comfyui.errors import (
    ComfyUIDownloadFailed,
    ComfyUIError,
    ComfyUIGenerationFailed,
    ComfyUIOutputMissing,
    ComfyUITimeout,
    ComfyUIUnavailable,
    ComfyUIWorkflowRejected,
)


def extract_output_images(history_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Collect every ``{"filename", "subfolder", "type"}`` image record produced by a
    completed workflow, scanning all node outputs.
    """
    images: list[dict[str, Any]] = []
    outputs = history_entry.get("outputs") or {}
    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        for image in node_output.get("images") or []:
            if isinstance(image, dict) and image.get("filename"):
                images.append(image)
    return images


class ComfyUIClient:
    """Minimal ComfyUI HTTP API adapter (submit, poll, download, upload)."""

    def __init__(
        self,
        server_url: str,
        *,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self._transport = transport
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            timeout = httpx.Timeout(self.timeout_seconds, connect=10.0)
            self._client = httpx.Client(
                base_url=self.server_url,
                timeout=timeout,
                transport=self._transport,
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def health_check(self) -> bool:
        """Return True when the ComfyUI server responds to a system status probe."""
        try:
            response = self._get_client().get("/system_stats")
            return response.status_code < 500
        except httpx.HTTPError:
            return False

    def submit_workflow(self, workflow: dict[str, Any]) -> str:
        """Submit an API-format workflow and return the assigned ``prompt_id``."""
        payload = {"prompt": workflow, "client_id": str(uuid.uuid4())}
        try:
            response = self._get_client().post("/prompt", json=payload)
        except httpx.HTTPError as exc:
            raise ComfyUIUnavailable(f"ComfyUI request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ComfyUIWorkflowRejected(
                f"ComfyUI rejected the workflow: {_response_error(response)}"
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise ComfyUIError("ComfyUI returned a non-JSON /prompt response") from exc

        node_errors = body.get("node_errors")
        if node_errors:
            raise ComfyUIWorkflowRejected(
                f"ComfyUI node validation failed: {node_errors}"
            )

        prompt_id = body.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError("ComfyUI /prompt response missing 'prompt_id'")
        return prompt_id

    def get_history(self, prompt_id: str) -> dict[str, Any]:
        """Fetch the raw history entry for a prompt (may be empty while pending)."""
        try:
            response = self._get_client().get(f"/history/{prompt_id}")
        except httpx.HTTPError as exc:
            raise ComfyUIUnavailable(f"ComfyUI history request failed: {exc}") from exc
        if response.status_code >= 400:
            raise ComfyUIError(
                f"ComfyUI history request failed: {_response_error(response)}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ComfyUIError("ComfyUI returned a non-JSON history response") from exc

    def wait_for_completion(self, prompt_id: str) -> dict[str, Any]:
        """Poll ``/history/{prompt_id}`` until completion, failure, or timeout."""
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            history = self.get_history(prompt_id)
            entry = history.get(prompt_id)
            if entry is not None:
                status = entry.get("status") or {}
                if status.get("status_str") == "error":
                    messages = status.get("messages") or ["unknown execution error"]
                    raise ComfyUIGenerationFailed(
                        f"ComfyUI execution failed: {messages}"
                    )
                if status.get("completed"):
                    return entry

            if time.monotonic() > deadline:
                raise ComfyUITimeout(
                    f"ComfyUI prompt '{prompt_id}' did not complete within "
                    f"{self.timeout_seconds}s"
                )

            if self.poll_interval_seconds > 0:
                time.sleep(self.poll_interval_seconds)

    def download_image(self, image: dict[str, Any]) -> bytes:
        """Download a generated image through ComfyUI ``/view``."""
        filename = image.get("filename")
        if not filename:
            raise ComfyUIOutputMissing("Image record is missing 'filename'")
        params = {
            "filename": filename,
            "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output"),
        }
        try:
            response = self._get_client().get("/view", params=params)
        except httpx.HTTPError as exc:
            raise ComfyUIDownloadFailed(f"Image download failed: {exc}") from exc

        if response.status_code >= 400 or not response.content:
            raise ComfyUIDownloadFailed(
                f"Image download failed: {_response_error(response)}"
            )
        return response.content

    def upload_image(self, filename: str, data: bytes, overwrite: bool = True) -> str:
        """Upload a reference image through ComfyUI ``/upload/image``."""
        try:
            response = self._get_client().post(
                "/upload/image",
                files={"image": (filename, data, "image/png")},
                data={"overwrite": "true" if overwrite else "false"},
            )
        except httpx.HTTPError as exc:
            raise ComfyUIUnavailable(f"Image upload failed: {exc}") from exc

        if response.status_code >= 400:
            raise ComfyUIError(f"Image upload failed: {_response_error(response)}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ComfyUIError("ComfyUI returned a non-JSON upload response") from exc
        return body.get("name", filename)


def _response_error(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            error = body.get("error") or body.get("node_errors") or body
            return str(error)
        return str(body)
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:200]}"
