"""Sanic and Super Sanic: the crude "Sanic" meme, drawn as a rig of SVG parts.

The look follows Jon's reference (2026-10-25), the meme drawing made in MS
Paint: the stock Paint palette (blue ``#3F48CC``, cream ``#EFE4B0``, red
``#ED1C24``), flat fills, a thin wobbly ink line. The body is a 3/4 view (the
belly and the face turn to the camera) on legs that run in profile, facing
east. A big blocky head with two derpy eyes and a cream grin, a fan of fat
quills swept back, thin stick limbs, one huge trailing glove and red shoe
blobs.

Each part is an SVG drawing in the reference's own pixels (a 447 px canvas),
rasterized once and placed per frame (``shape_rig.place``), so a part never
boils and the part flipbook records it by name. The wobble of a part is
seeded. A pose (:class:`Pose`) moves the parts: the torso leans about the
hips, the head turns on the neck, the quills sway, and each limb is two
strokes solved to a target (:func:`_ik`).

Rows:

* the jump and every curled pose are the BALL, and the ball turns a whole
  number of turns across its row so the row loops (Jon);
* ``sprint`` is the run at top speed: the feet run round a figure 8
  (Jon, 2026-10-25: "for running when the character gets up to speed, I do
  want circular fast moving feet animation"). The engine draws ``run`` for a
  sheet without it.
* the rest of a full fighter's vocabulary (``FIGHTER_ROWS``, mapped by
  ``FIGHTER_MOTION_COVERAGE``): stops, the turn, hits by height, launches by
  direction, the floor game, guard, ledge, grab, the show.

Super Sanic is the same rig in another :class:`Skin`: gold, quills raised,
red pupils and a glow. Both forms register from this module (``TARGETS``).

The hit area of each strike is measured from the drawn pose: where the glove,
the shoe or the ball is on the frames of the move's Active window
(:func:`_measured_hitboxes`), grown by ``HITBOX_GROWTH``.
"""

from __future__ import annotations

import functools
import io
import math
import random
from functools import lru_cache
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box, union_visible_bbox

Point = Tuple[float, float]

FRAME_SIZE = (160, 144)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

#: Frame pixels per reference pixel, and where the reference's body sits in
#: the frame: its middle (``REF_CX``) at ``CX``, the soles (``REF_GROUND``)
#: on ``GROUND_Y``.
K = 0.29
CX, GROUND_Y = 74.0, 132.0
REF_CX, REF_GROUND = 246.0, 395.0

INK = "#141414"
#: Ink width in reference pixels. The reference's line is ~2 px at 447 px;
#: drawn at ~0.3 of that it would vanish, so it is thicker here.
INK_W = 3.4


@dataclass(frozen=True)
class Skin:
    name: str
    body: str            # MS Paint blue
    crease: str          # the darker line down each quill
    cream: str           # MS Paint cream: belly, muzzle
    glove: str = "#ffffff"
    shoe: str = "#ed1c24"  # MS Paint red
    eye: str = "#ffffff"
    pupil: str = INK
    quills_up: bool = False
    aura: Optional[str] = None


NORMAL = Skin(name="sanic", body="#3f48cc", crease="#232a8a", cream="#efe4b0")
SUPER_SKIN = Skin(name="super", body="#ffd93b", crease="#c98f0c", cream="#fff3c4",
                  pupil="#d0101a", quills_up=True, aura="#fff0a0")


# --- The body at rest (reference pixels, facing east) -----------------------

TORSO_C = (246.0, 252.0)
LEAN_PIVOT = (246.0, 302.0)      # the torso leans about the hips
NECK = (238.0, 176.0)
SHOULDER_BACK = (192.0, 214.0)
SHOULDER_FRONT = (316.0, 208.0)
HIP_BACK = (214.0, 312.0)
HIP_FRONT = (268.0, 318.0)
ARM = (58.0, 54.0)               # upper, lower
LEG = (54.0, 54.0)
BALL_C = (246.0, 323.0)          # a ball on the ground: its bottom on the soles
BALL_R = 72.0
#: The sprint's feet run round a sideways figure 8 (a lemniscate) under the
#: hips: its middle, half-width and tilt. Its lower lobe runs under the ground
#: line, so the foot on it runs along the ground (:func:`_sprint_foot`).
EIGHT_C = (272.0, 366.0)
EIGHT_A = 92.0
EIGHT_TILT = -12.0
#: How far apart the two feet are round the 8, in turns. A quarter turn puts
#: one foot low while the other is high, as in a run.
SPRINT_FEET_APART = 0.25

#: Rest limb targets: a hand from its shoulder, a foot from its hip.
REST_HAND_BACK = (-112.0, 30.0)
REST_HAND_FRONT = (74.0, 6.0)
REST_FOOT_BACK = (-100.0, 62.0)
REST_FOOT_FRONT = (66.0, 66.0)

#: Each shoe: the way its toe points (+1: east) and its size.
SHOES = {"back": (-1, 1.25), "front": (1, 0.9)}


def _sole_drop(foot: str, tilt: float) -> float:
    """How far under the ankle the lowest point of ``foot``'s shoe is, with
    the shoe turned ``tilt`` degrees (reference pixels; the blob of
    :func:`_shoe` without its ink)."""
    facing, size = SHOES[foot]
    a = math.radians(tilt)
    cx, cy, rx, ry = facing * 14 * size, 6 * size, 34 * size, 13 * size
    return cx * math.sin(a) + cy * math.cos(a) + math.hypot(rx * math.sin(a), ry * math.cos(a))


#: The ground line (reference pixels): the higher of the two soles at rest. A
#: running foot that reaches it runs along it and goes no lower.
SOLE_Y = min(HIP_BACK[1] + REST_FOOT_BACK[1] + _sole_drop("back", 0.0),
             HIP_FRONT[1] + REST_FOOT_FRONT[1] + _sole_drop("front", 0.0))

#: Each quill: its root, its tip swept back, its tip raised (super), width.
#: The first four grow from the head, the rest from the back.
QUILLS = [
    ((226, 80), (160, 44), (232, -26), 40),
    ((210, 96), (110, 70), (186, -14), 46),
    ((204, 118), (88, 112), (140, 14), 44),
    ((208, 140), (82, 152), (104, 56), 40),
    ((198, 190), (66, 186), (76, 108), 46),
    ((192, 216), (58, 226), (66, 160), 40),
    ((196, 240), (96, 262), (90, 220), 30),
]
HEAD_QUILLS = 4


@dataclass
class Pose:
    """One drawn moment. Limb targets: hands from their shoulder, feet from
    their hip (``planted``: the feet stay on the ground when the body sinks or
    rises)."""

    root: Point = (0.0, 0.0)
    lean: float = 0.0
    head: float = 0.0
    quill_sway: float = 0.0
    hand_back: Point = REST_HAND_BACK
    hand_front: Point = REST_HAND_FRONT
    foot_back: Point = REST_FOOT_BACK
    foot_front: Point = REST_FOOT_FRONT
    glove_back: float = 1.0
    glove_front: float = 1.0
    shoe_back_tilt: float = 0.0
    shoe_front_tilt: float = 0.0
    knee_forward: float = 0.0      # 0: the reference's dropped knee; 1: bent forward
    planted: bool = True
    eyes: str = "derp"             # derp | wide | squint | closed | dead
    mouth: str = "grin"            # grin | open | flat | ouch
    ball: bool = False
    ball_at: Point = (0.0, 0.0)    # the ball's offset from BALL_C
    turn: float = 0.0              # the ball's turn, in turns
    eight: bool = False            # the sprint's figure-8 trail behind the feet
    eight_u: float = 0.0           # where the back foot is on it (turns)
    fx: Tuple[str, ...] = ()       # speed | dust | dirt
    mirror: bool = False           # drawn facing the other way (a turn's first frames)
    on_floor: bool = False         # lowered or raised until its lowest paint is on the floor (:func:`_on_floor`)
    legs: bool = True              # False: no legs (buried to the waist)


# --- Geometry -----------------------------------------------------------------


def _rot(p: Point, degrees: float, c: Point = (0.0, 0.0)) -> Point:
    r = math.radians(degrees)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(r) - y * math.sin(r), c[1] + x * math.sin(r) + y * math.cos(r))


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _frame(p: Point) -> Point:
    """A reference point in frame pixels."""
    return (CX + (p[0] - REF_CX) * K, GROUND_Y + (p[1] - REF_GROUND) * K)


def _two_bone(root: Point, target: Point, l1: float, l2: float, side: float) -> Tuple[Point, Point]:
    d = (target[0] - root[0], target[1] - root[1])
    dist = max(abs(l1 - l2) + 1e-3, min(math.hypot(*d), (l1 + l2) * 0.999))
    a = math.atan2(d[1], d[0])
    b = math.acos(max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    joint = (root[0] + l1 * math.cos(a - side * b), root[1] + l1 * math.sin(a - side * b))
    end = (root[0] + dist * math.cos(a), root[1] + dist * math.sin(a))
    return joint, end


def _ik(root: Point, target: Point, lengths: Tuple[float, float], hint: Point) -> Tuple[Point, Point]:
    """The middle joint and end of a two-bone limb, on the side of its line
    that lies further along ``hint``."""
    a = _two_bone(root, target, *lengths, 1.0)
    b = _two_bone(root, target, *lengths, -1.0)
    da = (a[0][0] - root[0]) * hint[0] + (a[0][1] - root[1]) * hint[1]
    db = (b[0][0] - root[0]) * hint[0] + (b[0][1] - root[1]) * hint[1]
    return a if da >= db else b


@dataclass
class Solved:
    """Where everything is in one pose (reference pixels)."""

    torso: Point
    pivot: Point
    neck: Point
    shoulder_back: Point
    elbow_back: Point
    hand_back: Point
    shoulder_front: Point
    elbow_front: Point
    hand_front: Point
    hip_back: Point
    knee_back: Point
    foot_back: Point
    hip_front: Point
    knee_front: Point
    foot_front: Point
    ball: Point


def _solve(pose: Pose) -> Solved:
    def body(p: Point) -> Point:
        return _add(_rot(p, pose.lean, LEAN_PIVOT), pose.root)

    sb, sf, hb, hf = body(SHOULDER_BACK), body(SHOULDER_FRONT), body(HIP_BACK), body(HIP_FRONT)
    if pose.planted:
        fb_target = _add(_add(HIP_BACK, pose.foot_back), (pose.root[0], 0.0))
        ff_target = _add(_add(HIP_FRONT, pose.foot_front), (pose.root[0], 0.0))
    else:
        fb_target, ff_target = _add(hb, pose.foot_back), _add(hf, pose.foot_front)
    knee_hint = (0.3 + 0.7 * pose.knee_forward, 1.0 - 1.2 * pose.knee_forward)
    kb, fb = _ik(hb, fb_target, LEG, knee_hint)
    kf, ff = _ik(hf, ff_target, LEG, knee_hint)
    eb, wb = _ik(sb, _add(sb, pose.hand_back), ARM, (0.2, 1.0))
    ef, wf = _ik(sf, _add(sf, pose.hand_front), ARM, (0.2, -1.0))
    return Solved(
        torso=body(TORSO_C), pivot=body(LEAN_PIVOT), neck=body(NECK),
        shoulder_back=sb, elbow_back=eb, hand_back=wb,
        shoulder_front=sf, elbow_front=ef, hand_front=wf,
        hip_back=hb, knee_back=kb, foot_back=fb,
        hip_front=hf, knee_front=kf, foot_front=ff,
        ball=_add(_add(BALL_C, pose.ball_at), pose.root),
    )


# --- SVG drawing helpers (reference pixels) -----------------------------------


def _wobble_blob(cx, cy, rx, ry, seed, n=16, amp=0.06, tilt=0.0):
    """A closed lumpy ellipse, the way a mouse draws one, fixed by its seed."""
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1.0 + rng.uniform(-amp, amp)
        pts.append(_rot((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)), tilt, (cx, cy)))
    return pts


def _smooth(pts, closed=True) -> str:
    """A Catmull-Rom curve through ``pts`` as SVG path data."""
    n = len(pts)
    P = [np.array(p, float) for p in pts]
    d = [f"M {P[0][0]:.2f},{P[0][1]:.2f}"]
    for i in range(n if closed else n - 1):
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        d.append(f"C {c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}")
    if closed:
        d.append("Z")
    return " ".join(d)


def _fill(pts, color, ink=INK_W) -> str:
    return f'<path d="{_smooth(pts)}" fill="{color}" stroke="{INK}" stroke-width="{ink}" stroke-linejoin="round"/>'


def _line(pts, color=INK, width=2.4) -> str:
    return (f'<path d="{_smooth(pts, closed=False)}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def _quill_svg(base, tip, width, seed, skin: Skin) -> str:
    """A long tapered spike, bowed a little, with a dark crease down it."""
    rng = random.Random(seed)
    b, t = np.array(base, float), np.array(tip, float)
    axis = t - b
    length = float(np.linalg.norm(axis))
    u = axis / length
    nrm = np.array([-u[1], u[0]])
    mid = b + axis * 0.5 + nrm * length * 0.18
    pts = [b + nrm * width / 2, mid + nrm * width * 0.28 + nrm * rng.uniform(-1, 1), t,
           mid - nrm * width * 0.22, b - nrm * width / 2]
    crease = [b + axis * 0.15, mid + nrm * rng.uniform(-1.5, 1.5), b + axis * 0.85 + nrm * length * 0.054]
    return (_fill([tuple(p) for p in pts], skin.body, INK_W * 0.9)
            + _line([tuple(p) for p in crease], skin.crease, 2.0))


# --- Pieces: each drawn once, placed per frame --------------------------------

_PIECES: Dict[tuple, Optional[Tuple[Image.Image, Point]]] = {}
_DEFS = ('<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
         '<feGaussianBlur stdDeviation="22"/></filter></defs>')


def _piece(key: tuple, svg: Callable[[], str], anchor: Point, reach: float = 260.0):
    """The raster of ``svg()`` (reference pixels) about ``anchor``, cut to its
    paint, and the anchor in it (super pixels); ``None`` when it paints
    nothing. ``key`` names everything ``svg`` reads."""
    if key not in _PIECES:
        import resvg_py

        px = int(round(2 * reach * K * SUPER))
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{anchor[0] - reach} {anchor[1] - reach} '
               f'{2 * reach} {2 * reach}" width="{px}" height="{px}">{_DEFS}{svg()}</svg>')
        img = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).convert("RGBA")
        box = img.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (img.crop(box), (px / 2 - box[0], px / 2 - box[1]))
    return _PIECES[key]


#: Set while a ``Pose.mirror`` pose is drawn: every piece is placed mirrored
#: about the body's middle (``CX``), so a mirrored frame is still made of
#: placed pieces and the part flipbook replays it.
_MIRRORED = [False]


def _put(img: Image.Image, key: tuple, svg, anchor: Point, at: Point, degrees: float, name: str, reach=260.0) -> None:
    """Place the piece ``key`` with its anchor at the reference point ``at``."""
    part = _piece(key, svg, anchor, reach)
    if part is not None:
        fx, fy = _frame(at)
        if _MIRRORED[0]:
            if ("mirror",) + key not in _PIECES:
                raster, (px, py) = part
                _PIECES[("mirror",) + key] = (raster.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (raster.width - px, py))
            part, fx, degrees = _PIECES[("mirror",) + key], 2 * CX - fx, -degrees
        shape_rig.place(img, part, (fx * SUPER, fy * SUPER), degrees, name)


def _limb(img, skin: Skin, points: Sequence[Point], width: float, name: str) -> None:
    """A two-segment Paint limb: both inks first, then both colours, so the
    joint shows no ink across it."""
    segs = list(zip(points[:-1], points[1:]))
    for layer, (stroke_w, color) in (("ink", (width + 2 * INK_W, INK)), ("", (width, skin.body))):
        for k, (a, b) in enumerate(segs):
            length = round(math.hypot(b[0] - a[0], b[1] - a[1]))
            degrees = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            svg = (lambda L=length, w=stroke_w, c=color:
                   f'<path d="M 0,0 L {L},0" stroke="{c}" stroke-width="{w}" stroke-linecap="round" fill="none"/>')
            _put(img, ("seg", length, stroke_w, color), svg, (0.0, 0.0), a, degrees, f"{name}_{k}{layer}")


