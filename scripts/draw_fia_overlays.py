"""Draw Fia's overlays: ``data/overlays/fia.overlay.svg`` (her own look),
``fia_touched.overlay.svg`` (the void's first traces) and
``fia_void.overlay.svg`` (embraced by the void), hand-placed art over the
generated parts of ``data/characters/fia/*.chargen.yaml`` (``chargen.overlay``;
the target is ``targets/characters/fia.py``).

The SVG files are generated: edit the shapes here and run it again::

    python scripts/draw_fia_overlays.py            # all three looks
    python scripts/draw_fia_overlays.py fia_void   # one

Every shape is in a group's own units: its anchor joint (the neck for the head,
the waist for the belt, an elbow or a wrist) at (0, 0), +x toward the way the
view faces, +y down; a head is about 82 units tall. A shape is a smooth path
through control points (Catmull-Rom); a point ``(x, y, "c")`` is a corner,
for the tips of locks and tatters.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Sequence, Tuple, Union

import yaml


# ---- shapes -------------------------------------------------------------------------------------------
P = Union[Tuple[float, float], Tuple[float, float, str]]


def _xy(p):
    return float(p[0]), float(p[1])


def _corner(p) -> bool:
    return len(p) > 2 and p[2] == "c"


def path(points: Sequence[P], closed: bool = True, tension: float = 0.5) -> str:
    """A cubic path through ``points`` (Catmull-Rom); a point (x, y, "c") is a corner."""
    pts = list(points)
    n = len(pts)
    out = [f"M{_xy(pts[0])[0]:.2f},{_xy(pts[0])[1]:.2f}"]
    segs = n if closed else n - 1
    k = tension / 3.0
    for i in range(segs):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[(i + 1) % n]
        x0, y0 = _xy(p0); x1, y1 = _xy(p1); x2, y2 = _xy(p2); x3, y3 = _xy(p3)
        if _corner(p1):
            c1 = (x1, y1)
        else:
            c1 = (x1 + (x2 - x0) * k, y1 + (y2 - y0) * k)
        if _corner(p2):
            c2 = (x2, y2)
        else:
            c2 = (x2 - (x3 - x1) * k, y2 - (y3 - y1) * k)
        out.append(f"C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {x2:.2f},{y2:.2f}")
    if closed:
        out.append("Z")
    return " ".join(out)


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0.0, n: int = 10) -> str:
    pts = []
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return path(pts, True)


def rect(cx: float, cy: float, w: float, h: float, rot: float = 0.0, r: float = 0.0) -> str:
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + x * c - y * s, cy + x * s + y * c, "c"))
    return path(pts, True)


def poly(points) -> str:
    return path([(p[0], p[1], "c") for p in points], True)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def band(spine: Sequence[Tuple[float, float]], width: Union[float, Sequence[float]]) -> List[Tuple[float, float, str]]:
    """A strip of ``width`` along ``spine``: its outline points (smooth)."""
    n = len(spine)
    ws = [width] * n if isinstance(width, (int, float)) else list(width)
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        a = spine[max(0, i - 1)]; b = spine[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        left.append((x + nx * ws[i] / 2, y + ny * ws[i] / 2))
        right.append((x - nx * ws[i] / 2, y - ny * ws[i] / 2))
    return left + right[::-1]


def el(d: str, fill: str = "none", stroke: str = "none", width: float = 0.0, opacity: float = 1.0, cap: str = "round") -> str:
    attrs = f'd="{d}" fill="{fill}"'
    if stroke != "none":
        attrs += f' stroke="{stroke}" stroke-width="{width:g}" stroke-linejoin="round" stroke-linecap="{cap}"'
    if opacity != 1.0:
        attrs += f' opacity="{opacity:g}"'
    return f"<path {attrs}/>"


def inked(d: str, fill: str, ink: str, w: float) -> List[str]:
    """A shape with an outline outside it: the outline drawn under the fill."""
    return [el(d, fill, ink, w), el(d, fill)]

from ambition_sprite2d_renderer.chargen.body import build  # noqa: E402
from ambition_sprite2d_renderer.chargen.overlay import MEASURES, OVERLAYS  # noqa: E402
from ambition_sprite2d_renderer.chargen.rig import CELL_H, CELL_W, GROUND, UNIT, draw_views  # noqa: E402
from ambition_sprite2d_renderer.chargen.spec import complete  # noqa: E402
from ambition_sprite2d_renderer.chargen.svgout import Canvas  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer" / "data" / "characters" / "fia"
VIEWS = ("front", "front_3q", "side", "back_3q", "back")

LOOKS = {
    "fia": dict(
        ink="#14110f", hair="#3b2418", hair_dark="#25150d", hair_light="#6b4932", streak="#efe8dc", streak_shade="#c4b9a6",
        band="#a8322d", band_dark="#741d1a", band_light="#cf5b50", freckle="#a35d3d", plaster="#efdcb8", plaster_dot="#c7a77c",
        cuff="#8c6c44", cuff_dark="#5e4428", leather="#4a3123", leather_dark="#2e1d14", leather_light="#6e4c35", brass="#c99a45",
        steel="#9aa0a6", steel_dark="#5d6268", steel_light="#d6dade", wrap="#a8322d", glow="#f2b44a", lining="#8e2a28",
        # Her own hair has no white in it: the streak is the void's first mark.
        streaked=False,
    ),
}
W = 3.0     # the outline, in overlay units
FINE = 1.3  # an inner line


# ---- the head: hair, bandana, ponytail, face marks ------------------------------------------------

def hair_side(c):
    """Her own hair, side view (she faces +x): a messy crop over the crown with
    a fringe of flicks, a lock before the ear, the nape in tufts."""
    cap = path([
        (48, -52, "c"), (42, -56), (45, -48, "c"), (38, -53), (37, -46, "c"), (31, -50), (27, -42),
        (24, -28, "c"), (19, -37), (13, -39), (6, -41), (-2, -41), (-7, -33), (-9, -19, "c"), (-14, -27),
        (-21, -8, "c"), (-24, -20), (-31, -14, "c"), (-33, -27), (-38, -42), (-38, -57), (-31, -71), (-16, -82),
        (4, -85), (22, -81), (36, -72), (44, -62), (49, -55),
    ])
    out = inked(cap, c["hair"], c["ink"], W)
    # shade under the crown and over the nape
    out.append(el(path([(-36, -42), (-30, -24), (-22, -14), (-14, -26), (-8, -34), (-12, -40), (-24, -44)]), c["hair_dark"]))
    # sheen on the crown
    out.append(el(path([(-18, -77), (2, -81), (24, -76), (34, -68), (20, -72), (0, -75), (-14, -71)]), c["hair_light"]))
    # strands
    for pts in (((8, -82), (2, -64), (6, -48)), ((-10, -78), (-18, -58), (-14, -42)), ((26, -76), (24, -62), (30, -50))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    return out


def streak_side(c):
    # the white streak: one lock from the crown down over the brow
    lock = path([(22, -80), (32, -73), (41, -62), (44, -50, "c"), (37, -58), (29, -67), (19, -75)])
    return inked(lock, c["streak"], c["ink"], FINE) + [el(path([(26, -74), (34, -65), (39, -56)], closed=False), "none", c["streak_shade"], 1.0)]


def bandana_side(c):
    if c.get("void"):
        return []
    """The red bandana: a band over the crown behind the fringe, knotted at the
    back of the head, its two tails out behind."""
    strip = path(band([(30, -73), (14, -78), (-4, -78), (-20, -72), (-30, -61), (-35, -50)], [5.5, 6, 6.5, 6.5, 6, 5.5]))
    out = inked(strip, c["band"], c["ink"], W * 0.7)
    out.append(el(path(band([(25, -74), (10, -77.5), (-6, -77), (-19, -72)], 1.6)), c["band_light"]))
    out.append(el(path([(-31, -60), (-35, -50)], closed=False), "none", c["band_dark"], 1.4))
    # the knot and the tails
    knot = ellipse(-37, -50, 4.6, 4.0, -20)
    tail_a = path([(-39, -53), (-49, -58), (-58, -56, "c"), (-52, -51), (-43, -49)])
    tail_b = path([(-39, -48), (-46, -42), (-53, -34, "c"), (-50, -42), (-41, -45)])
    for d in (tail_a, tail_b):
        out += inked(d, c["band"], c["ink"], W * 0.7)
    out.append(el(path([(-43, -53), (-51, -55)], closed=False), "none", c["band_dark"], 1.1))
    out += inked(knot, c["band_dark"], c["ink"], W * 0.7)
    return out


#: Her ponytail, side view: tied high at the back of the crown, it rises and
#: sweeps back in big spiky locks, the shape that marks her at any size.
TAIL_SIDE = [
    (-20, -80), (-24, -96), (-34, -110), (-40, -122, "c"), (-44, -106), (-56, -112), (-70, -116, "c"), (-66, -102), (-82, -100),
    (-98, -98, "c"), (-84, -88), (-94, -78), (-106, -70, "c"), (-88, -66), (-94, -54), (-100, -40, "c"), (-82, -46), (-76, -32, "c"),
    (-66, -46), (-54, -42, "c"), (-48, -56), (-34, -58),
]


def _tail(c, pts, sheen, strands):
    out = inked(path(pts), c["hair"], c["ink"], W)
    out.append(el(path(sheen), c["hair_light"], opacity=0.6))
    for q in strands:
        out.append(el(path(q, closed=False), "none", c["hair_dark"], FINE))
    return out


def _squash(pts, kx, dx=0.0, ky=1.0, dy=0.0):
    return [(x * kx + dx, y * ky + dy) + tuple(p[2:]) for p in pts for x, y in [p[:2]]]


def ponytail_side(c):
    """The high ponytail: up from the crown and back in spiky locks."""
    return _tail(c, TAIL_SIDE, [(-26, -92), (-40, -106), (-62, -104), (-80, -92), (-60, -94), (-40, -94)],
                 (((-30, -86), (-54, -96), (-84, -92)), ((-32, -76), (-62, -78), (-92, -68)), ((-36, -66), (-64, -62), (-84, -50))))


def face_side(c):
    out = []
    for x, y in ((38, -29), (41, -27.5), (44, -29), (35, -26.5), (39, -25), (32, -28)):
        out.append(el(ellipse(x, y, 0.8, 0.7), c["freckle"]))
    # the plaster across her cheekbone
    out += inked(rect(31, -20, 8.5, 3.8, -22), c["plaster"], c["ink"], 1.1)
    for dx in (-2, 0, 2):
        out.append(el(ellipse(31 + dx * 0.93, -20 - dx * 0.37, 0.42, 0.42), c["plaster_dot"]))
    return out


def hair_f3q(c):
    cap = path([
        (-31, -26, "c"), (-30, -40), (-36, -56), (-30, -72), (-14, -82), (6, -86), (26, -81), (39, -71), (45, -58),
        (44, -50, "c"), (38, -56), (35, -48, "c"), (28, -55), (22, -47, "c"), (16, -54), (9, -46, "c"), (3, -52),
        (-2, -44), (-5, -30, "c"), (-10, -40), (-15, -43), (-22, -42), (-26, -34),
    ])
    out = inked(cap, c["hair"], c["ink"], W)
    out.append(el(path([(-30, -40), (-26, -28), (-22, -36), (-16, -40), (-24, -44)]), c["hair_dark"]))
    out.append(el(path([(-16, -77), (6, -82), (26, -77), (36, -68), (20, -72), (2, -75), (-12, -71)]), c["hair_light"]))
    for pts in (((-6, -80), (-12, -62), (-8, -46)), ((18, -80), (16, -62), (24, -50)), ((32, -74), (34, -62), (38, -54))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    return out


def streak_f3q(c):
    lock = path([(2, -84), (11, -76), (14, -63), (11, -48, "c"), (6, -58), (1, -69), (-5, -78)])
    return inked(lock, c["streak"], c["ink"], FINE) + [el(path([(4, -76), (9, -65), (10, -55)], closed=False), "none", c["streak_shade"], 1.0)]


def bandana_f3q(c):
    if c.get("void"):
        return []
    strip = path(band([(-32, -55), (-24, -67), (-8, -75), (12, -78), (29, -73), (40, -63)], [5.5, 6, 6.5, 6.5, 6, 5.5]))
    out = inked(strip, c["band"], c["ink"], W * 0.7)
    out.append(el(path(band([(-20, -69), (-6, -74.5), (12, -77), (27, -73)], 1.6)), c["band_light"]))
    # a tail of the knot shows past the back of her head
    tail = path([(-33, -56), (-43, -59), (-49, -53, "c"), (-43, -51), (-35, -52)])
    out = inked(tail, c["band"], c["ink"], W * 0.7) + out
    return out


def ponytail_f3q(c):
    """Turned toward us the tail sweeps back past the far side of her head."""
    pts = _squash(TAIL_SIDE, 0.78, -6.0)
    return _tail(c, pts, _squash([(-26, -92), (-40, -106), (-62, -104), (-80, -92), (-60, -94), (-40, -94)], 0.78, -6.0),
                 [_squash(q, 0.78, -6.0) for q in (((-30, -86), (-54, -96), (-84, -92)), ((-36, -66), (-64, -62), (-84, -50)))])


def face_f3q(c):
    out = []
    for x, y in ((24, -25), (27, -23.5), (30, -25.5), (34, -24), (21, -23), (25.5, -21.5), (36.5, -26)):
        out.append(el(ellipse(x, y, 0.8, 0.7), c["freckle"]))
    out += inked(rect(14, -22, 9, 3.9, -18), c["plaster"], c["ink"], 1.1)
    for dx in (-2, 0, 2):
        out.append(el(ellipse(14 + dx * 0.95, -22 - dx * 0.31, 0.42, 0.42), c["plaster_dot"]))
    return out


def hair_front(c):
    cap = path([
        (-33, -26, "c"), (-31, -40), (-37, -56), (-30, -72), (-14, -82), (2, -85), (18, -82), (31, -73), (37, -58), (32, -42),
        (33, -27, "c"), (27, -38), (24, -48, "c"), (19, -54), (15, -47, "c"), (10, -55), (4, -47, "c"), (-1, -55),
        (-6, -47, "c"), (-12, -55), (-17, -47, "c"), (-22, -53), (-25, -42), (-27, -30, "c"), (-30, -38),
    ])
    out = inked(cap, c["hair"], c["ink"], W)
    out.append(el(path([(-18, -76), (0, -81), (18, -78), (28, -70), (14, -73), (0, -76), (-14, -72)]), c["hair_light"]))
    for pts in (((-20, -78), (-24, -64), (-22, -50)), ((22, -78), (24, -64), (22, -50)), ((6, -82), (4, -68), (8, -54))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    return out


def bandana_front(c):
    if c.get("void"):
        return []
    strip = path(band([(-35, -56), (-26, -69), (-10, -76), (8, -76), (24, -70), (34, -57)], [5.5, 6, 6.5, 6.5, 6, 5.5]))
    out = inked(strip, c["band"], c["ink"], W * 0.7)
    out.append(el(path(band([(-22, -71), (-8, -75.5), (8, -75.5), (22, -71)], 1.6)), c["band_light"]))
    return out


def streak_front(c):
    lock = path([(-8, -84), (-14, -76), (-17, -63), (-14, -49, "c"), (-10, -59), (-5, -70), (0, -79)])
    return inked(lock, c["streak"], c["ink"], FINE) + [el(path([(-10, -76), (-14, -65), (-14, -55)], closed=False), "none", c["streak_shade"], 1.0)]


def ponytail_front(c):
    """From the front the tail is behind her head, sweeping away from us: its
    locks show over the crown and out past her left side (+x)."""
    pts = [(-14, -80), (-12, -96), (-4, -108, "c"), (4, -98), (16, -112, "c"), (20, -96), (36, -104, "c"), (34, -90), (52, -88, "c"),
           (42, -78), (56, -66, "c"), (40, -66), (46, -52, "c"), (32, -60), (24, -76)]
    return inked(path(pts), c["hair"], c["ink"], W) + [el(path(((8, -92), (24, -94), (38, -84)), closed=False), "none", c["hair_dark"], FINE)]


def face_front(c):
    out = []
    for x, y in ((-6, -25), (-3, -23.5), (3, -23.5), (6, -25), (-9, -23), (9, -23), (0, -26)):
        out.append(el(ellipse(x, y, 0.8, 0.7), c["freckle"]))
    out += inked(rect(-18, -21, 9, 3.9, 14), c["plaster"], c["ink"], 1.1)
    for dx in (-2, 0, 2):
        out.append(el(ellipse(-18 + dx * 0.97, -21 + dx * 0.24, 0.42, 0.42), c["plaster_dot"]))
    return out


def _back_tail(c, cx, lean):
    """The ponytail from behind, over the back of her head: tied at the knot
    (cx, -66), its locks spring up past the crown and fan out and down to
    either side; ``lean`` turns it toward +x."""
    pts = [(cx - 8, -68), (cx - 18 + lean, -84), (cx - 28 + lean, -100, "c"), (cx - 16 + lean, -96), (cx - 8 + lean, -112, "c"),
           (cx + 2 + lean, -96), (cx + 16 + lean, -108, "c"), (cx + 16 + lean, -90), (cx + 30 + lean, -86, "c"), (cx + 22 + lean, -74),
           (cx + 34 + lean, -52, "c"), (cx + 18 + lean, -60), (cx + 16 + lean, -36, "c"), (cx + 6 + lean, -52), (cx - 2 + lean, -30, "c"),
           (cx - 8 + lean, -50), (cx - 20 + lean, -38, "c"), (cx - 20 + lean, -58), (cx - 32 + lean, -60, "c"), (cx - 22 + lean, -72)]
    out = inked(path(pts), c["hair"], c["ink"], W)
    out.append(el(path([(cx - 6, -74), (cx - 12 + lean, -92), (cx + 4 + lean, -100), (cx + 12 + lean, -88), (cx + 6, -74)]), c["hair_light"], opacity=0.55))
    for pts2 in (((cx - 4, -70), (cx - 14 + lean, -86), (cx - 18 + lean, -96)), ((cx + 4, -70), (cx + 16 + lean, -84), (cx + 24 + lean, -92)),
                 ((cx - 4, -62), (cx - 12 + lean, -52), (cx - 14 + lean, -46)), ((cx + 4, -62), (cx + 14 + lean, -54), (cx + 26 + lean, -54))):
        out.append(el(path(pts2, closed=False), "none", c["hair_dark"], FINE))
    # the bandana's knot, and its tails out over the hair
    for d in (path([(cx - 3, -66), (cx - 16, -74), (cx - 26, -68, "c"), (cx - 17, -64), (cx - 5, -63)]),
              path([(cx + 3, -66), (cx + 14, -58), (cx + 20, -46, "c"), (cx + 12, -54), (cx + 2, -62)])):
        out += inked(d, c["band"], c["ink"], W * 0.7)
    out += inked(ellipse(cx, -66, 5, 4.2), c["band_dark"], c["ink"], W * 0.7)
    return out


def hair_back_3q(c):
    cap = path([
        (-34, -46), (-38, -60), (-30, -74), (-14, -83), (6, -86), (24, -82), (37, -72), (41, -58), (40, -46),
        (38, -36, "c"), (32, -42), (27, -44), (24, -36), (20, -20, "c"), (14, -16), (8, -10, "c"), (2, -16), (-6, -10, "c"),
        (-10, -18), (-18, -14, "c"), (-22, -24), (-30, -30, "c"),
    ])
    out = inked(cap, c["hair"], c["ink"], W)
    out.append(el(path([(-20, -78), (4, -83), (26, -78), (36, -68), (20, -73), (2, -76), (-14, -72)]), c["hair_light"]))
    for pts in (((-24, -70), (-28, -50), (-22, -30)), ((24, -72), (26, -54), (20, -36))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    # the band over the crown, from her ear round to the knot
    if not c.get("void"):
        strip = path(band([(36, -60), (30, -72), (16, -78), (2, -76)], [5.5, 6, 6, 5.5]))
        out += inked(strip, c["band"], c["ink"], W * 0.7)
    return out + (_back_flame(c, 0, -6) if c.get("void") else _back_tail(c, 0, -6))


def hair_back_view(c):
    cap = path([
        (-35, -46), (-37, -60), (-30, -74), (-14, -83), (0, -85), (14, -83), (30, -74), (37, -60), (35, -46),
        (34, -30, "c"), (28, -36), (24, -20, "c"), (17, -26), (12, -12, "c"), (6, -20), (0, -10, "c"), (-6, -20), (-12, -12, "c"),
        (-17, -26), (-24, -20, "c"), (-28, -36), (-34, -30, "c"),
    ])
    out = inked(cap, c["hair"], c["ink"], W)
    out.append(el(path([(-20, -78), (0, -82), (20, -78), (30, -70), (14, -74), (0, -76), (-14, -74)]), c["hair_light"]))
    for pts in (((-24, -70), (-28, -50), (-24, -34)), ((24, -70), (28, -50), (24, -34))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    for side in (-1, 1) if not c.get("void") else ():
        strip = path(band([(side * 35, -56), (side * 28, -68), (side * 14, -74), (side * 4, -70)], [5.5, 6, 6, 5.5]))
        out += inked(strip, c["band"], c["ink"], W * 0.7)
    return out + (_back_flame(c, 0, 0) if c.get("void") else _back_tail(c, 0, 0))


def nothing(c):
    return []


HEAD = {
    "side": dict(hair=hair_side, bandana=bandana_side, streak=streak_side, ponytail=ponytail_side, face=face_side),
    "front_3q": dict(hair=hair_f3q, bandana=bandana_f3q, streak=streak_f3q, ponytail=ponytail_f3q, face=face_f3q),
    "front": dict(hair=hair_front, bandana=bandana_front, streak=streak_front, ponytail=ponytail_front, face=face_front),
    "back_3q": dict(hair=hair_back_3q, bandana=nothing, streak=nothing, ponytail=nothing, face=nothing),
    "back": dict(hair=hair_back_view, bandana=nothing, streak=nothing, ponytail=nothing, face=nothing),
}


# ---- the body: belt over the coat, pouch and wrench, rolled sleeves, wrist cuffs ---------------------

#: Per view: the belt's span across the coat (x0, x1, rel. the waist) and where its
#: buckle is (None: not seen), and the side of the hip the pouch hangs on.
BELT = {"front": (-45, 45, 0), "front_3q": (-33, 47, 18), "side": (-31, 29, 25), "back_3q": (-33, 47, None), "back": (-45, 45, None)}
POUCH_X = {"front": -12, "front_3q": -6, "side": 2, "back_3q": 2, "back": 10}


def belt(c, view):
    x0, x1, buckle = BELT[view]
    sag = 2.5 if view in ("front", "front_3q") else (-1.5 if view.startswith("back") else 0.0)
    mid = buckle if buckle is not None else (x0 + x1) / 2
    spine = [(x0, 21), (mid, 22 + sag), (x1, 21)]
    out = inked(path(band(spine, 7.5), closed=True), c["leather"], c["ink"], W * 0.7)
    out.append(el(path([(x0 + 2, 18.6), (mid, 19.6 + sag), (x1 - 2, 18.6)], closed=False), "none", c["leather_light"], 1.0))
    for k in range(5):
        x = x0 + (x1 - x0) * (k + 0.5) / 5
        if buckle is None or abs(x - buckle) > 8:
            out.append(el(ellipse(x, 21.5 + sag * (1 - abs(x - mid) / max(1, (x1 - x0) / 2)), 0.9, 0.9), c["brass"]))
    if buckle is not None:
        out += inked(rect(buckle, 22 + sag, 9, 9.5), c["brass"], c["ink"], 1.4)
        out.append(el(rect(buckle, 22 + sag, 4.6, 5.2), c["leather_dark"]))
        out.append(el(path([(buckle - 1.5, 19.5 + sag), (buckle - 1.5, 24.5 + sag)], closed=False), "none", c["steel_light"], 1.0))
    return out


def pouch(c, view, at=(0.0, 0.0)):
    """Her tool pouch on the belt at the near hip, tools showing, the wrench beside it;
    ``at`` is the near hip from the group's anchor."""
    x = POUCH_X[view] + at[0]
    top = -24 + at[1]
    out = []
    # the wrench, behind the pouch: steel, the grip wrapped red, a slot that glows
    if not view.startswith("back"):
        wx = x + 11
        jaw = path([(wx - 4, top - 13), (wx - 5.5, top - 20, "c"), (wx - 1.5, top - 17), (wx + 1.5, top - 17), (wx + 5.5, top - 20, "c"),
                    (wx + 4, top - 13), (wx + 2, top - 10), (wx - 2, top - 10)])
        shaft = rect(wx, top + 3, 4.2, 26)
        out += inked(shaft, c["steel"], c["ink"], 1.6) + inked(jaw, c["steel"], c["ink"], 1.6)
        out.append(el(rect(wx, top - 3, 1.4, 7), c["glow"]))
        out += inked(rect(wx, top + 12, 5.0, 9), c["wrap"], c["ink"], 1.2)
        out.append(el(path([(wx - 2.2, top + 9), (wx + 2.2, top + 11), (wx - 2.2, top + 13), (wx + 2.2, top + 15)], closed=False), "none", c["band_dark"], 0.9))
    # tools out of the top: a screwdriver and a pencil
    out += inked(rect(x - 3, top - 4, 2.6, 9, -8), c["band"], c["ink"], 1.1)
    out += inked(rect(x + 3, top - 3, 2.2, 8, 6), c["brass"], c["ink"], 1.1)
    body = path([(x - 8, top, "c"), (x + 8, top, "c"), (x + 8.5, top + 17), (x + 6, top + 20, "c"), (x - 6, top + 20, "c"), (x - 8.5, top + 17)])
    out += inked(body, c["leather_light"], c["ink"], W * 0.6)
    flap = path([(x - 8.6, top - 1, "c"), (x + 8.6, top - 1, "c"), (x + 8, top + 8), (x, top + 10), (x - 8, top + 8)])
    out += inked(flap, c["leather"], c["ink"], 1.3)
    out.append(el(ellipse(x, top + 7.5, 1.3, 1.3), c["brass"]))
    out.append(el(path([(x - 6, top + 16), (x + 6, top + 16)], closed=False), "none", c["leather"], 0.9))
    return out


