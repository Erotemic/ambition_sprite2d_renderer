"""The red balloon the Hunny Horror rises on.

A small code-generated prop: one transparent PNG the game loads as the
`red_balloon` projectile visual (game/ambition_content/src/projectiles.rs). He
rises on it over the room, lets go and pounces; the balloon floats on and
pops on the ceiling. A round red balloon, lit from the upper left, its knot,
and its string hanging to the bottom of the picture, where his paw holds it.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "red_balloon"
SHEET_FILES = (
    f"{TARGET_NAME}.png",
    # The packed sheet and its sidecars ship too: a published manifest naming
    # an unpublished page is a broken package contract.
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

#: The picture is twice as tall as it is wide: the balloon over its string.
WORK = (256, 576)
FINAL = (128, 288)
OUTPUT_NAME = f"{TARGET_NAME}.png"
ROWS = [("idle", 1, 100)]

OUTLINE = (70, 10, 16, 255)
RED = (214, 30, 40, 255)
RED_DEEP = (150, 14, 26, 255)
RED_LIGHT = (246, 92, 92, 255)
SHINE = (255, 236, 236, 255)
STRING = (60, 52, 56, 255)


def _render_balloon() -> Image.Image:
    img = Image.new("RGBA", WORK, (0, 0, 0, 0))
    d = blending_draw(img)
    cx, cy, rx, ry = WORK[0] / 2, 118.0, 104.0, 112.0
    # The string: from the knot down to the bottom of the picture, with a
    # lazy curl in it.
    pts = []
    for i in range(41):
        t = i / 40
        y = cy + ry + 14 + t * (WORK[1] - (cy + ry + 14) - 4)
        pts.append((cx + 14 * math.sin(t * math.tau * 1.2) * (1 - t * 0.6), y))
    d.line(pts, fill=STRING, width=6, joint="curve")
    # The balloon, a little pointed at the bottom.
    shape = []
    for i in range(96):
        a = math.tau * i / 96
        x = cx + rx * math.cos(a)
        y = cy + ry * math.sin(a)
        if math.sin(a) > 0:
            x = cx + (x - cx) * (1 - 0.18 * math.sin(a) ** 3)
            y += 10 * math.sin(a) ** 6
        shape.append((x, y))
    d.polygon(shape, fill=RED, outline=OUTLINE, width=12)
    d.ellipse((cx - rx * 0.55, cy + ry * 0.32, cx + rx * 0.6, cy + ry * 0.86), fill=RED_DEEP)
    d.ellipse((cx - rx * 0.78, cy - ry * 0.72, cx + rx * 0.3, cy + ry * 0.1), fill=RED_LIGHT)
    d.ellipse((cx - rx * 0.6, cy - ry * 0.62, cx - rx * 0.22, cy - ry * 0.22), fill=SHINE)
    d.polygon(shape, outline=OUTLINE, width=12)
    # The knot.
    k = cy + ry + 6
    d.polygon([(cx - 14, k + 14), (cx, k - 6), (cx + 14, k + 14)], fill=RED_DEEP, outline=OUTLINE, width=6)
    return img.resize(FINAL, Image.Resampling.LANCZOS)


def render_sheet(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_balloon(),
        out_dir=out_dir,
        frame_size=FINAL,
        auto_crop=True,
        crop_margin=4,
    )
    copy2(outputs["canonical_transparent"], out_dir / OUTPUT_NAME)
    return [
        out_dir / OUTPUT_NAME,
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["preview"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_balloon(),
        out_dir=out_dir,
        frame_size=FINAL,
        auto_crop=True,
        crop_margin=4,
    )
    return outputs["canonical_transparent"]


def install(render_dir: str | Path, dest_root: str | Path) -> Iterable[Path]:
    render_dir = Path(render_dir)
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: List[Path] = []
    for name in SHEET_FILES:
        src = render_dir / name
        if src.exists():
            dst = dest_root / name
            dst.write_bytes(src.read_bytes())
            installed.append(dst)
    return installed


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_sheet(out_dir, **opts)
