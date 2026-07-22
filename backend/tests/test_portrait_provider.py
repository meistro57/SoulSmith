# backend/tests/test_portrait_provider.py
from app.portrait_provider import (
    ExternalPortraitImageProvider,
    MockPortraitImageProvider,
    ProviderGenerationRequest,
    get_portrait_provider,
)


def test_mock_portrait_provider_generation():
    provider = MockPortraitImageProvider()
    req = ProviderGenerationRequest(
        candidate_id="cand_12345",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait of Kaelen with scar...",
    )

    res = provider.generate(req)
    assert res.success is True
    assert res.provider == "mock"
    assert "cand_12345" in res.generated_image_url
    assert res.provider_request_id.startswith("mock_req_")


def test_external_provider_fails_gracefully_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SOULSMITH_IMAGE_PROVIDER_API_KEY", raising=False)
    provider = ExternalPortraitImageProvider()
    req = ProviderGenerationRequest(
        candidate_id="cand_67890",
        soul_id="Kaelen the Star-Watcher",
        compiled_prompt="Portrait...",
    )

    res = provider.generate(req)
    assert res.success is False
    assert "unconfigured" in res.failure_reason.lower()


def test_get_portrait_provider_default():
    provider = get_portrait_provider()
    assert isinstance(provider, MockPortraitImageProvider)
