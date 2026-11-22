"""The Supreme Leader: the ruler of the Nazi Dimension
(`docs/planning/game/bosses.md`, "The Supreme Leader"; concept art
`assets/concept_art/misc/Supreme Leader Character Design Sheet.png`, the
final direction). His name, his history and his seat are open questions for
the maintainer; the art settles none of them.

A tall man in a long black coat, its front edges a broad crimson band with a
cream stripe and a gold edge; a stiff high collar, crimson inside, that
flares up behind his head; a crimson cape lined in cream from both
shoulders; a gold aiguillette from the near shoulder to the medallion at his
collar (the regime's sigil: a winged arrow, rising); a black belt with a gold
buckle; black gloves with crimson cuffs; tall black boots. Dark hair swept
back with one grey streak, a sharp face, clean shaven. His sceptre is a gold
staff whose ring holds a crimson orb: a gate device, the regime's science in
his hand.

A PAPER DOLL: every part is its own drawing, posed from one ``Pose`` per
frame. Back to front: the cape, the far leg, the far arm, the coat, the near
leg, the collar and the head, the near arm and the sceptre, then the effects
(the orb's glow, the gate ring, steam).

Rows: ``idle`` 10; ``walk`` 8; ``order`` 12 (tell 0-6: he turns and points
at his uplink; the fist that fires it, 7-11); ``decree`` 12 (the sceptre
raised, then brought down at the target); ``aim`` 10 (the sceptre levelled;
three recoils); ``sweep`` 10 (wound back, the arc, the follow through);
``gate_out`` 8 (the cape swirls round him and he is gone); ``gate_in`` 6 (he
steps out of the ring); ``report`` 10 (the plan failed: a hand to his ear,
shouting into it); ``mandate`` 12 (feet planted, the sceptre held out in
both hands, the orb blazing); ``overheat`` 10 (the sceptre vents, he shakes
his hand); ``address`` 12 (the speech: the arm thrown out); ``emergency``
14 (emergency powers: the orb drinks the light, the cape flies); ``turn`` 6;
``hurt`` 3; ``death`` 20 (thrown back, down on one knee on his sceptre,
defiant; the orb opens a gate behind him and he falls back through it; the
last frame is empty).

Facing right. The feet are on ``FLOOR``; the body is centred in the frame,
which the published boss row (`boss_sheets.ron`, ``supreme_leader``) draws
at the body's centre. No drop shadow.
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

TARGET_NAME = "supreme_leader"
FRAME_SIZE = (640, 480)
SUPER = 4
#: Where the feet stand: the body (about 300 px from the hair to the boots)
#: centred on the frame.
FLOOR = 420.0
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 10, 130),
    ("walk", 8, 110),
    ("order", 12, 75),
    ("decree", 12, 75),
    ("aim", 10, 70),
    ("sweep", 10, 60),
    ("gate_out", 8, 60),
    ("gate_in", 6, 60),
    ("report", 10, 100),
    ("mandate", 12, 70),
    ("overheat", 10, 100),
    ("address", 12, 120),
    ("emergency", 14, 80),
    ("turn", 6, 70),
    ("hurt", 3, 90),
    ("death", 20, 90),
]

OUTLINE: RGBA = (26, 18, 22, 255)
COAT: RGBA = (44, 36, 44, 255)
COAT_LIGHT: RGBA = (74, 62, 74, 255)
COAT_DARK: RGBA = (26, 21, 27, 255)
CRIMSON: RGBA = (156, 28, 42, 255)
CRIMSON_DARK: RGBA = (104, 16, 30, 255)
CRIMSON_LIGHT: RGBA = (198, 54, 62, 255)
CREAM: RGBA = (238, 224, 196, 255)
CREAM_SHADE: RGBA = (204, 186, 154, 255)
GOLD: RGBA = (224, 176, 66, 255)
GOLD_DARK: RGBA = (160, 114, 34, 255)
GOLD_LIGHT: RGBA = (252, 222, 132, 255)
SKIN: RGBA = (234, 198, 172, 255)
SKIN_SHADE: RGBA = (198, 154, 128, 255)
HAIR: RGBA = (46, 36, 36, 255)
HAIR_LIGHT: RGBA = (88, 72, 70, 255)
HAIR_GREY: RGBA = (200, 200, 204, 255)
GLOVE: RGBA = (32, 27, 32, 255)
BOOT: RGBA = (26, 23, 28, 255)
BOOT_SHINE: RGBA = (96, 92, 106, 255)
ORB: RGBA = (226, 44, 112, 255)
ORB_LIGHT: RGBA = (255, 176, 214, 255)
GATE: RGBA = (190, 70, 255, 255)
GATE_LIGHT: RGBA = (236, 196, 255, 255)
STEAM: RGBA = (236, 236, 240, 255)
EYE: RGBA = (30, 22, 24, 255)

#: The body's lengths (frame pixels).
THIGH = 64.0
SHIN = 66.0
UPPER_ARM = 50.0
FOREARM = 46.0
#: The sceptre's length, from its butt to the top of its ring.
STAFF = 196.0
#: The head is drawn this much larger than its sketch, so it reads at the
#: game's scale.
HEAD = 1.3


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

    def ring(self, c: Point, rx: float, ry: float, fill: RGBA, width: float) -> None:
        box = (*_s((c[0] - rx, c[1] - ry)), *_s((c[0] + rx, c[1] + ry)))
        w = max(1, int(width * SUPER))
        self._over(box, lambda d, dx, dy: d.ellipse((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), outline=fill, width=w))

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
    x: float = 320.0
    y: float = 240.0
    #: The body's lean: positive tips the chest forward (toward +x).
    lean: float = -3.0
    #: The head: its tilt (positive: the chin down), and the chin raised
    #: (negative tilt) in contempt.
    head: float = -4.0
    #: Arms: (shoulder angle from straight down, toward the facing; elbow
    #: bend, positive folds the forearm forward/up).
    near_arm: Tuple[float, float] = (26.0, 4.0)
    far_arm: Tuple[float, float] = (-8.0, 20.0)
    #: Legs: (hip angle from straight down, toward the facing; knee bend,
    #: positive folds the shin back).
    near_leg: Tuple[float, float] = (6.0, 4.0)
    far_leg: Tuple[float, float] = (-6.0, 4.0)
    #: The sceptre: in the near hand at this angle from straight up
    #: (positive: its top toward the facing), and where along it the hand
    #: holds it (0 the butt, 1 the top).
    staff: float = 2.0
    grip: float = 0.34
    #: Both hands on the sceptre (the far hand along it at ``grip2``).
    two_hands: bool = False
    grip2: float = 0.3
    #: The far hand: "fist", "point" (index out), "open", "ear" (at his ear).
    far_hand: str = "fist"
    #: The orb's glow (0..1), and its beam's flare (0..1).
    orb: float = 0.25
    flare: float = 0.0
    #: The cape: how far it flies out behind him (0 hangs, 1 streams), and
    #: its ripple's phase.
    cape: float = 0.1
    ripple: float = 0.0
    #: "stern", "contempt", "shout", "rage", "pain", "calm", "defiant".
    expression: str = "stern"
    #: The gate ring round him (0..1 open; below zero none) and how much of
    #: him shows (1 all; 0 gone through the gate).
    gate: float = -1.0
    shown: float = 1.0
    #: Steam from the sceptre (0..1).
    steam: float = 0.0
    #: Down on one knee (0..1), and fallen back through the gate (0..1).
    kneel: float = 0.0
    phase: float = 0.0


# ---- the skeleton -----------------------------------------------------------------------------------------------

def _body_point(pose: Pose, p: Point) -> Point:
    """A point of the body (local: the hip at the origin, facing right, the
    body upright) where the posed body puts it."""
    return _add((pose.x, pose.y), _rot(p, pose.lean))


def _shoulder(pose: Pose, near: bool) -> Point:
    return _body_point(pose, (8.0, -100.0) if near else (-16.0, -102.0))


def _neck_top(pose: Pose) -> Point:
    return _body_point(pose, (4.0, -118.0))


def _head_centre(pose: Pose) -> Point:
    return _add(_neck_top(pose), _rot((4.0, -24.0), pose.head * 0.4))


def _hip(pose: Pose, near: bool) -> Point:
    return _body_point(pose, (4.0, 0.0) if near else (-6.0, -2.0))


def _leg(pose: Pose, near: bool) -> Tuple[Point, Point, Point]:
    """Hip, knee and ankle."""
    hip_deg, knee = pose.near_leg if near else pose.far_leg
    hip = _hip(pose, near)
    k = _along(hip, hip_deg, THIGH)
    ankle = _along(k, hip_deg - knee, SHIN)
    return hip, k, ankle


def _arm(pose: Pose, near: bool) -> Tuple[Point, Point, Point]:
    """Shoulder, elbow and hand."""
    sh_deg, bend = pose.near_arm if near else pose.far_arm
    shoulder = _shoulder(pose, near)
    elbow = _along(shoulder, sh_deg + pose.lean, UPPER_ARM)
    hand = _along(elbow, sh_deg + pose.lean + bend, FOREARM)
    return shoulder, elbow, hand


def _grounded(pose: Pose) -> Pose:
    """Set the hip's height so that the lower foot stands on ``FLOOR``."""
    lowest = max(_leg(replace(pose, y=0.0), near)[2][1] for near in (True, False))
    return replace(pose, y=FLOOR - 8.0 - lowest)