def coat_cuff(c, view):
    """The coat's sleeve rolled up to the elbow (anchored at the elbow)."""
    out = inked(path(band([(-12, -3), (0, -2), (12, -3)], [9, 10, 9])), c["cuff"], c["ink"], W * 0.7)
    out.append(el(path([(-10, -5), (0, -4.5), (10, -5)], closed=False), "none", c["cuff_dark"], 1.1))
    return out


def wrist_cuff(c, view):
    """A leather cuff at the wrist (anchored at the wrist)."""
    out = inked(path(band([(-8, -4), (0, -3.5), (8, -4)], 6.5)), c["leather"], c["ink"], 1.6)
    out.append(el(ellipse(0, -3.8, 1.0, 1.0), c["brass"]))
    return out


# ---- the void: Fia embraced ---------------------------------------------------------------------------

#: Touched by the void: its first traces. A white streak in her hair, her
#: hands gone black and the black creeping up her forearms from the wrists,
#: two of its diamonds near her.
LOOKS["fia_touched"] = dict(LOOKS["fia"], streaked=True, touched=True, creep="#1c1c20", creep_edge="#3a3a3e", white="#f6f6f6")

LOOKS["fia_void"] = dict(
    LOOKS["fia"], void=True, streaked=True, ink="#050506", hair="#f2f2f2", hair_dark="#9a9a9e", hair_light="#ffffff", streak="#0b0b0c",
    streak_shade="#3a3a3e", cuff="#0b0b0c", cuff_dark="#3a3a3e", leather="#0b0b0c", leather_dark="#000000", leather_light="#26262a",
    brass="#f4f4f4", steel="#e6e6e8", steel_dark="#8a8a8e", steel_light="#ffffff", wrap="#0b0b0c", glow="#ffffff", band="#0b0b0c",
    band_dark="#000000", band_light="#3a3a3e", white="#f6f6f6",
)
#: The void's outline on its black pieces: white, as the family's ink.
VOID_INK = "#f4f4f4"


