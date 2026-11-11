"""The haunted floors of Hylbert's Hotel (skin `math_haunted`): their art for
the structural roles the game lays by a block's shape (`ornaments.py` has
the table of the roles and the proportions the game reads).

The floating ledges of the haunted wing are marble balconies of the hotel,
held off its walls by carved corbels. So a platform's underhang is a bay of
moulded soffit between two scrolled corbels, with the teal of the ghosts
sagging between them; a long bay hangs a brass ghost lantern; an open end of
a ledge curls down in a marble volute; and what trails below it is the
hotel's neglect (a cobweb veil, a drip of ectoplasm, a broken chain). A large
wall face carries the ellipse of the wallpaper with its two axes, the
eigen-sigil of the wing.

| role | size (units) | what it is |
| --- | --- | --- |
| `underhang` | 128 x 44 | a bay: a corbel at each end (0.12 of the width), a soffit with dentils between |
| `pendant` | 22 x 72 | a brass lantern on a chain, a teal ghost flame in it |
| `ledge_end` | 3 x 48 x 40 | a volute at a left top corner; the corner is at (11/64, 8/52) of the square |
| `trailing` | 3 x 32 x 96 | what hangs below a ledge end, x into the platform from its end |
| `motif` | 76 x 108 | the eigen-sigil, brass with a teal glow |

Colours are the haunted props' (`targets/props/hylbert_haunted_props.py`).
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from .ornaments import strip
from .two_state import Picture, mix, rand_cell, smoothstep

UNDERHANG = (128, 44)
PENDANT = (22, 72)
LEDGE_END = (48, 40)
TRAILING = (32, 96)
MOTIF = (76, 108)
VARIANTS = 3

#: Where the corner of the block is in a ledge-end square (the game reads
#: this fraction of the square: `LEDGE_END_CORNER` in `terrain_skin.rs`).
CORNER = (LEDGE_END[0] * 11.0 / 64.0, LEDGE_END[1] * 8.0 / 52.0)
#: Each end of an underhang bay (`UNDERHANG_END`).
BAY_END = UNDERHANG[0] * 0.12


def rgb(*c: int) -> np.ndarray:
    return np.array(c, dtype=np.float64) / 255.0


OUTLINE = rgb(22, 14, 30)
MARBLE = rgb(92, 78, 108)
MARBLE_LIT = rgb(176, 164, 190)
MARBLE_DEEP = rgb(44, 34, 56)
BRASS = rgb(204, 156, 72)
BRASS_LIT = rgb(250, 214, 140)
BRASS_DARK = rgb(134, 96, 44)
TEAL = rgb(92, 238, 214)
TEAL_CORE = rgb(214, 255, 246)
WEB = rgb(220, 220, 232)


def glow(pic: Picture, distance: np.ndarray, width: float, strength: float, core: float = 0.0) -> None:
    """A teal glow around the lines `distance` is the distance to: a soft halo
    `width` wide, and a pale core `core` wide."""
    halo = np.exp(-np.maximum(distance, 0.0) / max(width, 1e-3)) * strength
    pic.put(halo > 0.01, TEAL, np.clip(halo, 0.0, 1.0))
    if core > 0.0:
        pic.put(distance < core, TEAL_CORE, 0.9)


def segment_distance(x: np.ndarray, y: np.ndarray, a: tuple[float, float], b: tuple[float, float]) -> np.ndarray:
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / max(vx * vx + vy * vy, 1e-9), 0.0, 1.0)
    return np.hypot(x - (ax + t * vx), y - (ay + t * vy))


# ------------------------------------------------------------- underhang --


def corbel(d: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A scrolled corbel whose outer face is at `d` = 0 (the end of the bay):
    where it is marble, and where its edge catches the light. It is as wide
    as the end of the bay at the soffit and narrows to a volute at its foot."""
    top = BAY_END
    width = top - np.clip(y - 4.0, 0.0, None) * 0.30
    body = (d >= 0.0) & (d < width) & (y < 34.0)
    # The volute at its foot: a disc with a spiral cut in it.
    cx, cy, r = top * 0.42, 34.0, 6.2
    rr = np.hypot(d - cx, y - cy)
    ang = np.arctan2(y - cy, d - cx)
    spiral = np.abs(((rr - (ang + np.pi) / (2 * np.pi) * 2.2) % 2.2) - 1.1) < 0.35
    disc = rr < r
    volute = disc & ~(spiral & (rr > 1.2))
    shape = body | volute
    edge = shape & ((d < 1.0) | (np.abs(rr - r) < 0.8))
    # Its inner edge, dark, so it stands off the soffit behind it.
    inner = body & (d > width - 1.0)
    return shape, edge | inner


