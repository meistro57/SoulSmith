# backend/tests/test_art_director.py
from app.art_director import (
    ArtDirectionProfileVersionModel,
    compile_art_direction_spec,
    resolve_art_direction,
)
from app.chronicle_paintings import ProviderCapabilitiesModel
from app.main import app
from app.style_reviewer import (
    MockArtDirectionReviewer,
    final_verdict_after_style_review,
)
from fastapi.testclient import TestClient

client = TestClient(app)


def _create_profile(**overrides) -> dict:
    payload = {
        "name": "SoulSmith House Style",
        "description": "Painterly mythic realism.",
        "medium_style": "oil-on-canvas painterly",
        "palette_guidance": "amber and indigo",
        "lighting_guidance": "chiaroscuro",
        "atmosphere": "hushed and resonant",
        "texture_material": "tactile brushwork",
        "camera_framing": "cinematic depth",
        "composition_guidance": "clear focal separation",
        "portrait_treatment": "upper-body hero framing",
        "environment_treatment": "landmark-scale establishing",
        "relic_treatment": "studio still life",
        "phenomenon_treatment": "atmospheric phenomenon-dominant",
        "chronicle_treatment": "painterly scene",
        "negative_guidance": "no MMO poster composition",
        "provider_hints": {"workflow": "text-to-image"},
        "accessibility_notes": "high contrast",
    }
    payload.update(overrides)
    res = client.post("/api/v1/art-direction/profiles", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_profile_creation_and_versioning():
    created = _create_profile()
    profile = created["profile"]
    version = created["version"]
    assert profile["profile_id"]
    assert profile["status"] == "draft"
    assert profile["current_version_id"] == version["version_id"]
    assert version["version_number"] == 1

    listed = client.get("/api/v1/art-direction/profiles").json()
    assert any(p["profile_id"] == profile["profile_id"] for p in listed["profiles"])

    fetched = client.get(
        f"/api/v1/art-direction/profiles/{profile['profile_id']}"
    ).json()
    assert len(fetched["versions"]) == 1


def test_changing_profile_does_not_mutate_previous_version():
    created = _create_profile()
    profile_id = created["profile"]["profile_id"]
    v1 = created["version"]

    res = client.post(
        f"/api/v1/art-direction/profiles/{profile_id}/versions",
        json={"name": "ignored", "medium_style": "etched archival linework"},
    )
    assert res.status_code == 200
    v2 = res.json()["version"]

    assert v2["version_number"] == 2
    assert v2["medium_style"] == "etched archival linework"

    versions = client.get(
        f"/api/v1/art-direction/profiles/{profile_id}/versions"
    ).json()["versions"]
    v1_after = next(v for v in versions if v["version_number"] == 1)
    assert v1_after["medium_style"] == v1["medium_style"]
    assert v1_after["medium_style"] == "oil-on-canvas painterly"


def test_profile_version_has_no_canonical_fact_fields():
    created = _create_profile()
    version = created["version"]
    # Style profiles must not carry canonical character/world facts.
    assert "canonical_facts" not in version
    assert "participants" not in version
    assert "event_id" not in version


def test_deterministic_resolution_and_override():
    created = _create_profile()
    version = ArtDirectionProfileVersionModel(**created["version"])

    a = resolve_art_direction(version, "portrait")
    b = resolve_art_direction(version, "portrait")
    assert a.model_dump() == b.model_dump()

    overridden = resolve_art_direction(
        version, "portrait", {"medium_style": "watercolor wash"}
    )
    assert overridden.medium_style == "watercolor wash"
    assert overridden.palette_guidance == version.palette_guidance
    assert overridden.treatment == version.portrait_treatment


def test_deterministic_art_direction_spec():
    created = _create_profile()
    version = ArtDirectionProfileVersionModel(**created["version"])

    canonical = {"event_id": "evt_1", "location": "Salt Spire"}
    caps = ProviderCapabilitiesModel(
        provider="mock", text_to_image=True, single_reference=True
    )

    spec_a = compile_art_direction_spec(
        artifact_type="chronicle_painting",
        profile_version=version,
        canonical=canonical,
        historical_references=[{"source_id": "pv_1"}],
        provider_capabilities=caps,
    )
    spec_b = compile_art_direction_spec(
        artifact_type="chronicle_painting",
        profile_version=version,
        canonical=canonical,
        historical_references=[{"source_id": "pv_1"}],
        provider_capabilities=caps,
    )
    assert spec_a.provider_prompt == spec_b.provider_prompt
    # Canonical and stylistic requirements stay separate.
    assert spec_a.canonical == canonical
    assert spec_a.style.medium_style == version.medium_style
    assert "[CANONICAL]" in spec_a.provider_prompt
    assert "[ART DIRECTION]" in spec_a.provider_prompt


def test_provider_capability_degradation_is_explicit():
    from app.art_director import capability_limitations

    limited = ProviderCapabilitiesModel(provider="mock", multiple_references=False)
    limits = capability_limitations(limited, reference_count=2, requires_identity=True)
    assert any("multiple historical references" in l for l in limits)
    assert any("cannot condition on identity" in l for l in limits)


def test_guardian_block_not_overridden_by_style_approval():
    review = MockArtDirectionReviewer(forced_verdict=None).review(
        resolved=resolve_art_direction(
            ArtDirectionProfileVersionModel(
                version_id="v1", profile_id="p1", version_number=1
            ),
            "chronicle_painting",
        )
    )
    assert review.status == "pass"

    # A Guardian BLOCK always wins over a style pass.
    assert final_verdict_after_style_review("blocked", review) == "blocked"
    assert final_verdict_after_style_review("retry", review) == "retry"
    assert final_verdict_after_style_review("passed", review) == "passed"


def test_style_reviewer_can_request_retry_but_not_block():
    review = MockArtDirectionReviewer(forced_verdict="retry").review(
        resolved=resolve_art_direction(
            ArtDirectionProfileVersionModel(
                version_id="v1", profile_id="p1", version_number=1
            ),
            "portrait",
        )
    )
    assert review.status == "retry"
    assert review.correction_instructions


def test_current_profile_resolution_endpoint():
    created = _create_profile()
    profile_id = created["profile"]["profile_id"]
    client.post(
        f"/api/v1/art-direction/profiles/{profile_id}/status?status_value=current"
    )
    res = client.get("/api/v1/art-direction/current")
    assert res.status_code == 200
    assert res.json()["profile"]["profile_id"] == profile_id
    assert res.json()["version"]["version_number"] == 1
