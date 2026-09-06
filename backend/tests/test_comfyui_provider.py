# backend/tests/test_comfyui_provider.py
import json

import httpx
from app.comfyui.client import ComfyUIClient
from app.portrait_provider import (
    ComfyUIPortraitImageProvider,
    ProviderGenerationRequest,
    get_portrait_provider,
)

MINIMAL_WORKFLOW = {
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "model.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 768, "height": 1024, "batch_size": 1},
    },
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
    "10": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 0,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
    },
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["4", 2]}},
    "24": {
        "class_type": "SaveImage",
        "inputs": {"images": ["8", 0], "filename_prefix": "soulsmith_portrait"},
    },
}

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _write_workflow(tmp_path):
    path = tmp_path / "portrait_v1_api.json"
    path.write_text(json.dumps(MINIMAL_WORKFLOW))
    return path


def _success_client(submitted):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/prompt":
            submitted["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"prompt_id": "p123", "number": 1, "node_errors": {}}
            )
        if request.url.path == "/history/p123":
            return httpx.Response(
                200,
                json={
                    "p123": {
                        "outputs": {
                            "24": {
                                "images": [
                                    {
                                        "filename": "soulsmith_cand_1_00001_.png",
                                        "subfolder": "",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                        "status": {
                            "status_str": "success",
                            "completed": True,
                            "messages": [],
                        },
                    }
                },
            )
        if request.url.path == "/view":
            return httpx.Response(200, content=PNG_BYTES)
        return httpx.Response(404)

    return ComfyUIClient(
        "http://127.0.0.1:8188",
        transport=httpx.MockTransport(handler),
        poll_interval_seconds=0,
    )


def test_get_portrait_provider_comfyui():
    provider = get_portrait_provider("comfyui")
    assert isinstance(provider, ComfyUIPortraitImageProvider)


def test_comfyui_successful_generation(tmp_path):
    submitted = {}
    client = _success_client(submitted)
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_12345",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait of Kaelen with scar...",
        negative_prompt="deformed features, extra limbs",
        seed=12345,
    )

    res = provider.generate(req)

    assert res.success is True
    assert res.provider == "comfyui"
    assert res.provider_model == "soulsmith-comfyui-portrait-initial-v1"
    assert res.provider_request_id == "p123"
    assert res.generation_seed == 12345
    assert res.generated_image_url.startswith(
        "/assets/portraits/candidates/candidate_cand_12345.png"
    )

    # Prompt, negative prompt, and seed reach the workflow.
    prompt = submitted["body"]["prompt"]
    assert prompt["6"]["inputs"]["text"] == "Portrait of Kaelen with scar..."
    assert prompt["7"]["inputs"]["text"] == "deformed features, extra limbs"
    assert prompt["10"]["inputs"]["seed"] == 12345
    assert prompt["24"]["inputs"]["filename_prefix"] == "soulsmith_cand_12345"


def test_comfyui_stores_image_locally(tmp_path):
    client = _success_client({})
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_12345",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
    )

    res = provider.generate(req)

    expected = (
        tmp_path / "assets" / "portraits" / "candidates" / "candidate_cand_12345.png"
    )
    assert expected.exists()
    assert expected.read_bytes() == PNG_BYTES
    assert res.success is True


def test_comfyui_generates_seed_when_absent(tmp_path):
    client = _success_client({})
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_12345",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
    )

    res = provider.generate(req)
    assert res.success is True
    assert res.generation_seed is not None
    assert res.generation_seed >= 0


def test_comfyui_unavailable_fails_gracefully(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = ComfyUIClient(
        "http://127.0.0.1:8188", transport=httpx.MockTransport(handler)
    )
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_12345",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
    )

    res = provider.generate(req)
    assert res.success is False
    assert res.provider == "comfyui"
    assert res.failure_reason


def test_comfyui_sanitizes_candidate_id(tmp_path):
    submitted = {}
    client = _success_client(submitted)
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="../evil/path",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
    )

    res = provider.generate(req)
    assert res.success is True
    assert ".." not in res.generated_image_url
    assert (
        "/assets/portraits/candidates/candidate_evil_path.png"
        in res.generated_image_url
    )


REFERENCE_WORKFLOW = {
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "model.safetensors"},
    },
    "11": {"class_type": "LoadImage", "inputs": {"image": "placeholder.png"}},
    "12": {"class_type": "VAEEncode", "inputs": {"pixels": ["11", 0], "vae": ["4", 2]}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
    "10": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 0,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 0.6,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["12", 0],
        },
    },
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["4", 2]}},
    "24": {
        "class_type": "SaveImage",
        "inputs": {"images": ["8", 0], "filename_prefix": "soulsmith_portrait"},
    },
}


def _write_reference_workflow(tmp_path):
    path = tmp_path / "portrait_reference_api.json"
    path.write_text(json.dumps(REFERENCE_WORKFLOW))
    return path