def _vinked(d, fill, c, w):
    """A black void piece: a white outline outside it."""
    return inked(d, fill, VOID_INK if c.get("void") else c["ink"], w)


def _grow(pts, k, root):
    """``pts`` scaled ``k`` times about ``root``: the void's flame is bigger
    than the ponytail it was."""
    rx, ry = root
    return [(rx + (p[0] - rx) * k, ry + (p[1] - ry) * k) + tuple(p[2:]) for p in pts]


#: How much bigger than her ponytail the void's flame is.
FLAME = 1.45


#: The void's flame, side view: her ponytail loosed, white locks rising up and back.
FLAME_SIDE = [(-30, -64), (-42, -80), (-52, -100, "c"), (-52, -84), (-68, -96, "c"), (-64, -78), (-84, -78, "c"), (-70, -66),
              (-86, -56, "c"), (-68, -52), (-78, -38, "c"), (-60, -42), (-60, -26, "c"), (-48, -38), (-42, -26, "c"), (-38, -40), (-33, -46)]
FLAME_STRANDS = (((-38, -60), (-56, -72), (-70, -74)), ((-38, -52), (-58, -54), (-72, -50)), ((-40, -46), (-52, -40), (-56, -32)))


def _flame(c, kx, dx):
    root = (-30, -60)
    out = inked(path(_squash(_grow(FLAME_SIDE, FLAME, root), kx, dx)), c["hair"], c["ink"], W)
    for q in FLAME_STRANDS:
        out.append(el(path(_squash(_grow(q, FLAME, root), kx, dx), closed=False), "none", c["hair_dark"], FINE))
    return out


