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

Frames are obtained per target through its ``render_sheet`` output — every
target already knows how to render its sheet, so we render once, read the
manifest, and reconstruct each logical frame (trimmed crop pasted back at its
offset). As module targets migrate to a native ``frame_source()`` this can skip
the render+extract round-trip and pack native frames directly.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from PIL import Image

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
    frames: List[PackedFrame] = field(default_factory=list)

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


def _frames_from_target(target, tmp: Path) -> List[Tuple[FrameInput, dict]]:
    """Render one target's sheet into ``tmp`` and reconstruct every logical
    frame. Returns ``(FrameInput, meta)`` pairs where meta carries the source
    animation/index/duration for the catalog."""
    target.render_sheet(tmp)
    manifest_path = tmp / f"{target.name}_spritesheet.yaml"
    if not manifest_path.exists():
        return []  # multi-file / bespoke target without a standard sheet manifest
    manifest = yaml.safe_load(manifest_path.read_text()) or {}
    fw = int(manifest.get("frame_width", 0))
    fh = int(manifest.get("frame_height", 0))
    if fw <= 0 or fh <= 0:
        return []
    # Page filenames: the config manifest omits `image`/`images` (only the RON
    # carries them), so fall back to the conventional page-0 name.
    page_names = manifest.get("images") or [
        manifest.get("image") or f"{target.name}_spritesheet.png"
    ]
    pages = [Image.open(tmp / name).convert("RGBA") for name in page_names if name]
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
            key = (target.name, anim, idx)
            out.append(
                (
                    FrameInput(key=key, image=logical, logical_size=(fw, fh)),
                    {"target": target.name, "animation": anim, "index": idx, "duration_ms": duration_ms},
                )
            )
    return out


def ultrapack(targets, *, page_size: int = 2048, max_dim: int = 16384) -> UltraPack:
    """Pool every target's frames and MaxRects-pack them into uniform pages."""
    inputs: List[FrameInput] = []
    meta: Dict[object, dict] = {}
    with tempfile.TemporaryDirectory() as td:
        for target in targets:
            tdir = Path(td) / target.name
            tdir.mkdir(parents=True, exist_ok=True)
            try:
                pairs = _frames_from_target(target, tdir)
            except Exception:
                continue  # a bespoke target we can't read a standard manifest from
            for fi, m in pairs:
                inputs.append(fi)
                meta[fi.key] = m
        result = pack_frames(inputs, max_dim=max_dim, page_size=page_size, padding=1, trim=True)

    packed = UltraPack(page_size=page_size, pages=result.pages)
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


def write_pack(pack: UltraPack, out_dir: Path, *, name: str = "ultrapack") -> List[Path]:
    """Write the shared page PNGs + a catalog JSON. Returns every written path."""
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
