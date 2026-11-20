"""Marshal Gallus: the boss of the Frontier dimension (gate address
LEADENSADDLE), the marshal of Dry Dock and the boss of its refinery
(`docs/planning/game/leadensaddle.md`).

Jon, 2026-11-20: a robot rooster between a big chicken and a man with a
chicken's head. So the body plan is a rooster's (a deep keel of a chest, a
short body tipped up, legs with the joint that bends back, a fan of tail
feathers) and the stance is a man's (upright, legs wide, chest out). His
wings are arms. The near side of him is machine (a plate over half of the
face with a brass lens for an eye, a piston arm with a six-chamber cylinder
on the forearm, a piston shin); the far side is bird (a wing whose long
feathers close round the grip of a revolver, a scaled leg).

His kit: a wide flat-brimmed hat with a band of brass studs (the comb comes up
through a slit in the crown), a red bandana, a riveted chest plate like the
end of a boiler with a marshal's star on it, a bandolier, a gun belt with a
holster, cowboy spurs strapped over his own. His voice box is a steam
whistle between his shoulders: he crows with it. Three exhaust pipes curve
up among his sickle feathers and puff smoke.

A PAPER DOLL: every part is its own drawing, posed from one ``Pose`` per
frame. Back to front: the tail and its pipes, the far leg, the far (wing)
arm and its revolver, the body, the bandolier and belt, the hackle, the
whistle, the head and its hat, the near leg, the near (machine) arm, then
the effects (muzzle flashes, the lasso, the dynamite's fuse, steam).

Rows: ``idle`` 8; ``walk`` 8 (a strut); ``quickdraw`` 12 (tell 0-4: the wing
to the holster; draw 5-6; three shots 7-9; recovery 10-11); ``spur_kick``
12 (tell 0-4: he rears back on the far leg; kick 5-7; recovery 8-11);
``lasso`` 14 (twirl 0-7; throw 8-10; the yank 11-13); ``dynamite`` 12
(light 0-4; the throw 5-8; recovery 9-11); ``whistle`` 12 (puff 0-5; the crow
6-9; recovery 10-11); ``call`` 8 (a short whistle: the tumbleweeds);
``high_noon`` 16 (he squares up 0-5; six shots, high and low, 6-13; 14-15
he holds); ``reload`` 10 (the cylinder swings out, the shells fall);
``enrage`` 12 (he pushes his hat back and his chest glows); ``turn`` 6;
``hurt`` 3; ``death`` 14 (the whistle cracks, he goes down on one knee, the
hat falls); ``seated`` 8 (beaten, on an ore cart, hoarse).

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
    ("death", 14, 105),
    ("seated", 8, 160),
]

OUTLINE: RGBA = (34, 22, 20, 255)
FEATHER: RGBA = (238, 222, 186, 255)
FEATHER_SHADE: RGBA = (202, 176, 132, 255)
FEATHER_DARK: RGBA = (156, 126, 88, 255)
HACKLE: RGBA = (226, 150, 62, 255)
HACKLE_DARK: RGBA = (178, 98, 40, 255)
WING: RGBA = (176, 100, 48, 255)
WING_DARK: RGBA = (122, 64, 30, 255)
WING_LIGHT: RGBA = (214, 150, 86, 255)
SICKLE: RGBA = (30, 44, 40, 255)
SICKLE_SHEEN: RGBA = (60, 112, 96, 255)
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
HAT: RGBA = (196, 160, 108, 255)
HAT_DARK: RGBA = (146, 112, 70, 255)
HAT_LIGHT: RGBA = (224, 194, 142, 255)
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
    dark outline (``line`` is the outline's width in frame pixels)."""

    def __init__(self, img: Image.Image):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def poly(self, pts: Sequence[Point], fill: RGBA, line: float = 1.4, outline: RGBA = OUTLINE) -> None:
        sp = [_s(p) for p in pts]
        if len(sp) < 3:
            return
        self.d.polygon(sp, fill=fill)
        if line > 0:
            self.d.line(sp + [sp[0]], fill=outline, width=max(1, int(line * SUPER)), joint="curve")

    def shape(self, pts: Sequence[Point], fill: RGBA, line: float = 1.4, outline: RGBA = OUTLINE, steps: int = 8) -> None:
        self.poly(_smooth(pts, True, steps), fill, line, outline)

    def circle(self, c: Point, r: float, fill: RGBA, line: float = 1.2, outline: RGBA = OUTLINE) -> None:
        box = (*_s((c[0] - r, c[1] - r)), *_s((c[0] + r, c[1] + r)))
        self.d.ellipse(box, fill=fill, outline=outline if line > 0 else None, width=max(1, int(line * SUPER)) if line > 0 else 0)

    def ellipse(self, c: Point, rx: float, ry: float, fill: Optional[RGBA], line: float = 1.2, outline: RGBA = OUTLINE) -> None:
        box = (*_s((c[0] - rx, c[1] - ry)), *_s((c[0] + rx, c[1] + ry)))
        self.d.ellipse(box, fill=fill, outline=outline if line > 0 else None, width=max(1, int(line * SUPER)) if line > 0 else 0)

    def line(self, pts: Sequence[Point], fill: RGBA, width: float) -> None:
        self.d.line([_s(p) for p in pts], fill=fill, width=max(1, int(width * SUPER)), joint="curve")

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
    fn(ImageDraw.Draw(layer, "RGBA"))
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
    return _body_point(pose, (16.0, -70.0) if near else (-24.0, -80.0))


