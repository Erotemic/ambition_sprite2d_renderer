#!/usr/bin/env python3
"""Install the Godot editor version pinned by Ambition's pose-authoring pilot.

The editor is an authoring dependency only.  It is installed repo-locally under
``tpl/`` so normal sprite rendering and game builds do not acquire a system
Godot dependency.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


RELEASE_BASE_URL = "https://github.com/godotengine/godot-builds/releases/download"
VERSION_FILE = Path("godot/pose_editor/GODOT_VERSION")


@dataclass(frozen=True)
class AssetSpec:
    machine: str
    filename: str
    executable: str
    sha512: str


# SHA-512 values come from the official godotengine/godot-builds release
# manifest for 4.6.3-stable.  Updating the pinned version must update these
# values in the same change.
_ASSETS_BY_VERSION: dict[str, dict[str, AssetSpec]] = {
    "4.6.3": {
        "x86_64": AssetSpec(
            machine="x86_64",
            filename="Godot_v4.6.3-stable_linux.x86_64.zip",
            executable="Godot_v4.6.3-stable_linux.x86_64",
            sha512=(
                "a035258da32b77f966a5376f9fa29c30a6adde826a85ba918e1605bd1fc9823e"
                "ba7d85f1dd5e748956bd2ba72827c0025ffa11bb82aec91128c407a2e723c99c"
            ),
        ),
        "aarch64": AssetSpec(
            machine="aarch64",
            filename="Godot_v4.6.3-stable_linux.arm64.zip",
            executable="Godot_v4.6.3-stable_linux.arm64",
            sha512=(
                "447381de9ccc68aa02f37e279322289f7ddf88ce9b839ed88a97c73e01cdcda4"
                "6e026897e5d88722e08491f71b3d74f72dfeb22ec7e3add6fd3e9bfbbdad6751"
            ),
        ),
    }
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pinned_version(repo: Path) -> str:
    path = repo / VERSION_FILE
    version = path.read_text(encoding="utf8").strip()
    if not version:
        raise RuntimeError(f"empty Godot version pin: {path}")
    return version


def canonical_machine(machine: str | None = None) -> str:
    raw = (machine or platform.machine()).lower()
    aliases = {
        "amd64": "x86_64",
        "x64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }
    try:
        return aliases[raw]
    except KeyError as exc:
        supported = ", ".join(sorted(set(aliases.values())))
        raise RuntimeError(f"unsupported Linux architecture {raw!r}; supported: {supported}") from exc


def asset_spec(version: str, machine: str | None = None) -> AssetSpec:
    try:
        assets = _ASSETS_BY_VERSION[version]
    except KeyError as exc:
        raise RuntimeError(
            f"Godot {version} is pinned by {VERSION_FILE}, but the installer has no release metadata for it"
        ) from exc
    canonical = canonical_machine(machine)
    try:
        return assets[canonical]
    except KeyError as exc:
        raise RuntimeError(f"Godot {version} has no configured asset for {canonical}") from exc


def sha512_file(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(path: Path, spec: AssetSpec) -> None:
    actual = sha512_file(path)
    if actual != spec.sha512:
        raise RuntimeError(
            f"checksum mismatch for {path.name}: expected {spec.sha512}, got {actual}"
        )


def download_archive(spec: AssetSpec, version: str, destination: Path) -> None:
    url = f"{RELEASE_BASE_URL}/{version}-stable/{spec.filename}"
    print(f"Downloading Godot {version} from {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "ambition-godot-installer/1"})
    with urllib.request.urlopen(request) as response, destination.open("wb") as output:
        total_header = response.headers.get("Content-Length")
        total = int(total_header) if total_header and total_header.isdigit() else None
        received = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
            received += len(chunk)
            if total:
                print(f"\r  {received / (1024 * 1024):.1f}/{total / (1024 * 1024):.1f} MiB", end="", flush=True)
        if total:
            print()


def extract_executable(archive: Path, spec: AssetSpec, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / spec.executable
    with zipfile.ZipFile(archive) as bundle:
        matches = [name for name in bundle.namelist() if Path(name).name == spec.executable]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected exactly one {spec.executable!r} in {archive.name}, found {len(matches)}"
            )
        fd, temp_name = tempfile.mkstemp(prefix=f".{spec.executable}.", dir=destination)
        try:
            with os.fdopen(fd, "wb") as output, bundle.open(matches[0]) as source:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            temp = Path(temp_name)
            temp.chmod(0o755)
            temp.replace(target)
        except Exception:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass
            raise
    return target


def godot_version(executable: Path) -> str:
    result = subprocess.run(
        [str(executable), "--version"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
    )
    return result.stdout.strip()


def verify_installed_binary(executable: Path, version: str) -> str:
    actual = godot_version(executable)
    if not actual.startswith(version + "."):
        raise RuntimeError(
            f"installed executable reported {actual!r}; expected a Godot {version} stable build"
        )
    return actual


def install(
    *,
    repo: Path,
    destination: Path,
    archive: Path | None = None,
    force: bool = False,
    machine: str | None = None,
) -> Path:
    if sys.platform != "linux":
        raise RuntimeError(
            f"the repo-local Godot installer currently supports Linux only, not {sys.platform!r}"
        )

    version = pinned_version(repo)
    spec = asset_spec(version, machine)
    destination = destination.resolve()
    target = destination / spec.executable

    if target.exists() and not force:
        actual = verify_installed_binary(target, version)
        print(f"Godot already installed: {target} ({actual})")
        return target

    destination.mkdir(parents=True, exist_ok=True)
    if archive is not None:
        source = archive.expanduser().resolve()
        if not source.is_file():
            raise RuntimeError(f"archive does not exist: {source}")
        verify_archive(source, spec)
        target = extract_executable(source, spec, destination)
    else:
        with tempfile.TemporaryDirectory(prefix="ambition-godot-") as temp_dir:
            source = Path(temp_dir) / spec.filename
            download_archive(spec, version, source)
            print("Verifying SHA-512 checksum")
            verify_archive(source, spec)
            target = extract_executable(source, spec, destination)

    actual = verify_installed_binary(target, version)
    print(f"Installed Godot {actual} at {target}")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        help="install directory; defaults to the repository-local tpl/ directory",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="use an already downloaded official archive instead of downloading it",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing pinned Godot binary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = repo_root()
    destination = args.destination or (repo / "tpl")
    try:
        path = install(
            repo=repo,
            destination=destination,
            archive=args.archive,
            force=args.force,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"install_godot: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
