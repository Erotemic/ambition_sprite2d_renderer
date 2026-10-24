"""The sky of GNU-ton's third phase: open space (the game's
`presentation::gnu_ton_sky` draws it behind his hall while the fight is in
space).

Three pictures and no sheet:

* ``gnu_ton_space_stars.png`` — the dark of space and its stars, a tile that
  repeats in both directions;
* ``gnu_ton_space_earth.png`` — the limb of the Earth under it, a band of
  blue land and sea with its thin air, wide, to go along the bottom of the
  room;
* ``gnu_ton_space_moon.png`` — the Moon, round, with its dark seas.

Authored art: no shader draws any of it. No shadow is cast on anything.
"""

from __future__ import annotations

import io
import math
import random
from pathlib import Path
from typing import List

from PIL import Image

TARGET_NAME = "gnu_ton_space"
OUTPUTS = ("gnu_ton_space_stars.png", "gnu_ton_space_earth.png", "gnu_ton_space_moon.png")
#: What the publish installs: the three pictures, in `sprites/gnu_ton_space/`.
SHEET_FILES = OUTPUTS
INSTALL_SUBDIR = "gnu_ton_space"

INK = "#0d0b16"
SPACE = "#0b0c22"
SPACE_DEEP = "#06061a"
STAR = "#fff8e6"
STAR_BLUE = "#bfd8ff"
STAR_GOLD = "#ffe59a"


def _raster(svg_text: str) -> Image.Image:
    import resvg_py

    data = resvg_py.svg_to_bytes(svg_string=svg_text, skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def _star(cx: float, cy: float, r: float, colour: str) -> str:
    """A small four-point star: two thin diamonds, crossed."""
    pts = [(cx, cy - r), (cx + r * 0.22, cy), (cx, cy + r), (cx - r * 0.22, cy)]
    d1 = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    pts = [(cx - r, cy), (cx, cy + r * 0.22), (cx + r, cy), (cx, cy - r * 0.22)]
    d2 = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return f'<path d="{d1}" fill="{colour}" /><path d="{d2}" fill="{colour}" />'


def stars(size: int = 512) -> Image.Image:
    """The dark and its stars, a tile: a star near an edge is drawn again at
    the other edge, so the tile repeats with no seam."""
    rng = random.Random(1687)  # the year of the Principia
    items = [f'<rect x="0" y="0" width="{size}" height="{size}" fill="{SPACE}" />']
    # Two soft clouds of a darker blue: a shape of a colour, not a glow.
    for cx, cy, rx, ry in ((140.0, 380.0, 170.0, 70.0), (390.0, 120.0, 150.0, 60.0)):
        for dx in (-size, 0, size):
            for dy in (-size, 0, size):
                items.append(f'<ellipse cx="{cx + dx:.1f}" cy="{cy + dy:.1f}" rx="{rx}" ry="{ry}" fill="{SPACE_DEEP}" '
                             f'fill-opacity="0.55" transform="rotate(-18 {cx + dx:.1f} {cy + dy:.1f})" />')
    for k in range(150):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.choice((0.9, 1.1, 1.3, 1.6, 2.2))
        colour = rng.choice((STAR, STAR, STAR, STAR_BLUE, STAR_GOLD))
        for dx in (-size, 0, size):
            for dy in (-size, 0, size):
                if -8 < x + dx < size + 8 and -8 < y + dy < size + 8:
                    items.append(f'<circle cx="{x + dx:.1f}" cy="{y + dy:.1f}" r="{r}" fill="{colour}" />')
    for k in range(9):
        x, y = rng.uniform(20, size - 20), rng.uniform(20, size - 20)
        items.append(_star(x, y, rng.uniform(5.0, 9.0), rng.choice((STAR, STAR_BLUE, STAR_GOLD))))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
           + "".join(items) + "</svg>")
    return _raster(svg)


