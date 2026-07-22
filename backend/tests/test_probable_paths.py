# backend/tests/test_probable_paths.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_probable_paths():
    res = client.get("/api/v1/probable-paths")
    assert res.status_code == 200
    data = res.json()
    assert "probable_paths" in data
    assert len(data["probable_paths"]) >= 1


def test_log_and_manifest_probable_path():
    # 1. Log a new path
    log_res = client.post(
        "/api/v1/probable-paths/log",
        json={
            "soul_id": "Kaelen the Star-Watcher",
            "path_title": "The Glass Mirror Choice",
            "chosen_path": "Shattered the Mirror",
            "unchosen_approach": "Stepped through the Reflection",
            "potential_outcome_class": "ascendancy",
            "manifestation_type": "dream",
        },
    )
    assert log_res.status_code == 200
    path = log_res.json()["probable_path"]
    path_id = path["id"]
    assert path["path_title"] == "The Glass Mirror Choice"

    # 2. Manifest path as alternate scene
    man_res = client.post(
        "/api/v1/probable-paths/manifest",
        json={
            "path_id": path_id,
            "manifestation_type": "alternate_scene",
            "status": "manifested",
        },
    )
    assert man_res.status_code == 200
    updated_path = man_res.json()["probable_path"]
    assert updated_path["manifestation_type"] == "alternate_scene"
    assert updated_path["status"] == "manifested"


def test_explore_probable_path():
    # Get first path
    res = client.get("/api/v1/probable-paths")
    paths = res.json()["probable_paths"]
    path_id = paths[0]["id"]

    exp_res = client.post(
        "/api/v1/probable-paths/explore",
        json={
            "path_id": path_id,
            "soul_name": "Kaelen the Star-Watcher",
        },
    )
    assert exp_res.status_code == 200
    result = exp_res.json()["alternate_scene"]
    assert result["path_id"] == path_id
    assert "alternate_prose" in result
    assert result["canonical_integrity_preserved"] is True