def _neck_top(pose: Pose) -> Point:
    return _body_point(pose, (18.0 + pose.neck_reach, -120.0))


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

def draw_tail(pen: Pen, pose: Pose) -> None:
    base = _body_point(pose, (-36.0, -46.0))
    spread = pose.tail_spread
    # Sickle feathers: long dark arcs up and back, drooping at their tips.
    for i, (ang, length) in enumerate([(-58, 74), (-42, 88), (-26, 92), (-12, 80), (4, 64), (-70, 56)]):
        a = ang - 8 * spread + pose.lean * 0.6
        sway = 3.0 * math.sin(pose.phase * math.tau + i)
        p1 = _add(base, _rot((0.0, -length * 0.55), a))
        p2 = _add(base, _rot((-length * 0.25, -length * 0.95), a))
        tip = _add(p2, (-12.0 + sway, 22.0 + i * 2))
        spine = _smooth([base, p1, p2, tip], closed=False, steps=6)
        width = 12.0 - i * 0.6
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
        pen.line(spine[1:-2], _a(SICKLE_SHEEN, 0.9), 1.6)
    # Three exhaust pipes curve up among them; soot at their mouths.
    for j, (dx, h) in enumerate([(-6.0, 62.0), (-18.0, 72.0), (-30.0, 58.0)]):
        root = _add(base, (dx * 0.3 + 6.0, 6.0))
        bend = _add(root, _rot((dx, -h * 0.6), pose.lean * 0.5))
        mouth = _add(bend, _rot((dx * 0.6 - 10.0, -h * 0.38), pose.lean * 0.5))
        pts = _smooth([root, bend, mouth], closed=False, steps=6)
        pen.stroke(pts, STEEL, 6.0, 1.2)
        pen.line(pts, _a(STEEL_LIGHT, 0.8), 1.4)
        pen.ellipse(mouth, 4.0, 2.4, STEEL_DARK, 1.0)
        pen.ellipse(mouth, 2.4, 1.3, (20, 18, 18, 255), 0)
        # Smoke puffs drift up and back from each mouth.
        if pose.smoke > 0.01:
            for k in range(3):
                t = (pose.phase + k / 3.0 + j * 0.21) % 1.0
                c = _add(mouth, (-10.0 * t - 2.0, -26.0 * t - 3.0))
                r = 3.0 + 7.0 * t
                pen.circle(c, r, _a(SMOKE, pose.smoke * (1.0 - t) * 0.75), 0)


