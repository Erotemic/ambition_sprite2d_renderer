"""Ultrapacking: repack every target's frames into shared, uniformly-sized pages.

At publish time a single-frame static prop is no longer its own PNG file — its
frame is packed into whatever shared atlas page it fits in, alongside frames
from every other target. Every page is the same size (``page_size``). This is
the cross-target counterpart to per-target sheet building: one frame pool, one
MaxRects packer, N uniform pages.

First pass = general packing (best-fit across the whole pool). Memory-locality
grouping (keep a target's or a zone's frames co-resident on a page) can be
layered on later via pack groups; this pass deliberately packs everything into
the tightest set of uniform pages.

Frames enter the pool two ways:

* ``ultrapack(targets)`` renders each target's sheet fresh, reads the manifest,
  and reconstructs each logical frame (trimmed crop pasted back at its offset).
* ``ultrapack_rendered(sheet_dir)`` reads the *already-published* per-target
  sheets in a directory — no re-render. This is the efficient regen path: the
  main regen renders every sheet once, then the pool is packed straight from
  those sheets.

**Quality tiers.** A pack is produced at a ``scale`` (1.0 = authored, 0.5, 0.25,
1/16 potato). Each *isolated* logical frame is downsampled to the tier budget
*before* it enters the packer, then packed into fresh tier-local pages. This is
the sanctioned quality path (see
``docs/planning/engine/data-driven-sprites-and-characters.md`` and
``scripts/generate_visual_quality_variants.py``): never resize an
already-packed atlas page — packed neighbours bleed across frame edges — but a
lone frame may be downsampled and repacked freely. ``min_frame_px`` floors each
scaled frame so potato atlases stay loadable.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml
from PIL import Image, ImageDraw

from .packer import FrameInput, pack_frames


@dataclass
class PackedFrame:
    """One frame's placement in the shared atlas, plus what it needs to be
    addressed at runtime (source target/animation/index + trim + logical size)."""

    target: str
    animation: str
    index: int
    duration_ms: int
    page: int
    x: int
    y: int
    w: int
    h: int
    off_x: int
    off_y: int
    src_w: int
    src_h: int


@dataclass
class UltraPack:
    page_size: int
    pages: List[Image.Image]
    scale: float = 1.0
    frames: List[PackedFrame] = field(default_factory=list)

    def fill_fraction(self) -> float:
        """Packed pixel area / total page area — how tightly the pool packed."""
        if not self.pages:
            return 0.0
        used = sum(f.w * f.h for f in self.frames)
        total = self.page_size * self.page_size * len(self.pages)
        return used / total if total else 0.0

    def catalog(self, page_names: List[str]) -> dict:
        """A plain-dict catalog: uniform page list + every frame's placement,
        grouped by target -> animation -> [frames]."""
        by_target: Dict[str, Dict[str, list]] = {}
        for f in self.frames:
            anim = by_target.setdefault(f.target, {}).setdefault(f.animation, [])
            anim.append(
                {
                    "index": f.index,
                    "page": f.page,
                    "x": f.x,
                    "y": f.y,
                    "w": f.w,
                    "h": f.h,
                    "off": [f.off_x, f.off_y],
                    "src": [f.src_w, f.src_h],
                    "duration_ms": f.duration_ms,
                }
            )
        return {
            "page_size": self.page_size,
            "scale": self.scale,
            "pages": page_names,
            "targets": by_target,
        }


def _reconstruct_logical(page: Image.Image, rect: dict, src_w: int, src_h: int) -> Image.Image:
    """Rebuild a frame's logical (untrimmed) image from a sheet: crop the packed
    rect and paste it back at its trim offset in a transparent logical canvas."""
    x, y, w, h = int(rect["x"]), int(rect["y"]), int(rect["w"]), int(rect["h"])
    crop = page.crop((x, y, x + w, y + h))
    off = rect.get("off") or (0, 0)
    logical = Image.new("RGBA", (src_w, src_h), (0, 0, 0, 0))
    logical.paste(crop, (int(off[0]), int(off[1])))
    return logical


def _scale_logical(
    logical: Image.Image, scale: float, min_px: int
) -> Tuple[Image.Image, Tuple[int, int]]:
    """Downsample an *isolated* logical frame to a quality tier.

    Returns ``(image, (w, h))`` at the tier size. ``scale >= 1.0`` is a no-op.
    Below the potato threshold we use nearest-neighbour for deliberate crunchy
    pixels; otherwise LANCZOS for a clean reduction. Every side is floored at
    ``min_px`` so a frame never collapses to nothing.
    """
    if scale >= 1.0:
        return logical, logical.size
    w, h = logical.size
    nw = max(min_px, round(w * scale))
    nh = max(min_px, round(h * scale))
    resample = Image.NEAREST if scale <= 0.125 else Image.LANCZOS
    return logical.resize((nw, nh), resample), (nw, nh)


def _read_sheet_frames(
    sheet_dir: Path, stem: str, *, scale: float, min_px: int
) -> List[Tuple[FrameInput, dict]]:
    """Read one published sheet (``{stem}_spritesheet.yaml`` + its page PNGs) in
    ``sheet_dir`` and reconstruct every logical frame (scaled to the tier).

    Returns ``(FrameInput, meta)`` pairs where meta carries the source
    animation/index/duration for the catalog. Empty for a bespoke/multi-file
    target without a standard single-sheet manifest.
    """
    manifest_path = sheet_dir / f"{stem}_spritesheet.yaml"
    if not manifest_path.exists():
        return []
    manifest = yaml.safe_load(manifest_path.read_text()) or {}
    fw = int(manifest.get("frame_width", 0))
    fh = int(manifest.get("frame_height", 0))
    if fw <= 0 or fh <= 0:
        return []
    # Page filenames: the config manifest omits `image`/`images` (only the RON
    # carries them), so fall back to the conventional page-0 name.
    page_names = manifest.get("images") or [
        manifest.get("image") or f"{stem}_spritesheet.png"
    ]
    pages = [Image.open(sheet_dir / n).convert("RGBA") for n in page_names if n]
    out: List[Tuple[FrameInput, dict]] = []
    for row in manifest.get("rows", []):
        anim = row.get("animation", "")
        duration_ms = int(row.get("duration_ms", 0))
        row_page = int(row.get("page", 0))
        for idx, rect in enumerate(row.get("rects", [])):
            page_idx = int(rect.get("fpage", rect.get("page", row_page)))
            if page_idx >= len(pages):
                continue
            logical = _reconstruct_logical(pages[page_idx], rect, fw, fh)
            image, logical_size = _scale_logical(logical, scale, min_px)
            key = (stem, anim, idx)
            out.append(
                (
                    FrameInput(key=key, image=image, logical_size=logical_size),
                    {"target": stem, "animation": anim, "index": idx, "duration_ms": duration_ms},
                )
            )
    return out


def _frames_from_target(
    target, tmp: Path, *, scale: float, min_px: int
) -> List[Tuple[FrameInput, dict]]:
    """Render one target's sheet into ``tmp`` then read its logical frames."""
    target.render_sheet(tmp)
    return _read_sheet_frames(tmp, target.name, scale=scale, min_px=min_px)