def _staff_ends(pose: Pose) -> Tuple[Point, Point]:
    """The sceptre's butt and the centre of its orb, from where the near
    hand holds it."""
    hand = _arm(pose, True)[2]
    up = _rot((0.0, -1.0), pose.staff)
    butt = (hand[0] - up[0] * STAFF * pose.grip, hand[1] - up[1] * STAFF * pose.grip)
    top = (hand[0] + up[0] * STAFF * (1.0 - pose.grip), hand[1] + up[1] * STAFF * (1.0 - pose.grip))
    return butt, top


# ---- the parts --------------------------------------------------------------------------------------------------

def draw_cape(pen: Pen, pose: Pose) -> None:
    """The cape from both shoulders, hanging behind him to his ankles; it
    flies out behind (``cape``) and ripples."""
    sh_far = _shoulder(pose, False)
    sh_near = _shoulder(pose, True)
    top_back = _add(sh_far, (-14.0, 2.0))
    fly = pose.cape
    length = 210.0 - 30.0 * pose.kneel
    hem_back = (top_back[0] - 30.0 - 120.0 * fly, top_back[1] + length * (1.0 - 0.45 * fly))
    hem_front = (sh_near[0] - 6.0 - 40.0 * fly, sh_near[1] + length + 6.0 - 40.0 * fly)
    rip = [math.sin(pose.ripple + k * 1.7) * (4.0 + 6.0 * fly) for k in range(4)]
    outer = [top_back, (top_back[0] - 18.0 - 40.0 * fly, top_back[1] + 70.0 + rip[0]),
             (top_back[0] - 26.0 - 90.0 * fly, top_back[1] + 140.0 * (1.0 - 0.3 * fly) + rip[1]),
             hem_back, (_lerp(hem_back, hem_front, 0.35)[0], _lerp(hem_back, hem_front, 0.35)[1] + 6.0 + rip[2]),
             (_lerp(hem_back, hem_front, 0.7)[0], _lerp(hem_back, hem_front, 0.7)[1] + rip[3]), hem_front,
             (sh_near[0] - 4.0, sh_near[1] + 30.0), _add(sh_near, (0.0, -4.0))]
    pen.shape(outer, CRIMSON, 1.6)
    # The cream lining along its trailing edge and the gold edge outside it.
    edge = _smooth([top_back, outer[1], outer[2], hem_back], False, 6)
    lining = edge + [(x + 9.0, y - 2.0) for x, y in reversed(edge)]
    pen.poly(lining, CREAM, 1.0)
    pen.line(edge, GOLD, 2.2)
    # Folds.
    for k in (0.3, 0.55, 0.8):
        a = _lerp(top_back, sh_near, 0.4)
        b = _lerp(hem_back, hem_front, k)
        pen.line(_smooth([a, _lerp(a, b, 0.5), b], False, 4), CRIMSON_DARK, 2.0)