def draw_leg(pen: Pen, pose: Pose, near: bool) -> None:
    hip, knee, ankle = _leg(pose, near)
    # The thigh: a feathered drumstick, its trousers of feathers down to the hock.
    thigh_fill = FEATHER_SHADE if not near else FEATHER
    pen.tube(hip, knee, 30.0, 16.0, thigh_fill, 1.4)
    for k in range(3):
        p = _lerp(hip, knee, 0.45 + 0.18 * k)
        pen.line([_add(p, (-6.0, 0.0)), _add(p, (2.0, 5.0)), _add(p, (8.0, 1.0))], FEATHER_DARK, 1.0)
    # The shank: scaled bird leg (far) or a piston (near).
    if near:
        pen.tube(knee, _lerp(knee, ankle, 0.55), 12.0, 10.0, STEEL_DARK, 1.3)
        pen.tube(_lerp(knee, ankle, 0.35), ankle, 6.0, 6.0, STEEL_LIGHT, 1.1)
        pen.circle(knee, 6.0, STEEL, 1.2)
        pen.circle(knee, 2.0, BRASS, 0)
    else:
        pen.tube(knee, ankle, 12.0, 9.0, LEG, 1.3)
        for k in range(4):
            p = _lerp(knee, ankle, 0.2 + 0.2 * k)
            pen.line([_add(p, (-4.0, 0.0)), _add(p, (4.0, 1.0))], LEG_DARK, 1.0)
    # The foot: three toes forward, one back; the spur on the back of the shank,
    # and the cowboy's spur (a strap and a rowel) at the heel.
    toes_fill = LEG if not near else STEEL
    for ang, length in [(-8, 18.0), (4, 22.0), (14, 16.0)]:
        tip = _add(ankle, _rot((length, 4.0), ang))
        pen.tube(ankle, tip, 6.0, 3.6, toes_fill, 1.1)
    pen.tube(ankle, _add(ankle, (-12.0, 3.0)), 5.0, 3.0, toes_fill, 1.0)
    spur_root = _lerp(ankle, knee, 0.28)
    pen.poly([_add(spur_root, (-2.0, -3.0)), _add(spur_root, (-12.0, 1.0)), _add(spur_root, (-2.0, 3.0))], (236, 226, 200, 255), 1.0)
    strap = _lerp(ankle, knee, 0.12)
    pen.line([_add(strap, (-6.0, -1.0)), _add(strap, (6.0, 1.0))], LEATHER_DARK, 2.6)
    rowel = _add(strap, (-11.0, 1.0))
    pen.line([_add(strap, (-5.0, 0.0)), rowel], STEEL_DARK, 1.4)
    for k in range(6):
        a = k * 60 + pose.phase * 120
        pen.line([rowel, _add(rowel, _rot((0.0, -5.0), a))], STEEL_LIGHT, 1.0)
    pen.circle(rowel, 1.6, BRASS, 0.6)


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
    """The wing arm. Returns the revolver's muzzle when it is drawn."""
    sh, el, hand = _arm(pose, near=False)
    fdeg = _forearm_deg(pose, near=False)
    # The flight feathers first, so the coverts lie over their roots.
    for k in range(5):
        root = _lerp(el, hand, 0.25 + 0.17 * k)
        tip = _along(root, fdeg - 150.0 + k * 8, 30.0 - k * 2)
        pen.tube(root, tip, 8.0, 2.4, SICKLE, 1.0)
        pen.line([root, _lerp(root, tip, 0.8)], _a(SICKLE_SHEEN, 0.8), 1.0)
    pen.tube(sh, el, 24.0, 16.0, WING, 1.3)
    pen.tube(el, hand, 16.0, 11.0, WING, 1.3)
    for k in range(3):
        p = _lerp(sh, el, 0.3 + 0.25 * k)
        pen.line([_add(p, (-5.0, -2.0)), _add(p, (0.0, 3.0)), _add(p, (5.0, -1.0))], WING_DARK, 1.0)
    # The long flight feathers fan back from the forearm; closed round the grip
    # (the "fingers") when it holds the gun.
    muzzle = None
    if pose.revolver == "hand":
        muzzle = draw_revolver(pen, hand, fdeg, 1.35)
    for k in range(3):
        tip = _along(hand, fdeg + 30 - k * 26, 11.0)
        pen.tube(hand, tip, 6.0, 2.6, WING_LIGHT, 1.0)
    return muzzle


def draw_holster(pen: Pen, pose: Pose) -> None:
    top = _body_point(pose, (-14.0, -4.0))
    pen.poly([_add(top, (-6.0, 0.0)), _add(top, (8.0, 0.0)), _add(top, (6.0, 26.0)), _add(top, (-2.0, 30.0))], LEATHER, 1.2)
    if pose.revolver == "holster":
        pen.poly([_add(top, (-4.0, 0.0)), _add(top, (5.0, -2.0)), _add(top, (3.0, -12.0)), _add(top, (-5.0, -10.0))], WOOD, 1.1)
    pen.line([_add(top, (-4.0, 6.0)), _add(top, (6.0, 6.0))], LEATHER_DARK, 1.2)


