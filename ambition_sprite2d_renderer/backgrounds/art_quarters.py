"""The scenes of the four quarters of the Art dimension.

The Art dimension (`art_dimension.py`) is painting. Its four quarters are the
other arts: fiction, music, performance and teknis (the art of making). Each
quarter has its own look:

- ``art_stacks`` (fiction: the Story Stacks). A sky of old paper in the late
  sun. Letters fly in it as birds do. Far off, shelves of books stand as
  cliffs, open books are the hills, and a river of handwriting runs between
  them. Near are books as tall as trees and a quill stuck in the ground.
- ``art_resonance`` (music: the Resonant Reach). A night over a sea of
  cloud. Five-line staves float as roads, with notes on them, and sound
  goes out in cyan rings. Organ pipes stand out of the cloud as towers, and
  a great clef drifts. Near are tuning forks and a ledge of piano keys.
- ``art_stage`` (performance: the Amphitheatre). Dusk on the heights. Flats
  of painted scenery (a cloud, a moon, a star) hang on wires in front of
  the real sky. Far off, the tiers of an amphitheatre are cut in the hill,
  with a small lit stage. Near, red curtains hang at the sides and
  spotlights stand on their stands.
- ``art_forge`` (teknis: the Workshop Deeps). A cave under the ground.
  Drafting lines are scratched on its walls as on a blueprint. Bottle kilns
  glow orange, looms run threads up into the dark, and a vast machine that
  nobody finished stands at the back: half of it is metal, and half of it
  is only lines.

The palette is the one of the dimension (magenta, cyan, yellow, violet, paper
and stone), and each quarter adds its own accent colours. Bright detail is
kept far off or at the edges, so the play in front of it reads. The things
that drift in the air are the room's motes (`terrain/motes.py`), not part of
these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, smoothstep
from .parts import HORIZON, cloud_mask, cumulus, fog, haze, lamps, moon, shafts, solid, stars, vignette

STACKS = {
    "top": (112, 140, 184),
    "parchment": (236, 220, 186),
    "page": (250, 244, 226),
    "glow": (255, 232, 180),
    "gold": (222, 172, 70),
    "leather": (124, 66, 42),
    "maroon": (128, 40, 50),
    "green": (54, 94, 72),
    "navy": (46, 60, 104),
    "ink": (40, 32, 44),
    "ink_blue": (46, 70, 140),
    "far": (170, 148, 136),
    "near": (58, 34, 28),
    "near_light": (150, 100, 68),
}

RESONANCE = {
    "top": (6, 10, 34),
    "mid": (18, 30, 80),
    "low": (50, 72, 140),
    "moon": (240, 236, 220),
    "halo": (110, 140, 220),
    "cyan": (80, 230, 255),
    "brass": (214, 170, 80),
    "ivory": (236, 228, 206),
    "ebony": (16, 14, 24),
    "cloud": (78, 96, 160),
    "cloud_light": (176, 194, 236),
    "far": (36, 50, 104),
    "near": (10, 12, 30),
    "near_light": (64, 74, 136),
}

STAGE = {
    "top": (50, 38, 108),
    "violet": (120, 60, 134),
    "mid": (206, 84, 120),
    "low": (255, 156, 92),
    "glow": (255, 214, 150),
    "red": (168, 26, 42),
    "gold": (236, 182, 70),
    "black": (24, 18, 26),
    "spot": (255, 248, 226),
    "stone": (204, 150, 140),
    "flat_white": (250, 244, 236),
    "flat_blue": (130, 170, 226),
    "far": (116, 64, 116),
    "near": (30, 12, 24),
    "near_light": (120, 50, 70),
}

FORGE = {
    "top": (14, 9, 8),
    "mid": (40, 24, 20),
    "low": (78, 42, 28),
    "rock": (50, 30, 24),
    "rock_light": (124, 74, 50),
    "kiln": (255, 136, 48),
    "ember": (255, 196, 110),
    "brass": (204, 156, 72),
    "copper": (184, 100, 60),
    "clay": (176, 92, 60),
    "blueprint": (120, 200, 232),
    "near": (22, 12, 10),
    "near_light": (116, 58, 36),
}

#: The thread colours of a loom.
THREADS = ((222, 62, 84), (60, 176, 206), (240, 200, 80), (120, 196, 120), (196, 118, 220))


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------

#: Capital letters as strokes in a unit box (`x` right, `y` down). Only the
#: letters of straight strokes: they read at a small size.
GLYPHS: dict[str, list[list[tuple[float, float]]]] = {
    "A": [[(0.0, 1.0), (0.5, 0.0), (1.0, 1.0)], [(0.22, 0.6), (0.78, 0.6)]],
    "E": [[(0.9, 0.0), (0.0, 0.0), (0.0, 1.0), (0.9, 1.0)], [(0.0, 0.5), (0.7, 0.5)]],
    "F": [[(0.9, 0.0), (0.0, 0.0), (0.0, 1.0)], [(0.0, 0.5), (0.7, 0.5)]],
    "K": [[(0.0, 0.0), (0.0, 1.0)], [(0.9, 0.0), (0.0, 0.55), (0.9, 1.0)]],
    "M": [[(0.0, 1.0), (0.0, 0.0), (0.5, 0.6), (1.0, 0.0), (1.0, 1.0)]],
    "N": [[(0.0, 1.0), (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)]],
    "T": [[(0.0, 0.0), (1.0, 0.0)], [(0.5, 0.0), (0.5, 1.0)]],
    "V": [[(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)]],
    "W": [[(0.0, 0.0), (0.25, 1.0), (0.5, 0.35), (0.75, 1.0), (1.0, 0.0)]],
    "Y": [[(0.0, 0.0), (0.5, 0.5), (1.0, 0.0)], [(0.5, 0.5), (0.5, 1.0)]],
    "Z": [[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)]],
}


def _letter(pen: Pen, glyph: str, u: float, v: float, size: float, width: float, tilt: float = 0.0, value: int = 255) -> None:
    """One letter with its middle at `(u, v)`, `size` high, turned by `tilt` radians."""
    c, s = math.cos(tilt), math.sin(tilt)
    for stroke in GLYPHS[glyph]:
        pts = []
        for x, y in stroke:
            dx, dy = (x - 0.5) * size * 0.8, (y - 0.5) * size
            pts.append((u + dx * c - dy * s, v + dx * s + dy * c))
        pen.line(pts, width, value)


def _open_book(pages: Pen, cover: Pen, u: float, v_foot: float, w: float, h: float) -> list[list[tuple[float, float]]]:
    """An open book that lies on the land as a hill: its pages rise from the
    spine to a crest on each side and fall to the edge. Returns lines that
    follow the top of the pages a little lower each, for the edges of the
    pages under the top one."""
    top = []
    for i in range(41):
        t = -1.0 + 2.0 * i / 40.0
        r = abs(t)
        rise = math.sin(0.5 * math.pi * min(r / 0.78, 1.0)) ** 0.8 if r < 0.78 else 1.0 - (r - 0.78) / 0.22 * 0.40
        top.append((u + t * w, v_foot - h * (0.18 + 0.82 * rise)))
    foot = v_foot - h * 0.14
    pages.poly([(u - w, foot), *top, (u + w, foot)])
    cover.poly([(u - w * 1.06, v_foot), (u - w * 1.06, v_foot - h * 0.30), (u - w * 0.9, foot), (u + w * 0.9, foot), (u + w * 1.06, v_foot - h * 0.30), (u + w * 1.06, v_foot)])
    # The edges of the pages under the top one show at the outer sides.
    lines = []
    for k in range(1, 6):
        drop = h * 0.09 * k
        for side in (top[1:15], top[27:-1]):
            lines.append([(x, min(foot - h * 0.04, y + drop)) for x, y in side])
    return lines


def _shelf(case: Pen, boards: Pen, spines: list[Pen], rng, u: float, v_foot: float, w: float, h: float) -> None:
    """A bookcase that stands as a cliff: a case with a cornice, its shelves,
    and books of each width and height on them. `spines` are pens, one for
    each colour of binding."""
    case.rect(u - w, v_foot - h, u + w, v_foot)
    case.rect(u - w * 1.12, v_foot - h - 0.010, u + w * 1.12, v_foot - h)
    rows = max(2, int(h / 0.05))
    pitch = (h - 0.012) / rows
    for r in range(rows):
        floor = v_foot - h + 0.006 + (r + 1) * pitch
        boards.rect(u - w, floor, u + w, floor + 0.003)
        x = u - w + 0.005
        while x < u + w - 0.008:
            bw = rng.uniform(0.004, 0.009)
            bh = pitch * rng.uniform(0.62, 0.9)
            if rng.random() < 0.08:
                # A book that leans on the next one.
                rng.choice(spines).poly([(x, floor), (x + bw, floor), (x + bw + bh * 0.35, floor - bh * 0.94), (x + bh * 0.35, floor - bh)])
                x += bw + bh * 0.35
            else:
                rng.choice(spines).rect(x, floor - bh, min(x + bw, u + w - 0.004), floor)
            x += bw + 0.0007


def _handwriting(pen: Pen, u0: float, u1: float, v: float, size: float, width: float, rng) -> None:
    """A line of joined-up writing: loops along a line, in words."""
    u = u0
    while u < u1:
        letters = rng.randint(3, 8)
        pts = []
        for i in range(letters * 12 + 1):
            t = i / 12.0 * math.tau
            loop = rng.choice((0.9, 1.0, 1.0, 1.6)) if i % 12 == 0 else 1.0
            pts.append((u + size * 0.32 * (t - 1.25 * math.sin(t)) / math.tau * 2.0, v - size * 0.5 * (1.0 - math.cos(t)) * 0.5 * loop))
        pen.line(pts, width)
        u = pts[-1][0] + size * rng.uniform(0.7, 1.4)


def _rotated_ellipse(cu: float, cv: float, ru: float, rv: float, tilt: float, steps: int = 20) -> list[tuple[float, float]]:
    c, s = math.cos(tilt), math.sin(tilt)
    out = []
    for i in range(steps):
        a = math.tau * i / steps
        x, y = math.cos(a) * ru, math.sin(a) * rv
        out.append((cu + x * c - y * s, cv + x * s + y * c))
    return out


def _note(pen: Pen, u: float, v: float, size: float, flags: int = 1, stem_up: bool = True) -> tuple[float, float]:
    """A note: its head at `(u, v)`, its stem, and `flags` flags. Returns
    the end of the stem."""
    pen.poly(_rotated_ellipse(u, v, size * 0.36, size * 0.25, -0.45))
    if stem_up:
        x = u + size * 0.31
        top = v - size * 2.4
        pen.line([(x, v - size * 0.08), (x, top)], size * 0.09)
        for k in range(flags):
            y = top + k * size * 0.42
            pen.line([(x, y), (x + size * 0.32, y + size * 0.42), (x + size * 0.44, y + size * 0.95), (x + size * 0.30, y + size * 1.3)], size * 0.12)
        return x, top
    x = u - size * 0.31
    pen.line([(x, v + size * 0.08), (x, v + size * 2.4)], size * 0.09)
    return x, v + size * 2.4


def _beamed(pen: Pen, u: float, v: float, size: float, rise: float) -> None:
    """Two notes joined by a beam."""
    a = _note(pen, u, v, size, flags=0)
    b = _note(pen, u + size * 1.6, v - rise, size, flags=0)
    pen.poly([(a[0] - size * 0.05, a[1]), (b[0] + size * 0.05, b[1]), (b[0] + size * 0.05, b[1] + size * 0.32), (a[0] - size * 0.05, a[1] + size * 0.32)])


def _smooth(points: list[tuple[float, float]], steps: int = 8) -> list[tuple[float, float]]:
    """A Catmull-Rom curve through `points`."""
    out = []
    pts = [points[0], *points, points[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(points[-1])
    return out  # type: ignore[return-value]


def _clef(pen: Pen, u: float, v: float, h: float, width: float) -> None:
    """A treble clef: `(u, v)` is its middle and `h` its height."""
    w = h * 0.38
    path = [
        (0.52, 0.98), (0.40, 0.99), (0.36, 0.92), (0.44, 0.88),
        (0.52, 0.92), (0.54, 0.80), (0.52, 0.50), (0.56, 0.20),
        (0.62, 0.04), (0.72, 0.10), (0.68, 0.24), (0.42, 0.42),
        (0.20, 0.58), (0.20, 0.74), (0.40, 0.82), (0.64, 0.78),
        (0.76, 0.66), (0.66, 0.56), (0.46, 0.56), (0.40, 0.66), (0.50, 0.72),
    ]
    pts = [(u + (x - 0.5) * w * 2.0, v + (y - 0.5) * h) for x, y in path]
    pen.line(_smooth(pts), width)
    pen.ellipse(pts[2][0] + w * 0.02, pts[2][1] - h * 0.01, width * 1.6)


def _pipe(body: Pen, mouth: Pen, lit: Pen, u: float, top: float, foot: float, w: float) -> None:
    """An organ pipe: a column with a lip at its top, a mouth, and a cone
    for its foot. `lit` takes the stripe of light down its round side."""
    body.rect(u - w, top, u + w, foot - w * 3.0)
    body.rect(u - w * 1.15, top - w * 0.35, u + w * 1.15, top + w * 0.25)
    body.poly([(u - w, foot - w * 3.0), (u + w, foot - w * 3.0), (u + w * 0.25, foot), (u - w * 0.25, foot)])
    # The mouth: a dark slot with a pointed upper lip, a little over the foot.
    m = top + (foot - top) * 0.72
    mouth.poly([(u - w * 0.70, m + w * 1.6), (u + w * 0.70, m + w * 1.6), (u + w * 0.70, m), (u, m - w * 1.1), (u - w * 0.70, m)])
    lit.rect(u - w * 0.62, top + w * 0.3, u - w * 0.28, foot - w * 3.4)


def _tuning_fork(pen: Pen, u: float, v_foot: float, h: float, w: float) -> None:
    """A tuning fork that stands on a ball foot: a stem, and two prongs."""
    gap = w * 1.6
    bend = v_foot - h * 0.42
    pen.ellipse(u, v_foot - w * 0.8, w * 1.4, w * 0.9)
    pen.rect(u - w * 0.5, bend, u + w * 0.5, v_foot - w * 0.8)
    for side in (-1.0, 1.0):
        x = u + side * (gap * 0.5 + w * 0.5)
        pen.rect(x - w * 0.5, v_foot - h, x + w * 0.5, bend - gap * 0.5)
    pen.arc(u, bend - gap * 0.5, gap * 0.5 + w * 0.5, 0.0, 180.0, w)


def _wheel(pen: Pen, u: float, v: float, r: float, teeth: int, depth: float, hole: float = 0.0, spokes: int = 0, width: float | None = None) -> None:
    """A gear wheel: `teeth` teeth of `depth`. `hole` more than 0 cuts the
    hub hole; `spokes` more than 0 cuts the wheel between that many spokes.
    With `width`, the gear is drawn as an outline of that width."""
    pts = []
    for k in range(teeth):
        a0 = math.tau * k / teeth
        step = math.tau / teeth
        for frac, rad in ((0.0, r), (0.18, r + depth), (0.48, r + depth), (0.66, r)):
            pts.append(polar(u, v, rad, math.degrees(a0 + step * frac)))
    if width is not None:
        pen.line([*pts, pts[0]], width)
        pen.ring(u, v, r * 0.28, width)
        return
    pen.poly(pts)
    if spokes:
        inner = r * 0.78
        for k in range(spokes):
            a = 360.0 * k / spokes + 180.0 / spokes
            gap = 180.0 / spokes - 9.0
            sector = [(u, v)] + [polar(u, v, inner, a + d) for d in np.linspace(-gap, gap, 9)]
            hub = [polar(u, v, r * 0.30, a + d) for d in np.linspace(gap, -gap, 9)]
            pen.poly([*sector[1:], *hub], value=0)
    if hole > 0.0:
        pen.ellipse(u, v, hole, value=0)


def _bottle_kiln(pen: Pen, mouth: Pen, u: float, v_foot: float, h: float, w: float) -> None:
    """A bottle kiln of brick: a wide round body that narrows to a
    chimney, and the arch of its fire mouth at its foot."""
    side = []
    for i in range(13):
        t = i / 12.0
        y = v_foot - h * t
        bulge = w * (0.80 + 0.20 * math.sin(math.pi * min(1.0, t / 0.62)))
        half = bulge if t < 0.62 else w * (0.30 + 0.70 * (1.0 - (t - 0.62) / 0.38) ** 1.6)
        side.append((u + half, y))
    pen.poly(side + [(2.0 * u - x, y) for x, y in side[::-1]])
    pen.rect(u - w * 0.34, v_foot - h - h * 0.025, u + w * 0.34, v_foot - h + h * 0.01)
    mouth.rect(u - w * 0.22, v_foot - h * 0.14, u + w * 0.22, v_foot)
    mouth.ellipse(u, v_foot - h * 0.14, w * 0.22)


def _outline(art: Art, mask: np.ndarray, d: float) -> np.ndarray:
    """The edge of `mask` all round, `d` wide."""
    return np.clip(art.rim(mask, d, 0.0) + art.rim(mask, -d, 0.0) + art.rim(mask, 0.0, d) + art.rim(mask, 0.0, -d), 0.0, 1.0)


# ---------------------------------------------------------------------------
# Fiction: the Story Stacks
# ---------------------------------------------------------------------------


def art_stacks(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = STACKS
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["parchment"], 0.6)), (HORIZON - 0.05, p["glow"]), (HORIZON + 0.10, p["parchment"]), (1.0, mix(p["parchment"], p["leather"], 0.3))]))
        # Old paper: soft brown spots of age, and a low sun in the haze.
        a.tint(layer, smoothstep(0.62, 0.95, a.noise("foxing", cells=7.0, octaves=4)), p["gold"], 0.12)
        a.light(layer, a.spot(0.68, 0.44, 0.40, 2.0, squash=1.3), p["glow"], 0.55)
        sun, sun_pen = a.drawing()
        sun_pen.ellipse(0.68, 0.44, 0.032)
        a.put(layer, a.mask_of(sun, blur=1.5), mix(p["glow"], (255, 255, 255), 0.5), 0.85)
        # Clouds of torn paper: a hard edge with a faint line of ink.
        clouds = cloud_mask(a, "paper clouds", 0.34, 0.10, cells=3.0, cover=0.34, soft=0.03, stretch=2.8)
        a.tint(layer, clouds, p["page"], 0.70)
        a.tint(layer, _outline(a, clouds, 0.0015), p["ink"], 0.22)
        a.tint(layer, clouds * smoothstep(0.32, 0.42, a.v), p["gold"], 0.18)
        # Letters that fly in flocks, as birds do. A flock far off is pale.
        flocks, flock_pen = a.drawing()
        rng = a.rand("letter flocks")
        # Each flock flies in a V, as geese do, its lead at the front.
        for cu, cv, gap, count, size in ((0.24, 0.32, 0.022, 9, 0.016), (0.50, 0.42, 0.016, 5, 0.012), (0.80, 0.30, 0.020, 7, 0.015)):
            for i in range(count):
                rank = (i + 1) // 2
                side = -1.0 if i % 2 else 1.0
                u = cu - rank * gap + rng.uniform(-0.003, 0.003)
                v = cv + side * rank * gap * 0.45 + rng.uniform(-0.003, 0.003)
                glyph = rng.choice("VVWMAKTEYNZF")
                _letter(flock_pen, glyph, u, v, size * rng.uniform(0.8, 1.15), size * 0.13, rng.uniform(-0.35, 0.35), value=rng.randint(170, 255))
        a.tint(layer, a.mask_of(flocks, blur=0.3), p["ink"], 0.55)
        # Far shelves, pale in the haze, at the horizon.
        far, far_pen = a.drawing()
        for u, w, h in ((0.12, 0.04, 0.10), (0.34, 0.03, 0.07), (0.66, 0.035, 0.08), (0.90, 0.05, 0.12)):
            far_pen.rect(u - w, HORIZON - h, u + w, HORIZON + 0.05)
            far_pen.rect(u - w * 1.1, HORIZON - h - 0.006, u + w * 1.1, HORIZON - h)
        land, _ = a.ridge("far book hills", HORIZON + 0.01, 0.02, cells=4.0, octaves=3)
        cases = a.mask_of(far, blur=1.0)
        a.tint(layer, np.maximum(cases, land), mix(p["far"], p["parchment"], 0.45), 0.60)
        rows = (np.sin(a.v * 260.0) > 0.85) * cases + (np.sin(a.u * 900.0) > 0.4) * cases * 0.5
        a.tint(layer, np.clip(rows, 0.0, 1.0), p["far"], 0.25)
        a.grain(layer, "paper grain", 2.4)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far stacks")
        ground, line = a.ridge("far land", HORIZON + 0.045, 0.012, cells=3.0, octaves=3)
        case, case_pen = a.drawing()
        boards, board_pen = a.drawing()
        spine_layers = [a.drawing() for _ in range(5)]
        spine_pens = [pen for _, pen in spine_layers]
        for u, w, h in ((0.09, 0.055, 0.25), (0.20, 0.04, 0.17), (0.80, 0.045, 0.20), (0.915, 0.06, 0.29)):
            v = float(line[min(a.n - 1, int(u * a.n))]) + 0.01
            _shelf(case_pen, board_pen, spine_pens, rng, u, v, w, h)
        pages, page_pen = a.drawing()
        covers, cover_pen = a.drawing()
        edges, edge_pen = a.drawing()
        gutters, gutter_pen = a.drawing()
        ribbons, ribbon_pen = a.drawing()
        for u, w, h in ((0.40, 0.12, 0.085), (0.63, 0.085, 0.06)):
            v = float(line[min(a.n - 1, int(u * a.n))]) + 0.012
            for pts in _open_book(page_pen, cover_pen, u, v, w, h):
                edge_pen.line(pts, 0.0012)
            gutter_pen.poly([(u - w * 0.18, v), (u, v - h * 0.24), (u + w * 0.18, v)])
            ribbon_pen.poly([(u + 0.003, v - h * 0.22), (u + 0.009, v - h * 0.22), (u + 0.012, v + 0.02), (u + 0.0075, v + 0.014), (u + 0.003, v + 0.02)])
        mask = np.maximum.reduce([ground, a.mask_of(case), a.mask_of(covers), a.mask_of(pages)])
        layer = solid(a, mask, mix(p["far"], p["parchment"], 0.25), mix(p["far"], p["leather"], 0.35), 0.40, 0.70, "far paper", 0.05)
        wood = a.mask_of(case)
        a.put(layer, wood, mix(p["leather"], p["far"], 0.45))
        a.shade(layer, a.rim(wood, 0.004, 0.0, 0.5) * wood, 0.30)
        for (image, _pen), colour in zip(spine_layers, (p["maroon"], p["green"], p["navy"], p["leather"], p["gold"])):
            spine = a.mask_of(image)
            a.put(layer, spine, mix(colour, p["far"], 0.42))
            a.light(layer, a.rim(spine, 0.0015, 0.0) * spine, p["glow"], 0.25)
        a.shade(layer, a.mask_of(boards), 0.35)
        cover = a.mask_of(covers)
        a.put(layer, cover, mix(p["maroon"], p["far"], 0.25))
        page = a.mask_of(pages)
        a.put(layer, page, mix(p["page"], p["far"], 0.12))
        a.tint(layer, a.mask_of(edges, blur=0.3) * page, p["leather"], 0.55)
        a.shade(layer, a.mask_of(gutters, blur=12.0) * page, 0.30)
        a.put(layer, a.mask_of(ribbons, blur=0.3), mix(p["maroon"], p["far"], 0.20))
        # The river of handwriting: a band of blue ink that shines, and the
        # loops of the words in it.
        river_v = HORIZON + 0.065
        river = a.band(river_v, 0.016, 1.0) * ground
        a.put(layer, river, mix(p["ink_blue"], p["far"], 0.25), 0.90)
        a.light(layer, a.band(river_v - 0.008, 0.003) * ground, p["glow"], 0.35)
        writing, write_pen = a.drawing()
        for row, dv in enumerate((-0.006, 0.004)):
            _handwriting(write_pen, -0.02 + row * 0.03, 1.02, river_v + dv, 0.008, 0.0012, a.rand(("river words", row)))
        a.light(layer, a.mask_of(writing, blur=0.3) * river, p["page"], 0.75)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.6) * mask, p["glow"], 0.30)
        haze(a, layer, p["parchment"], 0.22, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near stacks")
        ground, _ = a.ridge("near land", 0.70, 0.010, cells=5.0, octaves=3)
        books = []
        bands, band_pen = a.drawing()
        labels, label_pen = a.drawing()
        # Books as tall as trees at the sides, their spines to the view; one
        # leans on its neighbour.
        for u, w, h, lean, colour in ((0.035, 0.042, 0.62, 0.0, p["maroon"]), (0.098, 0.026, 0.46, 0.06, p["green"]), (0.905, 0.030, 0.50, -0.05, p["navy"]), (0.965, 0.044, 0.68, 0.0, p["leather"])):
            one, one_pen = a.drawing()
            top = 0.74 - h
            one_pen.poly([(u - w, 0.74), (u + w, 0.74), (u + w + lean, top), (u - w + lean, top)])
            books.append((a.mask_of(one), colour))
            for t in (0.06, 0.10, 0.86, 0.90):
                y = 0.74 - h * (1.0 - t)
                x = lean * (1.0 - (y - top) / h)
                band_pen.poly([(u - w + x, y - 0.004), (u + w + x, y - 0.004), (u + w + x, y + 0.004), (u - w + x, y + 0.004)])
            y = top + h * 0.25
            x = lean * 0.75
            label_pen.rect(u - w * 0.6 + x, y, u + w * 0.6 + x, y + h * 0.10)
        # A pile of books that lie on the land, and a quill stuck in it.
        pile, pile_pen = a.drawing()
        pile_books = []
        y = 0.725
        for k in range(5):
            bw = rng.uniform(0.04, 0.065)
            bh = rng.uniform(0.014, 0.022)
            x = 0.25 + rng.uniform(-0.012, 0.012)
            pile_pen.rect(x - bw, y - bh, x + bw, y)
            one, one_pen = a.drawing()
            one_pen.rect(x - bw, y - bh, x + bw, y)
            ends, end_pen = a.drawing()
            end_pen.rect(x + bw - 0.006, y - bh + 0.002, x + bw, y - 0.002)
            pile_books.append((a.mask_of(one), a.mask_of(ends), (p["maroon"], p["green"], p["navy"], p["leather"])[k % 4]))
            y -= bh + 0.001
        quill, quill_pen = a.drawing()
        barbs, barb_pen = a.drawing()
        shaft = _smooth([(0.79, 0.735), (0.797, 0.60), (0.808, 0.45), (0.826, 0.30)], 6)
        quill_pen.line(shaft, 0.003)
        vane_l = _smooth([(0.798, 0.58), (0.783, 0.48), (0.788, 0.38), (0.810, 0.31), (0.826, 0.30)], 6)
        vane_r = _smooth([(0.826, 0.30), (0.834, 0.36), (0.828, 0.46), (0.810, 0.54), (0.798, 0.58)], 6)
        quill_pen.poly(vane_l + vane_r)
        for k in range(14):
            t = 0.33 + k * 0.018
            x = 0.797 + (0.826 - 0.797) * (0.60 - t) / 0.30
            barb_pen.line([(x, t), (x - 0.012, t + 0.010)], 0.0012)
            barb_pen.line([(x, t), (x + 0.009, t + 0.008)], 0.0012)
        quill_pen.ellipse(0.772, 0.722, 0.016, 0.014)
        quill_pen.rect(0.764, 0.700, 0.780, 0.712)
        mask = np.maximum.reduce([ground, a.mask_of(pile), a.mask_of(quill)] + [m for m, _ in books])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "near leather", 0.10)
        for one, colour in books:
            a.put(layer, one, mix(colour, p["near"], 0.40))
            a.light(layer, a.rim(one, -0.005, 0.0, 0.5) * one, p["glow"], 0.25)
            a.shade(layer, a.rim(one, 0.007, 0.0, 0.8) * one, 0.35)
        a.put(layer, a.mask_of(bands) * mask, mix(p["gold"], p["near"], 0.35))
        a.put(layer, a.mask_of(labels) * mask, mix(p["parchment"], p["near"], 0.45))
        for one, ends, colour in pile_books:
            a.put(layer, one, mix(colour, p["near"], 0.40))
            a.put(layer, ends, mix(p["page"], p["near"], 0.45))
            a.shade(layer, a.rim(one, 0.0, 0.003) * one, 0.40)
        feather = a.mask_of(quill)
        a.put(layer, feather, mix(p["page"], p["near"], 0.58))
        a.shade(layer, a.mask_of(barbs, blur=0.3) * feather, 0.30)
        a.put(layer, feather * (a.v > 0.69), mix(p["ink"], p["near"], 0.2))
        a.light(layer, a.rim(feather, -0.003, 0.0, 0.4) * feather, p["glow"], 0.35)
        # The top of the land is the edge of a great page: thin lines along it.
        edge = (np.sin(a.v * 1400.0) > 0.6) * smoothstep(0.69, 0.70, a.v) * smoothstep(0.76, 0.73, a.v) * ground
        a.tint(layer, edge, mix(p["parchment"], p["near"], 0.55), 0.45)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.4) * mask, p["glow"], 0.28)
        a.shade(layer, a.rim(mask, 0.005, -0.003, 1.2) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = a.blank()
    a.put(layer, shafts(a, "late light", 4, -0.12, 0.0, 0.80, 0.05), p["glow"], 0.14)
    a.put(layer, fog(a, "paper dust", 0.70, 0.12), p["parchment"], 0.24)
    vignette(a, layer, p["near"], 0.28)
    return layer


def stacks_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Bookmark ribbons that hang from above, each with a cut in its end."""
    del layer_lights
    rng = art_.rand("stacks foreground")
    for k in range(4):
        u = (k + rng.uniform(0.2, 0.8)) / 4.0
        end = rng.uniform(0.385, 0.405)
        w = rng.choice([0.004, 0.005])
        pen.poly([(u - w, 0.0), (u + w, 0.0), (u + w, end), (u, end - w * 1.4), (u - w, end)])