def _glove(img, skin, at, size, seed, rx, ry, name):
    s = round(size, 1)
    _put(img, ("glove", skin.glove, s, seed),
         lambda: _fill(_wobble_blob(0, 0, rx * s, ry * s, seed), skin.glove), (0.0, 0.0), at, 0.0, name)


def _shoe(img, skin, ankle, facing, tilt, size, seed, name):
    """A red blob of a shoe, its toe out ahead of the ankle."""
    _put(img, ("shoe", skin.shoe, facing, size, seed),
         lambda: _fill(_wobble_blob(facing * 14 * size, 6 * size, 34 * size, 13 * size, seed, amp=0.08), skin.shoe),
         (0.0, 0.0), ankle, tilt, name)


def _head_svg(skin: Skin) -> str:
    # the reference's head is nearly a rounded box
    head = [(204, 96), (228, 74), (270, 70), (300, 84), (306, 118), (300, 150), (272, 168), (232, 166), (206, 148), (198, 120)]
    muzzle = [(236, 138), (262, 134), (290, 137), (294, 148), (284, 158), (262, 161), (240, 158), (232, 148)]
    return "".join([
        f'<path d="M {NECK[0]},{NECK[1]} L 242,156" stroke="{INK}" stroke-width="{20 + 2 * INK_W}" stroke-linecap="round"/>',
        f'<path d="M {NECK[0]},{NECK[1]} L 242,156" stroke="{skin.body}" stroke-width="20" stroke-linecap="round"/>',
        _fill(head, skin.body),
        _fill(muzzle, skin.cream, INK_W * 0.85),
        f'<circle cx="252" cy="128" r="4.6" fill="{INK}"/>',
        _line([(210, 95), (236, 92)], INK, 2.4),
    ])


EYES = [((228, 108), 19, 13, -6), ((276, 112), 25, 14, 4)]


def _eyes_svg(skin: Skin, kind: str) -> str:
    out = []
    pupils = {"derp": [(236, 108), (268, 113)], "wide": [(228, 106), (280, 110)], "squint": [(232, 110), (276, 112)]}
    for k, (c, rx, ry, tilt) in enumerate(EYES):
        if kind == "dizzy":  # dazed: a spiral in each eye
            out.append(_fill(_wobble_blob(c[0], c[1], rx, ry, 500 + rx, amp=0.04, tilt=tilt), skin.eye, INK_W * 0.8))
            turn = 1 if k == 0 else -1
            spiral = [(c[0] + 1.6 * a * math.cos(turn * a), c[1] + 1.1 * a * math.sin(turn * a))
                      for a in np.linspace(0.5, 3.4 * math.pi, 16)]
            out.append(_line(spiral, skin.pupil, 2.2))
            continue
        if kind in ("closed", "dead"):
            if kind == "closed":  # squeezed shut: a > and a <
                s = 1 if k == 0 else -1
                out.append(_line([(c[0] - s * rx * 0.6, c[1] - 8), (c[0] + s * rx * 0.5, c[1]), (c[0] - s * rx * 0.6, c[1] + 8)], INK, 3.0))
            else:  # an X
                out.append(_line([(c[0] - 9, c[1] - 8), (c[0] + 9, c[1] + 8)], INK, 3.0))
                out.append(_line([(c[0] + 9, c[1] - 8), (c[0] - 9, c[1] + 8)], INK, 3.0))
            continue
        sy = 0.45 if kind == "squint" else 1.0
        out.append(_fill(_wobble_blob(c[0], c[1], rx, ry * sy, 500 + rx, amp=0.04, tilt=tilt), skin.eye, INK_W * 0.8))
        p = pupils[kind][k]
        out.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="4.2" fill="{skin.pupil}"/>')
    return "".join(out)


def _mouth_svg(kind: str) -> str:
    if kind == "grin":
        return _line([(242, 149), (264, 154), (286, 147)], INK, 2.6)
    if kind == "open":
        return _fill([(244, 146), (282, 145), (276, 158), (252, 160)], "#7a1010", 2.4)
    if kind == "ouch":
        return _line([(242, 152), (250, 147), (258, 153), (266, 147), (274, 153), (282, 148)], INK, 2.4)
    return _line([(244, 151), (282, 150)], INK, 2.6)


def _torso_svg(skin: Skin) -> str:
    belly = [(214, 210), (260, 200), (290, 214), (292, 262), (272, 284), (226, 282), (210, 254)]
    hairs = [((180, 270), (172, 282)), ((186, 292), (180, 304)), ((300, 290), (308, 300))]
    return "".join([_fill(_wobble_blob(*TORSO_C, 74, 80, 7, amp=0.05), skin.body, INK_W * 1.1),
                    _fill(belly, skin.cream, INK_W * 0.9)]
                   + [_line([a, b], INK, 1.8) for a, b in hairs])


def _ball_svg(skin: Skin) -> str:
    """The spin ball about ``BALL_C``: a lumpy ball with quill tips round it,
    one eye and one shoe peeking out so a whole turn reads."""
    cx, cy = BALL_C
    out = []
    for k in range(7):
        a = math.radians(-150 + k * 34)
        base = (cx + 60 * math.cos(a), cy + 60 * math.sin(a))
        tip = (cx + 104 * math.cos(a - 0.5), cy + 104 * math.sin(a - 0.5))
        out.append(_quill_svg(base, tip, 34, 600 + k, skin))
    out.append(_fill(_wobble_blob(cx, cy, BALL_R, BALL_R * 0.97, 9, amp=0.06), skin.body, INK_W * 1.1))
    out.append(_fill(_wobble_blob(cx + 22, cy + 18, 30, 26, 10, amp=0.08), skin.cream, INK_W * 0.9))
    out.append(_fill(_wobble_blob(cx + 34, cy - 26, 15, 11, 11, amp=0.05), skin.eye, INK_W * 0.8))
    out.append(f'<circle cx="{cx + 38}" cy="{cy - 25}" r="4" fill="{skin.pupil}"/>')
    out.append(_fill(_wobble_blob(cx - 40, cy + 50, 22, 10, 12, amp=0.08, tilt=-30), skin.shoe, INK_W * 0.8))
    return "".join(out)


def _eight_point(u: float) -> Point:
    """The point at ``u`` (turns) round the sprint's figure 8."""
    t = 2 * math.pi * u
    d = 1 + math.sin(t) ** 2
    p = (EIGHT_A * math.cos(t) / d, EIGHT_A * 0.9 * math.sin(t) * math.cos(t) / d)
    return _add(_rot(p, EIGHT_TILT), EIGHT_C)


def _sprint_foot(u: float, foot: str) -> Tuple[Point, float]:
    """The ankle of ``foot`` at ``u`` (turns) round the figure 8, and its
    shoe's tilt. The shoe tilts with the way it travels; where the 8 runs
    under the ground the foot runs flat along it, its sole on ``SOLE_Y``."""
    here, ahead = _eight_point(u), _eight_point(u - 0.02)
    tilt = math.degrees(math.atan2(ahead[1] - here[1], ahead[0] - here[0]))
    tilt = max(-30.0, min(30.0, ((tilt + 90) % 180) - 90))
    if here[1] + _sole_drop(foot, tilt) <= SOLE_Y:
        return here, tilt
    return (here[0], SOLE_Y - _sole_drop(foot, 0.0)), 0.0


#: Half the width of the blur of the feet (reference pixels).
EIGHT_BLUR = 13.0


def _eight_svg(skin: Skin) -> str:
    """The blur the feet leave round the figure 8, along the ground where
    the feet run along it."""
    pts = [(x, min(y, SOLE_Y - EIGHT_BLUR)) for x, y in (_eight_point(u) for u in np.linspace(0, 1, 33)[:-1])]
    return (f'<path d="{_smooth(pts)}" fill="none" stroke="{skin.body}" stroke-width="{2 * EIGHT_BLUR}" opacity="0.4"/>'
            f'<path d="{_smooth(pts)}" fill="none" stroke="{skin.shoe}" stroke-width="8" opacity="0.5"/>')


#: The ghosts each sprinting shoe leaves behind it on the figure 8:
#: (how far back, in turns; opacity).
SHOE_GHOSTS = ((0.07, 0.45), (0.14, 0.22))


#: The super glow: its middle above the torso's and its radii (reference
#: pixels). It reaches from over the raised quills to the soles, and its blur
#: fades out inside the frame: a glow that ran past the frame was cut flat at
#: the frame's edge, and the cut stood under the feet.
AURA_RISE, AURA_R = 62.0, (170.0, 200.0)
#: The glow round the ball: its rise over the ball's middle and its radius.
BALL_AURA_RISE, BALL_AURA_R = 40.0, 110.0


def _aura_svg(skin: Skin) -> str:
    return (f'<ellipse cx="{TORSO_C[0]}" cy="{TORSO_C[1] - AURA_RISE}" rx="{AURA_R[0]}" ry="{AURA_R[1]}" '
            f'fill="{skin.aura}" opacity="0.55" filter="url(#glow)"/>')


def _speed_svg(skin: Skin) -> str:
    out = []
    for k, (y, length) in enumerate([(170, 110), (215, 160), (262, 130), (310, 90)]):
        out.append(_line([(40 - length, y), (40, y)], skin.body if k % 2 else "#9aa4ff", 4.5))
    return "".join(out)


def _dirt_svg() -> str:
    """The mound a buried body stands in: Paint brown, its flat bottom on the
    ground line (reference pixels, about the body's middle)."""
    pts = [(150, 395), (170, 368), (204, 352), (246, 348), (290, 352), (324, 368), (344, 395)]
    return (f'<path d="{_smooth(pts, closed=False)} Z" fill="#b97a57" stroke="{INK}" stroke-width="{INK_W}" '
            'stroke-linejoin="round"/>' + _line([(196, 370), (214, 366)], INK, 1.8) + _line([(280, 364), (300, 372)], INK, 1.8))


def _dust_svg() -> str:
    return "".join(_fill(_wobble_blob(140 - k * 34, 390 - 4 * k, 16 - 2 * k, 10 - k, 900 + k), "#d8d2c4", 2.2)
                   for k in range(4))


# --- Drawing one pose -----------------------------------------------------------


def _draw_pose(skin: Skin, pose: Pose, body_only: bool = False) -> Image.Image:
    """One pose. ``body_only`` draws the body without what it gives off (the
    glow, the speed lines, the dust, the blur of the feet): the drawing the
    gameplay body is measured from (:func:`_pose_bodies`)."""
    _MIRRORED[0] = pose.mirror
    try:
        return _draw_placed(skin, pose, body_only)
    finally:
        _MIRRORED[0] = False