def draw_body(pen: Pen, pose: Pose) -> None:
    puff = pose.puff
    outline = [(-40.0, -2.0), (-8.0, 10.0), (24.0, 4.0), (44.0, -18.0), (54.0 + 8 * puff, -48.0 - 2 * puff),
               (46.0 + 4 * puff, -80.0), (24.0, -96.0), (-6.0, -98.0), (-30.0, -78.0), (-44.0, -40.0)]
    pen.shape([_body_point(pose, p) for p in outline], FEATHER, 1.6)
    # Shade along the back and under the belly.
    shade = [(-40.0, -2.0), (-8.0, 10.0), (14.0, 6.0), (-6.0, -6.0), (-30.0, -30.0), (-38.0, -70.0), (-44.0, -40.0)]
    pen.shape([_body_point(pose, p) for p in shade], _a(FEATHER_SHADE, 0.85), 0)
    # Feather scallops on the back.
    for k in range(5):
        p = _body_point(pose, (-28.0 + 3 * k, -24.0 - 12 * k))
        pen.line([_add(p, (-6.0, -3.0)), _add(p, (0.0, 3.0)), _add(p, (6.0, -2.0))], FEATHER_DARK, 1.0)
    # The chest plate: a riveted boiler end over the keel, the marshal's star on it.
    glow = pose.chest_glow
    plate = [(14.0, -14.0), (40.0, -20.0), (51.0 + 8 * puff, -48.0 - 2 * puff), (44.0 + 4 * puff, -78.0), (24.0, -90.0), (10.0, -64.0)]
    pen.shape([_body_point(pose, p) for p in plate], _mix(PLATE, (255, 120, 60, 255), glow * 0.6), 1.5)
    hi = [(30.0, -28.0), (44.0 + 6 * puff, -46.0), (40.0 + 3 * puff, -70.0), (30.0, -60.0)]
    pen.shape([_body_point(pose, p) for p in hi], _a(_mix(PLATE_LIGHT, (255, 190, 110, 255), glow), 0.9), 0)
    for (rx, ry) in [(18, -20), (36, -24), (47, -48), (41, -74), (24, -84), (13, -60), (16, -40)]:
        pen.circle(_body_point(pose, (rx + (6 * puff if rx > 30 else 0), ry)), 1.5, BRASS_LIGHT, 0.7)
    if glow > 0.05:
        c = _body_point(pose, (32.0, -52.0))
        _glow(pen.img, lambda d: d.ellipse((*_s((c[0] - 24, c[1] - 30)), *_s((c[0] + 24, c[1] + 30))), fill=_a((255, 110, 50, 255), 0.45 * glow)), 6.0)
    # The star: a five-point brass star in a ring.
    sc = _body_point(pose, (33.0 + 4 * puff, -56.0))
    pen.circle(sc, 8.0, BRASS, 1.1)
    star = []
    for k in range(10):
        r = 7.0 if k % 2 == 0 else 3.0
        star.append(_add(sc, _rot((0.0, -r), k * 36 + pose.lean)))
    pen.poly(star, BRASS_LIGHT, 0.8, BRASS_DARK)
    # The gun belt round the lower body, its buckle in front.
    belt = [(-42.0, -12.0), (24.0, -8.0), (40.0, -14.0), (42.0, -6.0), (24.0, 2.0), (-40.0, -2.0)]
    pen.poly([_body_point(pose, p) for p in belt], LEATHER, 1.2)
    for k in range(6):
        p = _body_point(pose, (-30.0 + 10 * k, -7.5 + 0.4 * k))
        pen.poly([_add(p, (-1.6, -3.0)), _add(p, (1.6, -3.0)), _add(p, (1.6, 2.4)), _add(p, (-1.6, 2.4))], BRASS, 0.6)
    bk = _body_point(pose, (36.0, -8.0))
    pen.poly([_add(bk, (-5.0, -5.0)), _add(bk, (5.0, -5.0)), _add(bk, (5.0, 5.0)), _add(bk, (-5.0, 5.0))], BRASS_LIGHT, 1.0, BRASS_DARK)
    # The bandolier across the plate, far shoulder to near hip.
    a, b = _body_point(pose, (-4.0, -92.0)), _body_point(pose, (36.0, -14.0))
    pen.stroke([a, _lerp(a, b, 0.5), b], LEATHER_DARK, 7.0, 1.0)
    for k in range(7):
        p = _lerp(a, b, 0.12 + 0.12 * k)
        pen.poly([_add(p, _rot((-1.8, -4.0), pose.lean + 28)), _add(p, _rot((1.8, -4.0), pose.lean + 28)),
                  _add(p, _rot((1.8, 3.0), pose.lean + 28)), _add(p, _rot((-1.8, 3.0), pose.lean + 28))], BRASS, 0.6)


