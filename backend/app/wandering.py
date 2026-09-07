# backend/app/wandering.py
"""
SoulSmith Phase 20: WANDERING foundation — real-world play, safely.

> THE WORLD MAY SUGGEST WHERE TO LOOK. IT MUST NEVER REQUIRE THE PLAYER TO
> SURRENDER THEIR PRIVACY OR SAFETY.

This module formalizes persistent place entities, consent-safe location
sampling, bounded deterministic nearby-discovery eligibility, and the privacy /
safety rules that keep real-world play from becoming tracking or grind.

Real places become story places only when an authorized canonical event is
committed through the existing systems. A location is context; it never
automatically becomes canon.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel

WANDERING_VERSION = "1.0.0"

PLACE_KINDS = frozenset(
    {
        "real_world",
        "fictional",
        "hybrid_interpretive",
        "region",
        "discovery_zone",
        "event_site",
    }
)

SAFETY_STATUSES = frozenset({"unknown", "safe", "restricted", "retired"})

# Bounded discovery contract. Count-based cooldowns and a deterministic radius;
# no wall-clock, no streak pressure, no continuous background tracking.
DEFAULT_DISCOVERY_RADIUS_M = 500.0
MAX_DISCOVERY_RESULTS = 10


class PlaceModel(BaseModel):
    place_id: str
    place_name: str
    place_kind: str = "interpretive"
    public_label: str | None = None
    region_id: str | None = None
    region_precision: str = "reduced"
    # Precise coordinates are stripped from every public projection.
    coordinate_latitude: float | None = None
    coordinate_longitude: float | None = None
    coordinate_precision_m: str = "coarse"
    consent_scope: str = "private"
    safety_status: str = "unknown"
    is_active: bool = True
    created_by_soul_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CreatePlaceRequest(BaseModel):
    place_name: str
    place_kind: str = "interpretive"
    public_label: str | None = None
    region_id: str | None = None
    region_precision: str = "reduced"
    coordinate_latitude: float | None = None
    coordinate_longitude: float | None = None
    coordinate_precision_m: str = "coarse"
    consent_scope: str = "private"
    safety_status: str = "unknown"
    created_by_soul_id: str | None = None


class RetirePlaceRequest(BaseModel):
    place_id: str
    safety_status: str = "retired"


class LocationConsentRequest(BaseModel):
    soul_id: str
    location_access_granted: bool = False
    purpose: str = ""
    precision_level: str = "coarse"
    retention_days: int | None = None


class LocationSampleRequest(BaseModel):
    soul_id: str
    latitude: float
    longitude: float
    precision_m: float = 50.0
    purpose: str = "wandering_discovery"


class RecordDiscoveryRequest(BaseModel):
    soul_id: str
    place_id: str


class RecordPlaceHistoryRequest(BaseModel):
    place_id: str
    event_type: str
    event_id: str
    soul_id: str | None = None
    provenance_source_type: str
    provenance_source_id: str
    visibility: str = "public_canon"


def _public_place(
    place: dict[str, Any], *, include_coordinates: bool
) -> dict[str, Any]:
    """Consent-safe place projection. Precise coordinates are stripped unless
    explicitly authorized; private places are reduced to a public label."""
    projected = dict(place)
    if not include_coordinates:
        projected["coordinate_latitude"] = None
        projected["coordinate_longitude"] = None
        projected["coordinate_precision_m"] = "hidden"
    if place.get("consent_scope") != "public_canon":
        # A private place is represented by its reduced-precision region only.
        projected["place_name"] = (
            place.get("public_label") or place.get("region_id") or "Undisclosed place"
        )
        projected["coordinate_latitude"] = None
        projected["coordinate_longitude"] = None
        projected["coordinate_precision_m"] = "hidden"
    return projected


def project_place_for_viewer(
    place: dict[str, Any], viewer_soul_id: str | None, *, debug: bool = False
) -> dict[str, Any]:
    """A place's precise coordinates are exposed only to its owner in authorized
    debug mode, never in public API metadata."""
    owner = place.get("created_by_soul_id")
    include_coordinates = bool(debug and owner and owner == viewer_soul_id)
    return _public_place(place, include_coordinates=include_coordinates)


def location_consent_granted(soul_id: str) -> bool:
    from app import db

    consent = db.get_or_create_location_consent_record(soul_id)
    return bool(consent.get("location_access_granted"))


def submit_location_sample(sample: LocationSampleRequest) -> dict[str, Any]:
    """Accept an authorized location sample. Without explicit consent the sample
    is rejected — core gameplay must remain usable without location."""
    from app import db

    consent = db.get_or_create_location_consent_record(sample.soul_id)
    if not consent.get("location_access_granted"):
        raise PermissionError(
            "Location access has not been granted for this Aspect. Core play remains available."
        )
    # Minimize stored precision: coarsen to the requested consent precision cap.
    precision = max(float(sample.precision_m), _min_precision_m(consent))
    return db.create_location_sample_record(
        soul_id=sample.soul_id,
        latitude=sample.latitude,
        longitude=sample.longitude,
        precision_m=precision,
        purpose=sample.purpose,
        consent_scope="private",
    )


def _min_precision_m(consent: dict[str, Any]) -> float:
    return {
        "fine": 10.0,
        "medium": 50.0,
        "coarse": 250.0,
    }.get(consent.get("precision_level"), 250.0)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def nearby_eligible_places(
    *,
    soul_id: str,
    latitude: float,
    longitude: float,
    radius_m: float = DEFAULT_DISCOVERY_RADIUS_M,
) -> dict[str, Any]:
    """Deterministic, bounded discovery from an authorized sample. Only active,
    non-retired places are returned, and public projections never expose
    precise coordinates. Unauthorized (no-consent) callers get no result."""
    from app import db

    if not location_consent_granted(soul_id):
        return {"authorized": False, "places": [], "reason": "no_consent"}

    places = db.list_place_records(active_only=True)
    results: list[dict[str, Any]] = []
    for place in places:
        if place.get("safety_status") in ("restricted", "retired"):
            continue
        lat = place.get("coordinate_latitude")
        lon = place.get("coordinate_longitude")
        if lat is None or lon is None:
            continue
        distance = _haversine_m(latitude, longitude, float(lat), float(lon))
        if distance <= radius_m:
            results.append(
                {
                    "place": project_place_for_viewer(place, soul_id),
                    "distance_m": round(distance, 1),
                }
            )
    results.sort(key=lambda r: r["distance_m"])
    results = results[:MAX_DISCOVERY_RESULTS]
    return {"authorized": True, "places": results, "radius_m": radius_m}


def list_places_visible_to(
    viewer_soul_id: str | None, *, debug: bool = False
) -> list[dict[str, Any]]:
    from app import db

    places = db.list_place_records(active_only=True)
    return [project_place_for_viewer(p, viewer_soul_id, debug=debug) for p in places]


def record_place_discovery(soul_id: str, place_id: str) -> dict[str, Any]:
    from app import db

    place = db.get_place_record(place_id)
    if not place:
        raise ValueError(f"Place '{place_id}' not found")
    discovery = db.create_wandering_discovery_record(
        soul_id=soul_id,
        place_id=place_id,
        opportunity_type="wandering_discovery",
        opportunity_id=None,
        hidden_details={"public_label": place.get("public_label")},
    )
    return {"discovery": discovery, "place": project_place_for_viewer(place, soul_id)}


def record_place_history(record: RecordPlaceHistoryRequest) -> dict[str, Any]:
    from app import db

    place = db.get_place_record(record.place_id)
    if not place:
        raise ValueError(f"Place '{record.place_id}' not found")
    return db.add_place_history_record(
        place_id=record.place_id,
        event_type=record.event_type,
        event_id=record.event_id,
        soul_id=record.soul_id,
        provenance_source_type=record.provenance_source_type,
        provenance_source_id=record.provenance_source_id,
        visibility=record.visibility,
    )


def inspect_place_history(
    place_id: str, viewer_soul_id: str | None = None
) -> dict[str, Any]:
    from app import db

    place = db.get_place_record(place_id)
    if not place:
        raise ValueError(f"Place '{place_id}' not found")
    history = db.list_place_history_records(place_id, viewer_soul_id=viewer_soul_id)
    return {
        "place": project_place_for_viewer(place, viewer_soul_id),
        "history": history,
    }
