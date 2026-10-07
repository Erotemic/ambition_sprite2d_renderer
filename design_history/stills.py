"""Make one still of a character as a given commit drew it.

The commit's own renderer code runs, in a scratch worktree OUTSIDE the
repository, through the renderer's ordinary ``canonical`` command. Nothing from
the old tree is copied back. The still lands in an ignored cache keyed by commit
and target, so asking twice costs nothing.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .store import SEGMENTS, Segment, git


def default_cache() -> Path:
    override = os.environ.get("AMBITION_DESIGN_HISTORY_CACHE")
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ambition-design-history"


@dataclasses.dataclass
class Still:
    path: Path | None
    target_id: str | None
    #: Pixel identity of the drawn character (cropped to its alpha box), so two
    #: commits that drew the same character compare equal.
    pixel_hash: str | None
    failure: str = ""


class Worktrees:
    """One sparse worktree per history segment, moved between commits."""

    def __init__(self, store: Path, cache: Path):
        self.store, self.cache = store, cache
        self._ready: set[str] = set()

    def _path(self, seg: Segment) -> Path:
        return self.cache / "worktrees" / seg.name

    def at(self, seg: Segment, sha: str) -> Path:
        """The renderer root of ``seg`` checked out at ``sha``."""
        path = self._path(seg)
        if seg.name not in self._ready:
            if not (path / ".git").exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                git(self.store, "worktree", "prune")
                git(self.store, "worktree", "add", "--detach", "--no-checkout", "-f", str(path), seg.ref)
                if seg.prefix:
                    git(path, "sparse-checkout", "init", "--cone")
                    git(path, "sparse-checkout", "set", seg.prefix.rstrip("/"))
            self._ready.add(seg.name)
        git(path, "checkout", "-q", "--detach", "-f", sha)
        git(path, "clean", "-fdq", check=False)
        return path / seg.prefix.rstrip("/") if seg.prefix else path

    def remove(self) -> None:
        for seg in SEGMENTS:
            path = self._path(seg)
            if path.exists():
                git(self.store, "worktree", "remove", "--force", str(path), check=False)
        git(self.store, "worktree", "prune", check=False)


def pixel_hash(png: Path) -> str:
    from PIL import Image

    with Image.open(png) as image:
        from .progression import character_bbox

        image = image.convert("RGBA")
        box = character_bbox(image) or (0, 0, *image.size)
        cropped = image.crop(box)
        digest = hashlib.sha1(f"{cropped.size}".encode())
        digest.update(cropped.tobytes())
    return digest.hexdigest()[:16]


#: The renderer's package name changed once (the lab was promoted).
PACKAGES = ("ambition_sprite2d_renderer", "proc2d_character_lab")


def package_of(root: Path) -> str | None:
    return next((name for name in PACKAGES if (root / name).is_dir()), None)


def _run(python: str, root: Path, args: list[str], timeout: int = 600):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="")
    return subprocess.run(
        [python, "-m", package_of(root), *args],
        cwd=root, env=env, capture_output=True, text=True, errors="replace", timeout=timeout,
    )


def _imports_this_tree(python: str, root: Path) -> bool:
    """The old package must be the one imported, not the checkout that this tool
    ships in (an editable install would otherwise answer for every commit)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="")
    out = subprocess.run(
        [python, "-c", f"import {package_of(root)} as a; print(a.__file__)"],
        cwd=root, env=env, capture_output=True, text=True,
    ).stdout.strip()
    return bool(out) and Path(out).resolve().is_relative_to(root.resolve())


def _png_in(directory: Path, target_id: str) -> Path | None:
    pngs = sorted(directory.glob("*.png"))
    exact = [p for p in pngs if p.stem.startswith(target_id)]
    return (exact or pngs or [None])[0]


def _rung_canonical(python: str, root: Path, target_id: str, out: Path) -> str:
    """The renderer's own still, from the era that has the command."""
    result = _run(python, root, ["canonical", target_id, "--out-dir", str(out)])
    return "" if result.returncode == 0 and _png_in(out, target_id) else _tail(result)


def _rung_config(python: str, root: Path, target_id: str, out: Path) -> str:
    """The earliest eras draw a character from a YAML job: one idle frame."""
    pkg = root / (package_of(root) or "")
    configs = sorted(pkg.glob(f"configs/**/{target_id}.yaml")) if pkg.exists() else []
    if not configs:
        return f"no config named {target_id}.yaml"
    target = out / f"{target_id}.png"
    for extra in (["--animation", "idle", "--frame-index", "0"], []):
        result = _run(python, root, ["single", str(configs[0]), str(target), *extra])
        if result.returncode == 0 and target.exists():
            return ""
    return _tail(result)


def _rung_render(python: str, root: Path, target_id: str, out: Path) -> str:
    """A tack-on target of the middle eras: take its rendered review image."""
    result = _run(python, root, ["render", target_id])
    if result.returncode != 0:
        return _tail(result)
    produced = sorted((root / "generated").glob(f"{target_id}/**/*.png")) if (root / "generated").exists() else []
    ranked = sorted(
        produced,
        key=lambda p: (not any(w in p.stem for w in ("canonical", "preview", "idle")), len(p.stem)),
    )
    if not ranked:
        return "render produced no png"
    shutil.copy(ranked[0], out / f"{target_id}.png")
    return ""


def _tail(result) -> str:
    lines = (result.stderr or result.stdout).strip().splitlines()
    return (lines[-1] if lines else "no output")[:140]


RUNGS = (_rung_canonical, _rung_config, _rung_render)