def draw_leg(pen: Pen, pose: Pose, near: bool) -> None:
    """The trouser leg into a tall boot."""
    hip, knee, ankle = _leg(pose, near)
    trouser = COAT if near else COAT_DARK
    boot = BOOT
    knee_top = _lerp(knee, hip, 0.12)
    pen.tube(hip, knee_top, 26.0, 20.0, trouser, 1.3)
    pen.tube(knee, ankle, 20.0, 16.0, boot, 1.3)
    pen.tube(knee_top, knee, 21.0, 21.0, boot, 1.3)
    # The boot's top band and its shine.
    pen.line([_add(knee, (-10.0, -4.0)), _add(knee, (10.0, -4.0))], BOOT_SHINE if near else COAT, 2.0)
    pen.line([_lerp(knee, ankle, 0.2), _lerp(knee, ankle, 0.8)], _a(BOOT_SHINE, 0.7 if near else 0.3), 2.0)
    # The foot.
    toe = (ankle[0] + 26.0, ankle[1] + 7.0)
    heel = (ankle[0] - 10.0, ankle[1] + 8.0)
    foot = [_add(ankle, (-10.0, -6.0)), _add(ankle, (8.0, -4.0)), (toe[0], toe[1] - 7.0), toe, heel]
    pen.shape(foot, boot, 1.3, steps=4)
    pen.line([(heel[0] + 4.0, heel[1] - 1.0), (toe[0] - 4.0, toe[1] - 1.0)], COAT_DARK, 2.0)


def _hand(pen: Pen, at: Point, deg: float, kind: str, scale: float = 1.0) -> None:
    """A gloved hand at ``at``, its fingers toward ``deg`` (from straight
    down, toward the facing)."""
    d = _down(deg)
    side = (-d[1], d[0])
    r = 8.0 * scale
    pen.circle(at, r, GLOVE, 1.2)
    if kind == "point":
        tip = (at[0] + d[0] * 22.0 * scale, at[1] + d[1] * 22.0 * scale)
        pen.tube(_add(at, (d[0] * 4, d[1] * 4)), tip, 6.0 * scale, 5.0 * scale, GLOVE, 1.1)
        thumb = (at[0] + side[0] * 7.0 + d[0] * 6.0, at[1] + side[1] * 7.0 + d[1] * 6.0)
        pen.circle(thumb, 3.4 * scale, GLOVE, 1.0)
    elif kind == "open":
        for k in (-1.0, -0.33, 0.33, 1.0):
            base = (at[0] + side[0] * k * 5.0, at[1] + side[1] * k * 5.0)
            fd = _down(deg + k * 14.0)
            pen.tube(base, (base[0] + fd[0] * 17.0 * scale, base[1] + fd[1] * 17.0 * scale), 4.6 * scale, 4.0 * scale, GLOVE, 1.0)
    else:
        # A fist: the knuckles a ridge, a gold seam on the glove's back.
        pen.ellipse(_add(at, (d[0] * 4.0, d[1] * 4.0)), 7.5 * scale, 7.5 * scale, GLOVE, 1.2)
        pen.line([_add(at, (side[0] * 5.0, side[1] * 5.0)), _add(at, (-side[0] * 5.0, -side[1] * 5.0))], COAT_LIGHT, 1.2)


def _cuff(pen: Pen, elbow: Point, hand: Point) -> None:
    """The coat sleeve's crimson cuff with its gold stripe, just above the
    glove."""
    a = _lerp(elbow, hand, 0.72)
    b = _lerp(elbow, hand, 0.86)
    pen.tube(a, b, 17.0, 16.0, CRIMSON, 1.1)
    m = _lerp(a, b, 0.5)
    dx, dy = hand[0] - elbow[0], hand[1] - elbow[1]
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n * 8.0, dx / n * 8.0
    pen.line([(m[0] + nx, m[1] + ny), (m[0] - nx, m[1] - ny)], GOLD, 1.8)


def draw_far_arm(pen: Pen, pose: Pose) -> None:
    shoulder, elbow, hand = _arm(pose, False)
    if pose.two_hands:
        return
    pen.tube(shoulder, elbow, 22.0, 18.0, COAT_DARK, 1.3)
    pen.tube(elbow, _lerp(elbow, hand, 0.8), 18.0, 16.0, COAT_DARK, 1.3)
    _cuff(pen, elbow, hand)
    sh_deg, bend = pose.far_arm
    deg = sh_deg + pose.lean + bend
    if pose.far_hand == "ear":
        return
    _hand(pen, hand, deg, pose.far_hand)


def _far_hand_on_staff(pose: Pose) -> Optional[Point]:
    if not pose.two_hands:
        return None
    butt, top = _staff_ends(pose)
    return _lerp(butt, top, pose.grip2)


def draw_far_arm_on_staff(pen: Pen, pose: Pose) -> None:
    """With both hands on the sceptre the far arm comes across his chest to
    it, drawn after the coat."""
    grip = _far_hand_on_staff(pose)
    if grip is None:
        return
    shoulder = _shoulder(pose, False)
    mid = _lerp(shoulder, grip, 0.5)
    elbow = (mid[0] - 6.0, mid[1] + 18.0)
    pen.tube(shoulder, elbow, 20.0, 17.0, COAT_DARK, 1.3)
    pen.tube(elbow, _lerp(elbow, grip, 0.8), 17.0, 15.0, COAT_DARK, 1.3)
    _cuff(pen, elbow, grip)
    pen.circle(grip, 8.0, GLOVE, 1.2)


