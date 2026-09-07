# backend/app/map_provider.py
"""
SoulSmith Phase 20: map/geocoding provider abstraction.

The domain model is never married to one map vendor. Providers translate an
authorized, consent-filtered location sample into nearby *candidate* place
references. A provider only ever receives reduced-precision coordinates (or a
region id) — never a precise private location unless the consent grant permits
it — and it never fabricates a canonical discovery.
"""

from __future__ import annotations

from typing import Any, Protocol

MAP_PROVIDER_VERSION = "1.0.0"


class MapProvider(Protocol):
    provider: str
    provider_model: str

    def nearby_places(
        self, *, latitude: float | None, longitude: float | None, region_id: str | None
    ) -> list[dict[str, Any]]: ...


class MockMapProvider:
    """Deterministic, offline provider. Returns an empty candidate list because
    a fictional map cannot know real geography; Wandering eligibility is then
    computed locally from stored Places, never from a vendor."""

    provider = "soulsmith-mock-map-v1"
    provider_model = "mock"

    def nearby_places(
        self, *, latitude: float | None, longitude: float | None, region_id: str | None
    ) -> list[dict[str, Any]]:
        return []


def get_map_provider(name: str | None = None) -> MapProvider:
    """Select a map provider. Only the deterministic mock is wired in Phase 20;
    a real geocoder can be added behind the same interface without touching the
    domain model."""
    return MockMapProvider()