def underhang() -> Picture:
    pic = Picture(UNDERHANG)
    x, y = pic.x, pic.y
    w = UNDERHANG[0]
    # The soffit: dark marble under the ledge, a brass line along its foot,
    # and a course of dentils.
    soffit = y < 4.0
    pic.put(soffit, mix(MARBLE_DEEP, MARBLE, 0.5))
    pic.put((y >= 3.2) & (y < 4.0), BRASS_DARK)
    dentil = (y >= 4.0) & (y < 7.0) & (np.mod(x, 4.0) < 2.4)
    pic.put(dentil, MARBLE)
    pic.put(dentil & (y < 4.6), MARBLE_LIT, 0.6)
    # The ghosts' teal sags between the corbels, faint, with a few drips.
    sag = 9.0 + 7.0 * (1.0 - ((x - w * 0.5) / (w * 0.5 - BAY_END)) ** 2)
    between = (x > BAY_END) & (x < w - BAY_END)
    d = np.abs(y - sag)
    pic.put(between & (d < 4.0), TEAL, np.clip(0.22 * np.exp(-d / 1.6), 0, 1))
    for k, cx in enumerate((w * 0.31, w * 0.5, w * 0.66)):
        length = (6.0, 11.0, 4.0)[k]
        top = 9.0 + 7.0 * (1.0 - ((cx - w * 0.5) / (w * 0.5 - BAY_END)) ** 2)
        drip = segment_distance(x, y, (cx, top), (cx, top + length))
        glow(pic, drip, 0.5, 0.35, core=0.3)
        glow(pic, np.hypot(x - cx, y - top - length - 0.6), 0.6, 0.45, core=0.6)
    # The two corbels.
    for d in (x, w - x):
        shape, edge = corbel(d, y)
        # Lit on its outer face, falling into shade across it and down it.
        across = np.clip(d / BAY_END, 0.0, 1.0)
        light = np.clip(0.75 - 0.5 * across - 0.25 * np.clip(y / 40.0, 0.0, 1.0), 0.0, 1.0)
        pic.put(shape, mix(MARBLE_DEEP, MARBLE_LIT, light))
        pic.put(edge & (d > 1.0), OUTLINE, 0.7)
        pic.put(edge & (d <= 1.0), MARBLE_LIT, 0.7)
        # A sunk panel down its face.
        panel = shape & (np.abs(d - BAY_END * 0.35) < 0.5) & (y > 8.0) & (y < 26.0)
        pic.put(panel, MARBLE_DEEP, 0.7)
        pic.put(shape & (y >= 3.2) & (y < 4.0), BRASS)
    # A rim of dark under everything solid, so it reads against the paper.
    return pic


# --------------------------------------------------------------- pendant --


def pendant() -> Picture:
    pic = Picture(PENDANT)
    x, y = pic.x, pic.y
    cx = PENDANT[0] * 0.5
    # The chain: brass links from the soffit down to the lantern.
    link = (y < 36.0) & (np.abs(x - cx) < 1.6) & (np.mod(y, 4.0) < 3.0)
    hole = (np.abs(x - cx) < 0.6) & (np.mod(y, 4.0) > 0.8) & (np.mod(y, 4.0) < 2.2) & (np.mod(np.floor(y / 4.0), 2) == 0)
    pic.put(link & ~hole, BRASS_DARK)
    pic.put(link & ~hole & (x < cx - 0.4), BRASS, 0.8)
    # The lantern: a cap, a cage of four bars around a teal flame, a foot.
    ax = np.abs(x - cx)
    cap = (y >= 36.0) & (y < 41.0) & (ax < 4.0 + (y - 36.0) * 0.9)
    cage = (y >= 41.0) & (y < 60.0)
    bars = cage & ((ax > 7.2) & (ax < 8.6) | (ax < 0.7))
    foot = (y >= 60.0) & (y < 64.0) & (ax < 8.6 - (y - 60.0) * 1.6)
    finial = (y >= 64.0) & (y < 70.0) & (ax < 1.6 - (y - 64.0) * 0.22)
    glass = cage & (ax <= 7.2)
    pic.put(glass, mix(MARBLE_DEEP, TEAL, 0.25), 0.55)
    flame_d = np.hypot((x - cx) * 1.6, (y - 51.0) * 0.8 + np.clip(y - 51.0, None, 0.0) * 0.4)
    glow(pic, np.maximum(flame_d - 2.4, 0.0), 2.4, 0.7, core=1.4)
    for part in (cap, bars, foot, finial):
        pic.put(part, BRASS)
    pic.put((cap | foot) & (x < cx), BRASS_LIT, 0.45)
    pic.put(bars & (x > cx), BRASS_DARK, 0.6)
    return pic