def _coat_outline(pose: Pose) -> List[Point]:
    """The coat's silhouette: shoulders, the chest, down the front to the
    hem below the knees, and up the back."""
    k = pose.kneel
    hem = 118.0 - 40.0 * k
    flare = 6.0 + 10.0 * pose.cape

    def bp(x: float, y: float) -> Point:
        return _body_point(pose, (x, y))
    return [bp(-32, -104), bp(-12, -114), bp(18, -112), bp(34, -98), bp(36, -62), bp(28, -12), bp(32 + 4 * k, 40),
            bp(34 + flare * 0.3, hem - 10), bp(30 + flare * 0.5, hem), bp(-32 - flare, hem + 2), bp(-36 - flare * 0.4, 40),
            bp(-33, -12), bp(-36, -62)]


def draw_coat(pen: Pen, pose: Pose) -> None:
    """The long coat: black, its front edge a broad crimson band with a cream
    stripe and a gold edge; the belt; the medallion and the aiguillette."""
    pen.shape(_coat_outline(pose), COAT, 1.6, steps=5)

    def bp(x: float, y: float) -> Point:
        return _body_point(pose, (x, y))
    k = pose.kneel
    hem = 118.0 - 40.0 * k
    # The front band, down the coat's leading edge.
    band = [bp(16, -110), bp(34, -98), bp(36, -62), bp(28, -12), bp(32 + 4 * k, 40), bp(32, hem - 6),
            bp(16, hem - 2), bp(14, 40), bp(12, -10), bp(12, -60)]
    pen.shape(band, CRIMSON, 1.2, steps=4)
    stripe = [bp(18, -62), bp(22, -62), bp(20, -10), bp(21, 40), bp(22, hem - 4), bp(19, hem - 4), bp(18, 40), bp(16, -10)]
    pen.poly(_smooth(stripe, True, 3), CREAM, 0.8)
    pen.line(_smooth([bp(12, -60), bp(12, -10), bp(14, 40), bp(16, hem - 2)], False, 4), GOLD, 1.8)
    # The coat's lit back edge and a fold.
    pen.line(_smooth([bp(-31, -100), bp(-34, -60), bp(-31, -10), bp(-34, 40)], False, 4), COAT_LIGHT, 2.0)
    pen.line(_smooth([bp(-6, 0), bp(-10, 50), bp(-12, hem - 8)], False, 4), COAT_DARK, 2.2)
    # The belt and its buckle.
    belt = [bp(-34, -22), bp(30, -24), bp(30, -12), bp(-34, -10)]
    pen.poly(belt, COAT_DARK, 1.2)
    pen.poly([bp(12, -25), bp(24, -25), bp(24, -11), bp(12, -11)], GOLD, 1.0)
    pen.poly([bp(15, -21), bp(21, -21), bp(21, -15), bp(15, -15)], GOLD_DARK, 0.6)
    # Buttons up the chest, gold, in two rows.
    for y in (-88, -72, -56, -40):
        pen.circle(bp(4, y), 2.4, GOLD, 0.8)
    # The aiguillette: gold cords from the near shoulder looping to the
    # medallion.
    sh = bp(10, -98)
    med = bp(18, -96)
    for k2, sag in ((0, 26.0), (1, 38.0)):
        a = _add(sh, (-14.0 + 4 * k2, 2.0))
        b = _add(med, (0.0, 6.0))
        mid = (_lerp(a, b, 0.5)[0] - 4.0, _lerp(a, b, 0.5)[1] + sag)
        pts = _smooth([a, mid, b], False, 8)
        pen.line(pts, GOLD_DARK, 4.2)
        pen.line(pts, GOLD, 2.8)
        for i in range(2, len(pts) - 1, 3):
            pen.circle(pts[i], 1.0, GOLD_LIGHT, 0)
    # The tassel ends.
    tas = _add(sh, (-8.0, 30.0))
    pen.line([sh, tas], GOLD_DARK, 3.0)
    pen.poly([_add(tas, (-4, 0)), _add(tas, (4, 0)), _add(tas, (5, 12)), _add(tas, (-5, 12))], GOLD, 0.8)
    # The epaulette over the near shoulder.
    ep = bp(0, -104)
    pen.ellipse(ep, 22.0, 9.0, CRIMSON, 1.2)
    pen.line([_add(ep, (-20.0, 4.0)), _add(ep, (20.0, 4.0))], GOLD, 2.2)
    for fx in (-14.0, -7.0, 0.0, 7.0, 14.0):
        pen.line([_add(ep, (fx, 6.0)), _add(ep, (fx * 1.1, 13.0))], GOLD_DARK, 1.6)


def _sigil(pen: Pen, c: Point, r: float) -> None:
    """The regime's sigil on a gold disc: an arrow rising between two wings."""
    pen.circle(c, r, GOLD, 1.2)
    pen.circle(c, r * 0.78, CRIMSON, 0.8)
    s = r / 12.0
    arrow = [(c[0], c[1] - 9 * s), (c[0] + 4 * s, c[1] - 4 * s), (c[0] + 1.4 * s, c[1] - 4 * s), (c[0] + 1.4 * s, c[1] + 8 * s),
             (c[0] - 1.4 * s, c[1] + 8 * s), (c[0] - 1.4 * s, c[1] - 4 * s), (c[0] - 4 * s, c[1] - 4 * s)]
    pen.poly(arrow, GOLD_LIGHT, 0.5)
    for side in (-1.0, 1.0):
        wing = [(c[0] + side * 2 * s, c[1] + 1 * s), (c[0] + side * 9 * s, c[1] - 3 * s), (c[0] + side * 8 * s, c[1] + 1 * s),
                (c[0] + side * 3 * s, c[1] + 4 * s)]
        pen.poly(wing, GOLD_LIGHT, 0.5)


