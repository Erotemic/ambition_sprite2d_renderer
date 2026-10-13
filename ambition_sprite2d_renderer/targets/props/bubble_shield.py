"""The bubble shield: the field about a body that guards, as three pictures.

The game draws ``bubble_shield_field.png`` about a body whose shield is up,
and gives it a colour for its state (`ambition_render`'s ``bubble_shield.rs``).
On a device with a budget for shaders, a second layer is drawn on it from the
other two pictures (``bubble_shield_fx.wgsl``): the lattice shows near the rim
and where a blow was taken, and the cracks grow as the guard is spent.

All three are WHITE: the game gives the hue, because the hue is the state of
the guard (blue whole, red spent, gold for a parry).

* ``field``: a bubble seen from the front, in flat bands as the rest of the
  game is drawn: a thin interior the body shows through, a deeper band toward
  the edge, a bright crisp rim, and two glints of glass.
* ``lattice``: a honeycomb of thin lines that TILES in both directions. The
  shader wraps it on the bubble as on a ball. Its alpha is the line.
* ``cracks``: cracks that start at the rim and branch toward the middle. The
  alpha is the line. The red channel is WHEN that part of the crack shows:
  0 at the rim (it shows first), 1 at the tip that shows last. The shader
  shows the part whose red is under how far the guard is spent.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image, ImageChops, ImageDraw

from ...authoring.sheet_build import build_sheet

TARGET_NAME = "bubble_shield"
SIZE = 256
SUPER = 4
ROWS = [("field", 1, 100), ("lattice", 1, 100), ("cracks", 1, 100)]
PICTURES = ("field", "lattice", "cracks")
SHEET_FILES = tuple(f"{TARGET_NAME}_{name}.png" for name in PICTURES) + (
    # The packed sheet and its sidecars ship too: a published manifest naming
    # an unpublished page is a broken package contract.
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

#: The honeycomb: columns across the tile, and periods (two rows) down it.
#: The cells are 4% wider than a true honeycomb so that both are whole numbers.
LATTICE_COLUMNS, LATTICE_PERIODS = 5, 3


def _white(alpha: Image.Image) -> Image.Image:
    white = Image.new("L", alpha.size, 255)
    return Image.merge("RGBA", (white, white, white, alpha))


def _field() -> Image.Image:
    n = SIZE * SUPER
    c = n / 2
    alpha = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(alpha)

    def disc(radius: float, value: int) -> None:
        r = radius * c
        d.ellipse((c - r, c - r, c + r, c + r), fill=value)

    # From the edge to the middle: the rim, the deep band, the thin interior.
    disc(0.940, 245)
    disc(0.895, 150)
    disc(0.860, 112)
    disc(0.700, 84)
    disc(0.470, 66)
    # A second thin ring inside the rim, as glass has.
    ring = Image.new("L", (n, n), 0)
    rd = ImageDraw.Draw(ring)
    for radius, value in ((0.805, 150), (0.790, 0)):
        r = radius * c
        rd.ellipse((c - r, c - r, c + r, c + r), fill=value)
    alpha = ImageChops.lighter(alpha, ring)
    # The glints: a crescent at the upper left, and a short one at the lower right.
    glint = Image.new("L", (n, n), 0)
    gd = ImageDraw.Draw(glint)

    def crescent(r_out: float, r_in: float, start: float, end: float, value: int) -> None:
        pts = []
        steps = 40
        for i in range(steps + 1):
            a = math.radians(start + (end - start) * i / steps)
            pts.append((c + r_out * c * math.cos(a), c + r_out * c * math.sin(a)))
        for i in range(steps + 1):
            a = math.radians(end - (end - start) * i / steps)
            # narrow at both ends
            t = i / steps
            r = r_in + (r_out - r_in) * (1.0 - math.sin(math.pi * t)) * 0.92
            pts.append((c + r * c * math.cos(a), c + r * c * math.sin(a)))
        gd.polygon(pts, fill=value)

    crescent(0.74, 0.60, 196.0, 262.0, 225)
    crescent(0.74, 0.66, 30.0, 58.0, 170)
    r = 0.045 * c
    gx, gy = c + 0.50 * c * math.cos(math.radians(276.0)), c + 0.50 * c * math.sin(math.radians(276.0))
    gd.ellipse((gx - r, gy - r, gx + r, gy + r), fill=210)
    alpha = ImageChops.lighter(alpha, glint)
    return _white(alpha.resize((SIZE, SIZE), Image.Resampling.LANCZOS))


def _lattice() -> Image.Image:
    """The honeycomb, from the distance of each pixel to the nearest edge of a
    cell. Made from a formula that repeats, so the tile has no seam."""
    n = SIZE * SUPER
    alpha = Image.new("L", (n, n), 0)
    px = alpha.load()
    a = n / LATTICE_COLUMNS  # the width of a cell
    row = n / (LATTICE_PERIODS * 2)  # the distance between two rows of centres
    line = 0.035 * a
    for y in range(n):
        for x in range(n):
            # the two nearest centres are in this row of centres and the next
            best = 1e9
            second = 1e9
            j0 = math.floor(y / row)
            for j in (j0, j0 + 1):
                cy = j * row
                shift = 0.5 * a if j % 2 else 0.0
                i0 = round((x - shift) / a)
                for i in (i0 - 1, i0, i0 + 1):
                    cx = i * a + shift
                    # distance in the shape of the cell: y is stretched so that a row counts as a true row
                    dx, dy = x - cx, (y - cy) * (a * math.sqrt(3) / 2) / row
                    dist = math.hypot(dx, dy)
                    if dist < best:
                        best, second = dist, best
                    elif dist < second:
                        second = dist
            # on an edge the two nearest centres are as far as each other
            edge = (second - best) * 0.5
            px[x, y] = int(255 * max(0.0, min(1.0, (line - edge) / (line * 0.5) + 0.5)))
    return _white(alpha.resize((SIZE, SIZE), Image.Resampling.LANCZOS))


def _cracks() -> Image.Image:
    n = SIZE * SUPER
    c = n / 2
    line = Image.new("L", (n, n), 0)
    when = Image.new("L", (n, n), 0)
    ld, wd = ImageDraw.Draw(line), ImageDraw.Draw(when)
    rng = random.Random(7)

    def grow(x: float, y: float, heading: float, length: float, width: float, t0: float, t1: float, depth: int) -> None:
        steps = max(3, int(length / (0.035 * n)))
        for k in range(steps):
            t = t0 + (t1 - t0) * k / steps
            heading += rng.uniform(-0.38, 0.38)
            step = length / steps
            nx, ny = x + step * math.cos(heading), y + step * math.sin(heading)
            w = max(SUPER * 1.2, width * (1.0 - 0.6 * k / steps))
            ld.line([(x, y), (nx, ny)], fill=255, width=int(w))
            wd.line([(x, y), (nx, ny)], fill=int(255 * min(1.0, t)), width=int(w) + SUPER * 2)
            x, y = nx, ny
            if depth < 2 and rng.random() < 0.42:
                side = rng.choice((-1.0, 1.0))
                grow(x, y, heading + side * rng.uniform(0.6, 1.1), length * rng.uniform(0.3, 0.5), w * 0.7,
                     t, min(1.0, t + (t1 - t0) * 0.6), depth + 1)

    # Each crack starts on the rim and goes toward the middle. They do not start at once.
    for start, first in ((38.0, 0.0), (205.0, 0.18), (300.0, 0.36), (118.0, 0.5)):
        a = math.radians(start)
        x, y = c + 0.93 * c * math.cos(a), c + 0.93 * c * math.sin(a)
        grow(x, y, a + math.pi + rng.uniform(-0.2, 0.2), 0.72 * c, SUPER * 4.2, first, min(1.0, first + 0.55), 0)
    # Only inside the bubble.
    mask = Image.new("L", (n, n), 0)
    r = 0.93 * c
    ImageDraw.Draw(mask).ellipse((c - r, c - r, c + r, c + r), fill=255)
    line = ImageChops.multiply(line, mask)
    size = (SIZE, SIZE)
    white = Image.new("L", size, 255)
    return Image.merge("RGBA", (when.resize(size, Image.Resampling.LANCZOS), white, white,
                                line.resize(size, Image.Resampling.LANCZOS)))


_DRAW = {"field": _field, "lattice": _lattice, "cracks": _cracks}
_CACHE: dict = {}


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if animation not in _CACHE:
        _CACHE[animation] = _DRAW[animation]()
    return _CACHE[animation].copy()


# Not a character: a `prop_` id keeps the actor-contract emitter from filing
# the sheet under the `npc_` names.
ACTOR_METADATA = {
    "actor": {"character_id": "prop_bubble_shield", "display_name": "Bubble Shield"},
    "visual_description": {
        "intent": "The field about a body that guards: a flat-banded bubble, a honeycomb and cracks, all white.",
        "visual_language": ["white: the game gives the hue, which is the state of the guard"],
    },
    "tags": ["effect", "shield"],
}


def _build(out_dir: Path):
    return build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=(SIZE, SIZE),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
    )


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = _build(out_dir)
    pictures = []
    for name in PICTURES:
        path = out_dir / f"{TARGET_NAME}_{name}.png"
        render_frame(name, 0, 1).save(path)
        pictures.append(path)
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return pictures + [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return _build(out_dir)["canonical_transparent"]


def install(render_dir: str | Path, dest_root: str | Path) -> Iterable[Path]:
    render_dir = Path(render_dir)
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: List[Path] = []
    for name in SHEET_FILES:
        src = render_dir / name
        if src.exists():
            dst = dest_root / name
            copy2(src, dst)
            installed.append(dst)
    return installed


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "install", "render", "render_canonical", "render_frame"]