def flame_side(c):
    """Her ponytail loosed by the void: white locks rising up and back like flame."""
    return _flame(c, 1.0, 0.0)


def flame_f3q(c):
    return _flame(c, 0.78, -2.0)


def flame_front(c):
    pts = [(-26, -74), (-34, -96, "c"), (-20, -86), (-12, -106, "c"), (-2, -88), (10, -108, "c"), (16, -88), (30, -100, "c"),
           (30, -82), (44, -88, "c"), (36, -72)]
    return inked(path(_grow(pts, FLAME * 0.9, (4, -72))), c["hair"], c["ink"], W)


def _back_flame(c, cx, lean):
    pts = [(cx - 10, -64), (cx - 22 + lean, -76), (cx - 30 + lean, -98, "c"), (cx - 16 + lean, -84), (cx - 8 + lean, -104, "c"),
           (cx + 2 + lean, -86), (cx + 14 + lean, -102, "c"), (cx + 14 + lean, -82), (cx + 30 + lean, -90, "c"), (cx + 20 + lean, -72),
           (cx + 10, -62)]
    root = (cx, -66)
    out = inked(path(_grow(pts, FLAME * 0.9, root)), c["hair"], c["ink"], W)
    out.append(el(path(_grow(((cx - 4, -66), (cx - 8 + lean, -82), (cx - 10 + lean, -94)), FLAME * 0.9, root), closed=False), "none", c["hair_dark"],
                  FINE))
    return out