def draw_collar(pen: Pen, pose: Pose, front: bool) -> None:
    """The stiff high collar: its back flares up behind his head (drawn
    before it), its front with the medallion (after it)."""
    nt = _neck_top(pose)

    def bp(x: float, y: float) -> Point:
        return _body_point(pose, (x, y))
    if not front:
        back = [bp(-30, -104), bp(-38, -156), bp(-18, -162), bp(-2, -118), bp(16, -110)]
        pen.shape(back, COAT_DARK, 1.4, steps=4)
        inner = [bp(-27, -108), bp(-33, -150), bp(-18, -154), bp(-5, -118)]
        pen.shape(inner, CRIMSON, 0.9, steps=4)
        pen.line(_smooth([bp(-38, -156), bp(-18, -162), bp(-2, -118)], False, 4), GOLD, 1.8)
        return
    # The front: a stiff band round the neck and the medallion at the throat.
    pen.poly([bp(-8, -112), bp(20, -114), bp(22, -102), bp(-6, -100)], COAT_DARK, 1.2)
    pen.line([bp(-6, -112), bp(20, -114)], GOLD, 1.6)
    _sigil(pen, bp(17, -98), 9.0)


def draw_head(pen: Pen, pose: Pose) -> Point:
    """His head: a long sharp face, a straight nose with a hook, a hard mouth,
    narrow eyes under heavy brows; dark hair swept back with a grey streak.
    Returns the mouth."""
    c = _head_centre(pose)
    tilt = pose.head

    def at(x: float, y: float) -> Point:
        return _add(c, _rot((x * HEAD, y * HEAD), tilt))
    # The neck.
    pen.tube(_neck_top(pose), at(-2, 14), 15.0, 14.0, SKIN_SHADE, 1.2)
    # The skull and face: the back of the head, the crown, the brow, the
    # nose, the lips, the long jaw, the chin.
    face = [at(-16, -14), at(-6, -24), at(8, -24), at(16, -16), at(17, -7), at(25, 5), at(20, 7), at(19, 12),
            at(18, 16), at(17, 23), at(8, 27), at(-2, 25), at(-10, 16), at(-16, 4)]
    pen.shape(face, SKIN, 1.4, steps=5)
    # The shaded cheek and the cheekbone line.
    pen.shape([at(-4, 6), at(4, 9), at(5, 18), at(-6, 16)], _a(SKIN_SHADE, 0.35), 0, steps=4)
    pen.line([at(2, 8), at(10, 12)], _a(SKIN_SHADE, 0.9), 1.2)
    # The ear.
    pen.ellipse(at(-8, 4), 4.0, 6.0, SKIN_SHADE, 1.1)
    # The hair: swept back from a widow's peak, slick, a grey streak along
    # it, cut close above the ear.
    hair = [at(14, -20), at(8, -27), at(-4, -30), at(-16, -26), at(-22, -14), at(-20, -2), at(-14, 2), at(-12, -8),
            at(-4, -14), at(4, -16), at(10, -14)]
    pen.shape(hair, HAIR, 1.3, steps=5)
    # The grey streak: a lock from the temple, swept back through the dark.
    streak = [at(11, -19), at(4, -23), at(-8, -22), at(-17, -14), at(-15, -11), at(-7, -17), at(3, -18)]
    pen.shape(streak, HAIR_GREY, 0, steps=4)
    pen.line(_smooth([at(8, -24), at(-6, -27), at(-18, -20)], False, 4), HAIR_LIGHT, 1.3)
    # The brow and the eye.
    expr = pose.expression
    brow_drop = {"rage": 3.0, "shout": 2.0, "contempt": 1.0, "pain": -2.0, "calm": 0.0, "defiant": 2.0}.get(expr, 1.5)
    pen.line([at(6, -9 + brow_drop * 0.2), at(16, -7 + brow_drop)], HAIR, 2.6)
    if expr == "pain":
        pen.line([at(9, -3), at(15, -2)], EYE, 1.6)
    else:
        open_ = 2.4 if expr in ("shout", "rage") else 1.6
        pen.ellipse(at(12, -3), 3.2, open_, (250, 246, 238, 255), 0.8)
        pen.circle(at(13.2, -3), 1.4, EYE, 0)
        pen.line([at(8, -5), at(16, -5.5)], OUTLINE, 1.1)
    # The nose's hooked line.
    pen.line([at(17, -6), at(24, 4), at(20, 6.5)], SKIN_SHADE, 1.3)
    # The mouth.
    mouth = at(17, 13)
    if expr in ("shout", "rage"):
        pen.shape([at(12, 10), at(19, 9), at(19, 17), at(13, 17)], (80, 22, 30, 255), 1.0, steps=3)
        pen.line([at(13, 10.5), at(18.5, 10)], CREAM, 1.2)
    elif expr == "contempt":
        pen.line([at(12, 13), at(17, 13), at(19, 11)], OUTLINE, 1.4)
    elif expr == "defiant":
        pen.line([at(12, 14), at(19, 13)], OUTLINE, 1.6)
    else:
        pen.line([at(12, 13), at(19, 13.5)], OUTLINE, 1.4)
    # The chin's cleft and the jaw's edge.
    pen.line([at(4, 24), at(14, 22)], _a(SKIN_SHADE, 0.8), 1.0)
    return mouth


def draw_near_arm(pen: Pen, pose: Pose) -> None:
    """The near arm, its sleeve, cuff and glove; the hand holds the
    sceptre."""
    shoulder, elbow, hand = _arm(pose, True)
    pen.tube(shoulder, elbow, 23.0, 19.0, COAT, 1.3)
    pen.tube(elbow, _lerp(elbow, hand, 0.8), 19.0, 17.0, COAT, 1.3)
    pen.line([_lerp(shoulder, elbow, 0.1), _lerp(shoulder, elbow, 0.9)], COAT_LIGHT, 1.6)
    _cuff(pen, elbow, hand)