def _draw_placed(skin: Skin, pose: Pose, body_only: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = _solve(pose)
    sk = skin.name
    fx = not body_only
    if fx and "speed" in pose.fx:
        _put(img, ("speed", sk), lambda: _speed_svg(skin), (0.0, 240.0), _add((0.0, 240.0), pose.root), 0.0, "speed_lines")
    if fx and "dust" in pose.fx:
        _put(img, ("dust",), _dust_svg, (90.0, 380.0), (90.0 + pose.root[0], 380.0), 0.0, "dust")

    if pose.ball:
        if fx and skin.aura:
            _put(img, ("ball_aura", sk), lambda: f'<circle cx="{BALL_C[0]}" cy="{BALL_C[1] - BALL_AURA_RISE}" r="{BALL_AURA_R}" fill="{skin.aura}" '
                 'opacity="0.55" filter="url(#glow)"/>', BALL_C, s.ball, 0.0, "aura")
        _put(img, ("ball", sk), lambda: _ball_svg(skin), BALL_C, s.ball, 360.0 * pose.turn, "ball")
        return _downsample(img)

    if fx and skin.aura:
        _put(img, ("aura", sk), lambda: _aura_svg(skin), TORSO_C, s.torso, 0.0, "aura", reach=300.0)

    # the quills, back to front: the back's, then the head's
    head_turn = pose.lean + pose.head
    for k in reversed(range(len(QUILLS))):
        base, tip_back, tip_up, width = QUILLS[k]
        tip = tip_up if skin.quills_up else tip_back
        on_head = k < HEAD_QUILLS
        at = _add(_rot(_add(_rot(base, pose.lean, LEAN_PIVOT), pose.root), pose.head, s.neck), (0, 0)) if on_head \
            else _add(_rot(base, pose.lean, LEAN_PIVOT), pose.root)
        degrees = (head_turn if on_head else pose.lean) + pose.quill_sway * (1 + 0.3 * k)
        _put(img, ("quill", sk, k), lambda b=base, t=tip, w=width, k=k: _quill_svg(b, t, w, 100 + k, skin),
             base, at, degrees, f"quill_{k}")

    # the back leg and arm, behind the body
    if fx and pose.eight:
        _put(img, ("eight", sk), lambda: _eight_svg(skin), EIGHT_C, _add(EIGHT_C, (pose.root[0], 0.0)), 0.0, "eight")
        for foot, (back, alpha) in [(f, g) for f in ("back", "front") for g in SHOE_GHOSTS]:
            u = pose.eight_u + (SPRINT_FEET_APART if foot == "front" else 0.0) + back
            at = _add(_sprint_foot(-u, foot)[0], (pose.root[0], 0.0))
            _put(img, ("ghost_shoe", skin.shoe, alpha),
                 lambda a=alpha: f'<g opacity="{a}">' + _fill(_wobble_blob(14, 6, 32, 12, 301, amp=0.08), skin.shoe) + "</g>",
                 (0.0, 0.0), at, 0.0, f"ghost_{foot}_{back}")
    if pose.legs:
        _limb(img, skin, [s.hip_back, s.knee_back, s.foot_back], 15, "leg_back")
        _shoe(img, skin, s.foot_back, SHOES["back"][0], pose.shoe_back_tilt, SHOES["back"][1], 300, "shoe_back")
    _limb(img, skin, [s.shoulder_back, s.elbow_back, s.hand_back], 15, "arm_back")
    _glove(img, skin, s.hand_back, pose.glove_back, 401, 27, 23, "glove_back")

    _put(img, ("torso", sk), lambda: _torso_svg(skin), LEAN_PIVOT, s.pivot, pose.lean, "torso")

    if pose.legs:
        _limb(img, skin, [s.hip_front, s.knee_front, s.foot_front], 15, "leg_front")
        _shoe(img, skin, s.foot_front, SHOES["front"][0], pose.shoe_front_tilt, SHOES["front"][1], 301, "shoe_front")

    _put(img, ("head", sk), lambda: _head_svg(skin), NECK, s.neck, head_turn, "head")
    _put(img, ("mouth", pose.mouth), lambda: _mouth_svg(pose.mouth), NECK, s.neck, head_turn, "mouth")
    _put(img, ("eyes", sk, pose.eyes), lambda: _eyes_svg(skin, pose.eyes), NECK, s.neck, head_turn, "eyes")

    # the front arm last: it crosses the body when it swings
    _limb(img, skin, [s.shoulder_front, s.elbow_front, s.hand_front], 14, "arm_front")
    _glove(img, skin, s.hand_front, pose.glove_front, 402, 17, 11, "glove_front")
    if fx and "dirt" in pose.fx:
        _put(img, ("dirt",), _dirt_svg, (246.0, 395.0), (246.0 + pose.root[0], 395.0), 0.0, "dirt")
    return _downsample(img)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


# --- The moves ------------------------------------------------------------------


def _lerp(a, b, u):
    if isinstance(a, bool) or isinstance(a, str) or isinstance(a, tuple) and a and isinstance(a[0], str):
        return a if u < 0.5 else b
    if isinstance(a, tuple):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def _between(a: Pose, b: Pose, u: float) -> Pose:
    e = 0.5 - 0.5 * math.cos(math.pi * u)  # ease in and out
    return Pose(**{f.name: _lerp(getattr(a, f.name), getattr(b, f.name), e) for f in fields(Pose)})


def _keyed(keys: Sequence[Tuple[float, Pose]], t: float) -> Pose:
    """The pose at ``t`` between key poses ``(t, Pose)``."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return _between(a, b, (t - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]


P = Pose


def _gait(t: float, stride: float, lift: float, lean: float, arm: float, bob: float, fx=()) -> Pose:
    a = 2 * math.pi * t
    s, c = math.sin(a), math.cos(a)
    return P(root=(0, -bob * abs(s)), lean=lean, head=-lean * 0.5, quill_sway=-lean * 0.4 + 3 * s,
             foot_back=(-40 + stride * s, 62 - lift * max(0.0, c)),
             foot_front=(10 - stride * s, 66 - lift * max(0.0, -c)),
             hand_back=(-90 - arm * s, 24 + arm * 0.6 * s), hand_front=(50 + arm * s, 14 - arm * 0.8 * s),
             shoe_back_tilt=-10 * s, shoe_front_tilt=10 * s, fx=fx)


def _sprint(t: float) -> Pose:
    """Top speed: the feet run round a figure 8 (:func:`_sprint_foot`),
    ``SPRINT_FEET_APART`` apart, and leave its blur behind them."""
    s = math.sin(2 * math.pi * t)
    fb, tb = _sprint_foot(-t, "back")
    ff, tf = _sprint_foot(-(t + SPRINT_FEET_APART), "front")
    return P(root=(0, -4 * abs(s)), lean=26, head=-14, quill_sway=-14 + 2 * s,
             foot_back=(fb[0] - HIP_BACK[0], fb[1] - HIP_BACK[1]), foot_front=(ff[0] - HIP_FRONT[0], ff[1] - HIP_FRONT[1]),
             shoe_back_tilt=tb, shoe_front_tilt=tf, knee_forward=1.0,
             hand_back=(-110 + 30 * s, 10 + 20 * s), hand_front=(60 - 40 * s, 10 - 30 * s),
             eight=True, eight_u=t, eyes="wide", fx=("speed",))


def _ball(t: float, turns: float, at: Point = (0, 0), fx=()) -> Pose:
    return P(ball=True, turn=turns * t, ball_at=at, fx=fx)


HANG = P(root=(0, -16), hand_front=(24, -108), hand_back=(70, -100), foot_back=(-30, 70), foot_front=(10, 74),
         planted=False, eyes="wide", mouth="flat", quill_sway=6)
CROUCH = P(root=(0, 36), lean=10, head=6, foot_back=(-60, 62), foot_front=(40, 66), knee_forward=1.0,
           hand_front=(30, 50), hand_back=(-60, 60))


def _row_poses(anim: str, n: int, skin: Skin = NORMAL) -> List[Pose]:
    """The ``n`` poses of a row, each ``on_floor`` pose stood on ``skin``'s floor."""
    return list(_row_poses_of(anim, n, skin))


@lru_cache(maxsize=None)
def _row_poses_of(anim: str, n: int, skin: Skin) -> Tuple[Pose, ...]:
    loop = anim in LOOPS
    ts = [i / n if loop else (i / (n - 1) if n > 1 else 0.0) for i in range(n)]
    key = ROW_KEYS.get(anim)
    poses = [_keyed(key, t) for t in ts] if key is not None else [ROW_FUNCS[anim](t) for t in ts]
    return tuple(_on_floor(skin, p) if p.on_floor else p for p in poses)


#: Alpha of paint that is part of the figure (not the resampling fringe).
SOLID_ALPHA = 192


def _lowest_paint(img: Image.Image) -> int:
    """One past the lowest frame row with solid paint."""
    rows = np.nonzero((np.asarray(img.getchannel("A")) >= SOLID_ALPHA).any(axis=1))[0]
    return int(rows.max()) + 1 if len(rows) else 0


@lru_cache(maxsize=None)
def _floor_line(skin: Skin) -> int:
    """The floor every pose stands on: the soles of the idle body."""
    return _lowest_paint(_draw_pose(skin, ROW_FUNCS["idle"](0.0), body_only=True))


def _on_floor(skin: Skin, pose: Pose) -> Pose:
    """``pose`` moved up or down until its lowest body paint is on the floor:
    a body lying, sitting or rolling on the ground neither hovers nor sinks."""
    for _ in range(3):
        dy = _floor_line(skin) - _lowest_paint(_draw_pose(skin, pose, body_only=True))
        if dy == 0:
            break
        pose = replace(pose, root=(pose.root[0], pose.root[1] + dy / K))
    return pose


LOOPS = {"idle", "walk", "run", "sprint", "dash", "ball", "jump", "fall", "special", "crouch",
         "block", "wall_grab", "ledge_grab", "air_neutral", "air_down"}

#: Rows drawn by a function of the row's time.
ROW_FUNCS: Dict[str, Callable[[float], Pose]] = {
    "idle": lambda t: P(root=(0, 4 * math.sin(math.pi * t) ** 2), quill_sway=2 * math.sin(2 * math.pi * t),
                        hand_front=(74, 6 + 4 * math.sin(2 * math.pi * t)), hand_back=(-112, 30 + 3 * math.sin(2 * math.pi * t)),
                        eyes="closed" if 0.6 < t < 0.75 else "derp"),
    "walk": lambda t: _gait(t, 46, 18, 5, 18, 4),
    "run": lambda t: _gait(t, 82, 34, 18, 34, 7, fx=("speed",)),
    "sprint": _sprint,
    "crouch": lambda t: replace(CROUCH, root=(0, 36 + 2 * math.sin(2 * math.pi * t))),
    "dash_startup": lambda t: _ball(t, 2.0, fx=("dust",)),
    "dash": lambda t: _ball(t, 2.0, fx=("speed",)),
    "ball": lambda t: _ball(t, 2.0),
    "jump": lambda t: _ball(t, 1.0, at=(0, -60)),
    "air_neutral": lambda t: _ball(t, 1.0, at=(0, -60)),
    "air_down": lambda t: _ball(t, 2.0, at=(0, -40)),
    "special": lambda t: _ball(t, 2.0, at=(0, -30)),
    "ledge_roll": lambda t: _ball(t, 1.0, at=(-60 + 120 * t, -40 * math.sin(math.pi * t))),
    "fall": lambda t: P(root=(0, -20), hand_front=(30, -90 + 12 * math.sin(2 * math.pi * t)),
                        hand_back=(-50, -84 - 12 * math.sin(2 * math.pi * t)), foot_back=(-40, 74), foot_front=(24, 76),
                        planted=False, eyes="wide", mouth="open", quill_sway=10),
    "block": lambda t: P(root=(0, 12), lean=-4, hand_front=(30, -4), hand_back=(110, -10), glove_front=1.2,
                         knee_forward=0.6, eyes="squint", mouth="flat"),
    "wall_grab": lambda t: P(lean=-4, hand_front=(78, -40), hand_back=(60, -60), foot_front=(92, 30),
                             foot_back=(-6, 76 + 2 * math.sin(2 * math.pi * t)), planted=False, eyes="derp", mouth="flat"),
    "ledge_grab": lambda t: replace(HANG, quill_sway=6 + 2 * math.sin(2 * math.pi * t)),
}

#: Rows drawn between key poses ``(t, Pose)``.
ROW_KEYS: Dict[str, List[Tuple[float, Pose]]] = {
    "land_hard": [(0.0, P(root=(0, 24), knee_forward=1, hand_front=(80, -20), hand_back=(-100, -10), eyes="squint", mouth="open")),
                  (0.5, P(root=(0, 40), knee_forward=1, lean=10, hand_front=(70, 20), hand_back=(-100, 20), eyes="squint", mouth="open")),
                  (1.0, replace(CROUCH, root=(0, 30)))],
    "land_recovery": [(0.0, replace(CROUCH, root=(0, 30))), (1.0, P())],
    "skid": [(0.0, P(lean=-12, foot_front=(96, 66), foot_back=(-24, 62), hand_front=(30, -60), hand_back=(-80, -30),
                      eyes="wide", mouth="open", fx=("dust",))),
             (1.0, P(lean=-18, root=(4, 4), foot_front=(104, 66), foot_back=(-20, 62), hand_front=(40, -70),
                     hand_back=(-70, -40), eyes="wide", mouth="open", fx=("dust",)))],
    "slash": [(0.0, P(hand_front=(-30, -60), lean=-4, eyes="squint")),
              (0.4, P(hand_front=(80, -60), lean=6, glove_front=1.3, mouth="open", eyes="squint")),
              (0.6, P(hand_front=(110, 0), lean=10, glove_front=1.4, mouth="open", eyes="wide")),
              (1.0, P(hand_front=(70, 20), lean=4))],
    "punch": [(0.0, P(hand_front=(40, 16), lean=2)),
              (0.4, P(hand_front=(116, 2), lean=10, head=-4, glove_front=1.5, mouth="open", eyes="wide")),
              (0.6, P(hand_front=(116, 2), lean=10, head=-4, glove_front=1.5, mouth="open", eyes="wide")),
              (1.0, P(hand_front=(70, 8), glove_front=1.1))],
    "attack_side": [(0.0, P(lean=-6, foot_front=(30, 40))),
                    (0.3, P(lean=-14, foot_front=(116, 0), shoe_front_tilt=-20, mouth="open", eyes="squint")),
                    (0.6, P(lean=-14, foot_front=(118, -4), shoe_front_tilt=-20, mouth="open", eyes="squint")),
                    (1.0, P(lean=-6, foot_front=(60, 40)))],
    "attack_up": [(0.0, P(root=(0, 10), hand_front=(40, 40), knee_forward=0.6)),
                  (0.35, P(root=(0, -6), lean=-10, head=-14, hand_front=(10, -118), glove_front=1.4, quill_sway=8,
                           eyes="wide", mouth="open")),
                  (0.6, P(root=(0, -6), lean=-10, head=-14, hand_front=(16, -116), glove_front=1.4, quill_sway=8,
                          eyes="wide", mouth="open")),
                  (1.0, P(hand_front=(40, -40)))],
    "attack_down": [(0.0, replace(CROUCH, foot_front=(20, 66))),
                    (0.35, replace(CROUCH, root=(0, 40), lean=18, foot_front=(132, 60), shoe_front_tilt=-6,
                                   eyes="squint", mouth="open")),
                    (0.6, replace(CROUCH, root=(0, 40), lean=18, foot_front=(132, 60), shoe_front_tilt=-6,
                                  eyes="squint", mouth="open")),
                    (1.0, replace(CROUCH, foot_front=(40, 66)))],
    "air_forward": [(0.0, P(root=(0, -40), lean=-6, foot_front=(20, 40), foot_back=(-40, 60), planted=False)),
                    (0.35, P(root=(0, -40), lean=-22, foot_front=(110, 10), foot_back=(30, 60), shoe_front_tilt=-25,
                             planted=False, eyes="squint", mouth="open")),
                    (0.6, P(root=(0, -40), lean=-22, foot_front=(112, 8), foot_back=(30, 60), shoe_front_tilt=-25,
                            planted=False, eyes="squint", mouth="open")),
                    (1.0, P(root=(0, -40), foot_front=(30, 60), foot_back=(-40, 60), planted=False))],
    "air_back": [(0.0, P(root=(0, -40), lean=6, foot_back=(-30, 60), planted=False)),
                 (0.35, P(root=(0, -40), lean=20, head=-6, foot_back=(-124, 6), foot_front=(20, 50), shoe_back_tilt=20,
                          planted=False, eyes="squint", mouth="open")),
                 (0.6, P(root=(0, -40), lean=20, head=-6, foot_back=(-126, 4), foot_front=(20, 50), shoe_back_tilt=20,
                         planted=False, eyes="squint", mouth="open")),
                 (1.0, P(root=(0, -40), foot_back=(-40, 60), foot_front=(20, 60), planted=False))],
    "air_up": [(0.0, P(root=(0, -40), lean=0, foot_front=(20, 60), foot_back=(-30, 60), planted=False)),
               (0.35, P(root=(0, -10), lean=-40, head=10, foot_front=(30, -96), foot_back=(-10, -90), hand_front=(40, 60),
                        hand_back=(-60, 70), planted=False, eyes="wide", mouth="open")),
               (0.6, P(root=(0, -10), lean=-40, head=10, foot_front=(36, -94), foot_back=(-4, -92), hand_front=(40, 60),
                       hand_back=(-60, 70), planted=False, eyes="wide", mouth="open")),
               (1.0, P(root=(0, -40), foot_front=(20, 60), foot_back=(-30, 60), planted=False))],
    "wall_jump": [(0.0, P(lean=-4, hand_front=(78, -40), foot_front=(80, 40), foot_back=(-6, 76), planted=False, knee_forward=1)),
                  (0.4, P(root=(-20, -30), lean=-20, hand_front=(-20, -100), hand_back=(-80, -80), foot_front=(80, 60),
                          foot_back=(40, 70), planted=False, eyes="wide", mouth="open")),
                  (1.0, P(root=(-40, -50), lean=-10, hand_front=(10, -100), hand_back=(-60, -90), foot_front=(20, 70),
                          foot_back=(-30, 70), planted=False, eyes="wide"))],
    "ledge_climb": [(0.0, HANG),
                    (0.5, P(root=(20, -10), lean=20, hand_front=(30, 40), hand_back=(30, 50), foot_front=(20, 10),
                            foot_back=(-40, 60), planted=False, knee_forward=1, eyes="squint", mouth="flat")),
                    (1.0, P(root=(40, 0)))],
    "ledge_getup": [(0.0, HANG),
                    (0.5, P(root=(20, -10), lean=20, hand_front=(30, 40), hand_back=(30, 50), foot_front=(20, 10),
                            foot_back=(-40, 60), planted=False, knee_forward=1, eyes="squint", mouth="flat")),
                    (1.0, P(root=(40, 0)))],
    "ledge_getup_attack": [(0.0, HANG),
                           (0.4, P(root=(30, -10), lean=10, foot_front=(30, 30), planted=False, knee_forward=1)),
                           (0.6, P(root=(40, 0), lean=-14, foot_front=(118, -2), shoe_front_tilt=-20, eyes="squint", mouth="open")),
                           (1.0, P(root=(40, 0)))],
    "hit": [(0.0, P(lean=-10, eyes="closed", mouth="ouch")),
            (0.4, P(root=(-12, -6), lean=-24, head=-12, hand_front=(40, -90), hand_back=(-60, -90), quill_sway=10,
                    eyes="closed", mouth="ouch", knee_forward=0.6)),
            (1.0, P(root=(-6, 0), lean=-12, hand_front=(70, -30), hand_back=(-90, -30), eyes="closed", mouth="ouch"))],
    "death": [(0.0, P(lean=-12, eyes="dead", mouth="ouch")),
              (0.35, P(root=(0, -50), lean=-20, hand_front=(30, -100), hand_back=(-50, -100), foot_back=(-30, 70),
                       foot_front=(20, 70), planted=False, eyes="dead", mouth="ouch")),
              (0.75, P(root=(56, -24), lean=-75, head=10, hand_front=(60, -60), hand_back=(-20, -90), foot_back=(30, -80),
                       foot_front=(70, -70), planted=False, eyes="dead", mouth="ouch")),
              (1.0, P(root=(64, -36), lean=-84, head=12, hand_front=(80, -20), hand_back=(-10, -60), foot_back=(40, -90),
                      foot_front=(80, -76), planted=False, eyes="dead", mouth="ouch"))],
    "taunt": [(0.0, P(hand_front=(50, -60), eyes="squint", mouth="grin")),
              (0.25, P(hand_front=(70, -64), eyes="squint", mouth="grin", foot_front=(66, 56))),
              (0.5, P(hand_front=(46, -60), eyes="squint", mouth="grin")),
              (0.75, P(hand_front=(70, -64), eyes="squint", mouth="grin", foot_front=(66, 56))),
              (1.0, P(hand_front=(50, -60), eyes="squint", mouth="grin"))],
    "interact": [(0.0, P()), (0.5, P(lean=8, hand_front=(100, 4), glove_front=1.1, eyes="wide")), (1.0, P())],
}

# --- The fighter vocabulary -------------------------------------------------------
#
# The rest of a full fighter's body language (``data/fighter_motion_vocabulary.yaml``,
# scope ``fighter_core``): the stops and the turn, the squat and the landings,
# the hits by height, the launches by direction, the floor game, the guard,
# the ledge, the grab, and the rest. Each row is its own pose on this rig;
# a curl, a roll or a spin is the BALL, as his jump is. A launch trails its
# limbs opposite the way it flies; a recoil ends on its settled pose (the
# game holds a recoil's last frame for the hitstun); a body on the ground is
# stood on the floor (``on_floor``).


def _steps(*poses: Pose) -> Callable[[float], Pose]:
    """A row of exactly these frames (its ``ROWS`` count is ``len(poses)``)."""
    def row(t: float) -> Pose:
        return poses[min(len(poses) - 1, int(round(t * (len(poses) - 1))))]
    row.frames = len(poses)
    return row


def _cycle(*poses: Pose) -> Callable[[float], Pose]:
    """A looping row of exactly these frames."""
    def row(t: float) -> Pose:
        return poses[int(t * len(poses) + 1e-6) % len(poses)]
    row.frames = len(poses)
    return row


def _rolled(turn: float, at: Point = (0.0, 0.0), fx=()) -> Pose:
    """The ball ``turn`` turns round, on the floor."""
    return P(ball=True, turn=turn, ball_at=at, on_floor=True, fx=fx)


def _flung(turn: float, at: Point, fx=()) -> Pose:
    """The ball ``turn`` turns round, in the air at ``at``."""
    return P(ball=True, turn=turn, ball_at=at, fx=fx)


def _wave(t: float, k: float = 1.0, phase: float = 0.0) -> float:
    return math.sin(2 * math.pi * k * t + phase)


STAND = P()
SQUAT = P(root=(0, 38), lean=18, head=4, knee_forward=1, hand_front=(0, 60), hand_back=(-140, -30),
          eyes="squint", mouth="grin", quill_sway=-8)
#: Half way down into the crouch, or up out of it.
HALF_CROUCH = P(root=(0, 18), lean=5, head=3, foot_back=(-80, 62), foot_front=(52, 66), knee_forward=0.6,
                hand_front=(50, 30), hand_back=(-86, 46))
GUARD = ROW_FUNCS["block"](0.0)
GRAB_HOLD = P(root=(0, 4), lean=-2, hand_front=(84, 0), glove_front=1.3, hand_back=(-100, 10), knee_forward=0.3,
              eyes="squint", mouth="grin")
#: On his back: head to the back, belly up, the back quills splayed along the
#: floor, knees up.
FACE_UP = P(root=(80, 0), planted=False, on_floor=True, lean=-86, head=-8, quill_sway=24, hand_back=(-60, 40), hand_front=(-50, -60),
            foot_front=(96, -24), foot_back=(104, 6), knee_forward=1, eyes="closed", mouth="ouch")
#: On his belly: head forward, chin up off the floor, quills up off his back.
FACE_DOWN = P(root=(-30, 0), planted=False, on_floor=True, lean=86, head=-24, quill_sway=-10, hand_front=(60, 30),
              hand_back=(70, -20), foot_front=(-96, 46), foot_back=(-104, 26), shoe_front_tilt=80, shoe_back_tilt=-80,
              eyes="closed", mouth="ouch")
#: Sat on the floor, legs out ahead, knees up.
SIT = P(root=(20, 0), planted=False, on_floor=True, lean=-14, head=16, foot_front=(104, 20), foot_back=(90, 36),
        knee_forward=1, hand_front=(80, 40), hand_back=(-70, 60), eyes="dizzy", mouth="flat", quill_sway=-10)
SLEEP = replace(SIT, lean=6, head=34, hand_front=(70, 60), hand_back=(-50, 70), eyes="closed", mouth="flat",
                quill_sway=-16)
TECH_BRACE = P(root=(0, 40), lean=26, head=-12, knee_forward=1, foot_front=(50, 66), foot_back=(-90, 62),
               hand_front=(36, 96), hand_back=(-130, -40), eyes="squint", mouth="flat",
               quill_sway=14, fx=("dust",))
#: Waist deep in the ground: the mound covers where the body goes under.
BURIED = P(planted=False, legs=False, on_floor=True, hand_front=(80, -40), hand_back=(-90, -30), eyes="wide",
           mouth="open", fx=("dirt",))
VICTORY = P(lean=-8, head=-10, hand_back=(30, -140), glove_back=1.2, hand_front=(90, -50), foot_front=(80, 66),
            eyes="squint", mouth="grin", quill_sway=10)
SMASH_WIND = P(root=(-4, 10), lean=-16, head=-6, hand_back=(-150, -20), hand_front=(-40, -20), glove_front=1.4,
               knee_forward=0.6,
               foot_front=(84, 66), foot_back=(-110, 62), eyes="squint", mouth="grin", quill_sway=10)


def _teeter(t: float) -> Pose:
    """Toes on the edge, pitched out over it, the back foot up behind to
    balance and both arms wheeling."""
    a = 2 * math.pi * t
    return P(root=(0, 4), lean=20 + 6 * math.sin(a), head=8, foot_front=(40, 66), shoe_front_tilt=-12,
             foot_back=(-96, 18 + 10 * math.sin(a)), knee_forward=0.4,
             hand_front=(60 + 50 * math.cos(a), -50 + 50 * math.sin(a)),
             hand_back=(-60 + 50 * math.cos(a + math.pi), -70 + 50 * math.sin(a + math.pi)),
             quill_sway=-6 + 6 * math.sin(a), eyes="wide", mouth="ouch" if t < 0.5 else "open")


def _tumble(t: float) -> Pose:
    """Helpless after a launch: limbs flailing, dazed."""
    a = 2 * math.pi * t
    return P(root=(0, -50), planted=False, lean=-22 + 10 * math.sin(a), head=-10 + 8 * math.sin(a + 1),
             hand_front=(50 + 40 * math.cos(a), -70 + 30 * math.sin(a)),
             hand_back=(-80 + 40 * math.cos(a + math.pi), -60 + 30 * math.sin(a + math.pi)),
             foot_front=(70 + 20 * math.sin(a), 30), foot_back=(-10, 50 + 20 * math.cos(a)), knee_forward=1,
             eyes="dizzy", mouth="ouch", quill_sway=8 * math.sin(a))


def _grabbed(t: float) -> Pose:
    a = 2 * math.pi * t
    return P(root=(0, -18), planted=False, lean=-10 + 4 * math.sin(a), head=-10,
             hand_front=(60 + 20 * math.cos(a), -50 + 20 * math.sin(a)), hand_back=(-60, -70 + 20 * math.cos(a)),
             foot_front=(40 + 20 * math.sin(a), 70), foot_back=(-30, 74 - 10 * math.sin(a)),
             eyes="wide", mouth="open", quill_sway=4 * math.sin(a))


ROW_FUNCS.update({
    # --- the movement seen every second
    # The turn is drawn in the NEW facing: its first two frames are mirrored
    # (still facing the old way, braking), and it ends on the side view.
    "turnaround": _steps(
        P(mirror=True, lean=-10, head=-6, foot_front=(96, 66), foot_back=(-70, 62), hand_front=(40, -50),
          hand_back=(-60, -40), shoe_front_tilt=-14, eyes="wide", mouth="open", quill_sway=8, fx=("dust",)),
        P(mirror=True, root=(0, 14), lean=-4, knee_forward=0.6, foot_front=(40, 66), foot_back=(-50, 62),
          hand_front=(10, 40), hand_back=(-40, 40), eyes="wide", mouth="flat", quill_sway=-6),
        P(root=(0, 12), lean=10, knee_forward=0.6, foot_front=(30, 66), foot_back=(-70, 62), hand_front=(70, 10),
          hand_back=(-130, -10), quill_sway=12, eyes="squint", mouth="grin"),
        P(root=(0, 4), lean=6, hand_front=(80, 0), hand_back=(-120, 20), quill_sway=-4),
        STAND),
    "run_stop": _steps(
        P(root=(-6, 10), lean=-26, head=-10, foot_front=(120, 66), foot_back=(-30, 62), shoe_front_tilt=-24,
          knee_forward=0.4, hand_front=(90, -50), hand_back=(30, -90), eyes="wide", mouth="open", quill_sway=10,
          fx=("dust",)),
        P(root=(-2, 16), lean=-30, head=-12, foot_front=(124, 66), foot_back=(-24, 62), shoe_front_tilt=-26,
          knee_forward=0.5, hand_front=(100, -30), hand_back=(50, -80), eyes="wide", mouth="open", quill_sway=12,
          fx=("dust",)),
        P(root=(0, 6), lean=24, head=8, foot_front=(80, 66), foot_back=(-50, 62), hand_front=(120, -20),
          hand_back=(-140, -40), knee_forward=0.6, eyes="wide", mouth="ouch", quill_sway=-10),
        P(root=(0, 4), lean=12, foot_front=(76, 66), foot_back=(-60, 62), hand_front=(100, 0), hand_back=(-130, 0),
          eyes="derp", mouth="flat", quill_sway=-4),
        P(lean=-3, quill_sway=4),
        STAND),
    "jump_squat": _steps(
        P(root=(0, 16), lean=8, knee_forward=0.7, hand_front=(40, 30), hand_back=(-100, 0)),
        P(root=(0, 32), lean=16, head=6, knee_forward=1, hand_front=(10, 50), hand_back=(-130, -20), eyes="squint",
          quill_sway=-6),
        SQUAT),
    # Uncurls with a kick of the legs, then curls into the ball again.
    "double_jump": _steps(
        P(root=(0, -50), planted=False, lean=-6, hand_front=(70, -90), hand_back=(-60, -110), foot_front=(50, 50),
          foot_back=(-70, 60), eyes="wide", mouth="open", quill_sway=14),
        P(root=(0, -60), planted=False, lean=-10, head=-8, hand_front=(50, -110), hand_back=(-30, -120),
          foot_front=(30, 80), foot_back=(-40, 84), eyes="wide", mouth="grin", quill_sway=18),
        _flung(0.25, (0, -60)), _flung(0.5, (0, -60)), _flung(0.75, (0, -60)), _flung(1.0, (0, -60))),
    "land_light": _steps(
        P(root=(0, 14), lean=6, knee_forward=0.7, hand_front=(70, 20), hand_back=(-104, 10), quill_sway=-4),
        P(root=(0, 6), lean=3, knee_forward=0.4, quill_sway=2),
        STAND),
    "crouch_start": _steps(HALF_CROUCH, CROUCH),
    "crouch_end": _steps(HALF_CROUCH, STAND),
    "crouch_walk": lambda t: replace(
        CROUCH, root=(0, 36 + 3 * abs(_wave(t))),
        foot_back=(-60 + 28 * _wave(t), 60 - 12 * max(0.0, _wave(t, phase=math.pi / 2))),
        foot_front=(40 - 28 * _wave(t), 64 - 12 * max(0.0, -_wave(t, phase=math.pi / 2))),
        shoe_back_tilt=-4 * _wave(t), shoe_front_tilt=4 * _wave(t), quill_sway=2 * _wave(t)),
    "teeter": _teeter,
    "idle_look_up": lambda t: P(root=(0, 3 * math.sin(math.pi * t) ** 2), head=-26, hand_front=(70, 2 + 3 * _wave(t)),
                                eyes="wide", mouth="flat", quill_sway=-4 + 2 * _wave(t)),
    # Helpless after an up-special: slumped, head hung, limbs limp and spread.
    "fall_special": lambda t: P(root=(0, -40), planted=False, lean=12, head=22 + 4 * _wave(t),
                                hand_front=(84, -54 + 10 * _wave(t)), hand_back=(-96, -44 - 10 * _wave(t)),
                                foot_front=(30, 90), foot_back=(-40, 86), shoe_front_tilt=40, shoe_back_tilt=-40,
                                eyes="dizzy", mouth="flat", quill_sway=16 + 4 * _wave(t)),

    # --- struck
    "hit_high": _steps(
        P(root=(-4, -2), lean=-6, head=-44, hand_front=(90, -60), hand_back=(-130, -30), foot_front=(70, 56),
          shoe_front_tilt=-24, quill_sway=26, eyes="closed", mouth="ouch"),
        P(root=(-8, -4), lean=-8, head=-56, hand_front=(100, -80), hand_back=(-136, -50), foot_front=(74, 50),
          shoe_front_tilt=-30, quill_sway=32, eyes="closed", mouth="open"),
        P(root=(-8, -2), lean=-7, head=-46, hand_front=(96, -66), hand_back=(-134, -36), foot_front=(72, 56),
          shoe_front_tilt=-22, quill_sway=26, eyes="closed", mouth="ouch"),
        P(root=(-6, 0), lean=-6, head=-40, hand_front=(90, -54), hand_back=(-130, -26), foot_front=(70, 62),
          shoe_front_tilt=-14, quill_sway=22, eyes="closed", mouth="ouch")),
    # Doubled over the belly: the hips pushed back over planted feet.
    "hit_mid": _steps(
        P(root=(-12, 10), lean=22, head=14, hand_front=(30, 60), hand_back=(30, 50), foot_front=(78, 66),
          foot_back=(-88, 62), knee_forward=0.6, eyes="wide", mouth="open", quill_sway=-6),
        P(root=(-18, 18), lean=32, head=20, hand_front=(16, 72), hand_back=(20, 64), foot_front=(84, 66),
          foot_back=(-82, 62), knee_forward=0.8, eyes="wide", mouth="open", quill_sway=-12),
        P(root=(-16, 16), lean=28, head=18, hand_front=(24, 66), hand_back=(20, 60), foot_front=(82, 66),
          foot_back=(-84, 62), knee_forward=0.8, eyes="closed", mouth="ouch", quill_sway=-10),
        P(root=(-14, 14), lean=25, head=16, hand_front=(30, 62), hand_back=(20, 58), foot_front=(80, 66),
          foot_back=(-86, 62), knee_forward=0.7, eyes="closed", mouth="ouch", quill_sway=-8)),
    # The front foot knocked out behind him: he pitches forward onto the back foot.
    "hit_low": _steps(
        P(root=(-8, 6), lean=20, head=-8, foot_front=(-30, 26), shoe_front_tilt=30, foot_back=(-92, 62),
          hand_front=(90, -60), hand_back=(-40, -100), eyes="wide", mouth="ouch", quill_sway=10),
        P(root=(-14, 12), lean=28, head=-12, foot_front=(-60, 14), shoe_front_tilt=44, foot_back=(-86, 62),
          hand_front=(116, -70), hand_back=(-10, -116), eyes="wide", mouth="ouch", quill_sway=14),
        P(root=(-12, 12), lean=25, head=-8, foot_front=(-40, 26), shoe_front_tilt=30, foot_back=(-88, 62),
          hand_front=(110, -50), hand_back=(-30, -104), knee_forward=0.3, eyes="wide", mouth="ouch", quill_sway=10),
        P(root=(-10, 10), lean=22, head=-6, foot_front=(-24, 36), shoe_front_tilt=20, foot_back=(-90, 62),
          hand_front=(104, -40), hand_back=(-50, -92), knee_forward=0.4, eyes="wide", mouth="ouch", quill_sway=8)),
    "hit_air": _steps(
        P(root=(0, -40), planted=False, lean=-28, head=-14, hand_front=(-20, -90), hand_back=(-90, -60),
          foot_front=(70, 40), foot_back=(30, 60), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=14),
        P(root=(8, -42), planted=False, lean=-36, head=-18, hand_front=(-40, -96), hand_back=(-100, -50),
          foot_front=(84, 30), foot_back=(40, 54), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=18),
        P(root=(-4, -42), planted=False, lean=-30, head=-14, hand_front=(-20, -90), hand_back=(-96, -54),
          foot_front=(74, 38), foot_back=(30, 58), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=14),
        P(root=(-2, -40), planted=False, lean=-24, head=-10, hand_front=(0, -80), hand_back=(-90, -50),
          foot_front=(60, 48), foot_back=(20, 62), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=10)),

    # --- launched: limbs trail opposite the flight
    "launch_up": _steps(
        P(root=(0, -40), planted=False, lean=-16, head=-24, hand_front=(30, -80), hand_back=(-70, -70),
          foot_front=(40, 70), foot_back=(-20, 74), eyes="closed", mouth="ouch", quill_sway=10),
        P(root=(0, -70), planted=False, lean=-8, head=-26, hand_front=(30, 100), hand_back=(-24, 104),
          foot_front=(-6, 104), foot_back=(-20, 102), shoe_front_tilt=70, shoe_back_tilt=-70, eyes="closed",
          mouth="open", quill_sway=-22),
        P(root=(0, -72), planted=False, lean=-6, head=-28, hand_front=(36, 98), hand_back=(-30, 102),
          foot_front=(-2, 104), foot_back=(-16, 103), shoe_front_tilt=74, shoe_back_tilt=-74, eyes="closed",
          mouth="open", quill_sway=-26),
        P(root=(0, -70), planted=False, lean=-8, head=-24, hand_front=(28, 100), hand_back=(-20, 104),
          foot_front=(-8, 104), foot_back=(-22, 102), shoe_front_tilt=70, shoe_back_tilt=-70, eyes="closed",
          mouth="open", quill_sway=-22)),
    "launch_horizontal": _steps(
        P(root=(10, -40), planted=False, lean=-30, head=-10, hand_front=(60, -40), hand_back=(-40, -60),
          foot_front=(80, 40), foot_back=(40, 60), eyes="closed", mouth="ouch", quill_sway=10),
        P(root=(40, -50), planted=False, lean=-60, head=22, hand_front=(104, 20), hand_back=(90, -10),
          foot_front=(106, 4), foot_back=(98, 30), knee_forward=0.3, eyes="closed", mouth="ouch", quill_sway=-8),
        P(root=(40, -50), planted=False, lean=-62, head=24, hand_front=(106, 26), hand_back=(94, -16),
          foot_front=(106, 0), foot_back=(100, 26), knee_forward=0.3, eyes="closed", mouth="ouch", quill_sway=-10),
        P(root=(40, -50), planted=False, lean=-58, head=20, hand_front=(102, 16), hand_back=(88, -6),
          foot_front=(104, 8), foot_back=(96, 32), knee_forward=0.3, eyes="closed", mouth="ouch", quill_sway=-6)),
    # Spiked: folded forward, head down, arms and legs flung up behind.
    "launch_down": _steps(
        P(root=(0, -40), planted=False, lean=20, head=10, hand_front=(40, -80), hand_back=(-40, -90),
          foot_front=(10, 60), foot_back=(-40, 50), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=10),
        P(root=(0, -60), planted=False, lean=44, head=22, hand_front=(10, -104), hand_back=(-40, -100),
          foot_back=(-70, -50), foot_front=(-40, -64), knee_forward=1, eyes="wide", mouth="open", quill_sway=22),
        P(root=(0, -60), planted=False, lean=48, head=24, hand_front=(4, -106), hand_back=(-46, -98),
          foot_back=(-74, -46), foot_front=(-44, -60), knee_forward=1, eyes="wide", mouth="open", quill_sway=26),
        P(root=(0, -60), planted=False, lean=44, head=20, hand_front=(14, -102), hand_back=(-36, -100),
          foot_back=(-68, -52), foot_front=(-38, -66), knee_forward=1, eyes="wide", mouth="open", quill_sway=22)),
    # The plain launch (what a sheet without a direction draws): thrown up
    # and back, limbs trailing down and ahead.
    "launch": _steps(
        P(root=(0, -40), planted=False, lean=-22, head=-14, hand_front=(40, -70), hand_back=(-60, -70),
          foot_front=(60, 50), foot_back=(10, 66), eyes="closed", mouth="ouch", quill_sway=10),
        P(root=(-6, -56), planted=False, lean=-36, head=8, hand_front=(90, 60), hand_back=(60, 74),
          foot_front=(90, 64), foot_back=(56, 84), eyes="closed", mouth="ouch", quill_sway=-4),
        P(root=(-6, -58), planted=False, lean=-38, head=10, hand_front=(94, 56), hand_back=(64, 70),
          foot_front=(92, 60), foot_back=(60, 80), eyes="closed", mouth="ouch", quill_sway=-6),
        P(root=(-6, -56), planted=False, lean=-34, head=6, hand_front=(88, 62), hand_back=(58, 76),
          foot_front=(88, 66), foot_back=(54, 86), eyes="closed", mouth="ouch", quill_sway=-2)),
    # Driven straight down head first, legs straight up: a spear, not a fold.
    "meteor": _steps(
        P(root=(0, -120), planted=False, lean=120, head=10, hand_front=(-60, -80), hand_back=(-80, -60),
          foot_front=(-60, -80), foot_back=(-80, -70), eyes="wide", mouth="open", quill_sway=20),
        P(root=(0, -186), planted=False, lean=168, head=0, hand_front=(-10, -100), hand_back=(14, -100),
          foot_front=(-8, -104), foot_back=(10, -104), eyes="closed", mouth="ouch", quill_sway=30),
        P(root=(0, -184), planted=False, lean=172, head=2, hand_front=(-14, -100), hand_back=(18, -98),
          foot_front=(-4, -104), foot_back=(14, -104), eyes="closed", mouth="ouch", quill_sway=32)),
    "tumble": _tumble,

    # --- the floor game
    "knockdown": _steps(
        P(root=(40, 0), planted=False, on_floor=True, lean=-50, head=-10, hand_front=(30, -90), hand_back=(-60, -80),
          foot_front=(100, 0), foot_back=(80, 20), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=14),
        replace(FACE_UP, lean=-84, hand_front=(-20, -100), hand_back=(-70, -20), foot_front=(80, -70),
                foot_back=(100, -40), quill_sway=20),
        replace(FACE_UP, lean=-88, hand_front=(-40, -80), hand_back=(-66, 30), foot_front=(92, -40),
                foot_back=(104, -10)),
        FACE_UP),
    # The plain prone: flat on his back, limbs out, out cold.
    "prone": _cycle(
        P(root=(80, 0), planted=False, on_floor=True, lean=-88, head=-4, quill_sway=24, hand_back=(-90, 20),
          hand_front=(-90, -40), foot_front=(106, 6), foot_back=(104, 24), eyes="closed", mouth="flat"),
        P(root=(80, 0), planted=False, on_floor=True, lean=-88, head=-6, quill_sway=24, hand_back=(-90, 20),
          hand_front=(-88, -46),
          foot_front=(106, 6), foot_back=(104, 24), eyes="closed", mouth="flat")),
    # On his back, knees up, his head lolling, dazed.
    "prone_face_up": _cycle(
        replace(FACE_UP, eyes="dizzy", mouth="flat"),
        replace(FACE_UP, eyes="dizzy", mouth="flat", head=-12, hand_front=(-46, -66)),
        replace(FACE_UP, eyes="dizzy", mouth="flat", head=-10, hand_front=(-48, -62)),
        replace(FACE_UP, eyes="dizzy", mouth="flat", head=-4, hand_front=(-52, -58))),
    "prone_face_down": _cycle(
        FACE_DOWN,
        replace(FACE_DOWN, head=-28, quill_sway=-12),
        replace(FACE_DOWN, head=-26, quill_sway=-8),
        replace(FACE_DOWN, head=-20, quill_sway=-8)),
    "prone_damage": _steps(
        replace(FACE_UP, lean=-72, head=-22, hand_front=(-20, -104), hand_back=(-40, -60), foot_front=(80, -70),
                foot_back=(100, -46), quill_sway=30),
        replace(FACE_UP, lean=-80, head=-16, hand_front=(-30, -90), hand_back=(-56, -10), foot_front=(90, -50),
                foot_back=(104, -24)),
        FACE_UP),
    # Sits up, plants his feet, springs up.
    "getup": _steps(
        replace(FACE_UP, eyes="derp", mouth="flat"),
        P(planted=False, on_floor=True, lean=-40, head=10, hand_back=(-70, 60), hand_front=(40, 30),
          foot_front=(100, 30), foot_back=(80, 40), knee_forward=1, eyes="derp", mouth="flat"),
        replace(CROUCH, eyes="squint", mouth="flat"),
        P(root=(0, -4), lean=-6, hand_front=(80, -50), hand_back=(-120, -40), eyes="squint", mouth="grin",
          quill_sway=8),
        STAND),
    "getup_roll": _steps(
        replace(FACE_UP, eyes="squint", mouth="flat"),
        _rolled(-0.2), _rolled(-0.45), _rolled(-0.7), _rolled(-0.95),
        replace(CROUCH, eyes="squint", mouth="grin")),
    # Sat up, a low kick ahead, then round on a hand for a kick behind.
    "getup_attack": _steps(
        replace(FACE_UP, eyes="squint", mouth="flat"),
        P(root=(30, 0), planted=False, on_floor=True, lean=-50, head=12, hand_back=(-60, 70), hand_front=(-10, -60),
          foot_front=(128, 24), foot_back=(60, 50), knee_forward=0.2, eyes="squint", mouth="open", quill_sway=10,
          fx=("dust",)),
        P(planted=False, on_floor=True, lean=20, head=-10, hand_front=(30, 110), hand_back=(10, 112),
          foot_back=(-132, 0), foot_front=(-20, 40), knee_forward=0.5, eyes="squint", mouth="open", quill_sway=-6,
          fx=("dust",)),
        P(planted=False, on_floor=True, lean=14, head=-4, hand_front=(40, 104), hand_back=(20, 108),
          foot_back=(-120, 20), foot_front=(-10, 50), knee_forward=0.5, eyes="squint", mouth="grin"),
        replace(CROUCH, eyes="squint", mouth="grin"),
        STAND),
    # Caught the landing: low, a hand down on the floor, the other out.
    "tech": _steps(
        replace(TECH_BRACE, root=(0, 46), lean=30, hand_front=(36, 84)),
        TECH_BRACE,
        replace(TECH_BRACE, root=(0, 30), lean=18, hand_front=(44, 80), fx=()),
        P(root=(0, 10), lean=6, knee_forward=0.5, hand_front=(90, -20), hand_back=(-110, 10), eyes="squint",
          mouth="grin")),
    "tech_roll": _steps(
        TECH_BRACE,
        _rolled(0.25, fx=("dust",)), _rolled(0.5), _rolled(0.75),
        replace(CROUCH, eyes="squint", mouth="grin")),
    "trip_fall": _steps(
        P(root=(0, 4), lean=24, head=-6, foot_front=(-40, 30), shoe_front_tilt=30, hand_front=(120, -20),
          hand_back=(60, -60), eyes="wide", mouth="open", quill_sway=-8),
        P(planted=False, on_floor=True, lean=56, head=-24, hand_front=(100, 40), hand_back=(80, 20),
          foot_front=(-80, -10), foot_back=(-60, 10), eyes="wide", mouth="ouch"),
        replace(FACE_DOWN, hand_front=(80, 10), head=-30),
        FACE_DOWN),

    # --- the guard and the dodges
    "shield_hit": _steps(
        P(root=(-14, 14), lean=-12, head=-8, hand_front=(20, -14), hand_back=(84, -24), glove_front=1.2,
          foot_front=(80, 66), foot_back=(-86, 62), knee_forward=0.7, eyes="closed", mouth="ouch", quill_sway=10),
        P(root=(-12, 13), lean=-8, head=-6, hand_front=(26, -8), hand_back=(96, -16), glove_front=1.2,
          foot_front=(78, 66), foot_back=(-88, 62), knee_forward=0.65, eyes="squint", mouth="ouch", quill_sway=6),
        replace(GUARD, root=(-8, 12), foot_front=(74, 66), foot_back=(-92, 62))),
    "parry": _steps(
        GUARD,
        P(root=(0, 6), lean=10, hand_front=(130, -40), glove_front=1.8, hand_back=(-120, -60), foot_front=(84, 66),
          eyes="wide", mouth="grin", quill_sway=14),
        P(root=(0, 6), lean=12, hand_front=(132, -44), glove_front=1.9, hand_back=(-124, -64), foot_front=(84, 66),
          eyes="wide", mouth="grin", quill_sway=16),
        P(root=(0, 8), lean=4, hand_front=(90, -10), glove_front=1.3, hand_back=(-110, -10), knee_forward=0.4,
          eyes="squint", mouth="grin")),
    "roll": _steps(
        replace(CROUCH, root=(0, 40), lean=24, head=14, hand_front=(30, 40), eyes="squint"),
        _rolled(0.15), _rolled(0.4), _rolled(0.65), _rolled(0.9),
        replace(CROUCH, lean=-2, hand_back=(-80, 30), eyes="squint", mouth="grin")),
    "roll_back": _steps(
        replace(CROUCH, root=(0, 36), lean=-10, head=-10, hand_front=(60, 10), hand_back=(-60, 20), eyes="squint"),
        _rolled(-0.15), _rolled(-0.4), _rolled(-0.65), _rolled(-0.9),
        replace(CROUCH, lean=14, eyes="squint", mouth="grin")),
    # Sucked in, quills flat, eyes shut: it goes past him.
    "spot_dodge": _steps(
        P(root=(0, 18), lean=-6, head=-4, hand_front=(10, 20), hand_back=(-30, 10), knee_forward=0.6,
          foot_front=(40, 66), foot_back=(-70, 62), eyes="closed", mouth="flat", quill_sway=-14),
        P(root=(0, 26), lean=-10, head=-6, hand_front=(0, 24), hand_back=(-20, 16), knee_forward=0.7,
          foot_front=(36, 66), foot_back=(-66, 62), eyes="closed", mouth="flat", quill_sway=-18),
        P(root=(0, 10), lean=2, hand_front=(60, 0), hand_back=(-90, 20), knee_forward=0.4, eyes="squint",
          mouth="grin", quill_sway=6),
        STAND),
    "air_dodge": _steps(
        P(root=(0, -40), planted=False, lean=4, head=6, hand_front=(50, 20), hand_back=(-50, 30), foot_front=(40, 40),
          foot_back=(-10, 50), knee_forward=1, eyes="closed", mouth="flat", quill_sway=-6),
        P(root=(0, -44), planted=False, lean=10, head=12, hand_front=(30, 24), hand_back=(60, 10),
          foot_front=(40, -10), foot_back=(14, 0), knee_forward=1, eyes="closed", mouth="flat", quill_sway=-12),
        P(root=(0, -44), planted=False, lean=12, head=12, hand_front=(28, 26), hand_back=(58, 12),
          foot_front=(38, -12), foot_back=(12, -2), knee_forward=1, eyes="closed", mouth="flat", quill_sway=-12),
        P(root=(0, -40), planted=False, lean=-4, hand_front=(70, -40), hand_back=(-80, -30), foot_front=(30, 60),
          foot_back=(-30, 66), eyes="squint", mouth="grin", quill_sway=6)),

    # --- the ledge
    "ledge_catch": _steps(
        P(root=(0, -16), planted=False, lean=14, hand_front=(30, -110), hand_back=(70, -104), foot_front=(60, 50),
          foot_back=(20, 70), eyes="wide", mouth="open", quill_sway=14),
        P(root=(0, -16), planted=False, lean=6, hand_front=(26, -108), hand_back=(70, -100), foot_front=(30, 64),
          foot_back=(-20, 72), eyes="wide", mouth="flat", quill_sway=10),
        HANG),
    "ledge_jump": _steps(
        HANG,
        P(root=(10, -40), planted=False, lean=10, hand_front=(10, -60), hand_back=(40, -60), foot_front=(40, 20),
          foot_back=(0, 40), knee_forward=1, eyes="squint", mouth="grin"),
        _flung(0.25, (20, -80)), _flung(0.55, (20, -80)), _flung(0.85, (20, -80))),
    "ledge_drop": _steps(
        HANG,
        P(root=(0, 10), planted=False, hand_front=(30, -110), hand_back=(60, -100), foot_front=(10, 80),
          foot_back=(-30, 80), eyes="wide", mouth="open", quill_sway=10),
        ROW_FUNCS["fall"](0.0)),

    # --- the grab
    "grab": _steps(
        P(lean=4, hand_front=(60, -10), eyes="squint"),
        P(root=(6, 4), lean=14, head=-4, hand_front=(130, -6), glove_front=1.5, hand_back=(-60, -20),
          foot_front=(90, 66), eyes="wide", mouth="open"),
        P(root=(6, 4), lean=14, head=-4, hand_front=(132, -4), glove_front=1.5, hand_back=(-60, -20),
          foot_front=(90, 66), eyes="wide", mouth="open"),
        P(lean=6, hand_front=(90, 4), glove_front=1.3, eyes="squint", mouth="grin"),
        GRAB_HOLD),
    "grab_hold": lambda t: replace(GRAB_HOLD, hand_front=(84, 2 * _wave(t)), quill_sway=2 * _wave(t)),
    # Squeezed in, then a swollen glove to the face.
    "pummel": _steps(
        replace(GRAB_HOLD, hand_front=(40, 10), hand_back=(-140, 0), lean=-6),
        replace(GRAB_HOLD, hand_front=(124, -4), glove_front=1.7, lean=10, eyes="wide", mouth="open"),
        GRAB_HOLD),
    "grab_release": _steps(
        replace(GRAB_HOLD, hand_front=(110, -10), glove_front=1.2, lean=6, mouth="flat"),
        P(root=(-8, 4), lean=-6, hand_front=(80, -30), hand_back=(-110, 10), eyes="derp", mouth="flat"),
        STAND),
    "throw_forward": _steps(
        GRAB_HOLD,
        P(root=(-6, 6), lean=-14, hand_front=(30, 10), hand_back=(-60, 0), glove_front=1.3, eyes="squint"),
        P(root=(10, 4), lean=24, head=-6, hand_front=(140, -10), hand_back=(110, -10), glove_front=1.4,
          glove_back=1.2, foot_front=(100, 66), eyes="wide", mouth="open"),
        P(root=(10, 4), lean=22, head=-6, hand_front=(136, -6), hand_back=(108, -6), glove_front=1.4,
          glove_back=1.2, foot_front=(100, 66), eyes="squint", mouth="grin"),
        P(lean=6, hand_front=(90, 0))),
    "throw_back": _steps(
        GRAB_HOLD,
        P(lean=-10, head=-14, hand_front=(10, -90), hand_back=(-40, -90), glove_front=1.3, eyes="squint",
          mouth="open"),
        P(lean=-26, head=-20, hand_front=(-130, -30), hand_back=(-150, -10), glove_front=1.3, foot_back=(-130, 62),
          eyes="wide", mouth="open", quill_sway=12),
        P(lean=-24, head=-18, hand_front=(-126, -20), hand_back=(-146, 0), glove_front=1.3, foot_back=(-130, 62),
          eyes="squint", mouth="grin", quill_sway=10),
        P(lean=-8, hand_front=(40, 0), hand_back=(-120, 20)),
        STAND),
    "throw_up": _steps(
        GRAB_HOLD,
        P(root=(0, 18), lean=10, hand_front=(70, 40), hand_back=(40, 40), glove_front=1.3, knee_forward=0.8,
          eyes="squint"),
        P(root=(0, -8), lean=-12, head=-20, hand_front=(30, -140), hand_back=(10, -130), glove_front=1.4,
          eyes="wide", mouth="open", quill_sway=14),
        P(root=(0, -6), lean=-10, head=-22, hand_front=(26, -136), hand_back=(8, -128), glove_front=1.3,
          eyes="squint", mouth="grin", quill_sway=12),
        STAND),
    "throw_down": _steps(
        GRAB_HOLD,
        P(root=(0, -6), lean=-8, head=-10, hand_front=(30, -120), hand_back=(0, -120), glove_front=1.3,
          eyes="squint"),
        P(root=(0, 30), lean=30, head=10, hand_front=(80, 80), hand_back=(50, 90), glove_front=1.4, knee_forward=1,
          eyes="squint", mouth="open", fx=("dust",)),
        P(root=(0, 28), lean=28, head=10, hand_front=(78, 76), hand_back=(48, 86), knee_forward=1, eyes="squint",
          mouth="grin"),
        STAND),
    "grabbed": _grabbed,
    "grabbed_pummel": _steps(
        P(root=(-6, -18), planted=False, lean=-20, head=-24, hand_front=(30, -80), hand_back=(-80, -60),
          foot_front=(60, 50), foot_back=(-30, 74), eyes="closed", mouth="ouch", quill_sway=12),
        P(root=(-4, -18), planted=False, lean=-16, head=-18, hand_front=(40, -70), hand_back=(-76, -64),
          foot_front=(56, 56), foot_back=(-30, 74), eyes="closed", mouth="ouch", quill_sway=8),
        replace(_grabbed(0.0), eyes="closed", mouth="ouch")),
    "grab_escape": _steps(
        _grabbed(0.25),
        P(root=(-14, -30), planted=False, lean=-20, foot_front=(80, 30), foot_back=(40, 50), knee_forward=1,
          hand_front=(20, -90), hand_back=(-80, -70), eyes="squint", mouth="open"),
        P(root=(-6, 14), lean=-8, knee_forward=0.6, eyes="derp", mouth="flat"),
        STAND),

    # --- attacks
    "dash_attack": _steps(
        P(root=(0, 10), lean=14, knee_forward=0.6, foot_front=(40, 66), hand_front=(40, 20), hand_back=(-120, -10),
          eyes="squint"),
        P(planted=False, on_floor=True, lean=-34, head=10, foot_front=(124, 20), foot_back=(20, 60),
          hand_back=(-70, 70), hand_front=(-20, -60), eyes="squint", mouth="grin", fx=("dust",)),
        P(planted=False, on_floor=True, lean=-36, head=12, foot_front=(126, 18), foot_back=(18, 60),
          hand_back=(-72, 70), hand_front=(-24, -62), eyes="squint", mouth="grin", fx=("dust",)),
        P(planted=False, on_floor=True, lean=-32, head=10, foot_front=(120, 24), foot_back=(20, 62),
          hand_back=(-70, 72), hand_front=(-16, -56), eyes="squint", mouth="grin", fx=("dust",)),
        replace(CROUCH, eyes="squint", mouth="grin"),
        STAND),
    "smash_charge": lambda t: replace(SMASH_WIND, root=(-4 + 3 * _wave(t, 2), 10), glove_front=1.4 + 0.15 * _wave(t),
                                      quill_sway=10 + 4 * _wave(t)),
})

ROW_KEYS.update({
    "walk_stop": [(0.0, P(foot_front=(36, 66), foot_back=(-70, 62), lean=7, hand_front=(60, 24), hand_back=(-96, 14),
                          quill_sway=-3)),
                  (0.5, P(root=(0, 6), foot_front=(50, 66), foot_back=(-90, 62), lean=-3, hand_front=(84, 0),
                          hand_back=(-118, 36), quill_sway=6, knee_forward=0.3)),
                  (1.0, STAND)],
    "teeter_start": [(0.0, STAND),
                     (0.4, P(lean=28, head=10, foot_back=(-70, 40), foot_front=(40, 66), hand_front=(110, -20),
                             hand_back=(40, -40), eyes="wide", mouth="open")),
                     (1.0, _teeter(0.0))],
    "shield_raise": [(0.0, P(root=(0, 4), hand_front=(60, 0), hand_back=(-20, 0), eyes="squint")), (1.0, GUARD)],
    "shield_release": [(0.0, GUARD), (1.0, STAND)],
    "smash_forward": [(0.0, SMASH_WIND),
                      (0.3, P(root=(12, 10), lean=24, head=-4, hand_front=(150, -14), glove_front=2.3,
                              hand_back=(-140, 10), foot_front=(96, 66), foot_back=(-80, 62), eyes="wide", mouth="open",
                              quill_sway=-12, on_floor=True)),
                      (0.6, P(root=(12, 10), lean=24, head=-4, hand_front=(152, -12), glove_front=2.3,
                              hand_back=(-140, 12), foot_front=(96, 66), foot_back=(-80, 62), eyes="wide", mouth="open",
                              quill_sway=-12, on_floor=True)),
                      (1.0, P(lean=8, hand_front=(80, 10), glove_front=1.2))],
    "smash_up": [(0.0, P(root=(0, 30), lean=12, knee_forward=1, hand_front=(40, 40), hand_back=(-60, 50), eyes="squint")),
                 (0.35, P(root=(0, -10), lean=-12, head=-24, hand_front=(30, -140), hand_back=(60, -130), glove_back=1.3,
                          glove_front=1.4, foot_back=(-80, 40), eyes="wide", mouth="open", quill_sway=16)),
                 (0.6, P(root=(0, -10), lean=-12, head=-24, hand_front=(32, -140), hand_back=(62, -128), glove_back=1.3,
                         glove_front=1.4, foot_back=(-80, 40), eyes="wide", mouth="open", quill_sway=16)),
                 (1.0, STAND)],
    # The splits: a kick out to each side at once, flat on the floor.
    "smash_down": [(0.0, replace(CROUCH, on_floor=True)),
                   (0.35, P(root=(0, 64), foot_front=(130, 62), foot_back=(-140, 58), shoe_front_tilt=-10,
                            shoe_back_tilt=10, hand_front=(60, -70), hand_back=(-60, -80), eyes="squint", mouth="open",
                            quill_sway=10, fx=("dust",), on_floor=True)),
                   (0.6, P(root=(0, 64), foot_front=(132, 62), foot_back=(-142, 58), shoe_front_tilt=-10,
                           shoe_back_tilt=10, hand_front=(60, -74), hand_back=(-60, -84), eyes="squint", mouth="grin",
                           quill_sway=10, on_floor=True)),
                   (1.0, replace(CROUCH, on_floor=True))],
})

ROW_FUNCS.update({
    "air_land": _steps(
        P(root=(0, 26), lean=-6, head=-4, knee_forward=1, hand_front=(90, -40), hand_back=(-120, -50), eyes="squint",
          mouth="open", quill_sway=10),
        P(root=(0, 14), knee_forward=0.6, hand_front=(80, -10), hand_back=(-120, 0), quill_sway=4),
        STAND),
    # Slammed flat against a wall behind him.
    "impact": _steps(
        P(root=(-24, -24), planted=False, lean=-6, head=-12, hand_front=(-40, -80), hand_back=(-20, -90),
          foot_front=(10, 74), foot_back=(-20, 76), eyes="closed", mouth="ouch", quill_sway=-20),
        P(root=(-30, -24), planted=False, lean=-2, head=-8, hand_front=(-50, -90), hand_back=(-30, -96),
          foot_front=(0, 76), foot_back=(-24, 76), eyes="closed", mouth="ouch", quill_sway=-24),
        P(root=(-26, -20), planted=False, lean=-8, head=-2, hand_front=(-30, -60), hand_back=(-40, -70),
          foot_front=(20, 70), foot_back=(-16, 76), eyes="dizzy", mouth="ouch", quill_sway=-16),
        P(root=(-22, -16), planted=False, lean=-10, head=4, hand_front=(-10, -40), hand_back=(-50, -50),
          foot_front=(30, 70), foot_back=(-10, 76), eyes="dizzy", mouth="ouch", quill_sway=-12)),
    # Spread-eagled, pancaked on a wall.
    "splat": _steps(
        P(root=(0, -40), planted=False, hand_front=(100, -70), hand_back=(-110, -80), foot_front=(90, 60),
          foot_back=(-100, 50), eyes="closed", mouth="ouch", quill_sway=-16),
        P(root=(0, -36), planted=False, hand_front=(100, -66), hand_back=(-110, -76), foot_front=(90, 62),
          foot_back=(-100, 52), eyes="dizzy", mouth="ouch", quill_sway=-18),
        P(root=(0, -30), planted=False, hand_front=(96, -60), hand_back=(-106, -70), foot_front=(86, 66),
          foot_back=(-96, 56), eyes="dizzy", mouth="ouch", quill_sway=-20)),
    "ground_bounce": _steps(
        replace(FACE_UP, lean=-80, hand_front=(-20, -110), hand_back=(20, -100), foot_front=(90, -60),
                foot_back=(70, -80), quill_sway=30),
        P(root=(30, -60), planted=False, lean=-60, head=10, hand_front=(-20, -100), hand_back=(30, -100),
          foot_front=(90, -40), foot_back=(80, -60), knee_forward=1, eyes="closed", mouth="ouch", quill_sway=20),
        P(root=(20, -80), planted=False, lean=-40, head=6, hand_front=(10, -90), hand_back=(-40, -90),
          foot_front=(90, 0), foot_back=(70, -20), knee_forward=1, eyes="dizzy", mouth="ouch", quill_sway=10),
        P(root=(0, -70), planted=False, lean=-30, head=0, hand_front=(30, -80), hand_back=(-60, -80),
          foot_front=(80, 30), foot_back=(50, 20), knee_forward=1, eyes="dizzy", mouth="ouch", quill_sway=6)),
    "wall_tech": _steps(
        P(root=(-10, -30), planted=False, lean=-10, head=6, foot_front=(90, 0), foot_back=(70, 20), knee_forward=1,
          hand_front=(80, -50), hand_back=(100, -40), eyes="squint", mouth="flat", quill_sway=12),
        P(root=(-4, -30), planted=False, lean=-4, head=8, foot_front=(84, 4), foot_back=(66, 24), knee_forward=1,
          hand_front=(76, -46), hand_back=(96, -36), eyes="squint", mouth="flat", quill_sway=16),
        P(root=(-8, -30), planted=False, lean=-8, head=6, foot_front=(88, 2), foot_back=(68, 22), knee_forward=1,
          hand_front=(78, -48), hand_back=(98, -38), eyes="squint", mouth="grin", quill_sway=12)),
    "wall_tech_jump": _steps(
        P(root=(-4, -30), planted=False, lean=-4, head=8, foot_front=(84, 4), foot_back=(66, 24), knee_forward=1,
          hand_front=(76, -46), hand_back=(96, -36), eyes="squint", mouth="flat", quill_sway=16),
        P(root=(-30, -50), planted=False, lean=-24, foot_front=(110, 30), foot_back=(100, 50), hand_front=(-60, -90),
          hand_back=(-100, -60), eyes="wide", mouth="grin", quill_sway=-8),
        _flung(-0.3, (-40, -70)), _flung(-0.6, (-40, -70))),
    "ceiling_tech": _steps(
        P(root=(0, -42), planted=False, lean=-6, head=12, hand_front=(30, -120), hand_back=(50, -118),
          foot_front=(40, -30), foot_back=(0, -20), knee_forward=1, eyes="squint", mouth="flat", quill_sway=-8),
        P(root=(0, -38), planted=False, lean=-2, head=14, hand_front=(28, -116), hand_back=(48, -114),
          foot_front=(44, -34), foot_back=(4, -24), knee_forward=1, eyes="squint", mouth="flat", quill_sway=-10),
        P(root=(0, -34), planted=False, lean=-4, head=6, hand_front=(40, -90), hand_back=(-40, -90),
          foot_front=(40, 40), foot_back=(-20, 50), knee_forward=1, eyes="squint", mouth="grin", quill_sway=4)),

    # --- the guard broken, sleep, buried
    "shield_break_launch": _steps(
        P(root=(0, -50), planted=False, lean=-20, head=-30, hand_front=(80, -60), hand_back=(-80, -70),
          foot_front=(40, 70), foot_back=(-30, 74), eyes="wide", mouth="open", quill_sway=12),
        P(root=(0, -70), planted=False, lean=-14, head=-30, hand_front=(70, 84), hand_back=(-70, 84),
          foot_front=(34, 96), foot_back=(-44, 90), eyes="dizzy", mouth="open", quill_sway=-16),
        P(root=(0, -72), planted=False, lean=-10, head=-34, hand_front=(74, 80), hand_back=(-66, 88),
          foot_front=(30, 98), foot_back=(-40, 92), eyes="dizzy", mouth="open", quill_sway=-18),
        P(root=(0, -70), planted=False, lean=-12, head=-28, hand_front=(66, 86), hand_back=(-72, 82),
          foot_front=(36, 94), foot_back=(-46, 88), eyes="dizzy", mouth="open", quill_sway=-14)),
    "shield_break_fall": lambda t: P(root=(0, -40), planted=False, lean=-10 + 3 * _wave(t), head=20,
                                     hand_front=(30, -100), hand_back=(-30, -104 + 6 * _wave(t)), foot_front=(10, 60),
                                     foot_back=(-40, 50), knee_forward=0.5, eyes="dizzy", mouth="open",
                                     quill_sway=18 + 3 * _wave(t)),
    "shield_break_collapse": _steps(
        P(root=(0, 14), lean=10, head=20, knee_forward=0.6, hand_front=(40, 70), hand_back=(-40, 80), eyes="dizzy",
          mouth="flat", quill_sway=-6),
        P(root=(0, 34), lean=14, head=24, knee_forward=1, hand_front=(40, 84), hand_back=(-30, 90), eyes="dizzy",
          mouth="flat", quill_sway=-10),
        replace(SIT, lean=4, head=22),
        SIT),
    "shield_break_recover": _steps(
        SIT,
        replace(CROUCH, eyes="dizzy", mouth="flat"),
        P(root=(0, 6), head=-14, hand_front=(10, -90), hand_back=(-110, 20), eyes="squint", mouth="flat",
          quill_sway=10),
        STAND),
    "dizzy": lambda t: P(root=(0, 6), lean=8 * _wave(t), head=10 + 14 * _wave(t, phase=1.0),
                         hand_front=(40, 60 + 10 * _wave(t)), hand_back=(-60, 70 - 10 * _wave(t)), knee_forward=0.4,
                         eyes="dizzy", mouth="open", quill_sway=6 * _wave(t)),
    "sleep_start": _steps(
        P(head=-16, hand_front=(30, -80), eyes="closed", mouth="open", quill_sway=4),
        P(root=(0, 20), lean=10, head=16, hand_front=(40, 50), hand_back=(-60, 70), knee_forward=0.8, eyes="closed",
          mouth="flat", quill_sway=-8),
        replace(SLEEP, lean=4, head=20, mouth="open"),
        SLEEP),
    "sleep": lambda t: replace(SLEEP, lean=12 + 2 * _wave(t), head=30 + 3 * _wave(t),
                               mouth="open" if t >= 0.5 else "flat"),
    "wake": _steps(
        SLEEP,
        replace(SIT, head=-20, eyes="wide", mouth="open", quill_sway=20, hand_front=(60, -40)),
        replace(CROUCH, eyes="wide", mouth="flat"),
        STAND),
    "bury_start": _steps(
        P(root=(0, 30), knee_forward=1, hand_front=(60, -80), hand_back=(-60, -90), eyes="closed", mouth="ouch",
          quill_sway=-10),
        replace(BURIED, eyes="closed", mouth="ouch", hand_front=(60, -80), hand_back=(-60, -90)),
        BURIED),
    "buried": _cycle(
        BURIED,
        replace(BURIED, hand_front=(90, -70), hand_back=(-100, -10), quill_sway=4),
        replace(BURIED, hand_front=(70, -10), hand_back=(-80, -60), quill_sway=-4)),
    "bury_escape": _steps(
        replace(BURIED, hand_front=(40, -110), hand_back=(-20, -110), eyes="squint"),
        P(root=(0, -30), planted=False, hand_front=(40, -110), hand_back=(-20, -114), foot_front=(20, 90),
          foot_back=(-30, 90), eyes="wide", mouth="open", quill_sway=10, fx=("dirt",)),
        _flung(0.3, (0, -60)), _flung(0.6, (0, -60))),
    "footstool_jump": _steps(
        P(root=(0, -30), planted=False, lean=-6, foot_front=(20, 100), foot_back=(-10, 96), hand_front=(60, -90),
          hand_back=(-60, -100), eyes="squint", mouth="grin", quill_sway=10),
        _flung(0.3, (0, -60)), _flung(0.6, (0, -60)), _flung(0.9, (0, -60))),
    "platform_drop": _steps(
        replace(CROUCH, eyes="derp"),
        P(root=(0, -10), planted=False, lean=-4, hand_front=(50, -80), hand_back=(-60, -90), foot_front=(20, 92),
          foot_back=(-20, 92), eyes="wide", mouth="open", quill_sway=10),
        ROW_FUNCS["fall"](0.0)),

    # --- the show
    # Drops in as the ball, and pops out of it.
    "entrance": _steps(
        _flung(0.0, (0, -150)), _flung(0.35, (0, -90)), _rolled(0.7),
        P(root=(0, -10), hand_front=(60, -100), hand_back=(-120, -60), eyes="wide", mouth="grin", quill_sway=12),
        P(hand_front=(50, -60), eyes="squint", mouth="grin"),
        P(hand_front=(70, -64), foot_front=(66, 56), eyes="squint", mouth="grin", on_floor=True)),
    "victory": _steps(
        _rolled(0.0), _rolled(0.5),
        P(root=(0, -10), lean=-4, hand_front=(80, -90), hand_back=(-80, -100), eyes="wide", mouth="grin",
          quill_sway=14),
        replace(VICTORY, hand_back=(10, -130)),
        VICTORY),
    "victory_hold": lambda t: replace(VICTORY, root=(0, 2 * abs(_wave(t))),
                                      foot_front=(80, 66 - 10 * max(0.0, _wave(t))),
                                      hand_back=(30, -140 + 4 * _wave(t))),
    "loss": lambda t: P(root=(0, 10), lean=18, head=26, hand_front=(30, 90), hand_back=(-40, 96), knee_forward=0.4,
                        eyes="closed", mouth="flat", quill_sway=-14 + 2 * _wave(t)),
})

LOOPS |= {"crouch_walk", "teeter", "idle_look_up", "fall_special", "tumble", "prone", "prone_face_up",
          "prone_face_down", "grab_hold", "grabbed", "smash_charge", "shield_break_fall", "dizzy", "sleep",
          "buried", "victory_hold", "loss"}

#: The fighter vocabulary's rows, after his own (``ROWS``).
FIGHTER_ROWS: List[Tuple[str, int, int]] = [
    ("idle_look_up", 4, 150),
    ("walk_stop", 4, 70),
    ("run_stop", 6, 60),
    ("turnaround", 5, 44),
    ("stumble", 5, 60),
    ("crouch_start", 2, 50),
    ("crouch_walk", 6, 90),
    ("crouch_end", 2, 50),
    ("jump_squat", 3, 40),
    ("double_jump", 6, 60),
    ("fall_special", 4, 100),
    ("land_light", 3, 60),
    ("air_land", 3, 60),
    ("teeter_start", 4, 60),
    ("teeter", 6, 90),
    ("hit_high", 4, 70),
    ("hit_mid", 4, 70),
    ("hit_low", 4, 70),
    ("hit_air", 4, 70),
    ("launch", 4, 70),
    ("launch_up", 4, 70),
    ("launch_horizontal", 4, 70),
    ("launch_down", 4, 70),
    ("meteor", 3, 70),
    ("tumble", 6, 90),
    ("impact", 4, 60),
    ("splat", 3, 80),
    ("ground_bounce", 4, 60),
    ("knockdown", 4, 80),
    ("prone", 2, 200),
    ("prone_face_up", 4, 160),
    ("prone_face_down", 4, 160),
    ("prone_damage", 3, 60),
    ("getup", 5, 80),
    ("getup_roll", 6, 60),
    ("getup_attack", 6, 60),
    ("tech", 4, 60),
    ("tech_roll", 5, 60),
    ("wall_tech", 3, 60),
    ("wall_tech_jump", 4, 60),
    ("ceiling_tech", 3, 60),
    ("trip_fall", 4, 70),
    ("shield_raise", 3, 50),
    ("shield_hit", 3, 60),
    ("shield_release", 3, 60),
    ("parry", 4, 60),
    ("roll", 6, 50),
    ("roll_back", 6, 50),
    ("spot_dodge", 4, 60),
    ("air_dodge", 4, 60),
    ("ledge_catch", 3, 60),
    ("ledge_jump", 5, 60),
    ("ledge_drop", 3, 60),
    ("grab", 5, 50),
    ("grab_hold", 3, 120),
    ("pummel", 3, 50),
    ("grab_release", 3, 70),
    ("throw_forward", 5, 60),
    ("throw_back", 6, 60),
    ("throw_up", 5, 60),
    ("throw_down", 5, 60),
    ("grabbed", 4, 100),
    ("grabbed_pummel", 3, 60),
    ("grab_escape", 4, 60),
    ("dash_attack", 6, 60),
    ("smash_charge", 4, 60),
    ("smash_forward", 6, 60),
    ("smash_up", 6, 60),
    ("smash_down", 6, 60),
    ("shield_break_launch", 4, 70),
    ("shield_break_fall", 3, 100),
    ("shield_break_collapse", 4, 80),
    ("shield_break_recover", 4, 80),
    ("dizzy", 6, 110),
    ("sleep_start", 4, 120),
    ("sleep", 4, 220),
    ("wake", 4, 80),
    ("bury_start", 3, 80),
    ("buried", 3, 140),
    ("bury_escape", 4, 60),
    ("footstool_jump", 4, 60),
    ("platform_drop", 3, 60),
    ("entrance", 6, 80),
    ("victory", 5, 90),
    ("victory_hold", 4, 140),
    ("loss", 4, 200),
]

ROW_FUNCS["stumble"] = _steps(
    P(root=(0, 6), lean=20, head=10, foot_front=(90, 66), foot_back=(-110, 40), hand_front=(110, -50),
      hand_back=(40, -90), eyes="wide", mouth="open", quill_sway=-8),
    P(root=(10, 14), lean=30, head=14, foot_front=(96, 66), foot_back=(-90, 20), hand_front=(130, -10),
      hand_back=(80, -70), eyes="wide", mouth="ouch", quill_sway=-10),
    P(root=(6, 6), lean=14, foot_front=(90, 66), foot_back=(-60, 62), hand_front=(100, -30), hand_back=(-120, -40),
      eyes="derp", mouth="flat", quill_sway=-4),
    P(lean=4),
    STAND)



def _stood(row: Callable[[float], Pose]) -> Callable[[float], Pose]:
    """``row`` with every pose stood on the floor: a lean or a lifted foot
    can raise the hips past what the planted leg reaches."""
    def stood(t: float) -> Pose:
        return replace(row(t), on_floor=True)
    if hasattr(row, "frames"):
        stood.frames = row.frames
    return stood


for _name in ("hit_high", "hit_low", "stumble", "trip_fall", "crouch_walk", "throw_forward", "crouch_start", "roll", "roll_back",
              "getup", "getup_roll", "getup_attack", "tech_roll", "dash_attack", "victory",
              "victory_hold"):
    ROW_FUNCS[_name] = _stood(ROW_FUNCS[_name])

#: Each fighter-vocabulary category (``fighter_core``) and the row that draws
#: it. Several categories may share a row; his signature moves are his
#: specials (the spin, the spin dash, its charge).
APPLICABLE_MOTION_SCOPES = ("fighter_core",)
FIGHTER_MOTION_COVERAGE: Dict[str, str] = {
    "idle": "idle", "idle_look_up": "idle_look_up", "walk": "walk", "locomotion_stop": "run_stop",
    "turnaround": "turnaround", "dash_startup": "dash_startup", "run": "run", "stumble": "stumble",
    "crouch_start": "crouch_start", "crouch": "crouch", "crouch_walk": "crouch_walk", "crouch_jump": "jump",
    "crouch_end": "crouch_end", "land_light": "land_light", "land_hard": "land_hard", "jump_squat": "jump_squat",
    "jump": "jump", "double_jump": "double_jump", "fall": "fall", "fall_special": "fall_special",
    "land_special": "land_hard", "tumble": "tumble",
    "shield_raise": "shield_raise", "shield_hold": "block", "shield_release": "shield_release", "parry": "parry",
    "shield_hit": "shield_hit", "spot_dodge": "spot_dodge", "roll_forward": "roll", "roll_backward": "roll_back",
    "air_dodge": "air_dodge",
    "jab": "punch", "dash_attack": "dash_attack", "attack_side": "attack_side", "attack_up": "attack_up",
    "attack_down": "attack_down", "smash_charge_forward": "smash_charge", "smash_forward": "smash_forward",
    "smash_charge_up": "smash_charge", "smash_up": "smash_up", "smash_charge_down": "smash_charge",
    "smash_down": "smash_down", "air_neutral": "air_neutral", "air_forward": "air_forward", "air_back": "air_back",
    "air_up": "air_up", "air_down": "air_down", "air_land": "air_land",
    "special_neutral": "special", "special_side": "dash", "special_up": "jump", "special_down": "dash_startup",
    "final_smash": "special",
    "grab": "grab", "grab_hold": "grab_hold", "pummel": "pummel", "grab_release": "grab_release",
    "throw_forward": "throw_forward", "throw_back": "throw_back", "throw_up": "throw_up", "throw_down": "throw_down",
    "grabbed": "grabbed", "grabbed_pummel": "grabbed_pummel", "grab_escape": "grab_escape",
    "hit": "hit_mid", "launch": "launch", "meteor": "meteor", "impact": "impact", "splat": "splat",
    "ground_bounce": "ground_bounce", "prone": "prone", "prone_damage": "prone_damage", "getup": "getup",
    "getup_attack": "getup_attack", "getup_roll": "getup_roll", "knockdown": "knockdown", "tech": "tech",
    "tech_roll": "tech_roll", "wall_tech": "wall_tech", "wall_tech_jump": "wall_tech_jump",
    "ceiling_tech": "ceiling_tech",
    "shield_break_launch": "shield_break_launch", "shield_break_fall": "shield_break_fall",
    "shield_break_collapse": "shield_break_collapse", "shield_break_recover": "shield_break_recover",
    "dizzy": "dizzy", "sleep_start": "sleep_start", "sleep": "sleep", "wake": "wake",
    "bury_start": "bury_start", "buried": "buried", "bury_escape": "bury_escape",
    "footstool_jump": "footstool_jump", "footstooled": "stumble", "platform_drop": "platform_drop",
    "teeter_start": "teeter_start", "teeter": "teeter", "lose_footing": "stumble",
    "ledge_catch": "ledge_catch", "ledge_hang": "ledge_grab", "ledge_getup": "ledge_getup",
    "ledge_attack": "ledge_getup_attack", "ledge_roll": "ledge_roll", "ledge_jump": "ledge_jump",
    "ledge_drop": "ledge_drop",
    "trip_fall": "trip_fall", "trip_land": "ground_bounce", "trip_idle": "prone_face_down", "trip_getup": "getup",
    "trip_attack": "getup_attack", "trip_roll": "getup_roll",
    "taunt": "taunt", "entrance": "entrance", "victory": "victory", "victory_hold": "victory_hold", "loss": "loss",
}


# The row names the runtime knows (crates/.../sprite_sheet/src/character/anim.rs
# `from_name`); an unlisted pose falls back through `base_pose`. `sprint` is the
# run at top speed; a sheet without it draws `run`.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 90),
    ("run", 8, 70),
    ("sprint", 8, 45),
    ("crouch", 2, 160),
    ("dash_startup", 6, 70),
    ("dash", 6, 60),
    ("ball", 6, 60),
    ("jump", 6, 80),
    ("fall", 4, 90),
    ("land_hard", 3, 70),
    ("land_recovery", 4, 90),
    ("skid", 3, 80),
    ("slash", 5, 60),
    ("punch", 4, 55),
    ("attack_side", 6, 70),
    ("attack_up", 6, 70),
    ("attack_down", 6, 70),
    ("air_neutral", 6, 70),
    ("air_forward", 5, 70),
    ("air_back", 5, 70),
    ("air_up", 5, 70),
    ("air_down", 6, 70),
    ("special", 8, 70),
    ("block", 3, 120),
    ("wall_grab", 3, 140),
    ("wall_jump", 4, 80),
    ("ledge_grab", 3, 150),
    ("ledge_climb", 5, 90),
    ("ledge_getup", 5, 90),
    ("ledge_getup_attack", 6, 70),
    ("ledge_roll", 5, 80),
    ("hit", 4, 100),
    ("death", 8, 110),
    ("taunt", 6, 120),
    ("interact", 5, 110),
] + FIGHTER_ROWS
# A row of given frames publishes each of them once.
assert all(getattr(ROW_FUNCS.get(name), "frames", n) == n for name, n, _ms in ROWS), "a row's count is not its frames"