def face_void(c, at, rot):
    """Where her plaster was, a white diamond: the void's mark."""
    x, y = at
    d = path([(x, y - 4.2, "c"), (x + 2.4, y, "c"), (x, y + 4.2, "c"), (x - 2.4, y, "c")])
    return inked(d, c["white"], c["ink"], 1.0)


def tatters(c, view, side):
    """The coat's hem coming apart into the void: long black tongues edged in
    white, trailing (anchored at the hip; the hem is about 88 below it)."""
    lean = -12 if view == "side" else (5 if side == "far" else -5)
    tips = ((-24, 132), (-6, 116), (10, 146), (26, 124)) if side == "near" else ((-26, 122), (-8, 142), (12, 118), (28, 136))
    pts = [(-33, 78), (-33, 92)]
    roots = [-33, -15, 2, 18, 33]
    for i, (tx, ty) in enumerate(tips):
        pts += [(tx + lean * (ty - 88) / 50, ty, "c"), (roots[i + 1] - 1, 94 + (i % 2) * 4)]
    pts += [(33, 78)]
    out = _vinked(path(pts), c["leather"], c, W * 0.7)
    for tx, ty in tips:
        out.append(el(path([(tx * 0.8, 92), (tx + lean * (ty - 88) / 80, ty - 14)], closed=False), "none", "#3a3a3e", 1.2))
    return out


def creep(c, elbow, arm_r):
    """The void creeping up a forearm from the wrist (anchored at the wrist;
    ``elbow`` is the elbow from it, ``arm_r`` the arm's radii in cm): black
    to a little past halfway, its top edge in flames, a vein or two above."""
    ex, ey = elbow
    L = math.hypot(ex, ey) or 1.0
    ux, uy = ex / L, ey / L
    nx, ny = -uy, ux
    _rs, re, rw = (r * UNIT for r in arm_r)

    def at(t, k):
        r = (rw + (re - rw) * t) * k + 0.4
        return (ux * L * t + nx * r, uy * L * t + ny * r)

    pts = [at(-0.04, -1.0), at(-0.04, 1.0)]
    for t, k in ((0.38, 1.0), (0.5, 0.75), (0.44, 0.45), (0.6, 0.15), (0.47, -0.15), (0.54, -0.5), (0.4, -0.8), (0.36, -1.0)):
        pts.append(at(t, k) + (("c",) if abs(k) < 0.9 and t > 0.45 else ()))
    out = [el(path(pts), c["creep"])]
    for t0, t1, k in ((0.5, 0.68, 0.3), (0.52, 0.64, -0.55)):
        out.append(el(path([at(t0, k), at((t0 + t1) / 2, k + 0.12), at(t1, k - 0.05)], closed=False), "none", c["creep_edge"], 1.2))
    return out


