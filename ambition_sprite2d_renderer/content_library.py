"""Read the library selected for an authoring request."""
from __future__ import annotations
import json
import os
from pathlib import Path
from .publication_store import relative


def repo_root() -> Path:
    return Path(os.environ.get("AMBITION_REPO_ROOT", Path(__file__).resolve().parents[3]))


def manifest_path(repo: Path | None = None) -> Path:
    root = repo if repo is not None else repo_root()
    return root / os.environ.get("AMBITION_CONTENT_LIBRARY", "game/ambition_content_library/library.json")


def read(repo: Path | None = None) -> dict:
    path = manifest_path(repo)
    manifest = json.loads(path.read_text())
    if manifest.get("schema") != "ambition.content_library.v1":
        raise ValueError(f"Unsupported content library: {path}")
    return manifest


def runtime_root(repo: Path | None = None) -> Path:
    return manifest_path(repo).parent / relative(read(repo)["asset_roots"]["generated"])


def publication_root(repo: Path | None = None) -> Path:
    return manifest_path(repo).parent / relative(read(repo)["publication"])


def provenance_root(repo: Path | None = None) -> Path | None:
    path = read(repo).get("provenance")
    return manifest_path(repo).parent / relative(path) if path else None