# Generic gameplay keys for per-pose combat metadata (hurtboxes auto-derived per
# key; hitboxes measured below). Keyed row -> generic key (== row name).
ANIMATION_KEY_MAP: Dict[str, str] = {
    name: name
    for name, _n, _ms in ROWS
    if name in {
        "idle", "walk", "run", "sprint", "crouch", "jump", "fall", "dash", "ball", "skid",
        "slash", "punch", "attack_side", "attack_up", "attack_down",
        "air_neutral", "air_forward", "air_back", "air_up", "air_down",
        "special", "block", "wall_grab", "ledge_grab", "ledge_getup_attack",
        "hit", "dash_attack", "smash_forward", "smash_up", "smash_down", "getup_attack",
    }
}


def _draw_sanic(skin: Skin, anim: str, frame_idx: int, nframes: int, body_only: bool = False) -> Image.Image:
    return _draw_pose(skin, _row_poses(anim, nframes, skin)[frame_idx], body_only)


# --- Hit areas, measured from the drawn strikes --------------------------------

#: Each strike's Active window (fraction of the row) and what lands.
STRIKES: Dict[str, Tuple[float, float, Tuple[str, ...]]] = {
    "slash": (0.34, 0.62, ("hand_front",)),
    "punch": (0.40, 0.60, ("hand_front",)),
    "attack_side": (0.30, 0.60, ("foot_front",)),
    "attack_up": (0.32, 0.58, ("hand_front",)),
    "attack_down": (0.34, 0.60, ("foot_front",)),
    "air_neutral": (0.15, 0.85, ("ball",)),
    "air_forward": (0.30, 0.58, ("foot_front",)),
    "air_back": (0.30, 0.58, ("foot_back",)),
    "air_up": (0.32, 0.58, ("foot_front", "foot_back")),
    "air_down": (0.20, 0.80, ("ball",)),
    "special": (0.10, 0.92, ("ball",)),
    "ledge_getup_attack": (0.36, 0.64, ("foot_front",)),
    "dash_attack": (0.18, 0.62, ("foot_front",)),
    "smash_forward": (0.28, 0.62, ("hand_front",)),
    "smash_up": (0.30, 0.62, ("hand_front", "hand_back")),
    "smash_down": (0.30, 0.62, ("foot_front", "foot_back")),
    "getup_attack": (0.18, 0.62, ("foot_front", "foot_back")),
}
#: The reach of each striking part about its point (reference pixels).
_STRIKE_R = {"hand_front": 24.0, "hand_back": 30.0, "foot_front": 30.0, "foot_back": 34.0, "ball": BALL_R + 20.0}

