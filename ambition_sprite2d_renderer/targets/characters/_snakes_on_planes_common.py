"""Shared procedural art for the two Snakes on a Plane enemy variants."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

FRAME_SIZE = (160, 128)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 145),
    ("fly", 8, 92),
    ("bank", 6, 105),
    ("hiss", 6, 108),
    ("hurt", 4, 96),
    ("death", 7, 118),
]

TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (24, 21, 19, 255)
SNAKE_GREEN = (91, 148, 82, 255)
SNAKE_LIGHT = (139, 188, 115, 255)
SNAKE_DARK = (56, 102, 54, 255)
SNAKE_BELLY = (225, 213, 151, 255)
SNAKE_EYE = (28, 25, 22, 255)
TONGUE = (207, 72, 98, 255)
PAPER = (239, 240, 226, 255)
PAPER_LIGHT = (255, 255, 247, 255)
PAPER_SHADE = (183, 197, 205, 255)
PAPER_FOLD = (120, 143, 153, 255)
GRID_BG = (239, 231, 201, 255)
GRID_LINE = (137, 166, 169, 255)
GRID_MAJOR = (80, 113, 118, 255)
AXIS = (46, 52, 56, 255)
AXIS_X = (183, 72, 66, 255)
AXIS_Y = (62, 103, 170, 255)


@dataclass(frozen=True)
class PlaneSpec:
    target_name: str
    display_name: str
    character_id: str
    kind: str
    traits: Tuple[str, ...]
    barks: Tuple[str, ...]


PAPER_SPEC = PlaneSpec(
    target_name="snakes_on_a_paper_plane",
    display_name="Snakes on a Paper Plane",
    character_id="npc_snakes_on_a_paper_plane",
    kind="paper",
    traits=("enemy", "flying", "snake_swarm", "paper_airplane", "plane_pun"),
    barks=(
        "This flight is hiss-class only.",
        "Please keep your scales inside the aircraft.",
        "We folded under pressure.",
    ),
)

CARTESIAN_SPEC = PlaneSpec(
    target_name="snakes_on_a_cartesian_plane",
    display_name="Snakes on a Cartesian Plane",
    character_id="npc_snakes_on_a_cartesian_plane",
    kind="cartesian",
    traits=("enemy", "flying", "snake_swarm", "cartesian_plane", "math_pun"),
    barks=(
        "We have coordinates for your location.",
        "Stay on the positive side.",
        "Our domain is all real snakes.",
    ),
)


def actor_metadata(spec: PlaneSpec) -> dict:
    if spec.kind == "cartesian":
        authoring_description = (
            "Snakes on a Cartesian Plane parodies the title Snakes on a Plane by "
            "putting a snake swarm on a literal coordinate grid. The joke should read "
            "both as airborne action-movie nonsense and as a mathematics pun about "
            "domains, axes, quadrants, and coordinates."
        )
        gameplay_description = (
            "Use as a flying swarm enemy whose motion, attacks, or weaknesses are tied "
            "to coordinates and quadrants. It can announce the player's location, cross "
            "axes, and weaponize positive and negative space."
        )
    else:
        authoring_description = (
            "Snakes on a Paper Plane parodies the title Snakes on a Plane at the most "
            "literal possible scale: several snakes have folded themselves onto a paper "
            "airplane. The fragile craft and overconfident passengers are the visual joke."
        )
        gameplay_description = (
            "Use as a light flying swarm enemy that banks, folds, crumples, and hisses. "
            "Its paper aircraft should make it agile but vulnerable to fire, water, or "
            "violent changes in direction."
        )
    return {
        "authoring_description": authoring_description,
        "gameplay_description": gameplay_description,
        "actor": {
            "character_id": spec.character_id,
            "display_name": spec.display_name,
        },
        "body": {
            "body_plan": "FlyingSwarm",
            "body_kind": "Wide",
            "mass_class": "Light",
            "locomotion_hint": "Hover",
            "traits": list(spec.traits),
        },
        "capabilities": {
            "traversal": {
                "walk": None,
                "jump": None,
                "climb": None,
                "fly": True,
                "swim": None,
                "crawl": None,
                "use_lifts": None,
                "door_access": [],
            },
            "interactions": {
                "talk": None,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": {"default_preset": "flying_patrol"},
        "actions": {"default_preset": "flying_contact"},
        "visual": {
            "default_pose": "idle",
            "portrait": {"animation": "idle", "frame": 2},
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.fly": {"animation": "fly", "events": []},
            "locomotion.bank": {"animation": "bank", "events": []},
            "action.taunt": {"animation": "hiss", "events": []},
            "damage.hit": {"animation": "hurt", "events": []},
            "lifecycle.death": {"animation": "death", "events": []},
        },
        "sockets": {
            "center": {
                "source": f"{spec.target_name}.geometry",
                "point": {"x": 80.0, "y": 65.0},
            },
            "projectile_origin": {
                "source": f"{spec.target_name}.geometry",
                "point": {"x": 135.0, "y": 50.0},
            },
        },
        "tags": list(spec.traits),
        "dialogue_hints": {"barks": list(spec.barks)},
    }


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _bbox(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(
            pts + [pts[0]],
            fill=outline,
            width=max(1, _s(width)),
            joint="curve",
        )


def _line(
    draw: ImageDraw.ImageDraw,
    points: Iterable[Point],
    fill: RGBA,
    width: float,
) -> None:
    draw.line(
        [_pt(point) for point in points],
        fill=fill,
        width=max(1, _s(width)),
        joint="curve",
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    radius: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _bbox(center[0], center[1], radius, radius),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline else 0,
    )


def _transform(point: Point, center: Point, angle: float, offset: Point) -> Point:
    x = point[0] - center[0]
    y = point[1] - center[1]
    c = math.cos(angle)
    s = math.sin(angle)
    return (
        center[0] + x * c - y * s + offset[0],
        center[1] + x * s + y * c + offset[1],
    )


def _transform_points(
    points: Sequence[Point], center: Point, angle: float, offset: Point
) -> List[Point]:
    return [_transform(point, center, angle, offset) for point in points]


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 0.8,
) -> None:
    draw.ellipse(
        _bbox(center[0], center[1], rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline else 0,
    )


def _outline(draw: ImageDraw.ImageDraw, points: Sequence[Point], width: float) -> None:
    _line(draw, list(points) + [points[0]], OUTLINE, width)


def _lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _quad_at(quad: Sequence[Point], u: float, v: float) -> Point:
    """A point of quad ``(root_aft, root_fore, tip_fore, tip_aft)``: ``u``
    runs aft to fore along the chord, ``v`` root to tip along the span."""
    return _lerp(_lerp(quad[0], quad[1], u), _lerp(quad[3], quad[2], u), v)


def _smooth(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


# ---- The snakes ----------------------------------------------------------------
#
# Each snake sits up on the deck like a cobra in a seat: its tail curled
# back along the deck, its body rising in a question mark, its big head
# level and facing the way the plane flies. The body is a shaded tube (a
# lit back, a shaded flank, a cream belly on the side it faces with) and
# the head carries the face: a bulging eye with a slit pupil under a heavy
# brow, a nostril, and a mouth that smirks, hisses (fangs and a forked
# tongue) or grimaces.


@dataclass(frozen=True)
class Scales:
    base: RGBA
    light: RGBA
    dark: RGBA
    pattern: RGBA


OLIVE_SCALES = Scales((132, 152, 64, 255), (182, 198, 104, 255), (88, 106, 42, 255), (64, 78, 30, 255))
GREEN_SCALES = Scales(SNAKE_GREEN, SNAKE_LIGHT, SNAKE_DARK, (40, 78, 42, 255))
TEAL_SCALES = Scales((56, 138, 118, 255), (110, 190, 164, 255), (32, 94, 82, 255), (24, 70, 62, 255))
BELLY_SHADE = (186, 168, 106, 255)
EYE_WHITE = (252, 248, 228, 255)
MOUTH = (118, 30, 46, 255)
FANG = (255, 252, 240, 255)
BRASS = (196, 152, 66, 255)
LENS = (156, 212, 230, 255)
STRAP = (104, 64, 40, 255)

#: The resting rise of a seated snake, tail tip to neck, about its seat on
#: the deck (frame pixels; scaled per plane).
SEAT_SHAPE: Tuple[Point, ...] = (
    (-15.0, -3.0), (-13.0, 0.0), (-8.0, 1.6), (-2.0, 1.4), (2.6, -1.8),
    (4.0, -7.5), (1.8, -13.0), (0.8, -17.0), (2.8, -20.4), (7.0, -21.8),
)
SNAKE_POINTS = 13
SNAKE_BONES = 4


@dataclass(frozen=True)
class Rider:
    """One snake: where it sits, how tall it rises, its scales, its face."""

    seat: Point
    rise: float
    scales: Scales
    mood: str  # resting face: "smug", "alert" or "angry"
    phase: float
    accessory: str = ""


def _catmull(points: Sequence[Point], samples: int) -> List[Point]:
    """``samples`` points evenly spaced along a Catmull-Rom curve through
    ``points``."""
    dense: List[Point] = []
    pts = [points[0]] + list(points) + [points[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(16):
            t = k / 16.0
            t2, t3 = t * t, t * t * t
            dense.append(tuple(
                0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in range(2)
            ))
    dense.append(points[-1])
    lengths = [0.0]
    for a, b in zip(dense, dense[1:]):
        lengths.append(lengths[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out: List[Point] = []
    j = 0
    for i in range(samples):
        target = lengths[-1] * i / (samples - 1)
        while j < len(lengths) - 2 and lengths[j + 1] < target:
            j += 1
        span = max(1e-6, lengths[j + 1] - lengths[j])
        out.append(_lerp(dense[j], dense[j + 1], (target - lengths[j]) / span))
    return out


def _rest_curve(rider: Rider) -> List[Point]:
    sx, sy = rider.seat
    return _catmull([(sx + x * rider.rise, sy + y * rider.rise) for x, y in SEAT_SHAPE], SNAKE_POINTS)


def _width(t: float) -> float:
    return 1.5 + 4.9 * _smooth(0.0, 0.38, t) - 0.9 * _smooth(0.72, 1.0, t)


def _normal(points: Sequence[Point], idx: int) -> Point:
    """The belly side at ``idx`` (to the right of the tail-to-head way)."""
    a = points[max(0, idx - 1)]
    b = points[min(len(points) - 1, idx + 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = max(1e-6, math.hypot(dx, dy))
    return (-dy / n, dx / n)


def _paint_snake_bone(draw, rest: Sequence[Point], k: int, scales: Scales, layer: str) -> None:
    """Bone ``k`` of a resting snake, its first point at ``HOME``: its
    outline (``layer == "ink"``) or its shaded body over it (``"body"``).
    Every bone's ink is laid before any bone's body, so the joints close."""
    per = (len(rest) - 1) // SNAKE_BONES
    first = per * k
    ox, oy = HOME[0] - rest[first][0], HOME[1] - rest[first][1]
    pts = [(x + ox, y + oy) for x, y in rest]
    last = len(pts) - 1
    # One segment past its own: turned apart, the next bone leaves a gap at
    # their joint that this segment fills under it.
    idxs = range(first, min(first + per + 1, last) + 1)
    widths = {i: _width(i / last) for i in idxs}
    if layer == "ink":
        for i in idxs:
            _circle(draw, pts[i], widths[i] / 2 + 1.0, OUTLINE, None)
            if i + 1 in widths:
                _line(draw, [pts[i], pts[i + 1]], OUTLINE, (widths[i] + widths[i + 1]) / 2 + 2.0)
        return

    def stroke(color: RGBA, side: float, frac: float) -> None:
        for i in idxs:
            n = _normal(pts, i)
            w = widths[i]
            c = (pts[i][0] + n[0] * side * w, pts[i][1] + n[1] * side * w)
            _circle(draw, c, w * frac / 2, color, None)
            if i + 1 in widths:
                n2 = _normal(pts, i + 1)
                w2 = widths[i + 1]
                c2 = (pts[i + 1][0] + n2[0] * side * w2, pts[i + 1][1] + n2[1] * side * w2)
                _line(draw, [c, c2], color, (w + w2) / 2 * frac)

    stroke(scales.base, 0.0, 1.0)
    stroke(scales.dark, 0.22, 0.56)  # the flank turned from the light
    stroke(SNAKE_BELLY, 0.3, 0.3)  # the belly scales on the side it faces with
    stroke(scales.light, -0.24, 0.22)  # the lit back
    # A diamond of darker scales down the back every few points.
    for i in idxs:
        if i % 2 == 1 and 1 < i < last - 1 and i < first + per + (1 if k == SNAKE_BONES - 1 else 0):
            n = _normal(pts, i)
            w = widths[i]
            c = (pts[i][0] - n[0] * w * 0.06, pts[i][1] - n[1] * w * 0.06)
            tx, ty = n[1], -n[0]
            r = w * 0.26
            _poly(draw, [(c[0] + tx * r * 1.4, c[1] + ty * r * 1.4), (c[0] - n[0] * r, c[1] - n[1] * r),
                         (c[0] - tx * r * 1.4, c[1] - ty * r * 1.4), (c[0] + n[0] * r, c[1] + n[1] * r)],
                  scales.pattern, None)


def _rot(p: Point, pivot: Point, angle: float) -> Point:
    c, s = math.cos(angle), math.sin(angle)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * c - y * s, pivot[1] + x * s + y * c)


# The head, facing +x with its neck at the origin (frame pixels).
_CROWN = [(-1.4, -3.0), (0.6, -4.5), (4.0, -5.4), (7.6, -5.0), (10.8, -3.5),
          (13.4, -1.7), (14.6, 0.0), (13.9, 0.9), (4.0, 1.1), (-1.4, 1.6)]
_JAW = [(-1.4, 1.6), (4.0, 1.1), (13.9, 0.9), (12.6, 2.1), (8.6, 3.1), (3.0, 3.7), (-1.4, 3.5)]
#: The head is drawn this much bigger than its frame-pixel outline: a big
#: head keeps the face readable at game scale.
HEAD_SCALE = 1.15
_HINGE = (2.4, 1.2)
_EYE = (6.2, -3.6)


def _paint_snake_head(draw, scales: Scales, face: str, gape: float, tongue: float, accessory: str) -> None:
    """A snake's head facing +x, its neck at ``HOME``. ``face``: smug,
    alert, angry, squeeze or dead; ``gape`` opens the jaw (radians);
    ``tongue`` flicks a forked tongue that far past the snout."""
    hx, hy = HOME
    up = -gape * 0.4
    down = gape * 0.6

    k = HEAD_SCALE

    def crown(p: Point) -> Point:
        q = _rot(p, _HINGE, up)
        return (hx + q[0] * k, hy + q[1] * k)

    def jaw(p: Point) -> Point:
        q = _rot(p, _HINGE, down)
        return (hx + q[0] * k, hy + q[1] * k)

    if gape > 0.0:
        _poly(draw, [crown(_HINGE), crown((13.9, 0.9)), jaw((13.9, 0.9)), jaw((4.0, 1.6))], MOUTH, OUTLINE, 0.7)
    if tongue > 0.0:
        root = crown((11.0, 1.2)) if gape <= 0.0 else _lerp(crown((10.0, 1.2)), jaw((10.0, 1.2)), 0.5)
        sag = 1.4 if face == "dead" else 0.0
        tip = (hx + 14.6 * k + tongue, hy + 1.0 + sag + (0.0 if gape <= 0.0 else 0.3))
        _line(draw, [root, tip], TONGUE, 0.95)
        _line(draw, [tip, (tip[0] + 2.0, tip[1] - 1.3 + sag)], TONGUE, 0.6)
        _line(draw, [tip, (tip[0] + 2.0, tip[1] + 1.3 + sag)], TONGUE, 0.6)
    if gape > 0.0:
        for x0 in (11.2, 8.2):
            _poly(draw, [crown((x0, 1.0)), crown((x0 + 1.3, 1.0)), crown((x0 + 0.5, 3.3))], FANG, OUTLINE, 0.4)

    # The jaw: cream underside, shaded where it turns away.
    _poly(draw, [jaw(p) for p in _JAW], SNAKE_BELLY, OUTLINE, 0.9)
    _line(draw, [jaw((0.0, 3.0)), jaw((4.0, 3.1)), jaw((8.4, 2.5)), jaw((11.6, 1.8))], BELLY_SHADE, 0.8)

    # The crown: its form shade under a lit top.
    _poly(draw, [crown(p) for p in _CROWN], scales.base, OUTLINE, 0.9)
    _poly(draw, [crown(p) for p in [(-1.0, -0.6), (5.0, -0.9), (10.6, -1.2), (13.9, 0.4), (13.6, 0.9),
                                    (4.0, 1.0), (-1.2, 1.4)]], scales.dark, None)
    _poly(draw, [crown(p) for p in [(1.2, -4.0), (4.2, -4.8), (7.6, -4.5), (10.6, -3.0), (7.0, -3.4),
                                    (2.6, -3.2)]], scales.light, None)
    _circle(draw, crown((12.6, -1.2)), 0.5, OUTLINE, None)  # nostril

    if gape <= 0.0:
        if face in ("squeeze", "dead"):
            mouth = [(13.8, 0.9), (9.6, 1.3), (6.4, 1.8), (4.4, 1.3)]  # a grimace
        else:
            mouth = [(13.8, 0.9), (9.2, 1.2), (5.4, 0.9), (3.8, -0.3)]  # the smirk
        _line(draw, [crown(p) for p in mouth], OUTLINE, 0.65)

    # The eye: big, bulging over the crown, a slit pupil looking ahead.
    ex, ey = _EYE
    if face == "dead":
        for a, b in (((-1.6, -1.6), (1.6, 1.6)), ((-1.6, 1.6), (1.6, -1.6))):
            _line(draw, [crown((ex + a[0], ey + a[1])), crown((ex + b[0], ey + b[1]))], OUTLINE, 0.75)
    elif face == "squeeze":
        _line(draw, [crown((ex - 1.4, ey - 1.8)), crown((ex + 1.2, ey)), crown((ex - 1.4, ey + 1.6))], OUTLINE, 0.75)
        _line(draw, [crown((ex - 2.0, ey - 3.2)), crown((ex + 1.6, ey - 2.2))], OUTLINE, 0.7)
    else:
        centre = crown((ex, ey))
        _ellipse(draw, centre, 2.5, 2.7, EYE_WHITE, OUTLINE, 0.7)
        _ellipse(draw, crown((ex + 0.8, ey + 0.2)), 0.75, 1.9, SNAKE_EYE, None)
        _circle(draw, crown((ex - 0.6, ey - 1.0)), 0.5, EYE_WHITE, None)
        # The lid tells the mood: drawn half down (smug: the pilot has seen
        # it all), slanted down to the snout (angry), or up off a wide eye
        # (alert), its edge a heavy brow.
        if face == "smug":
            lid = [(ex - 2.9, ey - 0.5), (ex + 2.9, ey - 0.3)]
        elif face == "angry":
            lid = [(ex - 2.9, ey - 2.2), (ex + 2.9, ey - 0.2)]
        else:
            lid = [(ex - 2.7, ey - 2.4), (ex + 2.7, ey - 2.5)]
        # The lid is the eye's own top, cut off along the lid line.
        (x0, y0), (x1, y1) = lid
        rim = []
        for i in range(41):
            th = math.pi + math.pi * i / 40
            x, y = ex + 2.85 * math.cos(th), ey + 3.05 * math.sin(th)
            line_y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            rim.append((x, min(y, line_y)))
        _poly(draw, [crown(p) for p in rim], scales.base, None)
        _line(draw, [crown(p) for p in rim if p[1] < y0 + (y1 - y0) * (p[0] - x0) / (x1 - x0) - 0.05], OUTLINE, 0.6)
        _line(draw, [crown((x0 - 0.3, y0 - 0.1)), crown((x1 + 0.3, y1))], OUTLINE, 1.0)

    if accessory == "goggles":
        # Pilot's goggles pushed up on the crown, their strap round the back.
        _line(draw, [crown((-0.6, -2.0)), crown((1.6, -5.4)), crown((4.0, -6.6))], STRAP, 1.3)
        for cx in (4.4, 8.0):
            _circle(draw, crown((cx, -6.4)), 1.75, LENS, BRASS, 0.6)
            _circle(draw, crown((cx - 0.5, -6.9)), 0.45, EYE_WHITE, None)
        _line(draw, [crown((6.1, -6.5)), crown((6.3, -6.5))], BRASS, 0.6)
    elif accessory == "spectacles" and face not in ("dead", "squeeze"):
        # Round spectacles: the mathematician.
        _circle(draw, crown((ex + 0.2, ey + 0.1)), 3.3, None, OUTLINE, 0.6)
        _line(draw, [crown((ex - 3.1, ey - 0.6)), crown((-0.6, -2.4))], OUTLINE, 0.55)
        _line(draw, [crown((ex + 1.2, ey - 2.4)), crown((ex + 2.3, ey - 1.4))], EYE_WHITE, 0.45)


# ---- The planes ----------------------------------------------------------------
#
# Each painter draws its plane level, in frame pixels about ``center``,
# moved by ``offset`` (the piece canvas puts ``center`` at ``HOME``).

PAPER_EDGE = (92, 106, 116, 255)
PAPER_KEEL = (206, 214, 214, 255)
RULE = (170, 196, 222, 255)
MARGIN = (226, 150, 160, 255)
GRID_FAR = (220, 210, 178, 255)
GRID_LINE_FAR = (150, 166, 160, 255)
AXIS_X_LIGHT = (226, 120, 108, 255)
AXIS_X_DARK = (128, 44, 42, 255)
AXIS_Y_LIGHT = (122, 160, 220, 255)
AXIS_Y_DARK = (38, 66, 120, 255)
PLOT = (124, 60, 168, 255)


def _draw_paper_plane(draw: ImageDraw.ImageDraw, center: Point, angle: float, offset: Point) -> None:
    """A folded dart seen from above its near wing: the far wing a shaded
    sliver over the spine, the keel's fold under the near wing, and the near
    wing in two lit facets split by the crease of its folded leading edge."""
    T = lambda pts: _transform_points(pts, center, angle, offset)
    nose, tail = (152.0, 61.0), (24.0, 63.0)
    far_tip, near_tip, keel = (40.0, 50.0), (34.0, 85.0), (50.0, 97.0)
    crease_aft = _lerp(tail, near_tip, 0.46)
    _poly(draw, T([nose, tail, far_tip]), PAPER_SHADE, OUTLINE, 1.0)
    _line(draw, T([_lerp(nose, far_tip, 0.06), _lerp(tail, far_tip, 0.35)]), PAPER_FOLD, 0.6)
    _poly(draw, T([nose, tail, keel]), PAPER_KEEL, OUTLINE, 1.0)
    _line(draw, T([_lerp(nose, keel, 0.05), _lerp(tail, keel, 0.55)]), PAPER_SHADE, 0.8)
    # The near wing: its inner facet faces the light, the outer one turns away.
    _poly(draw, T([nose, tail, crease_aft]), PAPER_LIGHT, None)
    _poly(draw, T([nose, crease_aft, near_tip]), PAPER, None)
    # Notebook paper: faint rules along the wing and its red margin.
    for f in (0.2, 0.42, 0.64, 0.86):
        _line(draw, T([_lerp(tail, near_tip, f), _lerp(nose, near_tip, f * 0.98)]), RULE, 0.45)
    _line(draw, T([_lerp(tail, nose, 0.12), _lerp(near_tip, nose, 0.1)]), MARGIN, 0.5)
    # The crease: a dark valley with a lit ridge along it.
    _line(draw, T([nose, crease_aft]), PAPER_FOLD, 0.8)
    _line(draw, T([_lerp(nose, crease_aft, 0.02), _lerp(crease_aft, near_tip, 0.08)]), PAPER_LIGHT, 0.5)
    _outline(draw, T([nose, tail, near_tip]), 1.05)
    _line(draw, T([nose, tail]), PAPER_EDGE, 0.75)  # the spine fold
    # The folded-down wingtip.
    _poly(draw, T([near_tip, _lerp(near_tip, nose, 0.09), (near_tip[0] + 8.0, near_tip[1] + 4.0)]),
          PAPER_SHADE, OUTLINE, 0.8)


def _draw_grid_wing(draw, quad: Sequence[Point], T, paper: RGBA, line: RGBA, major: RGBA,
                    cols: int, rows: int, plot: bool) -> None:
    _poly(draw, T(list(quad)), paper, None)
    for i in range(1, cols):
        u = i / cols
        _line(draw, T([_quad_at(quad, u, 0.0), _quad_at(quad, u, 1.0)]), major if i % 3 == 0 else line, 0.42)
    for j in range(1, rows):
        v = j / rows
        _line(draw, T([_quad_at(quad, 0.0, v), _quad_at(quad, 1.0, v)]), major if j % 3 == 0 else line, 0.42)
    if plot:
        # A plotted curve, its samples marked: y = sin x across the wing.
        curve = [_quad_at(quad, 0.04 + 0.92 * k / 24, 0.52 - 0.34 * math.sin(math.tau * k / 24 * 1.15)) for k in range(25)]
        _line(draw, T(curve), PLOT, 0.95)
        for k in (2, 8, 14, 20):
            _circle(draw, T([curve[k]])[0], 0.95, PLOT, OUTLINE, 0.35)
    _outline(draw, T(list(quad)), 1.0)


def _arrow(draw, T, tip: Point, back: float, half: float, along: Point, fill: RGBA, dark: RGBA) -> None:
    ax, ay = along
    base = (tip[0] - ax * back, tip[1] - ay * back)
    left = (base[0] - ay * half, base[1] + ax * half)
    right = (base[0] + ay * half, base[1] - ax * half)
    notch = (tip[0] - ax * back * 0.72, tip[1] - ay * back * 0.72)
    _poly(draw, T([tip, left, notch, right]), fill, OUTLINE, 0.9)
    _poly(draw, T([tip, notch, right]), dark, None)


def _draw_cartesian_plane(draw: ImageDraw.ImageDraw, center: Point, angle: float, offset: Point) -> None:
    """An aircraft built of the coordinate plane: the x-axis its fuselage
    (the arrow its nose), the y-axis its tail fin, graph paper its wings,
    and a curve plotted on the near wing."""
    T = lambda pts: _transform_points(pts, center, angle, offset)
    origin = (32.0, 70.0)
    # The far wing, behind the fuselage, turned from the light.
    far = [(76.0, 68.0), (114.0, 68.0), (94.0, 52.0), (68.0, 52.0)]
    _draw_grid_wing(draw, far, T, GRID_FAR, GRID_LINE_FAR, GRID_MAJOR, 6, 4, False)
    # The tail fin: quadrant-II graph paper swept back to the y-axis.
    fin = [(32.0, 68.0), (54.0, 68.0), (35.0, 52.0), (32.0, 52.0)]
    _draw_grid_wing(draw, fin, T, GRID_BG, GRID_LINE, GRID_MAJOR, 3, 3, False)
    # The y-axis: up through the fin, down to a tail skid, arrows both ends.
    _line(draw, T([(32.0, 80.0), (32.0, 49.0)]), OUTLINE, 3.6)
    _line(draw, T([(32.0, 80.0), (32.0, 49.0)]), AXIS_Y, 2.0)
    _line(draw, T([(31.5, 79.0), (31.5, 50.0)]), AXIS_Y_LIGHT, 0.6)
    _arrow(draw, T, (32.0, 44.0), 7.0, 3.6, (0.0, -1.0), AXIS_Y, AXIS_Y_DARK)
    _arrow(draw, T, (32.0, 85.0), 5.5, 3.0, (0.0, 1.0), AXIS_Y, AXIS_Y_DARK)
    for y in (56.0, 62.0, 76.0):
        _line(draw, T([(29.0, y), (35.0, y)]), OUTLINE, 0.7)
    # The x-axis fuselage: a lit top and a shaded belly on a red rod.
    _line(draw, T([(22.0, 70.0), (140.0, 70.0)]), OUTLINE, 6.4)
    _line(draw, T([(22.0, 70.0), (140.0, 70.0)]), AXIS_X, 4.4)
    _line(draw, T([(22.0, 71.4), (140.0, 71.4)]), AXIS_X_DARK, 1.5)
    _line(draw, T([(22.0, 68.7), (140.0, 68.7)]), AXIS_X_LIGHT, 1.1)
    for x in range(44, 136, 10):
        _line(draw, T([(float(x), 65.6), (float(x), 74.4)]), OUTLINE, 0.75)
    _arrow(draw, T, (155.0, 70.0), 15.0, 7.5, (1.0, 0.0), AXIS_X, AXIS_X_DARK)
    _arrow(draw, T, (15.0, 70.0), 7.0, 4.2, (-1.0, 0.0), AXIS_X, AXIS_X_DARK)
    # The origin: the hub the whole craft is measured from.
    _circle(draw, T([origin])[0], 2.6, EYE_WHITE, OUTLINE, 0.8)
    _circle(draw, T([origin])[0], 1.1, OUTLINE, None)
    # The near wing, under the fuselage and toward us, with the plot on it.
    near = [(70.0, 72.0), (122.0, 72.0), (94.0, 95.0), (56.0, 95.0)]
    _draw_grid_wing(draw, near, T, GRID_BG, GRID_LINE, GRID_MAJOR, 9, 5, True)


# ---- Pieces --------------------------------------------------------------------
#
# The plane and its snakes are drawn as a rig: the plane is one piece, turned
# with its bank; each snake is ``SNAKE_BONES`` bones of its resting rise (an
# ink piece and a body piece each) placed on its swaying curve and turned to
# it, and a head piece (one per face, gape and tongue) on its neck. A part
# flipbook stores each once.

#: Where a piece's anchor is painted on the scratch canvas (frame pixels);
#: the canvas is twice it.
HOME = (90.0, 70.0)
_PIECES: Dict[tuple, object] = {}


def _piece(key: tuple, paint):
    """``(raster, anchor)``: what ``paint(draw)`` paints with its anchor at
    ``HOME``, cut to its box; ``None`` when it paints nothing."""
    if key not in _PIECES:
        canvas = Image.new("RGBA", (int(2 * HOME[0] * SUPER), int(2 * HOME[1] * SUPER)), TRANSPARENT)
        paint(blending_draw(canvas))
        box = canvas.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (canvas.crop(box), (HOME[0] * SUPER - box[0], HOME[1] * SUPER - box[1]))
    return _PIECES[key]


def _put(canvas: Image.Image, key: tuple, paint, at: Point, name: str, degrees: float = 0.0) -> None:
    part = _piece(key, paint)
    if part is not None:
        shape_rig.place(canvas, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _angle(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _riders(kind: str) -> List[Rider]:
    """Drawn back to front: the rear snake, the captain at the nose, then
    the middle one, seated a little nearer us."""
    if kind == "paper":
        return [
            Rider((56.0, 66.5), 0.84, OLIVE_SCALES, "angry", 0.0),
            Rider((114.0, 65.5), 0.8, TEAL_SCALES, "smug", 2.2, "goggles"),
            Rider((85.0, 70.0), 0.8, GREEN_SCALES, "alert", 4.1),
        ]
    return [
        Rider((52.0, 67.0), 0.8, OLIVE_SCALES, "angry", 0.3),
        Rider((112.0, 67.0), 0.82, TEAL_SCALES, "smug", 2.4, "spectacles"),
        Rider((82.0, 69.0), 0.78, GREEN_SCALES, "alert", 4.3),
    ]


@dataclass(frozen=True)
class Pose:
    """What one frame asks of the riders."""

    lean: Point  # how far the heads are carried (frame pixels)
    sway: float
    head_tilt: float  # degrees, positive = down
    face: str  # "" keeps each rider's own mood
    gape: float
    tongue: Tuple[float, float, float]


def _pose(anim: str, frame_idx: int, nframes: int) -> Pose:
    t = frame_idx / max(1, nframes - 1)
    if anim == "fly":
        return Pose((2.6, 1.2), 1.0, 4.0, "", 0.0, (0.0, 0.0, 0.0))
    if anim == "bank":
        phase = math.tau * frame_idx / max(1, nframes)
        return Pose((-math.sin(phase) * 3.0, 0.0), 0.8, 0.0, "", 0.0, (0.0, 0.0, 0.0))
    if anim == "hiss":
        # Rear back, then strike forward with the jaws wide.
        lean = ((-2.5, -1.0), (-3.4, -1.4), (4.0, 1.0), (5.0, 1.4), (4.4, 1.2), (2.0, 0.4))[frame_idx % 6]
        gape = (0.25, 0.45, 0.9, 1.0, 0.95, 0.6)[frame_idx % 6]
        tilt = (-12.0, -16.0, 6.0, 8.0, 6.0, 0.0)[frame_idx % 6]
        tongue = 3.0 + 3.0 * math.sin(math.pi * t)
        return Pose(lean, 0.4, tilt, "angry", gape, (tongue * 0.7, tongue, tongue * 0.8))
    if anim == "hurt":
        lean = ((-4.0, -1.5), (-2.0, 1.0), (-1.0, 0.0), (0.0, 0.0))[frame_idx % 4]
        return Pose(lean, 0.3, -10.0, "squeeze", 0.35, (0.0, 0.0, 0.0))
    if anim == "death":
        return Pose((4.0 * t, 4.5 * t), 0.2, 8.0 + 22.0 * t, "dead", 0.0, (3.0 * t, 3.0 * t, 3.0 * t))
    # Idle: each snake flicks its tongue on its own beat.
    flick = (
        3.0 if frame_idx == 3 else 0.0,
        (0.0, 4.0, 2.5, 0.0, 0.0, 0.0)[frame_idx % 6],
        3.5 if frame_idx == 5 else 0.0,
    )
    return Pose((0.0, 0.0), 1.0, 0.0, "", 0.0, flick)


def _place_snake(canvas: Image.Image, kind: str, n: int, rider: Rider, phase: float, pose: Pose,
                 center: Point, angle: float, offset: Point) -> None:
    """Snake ``n``: its bones on its swaying curve (all ink, then all body),
    then its head."""
    rest = _rest_curve(rider)
    last = len(rest) - 1
    local: List[Point] = []
    for i, (x, y) in enumerate(rest):
        t = i / last
        rise = _smooth(0.3, 1.0, t) ** 1.4  # the tail stays on the deck
        dx = math.sin(phase + rider.phase + t * 1.6) * 1.8 * pose.sway * rise
        dy = math.cos(phase + rider.phase + t * 1.6) * 0.8 * pose.sway * rise
        local.append((x + dx + pose.lean[0] * rise, y + dy + pose.lean[1] * rise))
    curve = _transform_points(local, center, angle, offset)
    per = last // SNAKE_BONES
    for layer in ("ink", "body"):
        for k in range(SNAKE_BONES):
            a, b = per * k, per * (k + 1)
            _put(
                canvas,
                ("snake_bone", kind, n, k, layer),
                lambda d, k=k, layer=layer: _paint_snake_bone(d, rest, k, rider.scales, layer),
                curve[a],
                f"snake{n}_{layer}{k}",
                _angle(curve[a], curve[b]) - _angle(rest[a], rest[b]),
            )
    face = pose.face or rider.mood
    gape = round(pose.gape, 2)
    tongue = round(pose.tongue[n], 1)
    neck = _angle(local[-2], local[-1]) - _angle(rest[-2], rest[-1])
    _put(
        canvas,
        ("snake_head", kind, n, face, gape, tongue),
        lambda d: _paint_snake_head(d, rider.scales, face, gape, tongue, rider.accessory),
        curve[-1],
        f"snake{n}_head",
        math.degrees(angle) + 0.5 * neck + pose.head_tilt,
    )


def _motion(anim: str, frame_idx: int, nframes: int) -> Tuple[float, Point]:
    """The plane's bank (radians, positive = nose down) and its bob."""
    phase = math.tau * frame_idx / max(1, nframes)
    bob = math.sin(phase) * 2.0
    angle = math.sin(phase) * 0.035
    if anim == "fly":
        bob = math.sin(phase * 2.0) * 2.8
        angle = math.sin(phase) * 0.07
    elif anim == "bank":
        angle = math.sin(phase) * 0.22
        bob = math.cos(phase) * 2.0
    elif anim == "hiss":
        angle = (0.0, -0.03, 0.05, 0.06, 0.04, 0.0)[frame_idx % 6]
        bob = (0.0, -1.0, 1.0, 1.5, 1.0, 0.0)[frame_idx % 6]
    elif anim == "hurt":
        angle = (-0.14, 0.12, -0.08, 0.06)[frame_idx % 4]
        bob = (-3.0, 2.0, -1.0, 0.0)[frame_idx % 4]
    elif anim == "death":
        t = frame_idx / max(1, nframes - 1)
        angle = t * 0.42
        bob = 2.0 + t * 12.0
    return angle, (0.0, bob)


