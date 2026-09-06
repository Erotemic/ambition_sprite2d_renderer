from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import zipfile

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "install_godot.py"


def _load_installer():
    spec = importlib.util.spec_from_file_location("ambition_install_godot", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_installer_pin_matches_project_and_official_release_metadata_shape():
    installer = _load_installer()
    assert installer.pinned_version(REPO) == "4.6.3"

    x86 = installer.asset_spec("4.6.3", "amd64")
    arm = installer.asset_spec("4.6.3", "arm64")
    assert x86.filename == "Godot_v4.6.3-stable_linux.x86_64.zip"
    assert arm.filename == "Godot_v4.6.3-stable_linux.arm64.zip"
    assert len(x86.sha512) == 128
    assert len(arm.sha512) == 128
    int(x86.sha512, 16)
    int(arm.sha512, 16)


def test_extract_executable_only_installs_the_expected_zip_member(tmp_path):
    installer = _load_installer()
    spec = installer.AssetSpec(
        machine="x86_64",
        filename="fixture.zip",
        executable="Godot_fixture",
        sha512="0" * 128,
    )
    archive = tmp_path / "fixture.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("nested/Godot_fixture", b"#!/bin/sh\necho fixture\n")
        bundle.writestr("nested/not-installed.txt", b"ignore me")

    destination = tmp_path / "tpl"
    installed = installer.extract_executable(archive, spec, destination)

    assert installed == destination / "Godot_fixture"
    assert installed.read_bytes().startswith(b"#!/bin/sh")
    assert installed.stat().st_mode & 0o111
    assert not (destination / "not-installed.txt").exists()


def test_verify_archive_rejects_checksum_mismatch(tmp_path):
    installer = _load_installer()
    archive = tmp_path / "fixture.zip"
    archive.write_bytes(b"not the expected archive")
    spec = installer.AssetSpec(
        machine="x86_64",
        filename=archive.name,
        executable="Godot_fixture",
        sha512="0" * 128,
    )

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        installer.verify_archive(archive, spec)