def draw_whistle(pen: Pen, pose: Pose) -> Point:
    """The steam whistle between his shoulders. Returns its mouth."""
    base = _body_point(pose, (-16.0, -92.0))
    bell_top = _body_point(pose, (-20.0, -124.0))
    pen.tube(base, _lerp(base, bell_top, 0.5), 7.0, 6.0, BRASS_DARK, 1.1)
    bt = _lerp(base, bell_top, 0.45)
    if pose.cracked:
        bell_top = _add(bell_top, (-9.0, 4.0))
    pen.tube(bt, bell_top, 11.0, 10.0, BRASS, 1.2)
    pen.line([_lerp(bt, bell_top, 0.2), _lerp(bt, bell_top, 0.8)], BRASS_LIGHT, 1.6)
    pen.ellipse(bell_top, 5.5, 2.2, BRASS_LIGHT, 1.0)
    if pose.cracked:
        mid = _lerp(bt, bell_top, 0.5)
        pen.line([_add(mid, (-3.0, -2.0)), _add(mid, (1.0, 1.0)), _add(mid, (-1.0, 3.0))], OUTLINE, 1.0)
    return bell_top


def draw_hackle(pen: Pen, pose: Pose) -> None:
    """The hackle: pointed gold feathers from the head down over the shoulders,
    and the bandana knotted at the neck's base."""
    top = _neck_top(pose)
    base = _body_point(pose, (8.0, -92.0))
    pen.tube(base, top, 34.0, 22.0, HACKLE, 1.4)
    for k in range(9):
        t = k / 8.0
        root = _lerp(top, base, 0.1 + 0.6 * t)
        side = -14.0 + 4.0 * math.sin(k * 1.7)
        tip = _add(root, _rot((side, 20.0 + 6 * t), pose.lean))
        pen.poly([_add(root, (-5.0, 0.0)), tip, _add(root, (5.0, 0.0))], HACKLE if k % 2 else HACKLE_DARK, 1.0)
    # The bandana: a band round the neck, its point down the chest, its knot behind.
    n0, n1 = _body_point(pose, (-10.0, -98.0)), _body_point(pose, (30.0, -94.0))
    pen.stroke([n0, _body_point(pose, (10.0, -102.0)), n1], BANDANA, 8.0, 1.2)
    point = _body_point(pose, (30.0, -76.0))
    pen.poly([_body_point(pose, (18.0, -98.0)), _body_point(pose, (36.0, -96.0)), point], BANDANA, 1.2)
    pen.line([_body_point(pose, (20.0, -92.0)), _body_point(pose, (28.0, -84.0))], BANDANA_DARK, 1.0)
    knot = _body_point(pose, (-12.0, -98.0))
    flap = 4.0 * math.sin(pose.phase * math.tau)
    for k, ln in enumerate((14.0, 11.0)):
        pen.poly([knot, _add(knot, (-ln, 4.0 + flap + 4 * k)), _add(knot, (-ln + 4.0, 9.0 + flap + 4 * k))], BANDANA_DARK, 1.0)
    pen.circle(knot, 3.4, BANDANA, 1.0)