# ---------------------------------------------------------------------------
# Music: the Resonant Reach
# ---------------------------------------------------------------------------


def _stave(lines: Pen, notes: Pen, rng, v0: float, amp: float, turns: float, phase: float, gap: float) -> None:
    """A five-line stave that floats across the panel as a road, with notes
    on its lines and in its spaces."""

    def centre(u: float) -> float:
        return v0 + amp * math.sin(math.tau * (u * turns + phase))

    xs = np.linspace(-0.02, 1.02, 120)
    for k in range(5):
        lines.line([(float(x), centre(float(x)) + (k - 2) * gap) for x in xs], gap * 0.16)
    u = rng.uniform(0.02, 0.08)
    while u < 0.98:
        step = rng.randint(-4, 4)
        v = centre(u) + step * gap * 0.5
        if rng.random() < 0.3:
            _beamed(notes, u, v, gap * 1.1, rng.uniform(-gap, gap))
            u += gap * 1.8
        else:
            _note(notes, u, v, gap * 1.1, flags=rng.choice([0, 1, 1, 2]))
        u += rng.uniform(0.05, 0.11)
    for x in (0.25, 0.5, 0.75):
        lines.line([(x, centre(x) - gap * 2.0), (x, centre(x) + gap * 2.0)], gap * 0.16)