def earth(width: int = 2048, height: int = 512) -> Image.Image:
    """The limb of the Earth: an arc of a great circle across the bottom, the
    sea and the land on it, cloud, and the thin blue air over its edge."""
    r = width * 1.4
    cx, cy = width * 0.5, height * 0.62 + r
    items = []
    # The air: two bands over the limb, blue to clear.
    items.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 26}" fill="#5aa8ff" fill-opacity="0.18" />')
    items.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 12}" fill="#8cc6ff" fill-opacity="0.35" />')
    # The sea, with its ink edge.
    items.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#2f6fc0" stroke="{INK}" stroke-width="4" />')
    # The land: shapes on the arc.
    rng = random.Random(1666)  # the year of the apple
    clip = f'<clipPath id="globe"><circle cx="{cx}" cy="{cy}" r="{r}" /></clipPath>'
    land = []
    for k in range(7):
        x = rng.uniform(80, width - 80)
        y = cy - math.sqrt(max(0.0, r * r - (x - cx) ** 2)) + rng.uniform(30, 160)
        rx, ry = rng.uniform(90, 260), rng.uniform(30, 70)
        land.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#4f9a4a" stroke="{INK}" '
                    f'stroke-width="3" transform="rotate({rng.uniform(-14, 14):.1f} {x:.1f} {y:.1f})" />')
        land.append(f'<ellipse cx="{x + rx * 0.2:.1f}" cy="{y - ry * 0.25:.1f}" rx="{rx * 0.45:.1f}" ry="{ry * 0.35:.1f}" '
                    f'fill="#7cbf5e" />')
    for k in range(9):
        x = rng.uniform(40, width - 40)
        y = cy - math.sqrt(max(0.0, r * r - (x - cx) ** 2)) + rng.uniform(10, 120)
        land.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rng.uniform(70, 180):.1f}" ry="{rng.uniform(10, 22):.1f}" '
                    f'fill="#f4f8ff" fill-opacity="0.85" />')
    # The night side: the right of the arc is dark, behind a curved edge.
    land.append(f'<ellipse cx="{width * 1.08:.1f}" cy="{height * 1.1:.1f}" rx="{width * 0.36:.1f}" ry="{height * 1.0:.1f}" '
                f'fill="#0b1640" fill-opacity="0.55" />')
    items.append(clip + '<g clip-path="url(#globe)">' + "".join(land) + "</g>")
    items.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="4" />')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
           + "".join(items) + "</svg>")
    return _raster(svg)


def moon(size: int = 256) -> Image.Image:
    """The Moon: grey, its dark seas, a few round craters, its ink edge."""
    c, r = size * 0.5, size * 0.44
    items = [f'<circle cx="{c}" cy="{c}" r="{r}" fill="#d9d6cc" stroke="{INK}" stroke-width="4" />']
    for x, y, rx, ry in ((0.38, 0.36, 0.16, 0.11), (0.62, 0.46, 0.13, 0.12), (0.46, 0.62, 0.18, 0.09)):
        items.append(f'<ellipse cx="{x * size:.1f}" cy="{y * size:.1f}" rx="{rx * size:.1f}" ry="{ry * size:.1f}" fill="#a9a59b" />')
    for x, y, rr in ((0.30, 0.58, 0.04), (0.70, 0.30, 0.035), (0.58, 0.72, 0.03), (0.24, 0.40, 0.025)):
        items.append(f'<circle cx="{x * size:.1f}" cy="{y * size:.1f}" r="{rr * size:.1f}" fill="#bdb9ae" stroke="#8e8a80" '
                     f'stroke-width="2" />')
    # The dark side, on the right.
    items.append(f'<path d="M{c:.1f},{c - r:.1f} A{r:.1f},{r:.1f} 0 0 1 {c:.1f},{c + r:.1f} '
                 f'A{r * 0.55:.1f},{r:.1f} 0 0 0 {c:.1f},{c - r:.1f} Z" fill="#1d1c2c" fill-opacity="0.55" />')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
           + "".join(items) + "</svg>")
    return _raster(svg)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, picture in zip(OUTPUTS, (stars(), earth(), moon())):
        path = out_dir / name
        picture.save(path)
        paths.append(path)
    return paths


__all__ = ["INSTALL_SUBDIR", "OUTPUTS", "SHEET_FILES", "TARGET_NAME", "render"]
