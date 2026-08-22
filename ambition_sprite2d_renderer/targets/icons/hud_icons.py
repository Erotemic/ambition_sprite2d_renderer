"""HUD icons — the tiny symbols a match's own readouts are drawn from.

Distinct from ``item_icons`` next door, which is ability/item art for review
builds and is not consumed by the game.  Everything here IS consumed, by the
declared-HUD renderer, so its filenames are a contract:
``ambition_demo_smash::STOCK_ICON_ASSET`` names ``hud_stock_icon.png`` and the
renderer loads it by path.

⚠ **drawn white with a dark rim on purpose.**  One icon has to read against a
bright stage and a dark one, and the panel around it is tinted by seat rather
than by this — a coloured icon would fight the colour that says whose panel it
is.  The rim is what keeps it visible on white.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "hud_icons"
SHEET_FILES = ("hud_stock_icon.png",)

#: Rendered big and drawn small — the HUD asks for ~14px, and a 14px source
#: would alias the moment anything scaled it.
ICON_SIZE = (64, 64)


def render_stock_icon(size: Tuple[int, int] = ICON_SIZE) -> Image.Image:
    """One remaining life, as a faceted pip.

    A diamond rather than a circle or a head: the roster's own reference
    fighters are polygons, and a shape with corners survives being drawn at
    fourteen pixels far better than a smooth one, which turns to porridge.
    """
    w, h = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    #  `blending_draw`, never a raw `ImageDraw.Draw`: a raw draw ASSIGNS alpha
    # rather than compositing it, so the translucent rim below would punch a hole
    # in whatever it overlapped instead of darkening it. `test_no_raw_imagedraw`
    # guards this on every content path, and it caught this file.
    draw = blending_draw(image)

    cx, cy = w / 2.0, h / 2.0
    # Slightly taller than wide, so a row of them reads as a row of tokens
    # rather than as a dotted line.
    rx, ry = w * 0.34, h * 0.42
    diamond = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]

    # The rim first, as a fatter diamond underneath — an outline drawn ON the
    # shape eats half the fill at this size.
    rim = 0.14
    outer = [
        (cx, cy - ry * (1.0 + rim)),
        (cx + rx * (1.0 + rim), cy),
        (cx, cy + ry * (1.0 + rim)),
        (cx - rx * (1.0 + rim), cy),
    ]
    draw.polygon(outer, fill=(18, 20, 28, 235))
    draw.polygon(diamond, fill=(245, 247, 252, 255))

    # One facet, top-left, so the pip has a direction and does not read as a
    # flat lozenge. Kept subtle: at 14px this is two or three pixels.
    facet = [(cx, cy - ry), (cx, cy), (cx - rx, cy)]
    draw.polygon(facet, fill=(198, 208, 226, 255))
    return image


def write_hud_icons(out_dir: str | Path, *, size: Tuple[int, int] = ICON_SIZE) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "hud_stock_icon.png"
    render_stock_icon(size).save(path)
    return [path]


def render(out_dir: str | Path, **opts) -> List[Path]:
    """Render every HUD icon into ``out_dir``."""
    return write_hud_icons(out_dir, size=opts.get("size", ICON_SIZE))