def diamonds(c, view, which=(0, 1, 2, 3), size=1.0):
    """White diamonds that drift about her (anchored at the waist): ``which``
    of them, at ``size``."""
    spots = {"side": ((-52, -50, 5.5), (56, -78, 4.0), (-62, 30, 3.2), (60, 20, 4.6)),
             "front_3q": ((-58, -62, 5.0), (66, -70, 4.2), (-64, 24, 3.4), (70, 30, 4.4)),
             "front": ((-66, -60, 5.0), (66, -72, 4.4), (-70, 26, 3.4), (70, 18, 4.2)),
             "back_3q": ((-60, -70, 4.4), (66, -58, 5.0), (-66, 30, 4.2), (70, 22, 3.4)),
             "back": ((-66, -70, 4.4), (66, -60, 5.0), (-70, 20, 4.2), (70, 28, 3.4))}[view]
    out = []
    for x, y, r in (spots[i] for i in which):
        r *= size
        d = path([(x, y - r * 1.7, "c"), (x + r, y, "c"), (x, y + r * 1.7, "c"), (x - r, y, "c")])
        out += inked(d, c["white"], c["ink"], 1.4)
        out.append(el(path([(x, y - r * 1.1, "c"), (x + r * 0.35, y, "c"), (x, y + r * 1.1, "c"), (x - r * 0.35, y, "c")]), "#cfcfd3"))
    return out


# ---- mechanic look: revised local artwork, shared by normal and touched ------
# The accepted Void silhouette is deliberately left on the original contours.
# These are local part drawings; the chargen rig still owns all posing.
MECHANIC_TAILS = {
    'side': [(-19,-77),(-28,-99),(-46,-111),(-67,-109),(-86,-99),(-98,-83,'c'),(-78,-89),(-83,-75),(-104,-61,'c'),(-82,-63),(-85,-49),(-96,-36,'c'),(-73,-40),(-62,-51),(-67,-31,'c'),(-48,-44),(-37,-60),(-23,-65)],
    'front_3q': [(-18,-75),(-25,-97),(-41,-109),(-59,-107),(-75,-97),(-83,-82,'c'),(-67,-87),(-72,-72),(-88,-60,'c'),(-68,-64),(-70,-46),(-76,-37,'c'),(-57,-41),(-46,-57),(-48,-40,'c'),(-32,-53),(-21,-65)],
    'front': [(-14,-77),(-17,-96),(-6,-110),(11,-112),(30,-105),(43,-89,'c'),(27,-92),(34,-75),(48,-62,'c'),(31,-65),(31,-49),(19,-37,'c'),(21,-58),(8,-68),(-5,-67)],
    'back_3q': [(-6,-67),(-23,-88),(-25,-103),(-12,-111),(7,-109),(22,-99),(33,-80,'c'),(16,-88),(25,-65),(26,-47,'c'),(12,-59),(14,-38),(6,-24,'c'),(-1,-46),(-15,-36,'c'),(-18,-55),(-34,-46,'c'),(-25,-72)],
    'back': [(-10,-67),(-24,-87),(-23,-103),(-9,-111),(10,-110),(25,-99),(34,-82,'c'),(18,-88),(23,-65),(29,-48,'c'),(13,-58),(13,-39),(3,-24,'c'),(-4,-48),(-17,-36,'c'),(-17,-55),(-30,-45,'c'),(-22,-74)],
}

MECHANIC_LOCKS = {
    'side': [((-27,-88),(-47,-100),(-75,-97),(-89,-89)),((-30,-79),(-56,-85),(-84,-69)),((-34,-66),(-52,-62),(-75,-49))],
    'front_3q': [((-25,-87),(-45,-99),(-69,-94)),((-29,-76),(-48,-81),(-72,-68)),((-31,-66),(-47,-58),(-61,-45))],
    'front': [((-7,-95),(13,-103),(31,-93)),((0,-86),(17,-83),(31,-70)),((7,-75),(18,-63),(21,-48))],
    'back_3q': [((-9,-82),(-11,-101),(9,-101),(22,-90)),((2,-76),(12,-63),(15,-47)),((-9,-70),(-20,-58),(-22,-53))],
    'back': [((-9,-82),(-10,-102),(9,-101),(21,-91)),((3,-78),(9,-60),(5,-36)),((-9,-72),(-15,-60),(-20,-54))],
}


def mechanic_ponytail(c, view):
    """A tied, layered mass of hair, not evenly spaced radial spikes."""
    pts = MECHANIC_TAILS[view]
    locks = MECHANIC_LOCKS[view]
    out = inked(path(pts), c['hair'], c['ink'], W)
    for i, lock in enumerate(locks):
        out.append(el(path(band(lock, [1.0] + [5.0] * (len(lock)-2) + [0.6])),
                      c['hair_light'], opacity=0.68 if i == 0 else 0.43))
        out.append(el(path(lock, closed=False), 'none', c['hair_dark'], 1.5))
    return out


def mechanic_crown(c, view):
    """Keep the crown fitted to the existing head; draw swept, uneven locks."""
    if view == 'side':
        pts = [(47,-52,'c'),(39,-56),(43,-46,'c'),(31,-51),(24,-35,'c'),(20,-44),(12,-43),(4,-39),(-8,-37),(-12,-19,'c'),(-19,-28),(-26,-17,'c'),(-33,-36),(-37,-55),(-31,-70),(-15,-82),(5,-85),(24,-80),(39,-68)]
        locks = [((-20,-76),(-9,-64),(-11,-42)),((0,-80),(15,-70),(27,-53)),((19,-77),(32,-68),(41,-57))]
    elif view == 'front_3q':
        pts = [(-31,-26,'c'),(-30,-42),(-36,-56),(-30,-72),(-14,-82),(6,-86),(26,-81),(39,-71),(45,-58),(43,-48,'c'),(35,-56),(28,-46,'c'),(19,-55),(9,-48,'c'),(0,-54),(-6,-32,'c'),(-11,-43),(-21,-43),(-27,-32)]
        locks = [((-20,-75),(-9,-66),(-8,-46)),((-1,-81),(12,-70),(18,-54)),((22,-78),(34,-65),(40,-54))]
    elif view == 'front':
        pts = [(-33,-26,'c'),(-31,-41),(-37,-57),(-30,-72),(-14,-82),(2,-85),(18,-82),(31,-73),(37,-58),(32,-42),(33,-27,'c'),(25,-37),(20,-52),(8,-47,'c'),(12,-59),(0,-53),(-9,-44,'c'),(-6,-58),(-18,-52),(-26,-37),(-28,-29,'c')]
        locks = [((-21,-76),(-21,-64),(-26,-44)),((-5,-82),(1,-70),(-7,-52)),((12,-79),(23,-67),(28,-45))]
    else:
        # Rear cap, with the ponytail placed in front of it below.
        pts = [(-34,-46),(-37,-60),(-30,-74),(-14,-83),(3,-86),(23,-82),(35,-72),(38,-58),(35,-43),(32,-28,'c'),(25,-34),(19,-17,'c'),(9,-22),(2,-11,'c'),(-5,-21),(-15,-14,'c'),(-20,-27),(-30,-24,'c')]
        locks = [((-24,-71),(-27,-49),(-20,-32)),((18,-76),(27,-55),(24,-34))]
    out = inked(path(pts), c['hair'], c['ink'], W)
    for i, lock in enumerate(locks):
        out.append(el(path(band(lock, [0.6] + [5.0] * (len(lock)-2) + [1.0])), c['hair_light'], opacity=.55))
        out.append(el(path(lock, closed=False), 'none', c['hair_dark'], 1.2))
    return out


