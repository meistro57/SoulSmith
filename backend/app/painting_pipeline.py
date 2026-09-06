# backend/app/painting_pipeline.py
"""
Chronicle Painting orchestration: generate -> quarantine -> inspect -> pass/retry/block.

The pipeline owns the canonical rule:

    CANON -> SCENE SPEC -> IMAGE GENERATION -> VISUAL CANON GUARDIAN
    -> PLAYER-VISIBLE CANDIDATE

No generated image is exposed before the Visual Canon Guardian passes, and no
approval of a painting ever mutates the canonical Memory Object.
"""

from __future__ import annotations

import os
from typing import Optional

from app.chronicle_paintings import (
    ChroniclePaintingModel,
    GuardianReportModel,
    SceneSpecModel,
)
from app.comfyui.storage import ChronicleImageStore
from app.db import (
    create_chronicle_painting_record,
    get_chronicle_painting_record,
    record_chronicle_painting_guardian_report,
    update_chronicle_painting_generation,
    update_chronicle_painting_promotion,
)
from app.painting_compiler import compile_painting_prompt
from app.painting_provider import (
    PaintingGenerationRequest,
    get_painting_provider,
)
from app.visual_canon_guardian import VisualCanonGuardian, get_visual_canon_guardian
from app.visual_memory import MemoryObjectModel


def _max_retries() -> int:
    return int(os.environ.get("SOULSMITH_CHRONICLE_MAX_RETRIES", "2"))


def create_painting_attempt(
    *,
    memory_object: MemoryObjectModel,
    scene_spec: SceneSpecModel,
    historical_participant_refs,
    generation_type: str,
    composition: str,
    source_painting_id: Optional[str] = None,
    retry_count: int = 0,
    correction_instructions: Optional[list] = None,
) -> ChroniclePaintingModel:
    compiled_prompt = compile_painting_prompt(scene_spec)
    if correction_instructions:
        compiled_prompt += " [CORRECTION] " + "; ".join(correction_instructions)
    record = create_chronicle_painting_record(
        memory_object_id=memory_object.id,
        generation_type=generation_type,
        compiled_prompt=compiled_prompt,
        scene_spec=scene_spec.model_dump(),
        composition=composition,
        historical_participant_refs=historical_participant_refs,
        negative_prompt=", ".join(scene_spec.must_not_invent),
        source_painting_id=source_painting_id,
        retry_count=retry_count,
    )
    return ChroniclePaintingModel(**record)


def generate_chronicle_painting(
    painting_id: str,
    memory_object: MemoryObjectModel,
    *,
    provider_type: Optional[str] = None,
    seed: Optional[int] = None,
    guardian: Optional[VisualCanonGuardian] = None,
) -> ChroniclePaintingModel:
    """
    Run the full generation -> quarantine -> Guardian inspection loop.

    Returns the final painting attempt. On RETRY (within the bounded limit) a
    new attempt is created with ``source_painting_id`` tracking the prior
    attempt and ``memory_object_id`` tracking the canonical source.
    """
    store = ChronicleImageStore()
    provider = get_painting_provider(provider_type)
    guardian = guardian or get_visual_canon_guardian()

    current_id = painting_id
    while True:
        painting_record = get_chronicle_painting_record(current_id)
        if not painting_record:
            raise ValueError(f"Painting '{current_id}' not found")
        painting = ChroniclePaintingModel(**painting_record)

        gen_req = PaintingGenerationRequest(
            painting_id=painting.painting_id,
            memory_object_id=painting.memory_object_id,
            compiled_prompt=painting.compiled_prompt,
            negative_prompt=painting.negative_prompt,
            seed=seed,
            reference_image_url=None,
        )
        result = provider.generate(gen_req)

        if not result.success:
            updated = update_chronicle_painting_generation(
                current_id,
                guardian_status="failed",
                status="failed",
                provider=result.provider,
                provider_model=result.provider_model,
                provider_request_id=result.provider_request_id,
                failure_reason=result.failure_reason,
            )
            return ChroniclePaintingModel(**updated)

        # Quarantine the raw output; it is not player-visible yet.
        quarantined_url = store.quarantine(current_id, result.image_bytes or b"")
        update_chronicle_painting_generation(
            current_id,
            guardian_status="reviewing",
            quarantined_image_url=quarantined_url,
            provider=result.provider,
            provider_model=result.provider_model,
            provider_request_id=result.provider_request_id,
            generation_seed=result.generation_seed,
        )

        scene_spec = SceneSpecModel(**painting.scene_spec)
        report: GuardianReportModel = guardian.inspect(
            image_bytes=result.image_bytes or b"",
            memory_object=memory_object,
            scene_spec=scene_spec,
            provider=result.provider,
            provider_model=result.provider_model,
        )
        record_chronicle_painting_guardian_report(current_id, report.model_dump())

        if report.status == "pass":
            promoted_url = store.promote(current_id, result.image_bytes or b"")
            updated = update_chronicle_painting_promotion(
                current_id,
                image_url=promoted_url,
                guardian_report=report.model_dump(),
                status="candidate",
            )
            return ChroniclePaintingModel(**updated)

        if report.status == "block":
            updated = update_chronicle_painting_generation(
                current_id,
                guardian_status="blocked",
                status="failed",
                failure_reason=(
                    "Visual Canon Guardian blocked this painting: "
                    + "; ".join(v.description for v in report.violations)
                ),
            )
            return ChroniclePaintingModel(**updated)

        # RETRY: quarantine remains, attempt is failed/audited, and we retry.
        update_chronicle_painting_generation(
            current_id,
            guardian_status="retry",
            status="failed",
            failure_reason="Visual Canon Guardian requested regeneration.",
        )

        if painting.retry_count >= _max_retries():
            # Retry limit reached: keep diagnostics, surface a graceful failure.
            update_chronicle_painting_generation(
                current_id,
                guardian_status="blocked",
                status="failed",
                failure_reason=(
                    "Visual Canon Guardian retry limit reached; painting blocked."
                ),
            )
            return ChroniclePaintingModel(**get_chronicle_painting_record(current_id))

        retry_prompt = compile_painting_prompt(scene_spec)
        retry_prompt += " [CORRECTION] " + "; ".join(report.correction_instructions)
        retry_record = create_chronicle_painting_record(
            memory_object_id=memory_object.id,
            generation_type="retry",
            compiled_prompt=retry_prompt,
            scene_spec=scene_spec.model_dump(),
            composition=painting.composition,
            historical_participant_refs=painting.historical_participant_refs,
            negative_prompt=painting.negative_prompt,
            source_painting_id=current_id,
            retry_count=painting.retry_count + 1,
        )
        current_id = retry_record["painting_id"]