def art_resonance(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = RESONANCE
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.32, p["mid"]), (HORIZON, p["low"]), (0.80, p["mid"]), (1.0, p["top"])]))
        stars(a, layer, 700, (226, 232, 255), v_max=0.58)
        moon(a, layer, 0.78, 0.33, 0.034, p["moon"], p["halo"], crescent=0.0)
        # Two staves float across the sky, faint, with their notes.
        staff, staff_pen = a.drawing()
        notes, note_pen = a.drawing()
        _stave(staff_pen, note_pen, a.rand("high stave"), 0.30, 0.025, 0.8, 0.1, 0.0065)
        _stave(staff_pen, note_pen, a.rand("low stave"), 0.45, 0.020, 1.1, 0.6, 0.0050)
        ink = np.maximum(a.mask_of(staff, blur=0.3), a.mask_of(notes, blur=0.3))
        a.light(layer, a.blur(ink, 4.0), p["cyan"], 0.25)
        a.light(layer, ink, p["ivory"], 0.40)
        # Sound goes out in rings from where the far pipes stand.
        rings, ring_pen = a.drawing()
        for cu, cv in ((0.14, 0.42), (0.50, 0.30), (0.86, 0.46)):
            for k in range(5):
                ring_pen.ring(cu, cv, 0.03 + k * 0.025, 0.0018, value=int(230 * (1.0 - k / 5.0)))
        a.light(layer, a.mask_of(rings, blur=1.2), p["cyan"], 0.40)
        # The sea of cloud under the view, lit by the moon.
        sea = cumulus(a, "cloud sea", HORIZON + 0.08, 0.09, cells=4.0, cover=0.62, light=p["cloud_light"], shadow=p["cloud"])
        layer = a.over(layer, sea)
        a.tint(layer, smoothstep(HORIZON - 0.02, HORIZON + 0.10, a.v), p["low"], 0.25)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        body, body_pen = a.drawing()
        mouths, mouth_pen = a.drawing()
        lit, lit_pen = a.drawing()
        # Organ pipes in three groups, the longest in the middle of each.
        for cu, count, tall, w in ((0.14, 5, 0.30, 0.010), (0.50, 5, 0.24, 0.009), (0.86, 5, 0.27, 0.010)):
            for k in range(count):
                off = k - (count - 1) / 2.0
                u = cu + off * w * 2.5
                top = HORIZON - tall * (1.0 - abs(off) / (count * 0.9)) + 0.04
                _pipe(body_pen, mouth_pen, lit_pen, u, top, HORIZON + 0.07, w)
        # Notes and a clef that drift, very large.
        drift, drift_pen = a.drawing()
        _beamed(drift_pen, 0.68, 0.43, 0.020, 0.012)
        _note(drift_pen, 0.33, 0.44, 0.016, flags=1)
        _clef(drift_pen, 0.27, 0.34, 0.12, 0.0045)
        brass = a.mask_of(body)
        layer = solid(a, brass, mix(p["brass"], p["far"], 0.28), mix(p["brass"], p["far"], 0.60), 0.20, 0.66)
        a.light(layer, a.mask_of(lit, blur=0.6) * brass, p["brass"], 0.55)
        a.shade(layer, a.rim(brass, 0.004, 0.0, 0.4) * brass, 0.40)
        a.light(layer, a.rim(brass, 0.0015, 0.0) * brass, p["cyan"], 0.35)
        a.put(layer, a.mask_of(mouths, blur=0.3) * brass, mix(p["ebony"], p["far"], 0.3), 0.9)
        floating = a.mask_of(drift, blur=0.3)
        a.put(layer, floating, mix(p["ivory"], p["far"], 0.45))
        a.light(layer, a.blur(floating, 6.0), p["cyan"], 0.20)
        a.glow(layer, a.blur(floating, 8.0) * (1.0 - floating), p["cyan"], 0.12)
        # Cyan light at the top of the tallest pipes: the sound that comes out.
        for cu, top in ((0.14, HORIZON - 0.26), (0.50, HORIZON - 0.20), (0.86, HORIZON - 0.23)):
            a.glow(layer, a.spot(cu, top, 0.05, 2.0) * (1.0 - brass), p["cyan"], 0.30)
        # Cloud over the feet of the pipes.
        sea = cumulus(a, "far cloud", HORIZON + 0.07, 0.05, cells=5.0, cover=0.90, light=mix(p["cloud_light"], p["far"], 0.3), shadow=mix(p["cloud"], p["far"], 0.4))
        layer = a.over(layer, sea)
        haze(a, layer, p["low"], 0.14, HORIZON + 0.08)
        return layer
    if layer_key == "near_background":
        image, pen = a.drawing()
        ground, _ = a.ridge("near cloud", 0.705, 0.010, cells=6.0, octaves=3)
        # Tuning forks as tall as trees at the sides, and a metronome.
        for u, h, w in ((0.045, 0.58, 0.012), (0.12, 0.40, 0.008), (0.95, 0.62, 0.013)):
            _tuning_fork(pen, u, 0.74, h, w)
        pen.poly([(0.84, 0.74), (0.88, 0.74), (0.868, 0.56), (0.852, 0.56)])
        # A ledge of piano keys along the land.
        keys, key_pen = a.drawing()
        black, black_pen = a.drawing()
        kw = 0.016
        for k in range(int(1.0 / kw) + 2):
            x = k * kw
            key_pen.rect(x + 0.0008, 0.712, x + kw - 0.0008, 0.76)
            if k % 7 not in (2, 6):
                black_pen.rect(x + kw * 0.68, 0.712, x + kw * 1.32, 0.738)
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.24, 0.74, "near", 0.08)
        ivory = a.mask_of(keys) * ground
        a.put(layer, ivory, mix(p["ivory"], p["near"], 0.62))
        a.put(layer, a.mask_of(black) * ground, p["ebony"])
        a.put(layer, a.band(0.709, 0.0025, 1.0) * ground, mix(p["brass"], p["near"], 0.30))
        metal = a.mask_of(image)
        a.put(layer, metal, mix(p["brass"], p["near"], 0.55))
        a.light(layer, a.rim(metal, -0.004, 0.0, 0.4) * metal, p["brass"], 0.45)
        a.light(layer, a.rim(metal, 0.004, 0.0, 0.4) * metal, p["cyan"], 0.25)
        a.shade(layer, a.rim(metal, 0.006, 0.0, 0.8) * metal, 0.25)
        # The pendulum of the metronome, and rings round the forks.
        swing, swing_pen = a.drawing()
        swing_pen.line([(0.86, 0.72), (0.874, 0.58)], 0.0018)
        swing_pen.rect(0.868, 0.62, 0.878, 0.632)
        a.put(layer, a.mask_of(swing), mix(p["ivory"], p["near"], 0.4))
        rings, ring_pen = a.drawing()
        for cu, cv in ((0.045, 0.18), (0.95, 0.14)):
            for k in range(4):
                ring_pen.ring(cu, cv, 0.025 + k * 0.022, 0.0022, value=int(220 * (1.0 - k / 4.0)))
        a.glow(layer, a.mask_of(rings, blur=1.5), p["cyan"], 0.35)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.4) * mask, p["cloud_light"], 0.22)
        return layer
    layer = a.blank()
    a.put(layer, fog(a, "cloud mist", 0.72, 0.12), p["cloud_light"], 0.22)
    a.put(layer, fog(a, "high mist", 0.30, 0.10, cells=3.0), p["cyan"], 0.05)
    vignette(a, layer, p["top"], 0.40)
    return layer