def mechanic_hair(c, view):
    out = mechanic_crown(c, view)
    if view.startswith('back'):
        # Behind, the knot and tail overlay the crown rather than hiding under it.
        out += mechanic_ponytail(c, view)
        for d in (path([(-3,-69),(-19,-75),(-27,-68,'c'),(-15,-63),(-3,-63)]),
                  path([(3,-68),(14,-59),(21,-47,'c'),(10,-55),(1,-62)])):
            out += inked(d,c['band'],c['ink'],W*.7)
        out += inked(ellipse(0,-66,5,4.5),c['band_dark'],c['ink'],W*.7)
    else:
        # A wide cloth band across the crown, rather than a narrow hair hoop.
        spine = {'side': [(31,-73),(16,-79),(-4,-79),(-22,-72),(-35,-53)],
                 'front_3q': [(-32,-56),(-24,-69),(-8,-76),(12,-79),(29,-73),(40,-64)],
                 'front': [(-35,-57),(-26,-69),(-10,-76),(8,-76),(24,-70),(34,-57)]}[view]
        out += inked(path(band(spine, 9.0)),c['band'],c['ink'],W*.65)
        out.append(el(path(spine,closed=False),'none',c['band_light'],1.6))
        if view != 'front':
            x,y = spine[-1] if view == 'side' else spine[0]
            out += inked(path([(x,y-2),(x-9,y-2),(x-19,y+6,'c'),(x-8,y+6),(x-2,y+4)]),c['band_dark'],c['ink'],1.5)
            out += inked(ellipse(x,y,4.5,4),c['band'],c['ink'],1.5)
        if c.get('streaked'):
            out += HEAD[view]['streak'](c)
    return out


def mechanic_coat(c, view):
    """Lapel, reinforced seams and pockets on the torso part, in waist units."""
    seam, light, dark = '#67523d', '#c6aa7d', '#786044'
    out = []
    if view in ('front','front_3q'):
        # A folded facing and a small breast tool pocket. Coordinates are
        # independently selected in each view, never scaled from a full sprite.
        if view == 'front':
            panels = [(-1,0),(1,0)]
        else:
            panels = [(-1,3)]
        for s,dx in panels:
            q = [(dx+s*x,y) for x,y in [(13,-83),(25,-72),(21,-57),(13,-60),(19,-49),(9,-30),(10,-56)]]
            out += inked(path(q),dark,seam,1.6)
            out.append(el(path([(dx+s*14,-81),(dx+s*22,-72),(dx+s*18,-59)],closed=False),'none',light,1.3))
        x = -25 if view == 'front' else -18
        out += inked(path([(x-7,-37),(x+7,-37),(x+6,-21),(x,-18),(x-6,-21)]),dark,seam,1.3)
        out += inked(path([(x-8,-38),(x+8,-38),(x+6,-32),(x,-31),(x-6,-32)]),light,seam,1.2)
        out.append(el(ellipse(x,-33,1.2,1.2),c['brass']))
        out.append(el(path([(x+3,-38),(x+5,-49)],closed=False),'none',c['steel'],2.3))
    elif view.startswith('back'):
        left,right = (-31,31) if view=='back' else (-27,31)
        out.append(el(path([(left,-64),(left*.6,-53),(0,-50),(right*.6,-53),(right,-64)],closed=False),'none',seam,2.1))
        out.append(el(path([(left,-60),(left*.6,-49),(0,-46),(right*.6,-49),(right,-60)],closed=False),'none',light,1.0))
        out.append(el(path([(0,-49),(-1,-19),(1,15)],closed=False),'none',seam,1.5))
        # A sewn-on rectangular repair patch, kept in subdued canvas tones.
        out += inked(path([(-16,-30),(-3,-32),(-2,-17),(-14,-15)]),dark,seam,1.1)
        for y in (-28,-24,-20):
            out.append(el(path([(-15,y),(-13,y+1)],closed=False),'none',light,1.0))
    return out


# Open panels below the cinched belt. The original skirt geometry draws the
# whole near half of the loft; from the front that closes the opening. These
# contours show her work trousers through it, in the same hip-local parts.
MECHANIC_PANELS = {
    ('front', 'near'): [(-18,-24),(15,-24),(13,-8),(11,20),(8,48),(2,86,'c'),(-31,87,'c'),(-25,52),(-23,18)],
    ('front', 'far'): [(18,-24),(-15,-24),(-13,-8),(-11,20),(-8,48),(-2,86,'c'),(31,87,'c'),(25,52),(23,18)],
    ('front_3q', 'near'): [(-21,-25),(31,-24),(28,-4),(25,21),(19,52),(9,86,'c'),(-32,88,'c'),(-26,51),(-24,17)],
    ('front_3q', 'far'): [(-16,-23),(21,-25),(25,-10),(24,18),(28,49),(30,84,'c'),(13,86,'c'),(5,49),(4,18),(-6,-5)],
}


def mechanic_panel(c, view, side):
    pts = MECHANIC_PANELS[(view, side)]
    d = path(pts)
    col = '#ac8e62' if side == 'near' else '#967951'
    out = inked(d, col, c['ink'], W)
    if view == 'front':
        s = -1 if side == 'near' else 1
        out.append(el(path([(s*18,-20),(s*23,17),(s*25,52),(s*29,85),(s*23,85),(s*19,49),(s*18,14)]), '#8b704e'))
        out.append(el(path([(-s*13,-18),(-s*11,20),(-s*8,48),(-s*2,83)],closed=False),'none','#d4b88b',2.0))
    elif side == 'near':
        out.append(el(path([(-20,-20),(-24,18),(-26,51),(-30,85),(-22,85),(-20,47),(-19,15)]),'#8b704e'))
        out.append(el(path([(28,-17),(25,21),(19,52),(10,82)],closed=False),'none','#d4b88b',2.0))
    return out


def mechanic_gear(c, view, at):
    # Reuse the same belt and pouch construction. A larger open-ended wrench
    # is visible above the pouch even at gameplay scale.
    out = belt(c, view) + pouch(c, view, at)
    if not view.startswith('back'):
        x = POUCH_X[view] + at[0] + 11
        y = -24 + at[1] - 16
        jaw = path([(x-5,y+4),(x-7,y-6,'c'),(x-2,y-4),(x-1.8,y+0.5),
                    (x+1.8,y+0.5),(x+2,y-4),(x+7,y-6,'c'),(x+5,y+4),(x+2.6,y+7),(x-2.6,y+7)])
        out += inked(jaw,c['steel'],c['ink'],1.6)
        out.append(el(path([(x-5.4,y-4),(x-3.5,y+2)],closed=False),'none',c['steel_light'],1.4))
    return out


