"""GNU-ton, the scholar (v2): a posable figure for the rider sheet.

Drawn in three-quarter view FACING +x, so the runtime's horizontal mirror reads
as him turning round rather than as his arms trading places. A pose is joint
angles, not bespoke art per move: arms and legs are two-segment limbs hung from
the torso, so a new move is a new table of angles.

Coordinates are the generator's design space (y down). ``(hx, hy)`` is his
pelvis. Angles are degrees in screen space: 0 points forward (+x), 90 points
down, -90 points up.

Chirality: he leads with his NEAR hand (the one in front of his body, drawn
after it) and keeps the Principia in his FAR hand, so a prop never jumps hands
between frames of one facing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

from PIL import Image

RGBA = Tuple[int, int, int, int]

OUTLINE: RGBA = (20, 14, 8, 255)
COAT: RGBA = (48, 66, 132, 255)
COAT_D: RGBA = (32, 45, 96, 255)
COAT_L: RGBA = (74, 100, 176, 255)
WAISTCOAT: RGBA = (122, 40, 44, 255)
WAISTCOAT_D: RGBA = (86, 26, 30, 255)
GOLD: RGBA = (226, 186, 88, 255)
LINEN: RGBA = (246, 242, 230, 255)
LINEN_S: RGBA = (204, 196, 178, 255)
SKIN: RGBA = (226, 186, 150, 255)
SKIN_S: RGBA = (190, 146, 112, 255)
CHEEK: RGBA = (222, 140, 128, 255)
WIG: RGBA = (244, 238, 226, 255)
WIG_S: RGBA = (204, 194, 172, 255)
WIG_D: RGBA = (150, 140, 120, 255)
BREECH: RGBA = (40, 34, 44, 255)
STOCKING: RGBA = (236, 232, 222, 255)
SHOE: RGBA = (26, 22, 24, 255)
BOOK: RGBA = (120, 52, 36, 255)
BOOK_D: RGBA = (80, 32, 22, 255)
PAGE: RGBA = (250, 244, 224, 255)
QUILL: RGBA = (250, 250, 246, 255)
QUILL_S: RGBA = (184, 188, 196, 255)
APPLE: RGBA = (206, 40, 36, 255)
APPLE_L: RGBA = (246, 110, 90, 255)
LEAF: RGBA = (66, 140, 60, 255)
STAR: RGBA = (255, 226, 96, 255)
INK: RGBA = (30, 24, 40, 255)

UPPER_ARM = 6.8
FOREARM = 6.2
THIGH = 6.4
SHIN = 6.4


@dataclass
class Pose:
    """One frame of the scholar. Angles in degrees, screen space."""

    near_arm: Tuple[float, float] = (100.0, 80.0)
    far_arm: Tuple[float, float] = (95.0, 60.0)
    near_leg: Tuple[float, float] = (84.0, 92.0)
    far_leg: Tuple[float, float] = (98.0, 94.0)
    lean: float = 0.0  # forward lean of the torso, degrees (+ leans forward)
    head_tilt: float = 0.0  # + looks down, - looks up
    bob: float = 0.0  # vertical body offset
    expression: str = "neutral"
    blink: bool = False
    quill: bool = True  # quill in the near hand
    book: str = "held"  # "held" | "open" | "none"
    apple: Optional[Tuple[float, float]] = None  # relative to the head
    stars: float = -1.0  # >= 0: a ring of dazed stars at this phase
    rotation: float = 0.0  # whole-figure rotation (degrees), about the pelvis
    seated: bool = False


def _rot(p: Tuple[float, float], about: Tuple[float, float], deg: float) -> Tuple[float, float]:
    if deg == 0.0:
        return p
    r = math.radians(deg)
    dx, dy = p[0] - about[0], p[1] - about[1]
    return (about[0] + dx * math.cos(r) - dy * math.sin(r), about[1] + dx * math.sin(r) + dy * math.cos(r))


def _step(p: Tuple[float, float], deg: float, length: float) -> Tuple[float, float]:
    r = math.radians(deg)
    return (p[0] + math.cos(r) * length, p[1] + math.sin(r) * length)


def _limb(c, a, b, color: RGBA, width: float) -> None:
    c.line([a, b], OUTLINE, width + 1.1)
    c.line([a, b], color, width)


def _arm(c, shoulder, angles, sleeve: RGBA, cuff: RGBA) -> Tuple[float, float]:
    elbow = _step(shoulder, angles[0], UPPER_ARM)
    wrist = _step(elbow, angles[1], FOREARM)
    _limb(c, shoulder, elbow, sleeve, 2.6)
    _limb(c, elbow, _step(elbow, angles[1], FOREARM - 1.6), sleeve, 2.4)
    cuff_at = _step(elbow, angles[1], FOREARM - 1.4)
    c.ellipse(cuff_at[0], cuff_at[1], 1.5, 1.5, cuff, OUTLINE, 0.5)
    c.ellipse(wrist[0], wrist[1], 1.25, 1.25, SKIN, OUTLINE, 0.5)
    return wrist


def _leg(c, hip, angles) -> None:
    knee = _step(hip, angles[0], THIGH)
    ankle = _step(knee, angles[1], SHIN)
    _limb(c, hip, knee, BREECH, 2.8)
    _limb(c, knee, ankle, STOCKING, 2.2)
    # Buckled shoe, toe forward.
    toe = (ankle[0] + 2.6, ankle[1] + 0.6)
    c.polygon([(ankle[0] - 1.4, ankle[1] - 0.8), (toe[0], ankle[1] - 0.2), (toe[0] + 0.4, ankle[1] + 1.2), (ankle[0] - 1.6, ankle[1] + 1.2)], SHOE, OUTLINE, 0.5)
    c.ellipse(ankle[0] + 0.6, ankle[1] - 0.2, 0.7, 0.5, GOLD)


def _quill(c, hand, deg: float) -> None:
    tip = _step(hand, deg + 70, 2.2)
    top = _step(hand, deg - 110, 7.5)
    c.line([tip, top], QUILL_S, 0.7)
    vane = [_step(hand, deg - 110, 2.5), _step(_step(hand, deg - 110, 5.0), deg - 20, 1.6), top, _step(_step(hand, deg - 110, 5.0), deg - 200, 0.8)]
    c.polygon(vane, QUILL, OUTLINE, 0.4)
    c.ellipse(tip[0], tip[1], 0.45, 0.45, INK)


def _book_held(c, hand) -> None:
    x, y = hand
    c.polygon([(x - 2.8, y - 4.2), (x + 1.6, y - 4.6), (x + 1.8, y + 1.6), (x - 2.6, y + 2.0)], BOOK, OUTLINE, 0.6)
    c.line([(x - 2.5, y - 3.8), (x - 2.3, y + 1.6)], BOOK_D, 0.8)
    c.line([(x - 1.2, y - 2.0), (x + 0.8, y - 2.2)], GOLD, 0.5)


def _book_open(c, hand) -> None:
    x, y = hand
    c.polygon([(x - 5.0, y - 3.0), (x, y - 1.6), (x, y + 2.4), (x - 5.0, y + 1.0)], PAGE, OUTLINE, 0.5)
    c.polygon([(x, y - 1.6), (x + 5.0, y - 3.0), (x + 5.0, y + 1.0), (x, y + 2.4)], PAGE, OUTLINE, 0.5)
    for i in range(3):
        yy = y - 1.4 + i * 1.0
        c.line([(x - 4.0, yy - 0.2), (x - 1.0, yy + 0.4)], INK, 0.35)
        c.line([(x + 1.0, yy + 0.4), (x + 4.0, yy - 0.2)], INK, 0.35)


def _face(c, head, pose: Pose) -> None:
    hx, hy = head
    ex, ey = hx + 2.4, hy - 0.4  # near eye; the far eye sits behind the nose
    fx = hx + 4.9
    expr = pose.expression
    # Brows.
    if expr in ("focus", "grit"):
        c.line([(ex - 1.4, ey - 2.0), (ex + 1.2, ey - 1.2)], WIG_D, 0.7)
        c.line([(fx - 0.6, ey - 1.6), (fx + 0.4, ey - 2.0)], WIG_D, 0.6)
    elif expr in ("surprise", "smile"):
        c.line([(ex - 1.3, ey - 2.6), (ex + 1.2, ey - 2.8)], WIG_D, 0.6)
        c.line([(fx - 0.6, ey - 2.6), (fx + 0.4, ey - 2.8)], WIG_D, 0.5)
    elif expr == "pain":
        c.line([(ex - 1.3, ey - 1.5), (ex + 1.2, ey - 2.4)], WIG_D, 0.7)
    else:
        c.line([(ex - 1.2, ey - 2.1), (ex + 1.2, ey - 2.2)], WIG_D, 0.55)
    # Eyes.
    if expr == "daze":
        for i in range(6):
            a0 = i * 60 + pose.stars * 360
            p0 = _step((ex, ey), a0, 0.3 + i * 0.18)
            p1 = _step((ex, ey), a0 + 60, 0.3 + (i + 1) * 0.18)
            c.line([p0, p1], OUTLINE, 0.45)
    elif pose.blink or expr in ("pain", "grit"):
        c.line([(ex - 1.0, ey), (ex + 1.0, ey + 0.2)], OUTLINE, 0.6)
        c.line([(fx - 0.4, ey), (fx + 0.3, ey + 0.1)], OUTLINE, 0.5)
    elif expr == "surprise":
        c.ellipse(ex, ey, 1.1, 1.3, LINEN, OUTLINE, 0.45)
        c.ellipse(ex + 0.2, ey, 0.5, 0.55, OUTLINE)
        c.ellipse(fx, ey, 0.55, 0.9, LINEN, OUTLINE, 0.35)
    else:
        c.ellipse(ex, ey, 0.95, 0.85, LINEN, OUTLINE, 0.4)
        look = 0.45 if expr != "smile" else 0.2
        c.ellipse(ex + look, ey + 0.05, 0.5, 0.55, OUTLINE)
        c.ellipse(fx, ey, 0.4, 0.6, OUTLINE)
    # Nose (3/4: a small wedge past the far eye).
    c.polygon([(hx + 4.2, hy - 0.8), (hx + 6.4, hy + 1.6), (hx + 4.6, hy + 2.0)], SKIN, OUTLINE, 0.45)
    c.ellipse(hx + 1.6, hy + 2.0, 1.1, 0.7, CHEEK)
    # Mouth.
    mx, my = hx + 3.2, hy + 3.4
    if expr == "surprise":
        c.ellipse(mx, my + 0.3, 0.8, 1.0, OUTLINE)
    elif expr == "smile":
        c.line([(mx - 1.4, my - 0.3), (mx, my + 0.6), (mx + 1.2, my - 0.2)], OUTLINE, 0.5)
    elif expr == "grit":
        c.polygon([(mx - 1.4, my - 0.4), (mx + 1.4, my - 0.4), (mx + 1.2, my + 0.6), (mx - 1.2, my + 0.6)], LINEN, OUTLINE, 0.4)
    elif expr in ("pain", "daze"):
        c.line([(mx - 1.2, my + 0.3), (mx - 0.4, my - 0.2), (mx + 0.4, my + 0.3), (mx + 1.2, my - 0.1)], OUTLINE, 0.45)
    else:
        c.line([(mx - 1.0, my), (mx + 1.0, my - 0.2)], OUTLINE, 0.5)


def _head(c, head, pose: Pose) -> None:
    hx, hy = head
    # Wig mass behind the head, with the queue down his back.
    c.ellipse(hx - 2.6, hy - 1.2, 6.4, 6.8, WIG, OUTLINE, 0.8)
    for i, dy in enumerate((0.6, 3.2, 5.8)):
        c.ellipse(hx - 5.4 + i * 0.3, hy + dy, 2.6, 2.1, WIG, OUTLINE, 0.6)
        c.ellipse(hx - 5.6 + i * 0.3, hy + dy + 0.5, 1.1, 0.8, WIG_S)
    c.line([(hx - 7.4, hy + 2.0), (hx - 9.2, hy + 7.2)], OUTLINE, 1.6)
    c.line([(hx - 7.4, hy + 2.0), (hx - 9.2, hy + 7.2)], WIG_S, 0.9)
    c.ellipse(hx - 7.6, hy + 2.2, 1.0, 0.8, INK)
    # Face.
    c.ellipse(hx + 1.6, hy + 0.6, 4.6, 5.0, SKIN, OUTLINE, 0.8)
    c.ellipse(hx + 0.4, hy + 2.6, 1.8, 1.4, SKIN_S)
    # Wig crown over the brow, and the near-side curl framing the face.
    c.polygon([(hx - 6.0, hy - 3.0), (hx - 3.0, hy - 7.8), (hx + 2.4, hy - 8.0), (hx + 6.2, hy - 4.2), (hx + 5.4, hy - 3.0), (hx + 1.0, hy - 5.0), (hx - 2.0, hy - 3.4)], WIG, OUTLINE, 0.8)
    c.line([(hx - 2.0, hy - 6.8), (hx + 3.6, hy - 6.6)], WIG_S, 0.6)
    c.ellipse(hx - 2.2, hy + 1.2, 1.3, 2.0, WIG, OUTLINE, 0.6)
    c.ellipse(hx - 2.4, hy + 1.6, 0.5, 0.8, WIG_S)
    _face(c, head, pose)


def _stars(c, head, phase: float) -> None:
    hx, hy = head
    for i in range(3):
        a = math.radians(phase * 360 + i * 120)
        x, y = hx + math.cos(a) * 7.0, hy - 9.0 + math.sin(a) * 2.2
        pts = []
        for k in range(10):
            r = 1.6 if k % 2 == 0 else 0.7
            ang = math.radians(k * 36 - 90)
            pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
        c.polygon(pts, STAR, OUTLINE, 0.35)


def _apple(c, at) -> None:
    x, y = at
    c.ellipse(x, y, 2.2, 2.0, APPLE, OUTLINE, 0.6)
    c.ellipse(x - 0.8, y - 0.6, 0.6, 0.5, APPLE_L)
    c.line([(x, y - 2.0), (x + 0.4, y - 3.2)], OUTLINE, 0.5)
    c.polygon([(x + 0.4, y - 3.0), (x + 2.0, y - 3.6), (x + 1.0, y - 2.4)], LEAF, OUTLINE, 0.3)


def draw_scholar(c, hx: float, hy: float, pose: Pose, scale: float = 1.0) -> None:
    """Draw him on `c` with his pelvis at `(hx, hy)`, `scale` times his design
    size (the fused giant sheet draws him larger than his own sheet's units)."""
    pelvis = (hx, hy + pose.bob)

    def R(p):
        q = (pelvis[0] + (p[0] - pelvis[0]) * scale, pelvis[1] + (p[1] - pelvis[1]) * scale)
        return _rot(q, pelvis, pose.rotation)
    lean = math.radians(pose.lean)
    chest = (pelvis[0] + math.sin(lean) * 8.0, pelvis[1] - math.cos(lean) * 8.0)
    neck = (pelvis[0] + math.sin(lean) * 11.0, pelvis[1] - math.cos(lean) * 11.0)
    head = (neck[0] + 0.6 + math.sin(math.radians(pose.head_tilt)) * 1.2, neck[1] - 5.2)

    class _Rotated:
        """Forward the drawing calls through the whole-figure rotation."""

        def __init__(self, inner):
            self.inner = inner

        def line(self, pts, fill, width=2.0):
            self.inner.line([R(p) for p in pts], fill, width * scale)

        def polygon(self, pts, fill, outline=None, width=1.5):
            self.inner.polygon([R(p) for p in pts], fill, outline, width * scale)

        def ellipse(self, cx, cy, rx, ry, fill, outline=None, width=1.5):
            x, y = R((cx, cy))
            self.inner.ellipse(x, y, rx * scale, ry * scale, fill, outline, width * scale)

    d = _Rotated(c)
    far_shoulder = (neck[0] - 2.0, neck[1] + 1.4)
    near_shoulder = (neck[0] + 1.2, neck[1] + 1.8)
    hip_far = (pelvis[0] - 1.6, pelvis[1] + 0.6)
    hip_near = (pelvis[0] + 1.4, pelvis[1] + 0.8)

    # FAR side first: leg, arm and the book it holds.
    _leg(d, hip_far, pose.far_leg)
    far_hand = _arm(d, far_shoulder, pose.far_arm, COAT_D, LINEN_S)
    if pose.book == "held":
        _book_held(d, far_hand)

    # Coat: skirts flare past the hips, waistcoat and buttons down the front.
    back = (pelvis[0] - 5.4, pelvis[1] + 6.0)
    front = (pelvis[0] + 5.2, pelvis[1] + 6.4)
    d.polygon(
        [
            (neck[0] - 4.2, neck[1] + 1.2),
            (neck[0] + 3.4, neck[1] + 1.4),
            (chest[0] + 4.0, chest[1] + 2.0),
            (front[0], front[1]),
            (pelvis[0] + 0.8, pelvis[1] + 5.2),
            (back[0], back[1]),
            (chest[0] - 4.6, chest[1] + 1.6),
        ],
        COAT,
        OUTLINE,
        0.9,
    )
    d.polygon(
        [(neck[0] + 0.2, neck[1] + 1.6), (neck[0] + 3.0, neck[1] + 1.6), (chest[0] + 3.4, chest[1] + 3.0), (pelvis[0] + 2.6, pelvis[1] + 1.6), (pelvis[0] + 0.6, pelvis[1] + 1.4)],
        WAISTCOAT,
        OUTLINE,
        0.5,
    )
    for i in range(3):
        t = (i + 1) / 4.0
        bx = neck[0] + 2.4 + (pelvis[0] + 2.0 - neck[0] - 2.4) * t
        by = neck[1] + 2.4 + (pelvis[1] + 1.4 - neck[1] - 2.4) * t
        d.ellipse(bx, by, 0.55, 0.55, GOLD)
    d.line([(chest[0] - 3.4, chest[1] + 2.6), (back[0] + 0.8, back[1] - 0.4)], COAT_D, 0.7)
    d.line([(chest[0] + 2.6, chest[1] + 3.8), (front[0] - 1.2, front[1] - 0.6)], COAT_L, 0.6)
    # Cravat.
    d.polygon([(neck[0] + 0.2, neck[1] - 0.6), (neck[0] + 2.8, neck[1] - 0.4), (neck[0] + 2.2, neck[1] + 3.2), (neck[0] + 0.8, neck[1] + 3.4)], LINEN, OUTLINE, 0.5)

    _head(d, head, pose)
    if pose.book == "tucked":
        _book_held(d, (chest[0] + 2.4, chest[1] + 3.8))

    # NEAR side last: leg, arm, and the quill in the leading hand.
    _leg(d, hip_near, pose.near_leg)
    near_hand = _arm(d, near_shoulder, pose.near_arm, COAT, LINEN)
    if pose.quill:
        _quill(d, near_hand, pose.near_arm[1])
    if pose.book == "open":
        _book_open(d, (far_hand[0], far_hand[1] - 2.0))
    if pose.apple is not None:
        _apple(d, (head[0] + pose.apple[0], head[1] + pose.apple[1]))
    if pose.stars >= 0.0:
        _stars(d, head, pose.stars)


# ── The rows ────────────────────────────────────────────────────────────────


def _ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def pose_for(row: str, frame: int, frames: int) -> Pose:
    """The scholar's pose for `frame` of `row`."""
    t = frame / max(1, frames)
    s = math.sin(2 * math.pi * t)
    if row == "rest":
        return Pose(
            near_arm=(70 + 6 * s, 20 + 10 * s),
            far_arm=(80, -20),
            bob=0.3 * s,
            blink=frame == frames - 3,
            book="tucked",
        )
    if row == "point":
        k = _ease(min(1.0, t * 2.2))
        return Pose(
            near_arm=(40 - 30 * k, 30 - 40 * k),
            far_arm=(105, 5),
            lean=4 + 6 * k,
            head_tilt=6,
            expression="focus",
            book="held",
            near_leg=(78, 96),
        )
    if row == "conduct":
        return Pose(
            near_arm=(-5 + 55 * (0.5 + 0.5 * s), -40 + 80 * (0.5 + 0.5 * s)),
            far_arm=(140 - 30 * (0.5 - 0.5 * s), 170 - 60 * (0.5 - 0.5 * s)),
            lean=3 * s,
            expression="focus",
            book="none",
            bob=0.4 * abs(s),
        )
    if row == "invoke":
        k = _ease(min(1.0, t * 2.0))
        return Pose(
            near_arm=(30 - 70 * k, 10 - 80 * k),
            far_arm=(160 + 60 * k, 180 + 70 * k),
            lean=-6 * k,
            head_tilt=-10 * k,
            expression="surprise" if k > 0.6 else "focus",
            quill=True,
            book="open",
        )
    if row == "brace":
        return Pose(
            near_arm=(60, 110 + 6 * s),
            far_arm=(115, 115),
            near_leg=(40, 110),
            far_leg=(70, 120),
            lean=18,
            bob=3.0 + 0.6 * s,
            expression="grit",
            book="none",
        )
    if row == "hit":
        k = math.sin(math.pi * t)
        return Pose(
            near_arm=(40 - 20 * k, 10 - 50 * k),
            far_arm=(-150 + 20 * k, -170),
            lean=-14 * k,
            head_tilt=-12 * k,
            expression="pain",
            book="none",
        )
    if row == "death":
        k = _ease(t * 1.3)
        return Pose(
            near_arm=(60 + 40 * k, 100),
            far_arm=(120, 130),
            near_leg=(80 - 60 * k, 90 - 60 * k),
            far_leg=(95 - 70 * k, 95 - 70 * k),
            rotation=-80 * k,
            bob=4 * k,
            expression="daze",
            stars=t,
            book="none",
            quill=False,
        )
    if row == "tumble":
        return Pose(
            near_arm=(-40 + 30 * s, -80),
            far_arm=(-130, -170 + 30 * s),
            near_leg=(40 + 20 * s, 60),
            far_leg=(120, 150),
            rotation=-360 * t,
            expression="surprise",
            book="none",
            quill=False,
            apple=(4.0 + 6 * t, -9.0 + 2 * t) if t < 0.4 else None,
        )
    if row == "dazed":
        wob = math.sin(2 * math.pi * t) * 4
        return Pose(
            near_arm=(110, 40),
            far_arm=(130, 60),
            near_leg=(-5, 60),
            far_leg=(5, 75),
            lean=-6 + wob,
            head_tilt=wob,
            bob=4.5,
            expression="daze",
            stars=t,
            book="none",
            quill=False,
            seated=True,
            apple=(9.0, 6.0),
        )
    if row == "climb":
        up = _ease(0.5 + 0.5 * s)
        return Pose(
            near_arm=(-30 - 10 * up, -55 + 15 * up),
            far_arm=(-110 + 10 * up, -80 - 20 * up),
            near_leg=(20 + 40 * up, 110),
            far_leg=(80 - 30 * up, 100),
            lean=14,
            expression="grit",
            book="none",
            quill=False,
        )
    raise ValueError(f"no scholar row {row!r}")


# (row, frames, seconds per frame). `rest`, `hit` and `death` keep the names the
# boss sheet's fixed rows use; the rest are named rows a move or the conductor asks for.
ROWS = [
    ("rest", 10, 0.11),
    ("point", 8, 0.07),
    ("conduct", 10, 0.08),
    ("invoke", 8, 0.08),
    ("hit", 6, 0.08),
    ("death", 10, 0.105),
    ("brace", 6, 0.08),
    ("tumble", 8, 0.07),
    ("dazed", 8, 0.12),
    ("climb", 8, 0.07),
]


# The fixed boss-sheet slots, in the order `boss_sheets.ron` lists them, and the
# row each draws. Named rows beyond these follow in `ROWS` order.
SLOT_ROWS = ["rest", "point", "conduct", "invoke", "hit", "death"]
# His height from pelvis to sole, in design units: where his feet are.
PELVIS_TO_SOLE = THIGH + SHIN + 0.4


def row_frames(row: str) -> int:
    return next(frames for name, frames, _ in ROWS if name == row)


def render_frame(canvas_cls, row: str, frame: int, frames: int, size: Tuple[int, int], px_per_unit: int, supersample: int) -> Image.Image:
    """One frame, `size` pixels, `px_per_unit` pixels per design unit, centred on
    his body (pelvis a little below the centre, as the saddle expects)."""
    w, h = size[0] // px_per_unit, size[1] // px_per_unit
    c = canvas_cls(w, h, (0, 0, 0, 0), scale=px_per_unit * supersample)
    draw_scholar(c, 0.0, 4.0, pose_for(row, frame, frames))
    return c.img.resize(size, Image.LANCZOS)
