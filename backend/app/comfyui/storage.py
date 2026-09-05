# backend/app/comfyui/storage.py
"""
SoulSmith-owned candidate image storage.

Generated PNGs are copied out of ComfyUI into a local asset directory so the
Visual Memory workflow never depends on ComfyUI ``/view`` URLs after generation.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")

DEFAULT_ASSET_ROOT = Path(
    os.environ.get(
        "SOULSMITH_ASSET_ROOT",
        Path(__file__).resolve().parent.parent.parent / "assets",
    )
)

CANDIDATE_REL_DIR = Path("portraits") / "candidates"


def sanitize_filename(value: str) -> str:
    """Strip path separators and unsafe characters, returning a safe filename token."""
    cleaned = _SAFE_NAME_RE.sub("_", value).strip("._")
    return cleaned or "unknown"


def get_asset_root() -> Path:
    """Return the configured SoulSmith-owned asset root directory."""
    return Path(os.environ.get("SOULSMITH_ASSET_ROOT", DEFAULT_ASSET_ROOT))


def resolve_asset_path(url: str, asset_root: Optional[Path] = None) -> Path:
    """
    Map a SoulSmith ``/assets/...`` URL back to a local file path, rejecting any
    path that escapes the asset root (prevents traversal).
    """
    root = (asset_root or get_asset_root()).resolve()
    if not url.startswith("/assets/"):
        raise ValueError(f"Unsupported asset URL: {url}")
    rel = url[len("/assets/") :].lstrip("/")
    target = (root / rel).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Asset URL escapes asset root: {url}")
    return target


class CandidateImageStore:
    """Persist candidate images into SoulSmith-owned storage."""

    def __init__(self, asset_root: Optional[Path] = None) -> None:
        self._root = Path(asset_root) if asset_root is not None else get_asset_root()

    @property
    def asset_root(self) -> Path:
        return self._root

    @property
    def candidate_dir(self) -> Path:
        return self._root / CANDIDATE_REL_DIR

    def save(self, candidate_id: str, data: bytes, extension: str = ".png") -> str:
        """
        Write candidate image bytes and return the public URL path.

        The filename is derived from a sanitized ``candidate_id`` to prevent path
        traversal. The returned path (``/assets/portraits/candidates/...``) is
        served by FastAPI's static mount and is stable for the lifetime of the file.
        """
        safe_id = sanitize_filename(candidate_id)
        directory = self.candidate_dir
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"candidate_{safe_id}{extension}"
        (directory / filename).write_bytes(data)
        return f"/assets/{CANDIDATE_REL_DIR.as_posix()}/{filename}"

    def save_in_subdir(
        self, subdir: Path, item_id: str, data: bytes, extension: str = ".png"
    ) -> str:
        """
        Write image bytes under ``self._root / subdir`` and return the public URL.

        Used for generated artifacts other than portrait candidates (for example
        approved Chronicle paintings) while reusing the same traversal-safe
        filename rules and static mount.
        """
        safe_id = sanitize_filename(item_id)
        directory = self._root / subdir
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{safe_id}{extension}"
        (directory / filename).write_bytes(data)
        return f"/assets/{subdir.as_posix()}/{filename}"

    def is_writable(self) -> bool:
        """Return True when candidate images can actually be written to storage."""
        try:
            self.candidate_dir.mkdir(parents=True, exist_ok=True)
            probe = self.candidate_dir / ".write_probe"
            probe.write_bytes(b"")
            probe.unlink()
            return True
        except OSError:
            return False