def mechanic_skirt(c, view, side):
    """A pocket and seam on the actual skirt part (hip-local coordinates)."""
    # The visible front half differs by camera view. In profile the near half
    # covers the far one; both use their own existing local hip attachment.
    if view.startswith('back'):
        x = 9 if side == 'near' else -9
    elif view == 'side':
        x = 5
    elif view == 'front_3q':
        x = -8 if side == 'near' else 10
    else:
        x = -8 if side == 'near' else 8
    seam, light, dark = '#67523d','#c6aa7d','#826b4e'
    out = mechanic_panel(c, view, side) if (view,side) in MECHANIC_PANELS else []
    if not (view == 'front_3q' and side == 'far'):
        out.append(el(path([(x,3),(x-1,42),(x+2,76)],closed=False),'none',seam,1.3))
    if not view.startswith('back') and not (view == 'front_3q' and side == 'far'):
        d = path([(x-10,12),(x+10,12),(x+9,32),(x+5,37),(x-5,37),(x-9,32)])
        out += inked(d,dark,seam,1.6)
        out += inked(path([(x-11,11),(x+11,11),(x+9,18),(x,20),(x-9,18)]),light,seam,1.4)
        out.append(el(ellipse(x,16,1.5,1.5),c['brass']))
        out.append(el(path([(x-7,22),(x-7,31),(x-4,34)],closed=False),'none',light,1.1))
    return out


# ---- the document -------------------------------------------------------------------------------------

def group(part, mode, anchor, scale, at, els, gear=False):
    g = f'  <g data-overlay-part="{part}" data-overlay-mode="{mode}" data-overlay-anchor="{anchor}" data-overlay-scale="{scale}"'
    if gear:
        g += ' data-overlay-gear="true"'
    g += f' transform="translate({at[0]:.2f},{at[1]:.2f})">'
    return "\n".join([g] + ["    " + e for e in els] + ["  </g>"])


def write(look: str) -> Path:
    c = LOOKS[look]
    data = yaml.safe_load((DATA / f"{look}.chargen.yaml").read_text())
    data.pop("overlay", None)
    spec = complete(data)
    fig, drawn = draw_views(spec)
    ref = " ".join(f"{k}:{MEASURES[k](fig):g}" for k in ("height", "head", "trunk", "leg"))
    cells = []
    for i, dv in enumerate(drawn):
        key = dv.view.key
        if dv.view.mirrored or key not in HEAD:
            continue
        cv = Canvas(UNIT, (i * CELL_W + CELL_W / 2.0, GROUND))
        J = {k: cv.xy(p) for k, p in dv.joints.items()}
        h = dict(HEAD[key])
        if c.get("void"):
            mark = {"side": ((31, -21), 0), "front_3q": ((14, -23), 0), "front": ((-18, -22), 0)}.get(key)
            h.update(ponytail={"side": flame_side, "front_3q": flame_f3q, "front": flame_front}.get(key, nothing),
                     face=(lambda c, m=mark: face_void(c, *m)) if mark else nothing)
            crown = h["hair"](c) + h["bandana"](c) + (h["streak"](c) if c.get("streaked") else [])
            tail = h["ponytail"](c)
        else:
            crown = mechanic_hair(c, key)
            tail = [] if key.startswith("back") else mechanic_ponytail(c, key)
        gs = [
            group("hair", "replace", "neck", "head head", J["neck"], crown),
            group("hair_back", "replace", "neck", "head head", J["neck"], tail),
            group("head", "over", "neck", "head head", J["neck"], h["face"](c)),
        ]
        # The pouch hangs from the belt, so it is drawn with it, over the coat.
        hip_at = tuple(J["near_hip"][k] - J["waist"][k] for k in range(2))
        if c.get("void"):
            coat_detail = belt(c, key) + pouch(c, key, hip_at)
        else:
            coat_detail = mechanic_coat(c, key) + mechanic_gear(c, key, hip_at)
        gs.append(group("torso__outer", "over", "waist", "trunk trunk", J["waist"], coat_detail))
        if not c.get("void"):
            gs += [group(f"{side}_skirt__outer", "replace" if (key,side) in MECHANIC_PANELS else "over", f"{side}_hip", "trunk trunk", J[f"{side}_hip"],
                         mechanic_skirt(c, key, side)) for side in ("near", "far")]
            # The generic thigh drape is an opaque backing, visible through
            # the new opening and as tan round caps at the knees. The coat's
            # actual panels supply its silhouette; leave the trousers intact.
            gs += [group(f"{side}_leg_u__outer_drape", "replace", f"{side}_hip", "trunk trunk", J[f"{side}_hip"], [])
                   for side in ("near", "far")]
        if c.get("void"):
            gs += [group(f"{side}_skirt__outer", "over", f"{side}_hip", "trunk trunk", J[f"{side}_hip"], tatters(c, key, side)) for side in ("near", "far")]
            gs.append(group("torso__top", "over", "waist", "trunk trunk", J["waist"], diamonds(c, key)))
        if c.get("touched"):
            gs.append(group("torso__top", "over", "waist", "trunk trunk", J["waist"], diamonds(c, key, (0, 3), 0.7)))
            for side in ("near", "far"):
                e = (J[f"{side}_elbow"][0] - J[f"{side}_wrist"][0], J[f"{side}_elbow"][1] - J[f"{side}_wrist"][1])
                gs.append(group(f"{side}_arm_l", "over", f"{side}_wrist", "trunk trunk", J[f"{side}_wrist"], creep(c, e, fig.arm_r)))
        for side in ("near", "far"):
            gs += [
                group(f"{side}_arm_l__outer", "replace", f"{side}_elbow", "trunk trunk", J[f"{side}_elbow"], []),
                group(f"{side}_arm_u__outer", "over", f"{side}_elbow", "trunk trunk", J[f"{side}_elbow"], coat_cuff(c, key)),
            ]
        cells.append(f'<g data-view="{key}">\n' + "\n".join(gs) + "\n</g>")
    w = CELL_W * len(VIEWS)
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}mm" height="{CELL_H:g}mm" '
           f'viewBox="0 0 {w:g} {CELL_H:g}" data-overlay-ref="{ref}">\n'
           f"<!-- GENERATED by scripts/draw_fia_overlays.py ({look}): edit the script and run it again, not this file.\n"
           "     Overlay art for Fia (chargen/overlay.py). Each group draws one rig part of one view, in SVG units\n"
           "     with its anchor joint at (0, 0); its transform only places it over the chargen SVG for an editor. -->\n"
           + "\n".join(cells) + "\n</svg>\n")
    out = OVERLAYS / f"{look}.overlay.svg"
    out.write_text(svg)
    return out


if __name__ == "__main__":
    for look in sys.argv[1:] or list(LOOKS):
        print(write(look))