def draw_staff(pen: Pen, pose: Pose) -> Point:
    """The sceptre: a gold staff, a gold ring at its top round a crimson orb.
    Returns the orb's centre."""
    butt, top = _staff_ends(pose)
    pen.tube(butt, top, 6.0, 7.0, GOLD, 1.2)
    pen.line([_lerp(butt, top, 0.05), _lerp(butt, top, 0.92)], GOLD_LIGHT, 1.4)
    # Bands down the staff.
    for t in (0.18, 0.62, 0.86):
        q = _lerp(butt, top, t)
        pen.circle(q, 5.0, GOLD_DARK, 1.0)
    # The ferrule at the butt.
    pen.circle(butt, 4.6, GOLD_DARK, 1.0)
    up = _rot((0.0, -1.0), pose.staff)
    orb_c = (top[0] + up[0] * 14.0, top[1] + up[1] * 14.0)
    # The ring: an upright hoop with a cross band, round the orb.
    pen.ring(orb_c, 18.0, 18.0, OUTLINE, 6.0)
    pen.ring(orb_c, 18.0, 18.0, GOLD, 3.6)
    pen.ring(orb_c, 6.0, 18.0, GOLD_DARK, 2.4)
    glow = max(0.0, min(1.0, pose.orb))
    if glow > 0.05:
        _glow(pen.img, lambda d: d.ellipse([*_s((orb_c[0] - 22, orb_c[1] - 22)), *_s((orb_c[0] + 22, orb_c[1] + 22))],
                                           fill=_a(ORB, 0.55 * glow)), 6.0)
    pen.circle(orb_c, 10.0, _mix(CRIMSON_DARK, ORB, 0.4 + 0.6 * glow), 1.2)
    pen.circle(_add(orb_c, (-3.0, -3.0)), 3.5, _mix(ORB, ORB_LIGHT, glow), 0)
    # The finial over the ring.
    pen.poly([_add(orb_c, (up[0] * 18 - 3, up[1] * 18)), _add(orb_c, (up[0] * 26, up[1] * 26)),
              _add(orb_c, (up[0] * 18 + 3, up[1] * 18))], GOLD, 1.0)
    # His hand round the staff.
    hand = _arm(pose, True)[2]
    pen.circle(hand, 8.5, GLOVE, 1.2)
    pen.line([_add(hand, (-6, -2)), _add(hand, (6, -3))], COAT_LIGHT, 1.0)
    return orb_c


def draw_flare(pen: Pen, orb_c: Point, pose: Pose) -> None:
    """The orb's beam flare: a blaze at the orb when the Mandate burns."""
    k = pose.flare
    if k <= 0.0:
        return
    _glow(pen.img, lambda d: d.ellipse([*_s((orb_c[0] - 40 * k, orb_c[1] - 40 * k)), *_s((orb_c[0] + 40 * k, orb_c[1] + 40 * k))],
                                       fill=_a(ORB_LIGHT, 0.8)), 8.0)
    pen.circle(orb_c, 12.0 + 6.0 * k, _a((255, 240, 250, 255), 0.9), 0)


def draw_gate(pen: Pen, pose: Pose, front: bool) -> None:
    """The gate ring round him: an upright violet ring, its back half behind
    him and its front half over him."""
    g = pose.gate
    if g < 0.0:
        return
    c = _body_point(pose, (0.0, -60.0))
    rx, ry = 26.0 + 44.0 * g, 60.0 + 110.0 * g
    if not front:
        _glow(pen.img, lambda d: d.ellipse([*_s((c[0] - rx, c[1] - ry)), *_s((c[0] + rx, c[1] + ry))], fill=_a(GATE, 0.35 * g)), 10.0)
        pen.arc(c, rx, ry, 90, 270, GATE, 5.0)
        pen.arc(c, rx - 4, ry - 4, 90, 270, GATE_LIGHT, 2.0)
        return
    pen.arc(c, rx, ry, 270, 450, GATE, 5.0)
    pen.arc(c, rx - 4, ry - 4, 270, 450, GATE_LIGHT, 2.0)


def _arc(self: Pen, c: Point, rx: float, ry: float, a0: float, a1: float, fill: RGBA, width: float) -> None:
    box = (*_s((c[0] - rx, c[1] - ry)), *_s((c[0] + rx, c[1] + ry)))
    w = max(1, int(width * SUPER))
    self._over(box, lambda d, dx, dy: d.arc((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), a0, a1, fill=fill, width=w))


Pen.arc = _arc  # type: ignore[attr-defined]


def draw_steam(pen: Pen, orb_c: Point, pose: Pose) -> None:
    k = pose.steam
    if k <= 0.0:
        return
    for i in range(5):
        u = (k * 1.4 + i * 0.21) % 1.0
        p = (orb_c[0] + math.sin(i * 2.3 + u * 3.0) * 10.0 - 6.0 * u, orb_c[1] - 10.0 - 50.0 * u)
        pen.circle(p, 5.0 + 9.0 * u, _a(STEAM, 0.55 * (1.0 - u) * min(1.0, k * 2.0)), 0)


def draw_ear_hand(pen: Pen, pose: Pose) -> None:
    """``report``: the far hand at his ear, a finger on the earpiece."""
    if pose.far_hand != "ear":
        return
    c = _head_centre(pose)
    ear = _add(c, _rot((-8.0 * HEAD, 4.0 * HEAD), pose.head))
    shoulder = _shoulder(pose, False)
    elbow = (shoulder[0] - 22.0, shoulder[1] + 10.0)
    pen.tube(shoulder, elbow, 20.0, 17.0, COAT_DARK, 1.3)
    pen.tube(elbow, _lerp(elbow, ear, 0.8), 17.0, 15.0, COAT_DARK, 1.3)
    _cuff(pen, elbow, ear)
    pen.circle(ear, 8.0, GLOVE, 1.2)
    pen.circle(_add(ear, (2.0, -1.0)), 2.2, CRIMSON_LIGHT, 0)


def draw_leader(pose: Pose) -> Image.Image:
    work = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    pen = Pen(work)
    draw_gate(pen, pose, front=False)
    if pose.shown > 0.0:
        draw_cape(pen, pose)
        draw_leg(pen, pose, near=False)
        draw_far_arm(pen, pose)
        draw_collar(pen, pose, front=False)
        draw_coat(pen, pose)
        draw_leg(pen, pose, near=True)
        draw_coat_hem_over_near_leg(pen, pose)
        draw_head(pen, pose)
        draw_collar(pen, pose, front=True)
        draw_ear_hand(pen, pose)
        draw_far_arm_on_staff(pen, pose)
        draw_near_arm(pen, pose)
        orb_c = draw_staff(pen, pose)
        draw_flare(pen, orb_c, pose)
        draw_steam(pen, orb_c, pose)
    else:
        orb_c = None
    if 0.0 < pose.shown < 1.0:
        # Fade him, not the gate behind him: draw him alone, fade, then lay
        # him over the gate's back half.
        body = Image.new("RGBA", work.size, (0, 0, 0, 0))
        back = Image.new("RGBA", work.size, (0, 0, 0, 0))
        draw_gate(Pen(back), pose, front=False)
        body.alpha_composite(work)
        body.putalpha(body.getchannel("A").point(lambda v: int(v * pose.shown)))
        work = back
        work.alpha_composite(body)
        pen = Pen(work)
    draw_gate(pen, pose, front=True)
    return work.resize(FRAME_SIZE, Image.LANCZOS)


