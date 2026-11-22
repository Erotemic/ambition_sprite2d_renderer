"""Marshal Gallus "Rocq": the boss of the Frontier dimension (gate address
LEADENSADDLE), a former marshal and now a train robber
(`docs/planning/game/leadensaddle.md`).

Drawn from Jon's character sheet of 2026-11-21
(`assets/concept_art/misc/Marshal Gallus “Rocq” Character Sheet-2.png`): a
stout man with a rooster's head and a rooster's feet, in a gunfighter's
kit. A long riveted duster with brass along its seams, open on a dark vest;
the marshal's star still on its breast; a heavy belt with a brass buckle and
a gun belt below it, a holster on each hip; dark trousers down over the
hocks, bird's feet in spurs (the near shin a piston). A red poncho round his
shoulders, a woven band of a stepped zigzag along its hem and a fringe; its
back flies out behind him like a cape. A wide brown hat with a star on its
band, worn forward; the big red comb bursts up out of the back of it, behind
the crown. A white face, the near half a riveted plate with a brass lens for
an eye; big red wattles; a cigar. The near arm is a plated machine arm with a
steel hand; the far arm, in the coat's sleeve and a glove, is the gun arm.
The tail is dark, a blue sheen on it, out of the duster's back vent.

A PAPER DOLL: every part is its own drawing, posed from one ``Pose`` per
frame; ``draw_marshal`` gives the order, back to front.

Rows: ``idle`` 8; ``walk`` 8 (a strut); ``quickdraw`` 12 (tell 0-4: the gun
hand to the holster; draw 5-6; three shots 7-9; recovery 10-11);
``spur_kick`` 12 (tell 0-4: he rears back on the far leg; kick 5-7; recovery
8-11); ``lasso`` 14 (twirl 0-7; throw 8-10; the yank 11-13); ``dynamite`` 12
(he lights them off his cigar 0-4; the throw 5-8; recovery 9-11);
``whistle`` 12 (he puffs up 0-5; the crow 6-9, and its ring along the floor;
recovery 10-11); ``call`` 8 (a short whistle through the beak: the
tumbleweeds); ``high_noon`` 16 (he squares up 0-5; six shots, high and low,
a revolver in each hand, 6-13; 14-15 he holds); ``reload`` 10 (the cylinder
swings out, the shells fall); ``enrage`` 12 (he pushes his hat back and the
machine arm runs hot); ``turn`` 6; ``hurt`` 3; ``death`` 20 (the blow throws
him back and his hat off, the shoulder sparks; he sputters and staggers;
down on one knee; on his face, the tail up; the last frame is held);
``seated`` 8 (beaten, on an ore cart, the lens cracked).

Facing right. The feet are on the line ``FLOOR``; the published boss row
(`boss_sheets.ron`, ``marshal_gallus``) draws the frame's centre at his
body's centre, and ``FLOOR`` is where the bottom of a 96 x 140 body falls at
its ``collision_scale``. No drop shadow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "marshal_gallus"
FRAME_SIZE = (400, 400)
SUPER = 4
#: Where the feet stand. The game sizes his body from the drawn body box
#: and draws the frame's centre at the body's centre, so the drawn body
#: (from the hat's crown to the feet, about 290 px) is centred on the frame:
#: its bottom, the feet, at 200 + 145.
FLOOR = 340.0
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 130),
    ("walk", 8, 105),
    ("quickdraw", 12, 70),
    ("spur_kick", 12, 65),
    ("lasso", 14, 75),
    ("dynamite", 12, 75),
    ("whistle", 12, 75),
    ("call", 8, 80),
    ("high_noon", 16, 70),
    ("reload", 10, 90),
    ("enrage", 12, 85),
    ("turn", 6, 70),
    ("hurt", 3, 90),
    ("death", 20, 90),
    ("seated", 8, 160),
]

OUTLINE: RGBA = (34, 22, 20, 255)
FEATHER: RGBA = (246, 238, 222, 255)
FEATHER_SHADE: RGBA = (214, 200, 176, 255)
FEATHER_DARK: RGBA = (156, 126, 88, 255)
HACKLE: RGBA = (226, 150, 62, 255)
HACKLE_DARK: RGBA = (178, 98, 40, 255)
WING: RGBA = (176, 100, 48, 255)
WING_DARK: RGBA = (122, 64, 30, 255)
WING_LIGHT: RGBA = (214, 150, 86, 255)
SICKLE: RGBA = (36, 42, 66, 255)
SICKLE_SHEEN: RGBA = (86, 104, 156, 255)
COMB: RGBA = (204, 40, 36, 255)
COMB_DARK: RGBA = (150, 24, 26, 255)
BEAK: RGBA = (238, 190, 64, 255)
BEAK_DARK: RGBA = (184, 132, 34, 255)
LEG: RGBA = (232, 186, 70, 255)
LEG_DARK: RGBA = (178, 132, 40, 255)
PLATE: RGBA = (150, 64, 46, 255)
PLATE_LIGHT: RGBA = (190, 96, 66, 255)
PLATE_DARK: RGBA = (98, 40, 32, 255)
STEEL: RGBA = (132, 138, 146, 255)
STEEL_LIGHT: RGBA = (190, 196, 202, 255)
STEEL_DARK: RGBA = (72, 76, 86, 255)
GUNMETAL: RGBA = (62, 64, 72, 255)
BRASS: RGBA = (214, 170, 72, 255)
BRASS_DARK: RGBA = (150, 110, 40, 255)
BRASS_LIGHT: RGBA = (246, 218, 128, 255)
HAT: RGBA = (132, 88, 52, 255)
HAT_DARK: RGBA = (90, 58, 34, 255)
HAT_LIGHT: RGBA = (172, 124, 78, 255)
LEATHER: RGBA = (110, 66, 38, 255)
LEATHER_DARK: RGBA = (74, 42, 26, 255)
BANDANA: RGBA = (196, 42, 40, 255)
BANDANA_DARK: RGBA = (138, 24, 28, 255)
WOOD: RGBA = (132, 84, 48, 255)
LENS_RED: RGBA = (255, 70, 48, 255)
FLASH: RGBA = (255, 236, 160, 255)
WHITE_HOT: RGBA = (255, 252, 236, 255)
STEAM: RGBA = (236, 240, 244, 255)
SMOKE: RGBA = (90, 88, 92, 255)
COAT: RGBA = (124, 76, 44, 255)
COAT_DARK: RGBA = (86, 52, 32, 255)
VEST: RGBA = (66, 50, 44, 255)
TROUSERS: RGBA = (82, 68, 62, 255)
TROUSERS_DARK: RGBA = (58, 48, 46, 255)
PONCHO: RGBA = (172, 52, 42, 255)
PONCHO_DARK: RGBA = (120, 32, 30, 255)
PONCHO_BAND: RGBA = (238, 216, 178, 255)
GLOVE: RGBA = (80, 52, 34, 255)
CIGAR: RGBA = (112, 70, 40, 255)
ASH: RGBA = (196, 192, 186, 255)
EMBER: RGBA = (255, 120, 50, 255)
LENS_GOLD: RGBA = (255, 200, 70, 255)
SOOT: RGBA = (34, 30, 30, 255)
DYNAMITE: RGBA = (206, 48, 40, 255)
ROPE: RGBA = (200, 160, 96, 255)
ROPE_DARK: RGBA = (140, 104, 56, 255)
EYE: RGBA = (24, 16, 12, 255)
CART: RGBA = (96, 92, 88, 255)
ORE: RGBA = (88, 84, 92, 255)

#: The body's lengths (frame pixels): thigh, shank; upper arm, forearm.
THIGH = 40.0
SHANK = 44.0
UPPER_ARM = 32.0
#: The head is drawn this much larger than its sketch, so it reads over the body.
HEAD = 1.3
FOREARM = 32.0


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _mix(c0: RGBA, c1: RGBA, t: float) -> RGBA:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(4))  # type: ignore[return-value]


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _rot(p: Point, deg: float) -> Point:
    """Turn ``p`` about the origin, clockwise on the screen (y is down)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _down(deg: float) -> Point:
    """The unit vector at ``deg`` from straight down, toward the facing (+x)."""
    r = math.radians(deg)
    return (math.sin(r), math.cos(r))


def _along(p: Point, deg: float, length: float) -> Point:
    d = _down(deg)
    return (p[0] + d[0] * length, p[1] + d[1] * length)


def _smooth(points: Sequence[Point], closed: bool = True, steps: int = 8) -> List[Point]:
    """A Catmull-Rom curve through ``points``."""
    pts = list(points)
    n = len(pts)
    out: List[Point] = []
    count = n if closed else n - 1
    for i in range(count):
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[min(n - 1, i + 1)]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    if not closed:
        out.append(pts[-1])
    return out


