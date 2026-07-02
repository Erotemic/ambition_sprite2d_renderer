"""Debug + interchange tools built on the per-frame :mod:`frame_source` API.

Because a :class:`~.frame_source.FrameSource` renders every frame independently
at any resolution, two things fall out for free:

* :func:`export_frames` — write one PNG per frame plus a JSON index, so an
  external / custom packing algorithm can consume the raw frames.
* :func:`contact_sheet` — lay every frame out in a labeled grid, optionally with
  the source's authored gameplay geometry (hit/hurt boxes, body inset) drawn on
  top, for eyeballing what a generator actually produces at a given size.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw

from .frame_source import FrameSource, render_all_frames, render_animation
from ..core.draw import font as load_font


def export_frames(
    source: FrameSource, size: Tuple[int, int], out_dir: Path
) -> List[Path]:
    """Render every frame independently at ``size`` and write one PNG each, plus a
    ``frames.json`` index (target, size, and per-frame animation/index/duration/
    filename). The index is what a custom packer reads to place the frames."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = render_all_frames(source, size)
    written: List[Path] = []
    index = {
        "target": source.target,
        "width": size[0],
        "height": size[1],
        "frames": [],
    }
    for fr in frames:
        name = f"{source.target}__{fr.animation}__{fr.index:03d}.png"
        path = out_dir / name
        fr.image.save(path)
        written.append(path)
        index["frames"].append(
            {
                "file": name,
                "animation": fr.animation,
                "index": fr.index,
                "count": fr.count,
                "duration_ms": fr.duration_ms,
            }
        )
    index_path = out_dir / "frames.json"
    index_path.write_text(json.dumps(index, indent=1))
    written.append(index_path)
    return written


def _draw_box(draw: ImageDraw.ImageDraw, box: dict, outline, ox: int, oy: int) -> None:
    x, y, w, h = int(box["x"]), int(box["y"]), int(box["w"]), int(box["h"])
    draw.rectangle((ox + x, oy + y, ox + x + w, oy + y + h), outline=outline, width=1)


def _overlay_geometry(
    draw: ImageDraw.ImageDraw,
    source: FrameSource,
    animation: str,
    size: Tuple[int, int],
    ox: int,
    oy: int,
) -> None:
    """Draw the source's authored gameplay geometry *for this animation* (in
    source-canvas pixels, matching ``size``) onto a frame placed at ``(ox, oy)``.
    Geometry is keyed by animation, so a hitbox only overlays its own row."""
    hurt = source.hurtbox_parts(size) or {}
    hit = source.attack_hitboxes(size) or {}
    for spec, colour in ((hurt, (90, 200, 255, 255)), (hit, (255, 90, 120, 255))):
        entry = spec.get(animation)
        if not isinstance(entry, dict):
            continue
        if isinstance(entry.get("bbox"), tuple):
            x, y, w, h = entry["bbox"]
            draw.rectangle(
                (ox + int(x), oy + int(y), ox + int(x) + int(w), oy + int(y) + int(h)),
                outline=colour,
                width=1,
            )
        for part in entry.get("parts", []) or []:
            if isinstance(part, dict):
                _draw_box(draw, part, colour, ox, oy)
        poly = entry.get("poly")
        if isinstance(poly, list) and len(poly) >= 3:
            draw.polygon(
                [(ox + float(px), oy + float(py)) for px, py in poly], outline=colour
            )


def contact_sheet(
    source: FrameSource,
    size: Tuple[int, int],
    *,
    overlay_geometry: bool = True,
    columns: Optional[int] = None,
    bg=(28, 30, 38, 255),
) -> Image.Image:
    """Lay every frame out in a labeled grid — one row per animation — at the
    given render ``size``. With ``overlay_geometry`` the source's authored
    hit/hurt boxes are drawn on each frame. A pure inspection artifact; never a
    runtime asset."""
    fw, fh = size
    label_h = 16
    cell_w, cell_h = fw + 2, fh + label_h + 2
    animations = list(source.animations())
    max_cols = columns or max(
        (source.animations()[a]["frames"] for a in animations), default=1
    )
    grid_w = max(1, max_cols) * cell_w + 90
    grid_h = max(1, len(animations)) * cell_h
    sheet = Image.new("RGBA", (grid_w, grid_h), bg)
    draw = ImageDraw.Draw(sheet, "RGBA")
    font = load_font(11)

    for row, animation in enumerate(animations):
        y0 = row * cell_h
        draw.text((4, y0 + fh // 2), animation, fill=(220, 224, 230, 255), font=font)
        for fr in render_animation(source, animation, size):
            ox = 90 + fr.index * cell_w
            oy = y0
            sheet.alpha_composite(fr.image.convert("RGBA"), (ox, oy))
            draw.rectangle((ox, oy, ox + fw, oy + fh), outline=(70, 74, 84, 255), width=1)
            if overlay_geometry:
                _overlay_geometry(draw, source, animation, size, ox, oy)
            draw.text((ox + 2, oy + fh + 1), str(fr.index), fill=(150, 155, 165, 255), font=font)
    return sheet