# ------------------------------------------------------------- ledge end --


def ledge_end_square(variant: int) -> Picture:
    """The volute at a left top corner. `x` from the left of the square, `y`
    down from its top; the corner of the block is `CORNER`."""
    pic = Picture(LEDGE_END)
    x, y = pic.x, pic.y
    kx, ky = CORNER
    # The cap moulding: it runs along the top of the ledge and rolls over its
    # end, a little proud of both.
    cap = (y >= ky - 0.8) & (y < ky + 2.4) & (x >= kx - 3.0) & (x < kx + 7.0)
    # The volute, hung on the end of the ledge and curling under it.
    cx, cy, r = kx + 1.6, ky + 13.0, 8.5
    rr = np.hypot(x - cx, y - cy)
    ang = np.arctan2(y - cy, x - cx)
    turns = (rr - (ang + np.pi) / (2 * np.pi) * 2.8) % 2.8
    groove = (np.abs(turns - 1.4) < 0.45) & (rr > 1.6)
    disc = rr < r
    stone = disc
    pic.put(stone, MARBLE)
    pic.put(stone & (y < cy), MARBLE_LIT, 0.35)
    pic.put(groove & disc, MARBLE_DEEP, 0.9)
    pic.put(disc & (np.abs(rr - r) < 0.9), OUTLINE, 0.6)
    pic.put(cap, mix(MARBLE_LIT, rgb(255, 255, 255), 0.25))
    pic.put(cap & (y >= ky + 1.6), BRASS)
    pic.put(np.hypot(x - cx, y - cy) < 1.6, BRASS)
    if variant == 1:
        # A cobweb in the crook between the volute and the ledge.
        hub = (cx + r * 0.9, cy - r * 0.15)
        for k in range(5):
            a = np.pi * (0.95 + 0.14 * k)
            tip = (hub[0] + 12.0 * np.cos(a) * -1.0, hub[1] + 12.0 * np.sin(a))
            pic.put(segment_distance(x, y, hub, tip) < 0.22, WEB, 0.45)
        for ring in (3.5, 6.5, 9.5):
            d = np.abs(np.hypot(x - hub[0], y - hub[1]) - ring)
            pic.put((d < 0.2) & (x > hub[0] - 0.5) & (y < hub[1] + ring), WEB, 0.35)
    elif variant == 2:
        # A crack through the volute, the teal of the ghosts in it.
        crack = np.minimum(segment_distance(x, y, (cx - 6.0, cy - 5.0), (cx - 1.0, cy + 1.0)),
                           segment_distance(x, y, (cx - 1.0, cy + 1.0), (cx + 3.0, cy + 8.0)))
        glow(pic, crack, 0.7, 0.6, core=0.35)
    return pic


# -------------------------------------------------------------- trailing --


