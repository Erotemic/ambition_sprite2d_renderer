"""A space helmet: the first worn gear (`docs/systems/worn-gear.md` in the game).

Gear is an item a body wears at an anchor of its body (here its head). It is
not painted into the body's art: the game puts it on any body whose sheet
names the anchor, at the fit of that wearer. So this target publishes two
pictures and no sheet:

* ``space_helmet_back.png`` — what is behind the head: the inside of the far
  half of the bubble and the far half of its collar;
* ``space_helmet_front.png`` — what is in front of it: the glass (clear, with
  a tint and its shine), the near half of the collar, and the aerial.

The glass is clear so the face shows through it. The bubble is round, so it is
the same from the front and from the side. The pivot of the head is at
``SOCKET`` (a part of the picture from its top left). No shadow.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import List

from PIL import Image

from ..characters.gnu_ton_boss import _svg as svg

TARGET_NAME = "space_helmet"
#: The two pictures, square, at four times the size the game draws a helmet
#: on a body of the reference size.
SIZE = 256
VIEW = 256.0
#: Where the head's pivot is in the picture (from its top left, 0..1).
SOCKET = (0.5, 0.58)
OUTPUTS = ("space_helmet_back.png", "space_helmet_front.png")
#: What the publish installs: the two pictures, in `sprites/`.
SHEET_FILES = OUTPUTS

INK = "#1b1820"
GLASS = "#bfe6ff"
GLASS_EDGE = "#7fb6d8"
SHINE = "#ffffff"
METAL = "#c9ced8"
METAL_DARK = "#7d8494"
METAL_LIGHT = "#eef1f6"
BULB = "#ff6a4d"

#: The bubble's middle and radius, in the picture's units.
CX, CY, R = 128.0, 118.0, 104.0
#: The collar: a flat ring under the bubble.
COLLAR_Y, COLLAR_RX, COLLAR_RY = 214.0, 84.0, 20.0


def _document(items: List[str]) -> str:
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
            f'viewBox="0 0 {VIEW:g} {VIEW:g}">')
    return "\n".join([head] + items + ["</svg>"])


def _raster(items: List[str]) -> Image.Image:
    import resvg_py

    data = resvg_py.svg_to_bytes(svg_string=_document(items), skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def back() -> List[str]:
    """Behind the head: the inside of the far half of the bubble (a faint
    tint) and the far half of the collar."""
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=2.4, colors={})
    far_glass = f'<circle cx="{CX}" cy="{CY}" r="{R - 2.0}" fill="{GLASS}" fill-opacity="0.16" />'
    collar_back = svg.path(
        f"M{CX - COLLAR_RX:.1f},{COLLAR_Y:.1f} A{COLLAR_RX:.1f},{COLLAR_RY:.1f} 0 0 1 {CX + COLLAR_RX:.1f},{COLLAR_Y:.1f} "
        f"L{CX + COLLAR_RX:.1f},{COLLAR_Y + 10:.1f} A{COLLAR_RX:.1f},{COLLAR_RY:.1f} 0 0 0 {CX - COLLAR_RX:.1f},{COLLAR_Y + 10:.1f} Z",
        METAL_DARK, INK, 3.0)
    return [far_glass, collar_back]


def front() -> List[str]:
    """In front of the head: the glass with its shine, the near half of the
    collar with its bolts, and an aerial with a light."""
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=2.4, colors={})
    out = [
        f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="{GLASS}" fill-opacity="0.22" stroke="{GLASS_EDGE}" stroke-width="7" />',
        f'<circle cx="{CX}" cy="{CY}" r="{R + 3.5}" fill="none" stroke="{INK}" stroke-width="3" />',
    ]
    # The shine: two curves on the upper left of the glass.
    for r, a0, a1, w in ((R - 18.0, 200.0, 250.0, 9.0), (R - 30.0, 205.0, 225.0, 6.0)):
        x0, y0 = CX + r * math.cos(math.radians(a0)), CY + r * math.sin(math.radians(a0))
        x1, y1 = CX + r * math.cos(math.radians(a1)), CY + r * math.sin(math.radians(a1))
        out.append(f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" '
                   f'stroke="{SHINE}" stroke-width="{w}" stroke-linecap="round" stroke-opacity="0.9" />')
    # The near half of the collar, and its bolts.
    out.append(svg.path(
        f"M{CX - COLLAR_RX:.1f},{COLLAR_Y:.1f} A{COLLAR_RX:.1f},{COLLAR_RY:.1f} 0 0 0 {CX + COLLAR_RX:.1f},{COLLAR_Y:.1f} "
        f"L{CX + COLLAR_RX:.1f},{COLLAR_Y + 12:.1f} A{COLLAR_RX:.1f},{COLLAR_RY:.1f} 0 0 1 {CX - COLLAR_RX:.1f},{COLLAR_Y + 12:.1f} Z",
        METAL, INK, 3.0))
    out.append(svg.path(
        f"M{CX - COLLAR_RX + 10:.1f},{COLLAR_Y + 8:.1f} A{COLLAR_RX - 10:.1f},{COLLAR_RY - 6:.1f} 0 0 0 {CX + COLLAR_RX - 10:.1f},{COLLAR_Y + 8:.1f}",
        "none", METAL_LIGHT, 4.0))
    for k in range(-2, 3):
        a = math.radians(90.0 + k * 28.0)
        bx, by = CX + (COLLAR_RX - 6.0) * math.cos(a), COLLAR_Y + 6.0 + (COLLAR_RY - 2.0) * math.sin(a)
        out.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="{METAL_DARK}" stroke="{INK}" stroke-width="1.6" />')
    # The aerial, from the top right of the bubble.
    ax, ay = CX + R * math.cos(math.radians(-55.0)), CY + R * math.sin(math.radians(-55.0))
    tx, ty = ax + 22.0, ay - 34.0
    out.append(f'<path d="M{ax:.1f},{ay:.1f} L{tx:.1f},{ty:.1f}" stroke="{INK}" stroke-width="7" stroke-linecap="round" />')
    out.append(f'<path d="M{ax:.1f},{ay:.1f} L{tx:.1f},{ty:.1f}" stroke="{METAL}" stroke-width="3.5" stroke-linecap="round" />')
    out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="9" fill="{BULB}" stroke="{INK}" stroke-width="2.6" />')
    out.append(f'<circle cx="{tx - 3:.1f}" cy="{ty - 3:.1f}" r="3" fill="{SHINE}" />')
    return out


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, items in zip(OUTPUTS, (back(), front())):
        path = out_dir / name
        _raster(items).save(path)
        paths.append(path)
    return paths


__all__ = ["OUTPUTS", "SHEET_FILES", "SOCKET", "TARGET_NAME", "render"]