def resonance_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Wind chimes that hang from above: a bar, and tubes of each length on
    threads under it. Nothing stands from below."""
    rng = art_.rand("resonance foreground")
    for k in range(3):
        u = (k + rng.uniform(0.25, 0.75)) / 3.0
        bar = rng.uniform(0.30, 0.33)
        pen.rect(u - 0.0008, 0.0, u + 0.0008, bar)
        pen.rect(u - 0.014, bar, u + 0.014, bar + 0.003)
        for t in range(5):
            x = u - 0.011 + t * 0.0055
            end = rng.uniform(0.375, 0.40)
            pen.rect(x - 0.0004, bar, x + 0.0004, bar + 0.012)
            pen.rect(x - 0.0016, bar + 0.012, x + 0.0016, end)
        layer_lights.append((u, bar + 0.004, 0.0012, RESONANCE["cyan"]))


# ---------------------------------------------------------------------------
# Performance: the Amphitheatre
# ---------------------------------------------------------------------------


def _cutout_cloud(pen: Pen, u: float, v: float, w: float) -> None:
    """A cloud as a stage hand cuts it out of board: round lumps on a flat
    foot."""
    for du, dv, r in ((-0.55, 0.0, 0.32), (-0.18, -0.22, 0.42), (0.25, -0.12, 0.36), (0.58, 0.04, 0.26)):
        pen.ellipse(u + du * w, v + dv * w, r * w)
    pen.rect(u - 0.80 * w, v, u + 0.82 * w, v + 0.26 * w)


def _star_points(u: float, v: float, r: float, inner: float = 0.45) -> list[tuple[float, float]]:
    return [polar(u, v, r if k % 2 == 0 else r * inner, -90.0 + k * 36.0) for k in range(10)]


def art_stage(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = STAGE
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.28, p["violet"]), (0.46, p["mid"]), (HORIZON, p["low"]), (0.72, mix(p["low"], p["mid"], 0.5)), (1.0, p["violet"])]))
        # The sun is half down behind the heights.
        a.light(layer, a.spot(0.36, HORIZON, 0.40, 2.0, squash=1.6), p["glow"], 0.60)
        sun, sun_pen = a.drawing()
        sun_pen.ellipse(0.36, HORIZON - 0.01, 0.055)
        a.put(layer, a.mask_of(sun, blur=1.0), mix(p["glow"], (255, 255, 255), 0.35), 0.9)
        # Thin real clouds, lit from below.
        streaks = cloud_mask(a, "dusk streaks", 0.40, 0.10, cells=2.5, cover=0.30, soft=0.12, stretch=6.0)
        a.tint(layer, streaks, mix(p["mid"], p["violet"], 0.4), 0.45)
        a.light(layer, streaks * smoothstep(0.36, 0.48, a.v), p["low"], 0.40)
        # Flats of painted scenery that hang on wires from above: a cloud,
        # a moon and a star, each painted flat, with a dark edge.
        flats, flat_pen = a.drawing()
        moon_flat, moon_pen = a.drawing()
        star_flat, star_pen = a.drawing()
        wires, wire_pen = a.drawing()
        for u, v, w in ((0.14, 0.38, 0.06), (0.60, 0.33, 0.075)):
            _cutout_cloud(flat_pen, u, v, w)
            for du in (-0.5, 0.5):
                wire_pen.line([(u + du * w, 0.0), (u + du * w, v - 0.2 * w)], 0.0010)
        moon_pen.ellipse(0.84, 0.35, 0.040)
        moon_pen.ellipse(0.860, 0.336, 0.036, value=0)
        wire_pen.line([(0.82, 0.0), (0.82, 0.315)], 0.0010)
        star_pen.poly(_star_points(0.38, 0.30, 0.022))
        wire_pen.line([(0.38, 0.0), (0.38, 0.278)], 0.0010)
        a.tint(layer, a.mask_of(wires), p["black"], 0.35)
        board = a.mask_of(flats, blur=0.3)
        a.put(layer, board, p["flat_white"])
        a.put(layer, board * smoothstep(0.30, 0.42, a.v), p["flat_blue"], 0.40)
        crescent = a.mask_of(moon_flat, blur=0.3)
        a.put(layer, crescent, mix(p["gold"], (255, 255, 255), 0.25))
        star = a.mask_of(star_flat, blur=0.3)
        a.put(layer, star, p["gold"])
        props = np.maximum.reduce([board, crescent, star])
        a.shade(layer, a.rim(props, 0.003, 0.003) * props, 0.35)
        a.tint(layer, _outline(a, props, 0.0018), p["black"], 0.55)
        # The haze of the dusk over them, so they stay behind.
        a.tint(layer, props, p["mid"], 0.18)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far theatre")
        # The heights: a ridge, and a great round hill in the middle that
        # the amphitheatre is cut in.
        ridge, _ = a.ridge("heights", HORIZON + 0.03, 0.04, cells=3.0, octaves=4, sharp=0.5)
        cu = 0.52
        crest = HORIZON + 0.03 - 0.13 * np.exp(-(((a.u[0] - cu) / 0.20) ** 2))
        hill = np.clip((a.v - crest[None, :]) * a.n + 0.5, 0.0, 1.0)
        ground = np.maximum(ridge, hill)
        # The tiers: half rings, each smaller one lower, round a stage at
        # the foot. The rim of the bowl is under the crest of the hill.
        rim_v, rx, ry = HORIZON - 0.075, 0.16, 0.085
        bowl, bowl_pen = a.drawing()
        steps, step_pen = a.drawing()
        seats, seat_pen = a.drawing()
        lip = [(cu + rx * math.cos(t), rim_v + ry * math.sin(t)) for t in np.linspace(0.0, math.pi, 49)]
        bowl_pen.poly(lip)
        for k in range(9):
            s = 1.0 - k * 0.085
            ring = [(cu + rx * s * math.cos(t), rim_v + (1.0 - s) * 0.03 + ry * s * math.sin(t)) for t in np.linspace(0.03, math.pi - 0.03, 49)]
            step_pen.line(ring, 0.0018)
            for t in np.linspace(0.2, math.pi - 0.2, 16):
                if rng.random() < 0.35:
                    x, y = cu + rx * s * math.cos(t), rim_v + (1.0 - s) * 0.03 + ry * s * math.sin(t)
                    seat_pen.ellipse(x, y - 0.0025, 0.0018)
        # The stage at the foot: a gold arch with red curtains, lit.
        stage_v = rim_v + ry + 0.012
        arch, arch_pen = a.drawing()
        curtain, curtain_pen = a.drawing()
        arch_pen.rect(cu - 0.034, stage_v - 0.050, cu + 0.034, stage_v)
        arch_pen.ellipse(cu, stage_v - 0.050, 0.034, 0.014)
        for side in (-1.0, 1.0):
            curtain_pen.poly([(cu + side * 0.028, stage_v - 0.047), (cu + side * 0.008, stage_v - 0.047), (cu + side * 0.019, stage_v - 0.022), (cu + side * 0.022, stage_v - 0.003), (cu + side * 0.028, stage_v - 0.003)])
        curtain_pen.rect(cu - 0.028, stage_v - 0.051, cu + 0.028, stage_v - 0.043)
        mask = np.maximum.reduce([ground, a.mask_of(arch)])
        layer = solid(a, mask, mix(p["far"], p["mid"], 0.25), mix(p["far"], p["violet"], 0.4), 0.46, 0.70, "far rock", 0.08)
        cut = a.mask_of(bowl, blur=0.4) * ground
        a.put(layer, cut, mix(p["stone"], p["far"], 0.55))
        a.shade(layer, a.rim(cut, 0.0, -0.006, 0.8) * cut, 0.35)
        groove = a.mask_of(steps, blur=0.4) * cut
        a.shade(layer, groove, 0.30)
        a.light(layer, a.shift(groove, 0.0, -0.0025), p["glow"], 0.18)
        a.put(layer, a.mask_of(seats, blur=0.3) * cut, mix(p["red"], p["far"], 0.40), 0.7)
        gold = a.mask_of(arch, blur=0.3)
        a.put(layer, gold, mix(p["gold"], p["far"], 0.30))
        inside = gold * (np.abs(a.u - cu) < 0.028) * (a.v > stage_v - 0.047) * (a.v < stage_v - 0.003)
        a.put(layer, inside, mix(p["spot"], p["glow"], 0.5), 0.85)
        a.put(layer, a.mask_of(curtain, blur=0.2), mix(p["red"], p["far"], 0.20))
        # Beams from lamps on the rim to the stage.
        beams, beam_pen = a.drawing()
        lights = []
        for u in (cu - rx * 0.95, cu - rx * 0.5, cu + rx * 0.5, cu + rx * 0.95):
            v = rim_v - 0.004
            beam_pen.poly([(u - 0.003, v), (u + 0.003, v), (cu + (u - cu) * 0.08 + 0.015, stage_v - 0.01), (cu + (u - cu) * 0.08 - 0.015, stage_v - 0.01)])
            lights.append((u, v, 0.0022))
        a.glow(layer, a.mask_of(beams, blur=3.0), p["spot"], 0.14)
        lamps(a, layer, lights, p["spot"], halo=4.0, strength=0.7)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.6) * mask, p["glow"], 0.35)
        haze(a, layer, p["low"], 0.16, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        image, pen = a.drawing()
        ground, _ = a.ridge("stage floor", 0.705, 0.0, cells=2.0, octaves=1)
        # The red curtains at the sides, each held back by a gold cord.
        curtains = []
        for side in (0.0, 1.0):
            def x(t: float) -> float:
                return t if side == 0.0 else 1.0 - t
            one, one_pen = a.drawing()
            one_pen.poly([(x(0.0), 0.0), (x(0.13), 0.0), (x(0.10), 0.20), (x(0.055), 0.44), (x(0.075), 0.56), (x(0.115), 0.74), (x(0.0), 0.74)])
            curtains.append(a.mask_of(one, blur=0.3))
            pen.rect(x(0.0), 0.0, x(0.012), 0.74)
        # Spotlights on stands, turned to the middle.
        lenses = []
        for u, turn in ((0.19, 1.0), (0.81, -1.0)):
            for du in (-0.018, 0.0, 0.018):
                pen.line([(u, 0.62), (u + du, 0.74)], 0.003)
            pen.rect(u - 0.0015, 0.58, u + 0.0015, 0.63)
            can = [(u - 0.016 * turn, 0.565), (u + 0.010 * turn, 0.548), (u + 0.018 * turn, 0.570), (u - 0.008 * turn, 0.588)]
            pen.poly(can)
            lenses.append((u + 0.014 * turn, 0.559, 0.004))
        drape = np.maximum(curtains[0], curtains[1])
        mask = np.maximum.reduce([ground, a.mask_of(image), drape])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "near", 0.08)
        # Velvet: deep folds down the curtain, a sheen on each.
        folds = 0.5 + 0.5 * np.sin(a.u * math.tau * 34.0 + np.sin(a.v * 9.0) * 0.6)
        a.put(layer, drape, mix(p["red"], p["near"], 0.35))
        a.shade(layer, drape * (1.0 - folds) ** 1.5, 0.55)
        a.light(layer, drape * folds ** 6, p["red"], 0.35)
        cords, cord_pen = a.drawing()
        for side, xx in ((0.0, 0.058), (1.0, 0.942)):
            cord_pen.rect(xx - 0.012, 0.432, xx + 0.012, 0.444)
            cord_pen.ellipse(xx + (0.012 if side == 0.0 else -0.012), 0.455, 0.004, 0.010)
        a.put(layer, a.mask_of(cords, blur=0.3), mix(p["gold"], p["near"], 0.25))
        pillar = a.mask_of(image) * ((a.u < 0.013) | (a.u > 0.987))
        a.put(layer, pillar, mix(p["gold"], p["near"], 0.45))
        # The boards of the stage, and a row of footlights on its edge.
        boards = (np.sin(a.u * math.tau * 60.0) > 0.92) * smoothstep(0.70, 0.71, a.v) * ground
        a.shade(layer, boards, 0.30)
        a.put(layer, a.band(0.707, 0.003, 1.0) * ground, mix(p["gold"], p["near"], 0.30))
        lamps(a, layer, [(0.22 + k * 0.08, 0.712, 0.0022) for k in range(8)], p["glow"], halo=3.0, strength=0.55)
        lamps(a, layer, lenses, p["spot"], halo=3.0, strength=0.7)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.4) * mask, p["glow"], 0.25)
        return layer
    layer = a.blank()
    # Two spotlight beams that cross over the stage, very faint.
    beams, beam_pen = a.drawing()
    beam_pen.poly([(0.02, 0.10), (0.06, 0.08), (0.62, 0.76), (0.48, 0.80)])
    beam_pen.poly([(0.98, 0.10), (0.94, 0.08), (0.38, 0.76), (0.52, 0.80)])
    a.put(layer, a.mask_of(beams, blur=12.0), p["spot"], 0.08)
    a.put(layer, fog(a, "stage haze", 0.70, 0.12), p["low"], 0.18)
    vignette(a, layer, p["near"], 0.34)
    return layer


def stage_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The valance over the stage: swags of velvet that hang from above, a
    tassel between each two. Nothing stands from below."""
    del layer_lights
    rng = art_.rand("stage foreground")
    pen.rect(0.0, 0.0, 1.0, 0.33)
    u = -0.02
    while u < 1.02:
        w = rng.uniform(0.09, 0.12)
        sag = rng.uniform(0.036, 0.046)
        pts = [(u + w * t, 0.33 + sag * math.sin(math.pi * t)) for t in np.linspace(0.0, 1.0, 17)]
        pen.poly([(u, 0.32), *pts, (u + w, 0.32)])
        pen.line([(u + w, 0.33), (u + w, 0.362)], 0.0014)
        pen.ellipse(u + w, 0.369, 0.0028, 0.006)
        u += w