def draw_coat_hem_over_near_leg(pen: Pen, pose: Pose) -> None:
    """The coat's skirt falls over the near thigh: its front panel drawn
    again over the leg, to the knee."""
    def bp(x: float, y: float) -> Point:
        return _body_point(pose, (x, y))
    k = pose.kneel
    hem = 118.0 - 40.0 * k
    knee = _leg(pose, True)[1]
    reach = max(knee[0] - pose.x, 0.0)
    panel = [bp(-4, -12), bp(26, -10), bp(30 + 4 * k, 40), bp(32 + 0.3 * reach, hem - 10), bp(28 + 0.3 * reach, hem),
             bp(2, hem - 2), bp(-2, 40)]
    pen.shape(panel, COAT, 1.4, steps=4)
    band = [bp(14, -10), bp(26, -10), bp(30 + 4 * k, 40), bp(30 + 0.3 * reach, hem - 6), bp(16 + 0.3 * reach, hem - 2),
            bp(13, 40)]
    pen.shape(band, CRIMSON, 1.1, steps=4)
    stripe = [bp(16, -10), bp(19, -10), bp(20, 40), bp(21 + 0.3 * reach, hem - 4), bp(18 + 0.3 * reach, hem - 4), bp(17, 40)]
    pen.poly(_smooth(stripe, True, 3), CREAM, 0.7)
    pen.line(_smooth([bp(13, -10), bp(13, 40), bp(15 + 0.3 * reach, hem - 2)], False, 4), GOLD, 1.6)
    pen.line(_smooth([bp(-2, 0), bp(-4, 50), bp(0, hem - 4)], False, 4), COAT_DARK, 2.0)


# ---- the rows ---------------------------------------------------------------------------------------------------