def trailing_square(variant: int) -> Picture:
    """What hangs below a ledge end: `x` into the platform from its end, `y`
    down from the bottom of the platform."""
    pic = Picture(TRAILING)
    x, y = pic.x, pic.y
    if variant == 0:
        # A veil of cobweb from the volute to the underside, strands hanging.
        top = [(2.0, 0.0), (26.0, 0.0)]
        for k in range(9):
            sx = 3.0 + k * 2.8
            length = 18.0 + 22.0 * rand_cell(np.array(k * 1.0), np.array(3.0), 41)
            sway = np.sin(y * 0.18 + k) * 0.6
            d = np.abs(x - sx - sway)
            pic.put((d < 0.18) & (y < length), WEB, np.clip(0.5 - y / (length * 2.2), 0.05, 0.5))
        sag = 2.0 + 10.0 * np.sin(np.clip((x - top[0][0]) / (top[1][0] - top[0][0]), 0.0, 1.0) * np.pi)
        for ring in (0.0, 4.0):
            pic.put((np.abs(y - sag - ring) < 0.2) & (x > 2.0) & (x < 26.0), WEB, 0.4)
    elif variant == 1:
        # Ectoplasm dripping from the ledge: threads of teal, each with a bead.
        for k, (sx, length) in enumerate(((5.0, 30.0), (11.0, 52.0), (16.0, 22.0), (23.0, 40.0))):
            thread = segment_distance(x, y, (sx, 0.0), (sx + np.sin(k) * 1.2, length))
            glow(pic, thread, 0.45, 0.32, core=0.25)
            bead = np.hypot(x - sx - np.sin(k) * 1.2, (y - length - 1.4) * 0.8)
            glow(pic, np.maximum(bead - 0.9, 0.0), 0.9, 0.7, core=0.9)
    else:
        # A broken chain that once held a lantern, a wisp at its end.
        cx = 9.0
        link = (y < 58.0) & (np.abs(x - cx - np.sin(y * 0.05) * 1.5) < 1.5) & (np.mod(y, 4.0) < 3.0)
        pic.put(link, BRASS_DARK)
        pic.put(link & (x < cx), BRASS, 0.7)
        wisp = np.hypot((x - cx - 2.0) * 0.8, y - 64.0 - np.sin(x * 0.6) * 1.5)
        glow(pic, np.maximum(wisp - 1.2, 0.0), 2.6, 0.5, core=0.8)
    return pic


# ----------------------------------------------------------------- motif --


def motif() -> Picture:
    """The eigen-sigil: the wallpaper's ellipse, tilted, with its two axes
    drawn through it and an arrow at each, in brass, the teal under it."""
    pic = Picture(MOTIF)
    cx, cy = MOTIF[0] * 0.5, MOTIF[1] * 0.5
    t = np.radians(28.0)
    u = (pic.x - cx) * np.cos(t) + (pic.y - cy) * np.sin(t)
    v = -(pic.x - cx) * np.sin(t) + (pic.y - cy) * np.cos(t)
    a, b = 30.0, 16.0
    ring = np.abs(np.hypot(u / a, v / b) - 1.0) * min(a, b)
    major = np.where(np.abs(u) < a + 6.0, np.abs(v), 99.0)
    minor = np.where(np.abs(v) < b + 6.0, np.abs(u), 99.0)
    heads = np.minimum(
        np.hypot(np.abs(u) - a - 6.0, v) - 0.0,
        np.hypot(u, np.abs(v) - b - 6.0),
    )
    lines = np.minimum(np.minimum(ring, major), minor)
    halo = np.hypot(u / (a + 14.0), v / (b + 14.0))
    pic.put(halo < 1.0, TEAL, np.clip((1.0 - halo) * 0.30, 0, 1))
    glow(pic, lines, 1.4, 0.35)
    pic.put(lines < 1.1, BRASS)
    pic.put(lines < 0.45, BRASS_LIT, 0.7)
    pic.put(heads < 2.4, BRASS)
    pic.put(np.hypot(u, v) < 3.0, TEAL_CORE)
    return pic


PAINTERS = {
    ("math_haunted", "underhang"): lambda: underhang().publish(),
    ("math_haunted", "pendant"): lambda: pendant().publish(),
    ("math_haunted", "ledge_end"): lambda: strip([ledge_end_square(v) for v in range(VARIANTS)]),
    ("math_haunted", "trailing"): lambda: strip([trailing_square(v) for v in range(VARIANTS)]),
    ("math_haunted", "motif"): lambda: motif().publish(),
}

SIZES = {
    "underhang": UNDERHANG,
    "pendant": PENDANT,
    "ledge_end": (LEDGE_END[0] * VARIANTS, LEDGE_END[1]),
    "trailing": (TRAILING[0] * VARIANTS, TRAILING[1]),
    "motif": MOTIF,
}


def parts(key: str) -> dict[str, Image.Image]:
    return {part: paint() for (owner, part), paint in PAINTERS.items() if owner == key}