def _outputs_of(python: str, root: Path, target_id: str, out: Path) -> str:
    """Run the target's whole render so its output files exist in ``out``.

    A batched target may exit non-zero after writing its files (a missing
    canonical hook), so the exit code is not trusted: the caller looks for the
    file it wants."""
    result = _run(python, root, ["canonical", target_id, "--out-dir", str(out)])
    if any(out.iterdir()):
        return ""
    result = _run(python, root, ["render", target_id])
    generated = root / "generated" / target_id
    if generated.exists():
        for path in generated.rglob("*"):
            if path.is_file():
                shutil.copy(path, out / path.name)
    return "" if any(out.iterdir()) else _tail(result)


def _first_frame(out: Path, sheet: str, animation: str) -> Path | None:
    """Crop the first frame of ``animation`` from ``<sheet>_spritesheet``.

    Reads the sidecar's ``rects`` (packed sheets) or, in older sheets, the grid
    of ``frame_width`` by ``frame_height``. Returns None when neither fits."""
    import re

    from PIL import Image

    png, ron = out / f"{sheet}_spritesheet.png", out / f"{sheet}_spritesheet.ron"
    if not (png.exists() and ron.exists()):
        return None
    text = ron.read_text(encoding="utf-8", errors="replace")
    row = re.search(rf'animation:\s*"{re.escape(animation)}"(.*?)(?=animation:\s*"|\Z)', text, re.S)
    if row is None:
        return None
    body = row.group(1)
    rect = re.search(r"rects:\s*\[\s*\(x:\s*(\d+),\s*y:\s*(\d+),\s*w:\s*(\d+),\s*h:\s*(\d+)", body)
    with Image.open(png) as sheet_image:
        if rect:
            x, y, w, h = map(int, rect.groups())
        else:
            index = re.search(r"row_index:\s*(\d+)", body)
            size = re.search(r"frame_width:\s*(\d+),\s*frame_height:\s*(\d+)", text)
            if not (index and size):
                return None
            w, h = int(size.group(1)), int(size.group(2))
            x, y = 0, int(index.group(1)) * h
        frame = out / f"{sheet}-{animation}-frame0.png"
        sheet_image.convert("RGBA").crop((x, y, x + w, y + h)).save(frame)
    return frame


def _pick(python: str, root: Path, target_id: str, pick: str) -> tuple[Path | None, str]:
    """``file:<name>`` takes a named output; ``frame:<animation>[@<sheet>]``
    takes the first frame of an animation of one of the target's sheets."""
    out = Path(tempfile.mkdtemp(prefix="dh-pick-"))
    failure = _outputs_of(python, root, target_id, out)
    kind, _, spec = pick.partition(":")
    if kind == "file":
        hit = next(out.rglob(spec), None)
        return (hit, "") if hit else (None, failure or f"no output named {spec}")
    animation, _, sheet = spec.partition("@")
    frame = _first_frame(out, sheet or target_id, animation)
    return (frame, "") if frame else (None, failure or f"no {animation} frame in {sheet or target_id}")


def render_still(
    python: str, root: Path, target_ids: list[str], pick: str | None = None
) -> tuple[Path | None, str | None, str]:
    """Try each id, newest name first, and each command, until one draws.
    Returns the PNG (in a temporary directory the caller must move), the id and
    a failure note."""
    if package_of(root) is None:
        return None, None, "the renderer package does not exist at this commit"
    if not _imports_this_tree(python, root):
        return None, None, "the interpreter imports a different renderer than this commit's"
    notes: list[str] = []
    if pick:
        for target_id in target_ids:
            png, failure = _pick(python, root, target_id, pick)
            if png is not None:
                return png, target_id, ""
            notes.append(f"{target_id}/{pick}: {failure}")
        if pick.startswith("file:"):
            return None, None, "; ".join(notes)
        # A frame pick needs a sidecar the early eras do not write: fall back to
        # the era's ordinary still, which for those eras drew the whole thing.
    for target_id in target_ids:
        for rung in RUNGS:
            out = Path(tempfile.mkdtemp(prefix="dh-still-"))
            try:
                failure = rung(python, root, target_id, out)
            except subprocess.TimeoutExpired:
                failure = "timed out"
            png = _png_in(out, target_id)
            if not failure and png is not None:
                return png, target_id, ""
            shutil.rmtree(out, ignore_errors=True)
            notes.append(f"{target_id}/{rung.__name__[6:]}: {failure}")
    return None, None, "; ".join(notes)


def still_for(
    *, python: str, worktrees: Worktrees, cache: Path, seg: Segment, sha: str,
    target_ids: list[str], pick: str | None = None,
) -> Still:
    """The cached still of ``target_ids`` at ``sha``, rendering it if needed."""
    stills = cache / "stills"
    stills.mkdir(parents=True, exist_ok=True)
    key = f"{sha[:12]}-{'+'.join(target_ids)}"
    if pick:
        key += "-" + pick.replace(":", "_").replace("@", "_at_").replace("/", "_")
    hit = stills / f"{key}.png"
    miss = stills / f"{key}.failed"
    if hit.exists():
        return Still(hit, None, pixel_hash(hit))
    if miss.exists():
        return Still(None, None, None, miss.read_text())
    root = worktrees.at(seg, sha)
    png, used, failure = render_still(python, root, target_ids, pick)
    if png is None:
        miss.write_text(failure)
        return Still(None, None, None, failure)
    shutil.move(str(png), hit)
    shutil.rmtree(png.parent, ignore_errors=True)
    (stills / f"{key}.id").write_text(used or "")
    return Still(hit, used, pixel_hash(hit))