# ---------------------------------------------------------------------------
# Teknis: the Workshop Deeps
# ---------------------------------------------------------------------------


def art_forge(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = FORGE
    if layer_key == "sky":
        # The back of the cave: dark at the roof, warm from the kilns.
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.35, p["mid"]), (HORIZON, p["low"]), (0.80, p["mid"]), (1.0, p["top"])]))
        a.light(layer, a.spot(0.18, 0.62, 0.30, 2.0, squash=1.2), p["kiln"], 0.30)
        a.light(layer, a.spot(0.80, 0.60, 0.28, 2.0, squash=1.2), p["kiln"], 0.24)
        for tag, base, amp, colour, amount in (("far wall a", 0.48, 0.08, mix(p["rock"], p["low"], 0.5), 0.70), ("far wall b", 0.58, 0.06, p["rock"], 0.80)):
            wall, _ = a.ridge(tag, base, amp, cells=4.0, octaves=5, sharp=0.4)
            a.tint(layer, wall, colour, amount)
        # Drafting lines scratched on the wall: gears, arcs of a compass,
        # lines with their measures, a grid.
        plan, plan_pen = a.drawing()
        _wheel(plan_pen, 0.22, 0.34, 0.06, 14, 0.010, width=0.0016)
        _wheel(plan_pen, 0.30, 0.42, 0.035, 10, 0.008, width=0.0016)
        plan_pen.ring(0.22, 0.34, 0.090, 0.0010)
        _wheel(plan_pen, 0.84, 0.30, 0.05, 12, 0.009, width=0.0016)
        for u0, v0, u1, v1 in ((0.60, 0.26, 0.74, 0.26), (0.62, 0.30, 0.62, 0.44), (0.66, 0.44, 0.76, 0.36)):
            plan_pen.line([(u0, v0), (u1, v1)], 0.0012)
            for t in np.linspace(0.0, 1.0, 6):
                x, y = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
                nx, ny = -(v1 - v0), (u1 - u0)
                d = math.hypot(nx, ny) or 1.0
                plan_pen.line([(x - nx / d * 0.004, y - ny / d * 0.004), (x + nx / d * 0.004, y + ny / d * 0.004)], 0.0010)
        plan_pen.arc(0.66, 0.36, 0.08, 200.0, 320.0, 0.0012)
        grid = ((np.abs(((a.u - 0.40) / 0.02) % 1.0 - 0.5) > 0.47) | (np.abs(((a.v - 0.22) / 0.02) % 1.0 - 0.5) > 0.47)) * (a.u > 0.40) * (a.u < 0.56) * (a.v > 0.22) * (a.v < 0.32)
        lines = np.maximum(a.mask_of(plan, blur=0.3), grid.astype(np.float32) * 0.6)
        a.tint(layer, lines, p["blueprint"], 0.22)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far deeps")
        image, pen = a.drawing()
        roof = 1.0 - a.ridge("roof", 0.12, 0.05, cells=4.0, octaves=4)[0]
        for _ in range(10):
            u = rng.random()
            length = rng.uniform(0.03, 0.08)
            w = rng.uniform(0.008, 0.016)
            pen.poly([(u - w, 0.08), (u + w, 0.08), (u + w * 0.2, 0.08 + length), (u - w * 0.15, 0.08 + length * 0.96)])
        ground, line = a.ridge("floor", HORIZON + 0.06, 0.02, cells=4.0, octaves=4)
        # The great machine at the back: a frame, two gears of metal, and a
        # third that is still only lines.
        machine, machine_pen = a.drawing()
        machine_pen.rect(0.385, 0.20, 0.397, HORIZON + 0.08)
        machine_pen.rect(0.625, 0.20, 0.637, HORIZON + 0.08)
        machine_pen.rect(0.37, 0.19, 0.65, 0.205)
        machine_pen.line([(0.39, 0.40), (0.63, 0.40)], 0.006)
        gears, gear_pen = a.drawing()
        _wheel(gear_pen, 0.46, 0.38, 0.075, 18, 0.012, hole=0.012, spokes=5)
        _wheel(gear_pen, 0.575, 0.495, 0.048, 12, 0.010, hole=0.009, spokes=4)
        ghost, ghost_pen = a.drawing()
        _wheel(ghost_pen, 0.565, 0.29, 0.058, 14, 0.011, width=0.0022)
        ghost_pen.line([(0.565, 0.29), (0.46, 0.38)], 0.0014)
        ghost_pen.line([(0.50, 0.21), (0.62, 0.21), (0.62, 0.36)], 0.0014)
        # Bottle kilns at the sides, a fire in each mouth.
        kilns, kiln_pen = a.drawing()
        mouths, mouth_pen = a.drawing()
        for u, h, w in ((0.13, 0.22, 0.065), (0.84, 0.19, 0.058)):
            v = float(line[min(a.n - 1, int(u * a.n))]) + 0.01
            _bottle_kiln(kiln_pen, mouth_pen, u, v, h, w)
        # A loom, its threads running up into the dark.
        loom, loom_pen = a.drawing()
        threads = []
        lu, lv = 0.27, float(line[int(0.27 * a.n)]) + 0.01
        for du in (-0.045, 0.045):
            loom_pen.rect(lu + du - 0.004, lv - 0.12, lu + du + 0.004, lv)
        loom_pen.rect(lu - 0.05, lv - 0.124, lu + 0.05, lv - 0.114)
        loom_pen.rect(lu - 0.05, lv - 0.05, lu + 0.05, lv - 0.042)
        for k in range(10):
            x = lu - 0.036 + k * 0.008
            threads.append(([(x, lv - 0.05), (x, lv - 0.114), (x + (k - 4.5) * 0.004, 0.10)], THREADS[k % len(THREADS)]))
        rock = np.maximum.reduce([roof, ground, a.mask_of(image)])
        build = np.maximum.reduce([a.mask_of(machine), a.mask_of(gears), a.mask_of(kilns), a.mask_of(loom)])
        layer = solid(a, np.maximum(rock, build), mix(p["rock"], p["low"], 0.35), p["rock"], 0.20, 0.70, "rock", 0.10)
        a.light(layer, a.rim(rock, -0.003, -0.003, 0.5) * rock, p["rock_light"], 0.35)
        metal = np.maximum(a.mask_of(machine), a.mask_of(gears))
        a.put(layer, metal, mix(p["brass"], p["mid"], 0.74))
        a.light(layer, a.rim(metal, -0.003, -0.003, 0.4) * metal, p["ember"], 0.30)
        a.shade(layer, a.rim(metal, 0.004, 0.004, 0.6) * metal, 0.30)
        a.glow(layer, a.mask_of(ghost, blur=0.4), p["blueprint"], 0.50)
        brick = a.mask_of(kilns)
        a.put(layer, brick, mix(p["clay"], p["mid"], 0.50))
        courses = (np.sin(a.v * 700.0) > 0.85) * brick
        a.shade(layer, courses, 0.25)
        a.light(layer, a.rim(brick, -0.004, 0.0, 0.6) * brick, p["kiln"], 0.35)
        fire = a.mask_of(mouths, blur=0.5)
        a.put(layer, fire, p["kiln"])
        a.put(layer, a.shift(fire, 0.0, 0.006) * fire, p["ember"], 0.8)
        a.glow(layer, a.blur(fire, 14.0), p["kiln"], 0.50)
        a.put(layer, a.mask_of(loom), mix(p["copper"], p["mid"], 0.55))
        for pts, colour in threads:
            one, one_pen = a.drawing()
            one_pen.line(pts, 0.0016)
            a.glow(layer, a.mask_of(one, blur=0.3) * smoothstep(0.10, 0.30, a.v), mix(colour, p["mid"], 0.35), 0.75)
        cloth = (np.abs(a.u - lu) < 0.038) * (a.v > lv - 0.11) * (a.v < lv - 0.08)
        stripe = (np.sin(a.v * 900.0) > 0.0)
        a.put(layer, cloth * stripe, mix(THREADS[0], p["mid"], 0.35))
        a.put(layer, cloth * (1 - stripe), mix(THREADS[2], p["mid"], 0.35))
        haze(a, layer, p["low"], 0.14, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        image, pen = a.drawing()
        ground, _ = a.ridge("near floor", 0.70, 0.012, cells=5.0, octaves=3)
        # Columns of brick at the sides, and the arm of a crane on the left.
        for u, w in ((0.03, 0.045), (0.97, 0.05)):
            pen.rect(u - w, 0.0, u + w, 0.74)
        pen.rect(0.07, 0.12, 0.25, 0.135)
        pen.line([(0.07, 0.20), (0.17, 0.135)], 0.006)
        pen.ellipse(0.24, 0.145, 0.010)
        pen.line([(0.24, 0.155), (0.24, 0.29)], 0.0016)
        pen.arc(0.24, 0.30, 0.010, 0.0, 200.0, 0.003)
        # A potter's wheel with a pot half thrown, and a shelf of pots.
        pen.ellipse(0.20, 0.715, 0.035, 0.008)
        pen.rect(0.195, 0.715, 0.205, 0.74)
        pen.poly([(0.19, 0.708), (0.21, 0.708), (0.214, 0.69), (0.206, 0.676), (0.208, 0.668), (0.192, 0.668), (0.194, 0.676), (0.186, 0.69)])
        pen.rect(0.86, 0.46, 0.925, 0.466)
        for u, h in ((0.872, 0.03), (0.893, 0.04), (0.912, 0.025)):
            pen.ellipse(u, 0.46 - h * 0.45, 0.009, h * 0.45)
            pen.rect(u - 0.004, 0.46 - h, u + 0.004, 0.46 - h * 0.7)
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.20, 0.74, "near brick", 0.10)
        columns = a.mask_of(image) * ((a.u < 0.08) | (a.u > 0.915))
        bricks = ((np.sin(a.v * 520.0) > 0.88) | ((np.sin(a.u * 260.0 + np.floor(a.v * 520.0 / math.tau) * 1.6) > 0.94))) * columns
        a.put(layer, columns, mix(p["clay"], p["near"], 0.62))
        a.shade(layer, bricks.astype(np.float32), 0.35)
        a.light(layer, a.rim(mask, -0.004, 0.0, 0.4) * mask, p["kiln"], 0.30)
        a.shade(layer, a.rim(mask, 0.005, -0.003, 1.0) * mask, 0.25)
        # The glow of a kiln mouth off the view at the right, on the floor.
        a.glow(layer, a.spot(1.0, 0.72, 0.18, 2.0, squash=1.5) * (1.0 - mask), p["kiln"], 0.30)
        a.light(layer, a.spot(1.0, 0.72, 0.25, 1.5) * mask, p["kiln"], 0.40)
        return layer
    layer = a.blank()
    a.put(layer, fog(a, "kiln smoke", 0.66, 0.16), mix(p["low"], p["kiln"], 0.2), 0.22)
    a.put(layer, a.band(0.76, 0.10) * (0.6 + 0.4 * a.noise("embers", cells=4.0)), p["kiln"], 0.10)
    vignette(a, layer, p["top"], 0.42)
    return layer


def forge_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Chains with hooks and threads from the looms, from above. Nothing
    stands from below."""
    rng = art_.rand("forge foreground")
    for k in range(5):
        u = (k + rng.uniform(0.2, 0.8)) / 5.0
        end = rng.uniform(0.38, 0.40)
        if k % 2 == 0:
            v = 0.0
            while v < end - 0.012:
                pen.ellipse(u, v, 0.0034, 0.0060)
                v += 0.0098
            pen.arc(u, end - 0.002, 0.009, 0.0, 200.0, 0.0035)
        else:
            for du in (-0.006, 0.0, 0.006):
                pen.line([(u + du, 0.0), (u + du * 0.4, end - 0.02)], 0.0014)
            pen.ellipse(u, end - 0.02, 0.006, 0.009)
            layer_lights.append((u, end - 0.004, 0.0014, FORGE["ember"]))