def _reference_client(submitted, uploaded):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/upload/image":
            uploaded["name"] = "uploaded_ref.png"
            return httpx.Response(
                200,
                json={"name": "uploaded_ref.png", "subfolder": "", "type": "input"},
            )
        if request.url.path == "/prompt":
            submitted["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"prompt_id": "p123", "number": 1, "node_errors": {}}
            )
        if request.url.path == "/history/p123":
            return httpx.Response(
                200,
                json={
                    "p123": {
                        "outputs": {
                            "24": {
                                "images": [
                                    {
                                        "filename": "soulsmith_cand_1_00001_.png",
                                        "subfolder": "",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                        "status": {
                            "status_str": "success",
                            "completed": True,
                            "messages": [],
                        },
                    }
                },
            )
        if request.url.path == "/view":
            return httpx.Response(200, content=PNG_BYTES)
        return httpx.Response(404)

    return ComfyUIClient(
        "http://127.0.0.1:8188",
        transport=httpx.MockTransport(handler),
        poll_interval_seconds=0,
    )


def test_comfyui_reference_generation_uploads_and_binds(tmp_path):
    submitted = {}
    uploaded = {}
    client = _reference_client(submitted, uploaded)

    ref_dir = tmp_path / "assets" / "portraits" / "candidates"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "baseline.png").write_bytes(b"\x89PNG baseline")

    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_ref_1",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait with new scar...",
        generation_type="story_mark_update",
        negative_prompt="blurry",
        reference_image_url="/assets/portraits/candidates/baseline.png",
        seed=7,
    )

    res = provider.generate(req)
    assert res.success is True
    assert uploaded["name"] == "uploaded_ref.png"
    prompt = submitted["body"]["prompt"]
    assert prompt["11"]["inputs"]["image"] == "uploaded_ref.png"
    assert prompt["6"]["inputs"]["text"] == "Portrait with new scar..."
    assert prompt["7"]["inputs"]["text"] == "blurry"
    assert prompt["10"]["inputs"]["seed"] == 7
    assert (
        prompt["10"]["inputs"]["denoise"] == 0.25
    )  # 1 - default reference_strength 0.75


def test_comfyui_reference_missing_file_fails_cleanly(tmp_path):
    client = _reference_client({}, {})
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_ref_2",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
        generation_type="story_mark_update",
        reference_image_url="/assets/portraits/candidates/missing.png",
    )

    res = provider.generate(req)
    assert res.success is False
    assert "not found" in res.failure_reason.lower()


def test_comfyui_continuity_without_reference_fails(tmp_path):
    client = _reference_client({}, {})
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_ref_3",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
        generation_type="equipment_update",
    )

    res = provider.generate(req)
    assert res.success is False
    assert "source portrait" in res.failure_reason.lower()


def test_comfyui_initial_ignores_reference_and_uses_initial_workflow(tmp_path):
    submitted = {}
    client = _success_client(submitted)
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_init",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
        generation_type="initial",
        reference_image_url="/assets/portraits/candidates/baseline.png",
    )

    res = provider.generate(req)
    assert res.success is True
    assert res.provider_model == "soulsmith-comfyui-portrait-initial-v1"
    # Initial workflow has no LoadImage node; reference must not be injected.
    assert "11" not in submitted["body"]["prompt"]


def test_comfyui_reference_metadata(tmp_path):
    submitted = {}
    uploaded = {}
    client = _reference_client(submitted, uploaded)
    ref_dir = tmp_path / "assets" / "portraits" / "candidates"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "baseline.png").write_bytes(b"\x89PNG baseline")

    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        reference_strength=0.5,
        asset_root=str(tmp_path / "assets"),
        client=client,
    )
    req = ProviderGenerationRequest(
        candidate_id="cand_ref_meta",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
        generation_type="age_update",
        reference_image_url="/assets/portraits/candidates/baseline.png",
        seed=99,
    )

    res = provider.generate(req)
    assert res.success is True
    assert res.provider == "comfyui"
    assert res.provider_model == "soulsmith-comfyui-portrait-reference-v1"
    assert res.provider_request_id == "p123"
    assert res.generation_seed == 99
    assert submitted["body"]["prompt"]["10"]["inputs"]["denoise"] == 0.5


def test_comfyui_diagnose(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/system_stats":
            return httpx.Response(200, json={"system": {}})
        return httpx.Response(404)

    client = ComfyUIClient(
        "http://127.0.0.1:8188", transport=httpx.MockTransport(handler)
    )
    provider = ComfyUIPortraitImageProvider(
        server_url="http://127.0.0.1:8188",
        initial_workflow_path=str(_write_workflow(tmp_path)),
        reference_workflow_path=str(_write_reference_workflow(tmp_path)),
        asset_root=str(tmp_path / "assets"),
        client=client,
    )

    status = provider.diagnose()
    assert status["provider"] == "comfyui"
    assert status["reachable"] is True
    assert status["initial_workflow_available"] is True
    assert status["reference_workflow_available"] is True
    assert status["output_storage_writable"] is True