def draw_head(pen: Pen, pose: Pose) -> Tuple[Point, float]:
    """The head and the hat. Returns the beak's tip and the head's angle."""
    c = _head_centre(pose)
    ang = pose.lean * 0.4 + pose.head

    def at(x: float, y: float) -> Point:
        return _add(c, _rot((x * HEAD, y * HEAD), ang))
    # The comb under the hat (it comes up through the crown, drawn with the hat).
    # The wattles under the beak.
    sway = 2.0 * math.sin(pose.phase * math.tau + 0.6)
    pen.shape([at(8, 8), at(16, 10), at(18 + sway * 0.3, 24), at(12 + sway * 0.3, 30), at(6, 20)], COMB, 1.2)
    pen.shape([at(2, 10), at(8, 12), at(8 + sway * 0.3, 24), at(2, 22)], COMB_DARK, 1.1)
    # The comb, when the hat is not on it (the hat draws it through its crown).
    if pose.hat_off > 0.0:
        comb = [at(-8, -12), at(-6, -24), at(-2, -18), at(1, -30), at(5, -20), at(9, -28), at(11, -18), at(15, -22), at(14, -12)]
        pen.poly(comb, COMB, 1.2)
        pen.poly([at(4, -12), at(5, -20), at(9, -28), at(11, -18), at(15, -22), at(14, -12)], STEEL, 1.0)
    # The skull.
    pen.shape([at(-18, -2), at(-12, -16), at(4, -18), at(16, -10), at(19, 4), at(12, 14), at(-4, 15), at(-16, 10)], FEATHER, 1.5)
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
    pen.circle(lens, 6.4, BRASS, 1.3)
    pen.circle(lens, 4.2, (40, 10, 10, 255), 0.8)
    glow = pose.lens
    _glow(pen.img, lambda d: d.ellipse((*_s((lens[0] - 6, lens[1] - 6)), *_s((lens[0] + 6, lens[1] + 6))), fill=_a(LENS_RED, 0.55 * glow)), 2.4)
    pen.circle(lens, 2.8, _mix((120, 20, 16, 255), LENS_RED, glow), 0)
    pen.circle(_add(lens, (-1.2, -1.2)), 0.9, (255, 220, 200, 255), 0)
    return at(34, 2), ang


def draw_hat(pen: Pen, pose: Pose) -> None:
    c = _head_centre(pose)
    ang = pose.lean * 0.4 + pose.head - pose.hat_back
    lift = pose.hat_off
    if lift > 0.0:
        # It falls off behind him, turning over once, and lands on its brim on
        # the floor behind his tail.
        land = (pose.x - 120.0, FLOOR + 6.0 * HEAD)
        c = (c[0] + (land[0] - c[0]) * lift, c[1] + (land[1] - c[1]) * lift * lift - 40.0 * math.sin(lift * math.pi))
        ang = ang * (1.0 - lift) - 360.0 * lift

    def at(x: float, y: float) -> Point:
        return _add(c, _rot((x * HEAD, y * HEAD), ang))
    # The comb comes up through a slit in the crown.
    if lift <= 0.0:
        comb = [at(-8, -38), at(-6, -50), at(-2, -44), at(1, -56), at(5, -46), at(9, -54), at(11, -44), at(15, -48), at(14, -38)]
        pen.poly(comb, COMB, 1.2)
        steel = [at(4, -38), at(5, -46), at(9, -54), at(11, -44), at(15, -48), at(14, -38)]
        pen.poly(steel, STEEL, 1.0)
    # The crown: a pinched top, a dent along it.
    crown = [at(-15, -16), at(-14, -32), at(-10, -40), at(0, -37), at(10, -41), at(15, -33), at(16, -16)]
    pen.shape(crown, HAT, 1.5, steps=4)
    pen.shape([at(-12, -18), at(-11, -32), at(-7, -37), at(-2, -35), at(-4, -20)], _a(HAT_LIGHT, 0.8), 0, steps=4)
    pen.line([at(0, -36), at(1, -27)], HAT_DARK, 1.3)
    # The band of brass studs.
    pen.poly([at(-15, -16), at(16, -16), at(16, -23), at(-15, -23)], LEATHER_DARK, 1.0)
    for k in range(5):
        pen.circle(at(-11 + 6.5 * k, -19.5), 1.4, BRASS_LIGHT, 0.6)
    # The brim: wide and flat, curled up a little at its two ends.
    brim = [at(-38, -18), at(-30, -14), at(0, -11), at(30, -12), at(42, -18), at(44, -13), at(30, -7), at(0, -6), at(-30, -8), at(-40, -13)]
    pen.shape(brim, HAT, 1.5, steps=4)
    pen.line([at(-28, -11), at(28, -10)], HAT_DARK, 1.0)


