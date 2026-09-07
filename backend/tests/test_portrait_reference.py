# backend/tests/test_portrait_reference.py
import pytest

from app.db import create_portrait_version_record
from app.portrait_reference import SourcePortraitError, resolve_source_portrait


def test_resolve_none_when_no_source_requested():
    assert resolve_source_portrait("soul_a", None) is None


def test_resolve_valid_version():
    version = create_portrait_version_record(
        soul_id="soul_a", label="Portrait v1", image_url="/assets/portraits/v1.png"
    )
    resolved = resolve_source_portrait("soul_a", version["version_id"])
    assert resolved["version_id"] == version["version_id"]
    assert resolved["image_url"] == "/assets/portraits/v1.png"


def test_missing_version_raises():
    with pytest.raises(SourcePortraitError, match="not found"):
        resolve_source_portrait("soul_a", "pv_missing")


def test_wrong_soul_raises():
    version = create_portrait_version_record(
        soul_id="soul_a", label="Portrait v1", image_url="/assets/portraits/v1.png"
    )
    with pytest.raises(SourcePortraitError, match="does not belong"):
        resolve_source_portrait("soul_b", version["version_id"])


def test_historical_version_selected_exactly():
    # Two versions for the same soul; requesting v1 must return v1, not the newest.
    v1 = create_portrait_version_record(
        soul_id="soul_a", label="v1", image_url="/assets/portraits/v1.png"
    )
    create_portrait_version_record(
        soul_id="soul_a", label="v2", image_url="/assets/portraits/v2.png"
    )
    resolved = resolve_source_portrait("soul_a", v1["version_id"])
    assert resolved["image_url"] == "/assets/portraits/v1.png"