#: The drawn reach of a blow is a sliver of the body; the game's volumes are
#: about 1.6x the drawn reach, so each grows by this much, away from his middle
#: (the blow's end), not into his body.
HITBOX_GROWTH = 1.8
_BODY_MIDDLE = _frame(TORSO_C)


def _generous(bbox: dict) -> dict:
    cx, cy = bbox["x"] + bbox["w"] / 2.0, bbox["y"] + bbox["h"] / 2.0
    w, h = bbox["w"] * HITBOX_GROWTH, bbox["h"] * HITBOX_GROWTH
    # Half the growth goes outward along the line from his middle to the blow.
    dx, dy = cx - _BODY_MIDDLE[0], cy - _BODY_MIDDLE[1]
    norm = max(1.0, (dx * dx + dy * dy) ** 0.5)
    cx += dx / norm * (w - bbox["w"]) / 2.0
    cy += dy / norm * (h - bbox["h"]) / 2.0
    x0 = max(0, round(cx - w / 2.0))
    y0 = max(0, round(cy - h / 2.0))
    x1 = min(FRAME_SIZE[0], round(cx + w / 2.0))
    y1 = min(FRAME_SIZE[1], round(cy + h / 2.0))
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}


def _measured_hitboxes() -> Dict[str, dict]:
    counts = _FRAME_COUNTS
    out: Dict[str, dict] = {}
    for row, (t0, t1, parts) in STRIKES.items():
        n = counts[row]
        poses = _row_poses(row, n)
        live = [p for i, p in enumerate(poses) if t0 <= (i / n if row in LOOPS else i / max(1, n - 1)) <= t1] or poses
        xs, ys = [], []
        for pose in live:
            solved = _solve(pose)
            for part in parts:
                c = solved.ball if part == "ball" else getattr(solved, part)
                r = _STRIKE_R[part]
                for corner in ((c[0] - r, c[1] - r), (c[0] + r, c[1] + r)):
                    fx, fy = _frame(corner)
                    xs.append(fx)
                    ys.append(fy)
        box = {"x": round(min(xs)), "y": round(min(ys)), "w": round(max(xs) - min(xs)), "h": round(max(ys) - min(ys))}
        out[row] = {"bbox": _generous(box)}
    return out


