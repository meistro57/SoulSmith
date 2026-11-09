# backend/tests/test_comfyui_workflow_binder.py
import pytest
from app.comfyui.errors import WorkflowBindingError
from app.comfyui.workflow_binder import (
    DEFAULT_PORTRAIT_BINDINGS,
    REFERENCE_PORTRAIT_BINDINGS,
    BindingTarget,
    WorkflowBinder,
)

SAMPLE_WORKFLOW = {
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "model.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 768, "height": 1024, "batch_size": 1},
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "original positive", "clip": ["4", 1]},
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "original negative", "clip": ["4", 1]},
    },
    "10": {"class_type": "KSampler", "inputs": {"seed": 0, "steps": 25}},
    "24": {"class_type": "SaveImage", "inputs": {"filename_prefix": "orig"}},
}


def test_default_bindings_match_known_nodes():
    assert DEFAULT_PORTRAIT_BINDINGS["positive_prompt"].node_id == "6"
    assert DEFAULT_PORTRAIT_BINDINGS["seed"].node_id == "10"
    assert DEFAULT_PORTRAIT_BINDINGS["filename_prefix"].node_id == "24"


def test_bind_injects_positive_prompt():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, positive_prompt="NEW POSITIVE")
    assert result["6"]["inputs"]["text"] == "NEW POSITIVE"


def test_bind_injects_negative_prompt():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, negative_prompt="NEW NEGATIVE")
    assert result["7"]["inputs"]["text"] == "NEW NEGATIVE"


def test_bind_injects_seed():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, seed=42)
    assert result["10"]["inputs"]["seed"] == 42


def test_bind_injects_filename_prefix():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, filename_prefix="soulsmith_cand_1")
    assert result["24"]["inputs"]["filename_prefix"] == "soulsmith_cand_1"


def test_bind_preserves_unrelated_nodes_and_original():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, positive_prompt="X")
    # Unbound inputs stay as they were.
    assert result["4"]["inputs"]["ckpt_name"] == "model.safetensors"
    assert result["5"]["inputs"]["width"] == 768
    assert result["10"]["inputs"]["steps"] == 25
    # Original workflow is not mutated (deep copy semantics).
    assert SAMPLE_WORKFLOW["6"]["inputs"]["text"] == "original positive"


def test_bind_rejects_missing_node():
    binder = WorkflowBinder(
        {"positive_prompt": BindingTarget(node_id="999", input_name="text")}
    )
    with pytest.raises(WorkflowBindingError):
        binder.bind(SAMPLE_WORKFLOW, positive_prompt="X")


def test_bind_rejects_missing_input():
    binder = WorkflowBinder(
        {"positive_prompt": BindingTarget(node_id="6", input_name="nope")}
    )
    with pytest.raises(WorkflowBindingError):
        binder.bind(SAMPLE_WORKFLOW, positive_prompt="X")


def test_bind_skips_unprovided_concepts():
    binder = WorkflowBinder()
    result = binder.bind(SAMPLE_WORKFLOW, positive_prompt="X")
    # negative_prompt not supplied -> untouched.
    assert result["7"]["inputs"]["text"] == "original negative"


def test_reference_bindings_include_base_plus_reference_image():
    assert REFERENCE_PORTRAIT_BINDINGS["positive_prompt"].node_id == "6"
    assert REFERENCE_PORTRAIT_BINDINGS["reference_image"].node_id == "11"
    assert REFERENCE_PORTRAIT_BINDINGS["reference_image"].input_name == "image"


def test_bind_injects_reference_image():
    workflow = {
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "orig", "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "orig", "clip": ["4", 1]},
        },
        "10": {"class_type": "KSampler", "inputs": {"seed": 0}},
        "11": {"class_type": "LoadImage", "inputs": {"image": "placeholder.png"}},
        "24": {"class_type": "SaveImage", "inputs": {"filename_prefix": "orig"}},
    }
    binder = WorkflowBinder(REFERENCE_PORTRAIT_BINDINGS)
    result = binder.bind(
        workflow,
        positive_prompt="P",
        negative_prompt="N",
        seed=5,
        filename_prefix="fp",
        reference_image="uploaded_ref.png",
    )
    assert result["11"]["inputs"]["image"] == "uploaded_ref.png"
    assert result["6"]["inputs"]["text"] == "P"
    assert result["10"]["inputs"]["seed"] == 5
