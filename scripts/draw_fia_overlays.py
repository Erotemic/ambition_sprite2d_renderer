"""Draw Fia's overlays: ``data/overlays/fia.overlay.svg`` (her own look) and
``fia_void.overlay.svg`` (embraced by the void), hand-placed art over the
generated parts of ``data/characters/fia/*.chargen.yaml`` (``chargen.overlay``;
the target is ``targets/characters/fia.py``).

The SVG files are generated: edit the shapes here and run it again::

    python scripts/draw_fia_overlays.py            # both looks
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


def ponytail_side(c):
    """A high, messy ponytail from the back of the crown, out and down in flicks."""
    tail = path([
        (-30, -64), (-42, -71), (-56, -70), (-66, -63, "c"), (-60, -59), (-68, -48, "c"), (-60, -46), (-64, -33, "c"),
        (-55, -36), (-53, -22, "c"), (-47, -32), (-41, -25, "c"), (-39, -37), (-33, -46),
    ])
    out = inked(tail, c["hair"], c["ink"], W)
    out.append(el(path([(-36, -62), (-52, -64), (-62, -56), (-56, -50), (-44, -52)]), c["hair_light"], opacity=0.6))
    for pts in (((-40, -60), (-56, -54), (-64, -40)), ((-38, -52), (-48, -40), (-52, -26))):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    return out


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
    tail = path([
        (-22, -74), (-38, -80), (-52, -76), (-60, -66, "c"), (-52, -64), (-60, -50, "c"), (-50, -50), (-54, -34, "c"),
        (-44, -40), (-40, -26, "c"), (-34, -40), (-26, -50),
    ])
    out = inked(tail, c["hair"], c["ink"], W)
    for pts in (((-30, -66), (-44, -60), (-50, -46)),):
        out.append(el(path(pts, closed=False), "none", c["hair_dark"], FINE))
    return out


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
    """Seen from the front, the high ponytail shows above and beside the crown."""
    tail = path([(8, -80), (18, -90), (30, -90), (40, -82, "c"), (34, -80), (42, -70, "c"), (32, -72), (24, -78)])
    return inked(tail, c["hair"], c["ink"], W)


def face_front(c):
    out = []
    for x, y in ((-6, -25), (-3, -23.5), (3, -23.5), (6, -25), (-9, -23), (9, -23), (0, -26)):
        out.append(el(ellipse(x, y, 0.8, 0.7), c["freckle"]))
    out += inked(rect(-18, -21, 9, 3.9, 14), c["plaster"], c["ink"], 1.1)
    for dx in (-2, 0, 2):
        out.append(el(ellipse(-18 + dx * 0.97, -21 + dx * 0.24, 0.42, 0.42), c["plaster_dot"]))
    return out


def _back_tail(c, cx, lean):
    """The ponytail from behind, over the back of her head: gathered at the knot
    (cx, -62), out and down in flicks; lean turns it toward +x."""
    pts = [(cx - 8, -66), (cx - 22 + lean, -60), (cx - 30 + lean, -48, "c"), (cx - 22 + lean, -46), (cx - 26 + lean, -32, "c"),
           (cx - 15 + lean, -36), (cx - 12 + lean, -18, "c"), (cx - 4 + lean, -30), (cx + 4 + lean, -16, "c"), (cx + 8 + lean, -32),
           (cx + 18 + lean, -24, "c"), (cx + 16 + lean, -40), (cx + 26 + lean, -42, "c"), (cx + 16 + lean, -54), (cx + 8, -66)]
    out = inked(path(pts), c["hair"], c["ink"], W)
    out.append(el(path([(cx - 6, -60), (cx - 14 + lean, -50), (cx - 6 + lean, -40), (cx + 4 + lean, -46), (cx + 6, -58)]), c["hair_light"], opacity=0.55))
    for pts2 in (((cx - 4, -58), (cx - 10 + lean, -44), (cx - 10 + lean, -30)), ((cx + 4, -58), (cx + 6 + lean, -44), (cx + 10 + lean, -30))):
        out.append(el(path(pts2, closed=False), "none", c["hair_dark"], FINE))
    # the knot, and its tails over the hair
    for d in (path([(cx - 3, -64), (cx - 14, -70), (cx - 22, -66, "c"), (cx - 15, -63), (cx - 5, -61)]),
              path([(cx + 3, -64), (cx + 12, -58), (cx + 16, -48, "c"), (cx + 10, -54), (cx + 2, -60)])):
        out += inked(d, c["band"], c["ink"], W * 0.7)
    out += inked(ellipse(cx, -64, 5, 4.2), c["band_dark"], c["ink"], W * 0.7)
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

LOOKS["fia_void"] = dict(
    LOOKS["fia"], void=True, ink="#050506", hair="#f2f2f2", hair_dark="#9a9a9e", hair_light="#ffffff", streak="#0b0b0c",
    streak_shade="#3a3a3e", cuff="#0b0b0c", cuff_dark="#3a3a3e", leather="#0b0b0c", leather_dark="#000000", leather_light="#26262a",
    brass="#f4f4f4", steel="#e6e6e8", steel_dark="#8a8a8e", steel_light="#ffffff", wrap="#0b0b0c", glow="#ffffff", band="#0b0b0c",
    band_dark="#000000", band_light="#3a3a3e", white="#f6f6f6",
)
#: The void's outline on its black pieces: white, as the family's ink.
VOID_INK = "#f4f4f4"


def _vinked(d, fill, c, w):
    """A black void piece: a white outline outside it."""
    return inked(d, fill, VOID_INK if c.get("void") else c["ink"], w)


def flame_side(c):
    """Her ponytail loosed by the void: white locks rising up and back like flame."""
    pts = [(-30, -64), (-42, -80), (-52, -100, "c"), (-52, -84), (-68, -96, "c"), (-64, -78), (-84, -78, "c"), (-70, -66),
           (-86, -56, "c"), (-68, -52), (-78, -38, "c"), (-60, -42), (-60, -26, "c"), (-48, -38), (-42, -26, "c"), (-38, -40), (-33, -46)]
    out = inked(path(pts), c["hair"], c["ink"], W)
    for q in (((-38, -60), (-56, -72), (-70, -74)), ((-38, -52), (-58, -54), (-72, -50)), ((-40, -46), (-52, -40), (-56, -32))):
        out.append(el(path(q, closed=False), "none", c["hair_dark"], FINE))
    return out


def flame_f3q(c):
    pts = [(-22, -74), (-30, -90), (-34, -106, "c"), (-24, -94), (-14, -104, "c"), (-12, -88), (-40, -84), (-56, -92, "c"),
           (-50, -76), (-66, -68, "c"), (-52, -62), (-62, -46, "c"), (-48, -50), (-50, -32, "c"), (-38, -42), (-28, -52)]
    out = inked(path(pts), c["hair"], c["ink"], W)
    out.append(el(path(((-30, -70), (-46, -72), (-56, -66)), closed=False), "none", c["hair_dark"], FINE))
    return out


def flame_front(c):
    pts = [(-26, -74), (-34, -96, "c"), (-20, -86), (-12, -106, "c"), (-2, -88), (10, -108, "c"), (16, -88), (30, -100, "c"),
           (30, -82), (44, -88, "c"), (36, -72)]
    return inked(path(pts), c["hair"], c["ink"], W)


def _back_flame(c, cx, lean):
    pts = [(cx - 10, -64), (cx - 22 + lean, -76), (cx - 30 + lean, -98, "c"), (cx - 16 + lean, -84), (cx - 8 + lean, -104, "c"),
           (cx + 2 + lean, -86), (cx + 14 + lean, -102, "c"), (cx + 14 + lean, -82), (cx + 30 + lean, -90, "c"), (cx + 20 + lean, -72),
           (cx + 10, -62)]
    out = inked(path(pts), c["hair"], c["ink"], W)
    out.append(el(path(((cx - 4, -66), (cx - 8 + lean, -82), (cx - 10 + lean, -94)), closed=False), "none", c["hair_dark"], FINE))
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


def diamonds(c, view):
    """White diamonds that drift about her (anchored at the waist)."""
    spots = {"side": ((-52, -50, 5.5), (56, -78, 4.0), (-62, 30, 3.2), (60, 20, 4.6)),
             "front_3q": ((-58, -62, 5.0), (66, -70, 4.2), (-64, 24, 3.4), (70, 30, 4.4)),
             "front": ((-66, -60, 5.0), (66, -72, 4.4), (-70, 26, 3.4), (70, 18, 4.2)),
             "back_3q": ((-60, -70, 4.4), (66, -58, 5.0), (-66, 30, 4.2), (70, 22, 3.4)),
             "back": ((-66, -70, 4.4), (66, -60, 5.0), (-70, 20, 4.2), (70, 28, 3.4))}[view]
    out = []
    for x, y, r in spots:
        d = path([(x, y - r * 1.7, "c"), (x + r, y, "c"), (x, y + r * 1.7, "c"), (x - r, y, "c")])
        out += inked(d, c["white"], c["ink"], 1.4)
        out.append(el(path([(x, y - r * 1.1, "c"), (x + r * 0.35, y, "c"), (x, y + r * 1.1, "c"), (x - r * 0.35, y, "c")]), "#cfcfd3"))
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
        gs = [
            group("hair", "replace", "neck", "head head", J["neck"], h["hair"](c) + h["bandana"](c) + h["streak"](c)),
            group("hair_back", "replace", "neck", "head head", J["neck"], h["ponytail"](c)),
            group("head", "over", "neck", "head head", J["neck"], h["face"](c)),
        ]
        gs += [
            # The pouch hangs from the belt, so it is drawn with it, over the coat.
            group("torso__outer", "over", "waist", "trunk trunk", J["waist"],
                  belt(c, key) + pouch(c, key, (J["near_hip"][0] - J["waist"][0], J["near_hip"][1] - J["waist"][1]))),
        ]
        if c.get("void"):
            gs += [group(f"{side}_skirt__outer", "over", f"{side}_hip", "trunk trunk", J[f"{side}_hip"], tatters(c, key, side)) for side in ("near", "far")]
            gs.append(group("torso__top", "over", "waist", "trunk trunk", J["waist"], diamonds(c, key)))
        for side in ("near", "far"):
            gs += [
                group(f"{side}_arm_l__outer", "replace", f"{side}_elbow", "trunk trunk", J[f"{side}_elbow"], []),
                group(f"{side}_arm_u__outer", "over", f"{side}_elbow", "trunk trunk", J[f"{side}_elbow"], coat_cuff(c, key)),
                group(f"{side}_arm_l", "over", f"{side}_wrist", "trunk trunk", J[f"{side}_wrist"], wrist_cuff(c, key)),
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