#: The frames of each row, as the module defines them: a strike's box is
#: measured on its whole row whatever rows a caller publishes.
_FRAME_COUNTS: Dict[str, int] = {name: n for name, n, _ms in ROWS}


@functools.lru_cache(maxsize=1)
def attack_hitboxes() -> Dict[str, dict]:
    """The measured strike boxes (:func:`_measured_hitboxes`). They are
    measured when a sheet is drawn, not when the module is imported: drawing
    the strike poses takes seconds, and every listing of the targets imports
    this module."""
    return _measured_hitboxes()


def _melee_events(active_from: float, active_to: float, source: str) -> List[dict]:
    return [
        {"t": max(0.0, active_from - 0.12), "event": "telegraph_peak", "source": source},
        {"t": active_from, "event": "hitbox_active_start", "source": source},
        {"t": active_to, "event": "hitbox_active_end", "source": source},
    ]


def _strike(row: str, source: str) -> dict:
    t0, t1, _parts = STRIKES[row]
    return {"animation": row, "events": _melee_events(t0, t1, source)}


def _animation_bindings(source: str) -> dict:
    """Bindings for BOTH game styles: platformer locomotion + a full Smash-style
    melee/aerial/special/ledge kit, with active-frame windows on each strike."""
    return {
        "default": {"animation": "idle", "events": []},
        # platformer locomotion
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.sprint": {"animation": "sprint", "events": []},
        "locomotion.crouch": {"animation": "crouch", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "locomotion.land": {"animation": "land_hard", "events": [{"t": 0.0, "event": "land_impact", "source": source}]},
        "locomotion.land_recover": {"animation": "land_recovery", "events": []},
        "locomotion.wall_slide": {"animation": "wall_grab", "events": []},
        "locomotion.wall_cling": {"animation": "wall_grab", "events": []},
        "locomotion.wall_jump": {"animation": "wall_jump", "events": [{"t": 0.1, "event": "wall_launch", "source": source}]},
        "locomotion.ledge_grab": {"animation": "ledge_grab", "events": []},
        "locomotion.ledge_climb": {"animation": "ledge_climb", "events": []},
        # ground melee
        "action.melee.primary": _strike("slash", source),
        "action.melee.punch": _strike("punch", source),
        "action.melee.side": _strike("attack_side", source),
        "action.melee.up": _strike("attack_up", source),
        "action.melee.down": _strike("attack_down", source),
        "action.melee.dash": _strike("dash_attack", source),
        # smashes
        "action.smash.forward": _strike("smash_forward", source),
        "action.smash.up": _strike("smash_up", source),
        "action.smash.down": _strike("smash_down", source),
        # aerials
        "action.air.neutral": _strike("air_neutral", source),
        "action.air.forward": _strike("air_forward", source),
        "action.air.back": _strike("air_back", source),
        "action.air.up": _strike("air_up", source),
        "action.air.down": _strike("air_down", source),
        # specials (the spin)
        "action.special.spin": _strike("special", source),
        "action.special.dash": {"animation": "dash", "events": [{"t": 0.30, "event": "dash_commit", "source": source}]},
        "action.special.dash_charge": {"animation": "dash_startup", "events": []},
        # defense / ledge options
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.parry": {"animation": "parry", "events": []},
        "action.defense.roll": {"animation": "roll", "events": [{"t": 0.15, "event": "iframes_start", "source": source}, {"t": 0.75, "event": "iframes_end", "source": source}]},
        "action.ledge.getup": {"animation": "ledge_getup", "events": []},
        "action.ledge.getup_attack": _strike("ledge_getup_attack", source),
        "action.ledge.roll": {"animation": "ledge_roll", "events": []},
        # the grab
        "action.capture.grab": {"animation": "grab", "events": []},
        "action.capture.pummel": {"animation": "pummel", "events": []},
        "action.capture.throw_forward": {"animation": "throw_forward", "events": []},
        "action.capture.throw_back": {"animation": "throw_back", "events": []},
        "action.capture.throw_up": {"animation": "throw_up", "events": []},
        "action.capture.throw_down": {"animation": "throw_down", "events": []},
        # reactions / emotes
        "reaction.hit": {"animation": "hit", "events": []},
        "reaction.death": {"animation": "death", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
        "emote.victory": {"animation": "victory", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    }


ACTOR_METADATA_SANIC = {
    "actor": {"character_id": "npc_sanic", "display_name": "Sanic"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Run",
        "traits": ["npc", "meme", "fast", "runner", "fighter", "beast"],
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": False, "swim": None, "use_lifts": None, "door_access": []},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": _animation_bindings("sanic"),
    "tags": ["meme", "fast", "runner", "fighter", "platformer"],
}
ACTOR_METADATA_SANIC.update(
    {
        "authoring_description": (
            "Sanic is the deliberately crude internet-meme mutation of Sonic the "
            "Hedgehog: frantic, badly proportioned, overconfident, and defined by the "
            "demand to go fast rather than by polished mascot heroism. He is drawn "
            "after the meme's MS Paint picture: a 3/4 body with a cream belly, a "
            "blocky head with derpy eyes and a cream grin, fat swept quills, stick "
            "limbs, one huge white glove and red shoe blobs."
        ),
        "gameplay_description": (
            "Use as an absurdly fast runner, rival, playable fighter, or unstable speed "
            "tutorial. Movement should outrun composure, with skids, wall actions, spin "
            "attacks, and dialogue that treats standing still as abuse."
        ),
        "dialogue_hints": {
            "barks": [
                "The pedestal asked me to idle. I have reported it for abuse.",
                "I can stop whenever I want. I do not want.",
                "Fast enough to outrun the answer.",
            ]
        },
    }
)

# Super Sanic — the transformation. Same body/moveset/geometry; the golden,
# spikes-up, invincible power form. It flies and hits harder; the sprite is the
# same body re-skinned so a runtime transformation just swaps the sheet.
ACTOR_METADATA_SUPER = {
    "actor": {"character_id": "npc_super_sanic", "display_name": "Super Sanic"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Fly",
        "traits": ["npc", "meme", "fast", "runner", "fighter", "beast", "super", "transformation", "invincible", "flight"],
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": True, "swim": None, "use_lifts": None, "door_access": []},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": _animation_bindings("super_sanic"),
    "tags": ["meme", "fast", "runner", "fighter", "platformer", "super", "transformation"],
}
ACTOR_METADATA_SUPER.update(
    {
        "authoring_description": (
            "Super Sanic is the golden, airborne transformation of the Sanic meme, "
            "combining the crude Sonic parody with the invincible super-form spectacle "
            "of collected power and impossible speed: the same MS Paint body in gold, "
            "quills raised, red pupils and a glow."
        ),
        "gameplay_description": (
            "Use as a temporary transformation, boss phase, or overpowered unlock. He "
            "should fly, ignore ordinary hazards, and behave as though reality itself is "
            "too slow to enforce its rules."
        ),
        "dialogue_hints": {
            "barks": [
                "I am not glowing. The air is falling behind.",
                "Immortality is a budget with excellent music.",
                "The universe may submit a written request.",
            ]
        },
    }
)


def _pose_bodies(skin: Skin) -> Dict[str, dict]:
    """The gameplay body of each mapped row: the union of the visible boxes
    (``visible_bbox``) of the row's frames drawn ``body_only``.

    ⛔ Not the drawn frames. The game stands a body on the bottom of this box
    and draws the frame on it, so whatever the box holds under the soles is
    air between the feet and the floor: the super glow held 10 px of it, and
    every pose's speed lines and dust widened its box.
    """
    counts = {name: n for name, n, _ms in ROWS}
    bodies = {}
    for row, key in ANIMATION_KEY_MAP.items():
        x0, y0, x1, y1 = union_visible_bbox(_draw_sanic(skin, row, i, counts[row], body_only=True)
                                            for i in range(counts[row]))
        bodies[key] = {"parts": [{"name": "body", "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}]}
    return bodies


def _body_metrics(bodies: Dict[str, dict]):
    """The sheet's body: the idle pose's (:func:`_pose_bodies`), its feet on
    its bottom row."""
    part = bodies["idle"]["parts"][0]
    box = (part["x"], part["y"], part["x"] + part["w"], part["y"] + part["h"])
    return lambda fw, fh: body_metrics_for_box(box, fw, fh)


def _render_form(target_name: str, skin: Skin, actor_metadata: dict, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_sanic(skin, animation, frame_idx, nframes)

    bodies = _pose_bodies(skin)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target_name,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        # Keep frames uncropped so measured hitbox coords match our draw space.
        auto_crop=False,
        actor_metadata=actor_metadata,
        animation_key_map=ANIMATION_KEY_MAP,
        attack_hitboxes=attack_hitboxes(),
        body_metrics_fn=_body_metrics(bodies),
        hurtbox_parts=bodies,
    )
    parts = publish_rig_flipbook(target_name, ROWS, render_frame, outputs, frame_transform, out_dir)
    return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")] + list(
        parts.values()
    )


def render_sanic(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form("sanic", NORMAL, ACTOR_METADATA_SANIC, out_dir)


def render_super_sanic(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form("super_sanic", SUPER_SKIN, ACTOR_METADATA_SUPER, out_dir)


# Both forms register as targets from this one module (same drawing + moveset,
# different Skin). `super_sanic` is Sanic's transformation, shipped as its own
# swappable sheet.
TARGETS = {
    "sanic": {"render": render_sanic, "actor_metadata": ACTOR_METADATA_SANIC},
    "super_sanic": {"render": render_super_sanic, "actor_metadata": ACTOR_METADATA_SUPER},
}


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_sanic(NORMAL, animation, frame_idx, nframes)