def render_frame(spec: PlaneSpec, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    canvas = Image.new(
        "RGBA",
        (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
        TRANSPARENT,
    )
    center = (80.0, 69.0)
    angle, offset = _motion(anim, frame_idx, nframes)
    phase = math.tau * frame_idx / max(1, nframes)
    pose = _pose(anim, frame_idx, nframes)

    # The plane: painted level about its centre (as if at ``HOME``) and
    # turned with its bank.
    home_shift = (HOME[0] - center[0], HOME[1] - center[1])
    painter = _draw_paper_plane if spec.kind == "paper" else _draw_cartesian_plane
    _put(canvas, ("plane", spec.kind), lambda d: painter(d, HOME, 0.0, home_shift),
         (center[0] + offset[0], center[1] + offset[1]), "plane", math.degrees(angle))

    for idx, rider in enumerate(_riders(spec.kind)):
        _place_snake(canvas, spec.kind, idx, rider, phase, pose, center, angle, offset)

    if anim == "death":
        # Loose scraps of the craft tumble off as it goes down (debris, not
        # a shadow: each is a piece of the plane).
        hx, hy = HOME
        t = frame_idx / max(1, nframes - 1)
        if spec.kind == "paper":
            scrap = lambda d: _poly(d, [(hx - 3.5, hy - 1.5), (hx + 3.5, hy - 2.5), (hx + 1.0, hy + 3.0)], PAPER, OUTLINE, 0.6)
        else:
            def scrap(d):
                _poly(d, [(hx - 3.0, hy - 3.0), (hx + 3.0, hy - 3.0), (hx + 3.0, hy + 3.0), (hx - 3.0, hy + 3.0)], GRID_BG, OUTLINE, 0.6)
                _line(d, [(hx, hy - 3.0), (hx, hy + 3.0)], GRID_LINE, 0.4)
                _line(d, [(hx - 3.0, hy), (hx + 3.0, hy)], GRID_LINE, 0.4)
        for idx in range(4):
            x = 46.0 + idx * 24.0 + math.sin(idx * 1.7 + t * 4.0) * 4.0
            y = 92.0 + t * (10.0 + idx * 3.0)
            _put(canvas, ("fragment", spec.kind), scrap, (x, y), f"fragment_{idx}", t * 160.0 * (1 if idx % 2 else -1))

    return rigdoc.downsampled_canvas(canvas, FRAME_SIZE, Image.Resampling.LANCZOS)


def render_target(spec: PlaneSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    def render_fn(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        return render_frame(spec, anim, frame_idx, nframes)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=spec.target_name,
        rows=ROWS,
        render_fn=render_fn,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=actor_metadata(spec),
    )
    parts = publish_rig_flipbook(spec.target_name, ROWS, render_fn, outputs, frame_transform, out_dir)
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())