def draw_near_arm(pen: Pen, pose: Pose) -> Point:
    """The machine arm: pistons, a cylinder on the forearm, a claw. Returns the
    cannon's muzzle."""
    sh, el, hand = _arm(pose, near=True)
    fdeg = _forearm_deg(pose, near=True)
    pen.circle(sh, 11.0, STEEL, 1.4)
    pen.circle(sh, 4.0, BRASS, 0.8)
    pen.tube(sh, el, 13.0, 11.0, STEEL_DARK, 1.3)
    pen.line([_lerp(sh, el, 0.15), _lerp(sh, el, 0.85)], STEEL_LIGHT, 2.0)
    pen.circle(el, 7.0, STEEL, 1.2)
    pen.circle(el, 2.4, BRASS, 0)
    pen.tube(el, hand, 12.0, 10.0, STEEL, 1.3)
    # The cylinder: six chambers on the forearm, and the barrel past the claw.
    cyl = _lerp(el, hand, 0.45)
    out = pose.cylinder_out
    cyl_c = _add(cyl, _rot((-7.0 - 8.0 * out, 0.0), fdeg - 90.0 + 90.0))
    pen.circle(cyl_c, 8.4, GUNMETAL, 1.3)
    for k in range(6):
        p = _add(cyl_c, _rot((0.0, -5.0), k * 60 + pose.phase * 60 * out))
        pen.circle(p, 1.7, (24, 22, 22, 255) if out > 0.1 else BRASS_DARK, 0.5)
    muzzle = _along(hand, fdeg, 14.0)
    pen.tube(_along(el, fdeg, FOREARM * 0.6), muzzle, 6.0, 6.0, STEEL_DARK, 1.1)
    pen.circle(muzzle, 2.0, (20, 18, 18, 255), 0)
    # The claw: three fingers.
    for k, (off, ln) in enumerate([(-34.0, 10.0), (-8.0, 12.0), (24.0, 9.0)]):
        knuckle = _along(hand, fdeg + off * 0.4, 3.0)
        tip = _along(knuckle, fdeg + off, ln)
        pen.tube(knuckle, tip, 4.6, 2.6, STEEL_LIGHT if k == 1 else STEEL, 1.0)
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


def draw_steam(pen: Pen, pose: Pose, mouth: Point) -> None:
    if pose.cracked:
        # A thin wisp leaks out of the crack.
        for k in range(3):
            t = (pose.phase + k / 3.0) % 1.0
            pen.circle(_add(mouth, (-4.0 - 6 * t, -6.0 - 18.0 * t)), 2.0 + 4.0 * t, _a(STEAM, 0.5 * (1 - t)), 0)
    if pose.steam > 0.0:
        k = pose.steam
        # The jet up out of the whistle...
        for i in range(7):
            t = i / 6.0
            c = _add(mouth, (-6.0 * t + 2.0 * math.sin(i * 1.3), -14.0 - 70.0 * t * k))
            r = 6.0 + 14.0 * t * k
            pen.circle(c, r, _a(STEAM, 0.85 * (1.0 - 0.6 * t)), 0)
        # ...and the ring of steam round him at the height of his chest.
        ring_c = _body_point(pose, (4.0, -60.0))
        rr = 50.0 + 70.0 * k
        _glow(pen.img, lambda d: d.ellipse((*_s((ring_c[0] - rr, ring_c[1] - rr * 0.55)), *_s((ring_c[0] + rr, ring_c[1] + rr * 0.55))),
                                            outline=_a(STEAM, 0.75 * (1.0 - 0.5 * k)), width=int(10 * SUPER)), 3.0)
    if pose.call > 0.0:
        for i in range(3):
            t = (pose.call + i * 0.3) % 1.0
            pen.circle(_add(mouth, (-2.0 * t, -10.0 - 30.0 * t)), 3.0 + 6.0 * t, _a(STEAM, 0.7 * (1.0 - t)), 0)


def draw_shells(pen: Pen, pose: Pose) -> None:
    if pose.shells < 0.0:
        return
    sh, el, hand = _arm(pose, near=True)
    cyl = _lerp(el, hand, 0.45)
    for k in range(6):
        t = min(1.0, max(0.0, pose.shells * 1.4 - k * 0.08))
        x = cyl[0] - 10.0 + 4.0 * k + 10.0 * t * math.sin(k * 2.1)
        y = cyl[1] + (FLOOR - 4.0 - cyl[1]) * t * t
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