class Pen:
    """Draws in frame pixels on the supersampled canvas, every shape with a
    dark outline (``line`` is the outline's width in frame pixels).

    A translucent colour is laid OVER what is drawn: Pillow's own drawing
    writes a translucent fill's alpha into the canvas, which would cut a
    see-through hole in the shape under a shade."""

    def __init__(self, img: Image.Image):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")  # raw-draw-ok: opaque strokes only; translucent ones go through _over

    def _over(self, box: Sequence[float], paint) -> None:
        """``paint(draw, dx, dy)`` on a layer the size of ``box`` (canvas
        pixels), composited over the canvas."""
        x0, y0 = max(0, int(box[0]) - 4), max(0, int(box[1]) - 4)
        x1, y1 = min(self.img.width, int(box[2]) + 5), min(self.img.height, int(box[3]) + 5)
        if x1 <= x0 or y1 <= y0:
            return
        layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        paint(ImageDraw.Draw(layer, "RGBA"), -x0, -y0)  # raw-draw-ok: a clear layer, alpha-composited over the art
        self.img.alpha_composite(layer, (x0, y0))

    @staticmethod
    def _box(sp: Sequence[Tuple[float, float]], pad: float) -> Tuple[float, float, float, float]:
        xs, ys = [q[0] for q in sp], [q[1] for q in sp]
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

    def poly(self, pts: Sequence[Point], fill: RGBA, line: float = 1.4, outline: RGBA = OUTLINE) -> None:
        sp = [_s(p) for p in pts]
        if len(sp) < 3:
            return
        w = max(1, int(line * SUPER))

        def paint(d, dx: float, dy: float) -> None:
            q = [(x + dx, y + dy) for x, y in sp]
            d.polygon(q, fill=fill)
            if line > 0:
                d.line(q + [q[0]], fill=outline, width=w, joint="curve")
        if fill[3] < 255 or (line > 0 and outline[3] < 255):
            self._over(self._box(sp, w), paint)
        else:
            paint(self.d, 0.0, 0.0)

    def shape(self, pts: Sequence[Point], fill: RGBA, line: float = 1.4, outline: RGBA = OUTLINE, steps: int = 8) -> None:
        self.poly(_smooth(pts, True, steps), fill, line, outline)

    def ellipse(self, c: Point, rx: float, ry: float, fill: Optional[RGBA], line: float = 1.2, outline: RGBA = OUTLINE) -> None:
        box = (*_s((c[0] - rx, c[1] - ry)), *_s((c[0] + rx, c[1] + ry)))
        w = max(1, int(line * SUPER)) if line > 0 else 0

        def paint(d, dx: float, dy: float) -> None:
            d.ellipse((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), fill=fill, outline=outline if line > 0 else None, width=w)
        if (fill is not None and fill[3] < 255) or (line > 0 and outline[3] < 255):
            self._over(box, paint)
        else:
            paint(self.d, 0.0, 0.0)

    def circle(self, c: Point, r: float, fill: RGBA, line: float = 1.2, outline: RGBA = OUTLINE) -> None:
        self.ellipse(c, r, r, fill, line, outline)

    def line(self, pts: Sequence[Point], fill: RGBA, width: float) -> None:
        sp = [_s(p) for p in pts]
        w = max(1, int(width * SUPER))

        def paint(d, dx: float, dy: float) -> None:
            d.line([(x + dx, y + dy) for x, y in sp], fill=fill, width=w, joint="curve")
        if fill[3] < 255:
            self._over(self._box(sp, w), paint)
        else:
            paint(self.d, 0.0, 0.0)

    def arc(self, c: Point, r: float, a0: float, a1: float, fill: RGBA, width: float) -> None:
        box = (*_s((c[0] - r, c[1] - r)), *_s((c[0] + r, c[1] + r)))
        w = max(1, int(width * SUPER))
        self._over(box, lambda d, dx, dy: d.arc((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), a0, a1, fill=fill, width=w))

    def stroke(self, pts: Sequence[Point], fill: RGBA, width: float, line: float = 1.2, outline: RGBA = OUTLINE) -> None:
        """A thick stroke with a dark edge: a rope, a tube."""
        if line > 0:
            self.line(pts, outline, width + 2 * line)
            for p in (pts[0], pts[-1]):
                self.circle(p, width / 2 + line, outline, 0)
        self.line(pts, fill, width)
        for p in (pts[0], pts[-1]):
            self.circle(p, width / 2, fill, 0)

    def tube(self, a: Point, b: Point, w0: float, w1: float, fill: RGBA, line: float = 1.3) -> None:
        """A tapered limb from ``a`` (width ``w0``) to ``b`` (width ``w1``)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        pts = [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
               (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]
        self.circle(a, w0 / 2, fill, line)
        self.circle(b, w1 / 2, fill, line)
        self.poly(pts, fill, line)
        # The joint caps were outlined under the body of the tube: fill them again.
        self.circle(a, max(0.0, w0 / 2 - line * 0.6), fill, 0)
        self.circle(b, max(0.0, w1 / 2 - line * 0.6), fill, 0)


def _glow(img: Image.Image, fn, blur: float) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer, "RGBA"))  # raw-draw-ok: a clear glow layer, blurred and alpha-composited
    layer = layer.filter(ImageFilter.GaussianBlur(blur * SUPER))
    img.alpha_composite(layer)


@dataclass(frozen=True)
class Pose:
    #: The hip joint (frame pixels); ``y`` is set by ``_grounded`` for a pose
    #: that stands.
    x: float = 192.0
    y: float = 206.0
    #: The body's lean: positive tips the chest forward (toward +x).
    lean: float = -4.0
    #: The head's tilt about the neck (positive: the beak down) and its reach.
    head: float = 0.0
    neck_reach: float = 0.0
    beak: float = 0.0
    puff: float = 0.0
    #: Arms: (shoulder angle from straight down, toward the facing; elbow
    #: bend, positive folds the forearm forward/up).
    near_arm: Tuple[float, float] = (10.0, 40.0)
    far_arm: Tuple[float, float] = (-6.0, 30.0)
    #: Legs: (hip angle from straight down, toward the facing; hock bend, the
    #: shank turned back by it).
    near_leg: Tuple[float, float] = (16.0, 34.0)
    far_leg: Tuple[float, float] = (-10.0, 30.0)
    #: Where the revolver is: "holster", "hand" or "none".
    revolver: str = "holster"
    #: Muzzle flashes (0..1; below zero: none): the revolver's and the cannon's.
    flash_far: float = -1.0
    flash_near: float = -1.0
    #: The cannon's cylinder swung out (reload), 0..1, and shells falling.
    cylinder_out: float = 0.0
    shells: float = -1.0
    #: The lasso: "none", "twirl" (``lasso_phase`` turns the loop), "throw"
    #: (``lasso_reach`` 0..1 out), "yank".
    lasso: str = "none"
    lasso_phase: float = 0.0
    lasso_reach: float = 0.0
    #: Dynamite sticks in the claw (0..3) and the fuse's spark.
    dynamite: int = 0
    fuse: float = 0.0
    #: Steam: the crow's jet from the whistle and its ring (0..1).
    steam: float = 0.0
    call: float = 0.0
    smoke: float = 0.3
    phase: float = 0.0
    tail_spread: float = 0.0
    #: "menace", "fury", "pain", "smug", "calm", "hoarse".
    expression: str = "smug"
    lens: float = 0.6
    #: The hat: pushed back (degrees), lifted off (0..1 of its fall).
    hat_back: float = 0.0
    hat_off: float = 0.0
    #: Where the hat lands when it falls, along the floor from where he
    #: stands at rest (``x``'s default; behind him: negative): it stays put
    #: there while he moves. It turns over once toward that side.
    hat_land: float = -120.0
    hat_arc: float = 40.0
    #: How much of the body's lean the tail follows.
    tail_lean: float = 0.6
    #: Black smoke from the pipes (0..1), and the sparks off the chest plate
    #: of a blow that breaks him (0..1; below zero: none).
    soot: float = 0.0
    sparks: float = -1.0
    #: The crow's ring round him on the floor, with its rings of sound.
    steam_ring: bool = True
    #: The poncho's back flying out behind him (0: it hangs, 1: it streams).
    cape: float = 0.0
    #: The machine hand holds his second revolver (high noon, the reload).
    near_gun: bool = False
    cigar: bool = True
    chest_glow: float = 0.0
    cracked: bool = False
    kneel: float = 0.0
    seated: bool = False


# ---- the skeleton -----------------------------------------------------------------------------------------------

def _body_point(pose: Pose, p: Point) -> Point:
    """A point of the body (local: the hip at the origin, facing right, the
    body upright) where the posed body puts it."""
    return _add((pose.x, pose.y), _rot(p, pose.lean))


def _shoulder(pose: Pose, near: bool) -> Point:
    return _body_point(pose, (14.0, -84.0) if near else (-20.0, -88.0))


def _neck_top(pose: Pose) -> Point:
    return _body_point(pose, (14.0 + pose.neck_reach, -116.0))


def _head_centre(pose: Pose) -> Point:
    return _add(_neck_top(pose), _rot((4.0, -12.0), pose.head * 0.5))


def _hip(pose: Pose, near: bool) -> Point:
    return _body_point(pose, (6.0, -6.0) if near else (-6.0, -8.0))


def _leg(pose: Pose, near: bool) -> Tuple[Point, Point, Point]:
    """Hip, hock and ankle."""
    hip_deg, hock = pose.near_leg if near else pose.far_leg
    hip = _hip(pose, near)
    knee = _along(hip, hip_deg, THIGH)
    ankle = _along(knee, hip_deg - hock, SHANK)
    return hip, knee, ankle


def _arm(pose: Pose, near: bool) -> Tuple[Point, Point, Point]:
    """Shoulder, elbow and hand."""
    sh_deg, bend = pose.near_arm if near else pose.far_arm
    shoulder = _shoulder(pose, near)
    elbow = _along(shoulder, sh_deg + pose.lean, UPPER_ARM)
    hand = _along(elbow, sh_deg + pose.lean + bend, FOREARM)
    return shoulder, elbow, hand


def _forearm_deg(pose: Pose, near: bool) -> float:
    sh_deg, bend = pose.near_arm if near else pose.far_arm
    return sh_deg + pose.lean + bend


def _grounded(pose: Pose) -> Pose:
    """Set the hip's height so that the lower foot stands on ``FLOOR``."""
    lowest = max(_leg(replace(pose, y=0.0), near)[2][1] for near in (True, False))
    return replace(pose, y=FLOOR - 5.0 - lowest)


# ---- the parts --------------------------------------------------------------------------------------------------