def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _pose_for(animation: str, i: int, n: int) -> Pose:
    loop = animation in ("idle", "walk", "report", "mandate", "overheat", "address")
    t = i / n if loop else i / max(1, n - 1)
    tau = 2.0 * math.pi * t
    base = Pose(ripple=tau, phase=t)

    def g(p: Pose) -> Pose:
        return _grounded(p)

    if animation == "idle":
        breath = math.sin(tau)
        return g(replace(base, lean=-3.0 + breath * 0.8, head=-4.0 - 2.0 * max(0.0, math.sin(tau * 0.5)),
                         cape=0.08 + 0.04 * breath, orb=0.25 + 0.1 * math.sin(tau * 2.0),
                         far_arm=(-10.0, 22.0 + breath * 2.0), expression="stern" if t < 0.6 else "contempt"))
    if animation == "walk":
        s = math.sin(tau)
        return g(replace(base, lean=1.0, near_leg=(4.0 + 22.0 * s, 6.0 + 14.0 * max(0.0, -s)),
                         far_leg=(4.0 - 22.0 * s, 6.0 + 14.0 * max(0.0, s)), staff=6.0 + 8.0 * s,
                         near_arm=(14.0 + 10.0 * s, 8.0), far_arm=(-8.0 - 12.0 * s, 24.0), cape=0.3 + 0.1 * abs(s),
                         head=-3.0, orb=0.3))
    if animation == "order":
        # The far arm thrown out, pointing down the room (tell); then the
        # fist that fires his uplink's lines.
        tell = _ease(t / 0.55)
        fire = _ease((t - 0.6) / 0.15)
        return g(replace(base, lean=-6.0 * tell, head=-8.0 * tell, far_arm=(-8.0 + 104.0 * tell - 14.0 * fire, 22.0 - 20.0 * tell),
                         far_hand="fist" if fire > 0.5 else "point", expression="shout" if fire > 0.5 else "stern",
                         cape=0.2 + 0.3 * fire, orb=0.3 + 0.4 * tell, staff=2.0))
    if animation == "decree":
        lift = _ease(t / 0.55)
        drop = _ease((t - 0.62) / 0.2)
        staff = 4.0 - 30.0 * lift + 110.0 * drop
        arm_up = -130.0 * lift + 115.0 * drop
        return g(replace(base, lean=-6.0 * lift + 8.0 * drop, head=-12.0 * lift + 6.0 * drop, near_arm=(14.0 + arm_up, 10.0 - 30.0 * drop),
                         staff=staff, grip=0.85 - 0.4 * drop, orb=0.3 + 0.7 * lift - 0.3 * drop, expression="shout" if drop > 0.3 else "stern",
                         cape=0.2 + 0.5 * drop, far_arm=(-12.0, 30.0)))
    if animation == "aim":
        # The sceptre levelled like a rifle, both hands, three recoils.
        settle = _ease(t / 0.35)
        kick = 0.0
        for at in (0.45, 0.65, 0.85):
            if at <= t < at + 0.1:
                kick = 1.0 - (t - at) / 0.1
        return g(replace(base, lean=4.0 * settle - 5.0 * kick, head=2.0 * settle, near_arm=(14.0 + 66.0 * settle, 6.0 + 4.0 * settle),
                         staff=4.0 + 86.0 * settle - 6.0 * kick, grip=0.55, two_hands=settle > 0.5, grip2=0.32,
                         orb=0.3 + 0.7 * settle, flare=0.6 * kick, expression="contempt",
                         near_leg=(14.0 * settle, 4.0), far_leg=(-14.0 * settle, 6.0)))
    if animation == "sweep":
        wind = _ease(t / 0.45)
        swing = _ease((t - 0.45) / 0.25)
        staff = 4.0 - 70.0 * wind + 210.0 * swing
        return g(replace(base, lean=-10.0 * wind + 16.0 * swing, near_arm=(14.0 - 60.0 * wind + 130.0 * swing, 20.0 - 10.0 * swing),
                         staff=staff, grip=0.25, two_hands=True, grip2=0.12, cape=0.2 + 0.6 * swing,
                         expression="rage" if swing > 0.2 else "stern", orb=0.4 + 0.4 * swing,
                         near_leg=(20.0 * swing, 8.0), far_leg=(-18.0 * swing - 6.0 * wind, 8.0)))
    if animation == "gate_out":
        swirl = _ease(t / 0.6)
        gone = _ease((t - 0.45) / 0.55)
        return g(replace(base, cape=0.3 + 0.7 * swirl, lean=-4.0, orb=0.4 + 0.6 * swirl, gate=swirl, shown=1.0 - gone,
                         near_arm=(30.0 * swirl, 20.0), staff=-10.0 * swirl, expression="contempt"))
    if animation == "gate_in":
        show = _ease(t / 0.5)
        return g(replace(base, cape=0.9 - 0.7 * t, lean=4.0, gate=1.0 - t, shown=show, orb=0.9 - 0.5 * t,
                         near_arm=(30.0 - 10.0 * t, 16.0), staff=10.0, expression="contempt"))
    if animation == "report":
        # The plan failed: a hand to his ear, shouting into it, the sceptre
        # leaning off him.
        shake = math.sin(tau * 3.0)
        return g(replace(base, lean=6.0 + 2.0 * shake, head=6.0 + 3.0 * shake, far_hand="ear", expression="shout" if t < 0.5 else "rage",
                         staff=18.0 + 4.0 * shake, near_arm=(26.0, 4.0), cape=0.15, orb=0.1,
                         near_leg=(10.0, 8.0), far_leg=(-14.0, 10.0)))
    if animation == "mandate":
        surge = 0.5 + 0.5 * math.sin(tau * 2.0)
        return g(replace(base, lean=6.0, head=4.0, near_arm=(82.0, 4.0), staff=92.0, grip=0.6, two_hands=True, grip2=0.35,
                         orb=1.0, flare=0.7 + 0.3 * surge, cape=0.8 + 0.2 * surge, expression="rage",
                         near_leg=(24.0, 6.0), far_leg=(-24.0, 4.0)))
    if animation == "overheat":
        shake = math.sin(tau * 2.0)
        return g(replace(base, lean=-8.0, head=8.0, near_arm=(30.0, 30.0), staff=40.0 + 6.0 * shake, grip=0.5, orb=0.1,
                         steam=t, far_arm=(30.0 + 20.0 * shake, 60.0), far_hand="open", expression="pain", cape=0.1))
    if animation == "address":
        sweep = math.sin(tau)
        return g(replace(base, lean=-4.0, head=-10.0 + 3.0 * sweep, far_arm=(112.0 + 10.0 * sweep, -16.0), far_hand="open",
                         expression="shout" if (i % 4) < 2 else "stern", orb=0.35, cape=0.15 + 0.05 * sweep))
    if animation == "emergency":
        rise = _ease(t / 0.5)
        burst = _ease((t - 0.5) / 0.3)
        return g(replace(base, lean=-8.0 * rise, head=-16.0 * rise, near_arm=(14.0 - 144.0 * rise, 10.0), staff=-20.0 * rise, grip=0.35 + 0.45 * rise,
                         orb=0.4 + 0.6 * rise, flare=burst, cape=0.3 + 0.7 * burst, expression="rage" if burst > 0.2 else "shout",
                         far_arm=(-60.0 * rise, 40.0), far_hand="fist"))
    if animation == "turn":
        return g(replace(base, lean=-2.0, head=-2.0, cape=0.3 * math.sin(math.pi * t), orb=0.3))
    if animation == "hurt":
        k = [1.0, 0.7, 0.3][min(i, 2)]
        return g(replace(base, lean=-14.0 * k, head=12.0 * k, expression="pain", cape=0.3 * k, staff=-12.0 * k,
                         far_arm=(-30.0 * k, 40.0), orb=0.15))
    if animation == "death":
        # Thrown back (0-0.2), down on one knee on the sceptre (0.2-0.55),
        # defiant; the orb opens a gate behind him (0.55-0.8) and he falls
        # back through it (0.75-1).
        back = _ease(t / 0.15) * (1.0 - _ease((t - 0.15) / 0.15))
        kneel = _ease((t - 0.18) / 0.2)
        gate = _ease((t - 0.55) / 0.2)
        fall = _ease((t - 0.75) / 0.25)
        p = replace(base, lean=-16.0 * back + 10.0 * kneel - 30.0 * fall, head=10.0 * kneel - 14.0 * (t > 0.4) - 20.0 * fall,
                    near_leg=(6.0 + 60.0 * kneel, 4.0 + 90.0 * kneel), far_leg=(-6.0 - 10.0 * kneel, 4.0 + 10.0 * kneel),
                    near_arm=(14.0 + 10.0 * kneel, 10.0), staff=2.0 - 6.0 * kneel, grip=0.62,
                    expression="pain" if t < 0.4 else "defiant", kneel=kneel, orb=0.2 + 0.8 * gate,
                    gate=gate if gate > 0.0 else -1.0, shown=1.0 - fall, cape=0.2 + 0.6 * fall,
                    far_arm=(-20.0 - 20.0 * kneel, 50.0))
        p = g(p)
        if t >= 0.999:
            p = replace(p, shown=0.0, gate=-1.0)
        return p
    return g(base)


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    return draw_leader(_pose_for(animation, frame_index, nframes))


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "The Supreme Leader"},
    "body": {
        "body_plan": "Biped",
        "body_kind": "Standard",
        "mass_class": "Heavy",
        "traits": ["boss", "regime", "ruler"],
        "locomotion_hint": "Walk",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["regime", "boss", "ruler"],
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
