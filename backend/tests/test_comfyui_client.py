# backend/tests/test_comfyui_client.py
import json

import httpx
import pytest

from app.comfyui.client import ComfyUIClient, extract_output_images
from app.comfyui.errors import (
    ComfyUIGenerationFailed,
    ComfyUIOutputMissing,
    ComfyUITimeout,
    ComfyUIUnavailable,
    ComfyUIWorkflowRejected,
)


def _client(handler, **kwargs):
    transport = httpx.MockTransport(handler)
    kwargs.setdefault("poll_interval_seconds", 0)
    return ComfyUIClient("http://127.0.0.1:8188", transport=transport, **kwargs)


def _completed_history(prompt_id="p123", images=None):
    images = images or [
        {"filename": "soulsmith_cand_1_00001_.png", "subfolder": "", "type": "output"}
    ]
    return {
        prompt_id: {
            "outputs": {"24": {"images": images}},
            "status": {"status_str": "success", "completed": True, "messages": []},
        }
    }


def test_submit_workflow_returns_prompt_id():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"prompt_id": "p123", "number": 1, "node_errors": {}}
        )

    client = _client(handler)
    prompt_id = client.submit_workflow(
        {"6": {"class_type": "CLIPTextEncode", "inputs": {"text": "x"}}}
    )

    assert prompt_id == "p123"
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/prompt")
    assert "prompt" in captured["body"]


def test_submit_workflow_rejects_node_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"prompt_id": "p123", "node_errors": {"6": {"errors": ["bad"]}}}
        )

    client = _client(handler)
    with pytest.raises(ComfyUIWorkflowRejected):
        client.submit_workflow({"6": {}})


def test_wait_for_completion_polls_until_done():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/history/"):
            calls["n"] += 1
            if calls["n"] < 3:
                return httpx.Response(200, json={})
            return httpx.Response(200, json=_completed_history())
        return httpx.Response(404)

    client = _client(handler)
    entry = client.wait_for_completion("p123")
    assert entry["status"]["completed"] is True
    assert calls["n"] == 3


def test_wait_for_completion_detects_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "p123": {
                    "status": {
                        "status_str": "error",
                        "completed": False,
                        "messages": ["boom"],
                    }
                }
            },
        )

    client = _client(handler)
    with pytest.raises(ComfyUIGenerationFailed):
        client.wait_for_completion("p123")


def test_wait_for_completion_times_out():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = _client(handler, timeout_seconds=0.05, poll_interval_seconds=0.001)
    with pytest.raises(ComfyUITimeout):
        client.wait_for_completion("p123")


def test_download_image_returns_bytes():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/view":
            return httpx.Response(200, content=b"\x89PNG\r\n\x1a\n")
        return httpx.Response(404)

    client = _client(handler)
    data = client.download_image(
        {"filename": "x.png", "subfolder": "", "type": "output"}
    )
    assert data.startswith(b"\x89PNG")


def test_download_image_requires_filename():
    client = _client(lambda request: httpx.Response(200, content=b"x"))
    with pytest.raises(ComfyUIOutputMissing):
        client.download_image({"subfolder": "", "type": "output"})


def test_extract_output_images_missing_output():
    assert extract_output_images({"outputs": {"24": {}}}) == []


def test_extract_output_images_collects_all():
    history = {
        "outputs": {
            "24": {
                "images": [{"filename": "a.png", "subfolder": "", "type": "output"}]
            },
            "9": {
                "images": [{"filename": "b.png", "subfolder": "sub", "type": "temp"}]
            },
        }
    }
    assert len(extract_output_images(history)) == 2


def test_health_check_false_when_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = _client(handler)
    assert client.health_check() is False


def test_unavailable_raises_clean_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = _client(handler)
    with pytest.raises(ComfyUIUnavailable):
        client.submit_workflow({"6": {}})