def _sickle(pen: Pen, pose: Pose, base: Point, ang: float, length: float, width: float, i: int, sheen: RGBA) -> None:
    """One sickle feather: a long dark arc out and back, drooping at its tip."""
    a = ang - 8 * pose.tail_spread + pose.lean * pose.tail_lean
    sway = 3.0 * math.sin(pose.phase * math.tau + i)
    p1 = _add(base, _rot((0.0, -length * 0.55), a))
    p2 = _add(base, _rot((-length * 0.25, -length * 0.95), a))
    tip = _add(p2, (-10.0 + sway, 26.0 + i * 3))
    spine = _smooth([base, p1, p2, tip], closed=False, steps=6)
    left = []
    right = []
    for k, p in enumerate(spine):
        q = spine[min(len(spine) - 1, k + 1)]
        o = spine[max(0, k - 1)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        n = math.hypot(dx, dy) or 1.0
        w = width * (1.0 - k / len(spine)) * 0.5 + 0.8
        left.append((p[0] - dy / n * w, p[1] + dx / n * w))
        right.append((p[0] + dy / n * w, p[1] - dx / n * w))
    pen.poly(left + right[::-1], SICKLE, 1.2)
    # The vane's sheen along one side, and the quill.
    pen.line([_lerp(spine[k], left[k], 0.55) for k in range(1, len(spine) - 2)], sheen, 2.2)
    pen.line(spine[1:-3], _a(OUTLINE, 0.5), 0.8)


def _tail_root(pose: Pose) -> Point:
    return _body_point(pose, (-34.0, -18.0))


def draw_tail(pen: Pen, pose: Pose) -> None:
    """The far feathers of the tail, behind the coat: dark, a blue sheen,
    out of the duster's back vent and drooping."""
    base = _tail_root(pose)
    for i, (ang, length) in enumerate([(-80, 80), (-64, 94), (-48, 96), (-96, 70)]):
        _sickle(pen, pose, base, ang, length, 22.0 - i * 1.5, i, _a(SICKLE_SHEEN, 0.7))


def draw_tail_near(pen: Pen, pose: Pose) -> None:
    """The near feathers of the tail, over the coat's back panel."""
    base = _body_point(pose, (-30.0, -16.0))
    for i, (ang, length) in enumerate([(-72, 88), (-56, 72)]):
        _sickle(pen, pose, base, ang, length, 22.0 - 2.0 * i, i + 2, SICKLE_SHEEN)


def _hang(pose: Pose, top: Point, dx: float, length: float) -> Point:
    """Where cloth hanging from the body's ``top`` falls: down, turned a
    little with the body, blown back as he moves."""
    # Upright, it hangs; as he goes over, it goes with him.
    follow = 0.45 + 0.5 * min(1.0, max(0.0, (abs(pose.lean) - 25.0) / 45.0))
    return _add(_body_point(pose, top), _rot((dx - 6.0 * pose.cape, length), pose.lean * follow))


def draw_skirt_back(pen: Pen, pose: Pose) -> None:
    """The duster's skirt behind the legs, its lining in shade."""
    sw = 3.0 * math.sin(pose.phase * math.tau)
    pts = [_body_point(pose, (-38.0, -14.0)), _body_point(pose, (-10.0, -8.0)), _body_point(pose, (6.0, -6.0)),
           _hang(pose, (6.0, -6.0), 2.0 + sw, 52.0), _hang(pose, (-14.0, -8.0), -8.0 + sw, 58.0),
           _hang(pose, (-38.0, -14.0), -16.0 + sw, 56.0)]
    pen.shape(pts, COAT_DARK, 1.4, steps=4)
    pen.line([_hang(pose, (-14.0, -8.0), -6.0 + sw, 20.0), _hang(pose, (-14.0, -8.0), -8.0 + sw, 54.0)], _a(OUTLINE, 0.5), 1.0)


def draw_skirt_front(pen: Pen, pose: Pose) -> None:
    """The duster's near front panel, over the near thigh, brass along its
    edge."""
    sw = 3.0 * math.sin(pose.phase * math.tau + 0.8)
    top_a, top_b = (8.0, -8.0), (40.0, -6.0)
    pts = [_body_point(pose, top_a), _body_point(pose, (24.0, -4.0)), _body_point(pose, top_b),
           _hang(pose, top_b, 10.0 + sw, 46.0), _hang(pose, (24.0, -4.0), 4.0 + sw, 52.0), _hang(pose, top_a, -2.0 + sw, 50.0)]
    pen.shape(pts, COAT, 1.4, steps=4)
    pen.line([_body_point(pose, top_b), _hang(pose, top_b, 10.0 + sw, 46.0)], BRASS, 1.6)
    for k in range(3):
        pen.circle(_lerp(_body_point(pose, top_b), _hang(pose, top_b, 10.0 + sw, 46.0), 0.2 + 0.3 * k), 1.1, BRASS_LIGHT, 0.5)


def draw_leg(pen: Pen, pose: Pose, near: bool) -> None:
    hip, knee, ankle = _leg(pose, near)
    # The trousers, down over the hock; the bird's leg below them (the near
    # shin a piston).
    cloth = TROUSERS if near else TROUSERS_DARK
    pen.tube(hip, knee, 26.0, 18.0, cloth, 1.4)
    cuff = _lerp(knee, ankle, 0.55)
    if near:
        pen.tube(_lerp(knee, ankle, 0.4), ankle, 9.0, 7.0, STEEL_DARK, 1.2)
        pen.line([_lerp(knee, ankle, 0.5), _lerp(knee, ankle, 0.95)], STEEL_LIGHT, 1.4)
    else:
        pen.tube(_lerp(knee, ankle, 0.4), ankle, 10.0, 8.0, LEG, 1.2)
        for k in range(3):
            p = _lerp(knee, ankle, 0.62 + 0.12 * k)
            pen.line([_add(p, (-3.0, 0.0)), _add(p, (3.0, 1.0))], LEG_DARK, 1.0)
    pen.tube(knee, cuff, 18.0, 15.0, cloth, 1.4)
    pen.line([_add(knee, (-5.0, -2.0)), _add(knee, (4.0, 3.0))], _a(OUTLINE, 0.45), 1.0)
    pen.line([_add(cuff, (-7.0, 0.0)), _add(cuff, (7.0, 0.0))], _a(OUTLINE, 0.6), 1.2)
    # The foot: three toes forward, one back; the cowboy's spur strapped on.
    toes_fill = LEG if not near else STEEL
    for ang, length in [(-8, 18.0), (4, 22.0), (14, 16.0)]:
        tip = _add(ankle, _rot((length, 4.0), ang))
        pen.tube(ankle, tip, 6.0, 3.6, toes_fill, 1.1)
    pen.tube(ankle, _add(ankle, (-12.0, 3.0)), 5.0, 3.0, toes_fill, 1.0)
    strap = _lerp(ankle, knee, 0.1)
    pen.line([_add(strap, (-6.0, -1.0)), _add(strap, (6.0, 1.0))], LEATHER_DARK, 2.6)
    rowel = _add(strap, (-12.0, 1.0))
    pen.line([_add(strap, (-5.0, 0.0)), rowel], BRASS_DARK, 1.4)
    for k in range(6):
        a = k * 60 + pose.phase * 120
        pen.line([rowel, _add(rowel, _rot((0.0, -5.5), a))], BRASS_LIGHT, 1.0)
    pen.circle(rowel, 1.8, BRASS, 0.6)

def draw_revolver(pen: Pen, grip: Point, deg: float, scale: float = 1.0) -> Point:
    """A long-barrelled revolver held at ``grip``, pointing ``deg`` from straight
    down (90 is level, toward the facing). Returns the muzzle."""
    def at(x: float, y: float) -> Point:
        return _add(grip, _rot((x * scale, y * scale), deg - 90.0))
    pen.poly([at(-3, -2), at(4, -4), at(6, 10), at(0, 12)], WOOD, 1.1)
    pen.poly([at(2, -8), at(16, -8), at(16, 1), at(2, 1)], GUNMETAL, 1.1)
    pen.circle(at(9, -4), 4.6 * scale, STEEL, 1.0)
    pen.poly([at(15, -7), at(38, -7), at(38, -3), at(15, -3)], STEEL_DARK, 1.0)
    pen.poly([at(4, 1), at(8, 6), at(10, 1)], GUNMETAL, 0.8)
    return at(38, -5)


def draw_far_arm(pen: Pen, pose: Pose) -> Optional[Point]:
    """The gun arm: a coat sleeve with a brass cuff and a leather glove.
    Returns the revolver's muzzle when it is drawn."""
    sh, el, hand = _arm(pose, near=False)
    fdeg = _forearm_deg(pose, near=False)
    pen.tube(sh, el, 20.0, 16.0, COAT_DARK, 1.3)
    pen.tube(el, hand, 16.0, 13.0, COAT_DARK, 1.3)
    pen.line([_lerp(sh, el, 0.3), _lerp(sh, el, 0.9)], _a(COAT, 0.9), 2.0)
    cuff = _lerp(el, hand, 0.82)
    pen.tube(cuff, _lerp(el, hand, 0.95), 15.0, 14.0, BRASS_DARK, 1.0)
    muzzle = None
    if pose.revolver == "hand":
        muzzle = draw_revolver(pen, hand, fdeg, 1.35)
    pen.circle(hand, 6.4, GLOVE, 1.1)
    pen.tube(hand, _along(hand, fdeg + 40.0, 6.0), 4.4, 3.4, GLOVE, 0.9)
    return muzzle


def draw_holster(pen: Pen, pose: Pose, near: bool) -> None:
    """A holster on each hip, hung from the gun belt; a revolver's grip
    stands out of a full one."""
    top = _body_point(pose, (14.0, -4.0) if near else (-22.0, -6.0))
    d = pose.lean

    def at(x: float, y: float) -> Point:
        return _add(top, _rot((x, y), d * 0.5))
    pen.poly([at(-7, 0), at(8, 0), at(7, 28), at(1, 33), at(-5, 28)], LEATHER if near else LEATHER_DARK, 1.2)
    pen.line([at(-4, 22), at(4, 22)], BRASS, 1.0)
    full = (pose.revolver == "holster") if not near else not pose.near_gun
    if full:
        pen.poly([at(-5, 1), at(4, -1), at(1, -13), at(-7, -11)], WOOD, 1.1)
        pen.circle(at(-1, -2), 2.0, GUNMETAL, 0.6)


def draw_body(pen: Pen, pose: Pose) -> None:
    """The torso in the duster: riveted brown leather, brass along its seams,
    the vest at its open front; the marshal's star; the belts."""
    puff = pose.puff
    hot = pose.chest_glow

    def bp(x: float, y: float) -> Point:
        return _body_point(pose, (x + (6.0 * puff if x > 30 else 0.0), y))
    outline = [(-30, 6), (-38, -20), (-40, -50), (-34, -80), (-20, -96), (2, -102), (22, -98), (36, -82),
               (44, -56), (46, -30), (40, -6), (26, 8), (0, 10)]
    pen.shape([bp(*p) for p in outline], COAT, 1.6)
    # Shade down the back.
    pen.shape([bp(-30, 6), bp(-38, -20), bp(-40, -50), bp(-34, -80), bp(-22, -92), bp(-24, -60), bp(-20, -20), bp(-14, 6)],
              _a(COAT_DARK, 0.8), 0)
    # The open front: the vest and its buttons, brass along the coat's edge.
    vest = [bp(24, -96), bp(36, -82), bp(44, -56), bp(46, -30), bp(40, -8), bp(33, -8), bp(36, -30), bp(34, -56), bp(28, -78), bp(18, -92)]
    pen.shape(vest, VEST, 1.2, steps=4)
    for k in range(4):
        pen.circle(bp(39.0 + (2.0 if k in (1, 2) else 0.0), -74.0 + 16.0 * k), 1.3, BRASS_LIGHT, 0.5)
    pen.line([bp(18, -92), bp(28, -78), bp(34, -56), bp(36, -30), bp(33, -8)], BRASS, 1.6)
    # Seams and rivets.
    pen.line([bp(-6, -96), bp(-10, -60), bp(-8, -24)], _a(OUTLINE, 0.45), 1.0)
    for k in range(6):
        pen.circle(bp(-7.0 - 1.0 * math.sin(k), -88.0 + 13.0 * k), 1.1, BRASS_LIGHT, 0.5)
    # The star on the coat's breast, in its ring: he still wears it.
    sc = bp(18.0, -48.0)
    pen.circle(sc, 8.6, BRASS_DARK, 1.0)
    star = []
    for k in range(10):
        r = 8.0 if k % 2 == 0 else 3.4
        star.append(_add(sc, _rot((0.0, -r), k * 36 + pose.lean)))
    pen.poly(star, BRASS_LIGHT, 0.8, BRASS_DARK)
    pen.circle(sc, 1.4, BRASS, 0)
    # The waist belt and its big brass buckle.
    pen.poly([bp(-40, -30), bp(46, -26), bp(46, -17), bp(-40, -21)], LEATHER, 1.2)
    bk = bp(40.0, -21.5)
    pen.poly([_add(bk, (-6.0, -6.0)), _add(bk, (6.0, -6.0)), _add(bk, (6.0, 6.0)), _add(bk, (-6.0, 6.0))], BRASS_LIGHT, 1.0, BRASS_DARK)
    pen.poly([_add(bk, (-3.0, -3.0)), _add(bk, (3.0, -3.0)), _add(bk, (3.0, 3.0)), _add(bk, (-3.0, 3.0))], LEATHER_DARK, 0)
    # The gun belt slung lower, a row of brass rounds in its loops.
    pen.poly([bp(-38, -12), bp(42, -6), bp(42, 1), bp(-38, -5)], LEATHER_DARK, 1.1)
    for k in range(8):
        p = bp(-30.0 + 9.0 * k, -8.0 + 0.75 * k)
        pen.poly([_add(p, (-1.5, -3.2)), _add(p, (1.5, -3.2)), _add(p, (1.5, 2.2)), _add(p, (-1.5, 2.2))], BRASS, 0.6)
    if hot > 0.05:
        c = _shoulder(pose, near=True)
        _glow(pen.img, lambda d: d.ellipse((*_s((c[0] - 26, c[1] - 26)), *_s((c[0] + 26, c[1] + 26))), fill=_a((255, 110, 50, 255), 0.35 * hot)), 6.0)


def _hem(pose: Pose) -> List[Point]:
    """The poncho's hem, front to back (local points)."""
    p = pose.puff
    return [(46.0 + 6 * p, -60.0), (24.0, -55.0), (0.0, -57.0), (-24.0, -62.0), (-42.0, -66.0)]


def _band(pen: Pen, edge: Sequence[Point], up: Point, width: float) -> None:
    """The poncho's woven band along ``edge`` (world points): cream, with a
    red stepped zigzag."""
    top = [_add(q, (up[0] * width, up[1] * width)) for q in edge]
    pen.poly(list(edge) + top[::-1], PONCHO_BAND, 0.9)
    for a, b, ta, tb in zip(edge, edge[1:], top, top[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 7.0))
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            base0, base1 = _lerp(a, b, u0 + 0.12 / n), _lerp(a, b, u1 - 0.12 / n)
            peak = _lerp(_lerp(ta, tb, (u0 + u1) / 2), _lerp(a, b, (u0 + u1) / 2), 0.2)
            pen.poly([base0, peak, base1], PONCHO, 0)
            step = _lerp(_lerp(base0, base1, 0.5), peak, 0.55)
            pen.circle(step, 0.9, PONCHO_BAND, 0)


def _fringe(pen: Pen, edge: Sequence[Point], down: Point, length: float, phase: float) -> None:
    for a, b in zip(edge, edge[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 3.6))
        for k in range(n):
            p = _lerp(a, b, (k + 0.5) / n)
            sw = 1.5 * math.sin(phase * math.tau + k * 0.9)
            pen.line([p, _add(p, (down[0] * length + sw, down[1] * length))], PONCHO_DARK, 1.2)


def draw_cape(pen: Pen, pose: Pose) -> None:
    """The poncho's back flies out behind him like a cape: more as he moves.
    Its hem waves, and carries the band and the fringe."""
    flap = 0.5 + 0.5 * math.sin(pose.phase * math.tau) + pose.cape
    turn = pose.lean * 0.3
    root_a, root_b = _body_point(pose, (-16.0, -102.0)), _body_point(pose, (-40.0, -66.0))
    hem = []
    for k in range(5):
        t = k / 4.0
        wave = 4.0 * math.sin(pose.phase * math.tau * 2.0 + t * 4.0) * (0.4 + flap * 0.4)
        out = _rot((-(26.0 + 30.0 * flap) * (0.75 + 0.25 * t) + wave * 0.3, (6.0 - 14.0 * flap) + 34.0 * t + wave), turn)
        hem.append(_add(_lerp(root_a, root_b, t), out))
    pen.shape([root_a] + hem + [root_b], PONCHO_DARK, 1.4, steps=4)
    pen.shape([_lerp(root_a, hem[1], 0.3), hem[1], hem[2], _lerp(root_b, hem[3], 0.4)], _a(PONCHO, 0.55), 0, steps=4)
    edge = _smooth(hem, closed=False, steps=3)
    _band(pen, edge, _rot((0.85, -0.5), turn), 6.0)
    _fringe(pen, edge, _rot((-0.7, 0.7), turn), 5.0, pose.phase)


def draw_poncho(pen: Pen, pose: Pose) -> None:
    """The poncho round his shoulders, over the coat: red, a woven band
    along its hem, a fringe."""
    hem = [_body_point(pose, q) for q in _hem(pose)]
    top = [_body_point(pose, q) for q in [(-42.0, -86.0), (-26.0, -102.0), (0.0, -110.0), (24.0, -106.0), (40.0, -86.0)]]
    pen.shape(top + hem, PONCHO, 1.5, steps=5)
    # A fold of shade down the back and under the collar.
    pen.shape([_body_point(pose, q) for q in [(-42.0, -86.0), (-26.0, -100.0), (-18.0, -82.0), (-24.0, -64.0), (-42.0, -66.0)]],
              _a(PONCHO_DARK, 0.8), 0, steps=4)
    edge = _smooth(hem, closed=False, steps=3)
    _band(pen, edge, _rot((0.0, -1.0), pose.lean), 7.0)
    _fringe(pen, edge, _rot((0.0, 1.0), pose.lean * 0.6), 5.5, pose.phase)


def _comb(pen: Pen, at, sway: float) -> None:
    """The comb: big, red, its five lobes swept back like a crest."""
    pts = [at(-14, -12), at(-4, -16)]
    for k, (tx, ty) in enumerate(((2.0, -34.0), (-6.0, -48.0), (-18.0, -56.0), (-30.0, -52.0), (-38.0, -40.0))):
        tx += sway * (0.3 + 0.2 * k)
        pts += [at(tx + 3.0, ty + 2.0), at(tx + 1.0, ty - 1.6), at(tx - 2.4, ty - 1.2), at(tx - 3.4, ty + 2.4)]
        if k < 4:
            pts.append(at(tx - 4.0 - 1.0 * k, ty + 8.0))
    pts += [at(-30, -26), at(-20, -14)]
    pen.shape(pts, COMB, 1.3, steps=4)
    pen.shape([at(-12, -14), at(-6, -26), at(-16, -40), at(-28, -38), at(-22, -18)], _a(COMB_DARK, 0.7), 0, steps=4)


def draw_head(pen: Pen, pose: Pose) -> Tuple[Point, float]:
    """The head: a white face, red wattles, a yellow beak; the near half a
    riveted plate with a brass lens for an eye; a cigar. Returns the beak's
    tip and the head's angle."""
    c = _head_centre(pose)
    ang = pose.lean * 0.4 + pose.head

    def at(x: float, y: float) -> Point:
        return _add(c, _rot((x * HEAD, y * HEAD), ang))
    sway = 2.0 * math.sin(pose.phase * math.tau + 0.6)
    # The comb when the hat is off (on, it is drawn with the hat).
    if pose.hat_off > 0.0:
        _comb(pen, at, sway * 0.5)
    # The ruff: white feathers round the throat, over the poncho's collar.
    ruff = [at(-18, 2), at(-8, 10), at(4, 12), at(14, 8), at(12, 22), at(4, 28), at(-6, 24), at(-14, 26), at(-20, 16)]
    pen.shape(ruff, FEATHER, 1.3, steps=4)
    for k in range(5):
        p = at(-14 + 6 * k, 18 + 2 * math.sin(k))
        pen.line([_add(p, _rot((-2.0, -3.0), ang)), p, _add(p, _rot((2.0, -3.0), ang))], FEATHER_SHADE, 1.0)
    # The wattles under the beak: big, red.
    pen.shape([at(8, 8), at(18, 10), at(21 + sway * 0.3, 26), at(14 + sway * 0.3, 36), at(6, 26)], COMB, 1.3)
    pen.shape([at(3, 10), at(9, 13), at(9 + sway * 0.3, 27), at(2, 24)], COMB_DARK, 1.1)
    # The skull and the white face.
    pen.shape([at(-18, -2), at(-12, -16), at(4, -18), at(16, -10), at(19, 4), at(12, 14), at(-4, 15), at(-16, 10)], FEATHER, 1.5)
    pen.shape([at(-16, 6), at(-4, 12), at(8, 12), at(2, 8), at(-12, 2)], _a(FEATHER_SHADE, 0.7), 0)
    # The beak: upper and lower halves; the lower drops as it opens.
    gape = pose.beak * 20.0
    tip_up = at(34, 2)
    pen.poly([at(14, -6), at(26, -4), tip_up, at(30, 6), at(14, 5)], BEAK, 1.3)
    pen.line([at(16, -3), at(28, 0)], BEAK_DARK, 1.0)
    low = [at(14, 6), _add(c, _rot((28.0 * HEAD, 8.0 * HEAD), ang + gape)), _add(c, _rot((14.0 * HEAD, 11.0 * HEAD), ang + gape * 0.5))]
    pen.poly(low, BEAK_DARK, 1.2)
    if pose.beak > 0.2:
        pen.poly([at(15, 5), _add(c, _rot((25.0 * HEAD, 6.0 * HEAD), ang + gape * 0.7)), at(24, 5)], (120, 40, 40, 255), 0)
    # The far eye, beside the beak's ridge, and its brow: the expression.
    eye = at(12, -8)
    ex = pose.expression
    if ex == "pain":
        pen.line([_add(eye, (-3.0, 0.0)), _add(eye, (0.0, 1.5)), _add(eye, (3.0, -0.5))], EYE, 1.4)
    elif ex == "out":
        # Knocked out: a cross for an eye.
        pen.line([_add(eye, (-2.6, -2.6)), _add(eye, (2.6, 2.6))], EYE, 1.4)
        pen.line([_add(eye, (-2.6, 2.6)), _add(eye, (2.6, -2.6))], EYE, 1.4)
    else:
        r = 3.0 if ex in ("fury",) else 2.4
        pen.circle(eye, r, (250, 240, 214, 255), 0.9)
        pen.circle(_add(eye, (0.8, 0.2)), r * 0.62, EYE, 0)
        pen.circle(_add(eye, (1.4, -0.8)), 0.7, (255, 255, 255, 255), 0)
        if ex in ("smug", "hoarse"):
            pen.poly([_add(eye, (-3.6, -3.6)), _add(eye, (3.8, -3.0)), _add(eye, (3.8, 0.2)), _add(eye, (-3.6, -0.6))], FEATHER, 0)
    brow = {"menace": (-14, 4), "fury": (-24, 6), "pain": (16, 4), "smug": (-6, 3), "calm": (0, 3), "hoarse": (10, 4)}.get(ex, (0, 3))
    b0 = _add(eye, _rot((-5.0, -5.0), ang + brow[0]))
    b1 = _add(eye, _rot((5.0, -5.0), ang + brow[0]))
    pen.line([b0, b1], COMB_DARK, 2.0)
    # The machine half: a riveted plate from the eye back, a brass lens for an eye.
    plate = [at(-18, -2), at(-13, -15), at(0, -17), at(8, -6), at(6, 6), at(-2, 14), at(-15, 10)]
    pen.shape(plate, STEEL, 1.4)
    pen.shape([at(-15, -4), at(-10, -13), at(-2, -14), at(-6, 2), at(-14, 6)], _a(STEEL_LIGHT, 0.7), 0)
    for rx, ry in [(-14, 0), (-10, -11), (0, -14), (4, 4), (-10, 9)]:
        pen.circle(at(rx, ry), 1.1, STEEL_DARK, 0)
    lens = at(2, -4)
    pen.circle(lens, 6.6, BRASS, 1.3)
    pen.circle(lens, 4.4, (40, 22, 8, 255), 0.8)
    glow = pose.lens
    _glow(pen.img, lambda d: d.ellipse((*_s((lens[0] - 7, lens[1] - 7)), *_s((lens[0] + 7, lens[1] + 7))), fill=_a(LENS_GOLD, 0.55 * glow)), 2.4)
    pen.circle(lens, 3.0, _mix((90, 60, 16, 255), LENS_GOLD, glow), 0)
    pen.circle(_add(lens, (-1.2, -1.2)), 0.9, (255, 248, 220, 255), 0)
    if pose.cracked:
        pen.line([_add(lens, (-4.0, -3.0)), _add(lens, (0.0, 0.5)), _add(lens, (3.0, -1.0)), _add(lens, (4.0, 3.0))], (30, 20, 10, 255), 0.9)
    # The cigar in the corner of the beak, and its smoke.
    if pose.cigar and pose.beak < 0.35:
        a0, a1 = at(20, 6), at(33, 11)
        pen.tube(a0, a1, 3.4, 3.0, CIGAR, 0.9)
        pen.line([_lerp(a0, a1, 0.25), _lerp(a0, a1, 0.3)], BRASS, 3.0)
        pen.circle(a1, 1.6, ASH, 0.6)
        pen.circle(_add(a1, _rot((0.8, 0.0), ang)), 0.9, EMBER, 0)
        if pose.smoke > 0.01:
            for k in range(4):
                t = (pose.phase + k / 4.0) % 1.0
                q = _add(a1, (3.0 * math.sin(t * 6.0 + k) - 4.0 * t, -6.0 - 30.0 * t))
                pen.circle(q, 1.6 + 4.0 * t, _a(_mix(SMOKE, (220, 220, 220, 255), 0.6), pose.smoke * (1.0 - t) * 0.6), 0)
    return at(34, 2), ang


def draw_hat(pen: Pen, pose: Pose) -> None:
    c = _head_centre(pose)
    ang = pose.lean * 0.4 + pose.head - pose.hat_back
    lift = pose.hat_off
    if lift > 0.0:
        # It flies off and lands on its brim on the floor, turning over once
        # toward the side it falls.
        land = (Pose.x + pose.hat_land, FLOOR + 8.5 * HEAD)
        c = (c[0] + (land[0] - c[0]) * lift, c[1] + (land[1] - c[1]) * lift * lift - pose.hat_arc * math.sin(lift * math.pi))
        ang = ang * (1.0 - lift) + math.copysign(360.0, pose.hat_land) * lift

    def at(x: float, y: float) -> Point:
        return _add(c, _rot((x * HEAD, y * HEAD), ang))
    on_head = lift <= 0.0
    if on_head:
        # The comb bursts up out of the back of the hat, behind the crown: he
        # wears the hat forward over his eye and the comb will not be kept
        # under it.
        _comb(pen, lambda x, y: _add(_head_centre(pose), _rot((x * HEAD, y * HEAD), pose.lean * 0.4 + pose.head)),
              2.0 * math.sin(pose.phase * math.tau + 0.6))
        # The brim's shadow across the brow.
        pen.shape([at(-15, -11), at(16, -10), at(15, -5), at(-14, -6)], (40, 20, 10, 60), 0, steps=4)
    # The brim: a disc seen a little from above, its two ends curled up. The
    # crown stands on the middle of it.
    brim = [at(-42, -24), at(-32, -18.5), at(-16, -20), at(0, -20.5), at(18, -20), at(36, -18), at(47, -23),
            at(48, -18.5), at(36, -10.5), at(14, -8), at(0, -8), at(-16, -8.5), at(-32, -10.5), at(-43, -18)]
    pen.shape(brim, HAT, 1.5, steps=4)
    pen.shape([at(-41, -15), at(-32, -10.5), at(-16, -8.5), at(0, -8), at(14, -8), at(36, -10.5), at(46, -16),
               at(35, -13), at(14, -11), at(0, -11), at(-16, -11.5), at(-32, -13)], _a(HAT_DARK, 0.8), 0, steps=4)
    # The crown, its foot on the brim; worn, with a dent along the top.
    crown = [at(-15, -15.5), at(-14, -32), at(-10, -40), at(0, -37), at(10, -41), at(15, -33), at(16, -15.5),
             at(8, -14.2), at(0, -14), at(-8, -14.4)]
    pen.shape(crown, HAT, 1.5, steps=4)
    pen.shape([at(-12, -22), at(-11, -32), at(-7, -37), at(-2, -35), at(-4, -22)], _a(HAT_LIGHT, 0.8), 0, steps=4)
    pen.line([at(0, -36.5), at(1, -26)], HAT_DARK, 1.3)
    for rx, ry in ((-10, -30), (9, -33)):
        pen.line([at(rx, ry), at(rx + 3, ry + 2)], _a(HAT_DARK, 0.8), 0.9)
    # The band, its brass studs, and a star on it.
    band = [at(-15, -15.5), at(-8, -14.4), at(0, -14), at(8, -14.2), at(16, -15.5),
            at(16, -22), at(8, -20.8), at(0, -20.6), at(-8, -21), at(-15, -22)]
    pen.poly(band, LEATHER_DARK, 1.0)
    for k in range(4):
        x = -12 + 6.0 * k
        pen.circle(at(x, -18.2 + 0.004 * x * x), 1.2, BRASS_LIGHT, 0.5)
    sc = at(11, -18)
    star = [_add(sc, _rot((0.0, -(4.6 if k % 2 == 0 else 2.0) * HEAD), k * 36 + ang)) for k in range(10)]
    pen.poly(star, BRASS_LIGHT, 0.7, BRASS_DARK)


def _arm_heat(pose: Pose, c: RGBA) -> RGBA:
    return _mix(c, (230, 110, 60, 255), 0.55 * pose.chest_glow)


def draw_near_upper(pen: Pen, pose: Pose) -> None:
    """The machine arm's shoulder and upper arm, under the poncho."""
    sh, el, _hand = _arm(pose, near=True)
    pen.tube(sh, el, 16.0, 13.0, _arm_heat(pose, STEEL_DARK), 1.3)
    for t in (0.35, 0.7):
        p0, p1 = _lerp(sh, el, t - 0.12), _lerp(sh, el, t + 0.12)
        pen.tube(p0, p1, 17.0, 15.0, _arm_heat(pose, STEEL), 1.1)
        pen.line([_lerp(p0, p1, 0.2), _lerp(p0, p1, 0.8)], STEEL_LIGHT, 1.4)
    pen.circle(sh, 12.0, _arm_heat(pose, STEEL), 1.4)
    pen.circle(_add(sh, (-3.0, -3.0)), 5.0, _a(STEEL_LIGHT, 0.7), 0)
    for k in range(4):
        pen.circle(_add(sh, _rot((0.0, -9.0), 40 + k * 70)), 1.1, STEEL_DARK, 0)


def draw_near_lower(pen: Pen, pose: Pose) -> Point:
    """The machine arm's elbow, plated forearm and steel hand, over the
    poncho. Returns the muzzle of the gun it holds, or the hand."""
    _sh, el, hand = _arm(pose, near=True)
    fdeg = _forearm_deg(pose, near=True)
    pen.circle(el, 8.0, _arm_heat(pose, STEEL_DARK), 1.2)
    pen.circle(el, 3.0, BRASS, 0.6)
    pen.tube(el, hand, 16.0, 13.0, _arm_heat(pose, STEEL), 1.3)
    pen.line([_lerp(el, hand, 0.15), _lerp(el, hand, 0.7)], STEEL_LIGHT, 2.2)
    pen.tube(_lerp(el, hand, 0.78), _lerp(el, hand, 0.9), 15.0, 14.0, BRASS, 1.0)
    for t in (0.3, 0.55):
        pen.circle(_lerp(el, hand, t), 1.2, STEEL_DARK, 0)
    muzzle = _along(hand, fdeg, 10.0)
    if pose.near_gun:
        muzzle = draw_revolver(pen, hand, fdeg, 1.35)
        if pose.cylinder_out > 0.05:
            cyl = _add(_lerp(hand, muzzle, 0.25), _rot((0.0, 9.0 * pose.cylinder_out), fdeg - 90.0))
            pen.circle(cyl, 6.0, GUNMETAL, 1.1)
            for k in range(6):
                pen.circle(_add(cyl, _rot((0.0, -3.6), k * 60)), 1.3, (24, 22, 22, 255), 0)
    # The hand: a steel fist, the fingers plated.
    pen.circle(hand, 7.0, _arm_heat(pose, STEEL), 1.2)
    for k in range(3):
        knuckle = _along(hand, fdeg + 50 - 30 * k, 5.0)
        pen.circle(knuckle, 2.6, STEEL_LIGHT, 0.8)
    pen.tube(hand, _along(hand, fdeg - 60.0, 7.0), 4.4, 3.4, STEEL_LIGHT, 0.9)
    return muzzle

def draw_flash(pen: Pen, at: Point, deg: float, k: float) -> None:
    if k < 0.0:
        return
    size = 10.0 + 12.0 * (1.0 - abs(k - 0.4))
    _glow(pen.img, lambda d: d.ellipse((*_s((at[0] - size, at[1] - size)), *_s((at[0] + size, at[1] + size))), fill=_a(FLASH, 0.6)), 3.0)
    pts = []
    for i in range(10):
        r = size if i % 2 == 0 else size * 0.35
        pts.append(_add(at, _rot((0.0, -r), deg + i * 36)))
    pen.poly(pts, FLASH, 0)
    pen.circle(at, size * 0.3, WHITE_HOT, 0)
    # A streak along the shot.
    pen.line([at, _along(at, deg, size * 2.2)], _a(WHITE_HOT, 0.8), 1.6)


def draw_lasso(pen: Pen, pose: Pose, hand: Point) -> None:
    if pose.lasso == "none":
        return
    if pose.lasso == "twirl":
        c = (pose.x + 10.0, _head_centre(pose)[1] - 74.0)
        rx, ry = 40.0, 10.0
        # The loop, seen from the side, and the rope's run down to the hand.
        lead = (c[0] + rx * math.cos(pose.lasso_phase * math.tau), c[1] + ry * math.sin(pose.lasso_phase * math.tau))
        pen.ellipse(c, rx, ry, None, 2.4, ROPE_DARK)
        pen.ellipse(c, rx, ry, None, 1.2, ROPE)
        pen.stroke([hand, _lerp(hand, lead, 0.5), lead], ROPE, 2.0, 0.8)
        # The honda (the eye the rope runs through) on the loop.
        pen.circle(lead, 2.2, ROPE_DARK, 0.6)
    else:
        # Out toward the facing, to the frame's edge; taut when it yanks.
        reach = pose.lasso_reach if pose.lasso == "throw" else 1.0
        end = (hand[0] + 190.0 * reach, hand[1] + (8.0 if pose.lasso == "yank" else -30.0 + 40.0 * reach))
        mid = _lerp(hand, end, 0.5)
        if pose.lasso == "throw":
            mid = _add(mid, (0.0, -16.0 * (1.0 - reach)))
        pen.stroke(_smooth([hand, mid, end], closed=False, steps=6), ROPE, 2.0, 0.8)
        if pose.lasso == "throw":
            pen.ellipse(end, 12.0 + 6.0 * reach, 6.0, None, 2.4, ROPE_DARK)
            pen.ellipse(end, 12.0 + 6.0 * reach, 6.0, None, 1.2, ROPE)
        # The rope's coil, held in the wing.
        coil = _arm(pose, near=False)[2]
        for k in range(3):
            pen.ellipse(_add(coil, (2.0 * k, 2.0 * k)), 7.0, 10.0, None, 1.6, ROPE_DARK)


def draw_dynamite(pen: Pen, pose: Pose, hand: Point) -> None:
    if pose.dynamite <= 0:
        return
    fdeg = _forearm_deg(pose, near=True)
    tip = None
    for k in range(pose.dynamite):
        a = _add(hand, _rot((-4.0 + 4.0 * k, -2.0), fdeg - 90.0))
        b = _along(a, fdeg - 30.0, 30.0)
        pen.tube(a, b, 7.4, 7.4, DYNAMITE, 1.0)
        pen.line([_lerp(a, b, 0.3), _lerp(a, b, 0.32)], (240, 220, 190, 255), 7.0)
        tip = b
    if tip is not None and pose.fuse > 0.0:
        f = _add(tip, (3.0, -6.0))
        pen.line([tip, f], (60, 50, 40, 255), 1.0)
        r = 3.0 + 3.0 * pose.fuse
        _glow(pen.img, lambda d: d.ellipse((*_s((f[0] - r * 2, f[1] - r * 2)), *_s((f[0] + r * 2, f[1] + r * 2))), fill=_a(FLASH, 0.7)), 2.0)
        for i in range(6):
            pen.line([f, _add(f, _rot((0.0, -r * 1.4), i * 60 + pose.phase * 200))], FLASH, 0.8)
        pen.circle(f, 1.4, WHITE_HOT, 0)


def draw_crow(pen: Pen, pose: Pose, beak: Point, head_ang: float) -> None:
    """The crow (``steam``): rings of sound out of the open beak, and the
    shift's ring round him on the floor. The call (``call``): a short whistle
    through the beak."""
    if pose.steam > 0.0:
        k = pose.steam
        for i in range(4):
            r = 8.0 + 14.0 * i * (0.4 + 0.6 * k)
            pen.arc(beak, r, head_ang - 40.0, head_ang + 40.0, _a(STEAM, 0.9 * (1.0 - 0.2 * i)), 3.0)
    if pose.steam > 0.0 and pose.steam_ring:
        k = pose.steam
        ring_c = (pose.x + 10.0, FLOOR - 2.0)
        rr = 50.0 + 70.0 * k
        _glow(pen.img, lambda d: d.ellipse((*_s((ring_c[0] - rr, ring_c[1] - rr * 0.18)), *_s((ring_c[0] + rr, ring_c[1] + rr * 0.18))),
                                            outline=_a(STEAM, 0.8 * (1.0 - 0.5 * k)), width=int(8 * SUPER)), 3.0)
    if pose.call > 0.0:
        for i in range(3):
            t = (pose.call + i * 0.3) % 1.0
            r = 5.0 + 12.0 * t
            pen.arc(beak, r, head_ang - 30.0, head_ang + 30.0, _a(STEAM, 0.8 * (1.0 - t)), 2.0)


def draw_shells(pen: Pen, pose: Pose) -> None:
    if pose.shells < 0.0:
        return
    hand = _arm(pose, near=True)[2]
    for k in range(6):
        t = min(1.0, max(0.0, pose.shells * 1.4 - k * 0.08))
        x = hand[0] + 4.0 + 4.0 * k + 10.0 * t * math.sin(k * 2.1)
        y = hand[1] + (FLOOR - 4.0 - hand[1]) * t * t
        a = k * 50 + t * 400
        p0, p1 = _add((x, y), _rot((0.0, -3.0), a)), _add((x, y), _rot((0.0, 3.0), a))
        pen.stroke([p0, p1], BRASS_LIGHT, 2.2, 0.5)

def draw_cart(pen: Pen) -> None:
    """The ore cart he sits on when beaten (``seated``)."""
    x0, x1, top = 76.0, 236.0, FLOOR - 64.0
    pen.poly([(x0, top), (x1, top), (x1 - 12, FLOOR - 16), (x0 + 12, FLOOR - 16)], CART, 1.6)
    pen.poly([(x0 + 4, top + 4), (x1 - 4, top + 4), (x1 - 8, top + 12), (x0 + 8, top + 12)], _a(STEEL_DARK, 0.9), 0)
    for k in range(4):
        x = x0 + 22 + k * 36
        pen.line([(x, top + 2), (x - 3, FLOOR - 18)], STEEL_DARK, 1.2)
    for wx in (x0 + 34, x1 - 34):
        pen.circle((wx, FLOOR - 12.0), 11.0, GUNMETAL, 1.4)
        pen.circle((wx, FLOOR - 12.0), 3.0, STEEL_LIGHT, 0.8)
    for k in range(5):
        pen.circle((x0 + 30 + k * 22, top - 2.0), 8.0, ORE, 1.0)


# ---- one frame --------------------------------------------------------------------------------------------------

def draw_sparks(pen: Pen, pose: Pose) -> None:
    """Sparks thrown out of the machine shoulder by the blow that breaks him:
    they fly out and fall, and fade as they go. Black smoke after."""
    if pose.soot > 0.0:
        sh = _shoulder(pose, near=True)
        for k in range(4):
            t = (pose.phase * 2.0 + k / 4.0) % 1.0
            q = _add(sh, (-6.0 * t + 3.0 * math.sin(k * 2.0), -8.0 - 34.0 * t))
            pen.circle(q, 3.0 + 7.0 * t, _a(SOOT, 0.7 * pose.soot * (1.0 - t)), 0)
    if pose.sparks < 0.0:
        return
    k = pose.sparks
    c = _shoulder(pose, near=True)
    for i in range(11):
        a = -150.0 + i * 27.0 + 9.0 * math.sin(i * 2.3)
        speed = 46.0 + 18.0 * math.sin(i * 1.7)
        head = _add(c, (math.cos(math.radians(a)) * speed * k, math.sin(math.radians(a)) * speed * k + 60.0 * k * k))
        tail = _add(c, (math.cos(math.radians(a)) * speed * max(0.0, k - 0.18), math.sin(math.radians(a)) * speed * max(0.0, k - 0.18)
                        + 60.0 * max(0.0, k - 0.18) ** 2))
        fade = max(0.0, 1.0 - k * 0.9)
        pen.line([tail, head], _a(BRASS_LIGHT, fade), 2.2)
        pen.circle(head, 1.4, _a((255, 250, 220, 255), fade), 0)
    if k < 0.35:
        _glow(pen.img, lambda d: d.ellipse((*_s((c[0] - 22, c[1] - 22)), *_s((c[0] + 22, c[1] + 22))),
                                            fill=_a((255, 230, 150, 255), 0.7 * (1.0 - k / 0.35))), 6.0)


def _grounded_lying(pose: Pose) -> Pose:
    """Set the hip's height so that the lowest of the body, the feet and the
    tail's root rests on ``FLOOR``: for a body that is not standing."""
    flat = replace(pose, y=0.0)
    outline = [(-30.0, 6.0), (-38.0, -20.0), (-40.0, -50.0), (-34.0, -80.0), (-20.0, -96.0), (2.0, -102.0), (22.0, -98.0),
               (36.0, -82.0), (44.0, -56.0), (46.0, -30.0), (40.0, -6.0), (26.0, 8.0), (0.0, 10.0)]
    points = [_body_point(flat, q) for q in outline] + [_leg(flat, near)[2] for near in (True, False)]
    points.append(_add(_head_centre(flat), (0.0, 16.0 * HEAD)))
    # The coat's skirt, at its hem.
    points += [_hang(flat, (40.0, -6.0), 10.0, 46.0), _hang(flat, (8.0, -8.0), -2.0, 50.0), _hang(flat, (-38.0, -14.0), -16.0, 56.0)]
    lowest = max(q[1] for q in points)
    return replace(pose, y=FLOOR - 3.0 - lowest)


def draw_marshal(pose: Pose) -> Image.Image:
    """One frame. Back to front: the gun arm when it hangs, the poncho's
    back, the tail's far feathers, the coat's back skirt, the tail's near
    feathers, the far leg and holster, the coat, the near leg, the coat's
    front panel and the near holster, the gun arm when it reaches, the
    machine shoulder, the poncho, the head, the hat, the machine forearm,
    then what is in the hands and the effects."""
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    pen = Pen(img)
    if pose.seated:
        draw_cart(pen)
    # Turned a little toward us, he carries the gun arm at his back; reaching
    # forward, it crosses in front of the coat.
    reaching = pose.far_arm[0] + pose.lean > 50.0
    revolver_muzzle = None if reaching else draw_far_arm(pen, pose)
    draw_cape(pen, pose)
    draw_tail(pen, pose)
    draw_skirt_back(pen, pose)
    draw_tail_near(pen, pose)
    draw_leg(pen, pose, near=False)
    draw_holster(pen, pose, near=False)
    draw_body(pen, pose)
    draw_leg(pen, pose, near=True)
    draw_skirt_front(pen, pose)
    draw_holster(pen, pose, near=True)
    if reaching:
        revolver_muzzle = draw_far_arm(pen, pose)
    draw_near_upper(pen, pose)
    draw_poncho(pen, pose)
    beak_tip, head_ang = draw_head(pen, pose)
    if pose.hat_off <= 0.0:
        draw_hat(pen, pose)
    cannon = draw_near_lower(pen, pose)
    hand = _arm(pose, near=True)[2]
    draw_dynamite(pen, pose, hand)
    draw_lasso(pen, pose, hand)
    draw_shells(pen, pose)
    if pose.hat_off > 0.0:
        draw_hat(pen, pose)
    draw_crow(pen, pose, beak_tip, head_ang)
    if revolver_muzzle is not None:
        draw_flash(pen, revolver_muzzle, _forearm_deg(pose, near=False), pose.flash_far)
    draw_flash(pen, cannon, _forearm_deg(pose, near=True), pose.flash_near)
    draw_sparks(pen, pose)
    return img


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _pose_for(animation: str, i: int, n: int) -> Pose:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    base = Pose(phase=t, puff=0.15 + 0.1 * w, smoke=0.35, lens=0.6 + 0.15 * w)

    def g(p: Pose) -> Pose:
        return _grounded(p)

    if animation == "idle":
        # He stands wide, chest out, thumbs at his belt; his breath lifts the
        # chest and the pipes puff.
        return g(replace(base, lean=-4.0 + 1.5 * w, head=-2.0 * w, near_arm=(-6.0, 92.0 + 4 * w), far_arm=(-62.0, 96.0),
                         near_leg=(24.0, 38.0), far_leg=(-20.0, 26.0), puff=0.35 + 0.1 * w))
    if animation == "walk":
        # A strut: the head goes forward with each step, the legs wide.
        s = math.sin(t * math.tau)
        c = math.cos(t * math.tau)
        return g(replace(base, lean=4.0, neck_reach=4.0 + 4.0 * c, head=4.0 * c, x=192.0 + 2 * s,
                         near_leg=(10.0 + 26.0 * s, 34.0 + 14.0 * max(0.0, c)), far_leg=(10.0 - 26.0 * s, 34.0 + 14.0 * max(0.0, -c)),
                         near_arm=(4.0 - 20.0 * s, 50.0), far_arm=(-4.0 + 20.0 * s, 36.0), smoke=0.5))
    if animation == "quickdraw":
        if i <= 4:  # the tell: the wing drops to the holster; the lens lights
            k = _ease(i / 4.0)
            return g(replace(base, lean=-4.0 + 4.0 * k, far_arm=(-4.0 - 16.0 * k, 30.0 - 20.0 * k), near_arm=(8.0, 60.0),
                             expression="menace", lens=0.6 + 0.4 * k))
        if i <= 6:  # the draw: the gun comes up level
            k = (i - 4) / 2.0
            return g(replace(base, lean=4.0, far_arm=(-20.0 + 100.0 * k, 10.0 - 6.0 * k), revolver="hand", expression="fury", lens=1.0))
        if i <= 9:  # three shots
            k = i - 7
            return g(replace(base, lean=4.0 - 2.0 * k, far_arm=(80.0 - 6.0 * k, 6.0 + 4 * k), revolver="hand", expression="fury",
                             lens=1.0, flash_far=0.4, smoke=0.6))
        k = (i - 10) / 1.0  # recovery: he blows on the barrel, open
        return g(replace(base, lean=0.0, far_arm=(60.0 - 30.0 * k, 50.0), revolver="hand", head=8.0, expression="smug"))
    if animation == "spur_kick":
        if i <= 4:  # the tell: he rears back on the far leg, the near leg up
            k = _ease(i / 4.0)
            return g(replace(base, lean=-14.0 * k, near_leg=(18.0 - 50.0 * k, 34.0 + 50.0 * k), far_leg=(-6.0, 30.0),
                             near_arm=(8.0 - 30.0 * k, 50.0), far_arm=(-4.0 + 30.0 * k, 40.0), expression="menace", tail_spread=k))
        if i <= 7:  # the kick: the near leg straight out, the spur first
            k = (i - 5) / 2.0
            return g(replace(base, lean=-18.0 + 6.0 * k, near_leg=(80.0 + 14.0 * k, 4.0), far_leg=(-14.0, 26.0),
                             near_arm=(-30.0, 40.0), far_arm=(40.0, 30.0), expression="fury", tail_spread=1.0, lens=1.0))
        k = _ease((i - 8) / 3.0)  # recovery: the leg comes down slowly
        return g(replace(base, lean=-12.0 + 8.0 * k, near_leg=(90.0 - 72.0 * k, 4.0 + 30.0 * k), far_leg=(-14.0, 30.0),
                         near_arm=(-30.0 + 38.0 * k, 50.0), expression="calm", tail_spread=1.0 - k))
    if animation == "lasso":
        if i <= 7:  # the twirl: the near arm up, the loop turning over his hat
            return g(replace(base, lean=-6.0, near_arm=(168.0, 6.0 + 8 * math.sin(u * 20)), far_arm=(20.0, 70.0),
                             lasso="twirl", lasso_phase=i / 4.0, expression="smug", head=-6.0))
        if i <= 10:  # the throw: the arm comes over and the loop goes out
            k = (i - 7) / 3.0
            return g(replace(base, lean=-6.0 + 14.0 * k, near_arm=(150.0 - 70.0 * k, 20.0 - 10 * k), far_arm=(20.0, 70.0),
                             lasso="throw", lasso_reach=k, expression="menace", lens=1.0))
        k = (i - 11) / 2.0  # the yank: he leans back and hauls
        return g(replace(base, lean=-16.0 - 4.0 * k, near_arm=(60.0 - 30.0 * k, 50.0 + 20 * k), far_arm=(30.0, 80.0),
                         near_leg=(30.0, 30.0), far_leg=(-24.0, 40.0), lasso="yank", expression="fury", lens=1.0))
    if animation == "dynamite":
        if i <= 4:  # he lights three sticks off his cigar
            k = i / 4.0
            return g(replace(base, lean=6.0, near_arm=(70.0, 96.0 - 6.0 * k), far_arm=(10.0, 60.0), dynamite=3,
                             fuse=0.3 + 0.7 * k, expression="smug", head=8.0, smoke=0.6))
        if i <= 8:  # the throw: overhand
            k = (i - 5) / 3.0
            return g(replace(base, lean=6.0 - 22.0 * (1 - k) + 18.0 * k, near_arm=(170.0 - 110.0 * k, 10.0), far_arm=(-20.0, 40.0),
                             dynamite=3 if k < 0.6 else 0, fuse=1.0, expression="fury", lens=1.0))
        k = (i - 9) / 2.0
        return g(replace(base, lean=12.0 - 12.0 * k, near_arm=(60.0 - 40.0 * k, 30.0 + 30 * k), expression="smug"))
    if animation == "whistle":
        if i <= 5:  # he puffs the chest; the plates shake
            k = _ease(i / 5.0)
            shake = 1.5 * math.sin(i * 2.9) * k
            return g(replace(base, x=192.0 + shake, lean=-4.0 - 10.0 * k, puff=0.2 + 0.8 * k, head=-10.0 * k, near_arm=(-20.0 * k, 40.0),
                             far_arm=(-20.0 * k, 40.0), expression="menace", tail_spread=k, cape=0.5 * k))
        if i <= 9:  # the crow: the head thrown back, the beak wide, steam
            k = (i - 6) / 3.0
            return g(replace(base, lean=-16.0, puff=1.0, head=-30.0, beak=1.0, steam=0.3 + 0.7 * k, near_arm=(-40.0, 30.0),
                             far_arm=(-40.0, 30.0), expression="fury", tail_spread=1.0, lens=1.0, cape=1.0))
        k = (i - 10) / 1.0
        return g(replace(base, lean=-6.0, puff=0.5, head=-6.0 + 6 * k, beak=0.2, steam=0.0, expression="smug", tail_spread=0.4))
    if animation == "call":
        # A short whistle, two feathers to the beak: the tumbleweeds come.
        k = math.sin(u * math.pi)
        return g(replace(base, lean=-2.0, head=-6.0 * k, far_arm=(110.0 * k, 90.0 * k), near_arm=(8.0, 60.0), call=u, beak=0.3 * k,
                         expression="smug"))
    if animation == "high_noon":
        if i <= 5:  # he squares up: wide stance, both hands hovering
            k = _ease(i / 5.0)
            return g(replace(base, lean=2.0 * k, near_leg=(18.0 + 10 * k, 34.0), far_leg=(-14.0 - 10 * k, 30.0),
                             near_arm=(8.0 + 8.0 * k, 60.0 - 40 * k), far_arm=(-4.0 - 14.0 * k, 30.0 - 20.0 * k),
                             expression="menace", lens=0.7 + 0.3 * k, head=6.0 * k, tail_spread=k))
        if i <= 13:  # six shots, high and low by turns, both guns
            k = i - 6
            high = k % 2 == 0
            return g(replace(base, lean=4.0, near_leg=(28.0, 34.0), far_leg=(-24.0, 30.0), revolver="hand", near_gun=True, cape=0.6,
                             near_arm=(84.0 if high else 120.0, 4.0), far_arm=(96.0 if not high else 70.0, 4.0),
                             flash_near=0.4 if k % 2 == 1 else -1.0, flash_far=0.4 if k % 2 == 0 else -1.0,
                             expression="fury", lens=1.0, smoke=0.9, tail_spread=1.0))
        return g(replace(base, lean=2.0, near_leg=(28.0, 34.0), far_leg=(-24.0, 30.0), revolver="hand", near_gun=True,
                         near_arm=(100.0, 10.0), far_arm=(90.0, 10.0), expression="smug", lens=0.8, smoke=1.0, tail_spread=0.6))
    if animation == "reload":
        # The cylinder swings out of the revolver in the machine hand; the
        # shells fall; he fills it.
        k = math.sin(u * math.pi)
        return g(replace(base, lean=6.0, head=14.0, near_arm=(40.0, 90.0), far_arm=(20.0, 100.0), cylinder_out=k, near_gun=True,
                         shells=u if u < 0.7 else -1.0, expression="calm", lens=0.4, smoke=0.2))
    if animation == "enrage":
        # High noon comes: he pushes his hat back, his chest goes hot, the
        # pipes pour smoke and his lens burns.
        k = _ease(u * 1.4)
        shake = 2.0 * math.sin(i * 2.7) * k
        return g(replace(base, x=192.0 + shake, lean=-10.0 * k, puff=0.4 + 0.6 * k, head=-12.0 * k, hat_back=16.0 * k,
                         near_arm=(8.0 + 30.0 * k, 60.0 - 40 * k), far_arm=(-4.0 - 40.0 * k, 30.0), chest_glow=k, lens=1.0,
                         smoke=0.4 + 0.6 * k, tail_spread=k, beak=0.5 * k, expression="fury"))
    if animation == "turn":
        k = math.sin(u * math.pi)
        return g(replace(base, lean=-4.0 * (1 - k), head=0.0, near_arm=(8.0 - 8.0 * k, 50.0), far_arm=(-4.0 + 4.0 * k, 40.0)))
    if animation == "hurt":
        k = 1.0 - u
        return g(replace(base, lean=-14.0 * k, head=-16.0 * k, near_arm=(-30.0 * k, 50.0), far_arm=(-30.0 * k, 50.0), expression="pain",
                         lens=1.0, x=188.0 - 4 * k, tail_spread=0.6 * k))
    if animation == "death":
        # A death worthy of him, in four beats. The blow: it throws him back,
        # knocks his hat off behind him and the whistle shrieks; sparks fly
        # off the plate. The sputter: the whistle cracks, the pipes cough
        # soot, the lens flickers and he staggers forward. The knee: down on
        # the machine knee, a claw to the ground. The fall: he goes over on
        # his face, the tail up and the legs stiff behind him; a foot twitches,
        # a last wisp leaves the whistle, the lens goes out. The last frame is
        # held: it is what lies in the corral after.
        hat = dict(hat_off=min(1.0, i / 7.0) if i >= 1 else 0.0, hat_land=-112.0, hat_arc=110.0)
        if i <= 3:
            k = _ease(i / 3.0)
            return g(replace(base, x=192.0 - 8.0 * k, lean=-4.0 - 16.0 * k, head=-6.0 - 26.0 * k, beak=1.0, puff=0.6 + 0.4 * k,
                             steam=0.5 + 0.5 * k, steam_ring=False, near_arm=(8.0 - 60.0 * k, 50.0 - 30.0 * k),
                             far_arm=(-4.0 - 56.0 * k, 40.0 - 20.0 * k), near_leg=(16.0 + 6.0 * k, 34.0), far_leg=(-10.0 - 8.0 * k, 30.0),
                             tail_spread=k, expression="pain", lens=1.0, sparks=i / 3.0 * 0.6, cape=k, cigar=i == 0,
                             smoke=0.0, **hat))
        if i <= 8:
            k = _ease((i - 3) / 5.0)
            flicker = 1.0 if i % 2 == 0 else 0.15
            return g(replace(base, x=184.0 + 10.0 * k, lean=-20.0 + 34.0 * k, head=-32.0 + 54.0 * k, beak=0.5 * (1.0 - k),
                             puff=1.0 - 0.8 * k, cracked=True, cigar=False, cape=1.0 - 0.6 * k,
                             sparks=0.6 + 0.12 * (i - 3) if i <= 5 else -1.0,
                             near_arm=(-52.0 + 62.0 * k, 20.0 - 10.0 * k), far_arm=(-60.0 + 66.0 * k, 20.0 - 6.0 * k),
                             near_leg=(22.0 + 6.0 * k, 34.0 + 30.0 * k), far_leg=(-18.0 + 8.0 * k, 30.0 + 14.0 * k),
                             tail_spread=1.0 - 0.6 * k, expression="pain", lens=flicker, smoke=0.0, soot=1.0, **hat))
        if i <= 12:
            k = _ease((i - 8) / 4.0)
            return g(replace(base, x=194.0, lean=14.0 + 8.0 * k, head=22.0 + 6.0 * k, cracked=True,
                             near_arm=(10.0 + 18.0 * k, 10.0 - 26.0 * k), far_arm=(6.0 + 10.0 * k, 14.0),
                             near_leg=(28.0 + 52.0 * k, 64.0 + 62.0 * k), far_leg=(-10.0 + 30.0 * k, 44.0 + 10.0 * k),
                             tail_spread=0.4 * (1.0 - k), expression="hoarse", lens=0.5 if i % 2 else 0.25, cigar=False,
                             smoke=0.0, soot=1.0 - 0.4 * k, **hat))
        if i <= 16:
            k = _ease((i - 12) / 4.0)
            return _grounded_lying(replace(base, x=194.0 - 8.0 * k, lean=22.0 + 58.0 * k, head=28.0 - 22.0 * k, cracked=True,
                             near_arm=(28.0 - 196.0 * k, -16.0 + 24.0 * k), far_arm=(16.0 - 186.0 * k, 14.0 - 4.0 * k),
                             near_leg=(80.0 - 190.0 * k, 126.0 - 110.0 * k), far_leg=(20.0 - 136.0 * k, 54.0 - 34.0 * k),
                             tail_spread=0.5 * k, tail_lean=0.6 - 0.3 * k, beak=0.4 * k,
                             expression="hoarse" if k < 0.5 else "out", lens=0.2 * (1.0 - k), smoke=0.0, cigar=False,
                             soot=0.6 * (1.0 - k), **hat))
        # The end: on his face, tail up, legs stiff behind; a twitch, a last
        # wisp, the lens out.
        twitch = {17: 8.0, 18: -4.0}.get(i, 0.0)
        return _grounded_lying(replace(base, x=186.0, lean=80.0, head=6.0, cracked=True, phase=0.3 + 0.15 * (i - 17),
                         near_arm=(-168.0, 8.0), far_arm=(-170.0, 10.0), near_leg=(-110.0 + twitch, 16.0), far_leg=(-116.0, 20.0),
                         tail_spread=0.5, tail_lean=0.3, beak=0.4, expression="out", lens=0.0, smoke=0.0, steam=0.0, cigar=False,
                         soot=0.35 if i < 19 else 0.0, **hat))
    if animation == "seated":
        # Beaten: on an ore cart, hoarse, the lens cracked. The hat
        # on his knee... his hat back on, low.
        p = replace(base, lean=6.0, head=10.0 + 3 * w, near_leg=(84.0, 80.0), far_leg=(74.0, 70.0), near_arm=(40.0, 70.0),
                    far_arm=(30.0, 60.0), cracked=True, expression="hoarse", lens=0.35, smoke=0.15, puff=0.0)
        return replace(p, y=FLOOR - 64.0 - 4.0, seated=True)
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    img = draw_marshal(_pose_for(animation, frame_index, nframes))
    if animation == "turn" and frame_index / max(1, nframes - 1) > 0.5:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Marshal Gallus"},
    "body": {
        "body_plan": "AvianBiped",
        "body_kind": "Robot",
        "mass_class": "Heavy",
        "traits": ["boss", "rooster", "cyborg", "frontier", "western"],
        "locomotion_hint": "Walk",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["frontier", "boss", "rooster", "cyborg", "western"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
