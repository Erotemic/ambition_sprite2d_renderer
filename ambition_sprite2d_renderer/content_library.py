"""Read the library selected for an authoring request."""
from __future__ import annotations
import json
import os
from functools import lru_cache
from pathlib import Path
from .publication_store import relative


@lru_cache(maxsize=1)
def _checkout() -> Path:
    return Path(__file__).resolve().parents[3]


def repo_root() -> Path:
    selected = os.environ.get("AMBITION_REPO_ROOT")
    return Path(selected) if selected is not None else _checkout()


def manifest_path(repo: Path | None = None) -> Path:
    root = repo if repo is not None else repo_root()
    return root / os.environ.get("AMBITION_CONTENT_LIBRARY", "game/ambition_content_library/library.json")


_READ: dict = {}


def read(repo: Path | None = None) -> dict:
    """The library manifest, parsed once per file version; callers get their own copy."""
    path = manifest_path(repo)
    st = path.stat()
    stamp = (st.st_size, st.st_mtime_ns)
    if _READ.get(str(path), (None,))[0] != stamp:
        manifest = json.loads(path.read_text())
        if manifest.get("schema") != "ambition.content_library.v1":
            raise ValueError(f"Unsupported content library: {path}")
        _READ[str(path)] = (stamp, json.dumps(manifest))
    return json.loads(_READ[str(path)][1])


def runtime_root(repo: Path | None = None) -> Path:
    if os.environ.get("AMBITION_GENERATION_ROOT"):
        return Path(os.environ["AMBITION_GENERATION_ROOT"])
    return manifest_path(repo).parent / relative(read(repo)["asset_roots"]["generated"])


def publication_root(repo: Path | None = None) -> Path:
    return manifest_path(repo).parent / relative(read(repo)["publication"])


def provenance_root(repo: Path | None = None) -> Path | None:
    path = read(repo).get("provenance")
    return manifest_path(repo).parent / relative(path) if path else None


def quality_root(suffix: str, repo: Path | None = None) -> Path:
    role = {"0_5x": "half", "0_25x": "quarter", "potato": "potato"}[suffix]
    if os.environ.get("AMBITION_GENERATION_ROOT"):
        return Path(os.environ["AMBITION_GENERATION_ROOT"]).parent / role
    return manifest_path(repo).parent / relative(read(repo)["asset_roots"][role])
