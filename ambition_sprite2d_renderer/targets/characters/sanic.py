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

Super Sanic is the same rig in another :class:`Skin`: gold, quills raised,
red pupils and a glow. Both forms register from this module (``TARGETS``).

The hit area of each strike is measured from the drawn pose: where the glove,
the shoe or the ball is on the frames of the move's Active window
(:func:`_measured_hitboxes`), grown by ``HITBOX_GROWTH``.
"""

from __future__ import annotations

import io
import math
import random
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet

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
#: hips: its middle, half-width and tilt.
EIGHT_C = (272.0, 346.0)
EIGHT_A = 92.0
EIGHT_TILT = -12.0

#: Rest limb targets: a hand from its shoulder, a foot from its hip.
REST_HAND_BACK = (-112.0, 30.0)
REST_HAND_FRONT = (74.0, 6.0)
REST_FOOT_BACK = (-100.0, 62.0)
REST_FOOT_FRONT = (66.0, 66.0)

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
    fx: Tuple[str, ...] = ()       # speed | dust


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


def _put(img: Image.Image, key: tuple, svg, anchor: Point, at: Point, degrees: float, name: str, reach=260.0) -> None:
    """Place the piece ``key`` with its anchor at the reference point ``at``."""
    part = _piece(key, svg, anchor, reach)
    if part is not None:
        fx, fy = _frame(at)
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


def _eight_svg(skin: Skin) -> str:
    """The blur the feet leave round the figure 8."""
    pts = [_eight_point(u) for u in np.linspace(0, 1, 33)[:-1]]
    return (f'<path d="{_smooth(pts)}" fill="none" stroke="{skin.body}" stroke-width="26" opacity="0.4"/>'
            f'<path d="{_smooth(pts)}" fill="none" stroke="{skin.shoe}" stroke-width="8" opacity="0.5"/>')


#: The ghosts each sprinting shoe leaves behind it on the figure 8:
#: (how far back, in turns; opacity).
SHOE_GHOSTS = ((0.07, 0.45), (0.14, 0.22))


def _aura_svg(skin: Skin) -> str:
    return (f'<ellipse cx="{TORSO_C[0]}" cy="{TORSO_C[1] - 40}" rx="170" ry="210" '
            f'fill="{skin.aura}" opacity="0.55" filter="url(#glow)"/>')


def _speed_svg(skin: Skin) -> str:
    out = []
    for k, (y, length) in enumerate([(170, 110), (215, 160), (262, 130), (310, 90)]):
        out.append(_line([(40 - length, y), (40, y)], skin.body if k % 2 else "#9aa4ff", 4.5))
    return "".join(out)


def _dust_svg() -> str:
    return "".join(_fill(_wobble_blob(140 - k * 34, 390 - 4 * k, 16 - 2 * k, 10 - k, 900 + k), "#d8d2c4", 2.2)
                   for k in range(4))


# --- Drawing one pose -----------------------------------------------------------


def _draw_pose(skin: Skin, pose: Pose) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = _solve(pose)
    sk = skin.name
    if "speed" in pose.fx:
        _put(img, ("speed", sk), lambda: _speed_svg(skin), (0.0, 240.0), _add((0.0, 240.0), pose.root), 0.0, "speed_lines")
    if "dust" in pose.fx:
        _put(img, ("dust",), _dust_svg, (90.0, 380.0), (90.0 + pose.root[0], 380.0), 0.0, "dust")

    if pose.ball:
        if skin.aura:
            _put(img, ("ball_aura", sk), lambda: f'<circle cx="{BALL_C[0]}" cy="{BALL_C[1]}" r="125" fill="{skin.aura}" '
                 'opacity="0.55" filter="url(#glow)"/>', BALL_C, s.ball, 0.0, "aura")
        _put(img, ("ball", sk), lambda: _ball_svg(skin), BALL_C, s.ball, 360.0 * pose.turn, "ball")
        return _downsample(img)

    if skin.aura:
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
    if pose.eight:
        _put(img, ("eight", sk), lambda: _eight_svg(skin), EIGHT_C, _add(EIGHT_C, (pose.root[0], 0.0)), 0.0, "eight")
        for foot, (back, alpha) in [(f, g) for f in ("back", "front") for g in SHOE_GHOSTS]:
            u = pose.eight_u + (0.5 if foot == "front" else 0.0) + back
            at = _add(_eight_point(-u), (pose.root[0], 0.0))
            _put(img, ("ghost_shoe", skin.shoe, alpha),
                 lambda a=alpha: f'<g opacity="{a}">' + _fill(_wobble_blob(14, 6, 32, 12, 301, amp=0.08), skin.shoe) + "</g>",
                 (0.0, 0.0), at, 0.0, f"ghost_{foot}_{back}")
    _limb(img, skin, [s.hip_back, s.knee_back, s.foot_back], 15, "leg_back")
    _shoe(img, skin, s.foot_back, -1, pose.shoe_back_tilt, 1.25, 300, "shoe_back")
    _limb(img, skin, [s.shoulder_back, s.elbow_back, s.hand_back], 15, "arm_back")
    _glove(img, skin, s.hand_back, pose.glove_back, 401, 27, 23, "glove_back")

    _put(img, ("torso", sk), lambda: _torso_svg(skin), LEAN_PIVOT, s.pivot, pose.lean, "torso")

    _limb(img, skin, [s.hip_front, s.knee_front, s.foot_front], 15, "leg_front")
    _shoe(img, skin, s.foot_front, 1, pose.shoe_front_tilt, 0.9, 301, "shoe_front")

    _put(img, ("head", sk), lambda: _head_svg(skin), NECK, s.neck, head_turn, "head")
    _put(img, ("mouth", pose.mouth), lambda: _mouth_svg(pose.mouth), NECK, s.neck, head_turn, "mouth")
    _put(img, ("eyes", sk, pose.eyes), lambda: _eyes_svg(skin, pose.eyes), NECK, s.neck, head_turn, "eyes")

    # the front arm last: it crosses the body when it swings
    _limb(img, skin, [s.shoulder_front, s.elbow_front, s.hand_front], 14, "arm_front")
    _glove(img, skin, s.hand_front, pose.glove_front, 402, 17, 11, "glove_front")
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
    """Top speed: the feet run round a figure 8, half a lap apart, and leave
    its blur behind them. The shoe tilts with the way it travels."""
    s = math.sin(2 * math.pi * t)
    feet = []
    for phase in (0.0, 0.5):
        u = -(t + phase)
        here, ahead = _eight_point(u), _eight_point(u - 0.02)
        tilt = math.degrees(math.atan2(ahead[1] - here[1], ahead[0] - here[0]))
        feet.append((here, max(-30.0, min(30.0, ((tilt + 90) % 180) - 90))))
    (fb, tb), (ff, tf) = feet
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


def _row_poses(anim: str, n: int) -> List[Pose]:
    """The ``n`` poses of a row."""
    loop = anim in LOOPS
    ts = [i / n if loop else (i / (n - 1) if n > 1 else 0.0) for i in range(n)]
    key = ROW_KEYS.get(anim)
    if key is not None:
        return [_keyed(key, t) for t in ts]
    return [ROW_FUNCS[anim](t) for t in ts]


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
]

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
        "hit",
    }
}


def _draw_sanic(skin: Skin, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_pose(skin, _row_poses(anim, nframes)[frame_idx])


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
    counts = {name: n for name, n, _ms in ROWS}
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


ATTACK_HITBOXES: Dict[str, dict] = _measured_hitboxes()


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
        "action.defense.roll": {"animation": "ball", "events": [{"t": 0.15, "event": "iframes_start", "source": source}, {"t": 0.75, "event": "iframes_end", "source": source}]},
        "action.ledge.getup": {"animation": "ledge_getup", "events": []},
        "action.ledge.getup_attack": _strike("ledge_getup_attack", source),
        "action.ledge.roll": {"animation": "ledge_roll", "events": []},
        # reactions / emotes
        "reaction.hit": {"animation": "hit", "events": []},
        "reaction.death": {"animation": "death", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
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


def _render_form(target_name: str, skin: Skin, actor_metadata: dict, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_sanic(skin, animation, frame_idx, nframes)

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
        attack_hitboxes=ATTACK_HITBOXES,
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