def _pack_pool(
    pairs: Sequence[Tuple[FrameInput, dict]],
    *,
    scale: float,
    page_size: int,
    max_dim: int,
) -> UltraPack:
    """Pack a pool of ``(FrameInput, meta)`` pairs into uniform shared pages."""
    inputs = [fi for fi, _m in pairs]
    meta = {fi.key: m for fi, m in pairs}
    result = pack_frames(inputs, max_dim=max_dim, page_size=page_size, padding=1, trim=True)
    packed = UltraPack(page_size=page_size, pages=result.pages, scale=scale)
    for key, pl in result.placements.items():
        m = meta[key]
        packed.frames.append(
            PackedFrame(
                target=m["target"],
                animation=m["animation"],
                index=m["index"],
                duration_ms=m["duration_ms"],
                page=pl.page,
                x=pl.x,
                y=pl.y,
                w=pl.w,
                h=pl.h,
                off_x=pl.off_x,
                off_y=pl.off_y,
                src_w=pl.src_w,
                src_h=pl.src_h,
            )
        )
    return packed


def ultrapack(
    targets,
    *,
    scale: float = 1.0,
    min_frame_px: int = 1,
    page_size: int = 2048,
    max_dim: int = 16384,
) -> UltraPack:
    """Render every target fresh and pool its frames into uniform pages."""
    pairs: List[Tuple[FrameInput, dict]] = []
    with tempfile.TemporaryDirectory() as td:
        for target in targets:
            tdir = Path(td) / target.name
            tdir.mkdir(parents=True, exist_ok=True)
            try:
                pairs.extend(
                    _frames_from_target(target, tdir, scale=scale, min_px=min_frame_px)
                )
            except Exception:
                continue  # a bespoke target we can't read a standard manifest from
    return _pack_pool(pairs, scale=scale, page_size=page_size, max_dim=max_dim)