def draw_marshal(pose: Pose) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    pen = Pen(img)
    if pose.seated:
        draw_cart(pen)
    draw_tail(pen, pose)
    draw_leg(pen, pose, near=False)
    # The torso is turned a little toward us, so the far wing hangs at his
    # back; reaching forward, it crosses in front of the chest.
    reaching = pose.far_arm[0] + pose.lean > 50.0
    revolver_muzzle = None if reaching else draw_far_arm(pen, pose)
    draw_holster(pen, pose)
    draw_leg(pen, pose, near=True)
    draw_body(pen, pose)
    if reaching:
        revolver_muzzle = draw_far_arm(pen, pose)
    whistle = draw_whistle(pen, pose)
    draw_hackle(pen, pose)
    beak_tip, head_ang = draw_head(pen, pose)
    if pose.hat_off <= 0.0:
        draw_hat(pen, pose)
    cannon = draw_near_arm(pen, pose)
    hand = _arm(pose, near=True)[2]
    draw_dynamite(pen, pose, hand)
    draw_lasso(pen, pose, hand)
    draw_shells(pen, pose)
    if pose.hat_off > 0.0:
        draw_hat(pen, pose)
    draw_steam(pen, pose, whistle)
    if revolver_muzzle is not None:
        draw_flash(pen, revolver_muzzle, _forearm_deg(pose, near=False), pose.flash_far)
    draw_flash(pen, cannon, _forearm_deg(pose, near=True), pose.flash_near)
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
        if i <= 4:  # he lights three sticks off his own chest plate
            k = i / 4.0
            return g(replace(base, lean=6.0, near_arm=(40.0, 80.0 - 10.0 * k), far_arm=(10.0, 60.0), dynamite=3,
                             fuse=0.3 + 0.7 * k, expression="smug", head=8.0, chest_glow=0.3 * k))
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
                             far_arm=(-20.0 * k, 40.0), expression="menace", tail_spread=k, chest_glow=0.4 * k))
        if i <= 9:  # the crow: the head thrown back, the beak wide, steam
            k = (i - 6) / 3.0
            return g(replace(base, lean=-16.0, puff=1.0, head=-30.0, beak=1.0, steam=0.3 + 0.7 * k, near_arm=(-40.0, 30.0),
                             far_arm=(-40.0, 30.0), expression="fury", tail_spread=1.0, lens=1.0, chest_glow=0.5, smoke=1.0))
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
            return g(replace(base, lean=4.0, near_leg=(28.0, 34.0), far_leg=(-24.0, 30.0), revolver="hand",
                             near_arm=(84.0 if high else 120.0, 4.0), far_arm=(96.0 if not high else 70.0, 4.0),
                             flash_near=0.4 if k % 2 == 1 else -1.0, flash_far=0.4 if k % 2 == 0 else -1.0,
                             expression="fury", lens=1.0, smoke=0.9, tail_spread=1.0))
        return g(replace(base, lean=2.0, near_leg=(28.0, 34.0), far_leg=(-24.0, 30.0), revolver="hand",
                         near_arm=(100.0, 10.0), far_arm=(90.0, 10.0), expression="smug", lens=0.8, smoke=1.0, tail_spread=0.6))
    if animation == "reload":
        # The cylinder swings out of the forearm; the shells fall; he fills it.
        k = math.sin(u * math.pi)
        return g(replace(base, lean=6.0, head=14.0, near_arm=(40.0, 90.0), far_arm=(20.0, 100.0), cylinder_out=k,
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
        # The whistle cracks with a last shriek, he goes down on one knee, the
        # hat falls behind him.
        k = _ease(u * 1.3)
        p = replace(base, lean=-10.0 + 30.0 * k, head=10.0 + 20.0 * k, beak=0.6 * (1 - k), steam=0.4 * (1 - k) if u < 0.35 else 0.0,
                    cracked=u > 0.2, near_leg=(18.0 + 60.0 * k, 34.0 + 90.0 * k), far_leg=(-14.0 + 40 * k, 30.0 + 20 * k),
                    near_arm=(8.0 + 30.0 * k, 50.0), far_arm=(20.0 + 20 * k, 40.0), hat_off=max(0.0, (u - 0.3) / 0.7),
                    expression="pain" if u < 0.6 else "hoarse", lens=1.0 - 0.8 * k, smoke=0.4 * (1 - k), tail_spread=0.0)
        return g(p)
    if animation == "seated":
        # Beaten: on an ore cart, hoarse, the cracked whistle leaking. The hat
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