def ultrapack_rendered(
    sheet_dir: Path,
    *,
    stems: Optional[Sequence[str]] = None,
    scale: float = 1.0,
    min_frame_px: int = 1,
    page_size: int = 2048,
    max_dim: int = 16384,
) -> UltraPack:
    """Pool frames from the *already-published* per-target sheets in ``sheet_dir``
    (no re-render). ``stems`` limits which sheets to include; ``None`` packs
    every ``*_spritesheet.yaml`` found at the top level of ``sheet_dir``."""
    sheet_dir = Path(sheet_dir)
    if stems is None:
        stems = sorted(
            p.name[: -len("_spritesheet.yaml")]
            for p in sheet_dir.glob("*_spritesheet.yaml")
        )
    pairs: List[Tuple[FrameInput, dict]] = []
    for stem in stems:
        try:
            pairs.extend(
                _read_sheet_frames(sheet_dir, stem, scale=scale, min_px=min_frame_px)
            )
        except Exception:
            continue
    return _pack_pool(pairs, scale=scale, page_size=page_size, max_dim=max_dim)


def write_pack(pack: UltraPack, out_dir: Path, *, name: str = "ultrapack") -> List[Path]:
    """Write the shared page PNGs + a catalog JSON (runtime artifacts only).

    Diagnostics are NOT written here — see ``write_debug_views`` for the
    opt-in labeled/overlay sheets, which land under ``diagnostics/`` so the
    publish output stays clean by default."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    page_names = [f"{name}_{i}.png" for i in range(len(pack.pages))]
    for img, pname in zip(pack.pages, page_names):
        p = out_dir / pname
        img.save(p)
        written.append(p)
    catalog_path = out_dir / f"{name}.json"
    catalog_path.write_text(json.dumps(pack.catalog(page_names), indent=1, sort_keys=True))
    written.append(catalog_path)
    return written


def _checkerboard(size: Tuple[int, int], cell: int = 16) -> Image.Image:
    """Opaque grey checkerboard so packed transparency reads in a debug view."""
    w, h = size
    board = Image.new("RGBA", size, (52, 52, 60, 255))
    draw = ImageDraw.Draw(board)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(70, 70, 80, 255))
    return board


def write_debug_views(pack: UltraPack, out_dir: Path, *, name: str = "ultrapack") -> List[Path]:
    """Opt-in diagnostics: each page over a checkerboard with per-frame rect
    outlines, plus a text pack report. Written under ``out_dir/diagnostics/`` so
    they never mix with the runtime pages + catalog."""
    diag_dir = Path(out_dir) / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for i, page in enumerate(pack.pages):
        view = _checkerboard(page.size)
        view.alpha_composite(page)
        draw = ImageDraw.Draw(view)
        for f in pack.frames:
            if f.page != i:
                continue
            draw.rectangle([f.x, f.y, f.x + f.w - 1, f.y + f.h - 1], outline=(0, 255, 170, 200))
        p = diag_dir / f"{name}_{i}_debug.png"
        view.convert("RGB").save(p)
        written.append(p)

    by_target: Dict[str, int] = {}
    for f in pack.frames:
        by_target[f.target] = by_target.get(f.target, 0) + 1
    lines = [
        f"ultrapack '{name}'",
        f"scale        : {pack.scale:g}",
        f"page_size    : {pack.page_size}",
        f"pages        : {len(pack.pages)}",
        f"frames       : {len(pack.frames)}",
        f"targets      : {len(by_target)}",
        f"fill         : {pack.fill_fraction() * 100:.1f}%",
        "",
        "frames per target:",
    ]
    for stem in sorted(by_target):
        lines.append(f"  {stem}: {by_target[stem]}")
    report = diag_dir / f"{name}_report.txt"
    report.write_text("\n".join(lines) + "\n")
    written.append(report)
    return written
